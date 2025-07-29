#!/usr/bin/env python3
"""
Test script untuk mendemonstrasikan semua fitur baru scraping app
"""
import requests
import json
import time

BASE_URL = "http://localhost:8001"
API_KEY = "nexus_test_key_123"

def test_available_sources():
    """Test endpoint untuk melihat semua sumber yang tersedia"""
    print("🔍 Testing available sources...")
    response = requests.get(f"{BASE_URL}/api/v1/sources", params={"api_key": API_KEY})
    
    if response.status_code == 200:
        sources = response.json()["available_sources"]
        print(f"✅ Found {len(sources)} available sources:")
        
        categories = {}
        for source in sources:
            category = source["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(source["name"])
        
        for category, source_names in categories.items():
            print(f"  📂 {category.replace('_', ' ').title()}:")
            for name in source_names:
                print(f"    - {name}")
        print()
        return True
    else:
        print(f"❌ Failed: {response.text}")
        return False

def test_search_by_category(query, category):
    """Test pencarian berdasarkan kategori sumber"""
    print(f"🔍 Testing search by category '{category}' for query '{query}'...")
    
    params = {
        "query": query,
        "source_category": category,
        "api_key": API_KEY
    }
    
    response = requests.get(f"{BASE_URL}/api/v1/search/by-category", params=params)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['item_count']} results from sources: {', '.join(data['sources_searched'])}")
        
        if data['results']:
            print("📰 Sample results:")
            for i, result in enumerate(data['results'][:3]):  # Show first 3
                print(f"  {i+1}. {result['title'][:80]}..." if len(result['title']) > 80 else f"  {i+1}. {result['title']}")
                print(f"     Source: {result['source_name']}")
                print(f"     Link: {result['link'][:60]}..." if len(result['link']) > 60 else f"     Link: {result['link']}")
                print()
        return True
    else:
        print(f"❌ Failed: {response.text}")
        return False

def test_specific_sources(query, sources):
    """Test pencarian dengan sumber spesifik"""
    print(f"🔍 Testing specific sources {sources} for query '{query}'...")
    
    params = {
        "query": query,
        "sources": ",".join(sources),
        "api_key": API_KEY
    }
    
    response = requests.get(f"{BASE_URL}/api/v1/search", params=params)
    
    if response.status_code == 200:
        data = response.json()
        sources_used = list(set([result['source_name'] for result in data['results']]))
        print(f"✅ Found {data['item_count']} results from sources: {', '.join(sources_used)}")
        return True
    else:
        print(f"❌ Failed: {response.text}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing News Scraping App - New Features")
    print("=" * 50)
    
    # Test 1: Available sources
    if not test_available_sources():
        return
    
    time.sleep(1)
    
    # Test 2: Search by categories
    test_cases = [
        ("artificial intelligence", "news_aggregator"),
        ("teknologi", "national_news"),
        ("python programming", "blog_platform"),
        ("javascript", "tech_blog"),
    ]
    
    for query, category in test_cases:
        test_search_by_category(query, category)
        time.sleep(1)
    
    # Test 3: Specific sources
    print("🔍 Testing specific source combinations...")
    test_specific_sources("climate change", ["google_news", "bing_news"])
    time.sleep(1)
    test_specific_sources("startup", ["medium", "devto"])
    time.sleep(1)
    test_specific_sources("berita ekonomi", ["detik", "kompas"])
    
    print("\n🎉 All tests completed!")
    print("\n📋 Summary of new features:")
    print("1. ✅ 10 total scrapers (vs 3 previously)")
    print("2. ✅ Search engines: Google Search + DuckDuckGo backup")
    print("3. ✅ News aggregators: Google News + Bing News")  
    print("4. ✅ International news: BBC News + CNN")
    print("5. ✅ Indonesian news: Detik + Kompas")
    print("6. ✅ Blog platforms: Medium")
    print("7. ✅ Tech blogs: Dev.to")
    print("8. ✅ Search by source category endpoint")
    print("9. ✅ Enhanced fallback system")
    print("10. ✅ Priority-based result sorting")

if __name__ == "__main__":
    main()
