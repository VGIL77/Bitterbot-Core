import asyncio
import os
import sys
sys.path.append('.')
from app.services.claude import ClaudeService
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

async def main():
    claude = ClaudeService()
    user_message = "Hello Claude! Can you summarize what you are?"
    print("Sending message to Claude...")
    response = await claude.get_response(user_message)
    print("\nClaude's response:")
    print(response["content"])

if __name__ == "__main__":
    asyncio.run(main())
