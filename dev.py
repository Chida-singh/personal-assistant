"""
dev.py — Unified auto-restart launcher for the Personal Assistant.

Usage:
    python dev.py

This script starts:
1. The FastAPI Backend (on port 8000)
2. The React Frontend (on port 5173)

Press Ctrl+C to stop both.
"""

import subprocess
import sys
import time
from pathlib import Path

def main():
    root_dir = Path(__file__).parent
    frontend_dir = root_dir / "frontend"

    print("[dev] Starting FastAPI Backend...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--reload", "--port", "8000"],
        cwd=str(root_dir)
    )

    print("[dev] Starting React Frontend...")
    frontend_proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(frontend_dir),
        shell=True
    )

    print("[dev] Both servers running. Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[dev] Stopping servers...")
        backend_proc.terminate()
        frontend_proc.terminate()
        backend_proc.wait()
        frontend_proc.wait()
        print("[dev] Stopped.")

if __name__ == "__main__":
    main()
