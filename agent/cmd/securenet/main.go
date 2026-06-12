/*
SecureNet One - Desktop Agent
Windows desktop agent for the SecureNet One Zero Trust platform.

Features:
  - User authentication and device registration
  - WireGuard tunnel management via Wintun
  - DNS-over-HTTPS interception
  - Device posture collection and heartbeat
  - System tray UI with connect/disconnect
  - Auto-reconnect with exponential backoff
  - Windows service support
*/
package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/securenet-one/agent/internal/agent"
	"github.com/securenet-one/agent/internal/ui"
)

var (
	version   = "1.0.0"
	buildTime = "dev"
)

func main() {
	// Parse flags
	serverURL := flag.String("server", "http://localhost:8000/api", "Backend API server URL")
	email := flag.String("email", "", "User email for authentication")
	password := flag.String("password", "", "User password for authentication")
	autoConnect := flag.Bool("auto-connect", false, "Automatically connect on startup")
	showVersion := flag.Bool("version", false, "Show version and exit")
	headless := flag.Bool("headless", false, "Run without system tray UI (service mode)")
	flag.Parse()

	if *showVersion {
		fmt.Printf("SecureNet One Agent v%s (built: %s)\n", version, buildTime)
		os.Exit(0)
	}

	log.Printf("🛡️  SecureNet One Agent v%s starting...", version)

	// Create context with signal handling
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	// Create agent configuration
	cfg := &agent.Config{
		ServerURL:    *serverURL,
		Email:        *email,
		Password:     *password,
		AutoConnect:  *autoConnect,
		Version:      version,
	}

	// Create and initialize the agent
	a, err := agent.New(cfg)
	if err != nil {
		log.Fatalf("Failed to create agent: %v", err)
	}

	// Start the agent
	go func() {
		if err := a.Run(ctx); err != nil {
			log.Printf("Agent error: %v", err)
			cancel()
		}
	}()

	if !*headless {
		// Start system tray UI
		go func() {
			ui.RunSystemTray(a, version)
		}()
	}

	// Wait for shutdown signal
	select {
	case sig := <-sigCh:
		log.Printf("Received signal %s, shutting down...", sig)
	case <-ctx.Done():
	}

	// Graceful shutdown
	a.Shutdown()
	log.Println("✅ Agent shut down successfully")
}
