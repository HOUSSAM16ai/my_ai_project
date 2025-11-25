#!/usr/bin/env python3
"""
🔮 SUPERHUMAN ACCESS PORTAL 🔮
--------------------------------
This script manages the critical gateway to the Reality Kernel.
It handles URL generation with extreme prejudice and precision.
"""

import os
import socket
import sys
import time

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
    print(
        r"""
   _____                      _ ______
  / ____|                    (_)  ____|
 | |     ___   __ _ _ __  _   _| |__ ___  _ __ __ _  ___
 | |    / _ \ / _` | '_ \| | | |  __/ _ \| '__/ _` |/ _ \
 | |___| (_) | (_| | | | | |_| | | | (_) | | | (_| |  __/
  \_____\___/ \__, |_| |_|\__,_|_|  \___/|_|  \__, |\___|
               __/ |                           __/ |
              |___/                           |___/
    """
    )
    print(f"{Colors.CYAN}   >>> SUPERHUMAN ACCESS PROTOCOL INITIATED <<<{Colors.ENDC}")
    print(f"{Colors.HEADER}--------------------------------------------------{Colors.ENDC}")


def get_codespace_url(port):
    codespace_name = os.getenv("CODESPACE_NAME")
    domain = os.getenv("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN")

    if codespace_name and domain:
        return f"https://{codespace_name}-{port}.{domain}"
    return f"http://localhost:{port}"


def main():
    print_banner()

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
