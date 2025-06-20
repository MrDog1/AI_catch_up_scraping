#!/usr/bin/env python3
"""
LLM Response Validator for AI Catch-up Scraping
Validates scraped content to reduce false positive errors
"""

import re
import logging
from typing import Dict, List, Optional
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)


def validate_llm_response(content: str, url: str = "") -> Dict:
    """
    Validate LLM response content to detect false positives.
    
    Args:
        content: The content to validate
        url: Original URL (for context)
    
    Returns:
        Dict with validation results:
        {
            'is_valid': bool,
            'confidence_score': float,
            'issues': List[str],
            'content_type': str
        }
    """
    if not content:
        return {
            'is_valid': False,
            'confidence_score': 0.0,
            'issues': ['Empty content'],
            'content_type': 'empty'
        }
    
    content_lower = content.lower()
    issues = []
    confidence_factors = []
    
    # Check for obvious error patterns
    error_patterns = [
        # Japanese error patterns
        r'本文が取得できませんでした',
        r'アクセスできません',
        r'エラーが発生しました',
        r'ページが見つかりません',
        r'接続できません',
        
        # English error patterns
        r'could not.*fetch',
        r'unable to.*retrieve',
        r'failed to.*load',
        r'error.*occurred',
        r'page not found',
        r'access denied',
        r'connection.*failed',
        r'timeout.*error',
        r'404.*not found',
        r'500.*internal server error',
        r'503.*service unavailable',
        
        # Chinese error patterns
        r'无法获取',
        r'获取失败',
        r'连接失败',
        r'页面不存在',
        r'访问被拒绝',
    ]
    
    for pattern in error_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            issues.append(f"Error pattern detected: {pattern}")
            confidence_factors.append(-0.8)
    
    # Check content length
    if len(content) < 50:
        issues.append("Content too short")
        confidence_factors.append(-0.6)
    elif len(content) < 100:
        issues.append("Content very short")
        confidence_factors.append(-0.3)
    else:
        confidence_factors.append(0.2)
    
    # Check for meaningful content indicators
    positive_patterns = [
        r'abstract:?\s*[a-zA-Z]',
        r'title:?\s*[a-zA-Z]',
        r'introduction',
        r'conclusion',
        r'methodology',
        r'results',
        r'discussion',
        r'research',
        r'study',
        r'analysis',
        r'experiment'
    ]
    
    positive_matches = 0
    for pattern in positive_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            positive_matches += 1
    
    if positive_matches >= 3:
        confidence_factors.append(0.4)
    elif positive_matches >= 1:
        confidence_factors.append(0.2)
    else:
        confidence_factors.append(-0.1)
    
    # Check for HTML/XML artifacts
    html_pattern_count = len(re.findall(r'<[^>]+>', content))
    if html_pattern_count > 10:
        issues.append("Too many HTML tags")
        confidence_factors.append(-0.2)
    
    # Check for repeated characters/patterns
    if re.search(r'(.)\1{10,}', content):
        issues.append("Repeated character patterns")
        confidence_factors.append(-0.3)
    
    # Check for encoding issues
    if '�' in content or re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f]', content):
        issues.append("Encoding issues detected")
        confidence_factors.append(-0.2)
    
    # Calculate confidence score
    base_confidence = 0.5
    total_factor = sum(confidence_factors)
    confidence_score = max(0.0, min(1.0, base_confidence + total_factor))
    
    # Determine content type
    content_type = 'text'
    if 'arxiv.org' in url.lower():
        content_type = 'academic'
    elif any(word in content_lower for word in ['research', 'study', 'analysis']):
        content_type = 'research'
    elif any(word in content_lower for word in ['news', 'article', 'report']):
        content_type = 'news'
    
    # Final validation decision
    is_valid = confidence_score >= 0.3 and len(issues) <= 2
    
    # Special case: if there are critical error patterns, mark as invalid
    critical_errors = ['Error pattern detected', 'Content too short']
    if any(any(error in issue for error in critical_errors) for issue in issues):
        is_valid = False
    
    return {
        'is_valid': is_valid,
        'confidence_score': confidence_score,
        'issues': issues,
        'content_type': content_type,
        'length': len(content),
        'positive_indicators': positive_matches
    }


def batch_validate(contents: List[str], urls: List[str] = None) -> List[Dict]:
    """
    Validate multiple content pieces in batch.
    
    Args:
        contents: List of content strings to validate
        urls: Optional list of corresponding URLs
    
    Returns:
        List of validation results
    """
    if urls is None:
        urls = [""] * len(contents)
    
    results = []
    for content, url in zip(contents, urls):
        result = validate_llm_response(content, url)
        results.append(result)
    
    return results


def get_validation_summary(results: List[Dict]) -> Dict:
    """
    Get summary statistics from validation results.
    
    Args:
        results: List of validation results from validate_llm_response
    
    Returns:
        Summary statistics
    """
    if not results:
        return {'total': 0, 'valid': 0, 'invalid': 0, 'avg_confidence': 0.0}
    
    total = len(results)
    valid = sum(1 for r in results if r['is_valid'])
    invalid = total - valid
    avg_confidence = sum(r['confidence_score'] for r in results) / total
    
    # Most common issues
    all_issues = []
    for r in results:
        all_issues.extend(r['issues'])
    
    issue_counts = {}
    for issue in all_issues:
        issue_counts[issue] = issue_counts.get(issue, 0) + 1
    
    common_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        'total': total,
        'valid': valid,
        'invalid': invalid,
        'success_rate': valid / total if total > 0 else 0.0,
        'avg_confidence': avg_confidence,
        'common_issues': common_issues
    }


if __name__ == "__main__":
    # Test the validator
    test_cases = [
        "This is a research paper about machine learning algorithms and their applications in data science.",
        "本文が取得できませんでした",
        "Error 404: Page not found",
        "Title: Advanced AI Research\n\nAbstract: This study examines...",
        "A" * 30,  # Very short content
        ""  # Empty content
    ]
    
    print("Testing LLM Response Validator")
    print("=" * 40)
    
    for i, content in enumerate(test_cases, 1):
        result = validate_llm_response(content)
        print(f"\nTest {i}: {'VALID' if result['is_valid'] else 'INVALID'}")
        print(f"Content: {content[:50]}...")
        print(f"Confidence: {result['confidence_score']:.2f}")
        print(f"Issues: {', '.join(result['issues']) if result['issues'] else 'None'}")
    
    # Batch test
    batch_results = batch_validate(test_cases)
    summary = get_validation_summary(batch_results)
    
    print(f"\nBatch Summary:")
    print(f"Total: {summary['total']}")
    print(f"Valid: {summary['valid']}")
    print(f"Success Rate: {summary['success_rate']:.1%}")
    print(f"Average Confidence: {summary['avg_confidence']:.2f}")