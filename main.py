"""Main entry point for GitHub Genie - demonstrates basic usage."""

import asyncio
from agent import ask_genie


async def main():
    """Example usage of the GitHub Genie."""
    # Example question
    question = """
    Repository: https://github.com/pydantic/pydantic-ai
    Question: How does the agent system work? What are the main components and how do they interact?
    """
    
    print("Asking GitHub Genie...")
    response = await ask_genie(question)
    print("\nResponse:")
    print(response)


if __name__ == '__main__':
    asyncio.run(main())
