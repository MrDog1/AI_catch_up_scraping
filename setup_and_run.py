#!/usr/bin/env python3
"""
AI Catch-up Scraping - Setup and Run
Unified script for setup, testing, and running the processor
"""

import os
import sys
import subprocess
import json
import webbrowser
from pathlib import Path

def run_authentication_setup():
    """Run interactive authentication setup."""
    print("\n🔑 Authentication Setup")
    print("-" * 40)
    
    print("Opening browser pages for setup...")
    try:
        webbrowser.open("https://console.cloud.google.com/")
        webbrowser.open("https://aistudio.google.com/")
    except:
        pass
    
    print("\n📋 SETUP INSTRUCTIONS:")
    print("1. Google Sheets API:")
    print("   - Go to: https://console.cloud.google.com/")
    print("   - Create/select project")
    print("   - Enable Google Sheets API")
    print("   - Create Service Account credentials")
    print("   - Download JSON key file as 'Credential_ver3.json'")
    print("   - Share your Google Sheet with the service account email")
    
    print("\n2. Google Sheet ID:")
    print("   - Open your Google Sheet")
    print("   - Copy the ID from URL: docs.google.com/spreadsheets/d/[SHEET_ID]/")
    
    print("\n3. Gemini API (optional):")
    print("   - Go to: https://aistudio.google.com/")
    print("   - Get API key")
    print("   - Set environment variable: GEMINI_API_KEY")
    
    input("\nPress Enter when setup is complete...")
    
    # Verify setup after completion
    print("\n🔍 Verifying setup...")
    verify_authentication()

def verify_authentication():
    """Verify authentication setup."""
    try:
        from src.config import Config
        config = Config()
        
        sheet_id = config.get('google_sheets', 'sheet_id')
        credentials_path = config.get_credentials_path()
        gemini_key = config.get('api_keys', 'gemini_api_key')
        
        print(f" - Sheet ID: {'✅' if sheet_id and sheet_id != 'YOUR_GOOGLE_SHEET_ID_HERE' else '❌'}")
        print(f" - Credentials: {'✅' if credentials_path and os.path.exists(credentials_path) else '❌'}")
        print(f" - Gemini API: {'✅' if gemini_key else '⚠️  Not configured (optional)'}")
        
        return sheet_id and credentials_path and os.path.exists(credentials_path)
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

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
        
        if not all([sheet_id, Path(creds_path).exists()]):
            print("⚠ Authentication setup required...")
            setup_choice = input("Run authentication setup? (y/n): ").lower().strip()
            if setup_choice == 'y':
                run_authentication_setup()
            
    except Exception as e:
        print(f"⚠ Configuration test failed: {e}")
    
    print("\n[3/3] Starting processor...")
    return True

def run_processor():
    """Run the main processor."""
    try:
        from src.processor import main
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError running processor: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    # Setup environment first
    if setup_environment():
        # Then run the processor
        run_processor()
