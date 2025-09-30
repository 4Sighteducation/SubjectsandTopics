#!/usr/bin/env python
"""
Download AQA History A-Level specification PDF.
Saves to data/raw/AQA/specifications/
"""

import os
import sys
from pathlib import Path
import requests
from tqdm import tqdm

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import setup_logger
from utils.helpers import ensure_directory

def download_file(url: str, filepath: str) -> bool:
    """Download file with progress bar."""
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        # Ensure directory exists
        ensure_directory(os.path.dirname(filepath))
        
        # Download with progress bar
        with open(filepath, 'wb') as f, tqdm(
            desc=os.path.basename(filepath),
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for data in response.iter_content(chunk_size=1024):
                size = f.write(data)
                pbar.update(size)
        
        return True
        
    except Exception as e:
        print(f"Error downloading: {e}")
        return False


def main():
    logger = setup_logger('INFO', 'data/logs/download_spec.log')
    
    # AQA History A-Level specification PDF
    spec_url = "https://filestore.aqa.org.uk/resources/history/specifications/AQA-7042-SP-2015.PDF"
    
    # Output path
    output_dir = "data/raw/AQA/specifications"
    output_file = os.path.join(output_dir, "History_A-Level_7042.pdf")
    
    logger.info(f"Downloading AQA History A-Level specification...")
    logger.info(f"From: {spec_url}")
    logger.info(f"To: {output_file}")
    
    if Path(output_file).exists():
        overwrite = input(f"\nFile already exists at {output_file}\nOverwrite? (y/n): ")
        if overwrite.lower() != 'y':
            logger.info("Download cancelled")
            return 0
    
    success = download_file(spec_url, output_file)
    
    if success:
        size_mb = os.path.getsize(output_file) / (1024 * 1024)
        logger.info(f"\n✅ Download complete! ({size_mb:.2f} MB)")
        logger.info(f"Saved to: {output_file}")
        logger.info("\nNext step: Run test_aqa_history.py to extract data")
        return 0
    else:
        logger.error("\n❌ Download failed")
        return 1


if __name__ == '__main__':
    exit(main())
