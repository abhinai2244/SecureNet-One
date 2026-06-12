/*
Package ui provides the system tray interface for the SecureNet One agent on Windows.
Uses native Windows API for MVP — no external GUI framework dependencies.
*/
package ui

import (
	"fmt"
	"log"

	"github.com/securenet-one/agent/internal/agent"
)

// RunSystemTray starts the system tray icon with a context menu.
// In a full implementation, this would use:
//   - github.com/getlantern/systray
//   - or golang.org/x/sys/windows for native Win32 tray API
//
// For the MVP, this logs the tray status to console.
func RunSystemTray(a *agent.Agent, version string) {
	log.Printf("🖥️  System Tray UI initialized (SecureNet One v%s)", version)

	/*
	   ┌──────────────────────────────────────────────────────────┐
	   │ PRODUCTION SYSTEM TRAY (using getlantern/systray)       │
	   │                                                         │
	   │ systray.Run(onReady, onExit)                            │
	   │                                                         │
	   │ func onReady() {                                        │
	   │     systray.SetIcon(iconData)                           │
	   │     systray.SetTitle("SecureNet One")                   │
	   │     systray.SetTooltip("SecureNet One - Disconnected")  │
	   │                                                         │
	   │     mConnect := systray.AddMenuItem("Connect", "")      │
	   │     mDisconnect := systray.AddMenuItem("Disconnect","") │
	   │     systray.AddSeparator()                              │
	   │     mStatus := systray.AddMenuItem("Status: Off", "")   │
	   │     mStats := systray.AddMenuItem("↑ 0 B  ↓ 0 B", "")  │
	   │     systray.AddSeparator()                              │
	   │     mDashboard := systray.AddMenuItem("Dashboard","")   │
	   │     mQuit := systray.AddMenuItem("Quit", "")            │
	   │                                                         │
	   │     go handleClicks(a, ...)                              │
	   │ }                                                       │
	   └──────────────────────────────────────────────────────────┘
	*/

	// Register state change listener for console output
	a.OnStateChange(func(state agent.State) {
		var icon string
		switch state {
		case agent.StateConnected:
			icon = "🟢"
		case agent.StateConnecting, agent.StateAuthenticating, agent.StateReconnecting:
			icon = "🟡"
		case agent.StateError:
			icon = "🔴"
		default:
			icon = "⚪"
		}
		log.Printf("%s Tray: Status → %s", icon, state.String())
	})

	// Print menu options
	fmt.Println()
	fmt.Println("╔══════════════════════════════════════╗")
	fmt.Printf("║  SecureNet One Agent v%-15s ║\n", version)
	fmt.Println("╠══════════════════════════════════════╣")
	fmt.Println("║  System Tray Menu:                   ║")
	fmt.Println("║  • Connect/Disconnect via CLI flags  ║")
	fmt.Println("║  • Status shown in console output    ║")
	fmt.Println("║  • Ctrl+C to quit                    ║")
	fmt.Println("╚══════════════════════════════════════╝")
	fmt.Println()
}

// FormatBytes formats byte count to human-readable string.
func FormatBytes(b int64) string {
	const unit = 1024
	if b < unit {
		return fmt.Sprintf("%d B", b)
	}
	div, exp := int64(unit), 0
	for n := b / unit; n >= unit; n /= unit {
		div *= unit
		exp++
	}
	return fmt.Sprintf("%.1f %cB", float64(b)/float64(div), "KMGTPE"[exp])
}
