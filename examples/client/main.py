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


async def main():
    """Main example demonstrating A2A tool integration."""
    
    # URL of your A2A agent (GitHub Genie)
    a2a_agent_url = "http://0.0.0.0:8000"
    
    print("🚀 A2A Tool Integration Example")
    print("=" * 50)
    
    try:
        # Step 1: Create the A2A tool wrapper
        print(f"📡 Connecting to A2A agent at: {a2a_agent_url}")
        a2a_wrapper = A2AToolWrapper(agent_url=a2a_agent_url)
        
        # Step 2: Fetch agent card and create tool
        print("🔍 Fetching agent card and creating tool...")
        a2a_tool = await a2a_wrapper.create_tool()
        
        print(f"✅ Successfully created tool: {a2a_tool.name}")
        print(f"📝 Tool description: {a2a_tool.description}")
        
        # Step 3: Create a pydantic-ai agent that uses the A2A tool
        print("\n🤖 Creating pydantic-ai agent with A2A tool...")
        
        coordinator_agent = Agent(
            'openai:gpt-4o-mini',
            system_prompt="""You are a Coordinator Agent that helps users by delegating tasks to specialized agents.

When a user asks about GitHub repositories, code analysis, or anything related to software development, use the A2A agent tool to get help from the GitHub Genie specialist.

Always explain what you're doing and provide comprehensive responses based on the specialist's output.""",
            tools=[a2a_tool],
        )
        
        print("✅ Coordinator agent created with A2A tool")
        
        # Step 4: Example interactions
        print("\n💬 Example Interactions")
        print("-" * 30)
        
        # Example 1: Simple GitHub repository analysis
        example_queries = [
            "How does the tool system work in pydantic-ai? url is https://github.com/pydantic/pydantic-ai"
        ]
        
        for i, query in enumerate(example_queries, 1):
            print(f"\n📋 Example {i}:")
            print(f"Query: {query}")
            print("Processing...")
            
            try:
                result = await coordinator_agent.run(query)
                print(f"✅ Response: {result.data[:500]}...")
                if len(result.data) > 500:
                    print("    (truncated for display)")
                print()
                
                # Add a small delay between requests
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ Error processing query: {e}")
        
        print("\n🎉 A2A Tool Integration Example Complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Example failed: {e}", exc_info=True)


async def test_a2a_connection():
    """Test connection to A2A agent without full integration."""
    
    a2a_agent_url = "http://0.0.0.0:8000"
    
    print("🔧 Testing A2A Agent Connection")
    print("=" * 40)
    
    try:
        # Test fetching agent card
        a2a_wrapper = A2AToolWrapper(agent_url=a2a_agent_url)
        agent_card = await a2a_wrapper.fetch_agent_card()
        
        print(f"✅ Successfully connected to: {agent_card.name}")
        print(f"📝 Description: {agent_card.description}")
        print(f"🔧 Version: {agent_card.version}")
        
        if agent_card.skills:
            print(f"🛠️  Skills ({len(agent_card.skills)}):")
            for skill in agent_card.skills:
                print(f"   - {skill.name}: {skill.description}")
        else:
            print("🛠️  No specific skills defined")
            
        # Test creating a tool
        tool = a2a_wrapper.create_tool_from_agent_card(agent_card)
        print(f"🔨 Created tool: {tool.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        logger.error(f"Connection test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    print("🚀 A2A Tool Integration for Pydantic-AI")
    print("========================================")
    
    # First test the connection
    print("\n1️⃣  Testing A2A connection...")
    connection_ok = asyncio.run(test_a2a_connection())
    
    if connection_ok:
        print("\n2️⃣  Running full integration example...")
        asyncio.run(main())
    else:
        print("\n❌ Skipping full example due to connection issues")
        print("\n💡 Make sure your A2A agent is running at http://0.0.0.0:8000")
        print("   You can start it with: python start_server.py")
