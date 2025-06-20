#!/usr/bin/env python3
"""
Standalone Processor for AI Catch-up Scraping
Works without Gemini API key - focuses on scraping and validation only
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Ensure we're working in the correct directory
script_dir = Path(__file__).parent.absolute()
os.chdir(script_dir)
sys.path.insert(0, str(script_dir))

try:
    from src.config import config, get_status_values
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
        logging.FileHandler('standalone_processor.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class StandaloneProcessor:
    """Standalone processor that works without external APIs."""
    
    def __init__(self):
        """Initialize standalone processor."""
        try:
            self.scraper = UnifiedScraper()
            self.STATUS = get_status_values()
            self.processing_config = config.get("processing", default={})
            logger.info("Standalone processor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            raise

    def process_urls(self, urls: List[str]) -> List[Dict]:
        """Process a list of URLs and return results with validation."""
        results = []
        
        logger.info(f"Processing {len(urls)} URLs...")
        
        for i, url in enumerate(urls, 1):
            logger.info(f"[{i}/{len(urls)}] Processing: {url}")
            
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
                    
                    if validation['is_valid']:
                        logger.info(f"✓ SUCCESS: {len(content)} chars, confidence: {validation['confidence_score']:.2f}")
                    else:
                        logger.warning(f"✗ VALIDATION FAILED: {', '.join(validation['issues'])}")
                        result['error'] = f"Validation failed: {', '.join(validation['issues'])}"
                else:
                    result['error'] = "No content returned from scraper"
                    logger.warning("✗ No content returned")
                    
            except Exception as e:
                error_msg = str(e)
                result['error'] = error_msg
                logger.error(f"✗ ERROR: {error_msg}")
            
            results.append(result)
            
            # Add delay between requests
            delay = self.processing_config.get('request_delay', 1)
            if i < len(urls):  # Don't delay after last request
                time.sleep(delay)
        
        return results
    
    def generate_report(self, results: List[Dict]) -> str:
        """Generate a summary report of processing results."""
        total = len(results)
        successful = sum(1 for r in results if r['success'])
        failed = total - successful
        
        report = [
            "=" * 60,
            "STANDALONE PROCESSING REPORT",
            "=" * 60,
            f"Total URLs processed: {total}",
            f"Successful: {successful} ({successful/total*100:.1f}%)",
            f"Failed: {failed} ({failed/total*100:.1f}%)",
            "",
            "DETAILED RESULTS:",
            "-" * 40
        ]
        
        for i, result in enumerate(results, 1):
            status = "✓ SUCCESS" if result['success'] else "✗ FAILED"
            report.append(f"{i:2d}. {status} - {result['url']}")
            
            if result['success']:
                report.append(f"    Content: {result['content_length']} chars")
                report.append(f"    Confidence: {result['validation']['confidence_score']:.2f}")
            else:
                report.append(f"    Error: {result['error']}")
            report.append("")
        
        return "\n".join(report)


def demo_mode():
    """Run a quick demonstration with sample URLs."""
    print("🚀 DEMO MODE - Standalone Processor")
    print("=" * 50)
    
    sample_urls = [
        "https://arxiv.org/abs/2501.00001",  # arXiv test
        "https://www.nature.com/articles/d41586-024-00001-0",  # Nature test
        "https://example.com/test-page"  # General test
    ]
    
    processor = StandaloneProcessor()
    results = processor.process_urls(sample_urls)
    
    print("\n" + processor.generate_report(results))
    
    return results


def interactive_mode():
    """Interactive mode for custom URL processing."""
    print("🔧 INTERACTIVE MODE - Custom URL Processing")
    print("=" * 50)
    print("Enter URLs to process (one per line, empty line to finish):")
    
    urls = []
    while True:
        url = input(f"URL {len(urls)+1}: ").strip()
        if not url:
            break
        urls.append(url)
    
    if not urls:
        print("No URLs provided.")
        return
    
    processor = StandaloneProcessor()
    results = processor.process_urls(urls)
    
    print("\n" + processor.generate_report(results))
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"standalone_results_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        import json
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed results saved to: {output_file}")
    
    return results


def main():
    """Main function with mode selection."""
    print("🌟 AI Catch-up Scraping - Standalone Processor")
    print("=" * 60)
    print("This mode works without authentication and focuses on")
    print("scraping and validation testing only.")
    print()
    
    print("Select mode:")
    print("1. Demo mode (test with sample URLs)")
    print("2. Interactive mode (enter custom URLs)")
    print("3. Exit")
    
    while True:
        try:
            choice = input("\nChoice (1-3): ").strip()
            
            if choice == "1":
                demo_mode()
                break
            elif choice == "2":
                interactive_mode()
                break
            elif choice == "3":
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
                
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            break
        except Exception as e:
            print(f"Error: {e}")
            logger.error(f"Unexpected error in main: {e}")


if __name__ == "__main__":
    main()