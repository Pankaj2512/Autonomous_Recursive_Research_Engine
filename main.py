#!/usr/bin/env python3
"""Main entry point for Autonomous Recursive Research Engine (Prime Agent RLM)."""
from __future__ import annotations

import subprocess
import sys
from src.cli import run_cli

if __name__ == "__main__":
    try:
        if "--ui" in sys.argv:
            try:
                import streamlit
                subprocess.run(["streamlit", "run", "src/ui/dashboard.py"])
            except ImportError:
                print("Streamlit is not installed. Please install it with:\n    pip install streamlit")
                sys.exit(1)
        else:
            run_cli()
    except KeyboardInterrupt:
        print("\nResearch session cancelled by user.")
        sys.exit(0)
