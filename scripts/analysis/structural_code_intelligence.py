#!/usr/bin/env python3
"""
Structural Code Intelligence - Deconstructed Wrapper
Forwarding to modular implementation in app.overmind.code_intelligence
"""

import sys
from pathlib import Path

# Ensure app is in path
sys.path.append(str(Path(__file__).parent.parent))

from app.overmind.code_intelligence.cli import main

if __name__ == "__main__":
    main()
