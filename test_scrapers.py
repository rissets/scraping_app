#!/usr/bin/env python3
"""
Test script for the improved scrapers.
"""
import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.scraper import search_news, scrapers
from app.models.schemas import NewsCategory


async def test_scrapers():
    """Test all scrapers with a sample query."""
    query = "AI technology"
    print(f"Testing scrapers with query: '{query}'")
    print("=" * 50)
    
    # Test individual scrapers
    for source_name, scraper in scrapers.items():
        print(f"\nTesting {source_name}:")
        print("-" * 30)
        try:
            results = await scraper.search(query, limit=3)
            print(f"Results: {len(results)}")
            
            for i, result in enumerate(results, 1):
                print(f"{i}. {result.title}")
                print(f"   URL: {result.link}")
                print(f"   Source: {result.source_name}")
                print(f"   Snippet: {result.snippet[:100]}...")
                print()
                
        except Exception as e:
            print(f"Error: {str(e)}")
    
    # Test combined search
    print("\n" + "=" * 50)
    print("Testing combined search:")
    print("-" * 30)
    
    try:
        all_results = await search_news(query, limit=5)
        print(f"Total results: {len(all_results)}")
        
        for i, result in enumerate(all_results, 1):
            print(f"{i}. {result.title}")
            print(f"   URL: {result.link}")
            print(f"   Source: {result.source_name}")
            print()
            
    except Exception as e:
        print(f"Error in combined search: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_scrapers())
