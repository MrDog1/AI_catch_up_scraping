#!/usr/bin/env python3
"""
Minimal Test for Enhanced System
Tests the improved components without dependencies
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

try:
    from src.scraper_base import UnifiedScraper, URLProcessor
    from src.llm_response_validator import validate_llm_response
    print("✅ Successfully imported enhanced modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_arxiv_scraping():
    """Test arXiv scraping with real URLs from Error.csv"""
    print("\n🧪 Testing Enhanced arXiv Scraping")
    print("=" * 50)
    
    # Test URLs that previously failed in Error.csv
    test_urls = [
        "https://arxiv.org/pdf/2506.09954",
        "https://arxiv.org/pdf/2504.04749", 
        "https://arxiv.org/abs/2505.05074",
        "https://arxiv.org/pdf/2503.16405",
        "https://arxiv.org/pdf/2504.08107"
    ]
    
    scraper = UnifiedScraper()
    results = []
    
    for i, url in enumerate(test_urls, 1):
        print(f"\nTest {i}: {url}")
        
        try:
            content = scraper.scrape_url(url)
            
            if content and len(content) > 100:
                print(f"✅ SUCCESS: {len(content)} characters")
                print(f"📝 Preview: {content[:100]}...")
                
                # Test validation
                validation = validate_llm_response(content, url)
                print(f"🔍 Validation: {'PASSED' if validation['is_valid'] else 'FAILED'}")
                
                results.append({
                    'url': url,
                    'success': True,
                    'length': len(content),
                    'validation': validation
                })
            else:
                print(f"❌ FAILED: {content[:50] if content else 'No content'}")
                results.append({
                    'url': url,
                    'success': False,
                    'error': content or 'No content returned'
                })
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)[:100]}")
            results.append({
                'url': url,
                'success': False,
                'error': str(e)
            })
    
    # Summary
    success_count = sum(1 for r in results if r.get('success', False))
    print(f"\n📊 Summary: {success_count}/{len(test_urls)} successful")
    print(f"🎯 Success rate: {success_count/len(test_urls)*100:.1f}%")
    
    return results

def test_validation_system():
    """Test the LLM response validation system"""
    print("\n🔍 Testing Validation System")
    print("=" * 50)
    
    test_cases = [
        {
            'content': 'This is a normal article about machine learning and AI research.',
            'url': 'https://example.com/article',
            'expected': True
        },
        {
            'content': '本文が取得できませんでした',
            'url': 'https://example.com/error',
            'expected': False
        },
        {
            'content': 'Error 404: Page not found',
            'url': 'https://example.com/404',
            'expected': False
        },
        {
            'content': '很抱歉，无法获取页面内容',
            'url': 'https://example.com/chinese-error',
            'expected': False
        },
        {
            'content': 'A' * 50,  # Very short content
            'url': 'https://example.com/short',
            'expected': False
        }
    ]
    
    correct_validations = 0
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {'Valid' if case['expected'] else 'Invalid'} content")
        print(f"Content: {case['content'][:50]}...")
        
        validation = validate_llm_response(case['content'], case['url'])
        is_correct = validation['is_valid'] == case['expected']
        
        print(f"Result: {'✅ CORRECT' if is_correct else '❌ INCORRECT'}")
        print(f"Expected: {case['expected']}, Got: {validation['is_valid']}")
        print(f"Confidence: {validation['confidence_score']:.2f}")
        print(f"Issues: {', '.join(validation['issues']) if validation['issues'] else 'None'}")
        
        if is_correct:
            correct_validations += 1
    
    accuracy = correct_validations / len(test_cases) * 100
    print(f"\n🎯 Validation Accuracy: {accuracy:.1f}% ({correct_validations}/{len(test_cases)})")
    
    return accuracy

def test_url_processor():
    """Test URL processing and type detection"""
    print("\n🌐 Testing URL Processing")
    print("=" * 50)
    
    test_urls = [
        "https://arxiv.org/pdf/2506.09954",
        "https://www.nature.com/articles/s41586-024-07092-x",
        "https://example.com/test-page",
        "https://researchgate.net/publication/123456789",
        "invalid-url"
    ]
    
    processor = URLProcessor()
    
    for url in test_urls:
        print(f"\nProcessing: {url}")
        
        try:
            result = processor.process_url(url)
            print(f"Type: {result.get('type', 'Unknown')}")
            print(f"Domain: {result.get('domain', 'Unknown')}")
            print(f"Valid: {'✅' if result.get('is_valid', False) else '❌'}")
            
            if result.get('content'):
                print(f"Content: {len(result['content'])} characters")
                
        except Exception as e:
            print(f"Error: {str(e)[:100]}")

def main():
    """Run all tests"""
    print("🚀 AI Catch-up Scraping - Enhanced System Test")
    print("=" * 60)
    
    try:
        # Test 1: arXiv scraping improvements
        arxiv_results = test_arxiv_scraping()
        
        # Test 2: Validation system
        validation_accuracy = test_validation_system()
        
        # Test 3: URL processing
        test_url_processor()
        
        # Overall assessment
        print("\n🏆 OVERALL ASSESSMENT")
        print("=" * 60)
        
        arxiv_success_rate = sum(1 for r in arxiv_results if r.get('success', False)) / len(arxiv_results) * 100
        
        print(f"📈 arXiv Success Rate: {arxiv_success_rate:.1f}%")
        print(f"🔍 Validation Accuracy: {validation_accuracy:.1f}%")
        
        if arxiv_success_rate >= 80 and validation_accuracy >= 80:
            print("\n🎉 SYSTEM STATUS: EXCELLENT")
            print("   Ready for production use!")
        elif arxiv_success_rate >= 60 and validation_accuracy >= 70:
            print("\n✅ SYSTEM STATUS: GOOD")
            print("   Minor improvements may be beneficial.")
        else:
            print("\n⚠️  SYSTEM STATUS: NEEDS IMPROVEMENT")
            print("   Consider debugging failed test cases.")
            
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        
    print("\n✨ Test completed. Check logs for detailed information.")

if __name__ == "__main__":
    main()