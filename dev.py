"""
dev.py — Unified auto-restart launcher for the Personal Assistant.

Usage:
    python dev.py

This script:
1. Checks & installs backend requirements (pip)
2. Checks & installs frontend dependencies (npm)
3. Starts the FastAPI Backend (on port 8000)
4. Starts the React Frontend (on port 5173)

Press Ctrl+C to stop both.
"""

import subprocess
import sys
import time
from pathlib import Path


def ensure_backend_requirements(root_dir: Path):
    venv_python = root_dir / "backend" / ".venv" / "Scripts" / "python.exe"
    requirements = root_dir / "backend" / "requirements.txt"

    if not requirements.exists():
        print("[dev] No requirements.txt found, skipping backend install.")
        return

    # Create venv if it doesn't exist
    if not venv_python.exists():
        print("[dev] Creating backend virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", str(root_dir / "backend" / ".venv")], check=True)

    print("[dev] Checking backend requirements...")
    subprocess.run(
        [str(venv_python), "-m", "pip", "install", "-r", str(requirements), "-q"],
        check=True,
    )
    print("[dev] Backend requirements OK.")


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
    root_dir = Path(__file__).parent
    frontend_dir = root_dir / "frontend"

    ensure_backend_requirements(root_dir)
    ensure_frontend_dependencies(frontend_dir)

    venv_python = root_dir / "backend" / ".venv" / "Scripts" / "python.exe"
    python_exe = str(venv_python) if venv_python.exists() else sys.executable

    print("[dev] Starting FastAPI Backend...")
    backend_proc = subprocess.Popen(
        [python_exe, "-m", "uvicorn", "backend.main:app", "--reload", "--port", "8000"],
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
