/*
Package posture collects device health and security posture information on Windows.
*/
package posture

import (
	"fmt"
	"os"
	"runtime"
	"strings"
	"os/exec"
)

// Collector gathers device posture data.
type Collector struct {
	agentVersion string
}

// NewCollector creates a new posture collector.
func NewCollector(version string) *Collector {
	return &Collector{agentVersion: version}
}

// Collect gathers all device posture information.
func (c *Collector) Collect() map[string]interface{} {
	hostname, _ := os.Hostname()

	data := map[string]interface{}{
		"hostname":      hostname,
		"os":            runtime.GOOS,
		"os_version":    c.getOSVersion(),
		"agent_version": c.agentVersion,
		"cpu_info":      c.getCPUInfo(),
		"ram_bytes":     c.getRAMBytes(),
		"disk_encrypted": c.isDiskEncrypted(),
		"antivirus_active": c.isAntivirusActive(),
		"arch":          runtime.GOARCH,
		"num_cpu":       runtime.NumCPU(),
	}

	return data
}

func (c *Collector) getOSVersion() string {
	if runtime.GOOS == "windows" {
		out, err := exec.Command("cmd", "/c", "ver").Output()
		if err == nil {
			return strings.TrimSpace(string(out))
		}
	}
	return runtime.GOOS + " " + runtime.GOARCH
}

func (c *Collector) getCPUInfo() string {
	return fmt.Sprintf("%s/%s (%d cores)", runtime.GOOS, runtime.GOARCH, runtime.NumCPU())
}

func (c *Collector) getRAMBytes() int64 {
	// On Windows, use WMI or systeminfo
	// For MVP, return a reasonable estimate
	if runtime.GOOS == "windows" {
		out, err := exec.Command("wmic", "ComputerSystem", "get", "TotalPhysicalMemory", "/value").Output()
		if err == nil {
			lines := strings.Split(string(out), "=")
			if len(lines) > 1 {
				val := strings.TrimSpace(lines[1])
				var ram int64
				fmt.Sscanf(val, "%d", &ram)
				if ram > 0 {
					return ram
				}
			}
		}
	}
	// Fallback
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	return int64(m.Sys)
}

func (c *Collector) isDiskEncrypted() bool {
	if runtime.GOOS == "windows" {
		// Check BitLocker status via manage-bde
		out, err := exec.Command("manage-bde", "-status", "C:").Output()
		if err == nil {
			output := strings.ToLower(string(out))
			return strings.Contains(output, "fully encrypted") ||
				strings.Contains(output, "encryption in progress")
		}
	}
	return false
}

func (c *Collector) isAntivirusActive() bool {
	if runtime.GOOS == "windows" {
		// Query Windows Security Center via WMIC
		out, err := exec.Command("wmic", "/namespace:\\\\root\\SecurityCenter2",
			"path", "AntiVirusProduct", "get", "displayName", "/value").Output()
		if err == nil {
			output := strings.TrimSpace(string(out))
			return len(output) > 0 && strings.Contains(output, "=")
		}
	}
	return false
}
