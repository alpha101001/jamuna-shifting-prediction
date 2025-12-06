import os
import sys
import subprocess
import platform
import shutil
import time
from pathlib import Path

# --- CONFIGURATION ---
PROJECT_ROOT = Path(__file__).resolve().parent
VENV_DIR = PROJECT_ROOT / "venv"
SRC_DIR = PROJECT_ROOT / "src"
WEB_DIR = PROJECT_ROOT / "web"

# Colors for Terminal Output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_step(msg):
    print(f"\n{Colors.HEADER}➤ {msg}{Colors.ENDC}")

def print_success(msg):
    print(f"{Colors.GREEN}✔ {msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.FAIL}✘ {msg}{Colors.ENDC}")

def get_venv_python():
    """Returns the path to the Python executable inside the virtual environment."""
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "python.exe"
    else:
        return VENV_DIR / "bin" / "python"

def run_command(command, cwd=PROJECT_ROOT, shell=False, env=None):
    """Runs a shell command and halts on failure."""
    try:
        subprocess.run(command, cwd=cwd, check=True, shell=shell, env=env)
    except subprocess.CalledProcessError:
        print_error(f"Command failed: {' '.join(command)}")
        sys.exit(1)
    except FileNotFoundError:
        print_error(f"Tool not found: {command[0]}")
        sys.exit(1)

def check_system_requirements():
    print_step("Checking System Requirements...")

    # 1. Check Node.js
    try:
        subprocess.run(["node", "-v"], check=True, stdout=subprocess.DEVNULL)
        print_success("Node.js is installed.")
    except (FileNotFoundError, subprocess.CalledProcessError):
        print_error("Node.js is MISSING.")
        if platform.system() == "Linux":
            print(f"{Colors.WARNING}👉 To install on Fedora: sudo dnf install nodejs -y{Colors.ENDC}")
        elif platform.system() == "Windows":
            print(f"{Colors.WARNING}👉 Download installer: https://nodejs.org/{Colors.ENDC}")
        sys.exit(1)

    # 2. Check pnpm (Install if missing)
    try:
        # Check if pnpm exists
        if platform.system() == "Windows":
             subprocess.run(["pnpm.cmd", "-v"], check=True, stdout=subprocess.DEVNULL, shell=True)
        else:
             subprocess.run(["pnpm", "-v"], check=True, stdout=subprocess.DEVNULL)
        print_success("pnpm is installed.")
    except (FileNotFoundError, subprocess.CalledProcessError):
        print(f"{Colors.WARNING}⚠ pnpm not found. Attempting auto-installation via npm...{Colors.ENDC}")
        try:
            # Attempt global install (might fail on Linux without sudo)
            if platform.system() == "Windows":
                run_command(["npm.cmd", "install", "-g", "pnpm"], shell=True)
            else:
                # Try corepack first (cleaner), else npm
                try:
                    subprocess.run(["corepack", "enable"], check=True)
                    subprocess.run(["corepack", "prepare", "pnpm@latest", "--activate"], check=True)
                except:
                     run_command(["npm", "install", "-g", "pnpm"])
            print_success("pnpm installed successfully.")
        except Exception as e:
            print_error(f"Could not auto-install pnpm: {e}")
            print(f"{Colors.WARNING}👉 Please run: npm install -g pnpm{Colors.ENDC}")
            sys.exit(1)

def setup_python_env():
    print_step("Setting up Python Environment...")

    venv_python = get_venv_python()

    # 1. Create venv if missing
    if not VENV_DIR.exists():
        print(f"   Creating virtual environment at {VENV_DIR}...")
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
        print_success("Virtual Environment Created.")
    else:
        print_success("Virtual Environment exists.")

    # 2. Install Dependencies
    print("   Installing/Updating Python libraries...")
    # Determine pip path
    if platform.system() == "Windows":
        pip_cmd = VENV_DIR / "Scripts" / "pip.exe"
    else:
        pip_cmd = VENV_DIR / "bin" / "pip"

    # We use the venv pip to install requirements
    subprocess.run([str(pip_cmd), "install", "-r", "requirements.txt"], check=True)
    print_success("Python Dependencies Installed.")

def setup_frontend():
    print_step("Setting up Frontend (Next.js)...")

    pnpm_cmd = "pnpm.cmd" if platform.system() == "Windows" else "pnpm"

    # Install node_modules
    print("   Running pnpm install...")
    run_command([pnpm_cmd, "install"], cwd=WEB_DIR, shell=(platform.system()=="Windows"))
    print_success("Frontend Dependencies Installed.")

def run_pipeline():
    print_step("Running ML Data Pipeline...")

    venv_python = str(get_venv_python())

    # 1. Preprocessing
    run_command([venv_python, str(SRC_DIR / "preprocessing.py")])
    # 2. EDA
    run_command([venv_python, str(SRC_DIR / "eda.py")])
    # 3. Training
    run_command([venv_python, str(SRC_DIR / "train.py")])

    print_success("Model Pipeline Completed.")

def start_servers():
    print_step("🚀 LAUNCHING JAMUNA PREDICTION SYSTEM 🚀")

    venv_python = str(get_venv_python())
    pnpm_cmd = "pnpm.cmd" if platform.system() == "Windows" else "pnpm"

    processes = []

    try:
        # Prepare Environment Variables (Add venv to PATH)
        env = os.environ.copy()
        if platform.system() == "Windows":
            env["PATH"] = str(VENV_DIR / "Scripts") + ";" + env["PATH"]
        else:
            env["PATH"] = str(VENV_DIR / "bin") + ":" + env["PATH"]

        # 1. Start Backend
        print(f"{Colors.BLUE}[Backend] Starting FastAPI on port 8000...{Colors.ENDC}")
        backend = subprocess.Popen(
            [venv_python, "-m", "uvicorn", "api.main:app", "--reload"],
            cwd=PROJECT_ROOT,
            env=env
        )
        processes.append(backend)

        # Wait a moment for API to boot
        time.sleep(3)

        # 2. Start Frontend
        print(f"{Colors.BLUE}[Frontend] Starting Next.js on port 3000...{Colors.ENDC}")
        frontend = subprocess.Popen(
            [pnpm_cmd, "run", "dev"],
            cwd=WEB_DIR,
            env=env,
            shell=(platform.system()=="Windows")
        )
        processes.append(frontend)

        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ SYSTEM IS LIVE!{Colors.ENDC}")
        print(f"👉 Frontend: http://localhost:3000")
        print(f"👉 Backend:  http://localhost:8000/docs")
        print(f"{Colors.WARNING}Press Ctrl+C to stop.{Colors.ENDC}\n")

        # Keep running
        backend.wait()
        frontend.wait()

    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}🛑 Shutting down services...{Colors.ENDC}")
        for p in processes:
            p.terminate()
        print_success("Goodbye!")

def main():
    if not (PROJECT_ROOT / "requirements.txt").exists():
        print_error("requirements.txt not found. Please run 'pip freeze > requirements.txt' first.")
        sys.exit(1)

    check_system_requirements()
    setup_python_env()
    setup_frontend()
    run_pipeline()
    start_servers()

if __name__ == "__main__":
    main()
