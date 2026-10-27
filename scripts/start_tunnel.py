#!/usr/bin/env python3
"""
Public Tunnel Launcher for Ghajini 2.0 Backend.
Exposes local port 8000 to the internet via Cloudflare Tunnel or ngrok
so you can deploy Flutter Web on Vercel/Netlify with live backend access.
"""

import os
import re
import shutil
import subprocess
import sys
import time


def find_tunnel_binary():
    # 1. Check cloudflared
    cloudflared = shutil.which("cloudflared")
    if cloudflared:
        return "cloudflared", cloudflared

    # 2. Check ngrok
    ngrok = shutil.which("ngrok")
    if ngrok:
        return "ngrok", ngrok

    return None, None


def main():
    print("==================================================")
    print("  Ghajini 2.0 - Public Backend Tunnel Launcher")
    print("==================================================")

    tool_type, tool_path = find_tunnel_binary()

    if not tool_path:
        print("\n[!] Neither 'cloudflared' nor 'ngrok' was found on your system PATH.")
        print("\nOption 1 (Recommended - Free, No Account Needed):")
        print("  Install Cloudflare Tunnel:")
        print("  - Windows: winget install Cloudflare.cloudflared")
        print("  - macOS: brew install cloudflared")
        print("  - Linux: sudo apt-get install cloudflared")
        print("\nOption 2 (ngrok):")
        print("  - Download from: https://ngrok.com/download")
        print("  - Run: ngrok http 8000\n")
        print("Once installed, re-run this script to get your public tunnel URL.")
        return

    print(f"\n[+] Detected tunnel provider: {tool_type} ({tool_path})")
    print("[+] Starting tunnel targeting local backend: http://localhost:8000 ...\n")

    if tool_type == "cloudflared":
        cmd = [tool_path, "tunnel", "--url", "http://localhost:8000"]
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        tunnel_url = None
        for line in proc.stdout:
            # Match trycloudflare.com URL
            match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
            if match:
                tunnel_url = match.group(0)
                break
            time.sleep(0.05)

        if tunnel_url:
            api_v1_url = f"{tunnel_url}/v1"
            print("==================================================")
            print(f" SUCCESS! Public Backend URL:")
            print(f"  {tunnel_url}")
            print(f"\n API v1 Endpoint:")
            print(f"  {api_v1_url}")
            print("\n Flutter Web Build Command for Vercel/Web:")
            print(f"  flutter build web --dart-define=API_URL={api_v1_url}")
            print("==================================================")
            print("\nTunnel is active. Press Ctrl+C to terminate.")
            try:
                proc.wait()
            except KeyboardInterrupt:
                proc.terminate()
                print("\nTunnel closed.")
        else:
            print("[!] Cloudflare tunnel started. Check output or logs.")
            proc.wait()

    elif tool_type == "ngrok":
        print("[+] Starting ngrok http 8000...")
        subprocess.run([tool_path, "http", "8000"])


if __name__ == "__main__":
    main()
