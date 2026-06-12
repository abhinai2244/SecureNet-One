# SecureNet One

SecureNet One is a Zero Trust Desktop Agent, DNS Proxy, and Dashboard built for secure browsing, telemetry, and bypassing ISP Deep Packet Inspection.

## 🚀 Features
- **Local DNS Proxy**: Encrypts and forwards local DNS queries using Post-Quantum Cryptography to Cloudflare.
- **Deep Packet Inspection Bypass**: Fragments TLS ClientHello packets to evade SNI-based filtering.
- **VPS Tunneling**: Built-in support to create a secure SSH SOCKS5 tunnel to any remote VPS.
- **Analytics Dashboard**: Tracks total DNS usage, average latency, and most requested domains.

## 🖥️ Deploying on a VPS

To properly bypass advanced IP-blocking or stateful DPI, the best architecture is to host the Python backend on a cloud VPS (e.g., AWS, DigitalOcean, Linode) and establish an encrypted tunnel from your desktop to the VPS.

### 1. Set up the VPS Backend
Run these commands on your Ubuntu/Debian VPS:

```bash
# Clone or upload the repository to your VPS
cd backend

# Install dependencies
python3 -m pip install -r requirements.txt

# Start the SecureNet Backend API
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. Run the Agent (with VPS Tunnel)
On your Windows machine, build the Go Agent:

```powershell
cd agent
go build -o securenet.exe ./cmd/securenet/
```

Run the agent with the new `--vps-tunnel` flag, passing in your VPS username and IP address:

```powershell
.\securenet.exe --server http://<YOUR_VPS_IP>:8000/api --email admin@securenet.dev --password admin123456 --vps-tunnel root@<YOUR_VPS_IP>
```

*(Note: You will be prompted to enter your VPS SSH password in the terminal, or it will use your SSH keys automatically).*

### 3. Route Traffic through the Tunnel
The agent will automatically create a secure SOCKS5 proxy running on port 1080.
To route your traffic securely:
1. Open Windows **Proxy settings**.
2. Turn on **Manual proxy setup**.
3. Set the Proxy to `127.0.0.1` and Port to `1080`.
4. (Optional) Set your Windows DNS to `127.0.0.1` to use the Agent's secure DNS proxy.

Your entire computer is now securely tunneled to your VPS!

## 📊 Dashboard Usage

Start the Next.js dashboard locally or on your VPS to view analytics:

```bash
cd dashboard
npm install
npm run dev
```

The Dashboard displays:
- **Total DNS Queries** and **Average Latency** (Efficiency).
- **Top Requested Domains** showing exactly what sites are being requested the most.
- **Top Blocked Domains** and recent security events.
