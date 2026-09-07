#!/usr/bin/env python3
"""Main entry point for Autonomous Recursive Research Engine (Prime Agent RLM)."""
from __future__ import annotations

import sys
from src.cli import run_cli

if __name__ == "__main__":
    try:
        run_cli()
    except KeyboardInterrupt:
        print("\nResearch session cancelled by user.")
        sys.exit(0)
