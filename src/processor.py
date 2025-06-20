#!/usr/bin/env python3
"""
Main Processor for AI Catch-up Scraping
Handles all processing modes with GAS compatibility
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Ensure we're working in the correct directory
script_dir = Path(__file__).parent.parent.absolute()
os.chdir(script_dir)
sys.path.insert(0, str(script_dir))

try:
    from src.config import config, get_status_values, get_column_mapping
    from src.scraper_base import UnifiedScraper
    from src.llm_response_validator import validate_llm_response
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('processor.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class AIProcessor:
    """Main processor class with multiple operation modes."""
    
    def __init__(self):
        """Initialize processor."""
        try:
            self.scraper = UnifiedScraper()
            self.STATUS = get_status_values()
            self.COLUMNS = get_column_mapping()
            self.processing_config = config.get("processing", default={})
            logger.info("AIProcessor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize processor: {e}")
            raise
    
    def process_urls_manual(self, urls: List[str]) -> List[Dict]:
        """Manual mode: Process custom URLs."""
        logger.info(f"Starting manual processing of {len(urls)} URLs")
        
        results = []
        for i, url in enumerate(urls, 1):
            logger.info(f"[{i}/{len(urls)}] Processing: {url}")
            
            result = self._process_single_url(url)
            results.append(result)
            
            # Add delay between requests
            delay = self.processing_config.get('request_delay', 1)
            if i < len(urls):
                time.sleep(delay)
        
        return results
    
    def process_semi_automated(self) -> str:
        """Semi-automated mode: Show processing instructions."""
        instructions = """
=== SEMI-AUTOMATED MODE ===

1. Copy URLs from your Error sheet
2. Paste them below (one per line)
3. Results will be displayed for manual copying

Enter URLs (empty line to finish):
        """
        
        print(instructions)
        
        urls = []
        while True:
            url = input(f"URL {len(urls)+1}: ").strip()
            if not url:
                break
            urls.append(url)
        
        if not urls:
            return "No URLs provided."
        
        results = self.process_urls_manual(urls)
        
        # Format results for copy-paste
        output = ["\n=== RESULTS FOR COPY-PASTE ==="]
        
        for i, result in enumerate(results, 1):
            output.append(f"\n--- URL {i} ---")
            output.append(f"Original URL: {result['url']}")
            output.append(f"Status: {'SUCCESS' if result['success'] else 'FAILED'}")
            
            if result['success']:
                output.append(f"Content: {result['content'][:500]}...")
                output.append(f"Validation: {result['validation']['confidence_score']:.2f}")
            else:
                output.append(f"Error: {result['error']}")
        
        return "\n".join(output)
    
    def process_error_sheet_gas_compatible(self) -> Dict:
        """GAS-compatible Error sheet processing mode."""
        logger.info("Starting GAS-compatible Error sheet processing")
        
        try:
            # Check if sheets integration is available
            from src.sheets_integration import GoogleSheetsService
            
            sheets_service = GoogleSheetsService()
            
            # Get URLs from Error sheet
            error_urls = sheets_service.get_error_urls()
            
            if not error_urls:
                logger.info("No URLs found in Error sheet")
                return {'processed': 0, 'successful': 0, 'failed': 0}
            
            # Limit processing based on GAS compatibility settings
            max_rows = self.processing_config.get('rows_per_exec', 15)
            urls_to_process = error_urls[:max_rows]
            
            logger.info(f"Processing {len(urls_to_process)} URLs from Error sheet")
            
            successful = 0
            failed = 0
            
            for url_data in urls_to_process:
                try:
                    result = self._process_single_url(url_data['url'])
                    
                    if result['success']:
                        # Move to Main sheet
                        sheets_service.move_to_main_sheet(url_data, result)
                        successful += 1
                        logger.info(f"✓ Moved to Main: {url_data['url']}")
                    else:
                        # Update Error sheet with error info
                        sheets_service.update_error_sheet(url_data, result)
                        failed += 1
                        logger.warning(f"✗ Updated Error: {url_data['url']}")
                        
                except Exception as e:
                    logger.error(f"Error processing {url_data['url']}: {e}")
                    failed += 1
                
                # Add delay between requests
                delay = self.processing_config.get('request_delay', 1)
                time.sleep(delay)
            
            return {
                'processed': len(urls_to_process),
                'successful': successful,
                'failed': failed
            }
            
        except ImportError:
            logger.error("Google Sheets integration not available. Check credentials.")
            return {'error': 'Sheets integration not available'}
        except Exception as e:
            logger.error(f"Error in GAS-compatible processing: {e}")
            return {'error': str(e)}
    
    def _process_single_url(self, url: str) -> Dict:
        """Process a single URL and return structured result."""
        result = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'content': '',
            'validation': {},
            'error': ''
        }
        
        try:
            # Scrape content
            content = self.scraper.scrape_url(url)
            
            if content:
                # Validate content
                validation = validate_llm_response(content, url)
                
                result.update({
                    'success': validation['is_valid'],
                    'content': content,
                    'validation': validation,
                    'content_length': len(content)
                })
                
                if not validation['is_valid']:
                    result['error'] = f"Validation failed: {', '.join(validation['issues'])}"
            else:
                result['error'] = "No content returned from scraper"
                
        except Exception as e:
            result['error'] = str(e)
        
        return result


def display_menu():
    """Display the main menu."""
    menu = """
🌟 AI Catch-up Scraping - Main Processor
======================================

Select processing mode:

1. Manual Mode - Process custom URLs
2. Semi-Automated Mode - Copy-paste workflow
3. Fully Automated Mode - Google Sheets integration
4. Error Sheet Processing (GAS Compatible) ⭐
5. Test Mode - Quick system test
6. Exit

Choice (1-6): """
    return input(menu).strip()


def main():
    """Main function with interactive menu."""
    print("🚀 Starting AI Catch-up Scraping Processor")
    print("==========================================")
    
    try:
        processor = AIProcessor()
        
        while True:
            choice = display_menu()
            
            if choice == "1":
                # Manual Mode
                print("\n📝 Manual Mode")
                print("Enter URLs to process (one per line, empty line to finish):")
                
                urls = []
                while True:
                    url = input(f"URL {len(urls)+1}: ").strip()
                    if not url:
                        break
                    urls.append(url)
                
                if urls:
                    results = processor.process_urls_manual(urls)
                    
                    # Display results
                    successful = sum(1 for r in results if r['success'])
                    print(f"\n📊 Results: {successful}/{len(results)} successful")
                    
                    for i, result in enumerate(results, 1):
                        status = "✓" if result['success'] else "✗"
                        print(f"{i}. {status} {result['url']}")
                        if not result['success']:
                            print(f"   Error: {result['error']}")
                else:
                    print("No URLs provided.")
            
            elif choice == "2":
                # Semi-Automated Mode
                output = processor.process_semi_automated()
                print(output)
            
            elif choice == "3":
                # Fully Automated Mode
                print("\n🔄 Fully Automated Mode")
                print("This mode requires Google Sheets integration.")
                
                result = processor.process_error_sheet_gas_compatible()
                if 'error' in result:
                    print(f"❌ Error: {result['error']}")
                else:
                    print(f"📊 Processed: {result['processed']}")
                    print(f"✅ Successful: {result['successful']}")
                    print(f"❌ Failed: {result['failed']}")
            
            elif choice == "4":
                # Error Sheet Processing (GAS Compatible)
                print("\n⭐ Error Sheet Processing (GAS Compatible)")
                print("Processing URLs from Error sheet...")
                
                result = processor.process_error_sheet_gas_compatible()
                if 'error' in result:
                    print(f"❌ Error: {result['error']}")
                else:
                    print(f"📊 Processed: {result['processed']}")
                    print(f"✅ Successful: {result['successful']}")
                    print(f"❌ Failed: {result['failed']}")
            
            elif choice == "5":
                # Test Mode
                print("\n🧪 Test Mode")
                test_urls = [
                    "https://arxiv.org/abs/2501.00001",
                    "https://example.com/test"
                ]
                
                results = processor.process_urls_manual(test_urls)
                successful = sum(1 for r in results if r['success'])
                print(f"Test completed: {successful}/{len(results)} successful")
            
            elif choice == "6":
                print("\n👋 Goodbye!")
                break
            
            else:
                print("\n❌ Invalid choice. Please select 1-6.")
            
            input("\nPress Enter to continue...")
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        logger.error(f"Unexpected error in main: {e}")


if __name__ == "__main__":
    main()