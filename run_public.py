import os
import sys
import subprocess
import time
import urllib.request
import threading
import uvicorn

from app import app
from config import HOST, PORT

def get_public_ip():
    try:
        req = urllib.request.Request("https://api.ipify.org", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3) as res:
            return res.read().decode("utf-8").strip()
    except Exception:
        return "152.59.191.32"

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

def main():
    print("=" * 60)
    print("  Instagram Transcript Generator - Public Tunnel Launcher")
    print("=" * 60)

    # Fetch public IP for tunnel password
    public_ip = get_public_ip()

    # Start FastAPI server in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    time.sleep(2)

    print("\n" + "-" * 60)
    print(f"  Tunnel Password (if prompted in browser): {public_ip}")
    print("-" * 60 + "\n")
    print("Generating public HTTPS tunnel link...")

    # Start localtunnel
    cmd = ["npx.cmd" if sys.platform == "win32" else "npx", "localtunnel", "--port", "8000"]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nStopping server and tunnel...")

if __name__ == "__main__":
    main()
