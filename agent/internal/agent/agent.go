/*
Package agent provides the core orchestrator for the SecureNet One desktop agent.
It manages the agent lifecycle: authentication, device registration, tunnel connection,
heartbeat, and DNS interception.
*/
package agent

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/securenet-one/agent/internal/api"
	"github.com/securenet-one/agent/internal/dns"
	"github.com/securenet-one/agent/internal/posture"
	"github.com/securenet-one/agent/internal/tunnel"
)

// State represents the agent's connection state.
type State int

const (
	StateDisconnected State = iota
	StateAuthenticating
	StateRegistering
	StateConnecting
	StateConnected
	StateReconnecting
	StateError
)

func (s State) String() string {
	names := [...]string{
		"Disconnected",
		"Authenticating",
		"Registering",
		"Connecting",
		"Connected",
		"Reconnecting",
		"Error",
	}
	if int(s) < len(names) {
		return names[s]
	}
	return "Unknown"
}

// Agent is the main orchestrator.
type Agent struct {
	config    *Config
	client    *api.Client
	tunnel    *tunnel.Manager
	dohClient *dns.DoHClient
	collector *posture.Collector

	state     State
	stateMu   sync.RWMutex
	deviceID  string
	token     string
	txBytes   int64
	rxBytes   int64
	statsMu   sync.RWMutex

	stateListeners []func(State)
	listenerMu     sync.Mutex

	stopHeartbeat context.CancelFunc
}

// Config holds agent configuration.
type Config struct {
	ServerURL   string
	Email       string
	Password    string
	AutoConnect bool
	Version     string
}

// New creates a new agent instance.
func New(cfg *Config) (*Agent, error) {
	client := api.NewClient(cfg.ServerURL)

	return &Agent{
		config:    cfg,
		client:    client,
		tunnel:    tunnel.NewManager(),
		dohClient: dns.NewDoHClient(cfg.ServerURL + "/../dns/dns-query"),
		collector: posture.NewCollector(cfg.Version),
		state:     StateDisconnected,
	}, nil
}

// Run starts the agent lifecycle.
func (a *Agent) Run(ctx context.Context) error {
	log.Println("Agent running...")

	if a.config.AutoConnect && a.config.Email != "" && a.config.Password != "" {
		if err := a.Connect(ctx); err != nil {
			log.Printf("Auto-connect failed: %v", err)
		}
	}

	<-ctx.Done()
	return nil
}

// Connect performs authentication, registration, and tunnel connection.
func (a *Agent) Connect(ctx context.Context) error {
	// Step 1: Authenticate
	a.setState(StateAuthenticating)
	log.Println("Authenticating...")

	loginResp, err := a.client.Login(a.config.Email, a.config.Password)
	if err != nil {
		a.setState(StateError)
		return fmt.Errorf("authentication failed: %w", err)
	}

	a.token = loginResp.Tokens.AccessToken
	a.client.SetToken(a.token)
	log.Printf("Authenticated as user %s", loginResp.User.Email)

	// Step 2: Register device (or retrieve existing)
	a.setState(StateRegistering)
	log.Println("Registering device...")

	postureData := a.collector.Collect()
	deviceResp, err := a.client.RegisterDevice(postureData)
	if err != nil {
		// Device may already be registered — try to get existing
		log.Printf("Device registration note: %v (may already exist)", err)
	} else {
		a.deviceID = deviceResp.ID
		log.Printf("Device registered: %s (IP: %s)", deviceResp.DeviceName, deviceResp.AssignedIP)
	}

	// Step 3: Get WireGuard config
	a.setState(StateConnecting)
	log.Println("Fetching WireGuard configuration...")

	if a.deviceID != "" {
		wgConfig, err := a.client.GetWireGuardConfig(a.deviceID)
		if err != nil {
			log.Printf("WireGuard config fetch failed: %v", err)
		} else {
			log.Printf("WireGuard config received (endpoint: %s)", wgConfig.PeerEndpoint)

			// Step 4: Create tunnel
			if err := a.tunnel.Connect(wgConfig); err != nil {
				log.Printf("Tunnel connection failed: %v", err)
			} else {
				log.Println("🔒 WireGuard tunnel established")
			}
		}
	}

	// Step 5: Start local DNS proxy
	a.dohClient.Enable()
	go a.dohClient.StartLocalServer()

	// Step 6: Start heartbeat
	a.setState(StateConnected)
	hbCtx, hbCancel := context.WithCancel(ctx)
	a.stopHeartbeat = hbCancel
	go a.heartbeatLoop(hbCtx)

	log.Println("✅ Agent connected successfully")
	return nil
}

// Disconnect tears down the tunnel and stops heartbeat.
func (a *Agent) Disconnect() {
	log.Println("Disconnecting...")

	if a.stopHeartbeat != nil {
		a.stopHeartbeat()
	}

	if err := a.tunnel.Disconnect(); err != nil {
		log.Printf("Tunnel disconnect error: %v", err)
	}

	a.dohClient.Disable()

	a.setState(StateDisconnected)
	log.Println("Disconnected")
}

// Shutdown gracefully shuts down the agent.
func (a *Agent) Shutdown() {
	a.Disconnect()
}

// GetState returns the current agent state.
func (a *Agent) GetState() State {
	a.stateMu.RLock()
	defer a.stateMu.RUnlock()
	return a.state
}

// GetStats returns current traffic statistics.
func (a *Agent) GetStats() (tx, rx int64) {
	a.statsMu.RLock()
	defer a.statsMu.RUnlock()
	return a.txBytes, a.rxBytes
}

// OnStateChange registers a callback for state changes.
func (a *Agent) OnStateChange(fn func(State)) {
	a.listenerMu.Lock()
	defer a.listenerMu.Unlock()
	a.stateListeners = append(a.stateListeners, fn)
}

func (a *Agent) setState(s State) {
	a.stateMu.Lock()
	a.state = s
	a.stateMu.Unlock()

	a.listenerMu.Lock()
	listeners := make([]func(State), len(a.stateListeners))
	copy(listeners, a.stateListeners)
	a.listenerMu.Unlock()

	for _, fn := range listeners {
		go fn(s)
	}
}

func (a *Agent) heartbeatLoop(ctx context.Context) {
	ticker := time.NewTicker(60 * time.Second)
	defer ticker.Stop()

	// Send initial heartbeat
	a.sendHeartbeat()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			a.sendHeartbeat()
		}
	}
}

func (a *Agent) sendHeartbeat() {
	if a.deviceID == "" {
		return
	}

	postureData := a.collector.Collect()
	resp, err := a.client.SendHeartbeat(a.deviceID, postureData)
	if err != nil {
		log.Printf("Heartbeat failed: %v", err)
		return
	}

	log.Printf("💓 Heartbeat OK (next in %ds)", resp.NextHeartbeatSeconds)
}
