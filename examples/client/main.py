"""Example client demonstrating pydantic-ai agent using A2A tools."""

import asyncio
import logging
from pydantic_ai import Agent
from a2a_tool_wrapper import A2AToolWrapper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('a2a_example_client')


async def create_coordinator_agent(a2a_agent_url: str = "http://0.0.0.0:8000") -> Agent:
    """Create and return a coordinator agent with A2A tool integration.
    
    Args:
        a2a_agent_url: URL of the A2A agent server
        
    Returns:
        Configured pydantic-ai Agent with A2A tool integration
    """
    logger.info("Creating A2A tool wrapper")
    a2a_wrapper = A2AToolWrapper(agent_url=a2a_agent_url)
    
    logger.info("Fetching agent card and creating tool")
    a2a_tool = await a2a_wrapper.create_tool()
    
    logger.info("Creating pydantic-ai coordinator agent")
    coordinator_agent = Agent(
        'openai:gpt-5-nano',
        system_prompt="""You are a Coordinator Agent that helps users by delegating tasks to specialized agents.

When a user asks about GitHub repositories, code analysis, or anything related to software development, use the A2A agent tool to get help from the GitHub Genie specialist.

Always explain what you're doing and provide comprehensive responses based on the specialist's output.

Always report all the information that you have gathered from the specialist.
""",
        tools=[a2a_tool],
    )
    
    return coordinator_agent


async def main():
    """Main example demonstrating A2A tool integration."""
    try:
        coordinator_agent = await create_coordinator_agent()
        
        query = "How does the tool system work in pydantic-ai? url is https://github.com/pydantic/pydantic-ai"
        logger.info(f"Running query: {query}")
        
        result = await coordinator_agent.run(query)
        print(result.output)
        
        logger.info("Query completed successfully")
        
    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
