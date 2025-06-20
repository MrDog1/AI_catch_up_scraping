#!/usr/bin/env python3
"""
Base Scraper Classes for AI Catch-up Scraping
Unified scraping functionality with specialized handlers
"""

import os
import sys
import urllib.request
import urllib.parse
import re
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from abc import ABC, abstractmethod
from pathlib import Path

# Ensure we're working in the correct directory when imported
script_dir = Path(__file__).parent.parent.absolute()  # Go up to project root
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))
if os.getcwd() != str(script_dir):
    os.chdir(script_dir)

from src.config import config, get_status_values

# Set up logging
log_config = config.get("logging", default={})
log_level = getattr(logging, log_config.get("level", "INFO"))
log_format = '%(asctime)s - %(levelname)s - %(message)s'

# Configure logging to both console and file
logging.basicConfig(
    level=log_level,
    format=log_format,
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler(log_config.get("file", "scraping.log"), encoding='utf-8')  # File output
    ]
)
logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""
    
    def __init__(self):
        """Initialize base scraper."""
        self.STATUS = get_status_values()
        self.session_config = config.get("scraping", default={})
        self.processing_config = config.get("processing", default={})
        
        # Create opener with headers
        self.opener = urllib.request.build_opener()
        user_agent = self.session_config.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        self.opener.addheaders = [
            ('User-Agent', user_agent),
            ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'),
            ('Accept-Language', 'en-US,en;q=0.5'),
            ('Connection', 'keep-alive'),
        ]
    
    @abstractmethod
    def scrape(self, url: str) -> str:
        """Scrape content from URL. Must be implemented by subclasses."""
        pass
    
    def is_skip_domain(self, url: str) -> bool:
        """Check if URL should be skipped based on domain."""
        skip_domains = self.session_config.get("skip_domains", [])
        return any(domain in url for domain in skip_domains)
    
    def clean_text(self, text: str) -> str:
        """Clean extracted text."""
        if not text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]*>', ' ', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()


class UnifiedScraper:
    """Unified scraper that handles multiple URL types."""
    
    def __init__(self):
        """Initialize unified scraper."""
        self.session_config = config.get("scraping", default={})
        self.processing_config = config.get("processing", default={})
        logger.info("UnifiedScraper initialized")
    
    def scrape_url(self, url: str) -> str:
        """Main scraping method that routes to appropriate handler."""
        try:
            logger.info(f"Processing URL: {url}")
            
            # Basic validation
            if not url or not url.startswith(('http://', 'https://')):
                logger.warning(f"Invalid URL format: {url}")
                return ""
            
            # Check skip domains
            skip_domains = self.session_config.get("skip_domains", [])
            if any(domain in url.lower() for domain in skip_domains):
                logger.info(f"Skipping domain: {url}")
                return self.session_config.get("pdf_placeholder", "[Skipped Domain]")
            
            # Route to appropriate handler based on URL pattern
            if 'arxiv.org' in url.lower():
                return self._scrape_arxiv(url)
            elif 'researchgate.net' in url.lower():
                return self._scrape_researchgate(url)
            else:
                return self._scrape_general(url)
                
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return ""
    
    def _scrape_arxiv(self, url: str) -> str:
        """Enhanced arXiv scraper."""
        try:
            logger.info(f"[ARXIV] Processing: {url}")
            
            # Extract paper ID
            paper_id_match = re.search(r'arxiv\.org/(?:pdf|abs)/([0-9]{4}\.[0-9]{4,5})', url)
            if not paper_id_match:
                logger.warning(f"[ARXIV] Could not extract paper ID from URL: {url}")
                return ""
            
            paper_id = paper_id_match.group(1)
            
            # Try multiple strategies
            strategies = [
                f"https://arxiv.org/abs/{paper_id}",  # Abstract page
                f"https://export.arxiv.org/abs/{paper_id}",  # Export mirror
                f"https://arxiv.org/pdf/{paper_id}.pdf"  # Direct PDF
            ]
            
            for strategy_url in strategies:
                try:
                    content = self._fetch_url_content(strategy_url)
                    if content and len(content) > 100:
                        logger.info(f"[ARXIV] Success with strategy: {strategy_url}")
                        return self._extract_arxiv_content(content, strategy_url)
                except Exception as e:
                    logger.debug(f"[ARXIV] Strategy failed {strategy_url}: {e}")
                    continue
            
            logger.warning(f"[ARXIV] All strategies failed for: {url}")
            return ""
            
        except Exception as e:
            logger.error(f"[ARXIV] Error processing {url}: {e}")
            return ""
    
    def _extract_arxiv_content(self, html_content: str, url: str) -> str:
        """Extract meaningful content from arXiv page."""
        try:
            # Look for title and abstract
            title_match = re.search(r'<h1[^>]*class="title"[^>]*>.*?<span[^>]*>(.+?)</span>', html_content, re.DOTALL | re.IGNORECASE)
            abstract_match = re.search(r'<blockquote[^>]*class="abstract"[^>]*>.*?<span[^>]*>Abstract:</span>\s*(.+?)</blockquote>', html_content, re.DOTALL | re.IGNORECASE)
            
            content_parts = []
            
            if title_match:
                title = re.sub(r'<[^>]*>', '', title_match.group(1)).strip()
                content_parts.append(f"Title: {title}")
            
            if abstract_match:
                abstract = re.sub(r'<[^>]*>', ' ', abstract_match.group(1))
                abstract = re.sub(r'\s+', ' ', abstract).strip()
                content_parts.append(f"Abstract: {abstract}")
            
            if content_parts:
                result = "\n\n".join(content_parts)
                logger.info(f"[ARXIV] Extracted {len(result)} characters")
                return result
            else:
                logger.warning(f"[ARXIV] Could not extract title/abstract from {url}")
                return ""
                
        except Exception as e:
            logger.error(f"[ARXIV] Content extraction error: {e}")
            return ""
    
    def _scrape_researchgate(self, url: str) -> str:
        """ResearchGate scraper."""
        try:
            logger.info(f"[RESEARCHGATE] Processing: {url}")
            content = self._fetch_url_content(url)
            
            if content:
                # Extract title and description
                title_match = re.search(r'<h1[^>]*>(.+?)</h1>', content, re.DOTALL | re.IGNORECASE)
                desc_match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', content, re.IGNORECASE)
                
                parts = []
                if title_match:
                    title = re.sub(r'<[^>]*>', '', title_match.group(1)).strip()
                    parts.append(f"Title: {title}")
                
                if desc_match:
                    desc = desc_match.group(1).strip()
                    parts.append(f"Description: {desc}")
                
                if parts:
                    return "\n\n".join(parts)
            
            logger.warning(f"[RESEARCHGATE] Could not extract content from {url}")
            return ""
            
        except Exception as e:
            logger.error(f"[RESEARCHGATE] Error processing {url}: {e}")
            return ""
    
    def _scrape_general(self, url: str) -> str:
        """General purpose scraper for other websites."""
        try:
            logger.info(f"[GENERAL] Processing: {url}")
            content = self._fetch_url_content(url)
            
            if content:
                # Extract basic content using simple heuristics
                # Look for title
                title_match = re.search(r'<title[^>]*>(.+?)</title>', content, re.DOTALL | re.IGNORECASE)
                
                # Look for meta description
                desc_match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', content, re.IGNORECASE)
                
                # Look for main content areas
                main_content = ""
                content_patterns = [
                    r'<main[^>]*>(.+?)</main>',
                    r'<article[^>]*>(.+?)</article>',
                    r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.+?)</div>'
                ]
                
                for pattern in content_patterns:
                    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
                    if match:
                        main_content = match.group(1)
                        break
                
                # Clean and combine content
                parts = []
                
                if title_match:
                    title = re.sub(r'<[^>]*>', '', title_match.group(1)).strip()
                    parts.append(f"Title: {title}")
                
                if desc_match:
                    desc = desc_match.group(1).strip()
                    parts.append(f"Description: {desc}")
                
                if main_content:
                    clean_content = re.sub(r'<[^>]*>', ' ', main_content)
                    clean_content = re.sub(r'\s+', ' ', clean_content).strip()
                    if len(clean_content) > 100:
                        parts.append(f"Content: {clean_content[:1000]}...")
                
                if parts:
                    result = "\n\n".join(parts)
                    logger.info(f"[GENERAL] Extracted {len(result)} characters")
                    return result
            
            logger.warning(f"[GENERAL] Could not extract meaningful content from {url}")
            return ""
            
        except Exception as e:
            logger.error(f"[GENERAL] Error processing {url}: {e}")
            return ""
    
    def _fetch_url_content(self, url: str) -> str:
        """Fetch raw content from URL with proper error handling."""
        try:
            opener = urllib.request.build_opener()
            user_agent = self.session_config.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            opener.addheaders = [('User-Agent', user_agent)]
            
            timeout = self.processing_config.get("timeout_seconds", 30)
            response = opener.open(url, timeout=timeout)
            
            # Handle encoding
            content = response.read()
            
            # Try to decode with various encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    return content.decode(encoding)
                except UnicodeDecodeError:
                    continue
            
            # Fallback: decode with errors ignored
            return content.decode('utf-8', errors='ignore')
            
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            raise


class URLProcessor:
    """URL processor for type detection and validation."""
    
    def __init__(self):
        """Initialize URL processor."""
        pass
    
    def process_url(self, url: str) -> Dict:
        """Process URL and return metadata."""
        try:
            # Basic validation
            is_valid = bool(url and url.startswith(('http://', 'https://')))
            
            # Extract domain
            domain = ""
            if is_valid:
                try:
                    parsed = urllib.parse.urlparse(url)
                    domain = parsed.netloc
                except:
                    pass
            
            # Determine type
            url_type = "unknown"
            if 'arxiv.org' in url.lower():
                url_type = "arxiv"
            elif 'researchgate.net' in url.lower():
                url_type = "researchgate"
            elif url.lower().endswith('.pdf'):
                url_type = "pdf"
            else:
                url_type = "html"
            
            return {
                'url': url,
                'is_valid': is_valid,
                'domain': domain,
                'type': url_type
            }
            
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            return {
                'url': url,
                'is_valid': False,
                'error': str(e)
            }


if __name__ == "__main__":
    # Simple test
    scraper = UnifiedScraper()
    test_url = "https://arxiv.org/abs/2501.00001"
    print(f"Testing with: {test_url}")
    result = scraper.scrape_url(test_url)
    print(f"Result: {result[:200]}..." if result else "No result")