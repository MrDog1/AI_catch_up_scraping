#!/usr/bin/env python3
"""
Configuration Management for AI Catch-up Scraping
Centralized configuration to handle sensitive data securely
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, Optional

# Ensure we're working in the correct directory when imported
script_dir = Path(__file__).parent.absolute()
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))
if os.getcwd() != str(script_dir):
    os.chdir(script_dir)

class Config:
    """Centralized configuration management."""
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize configuration."""
        self.config_file = Path(config_file)
        self.config_data = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from file or environment variables."""
        # Default configuration
        defaults = {
            "google_sheets": {
                "sheet_id": "",
                "credentials_path": "Credential_ver2.json"
            },
            "gmail": {
                "max_emails_per_run": 10,
                "search_days_back": 10,
                "auto_archive": True,
                "process_mode": "archive"  # "archive" or "delete"
            },
            "api_keys": {
                "gemini_api_key": "",
                "openai_api_key": ""
            },
            "processing": {
                "max_urls_per_batch": 20,
                "request_delay": 1,
                "timeout_seconds": 30,
                "max_retries": 3,
                "threads_per_exec": 5,
                "rows_per_exec": 15,
                "max_execution_time_minutes": 4
            },
            "scraping": {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "skip_domains": ["go.gale.com"],
                "pdf_placeholder": "[PDF Document - Content available but text extraction is limited]"
            },
            "logging": {
                "level": "INFO",
                "file": "scraping.log",
                "max_size_mb": 10
            }
        }
        
        # Load from file if exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                self.config_data = {**defaults, **file_config}
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Error loading config file: {e}")
                self.config_data = defaults
        else:
            self.config_data = defaults
        
        # Override with environment variables (for production/GitHub safety)
        self._load_from_environment()
    
    def _load_from_environment(self):
        """Load sensitive data from environment variables."""
        env_mappings = {
            "GOOGLE_SHEET_ID": ["google_sheets", "sheet_id"],
            "GOOGLE_CREDENTIALS_PATH": ["google_sheets", "credentials_path"],
            "GEMINI_API_KEY": ["api_keys", "gemini_api_key"],
            "OPENAI_API_KEY": ["api_keys", "openai_api_key"],
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                self._set_nested_value(config_path, value)
    
    def _set_nested_value(self, path: list, value):
        """Set a nested configuration value."""
        current = self.config_data
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
    
    def get(self, *path, default=None):
        """Get a configuration value using dot notation."""
        current = self.config_data
        try:
            for key in path:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, *path, value):
        """Set a configuration value using dot notation."""
        current = self.config_data
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
    
    def save_config(self, exclude_sensitive: bool = True):
        """Save configuration to file."""
        config_to_save = self.config_data.copy()
        
        if exclude_sensitive:
            # Don't save sensitive data to file
            if "api_keys" in config_to_save:
                config_to_save["api_keys"] = {
                    "gemini_api_key": "",
                    "openai_api_key": ""
                }
            if "google_sheets" in config_to_save and "sheet_id" in config_to_save["google_sheets"]:
                config_to_save["google_sheets"]["sheet_id"] = ""
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)
            print(f"Configuration saved to {self.config_file}")
        except IOError as e:
            print(f"Error saving config: {e}")
    
    def create_sample_config(self):
        """Create a sample configuration file."""
        sample_config = {
            "google_sheets": {
                "sheet_id": "YOUR_GOOGLE_SHEET_ID_HERE",
                "credentials_path": "Credential.json"
            },
            "api_keys": {
                "gemini_api_key": "YOUR_GEMINI_API_KEY_HERE",
                "openai_api_key": "YOUR_OPENAI_API_KEY_HERE"
            },
            "processing": {
                "max_urls_per_batch": 20,
                "request_delay": 1,
                "timeout_seconds": 30,
                "max_retries": 3
            },
            "scraping": {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "skip_domains": ["go.gale.com"],
                "pdf_placeholder": "[PDF Document - Content available but text extraction is limited]"
            },
            "logging": {
                "level": "INFO",
                "file": "scraping.log",
                "max_size_mb": 10
            }
        }
        
        sample_file = Path("config.sample.json")
        try:
            with open(sample_file, 'w', encoding='utf-8') as f:
                json.dump(sample_config, f, indent=2, ensure_ascii=False)
            print(f"Sample configuration created: {sample_file}")
            print("Copy this to config.json and fill in your credentials.")
        except IOError as e:
            print(f"Error creating sample config: {e}")
    
    def validate_config(self) -> Dict[str, bool]:
        """Validate that required configuration is present."""
        credentials_path = self.get("google_sheets", "credentials_path", default="Credential.json")
        validation = {
            "google_sheet_id": bool(self.get("google_sheets", "sheet_id")),
            "credentials_file": Path(credentials_path).exists() if credentials_path else False,
            "gemini_api_key": bool(self.get("api_keys", "gemini_api_key")),
        }
        
        validation["all_valid"] = all(validation.values())
        return validation
    
    def print_status(self):
        """Print configuration status."""
        validation = self.validate_config()
        
        print("Configuration Status:")
        print("=" * 40)
        print(f"Google Sheet ID: {'✓' if validation['google_sheet_id'] else '✗'}")
        print(f"Credentials file: {'✓' if validation['credentials_file'] else '✗'}")
        print(f"Gemini API key: {'✓' if validation['gemini_api_key'] else '✗'}")
        print(f"Overall: {'✓ READY' if validation['all_valid'] else '✗ INCOMPLETE'}")
        
        if not validation['all_valid']:
            print("\nTo fix:")
            if not validation['google_sheet_id']:
                print("- Set GOOGLE_SHEET_ID environment variable or add to config.json")
            if not validation['credentials_file']:
                credentials_path = self.get("google_sheets", "credentials_path", default="Credential.json")
                print(f"- Download Google credentials file to {credentials_path}")
            if not validation['gemini_api_key']:
                print("- Set GEMINI_API_KEY environment variable or add to config.json")

# Global configuration instance
config = Config()

def get_column_mapping():
    """Get the column mapping used throughout the application."""
    return {
        'TIMESTAMP': 1,      # A: 日付/タイムスタンプ
        'FINAL_URL': 2,      # B: リダイレクト後の最終URL
        'CONTENT': 3,        # C: 記事内容/要約
        'STATUS': 4,         # D: 処理ステータス
        'ERROR_STATUS': 5,   # E: 追加ステータス（エラー用）
        'KEYWORDS': 6,       # F: 抽出キーワード（該当する場合）
        'FLOW_STATUS': 7,    # G: 記事フローステータス
        'TERMS': 8,          # H: 説明付き抽出用語
        'GENRE': 9,          # I: ジャンル分類
        'HISTORY': 10,       # J: URL履歴/メタデータ
        'TYPE': 11           # K: URLタイプ（HTML、PDFなど）
    }

def get_status_values():
    """Get the status values used throughout the application."""
    return {
        'PENDING': "PENDING",
        'PROCESSING': "PROCESSING",
        'DONE': "DONE",
        'ERROR': "ERROR",
        'STEP1': "Step1/2",
        'ERROR_TEXT_FETCHING': "（本文が取得できませんでした）",
        'ERROR_SUMMARY': "（要約に失敗しました）"
    }

if __name__ == "__main__":
    # CLI for configuration management
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "status":
            config.print_status()
        elif command == "sample":
            config.create_sample_config()
        elif command == "validate":
            validation = config.validate_config()
            print(f"Configuration is {'valid' if validation['all_valid'] else 'invalid'}")
            sys.exit(0 if validation['all_valid'] else 1)
        else:
            print("Usage: python config.py [status|sample|validate]")
    else:
        config.print_status()