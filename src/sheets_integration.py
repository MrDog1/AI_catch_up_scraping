#!/usr/bin/env python3
"""
Google Sheets Integration for AI Catch-up Scraping
Handles all Google Sheets operations with GAS compatibility
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Ensure we're working in the correct directory
script_dir = Path(__file__).parent.parent.absolute()
os.chdir(script_dir)
sys.path.insert(0, str(script_dir))

try:
    from google.auth.transport.requests import Request
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as e:
    print(f"Google API libraries not available: {e}")
    print("Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)

from src.config import config, get_column_mapping, get_status_values

# Setup logging
logger = logging.getLogger(__name__)


class GoogleSheetsService:
    """Google Sheets service with GAS-compatible operations."""
    
    def __init__(self):
        """Initialize Google Sheets service."""
        self.service = None
        self.sheet_id = config.get('google_sheets', 'sheet_id')
        self.credentials_path = config.get('google_sheets', 'credentials_path')
        self.COLUMNS = get_column_mapping()
        self.STATUS = get_status_values()
        
        if not self.sheet_id:
            raise ValueError("Google Sheet ID not configured")
        
        if not Path(self.credentials_path).exists():
            raise FileNotFoundError(f"Credentials file not found: {self.credentials_path}")
        
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Sheets API."""
        try:
            # Define the scope
            SCOPES = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive.readonly'
            ]
            
            # Load credentials
            credentials = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=SCOPES
            )
            
            # Build the service
            self.service = build('sheets', 'v4', credentials=credentials)
            
            logger.info("Successfully authenticated with Google Sheets API")
            
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Sheets: {e}")
            raise
    
    def get_error_urls(self, max_rows: int = None) -> List[Dict]:
        """Get URLs from Error sheet that need processing."""
        try:
            if max_rows is None:
                max_rows = config.get('processing', 'rows_per_exec', default=15)
            
            # Read Error sheet
            range_name = f"Error!A:K"  # Read all columns A through K
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                logger.info("Error sheet is empty")
                return []
            
            # Skip header row if it exists
            data_rows = values[1:] if len(values) > 1 else []
            
            error_urls = []
            
            for row_idx, row in enumerate(data_rows, start=2):  # Start from row 2 (after header)
                # Ensure row has enough columns
                while len(row) < 11:
                    row.append('')
                
                # Check if this row needs processing
                final_url = row[self.COLUMNS['FINAL_URL'] - 1] if len(row) >= self.COLUMNS['FINAL_URL'] else ''
                status = row[self.COLUMNS['STATUS'] - 1] if len(row) >= self.COLUMNS['STATUS'] else ''
                
                # Process if URL exists and status is empty or ERROR
                if final_url and (not status or status == self.STATUS['ERROR']):
                    error_urls.append({
                        'row_index': row_idx,
                        'url': final_url,
                        'timestamp': row[self.COLUMNS['TIMESTAMP'] - 1] if len(row) >= self.COLUMNS['TIMESTAMP'] else '',
                        'content': row[self.COLUMNS['CONTENT'] - 1] if len(row) >= self.COLUMNS['CONTENT'] else '',
                        'error_status': row[self.COLUMNS['ERROR_STATUS'] - 1] if len(row) >= self.COLUMNS['ERROR_STATUS'] else '',
                        'row_data': row
                    })
                
                # Limit to max_rows
                if len(error_urls) >= max_rows:
                    break
            
            logger.info(f"Found {len(error_urls)} URLs to process in Error sheet")
            return error_urls
            
        except HttpError as e:
            logger.error(f"HTTP error accessing Error sheet: {e}")
            raise
        except Exception as e:
            logger.error(f"Error reading Error sheet: {e}")
            raise
    
    def move_to_main_sheet(self, url_data: Dict, result: Dict):
        """Move successfully processed URL from Error to Main sheet."""
        try:
            # Prepare row data for Main sheet
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            new_row = [
                timestamp,  # A: Timestamp
                url_data['url'],  # B: Final URL
                result['content'][:1000] if result.get('content') else '',  # C: Content (truncated)
                self.STATUS['DONE'],  # D: Status
                '',  # E: Error Status
                '',  # F: Keywords
                '',  # G: Flow Status
                '',  # H: Terms
                '',  # I: Genre
                f"Processed: {timestamp}",  # J: History
                result['validation'].get('content_type', 'text') if result.get('validation') else 'text'  # K: Type
            ]
            
            # Append to Main sheet
            self.service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range="Main!A:K",
                valueInputOption="RAW",
                body={'values': [new_row]}
            ).execute()
            
            # Remove from Error sheet
            self._delete_error_row(url_data['row_index'])
            
            logger.info(f"Successfully moved URL to Main sheet: {url_data['url']}")
            
        except Exception as e:
            logger.error(f"Error moving URL to Main sheet: {e}")
            raise
    
    def update_error_sheet(self, url_data: Dict, result: Dict):
        """Update Error sheet with processing result."""
        try:
            # Update the error status and timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            error_message = result.get('error', 'Processing failed')
            
            # Prepare update data
            updates = [
                {
                    'range': f"Error!A{url_data['row_index']}",
                    'values': [[timestamp]]
                },
                {
                    'range': f"Error!D{url_data['row_index']}",
                    'values': [[self.STATUS['ERROR']]]
                },
                {
                    'range': f"Error!E{url_data['row_index']}",
                    'values': [[error_message[:500]]]  # Truncate error message
                }
            ]
            
            # Batch update
            self.service.spreadsheets().values().batchUpdate(
                spreadsheetId=self.sheet_id,
                body={
                    'valueInputOption': 'RAW',
                    'data': updates
                }
            ).execute()
            
            logger.info(f"Updated Error sheet for URL: {url_data['url']}")
            
        except Exception as e:
            logger.error(f"Error updating Error sheet: {e}")
            raise
    
    def _delete_error_row(self, row_index: int):
        """Delete a row from Error sheet."""
        try:
            # Delete the row
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.sheet_id,
                body={
                    'requests': [{
                        'deleteDimension': {
                            'range': {
                                'sheetId': self._get_sheet_id('Error'),
                                'dimension': 'ROWS',
                                'startIndex': row_index - 1,  # 0-based index
                                'endIndex': row_index
                            }
                        }
                    }]
                }
            ).execute()
            
            logger.debug(f"Deleted row {row_index} from Error sheet")
            
        except Exception as e:
            logger.error(f"Error deleting row from Error sheet: {e}")
            raise
    
    def _get_sheet_id(self, sheet_name: str) -> int:
        """Get the internal sheet ID for a given sheet name."""
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.sheet_id
            ).execute()
            
            for sheet in spreadsheet['sheets']:
                if sheet['properties']['title'] == sheet_name:
                    return sheet['properties']['sheetId']
            
            raise ValueError(f"Sheet '{sheet_name}' not found")
            
        except Exception as e:
            logger.error(f"Error getting sheet ID for '{sheet_name}': {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test the connection to Google Sheets."""
        try:
            # Try to get spreadsheet metadata
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.sheet_id
            ).execute()
            
            logger.info(f"Successfully connected to spreadsheet: {spreadsheet.get('properties', {}).get('title', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")
            return False


def test_sheets_integration():
    """Test function for Google Sheets integration."""
    print("Testing Google Sheets Integration")
    print("=" * 40)
    
    try:
        service = GoogleSheetsService()
        
        # Test connection
        if service.test_connection():
            print("✅ Connection successful")
            
            # Test reading Error sheet
            error_urls = service.get_error_urls(max_rows=5)
            print(f"✅ Found {len(error_urls)} URLs in Error sheet")
            
            for i, url_data in enumerate(error_urls, 1):
                print(f"  {i}. {url_data['url']}")
        else:
            print("❌ Connection failed")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    test_sheets_integration()