"""GitHub Genie - A pydantic-ai agent for analyzing GitHub repositories.

This agent can clone repositories, understand their structure, and answer questions about the codebase.
Similar to cursor/cline but as an agent that can be queried programmatically.
"""

import asyncio
import logging
import os
import shutil
from dataclasses import dataclass

from pydantic_ai import Agent
from pydantic_ai.models.fallback import FallbackModel

from . import tools
from .dependencies import GenieDependencies

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('github_genie')


# Create the GitHub Genie agent with fallback model
github_genie = Agent(
    FallbackModel('openai:gpt-5-nano', 'openai:gpt-4.1-nano'),
    deps_type=GenieDependencies,
    system_prompt=
f"""You are GitHub Genie, a code analysis agent that helps users understand repositories.

When a user provides a repository URL and asks questions about it:
1. Extract the repo URL from their query
2. Clone the repository using the clone_repository tool
3. Analyze the structure using get_repository_structure to understand the project
4. Use your tools to explore files and find answers to the user's specific questions
5. Provide detailed, helpful responses about the codebase

Be thorough in your analysis but efficient - don't read unnecessary files. Focus on answering the specific question asked.
Use the tools strategically:
- Start with repository structure to get context
- Use list_directory_contents to explore specific directories
- Use read_file_content to examine files (defaults to first 200 lines with line numbers)
  - For specific sections: read_file_content(file_path, line_start=100, line_end=200)
  - For entire file: read_file_content(file_path, line_end=None)
- Use search_in_files when looking for specific patterns or functionality

When using search_in_files, be careful with regex patterns:
- Escape special characters like parentheses: use 'function_name\\(' instead of 'function_name('
- For simple text searches, avoid regex special characters

Always provide comprehensive answers with code examples when relevant.""",
    retries=2,
    tools=[
        tools.clone_repository,
        tools.get_repository_structure,
        tools.list_directory_contents,
        tools.read_file_content,
        tools.search_in_files,
    ]
)


async def ask_genie(question: str, deps: GenieDependencies = None) -> str:
    """Main function to ask the GitHub Genie a question about a repository.
    
    Args:
        question: Question that should include a repository URL and the actual question.
        deps: Optional dependencies. If not provided, creates default dependencies.
    
    Returns:
        The agent's response as a string.
    """
    if deps is None:
        deps = GenieDependencies()
    
    result = await github_genie.run(question, deps=deps)
    
    # Clean up temporary directory if it was created
    if deps.current_repo_path and os.path.exists(deps.current_repo_path):
        try:
            shutil.rmtree(os.path.dirname(deps.current_repo_path))
        except Exception:
            pass  # Ignore cleanup errors
    
    return result.output
