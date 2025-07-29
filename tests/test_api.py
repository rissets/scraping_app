#!/usr/bin/env python3
"""
Simple test script to verify the Nexus Aggregator API functionality.
"""

import requests
import json
import sys
from urllib.parse import urlencode

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "nexus_test_key_123"  # Default test API key
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


def test_health_check():
    """Test the health check endpoint."""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False


def test_search_endpoint():
    """Test the news search endpoint."""
    print("\n🔍 Testing news search...")
    try:
        params = {
            "query": "artificial intelligence",
            "sources": "google_news",
            "format": "json"
        }
        
        url = f"{BASE_URL}/api/v1/search?" + urlencode(params)
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Search endpoint passed")
            print(f"   Found {data.get('item_count', 0)} articles")
            
            # Show first result if available
            if data.get('results'):
                first_result = data['results'][0]
                print(f"   First result: {first_result.get('title', 'No title')}")
        else:
            print(f"❌ Search endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Search endpoint error: {str(e)}")
        return False


def test_scrape_endpoint():
    """Test the URL scraping endpoint."""
    print("\n🔍 Testing URL scraping...")
    try:
        payload = {
            "url": "https://example.com",
            "output_mode": "response"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/scrape-url",
            headers=HEADERS,
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Scrape endpoint passed")
            print(f"   Status: {data.get('status', 'unknown')}")
            
            if data.get('markdown_content'):
                content_preview = data['markdown_content'][:100] + "..." if len(data['markdown_content']) > 100 else data['markdown_content']
                print(f"   Content preview: {content_preview}")
        else:
            print(f"❌ Scrape endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Scrape endpoint error: {str(e)}")
        return False


def test_sources_endpoint():
    """Test the sources listing endpoint."""
    print("\n🔍 Testing sources endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/sources", headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Sources endpoint passed")
            sources = data.get('available_sources', [])
            print(f"   Available sources: {len(sources)}")
            for source in sources:
                print(f"   - {source.get('name', 'Unknown')}: {source.get('id', 'no-id')}")
        else:
            print(f"❌ Sources endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Sources endpoint error: {str(e)}")
        return False


def test_categories_endpoint():
    """Test the categories listing endpoint."""
    print("\n🔍 Testing categories endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/categories", headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Categories endpoint passed")
            categories = data.get('available_categories', [])
            print(f"   Available categories: {len(categories)}")
            for category in categories[:5]:  # Show first 5
                print(f"   - {category.get('name', 'Unknown')}")
        else:
            print(f"❌ Categories endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Categories endpoint error: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("🚀 Starting Nexus Aggregator API Tests")
    print(f"   Base URL: {BASE_URL}")
    print(f"   API Key: {API_KEY}")
    print("="*50)
    
    tests = [
        test_health_check,
        test_sources_endpoint,
        test_categories_endpoint,
        test_search_endpoint,
        test_scrape_endpoint
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        if test_func():
            passed += 1
    
    print("\n" + "="*50)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Check the server logs.")
        sys.exit(1)


if __name__ == "__main__":
    main()
