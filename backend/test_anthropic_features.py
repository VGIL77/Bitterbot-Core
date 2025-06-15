#!/usr/bin/env python3
"""
Test script for new Anthropic features:
- thinking_budget_tokens 
- enable_native_web_search
"""

import asyncio
import os
from services.llm import make_llm_api_call
from utils.logger import logger

async def test_thinking_budget():
    """Test the new thinking_budget_tokens parameter"""
    logger.info("Testing thinking_budget_tokens...")
    
    messages = [
        {"role": "user", "content": "What is 2 + 2? Think about this step by step."}
    ]
    
    try:
        response = await make_llm_api_call(
            messages,
            "anthropic/claude-3-opus-latest",
            enable_thinking=True,
            thinking_budget_tokens=500,  # Using new API
            stream=False
        )
        
        logger.info("✅ thinking_budget_tokens test passed!")
        logger.info(f"Response: {response.choices[0].message.content[:100]}...")
        return True
    except Exception as e:
        logger.error(f"❌ thinking_budget_tokens test failed: {e}")
        return False

async def test_native_web_search():
    """Test the native web search feature"""
    logger.info("Testing enable_native_web_search...")
    
    messages = [
        {"role": "user", "content": "What is the latest news about Claude AI today?"}
    ]
    
    try:
        response = await make_llm_api_call(
            messages,
            "anthropic/claude-3-opus-latest", 
            enable_native_web_search=True,
            stream=False
        )
        
        logger.info("✅ enable_native_web_search test passed!")
        logger.info(f"Response: {response.choices[0].message.content[:100]}...")
        return True
    except Exception as e:
        logger.error(f"❌ enable_native_web_search test failed: {e}")
        return False

async def test_both_features():
    """Test both features together"""
    logger.info("Testing both features together...")
    
    messages = [
        {"role": "user", "content": "Search for the latest AI research papers and summarize the key findings. Think through this carefully."}
    ]
    
    try:
        response = await make_llm_api_call(
            messages,
            "anthropic/claude-3-opus-latest",
            enable_thinking=True,
            thinking_budget_tokens=1000,
            enable_native_web_search=True,
            stream=False
        )
        
        logger.info("✅ Combined features test passed!")
        logger.info(f"Response: {response.choices[0].message.content[:100]}...")
        return True
    except Exception as e:
        logger.error(f"❌ Combined features test failed: {e}")
        return False

async def main():
    """Run all tests"""
    logger.info("Starting Anthropic features test suite...")
    
    # Make sure we have the API key
    if not os.environ.get('ANTHROPIC_API_KEY'):
        logger.error("ANTHROPIC_API_KEY not set!")
        return
    
    results = []
    
    # Test thinking budget
    results.append(await test_thinking_budget())
    
    # Test native web search
    results.append(await test_native_web_search())
    
    # Test both together
    results.append(await test_both_features())
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    logger.info(f"\n{'='*50}")
    logger.info(f"Test Results: {passed}/{total} passed")
    logger.info(f"{'='*50}")
    
    if passed == total:
        logger.info("✅ All tests passed!")
    else:
        logger.error("❌ Some tests failed!")

if __name__ == "__main__":
    asyncio.run(main())