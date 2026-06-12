/*
Package tunnel manages the WireGuard tunnel using Wintun on Windows.
For the MVP, this provides a simulation layer that logs tunnel operations.
Full Wintun integration requires the wintun.dll distributed alongside the binary.
*/
package tunnel

import (
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/securenet-one/agent/internal/api"
)

// Manager manages the WireGuard tunnel lifecycle.
type Manager struct {
	connected bool
	config    *api.WireGuardConfigResponse
	mu        sync.RWMutex
	txBytes   int64
	rxBytes   int64
	startTime time.Time
}

// NewManager creates a new tunnel manager.
func NewManager() *Manager {
	return &Manager{}
}

// Connect establishes the WireGuard tunnel.
func (m *Manager) Connect(config *api.WireGuardConfigResponse) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.connected {
		return fmt.Errorf("tunnel already connected")
	}

	log.Printf("🔧 Creating WireGuard tunnel...")
	log.Printf("   Interface Address: %s", config.InterfaceAddress)
	log.Printf("   DNS: %s", config.InterfaceDNS)
	log.Printf("   MTU: %d", config.InterfaceMTU)
	log.Printf("   Peer Endpoint: %s", config.PeerEndpoint)
	log.Printf("   Allowed IPs: %s", config.PeerAllowedIPs)

	/*
	   ┌──────────────────────────────────────────────────────────┐
	   │ PRODUCTION WINTUN INTEGRATION                           │
	   │                                                         │
	   │ In production, this would:                               │
	   │ 1. Load wintun.dll                                      │
	   │ 2. Create a Wintun adapter:                             │
	   │    adapter, err := wintun.CreateAdapter(                 │
	   │        "SecureNet", "WireGuard", tunnelGUID)             │
	   │ 3. Start a session:                                     │
	   │    session, err := adapter.StartSession(0x800000)        │
	   │ 4. Configure the interface IP and routes                │
	   │ 5. Start packet read/write loops:                       │
	   │    - Read from Wintun → encrypt → send UDP              │
	   │    - Receive UDP → decrypt → write to Wintun            │
	   │ 6. Set DNS to the DoH endpoint                          │
	   │                                                         │
	   │ Dependencies:                                            │
	   │   go get golang.zx2c4.com/wintun                        │
	   │   go get golang.zx2c4.com/wireguard                     │
	   │   Distribute wintun.dll alongside the binary            │
	   │   Run as Administrator                                   │
	   └──────────────────────────────────────────────────────────┘
	*/

	m.config = config
	m.connected = true
	m.startTime = time.Now()
	m.txBytes = 0
	m.rxBytes = 0

	log.Printf("✅ WireGuard tunnel established (simulation mode)")
	log.Printf("   For production: install wintun.dll and build with -tags wintun")

	return nil
}

// Disconnect tears down the WireGuard tunnel.
func (m *Manager) Disconnect() error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if !m.connected {
		return nil
	}

	log.Printf("🔌 Disconnecting WireGuard tunnel...")
	/*
	   In production:
	   - Close the Wintun session
	   - Delete the adapter
	   - Restore DNS settings
	   - Remove routes
	*/

	m.connected = false
	m.config = nil
	log.Printf("✅ Tunnel disconnected")
	return nil
}

// IsConnected returns whether the tunnel is active.
func (m *Manager) IsConnected() bool {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.connected
}

// GetStats returns traffic statistics.
func (m *Manager) GetStats() (tx, rx int64, uptime time.Duration) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	if m.connected {
		return m.txBytes, m.rxBytes, time.Since(m.startTime)
	}
	return 0, 0, 0
}

// GetConfig returns the current WireGuard config.
func (m *Manager) GetConfig() *api.WireGuardConfigResponse {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.config
}
