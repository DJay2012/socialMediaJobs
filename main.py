#!/usr/bin/env python3
"""
Social Media Jobs - Main Entry Point
Simple wrapper to run the main social media job runner
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import and run the main job runner
from socialMediaJobRunner import main

if __name__ == "__main__":
    main()
