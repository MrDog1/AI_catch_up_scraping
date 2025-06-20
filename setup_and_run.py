#!/usr/bin/env python3
"""
AI Catch-up Scraping - Setup and Run
Unified script for setup, testing, and running the processor
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_environment():
    """Setup the environment and install dependencies."""
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    print("=== AI Catch-up Scraping Setup ===")
    print(f"Working directory: {script_dir}")
    
    # Install dependencies
    print("\n[1/3] Installing dependencies...")
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Dependencies installed successfully")
        else:
            print("⚠ Dependencies installation failed, but continuing...")
            print(result.stderr)
    except Exception as e:
        print(f"⚠ Could not install dependencies: {e}")
    
    # Test configuration
    print("\n[2/3] Testing configuration...")
    try:
        sys.path.insert(0, str(script_dir))
        from src.config import config
        
        sheet_id = config.get('google_sheets', 'sheet_id')
        creds_path = config.get('google_sheets', 'credentials_path')
        api_key = config.get('api_keys', 'gemini_api_key')
        
        print(f"Sheet ID: {'✓' if sheet_id else '✗'}")
        print(f"Credentials: {'✓' if Path(creds_path).exists() else '✗'}")
        print(f"Gemini API: {'✓' if api_key else '✗'}")
        
        if not all([sheet_id, Path(creds_path).exists(), api_key]):
            print("⚠ Some configuration is missing, but continuing...")
            
    except Exception as e:
        print(f"⚠ Configuration test failed: {e}")
    
    print("\n[3/3] Starting processor...")
    return True

def main():
    """Main function."""
    try:
        # Setup first
        if not setup_environment():
            input("Setup failed. Press Enter to exit...")
            return
        
        # Import and run processor
        script_dir = Path(__file__).parent.absolute()
        sys.path.insert(0, str(script_dir))
        
        # Import processor after setup
        from src.processor import main as processor_main
        
        # Run the processor
        processor_main()
        
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
    except ImportError as e:
        print(f"\n✗ Import error: {e}")
        print("Dependencies may not be installed correctly.")
        print("Try running: pip install -r requirements.txt")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()