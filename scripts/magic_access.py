#!/usr/bin/env python3
"""
🔮 SUPERHUMAN ACCESS PORTAL 🔮
--------------------------------
This script manages the critical gateway to the Reality Kernel.
It handles port conflicts, process termination, and URL generation
with extreme prejudice and precision.
"""

import os
import socket
import sys
import time

import psutil

# --- CONFIGURATION ---
PORT_BACKEND = 8000
PORT_FRONTEND = 5000
APP_NAME = "CogniForge Reality Kernel"


# --- SUPERHUMAN VISUALS ---
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_banner():
    print(f"{Colors.HEADER}")
    print(r"""
   _____                      _ ______
  / ____|                    (_)  ____|
 | |     ___   __ _ _ __  _   _| |__ ___  _ __ __ _  ___
 | |    / _ \ / _` | '_ \| | | |  __/ _ \| '__/ _` |/ _ \
 | |___| (_) | (_| | | | | |_| | | | (_) | | | (_| |  __/
  \_____\___/ \__, |_| |_|\__,_|_|  \___/|_|  \__, |\___|
               __/ |                           __/ |
              |___/                           |___/
    """)
    print(f"{Colors.CYAN}   >>> SUPERHUMAN ACCESS PROTOCOL INITIATED <<<{Colors.ENDC}")
    print(f"{Colors.HEADER}--------------------------------------------------{Colors.ENDC}")


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("0.0.0.0", port)) == 0


def kill_process_on_port(port):
    print(
        f"{Colors.WARNING}⚠️  Port {port} is occupied. Scanning for unauthorized entities...{Colors.ENDC}"
    )
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            for conn in proc.connections(kind="inet"):
                if conn.laddr.port == port:
                    print(
                        f"{Colors.FAIL}🔥 DETECTED HOSTILE: {proc.info['name']} (PID: {proc.info['pid']}){Colors.ENDC}"
                    )
                    proc.terminate()
                    proc.wait(timeout=3)
                    print(f"{Colors.GREEN}✅ Entity Neutralized.{Colors.ENDC}")
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False


def get_codespace_url(port):
    codespace_name = os.getenv("CODESPACE_NAME")
    domain = os.getenv("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN")

    if codespace_name and domain:
        return f"https://{codespace_name}-{port}.{domain}"
    return f"http://localhost:{port}"


def main():
    print_banner()

    # 1. Check Backend Port
    if is_port_in_use(PORT_BACKEND):
        print(
            f"{Colors.WARNING}⚡ Port {PORT_BACKEND} is active. Ensuring system integrity...{Colors.ENDC}"
        )
        # In a dev script, we might want to kill it to restart fresh, or just warn.
        # "Superhuman" implies we take control.
        # But if it's running, maybe we just want to show the link?
        # Let's assume if this script is run, the user WANTS to start the app.
        # So we kill the old one.
        kill_process_on_port(PORT_BACKEND)
        # Verify kill
        time.sleep(1)
        if is_port_in_use(PORT_BACKEND):
            print(
                f"{Colors.FAIL}❌ Failed to clear port {PORT_BACKEND}. Manual intervention required.{Colors.ENDC}"
            )
            sys.exit(1)

    # 2. Check Frontend Port (just for info)
    frontend_url = get_codespace_url(PORT_FRONTEND)
    backend_url = get_codespace_url(PORT_BACKEND)

    print(f"\n{Colors.GREEN}🚀 READY FOR LAUNCH.{Colors.ENDC}")
    print(f"{Colors.BLUE}ℹ️  The Reality Kernel will inhabit Port {PORT_BACKEND}.{Colors.ENDC}")

    # Write URLs to a file for other scripts to use if needed
    with open(".magic_urls", "w") as f:
        f.write(f"BACKEND={backend_url}\n")
        f.write(f"FRONTEND={frontend_url}\n")

    print(f"\n{Colors.BOLD}🌐 ACCESS PORTALS:{Colors.ENDC}")
    print(f"{Colors.CYAN}   👉 Backend (API/Docs): {Colors.UNDERLINE}{backend_url}{Colors.ENDC}")
    print(f"{Colors.CYAN}   👉 Frontend (UI):      {Colors.UNDERLINE}{frontend_url}{Colors.ENDC}")
    print(f"{Colors.HEADER}--------------------------------------------------{Colors.ENDC}")


if __name__ == "__main__":
    main()
