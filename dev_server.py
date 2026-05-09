#!/usr/bin/env python3
"""
LocalCopilot Development Server Startup and Verification Script

This script helps with:
1. Installing dependencies for backend and frontend
2. Starting the backend server (FastAPI on port 8000)
3. Starting the frontend dev server (Vite on port 5173)
4. Verifying the application is working

Usage:
  python dev_server.py --help
  python dev_server.py setup              # Install dependencies
  python dev_server.py start-backend      # Start backend only
  python dev_server.py start-frontend     # Start frontend only
  python dev_server.py start-all          # Start both servers
  python dev_server.py test               # Run integration tests
"""

import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path
import argparse

PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(msg):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{msg:^60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(msg):
    print(f"{Colors.OKGREEN}✅ {msg}{Colors.ENDC}")

def print_info(msg):
    print(f"{Colors.OKCYAN}ℹ️  {msg}{Colors.ENDC}")

def print_warning(msg):
    print(f"{Colors.WARNING}⚠️  {msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.FAIL}❌ {msg}{Colors.ENDC}")

def run_command(cmd, cwd=None, shell=True):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, cwd=cwd, shell=shell, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {cmd}")
        return False

def setup_backend():
    """Install backend dependencies"""
    print_header("Setting Up Backend")
    
    # Create .env if it doesn't exist
    env_file = BACKEND_DIR / ".env"
    env_example = BACKEND_DIR / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        print_info("Creating .env from .env.example...")
        with open(env_example) as src, open(env_file, 'w') as dst:
            dst.write(src.read())
        print_success(".env created")
    
    # Install Python dependencies
    print_info("Installing Python dependencies...")
    if sys.platform == "win32":
        cmd = f"{sys.executable} -m pip install -r requirements.txt"
    else:
        cmd = f"{sys.executable} -m pip install -r requirements.txt"
    
    if run_command(cmd, cwd=BACKEND_DIR):
        print_success("Backend dependencies installed")
    else:
        print_error("Failed to install backend dependencies")
        return False
    
    return True

def setup_frontend():
    """Install frontend dependencies"""
    print_header("Setting Up Frontend")
    
    print_info("Installing Node.js dependencies...")
    if sys.platform == "win32":
        cmd = "npm install"
    else:
        cmd = "npm install"
    
    if run_command(cmd, cwd=FRONTEND_DIR):
        print_success("Frontend dependencies installed")
    else:
        print_error("Failed to install frontend dependencies")
        return False
    
    return True

def setup_all():
    """Setup both backend and frontend"""
    print_header("Setting Up LocalCopilot")
    
    success = True
    success = success and setup_backend()
    success = success and setup_frontend()
    
    if success:
        print_header("Setup Complete ✅")
        print_info("You can now start the servers:")
        print(f"  • Backend:  {Colors.BOLD}python dev_server.py start-backend{Colors.ENDC}")
        print(f"  • Frontend: {Colors.BOLD}python dev_server.py start-frontend{Colors.ENDC}")
        print(f"  • Both:     {Colors.BOLD}python dev_server.py start-all{Colors.ENDC}")
    else:
        print_error("Setup failed")
    
    return success

def start_backend():
    """Start the backend FastAPI server"""
    print_header("Starting Backend Server")
    
    print_info("Starting FastAPI server on http://localhost:8000")
    print_warning("Press Ctrl+C to stop the server")
    
    if sys.platform == "win32":
        cmd = f"{sys.executable} -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    else:
        cmd = f"{sys.executable} -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    
    subprocess.run(cmd, cwd=BACKEND_DIR, shell=True)

def start_frontend():
    """Start the frontend Vite dev server"""
    print_header("Starting Frontend Server")
    
    print_info("Starting Vite dev server on http://localhost:5173")
    print_warning("Press Ctrl+C to stop the server")
    
    cmd = "npm run dev"
    subprocess.run(cmd, cwd=FRONTEND_DIR, shell=True)

def start_all():
    """Start both servers in parallel"""
    print_header("Starting LocalCopilot (All Servers)")
    
    print_info("Starting backend and frontend servers...")
    print_info("Backend:  http://localhost:8000")
    print_info("Frontend: http://localhost:5173")
    print_warning("Press Ctrl+C to stop all servers")
    
    import threading
    
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    frontend_thread = threading.Thread(target=start_frontend, daemon=True)
    
    backend_thread.start()
    print_info("Waiting for backend to start...")
    time.sleep(3)
    
    frontend_thread.start()
    print_info("Waiting for frontend to start...")
    time.sleep(3)
    
    print_header("✅ Servers Started")
    print_info("Opening browser in 3 seconds...")
    time.sleep(3)
    
    try:
        webbrowser.open("http://localhost:5173")
    except:
        print_warning("Could not open browser automatically")
    
    try:
        backend_thread.join()
        frontend_thread.join()
    except KeyboardInterrupt:
        print_warning("\nShutting down servers...")

def run_tests():
    """Run integration tests"""
    print_header("Running Integration Tests")
    
    test_file = PROJECT_ROOT / "tests" / "test_api.py"
    if not test_file.exists():
        print_error("Test file not found")
        return False
    
    print_info("Ensure backend server is running on port 8000")
    print_info("Running tests...")
    
    cmd = f"{sys.executable} tests/test_api.py"
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    
    return result.returncode == 0

def main():
    parser = argparse.ArgumentParser(
        description="LocalCopilot Development Server Manager"
    )
    parser.add_argument(
        "command",
        choices=["setup", "start-backend", "start-frontend", "start-all", "test"],
        help="Command to run"
    )
    
    args = parser.parse_args()
    
    os.chdir(PROJECT_ROOT)
    
    if args.command == "setup":
        setup_all()
    elif args.command == "start-backend":
        start_backend()
    elif args.command == "start-frontend":
        start_frontend()
    elif args.command == "start-all":
        start_all()
    elif args.command == "test":
        run_tests()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_warning("\nOperation cancelled")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error: {e}")
        sys.exit(1)
