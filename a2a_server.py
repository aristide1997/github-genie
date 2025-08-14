"""A2A Server for GitHub Genie - Pydantic AI Agent."""

import logging
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from a2a_executor import PydanticAIAgentExecutor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('github_genie_a2a')


def create_agent_skills():
    """Create skills that represent GitHub Genie's capabilities."""
    
    analyze_repo_skill = AgentSkill(
        id='analyze_repository',
        name='Analyze GitHub Repository',
        description='Clone and analyze GitHub repositories to understand their structure and codebase',
        tags=['github', 'repository', 'analysis', 'code'],
        examples=[
            'Analyze https://github.com/user/repo',
            'What is the structure of https://github.com/pydantic/pydantic-ai?',
            'Repository: https://github.com/user/repo - How does this project work?'
        ],
    )

    answer_questions_skill = AgentSkill(
        id='answer_code_questions',
        name='Answer Code Questions',
        description='Answer detailed questions about codebases after analyzing repository structure and files',
        tags=['code', 'questions', 'analysis', 'documentation'],
        examples=[
            'How does the authentication system work in this repo?',
            'What are the main components and how do they interact?',
            'Explain the API endpoints in this project',
            'What dependencies does this project use?'
        ],
    )

    search_code_skill = AgentSkill(
        id='search_code',
        name='Search Code Patterns',
        description='Search for specific patterns, functions, or implementations across the codebase',
        tags=['search', 'code', 'patterns', 'functions'],
        examples=[
            'Find all API endpoints in the repository',
            'Search for authentication functions',
            'Find error handling patterns',
            'Locate configuration files'
        ],
    )

    return [analyze_repo_skill, answer_questions_skill, search_code_skill]


def create_public_agent_card(base_url: str):
    """Create the public agent card for GitHub Genie."""
    
    skills = create_agent_skills()
    
    return AgentCard(
        name='GitHub Genie',
        description='A code analysis agent that helps users understand GitHub repositories. '
                   'Provide a repository URL and ask questions about the codebase to get detailed analysis.',
        url=base_url,
        version='1.0.0',
        defaultInputModes=['text/plain'],
        defaultOutputModes=['text/plain'],
        capabilities=AgentCapabilities(streaming=True),
        skills=skills,
        supportsAuthenticatedExtendedCard=False,  # No extended card for now
    )


def main():
    """Main function to start the A2A server."""
    
    # Configuration
    HOST = '0.0.0.0'
    PORT = 8000
    BASE_URL = f'http://{HOST}:{PORT}/'
    
    logger.info(f"Initializing GitHub Genie A2A Server at {BASE_URL}")

    # Create agent card
    public_agent_card = create_public_agent_card(BASE_URL)
    
    # Create agent executor
    agent_executor = PydanticAIAgentExecutor()
    
    # Create request handler
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=InMemoryTaskStore(),
    )

    # Create A2A server
    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
    )

    logger.info(f"Starting GitHub Genie A2A Server on {HOST}:{PORT}")
    logger.info(f"Agent card will be available at: {BASE_URL}.well-known/agent.json")
    
    # Run the server
    uvicorn.run(server.build(), host=HOST, port=PORT)


if __name__ == '__main__':
    main()
