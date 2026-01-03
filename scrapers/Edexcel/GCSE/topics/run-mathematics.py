"""
Mathematics Subject Runner
==========================

Runs Stage 1 and Stage 2 for Mathematics subject.

Usage:
    python run-mathematics.py
"""

import sys
import subprocess
from pathlib import Path

CONFIG_FILE = "configs/mathematics.yaml"

def main():
    script_dir = Path(__file__).parent
    
    print("=" * 80)
    print("MATHEMATICS SUBJECT SCRAPER")
    print("=" * 80)
    print(f"Config: {CONFIG_FILE}")
    print("=" * 80)
    print()
    
    config_path = script_dir / CONFIG_FILE
    
    if not config_path.exists():
        print(f"[ERROR] Config file not found: {config_path}")
        sys.exit(1)
    
    # Stage 1: Upload structure
    print("=" * 80)
    print("STAGE 1: Upload Structure")
    print("=" * 80)
    result1 = subprocess.run([
        sys.executable,
        str(script_dir / "universal-stage1-upload.py"),
        str(config_path)
    ])
    
    if result1.returncode != 0:
        print("\n[ERROR] Stage 1 failed!")
        sys.exit(1)
    
    print()
    print()
    
    # Stage 2: Extract PDF content (using custom Mathematics scraper)
    print("=" * 80)
    print("STAGE 2: Extract PDF Content (Mathematics Custom Scraper)")
    print("=" * 80)
    result2 = subprocess.run([
        sys.executable,
        str(script_dir / "mathematics-stage2-scrape.py"),
        str(config_path)
    ])
    
    if result2.returncode != 0:
        print("\n[ERROR] Stage 2 failed!")
        sys.exit(1)
    
    print()
    print()
    print("=" * 80)
    print("COMPLETE!")
    print("=" * 80)

if __name__ == '__main__':
    main()

