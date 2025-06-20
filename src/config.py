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
        # Always look for config.json in the parent directory (project root)
        if not Path(config_file).is_absolute():
            project_root = Path(__file__).parent.parent
            self.config_file = project_root / config_file
        else:
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
    
    def get_credentials_path(self):
        """Get the full path to credentials file."""
        credentials_path = self.get('google_sheets', 'credentials_path')
        if not credentials_path:
            return None
        
        # If relative path, resolve from project root
        if not os.path.isabs(credentials_path):
            project_root = Path(__file__).parent.parent
            return str(project_root / credentials_path)
        return credentials_path
    
    def create_sample_config(self):
        """Create a sample configuration file."""
        sample_config = {
            "google_sheets": {
                "sheet_id": "YOUR_GOOGLE_SHEET_ID_HERE",
                "credentials_path": "Credential_ver2.json"
            },
            "api_keys": {
                "gemini_api_key": "YOUR_GEMINI_API_KEY_HERE",
                "openai_api_key": "YOUR_OPENAI_API_KEY_HERE (optional)"
            },
            "processing": self.config_data.get("processing", {}),
            "scraping": self.config_data.get("scraping", {}),
            "logging": self.config_data.get("logging", {})
        }
        
        sample_path = self.config_file.parent / "config.sample.json"
        with open(sample_path, 'w', encoding='utf-8') as f:
            json.dump(sample_config, f, indent=2, ensure_ascii=False)
        print(f"Sample configuration created at: {sample_path}")


def get_status_values():
    """Get GAS-compatible status values."""
    return {
        "STATUS_TODO": "ToScrape",
        "STATUS_SCRAPED": "Scraped",
        "STATUS_ERROR": "Error",
        "STATUS_SUMMARIZED": "Summarized",
        "STATUS_NO_URL": "No URL",
        "STATUS_NO_CONTENT": "No Content",
        "STATUS_TIMEOUT": "Timeout",
        "STATUS_ARCHIVED": "Archived"
    }


# Create global config instance
config = Config()
