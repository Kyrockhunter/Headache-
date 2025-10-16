#!/usr/bin/env python3
"""
Fantasy Optimizer – Framework Test Runner (v4.3.0)
Maintained by: KyRockHunter
Python: 3.13.7
"""
import sys
import subprocess
import datetime
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd  # Ensures `pd` is defined everywhere

# Color output (safe fallback if colorama missing)
try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)
except ImportError:
    class Dummy:
        RESET_ALL = ""
        GREEN = ""
        RED = ""
        YELLOW = ""
        CYAN = ""
        MAGENTA = ""
    Fore = Style = Dummy()

def c_ok(msg):
    print(f"{Fore.GREEN}✔ {msg}{Style.RESET_ALL}")

def c_warn(msg):
    print(f"{Fore.YELLOW}⚠ {msg}{Style.RESET_ALL}")

def c_err(msg):
    print(f"{Fore.RED}✘ {msg}{Style.RESET_ALL}")

def c_info(msg):
    print(f"{Fore.CYAN}• {msg}{Style.RESET_ALL}")

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUTPUTS = DATA / "outputs"
OUTPUTS.mkdir(parents=True, exist_ok=True)

# Ensure src package is importable for VS Code/Pylance
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

TS = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
LOG = OUTPUTS / f"test_summary_{TS}.txt"

def run_pytest() -> Tuple[int, str]:
    """Run pytest as a subprocess, tee stdout/stderr to console and capture to string."""
    c_info("Running pytest (full output will be logged)...")
    cmd = [sys.executable, "-m", "pytest", "-vv"]
    proc = subprocess.Popen(cmd, cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    output_lines = []
    for line in proc.stdout:
        print(line, end="")
        output_lines.append(line)
    proc.wait()
    return proc.returncode, "".join(output_lines)


def main():
    print("="*70)
    print(" FANTASY OPTIMIZER – FRAMEWORK TEST (v4.3.0) ".center(70, "="))
    print("="*70)
    c_info("Stub version for debugging import and structure.")
    print("="*70)

if __name__ == "__main__":
    main()
