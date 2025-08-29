"""Test cases and example questions for GitHub Genie.

This file contains various test scenarios and example questions that can be used
to test the GitHub Genie functionality with different repositories and use cases.
"""

import asyncio
import sys
import os

# Add parent directory to Python path so we can import from agent module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.github_genie.agent import ask_genie


async def test_cline_agent_system():
    """Test question about Cline's agent system architecture."""
    question = """
    Repository: https://github.com/cline/cline
    Question: How does the agent system work? What are the main components and how do they interact?
    """
    
    print("Testing Cline agent system analysis...")
    response = await ask_genie(question)
    print("\nResponse:")
    print(response)
    return response


async def test_pydantic_graph_persistence():
    """Test detailed question about pydantic-ai graph persistence methods."""
    question = """
    Repository: https://github.com/pydantic/pydantic-ai
    
Question

Hi, I'm trying to clarify the intended usage and behavior differences between .iter() and .iter_from_persistence() in pydantic-graph, especially in the context of using a shared persistence layer.

Context

In our application we're using both methods like this:

async with self.graph.iter_from_persistence(
    persistence=self.persistence, deps=self.graph_deps
) as run:
    while True:
        run.state.user_input = user_input
        node = await run.next()
        logfire.info(f"Post-node {node}")
        if isinstance(node, End):
            logfire.info(
                f"Graph completed with End node: {node.data}",
                chat_id=self.chat_id,
                _tags=self.tags,
            )
            # Extract response from End node
            if isinstance(
                node.data, MedicalQuestionnaireSystemResponse
            ):
                return node.data
            else:
                # Fallback if End data is not the expected type
                return MedicalQuestionnaireSystemResponse(
                    id="end_fallback",
                    question_text="Processing completed.",
                    type=ChatQuestionType.OPEN_TEXT,
                    question_choices=None,
                )
        elif isinstance(node, AwaitingUserInput):
            # Execute the AwaitingUserInput node and get the next node
            next_node = await run.next()
            logfire.info(
                f"Executed AwaitingUserInput, next node: {next_node}"
            )

            logfire.info(
                f"Current state conversation history: {len(run.state.conversation_history)} messages"
            )

            logfire.info(
                f"Message: {run.state.conversation_history.to_llm_format()}"
            )

            # After AwaitingUserInput execution, look for the most recent response
            for msg in reversed(run.state.conversation_history):
                logfire.info(f"Checking message: {type(msg).__name__}")
                if isinstance(msg, MedicalQuestionnaireSystemResponse):
                    return msg
            break
and

async with self.graph.iter(
    start_node=InitializingSystem(),
    state=self.graph_state,
    deps=self.graph_deps,
    persistence=self.persistence,
) as run:
    while True:
        node = await run.next()
        if isinstance(node, End):
            logfire.info(
                f"Graph completed with End node: {node.data}",
                chat_id=self.chat_id,
                _tags=self.tags,
            )
            # Extract response from End node
            if isinstance(
                node.data, MedicalQuestionnaireSystemResponse
            ):
                return node.data
            else:
                # Return initial message for new sessions if End data is not expected type
                return MedicalQuestionnaireSystemResponse(
                    id="initial_message",
                    question_text=self.INITIAL_MESSAGE,
                    type=ChatQuestionType.OPEN_TEXT,
                    question_choices=None,
                )
        elif isinstance(node, AwaitingUserInput):
            logfire.info(
                "Executing AwaitingUserInput node - will stop iteration after this",
                chat_id=self.chat_id,
                _tags=self.tags,
            )
            # Execute the AwaitingUserInput node and get the next node
            next_node = await run.next()
            logfire.info(
                f"Executed AwaitingUserInput, next node: {next_node}"
            )
            break
        # For other node types, continue the iteration

    # After AwaitingUserInput execution, look for the most recent response
    for msg in reversed(run.state.conversation_history):
        if isinstance(msg, MedicalQuestionnaireSystemResponse):
            return msg

    # Return initial message for new sessions
    return MedicalQuestionnaireSystemResponse(
        id="initial_message",
        question_text=self.INITIAL_MESSAGE,
        type=ChatQuestionType.OPEN_TEXT,
        question_choices=None,
    )
Questions

While .iter() seems to start a new graph run and .iter_from_persistence() resumes from saved state, both accept the same persistence instance (self.persistence). This raises a few questions:
1. What exactly changes in how the persistence parameter is used between the two methods?
2. Why does .iter() require state and start_node explicitly even when persistence is provided?
3. Does .iter_from_persistence() infer the start node/state from persistence, or is it cached/stored elsewhere?
4. How do the lifecycle and side effects differ—does .iter() create a new record while .iter_from_persistence() modifies an existing one?

Use Case

We're implementing a medical chatbot where:
• New conversations are started with .iter()
• Interrupted sessions are resumed via .iter_from_persistence()
• We want to ensure state consistency between both paths
    """
    
    print("Testing pydantic-ai graph persistence analysis...")
    response = await ask_genie(question)
    print("\nResponse:")
    print(response)
    return response

# TODO: Add tools for git commands
async def test_git_commands():
    """Test git command functionality."""
    question = """
    Repository: https://github.com/pydantic/pydantic-ai
    
    I want to test the git command functionality. Please:
    
    1. Clone the repository 
    2. Use git commands to analyze the repository:
       - Show git status
       - Show the last 5 commits with --oneline format
       - Show all available branches
       - Show details of the latest commit
       - Show a diff of the latest commit
    
    Question: What can you tell me about this repository's git history and structure using the git commands?
    """
    
    print("Testing git command functionality...")
    response = await ask_genie(question)
    print("\nResponse:")
    print(response)
    return response


async def run_all_tests():
    """Run all test cases."""
    print("=" * 80)
    print("GitHub Genie Test Suite")
    print("=" * 80)
    
    tests = [
        ("Cline Agent System", test_cline_agent_system),
        ("Pydantic-AI Graph Persistence", test_pydantic_graph_persistence),
        ("Git Commands", test_git_commands),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'=' * 40}")
        print(f"Running: {test_name}")
        print(f"{'=' * 40}")
        
        try:
            result = await test_func()
            results[test_name] = {"status": "success", "result": result}
            print(f"\n✅ {test_name} completed successfully")
        except Exception as e:
            results[test_name] = {"status": "error", "error": str(e)}
            print(f"\n❌ {test_name} failed: {e}")
    
    print(f"\n{'=' * 80}")
    print("Test Summary")
    print(f"{'=' * 80}")
    
    for test_name, result in results.items():
        status_emoji = "✅" if result["status"] == "success" else "❌"
        print(f"{status_emoji} {test_name}: {result['status']}")
    
    return results


async def main():
    """Main function to run individual tests or all tests."""
    import sys
    
    if len(sys.argv) > 1:
        test_name = sys.argv[1].lower()
        
        if test_name == "cline":
            await test_cline_agent_system()
        elif test_name == "persistence":
            await test_pydantic_graph_persistence()
        elif test_name == "git":
            await test_git_commands()
        elif test_name == "all":
            await run_all_tests()
        else:
            print("Available tests:")
            print("  python test.py cline          - Test Cline agent system")
            print("  python test.py persistence     - Test pydantic-ai persistence")
            print("  python test.py git            - Test git commands functionality")
            print("  python test.py all            - Run all tests")
    else:
        print("GitHub Genie Test Cases")
        print("=" * 40)
        print("Available tests:")
        print("  python test.py cline          - Test Cline agent system")
        print("  python test.py persistence     - Test pydantic-ai persistence")
        print("  python test.py git            - Test git commands functionality")
        print("  python test.py all            - Run all tests")


if __name__ == '__main__':
    asyncio.run(main())
