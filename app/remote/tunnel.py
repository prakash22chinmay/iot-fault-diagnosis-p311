"""
Remote Access and 24/7 Global Connectivity Module for Project P_311.
Enables instant access from any smartphone, tablet, or PC worldwide on cellular, 4G/5G, or external networks.
Supports Cloudflare Quick Tunnels, Local Area Network IP discovery, and ngrok.
"""
import os
import re
import socket
import subprocess
import threading
import time
import urllib.request
from pathlib import Path
from typing import Optional, Dict, Any

from app.config import settings, DATA_DIR


class RemoteTunnelManager:
    def __init__(self):
        self.public_url: Optional[str] = None
        self.local_network_url: Optional[str] = None
        self.status: str = "OFFLINE"
        self._process: Optional[subprocess.Popen] = None
        self._thread: Optional[threading.Thread] = None
        self.bin_dir = DATA_DIR / "bin"
        self.bin_dir.mkdir(parents=True, exist_ok=True)
        self.cloudflared_path = self.bin_dir / ("cloudflared.exe" if os.name == "nt" else "cloudflared")
        self._detect_local_ip()

    def _detect_local_ip(self):
        """Find the machine's local LAN IP (e.g. 192.168.x.x) for LAN access."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            self.local_network_url = f"http://{ip}:{settings.PORT}"
        except Exception:
            self.local_network_url = f"http://localhost:{settings.PORT}"

    def get_info(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "public_url": self.public_url,
            "local_network_url": self.local_network_url,
            "localhost_url": f"http://localhost:{settings.PORT}",
            "instructions": "Open the Public URL from any mobile phone or device worldwide to access the dashboard 24/7."
        }

    def start_tunnel(self, port: int = 8000):
        """Asynchronously start remote tunnel."""
        if not settings.ENABLE_PUBLIC_TUNNEL:
            self.status = "LOCAL_ONLY"
            return

        self._thread = threading.Thread(target=self._run_cloudflare_tunnel, args=(port,), daemon=True)
        self._thread.start()

    def _download_cloudflared(self) -> bool:
        """Download cloudflared binary if not present."""
        if self.cloudflared_path.exists():
            return True

        print("[Tunnel] Downloading Cloudflare Quick Tunnel binary for zero-config global access...")
        try:
            if os.name == "nt":
                url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
            else:
                url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"

            urllib.request.urlretrieve(url, str(self.cloudflared_path))
            if os.name != "nt":
                os.chmod(self.cloudflared_path, 0o755)
            print("[Tunnel] Cloudflare tunnel binary downloaded successfully.")
            return True
        except Exception as e:
            print(f"[Tunnel] Could not automatically download cloudflared: {e}")
            return False

    def _run_cloudflare_tunnel(self, port: int):
        self.status = "INITIALIZING"
        
        # Check system PATH first
        has_system = subprocess.run(
            ["where" if os.name == "nt" else "which", "cloudflared"],
            capture_output=True,
            shell=True
        ).returncode == 0

        cmd_path = "cloudflared" if has_system else str(self.cloudflared_path)

        if not has_system and not self.cloudflared_path.exists():
            downloaded = self._download_cloudflared()
            if not downloaded:
                self.status = "FALLBACK_LAN"
                print(f"[Tunnel] Global tunnel unavailable. Accessible on LAN: {self.local_network_url}")
                return

        try:
            print(f"[Tunnel] Launching Cloudflare Tunnel for port {port}...")
            # cloudflared tunnel --url http://127.0.0.1:<port>
            self._process = subprocess.Popen(
                [cmd_path, "tunnel", "--url", f"http://127.0.0.1:{port}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Monitor stdout/stderr for the generated https://*.trycloudflare.com URL
            pattern = re.compile(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com')
            while self._process and self._process.poll() is None:
                line = self._process.stdout.readline()
                if not line:
                    break
                match = pattern.search(line)
                if match:
                    self.public_url = match.group(0)
                    self.status = "ACTIVE_GLOBAL"
                    print("\n" + "="*70)
                    print(f"🚀 [24/7 GLOBAL ACCESS URL ACTIVE]")
                    print(f"🌐 Public HTTPS URL: {self.public_url}")
                    print(f"📱 Access from any phone, laptop, or tablet on any network worldwide!")
                    print(f"🏠 LAN Wi-Fi URL:    {self.local_network_url}")
                    print("="*70 + "\n")
                    break

        except Exception as e:
            print(f"[Tunnel] Error starting cloudflare tunnel: {e}")
            self.status = "ERROR"

    def stop_tunnel(self):
        if self._process:
            self._process.terminate()
            self._process = None
            self.status = "OFFLINE"
            self.public_url = None


# Global singleton instance
remote_tunnel = RemoteTunnelManager()
