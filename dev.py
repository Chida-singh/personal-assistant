"""
dev.py — Unified local runner for Personal Assistant (Streamlined Monolith + React Frontend).

Usage:
    python dev.py

This script:
1. Ensures frontend dependencies are installed (npm install)
2. Starts the FastAPI backend (port 8000)
3. Starts the React frontend with Vite (port 5173)
4. Gracefully stops both on Ctrl+C
"""

import subprocess
import sys
import time
from pathlib import Path


def ensure_frontend_dependencies(frontend_dir: Path):
    if not (frontend_dir / "package.json").exists():
        print("[dev] No package.json found, skipping frontend install.")
        return

    if not (frontend_dir / "node_modules").exists():
        print("[dev] Installing frontend dependencies (npm install)...")
        subprocess.run(["npm", "install"], cwd=str(frontend_dir), shell=True, check=True)
        print("[dev] Frontend dependencies installed.")
    else:
        print("[dev] Frontend dependencies OK.")


def main():
    root_dir = Path(__file__).resolve().parent
    frontend_dir = root_dir / "frontend"

    ensure_frontend_dependencies(frontend_dir)

    python_exe = sys.executable

    print("[dev] Starting FastAPI Backend on http://localhost:8000...")
    backend_proc = subprocess.Popen(
        [python_exe, "-m", "uvicorn", "backend.main:app", "--reload", "--port", "8000"],
        cwd=str(root_dir)
    )

    print("[dev] Starting React Frontend on http://localhost:5173...")
    frontend_proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(frontend_dir),
        shell=True
    )

    print("\n[dev] Both backend and frontend are running. Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None:
                print("[dev] Backend process terminated.")
                break
            if frontend_proc.poll() is not None:
                print("[dev] Frontend process terminated.")
                break
    except KeyboardInterrupt:
        print("\n[dev] Stopping servers...")
    finally:
        if backend_proc.poll() is None:
            backend_proc.terminate()
        if frontend_proc.poll() is None:
            frontend_proc.terminate()
        print("[dev] Stopped.")


if __name__ == "__main__":
    main()
