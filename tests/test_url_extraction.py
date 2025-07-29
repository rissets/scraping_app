#!/usr/bin/env python3
"""
Test Google News URL extraction specifically.
"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.scraper import GoogleNewsScraper

def test_google_news_url_extraction():
    """Test Google News URL extraction with real examples."""
    scraper = GoogleNewsScraper()
    
    # Test URLs from the previous output
    test_urls = [
        "https://news.google.com/rss/articles/CBMiyAFBVV95cUxOa25lOUpxUklMdVQ4Wm11ZjA5RVBmeXkyeUdOQnBQYW01RVhHd19Mc3NwT3BqdVh6SkZ1RmRRdEUtdTJMVXdpeEpLMndFZ3JXdmlaUEVTOXRtUFM1ZXBVN3M1emkxZkV3MWQxUm95a0NMUEJHbkhoY1BZd0FDRlpRQi1QNElmMWhIM0xocTZDZDIxcHZPMlNJZnVONWxIUUwwakM0cVFyMENiRHRQTXd3VS04YVlKUHE1dWFONTVyRnZ2eGlVaEFYSA?oc=5&hl=en-ID&gl=ID&ceid=ID:en"
    ]
    
    print("Testing Google News URL extraction:")
    print("=" * 50)
    
    for i, url in enumerate(test_urls, 1):
        print(f"\nTest {i}:")
        print(f"Original: {url[:80]}...")
        
        extracted = scraper._extract_original_url_from_google_news(url)
        
        if extracted != url:
            print(f"✅ Extracted: {extracted}")
        else:
            print(f"❌ Failed - returned original URL")

if __name__ == "__main__":
    test_google_news_url_extraction()
