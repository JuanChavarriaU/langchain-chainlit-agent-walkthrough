"""
Phase 2: Test GitHub Models Connection
Run with: python test_github_models.py

This script verifies that your GitHub Models connection is working correctly.
It's the foundation for all subsequent phases.

Key Concepts Introduced:
- Loading environment variables with dotenv
- Creating a ChatOpenAI client configured for GitHub Models
- Making a simple LLM request
"""

import os
from dotenv import load_dotenv 
from langchain_openai import ChatOpenAI

load_dotenv() # Load environment variables from .env file

def main():
    github_token = os.getenv("GITHUB_TOKEN")

    if not github_token:
        print("❌ Error: GITHUB_TOKEN not set in .env file")
        print("   Please add your GitHub token to the .env file")
        return
    
    print("🔄 Testing connection to GitHub Models...")

    llm = ChatOpenAI(
        model=os.getenv("MODEL"),
        api_key=github_token,
        base_url=os.getenv("ENDPOINT"),
        temperature=0.5
    )

    try:
        response = llm.invoke("What is the capital of Verguas in Panama?")
        print("✅ Connection successful! Response from model:")
        print(response)
    except Exception as e:
        print("❌ Error. Error:")
        print("\nTroubleshooting:")
        print("- Make sure your GitHub token is valid")
        print("- Check your internet connection")
        print("- Verify the token hasn't expired")
        print(e)
if __name__ == "__main__":
    main()