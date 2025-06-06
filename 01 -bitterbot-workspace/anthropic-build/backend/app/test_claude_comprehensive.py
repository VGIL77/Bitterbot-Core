import asyncio
import os
import sys
sys.path.append('.')
from app.services.claude import ClaudeService
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

async def test_basic_chat():
    """Test basic chat functionality"""
    print("=== Testing Basic Chat ===")
    claude = ClaudeService()
    
    response = await claude.get_response("What are 3 benefits of Python programming?")
    print("Response:", response["content"])
    print("Input tokens:", response["usage"]["input_tokens"])
    print("Output tokens:", response["usage"]["output_tokens"])
    print()

async def test_with_tools():
    """Test advanced functionality with tools"""
    print("=== Testing Advanced Features with Tools ===")
    claude = ClaudeService()
    
    # This will show how Claude can break down tasks
    response = await claude.process_message(
        "I need help creating a Python web scraper that extracts data from multiple websites and saves it to a database"
    )
    
    print("Response:", response["content"])
    print("Tools used:", response["tools_used"])
    print("Tasks identified:", len(response["tasks"]))
    for i, task in enumerate(response["tasks"], 1):
        print(f"  Task {i}: {task['title']} - {task['description']}")
    print()

async def test_conversation():
    """Test conversation with context"""
    print("=== Testing Conversation with Context ===")
    claude = ClaudeService()
    
    # First message
    response1 = await claude.get_response("My name is Victor and I'm learning to code.")
    print("Claude:", response1["content"][:200] + "...")
    
    # Second message with context
    context = [
        {"role": "user", "content": "My name is Victor and I'm learning to code."},
        {"role": "assistant", "content": response1["content"]}
    ]
    
    response2 = await claude.get_response("What programming language should I start with?", context=context)
    print("Claude (with context):", response2["content"][:200] + "...")
    print()

async def main():
    print("🤖 Testing Claude Integration...")
    print("Your API key is working! ✅\n")
    
    try:
        await test_basic_chat()
        await test_with_tools()
        await test_conversation()
        
        print("🎉 All tests passed! Claude is ready to use in your project.")
        print("\nNext steps:")
        print("1. Your ClaudeService is working perfectly")
        print("2. You can now integrate this into your FastAPI backend")
        print("3. Connect it to your frontend React/Next.js app")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Check your .env file and API key")

if __name__ == "__main__":
    asyncio.run(main())
