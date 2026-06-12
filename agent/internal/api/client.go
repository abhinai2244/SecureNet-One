/*
Package api provides the HTTP client for communicating with the SecureNet One backend.
*/
package api

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// Client communicates with the SecureNet One backend API.
type Client struct {
	baseURL    string
	httpClient *http.Client
	token      string
}

// NewClient creates a new API client.
func NewClient(baseURL string) *Client {
	return &Client{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// SetToken sets the JWT authentication token.
func (c *Client) SetToken(token string) {
	c.token = token
}

// ── Request/Response Types ──────────────────────────────────────

type LoginRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

type LoginResponse struct {
	User   UserInfo      `json:"user"`
	Tokens TokenResponse `json:"tokens"`
}

type UserInfo struct {
	ID       string `json:"id"`
	Email    string `json:"email"`
	FullName string `json:"full_name"`
	Role     string `json:"role"`
}

type TokenResponse struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
	ExpiresIn    int    `json:"expires_in"`
}

type DeviceRegisterRequest struct {
	DeviceName   string `json:"device_name"`
	Hostname     string `json:"hostname"`
	OS           string `json:"os"`
	OSVersion    string `json:"os_version,omitempty"`
	AgentVersion string `json:"agent_version,omitempty"`
}

type DeviceResponse struct {
	ID         string `json:"id"`
	DeviceName string `json:"device_name"`
	Hostname   string `json:"hostname"`
	OS         string `json:"os"`
	Status     string `json:"status"`
	AssignedIP string `json:"assigned_ip"`
	PublicKey  string `json:"public_key"`
}

type HeartbeatRequest struct {
	DeviceID       string                 `json:"device_id"`
	OS             string                 `json:"os,omitempty"`
	OSVersion      string                 `json:"os_version,omitempty"`
	AgentVersion   string                 `json:"agent_version,omitempty"`
	DiskEncrypted  *bool                  `json:"disk_encrypted,omitempty"`
	AntivirusActive *bool                 `json:"antivirus_active,omitempty"`
	CPUInfo        string                 `json:"cpu_info,omitempty"`
	RAMBytes       *int64                 `json:"ram_bytes,omitempty"`
	Metadata       map[string]interface{} `json:"metadata,omitempty"`
}

type HeartbeatResponse struct {
	Status               string `json:"status"`
	ServerTime           string `json:"server_time"`
	NextHeartbeatSeconds int    `json:"next_heartbeat_seconds"`
}

type WireGuardConfigResponse struct {
	InterfacePrivateKey    string `json:"interface_private_key"`
	InterfaceAddress       string `json:"interface_address"`
	InterfaceDNS           string `json:"interface_dns"`
	InterfaceMTU           int    `json:"interface_mtu"`
	PeerPublicKey          string `json:"peer_public_key"`
	PeerEndpoint           string `json:"peer_endpoint"`
	PeerAllowedIPs         string `json:"peer_allowed_ips"`
	PeerPersistentKeepalive int   `json:"peer_persistent_keepalive"`
	PeerPresharedKey       string `json:"peer_preshared_key,omitempty"`
}

// ── API Methods ─────────────────────────────────────────────────

// Login authenticates with the backend.
func (c *Client) Login(email, password string) (*LoginResponse, error) {
	body := LoginRequest{Email: email, Password: password}
	var resp LoginResponse
	if err := c.post("/auth/login", body, &resp); err != nil {
		return nil, err
	}
	return &resp, nil
}

// RegisterDevice registers a new device.
func (c *Client) RegisterDevice(posture map[string]interface{}) (*DeviceResponse, error) {
	hostname, _ := posture["hostname"].(string)
	osName, _ := posture["os"].(string)
	osVersion, _ := posture["os_version"].(string)
	agentVersion, _ := posture["agent_version"].(string)

	body := DeviceRegisterRequest{
		DeviceName:   hostname,
		Hostname:     hostname,
		OS:           osName,
		OSVersion:    osVersion,
		AgentVersion: agentVersion,
	}

	var resp DeviceResponse
	if err := c.post("/devices/register", body, &resp); err != nil {
		return nil, err
	}
	return &resp, nil
}

// SendHeartbeat sends device heartbeat with posture data.
func (c *Client) SendHeartbeat(deviceID string, posture map[string]interface{}) (*HeartbeatResponse, error) {
	osName, _ := posture["os"].(string)
	osVersion, _ := posture["os_version"].(string)
	agentVersion, _ := posture["agent_version"].(string)
	cpuInfo, _ := posture["cpu_info"].(string)

	encrypted, _ := posture["disk_encrypted"].(bool)
	antivirus, _ := posture["antivirus_active"].(bool)
	ramBytes, _ := posture["ram_bytes"].(int64)

	body := HeartbeatRequest{
		DeviceID:        deviceID,
		OS:              osName,
		OSVersion:       osVersion,
		AgentVersion:    agentVersion,
		DiskEncrypted:   &encrypted,
		AntivirusActive: &antivirus,
		CPUInfo:         cpuInfo,
		RAMBytes:        &ramBytes,
		Metadata:        posture,
	}

	var resp HeartbeatResponse
	if err := c.post("/devices/heartbeat", body, &resp); err != nil {
		return nil, err
	}
	return &resp, nil
}

// GetWireGuardConfig fetches the WireGuard configuration for a device.
func (c *Client) GetWireGuardConfig(deviceID string) (*WireGuardConfigResponse, error) {
	var resp WireGuardConfigResponse
	if err := c.get(fmt.Sprintf("/wireguard/config/%s", deviceID), &resp); err != nil {
		return nil, err
	}
	return &resp, nil
}

// ── HTTP Helpers ────────────────────────────────────────────────

func (c *Client) get(path string, result interface{}) error {
	req, err := http.NewRequest("GET", c.baseURL+path, nil)
	if err != nil {
		return err
	}
	return c.doRequest(req, result)
}

func (c *Client) post(path string, body interface{}, result interface{}) error {
	jsonBody, err := json.Marshal(body)
	if err != nil {
		return fmt.Errorf("marshal request: %w", err)
	}

	req, err := http.NewRequest("POST", c.baseURL+path, bytes.NewReader(jsonBody))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	return c.doRequest(req, result)
}

func (c *Client) doRequest(req *http.Request, result interface{}) error {
	if c.token != "" {
		req.Header.Set("Authorization", "Bearer "+c.token)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("read response: %w", err)
	}

	if resp.StatusCode >= 400 {
		return fmt.Errorf("API error %d: %s", resp.StatusCode, string(respBody))
	}

	if result != nil {
		if err := json.Unmarshal(respBody, result); err != nil {
			return fmt.Errorf("decode response: %w", err)
		}
	}

	return nil
}
