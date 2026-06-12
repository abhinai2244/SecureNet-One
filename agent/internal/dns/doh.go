/*
Package dns provides a DNS-over-HTTPS client that intercepts and forwards
DNS queries to the SecureNet One DoH endpoint.
*/
package dns

import (
	"bytes"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"time"
)

// DoHClient forwards DNS queries to the SecureNet One DoH server.
type DoHClient struct {
	endpoint   string
	httpClient *http.Client
	enabled    bool
}

// NewDoHClient creates a new DoH client.
func NewDoHClient(endpoint string) *DoHClient {
	return &DoHClient{
		endpoint: endpoint,
		httpClient: &http.Client{
			Timeout: 5 * time.Second,
		},
		enabled: false,
	}
}

// Enable activates DNS interception.
func (c *DoHClient) Enable() {
	c.enabled = true
	log.Printf("🔒 DNS-over-HTTPS enabled (endpoint: %s)", c.endpoint)
}

// Disable deactivates DNS interception.
func (c *DoHClient) Disable() {
	c.enabled = false
	log.Println("DNS-over-HTTPS disabled")
}

// IsEnabled returns whether DoH is active.
func (c *DoHClient) IsEnabled() bool {
	return c.enabled
}

// Resolve sends a DNS wire-format query to the DoH endpoint.
func (c *DoHClient) Resolve(dnsQuery []byte) ([]byte, error) {
	if !c.enabled {
		return nil, fmt.Errorf("DoH client is disabled")
	}

	req, err := http.NewRequest("POST", c.endpoint, bytes.NewReader(dnsQuery))
	if err != nil {
		return nil, fmt.Errorf("create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/dns-message")
	req.Header.Set("Accept", "application/dns-message")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("DoH request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("DoH server returned %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("read response: %w", err)
	}

	return body, nil
}

// SetEndpoint updates the DoH server endpoint.
func (c *DoHClient) SetEndpoint(endpoint string) {
	c.endpoint = endpoint
	log.Printf("DoH endpoint updated: %s", endpoint)
}

// StartLocalServer starts a local UDP DNS proxy on 127.0.0.1:53
func (c *DoHClient) StartLocalServer() {
	addr, err := net.ResolveUDPAddr("udp", "127.0.0.1:53")
	if err != nil {
		log.Printf("Failed to resolve UDP address: %v", err)
		return
	}
	conn, err := net.ListenUDP("udp", addr)
	if err != nil {
		log.Printf("⚠️ Could not bind to UDP port 53. Try running as Administrator if you want local DNS proxy: %v", err)
		return
	}
	log.Printf("✅ Local DNS Proxy running on 127.0.0.1:53")

	buf := make([]byte, 2048)
	for {
		n, remoteAddr, err := conn.ReadFromUDP(buf)
		if err != nil {
			continue
		}

		query := make([]byte, n)
		copy(query, buf[:n])

		go func(q []byte, rAddr *net.UDPAddr) {
			resp, err := c.Resolve(q)
			if err == nil && resp != nil {
				conn.WriteToUDP(resp, rAddr)
			}
		}(query, remoteAddr)
	}
}
