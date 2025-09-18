#!/usr/bin/env python3
"""
Test script for the search_similar_pairs tool
"""

import asyncio
import json
from search_similar_tool import search_similar_pairs, get_service_info, health_check

async def test_search_similar_pairs():
    """Test the search_similar_pairs function with sample data"""
    
    print("=" * 60)
    print("Testing Search Similar Pairs Tool")
    print("=" * 60)
    
    # First, let's check if the service is healthy
    print("\n1. Checking service health...")
    health_result = health_check()
    print(f"Health Check Result: {json.dumps(health_result, indent=2)}")
    
    # Get service info
    print("\n2. Getting service information...")
    service_info = get_service_info()
    print(f"Service Info: {json.dumps(service_info, indent=2)}")
    
    # Test the search function with your specific parameters
    print("\n3. Testing search_similar_pairs function...")
    print("-" * 40)
    
    test_params = {
        "user_input": "insurance guidelines",
        "target_language": "chinese",
        "top_k": 3
    }
    
    print(f"Test Parameters: {json.dumps(test_params, indent=2)}")
    print("\nExecuting search...")
    
    try:
        result = await search_similar_pairs(
            user_input=test_params["user_input"],
            target_language=test_params["target_language"],
            top_k=test_params["top_k"]
        )
        
        print("\n" + "=" * 60)
        print("SEARCH RESULTS:")
        print("=" * 60)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"📊 Query Language: {result['query_language']}")
            print(f"🎯 Target Language: {result['target_language']}")
            print(f"📈 Total Found: {result['total_found']}")
            print(f"🔍 Query: '{test_params['user_input']}'")
            
            if result['pairs']:
                print(f"\n📝 Top {len(result['pairs'])} Similar Translation Pairs:")
                print("-" * 50)
                
                for i, pair in enumerate(result['pairs'], 1):
                    print(f"\n{i}. Translation Pair #{pair['id']}")
                    print(f"   GL Number: {pair.get('gl_number', 'N/A')}")
                    print(f"   Row Number: {pair.get('row_number', 'N/A')}")
                    print(f"   Version: {pair.get('version', 'N/A')}")
                    print(f"   Effective Date: {pair.get('effective_date', 'N/A')}")
                    print(f"   🇺🇸 English: {pair['english_text']}")
                    print(f"   🇨🇳 Chinese: {pair['chinese_text']}")
                    print(f"   📅 Created: {pair['metadata'].get('created_at', 'N/A')}")
                    print("-" * 50)
            else:
                print("📭 No translation pairs found for the given query.")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_additional_queries():
    """Test with additional sample queries"""
    
    print("\n" + "=" * 60)
    print("TESTING ADDITIONAL QUERIES")
    print("=" * 60)
    
    additional_tests = [
        {
            "user_input": "payment terms",
            "target_language": "chinese", 
            "top_k": 2
        },
        {
            "user_input": "保险条款",  # Chinese text meaning "insurance terms"
            "target_language": "english",
            "top_k": 2
        }
    ]
    
    for i, test_case in enumerate(additional_tests, 1):
        print(f"\n{i}. Testing: '{test_case['user_input']}'")
        print("-" * 40)
        
        try:
            result = await search_similar_pairs(**test_case)
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
            else:
                print(f"Language: {result['query_language']} → {result['target_language']}")
                print(f"Found: {result['total_found']} pairs")
                
                for j, pair in enumerate(result['pairs'], 1):
                    print(f"  {j}. #{pair['id']}: {pair['english_text'][:50]}...")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Search Similar Pairs Tool Test")
    
    # Run the main test
    asyncio.run(test_search_similar_pairs())

    
    print("\n✅ Testing completed!")