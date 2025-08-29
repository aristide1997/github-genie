# GitHub Genie 🧞‍♂️

GitHub Genie showcases the A2A (Agent-to-Agent) protocol by solving a problem many of us have: understanding unfamiliar codebases. Point it at any public GitHub repo, ask questions about the code, and get detailed analysis back.

This agent follows the A2A protocol, making it interoperable with other AI systems. Other agents can discover and use GitHub Genie as a specialized tool for code analysis.

## What it does

Give GitHub Genie a repository URL and a question like "How does authentication work in this codebase?" and it will:

1. Clone the repository  
2. Analyze the project structure
3. Navigate through relevant files
4. Give you a detailed explanation with code examples

Because it follows the A2A protocol, other AI agents can use it as a tool. Your personal AI assistant could delegate code analysis questions to GitHub Genie automatically.

## Why A2A matters

Traditional AI systems are isolated. A2A changes that by letting agents communicate and delegate tasks to each other. Think of it as microservices for AI agents.

In this project:
- **GitHub Genie** specializes in code analysis
- **Your agent** handles general conversation but can call GitHub Genie when needed
- **Other agents** can discover and use GitHub Genie through the standard A2A protocol

## Three ways to use it

### 1. Standard A2A Protocol (Universal)

Run the server and any A2A-compatible client can discover and use GitHub Genie:

```bash
python main.py
```

The agent exposes its capabilities at `http://localhost:8000/.well-known/agent.json`. Any A2A client can:

1. Fetch the agent card to understand GitHub Genie's capabilities
2. Send tasks to the `/execute` endpoint
3. Stream responses via WebSocket

This works with any A2A client implementation, regardless of framework. See the [A2A samples repo](https://github.com/a2aproject/a2a-samples) for examples in different languages.

### 2. Pydantic-AI Specific Implementation

For pydantic-ai users, we've built a convenience wrapper that handles the A2A protocol:

```python
from examples.client.a2a_tool_wrapper import A2AToolWrapper
from pydantic_ai import Agent

# Create A2A tool wrapper
a2a_wrapper = A2AToolWrapper(agent_url="http://localhost:8000")
a2a_tool = await a2a_wrapper.create_tool()

# Your agent can now delegate to GitHub Genie
coordinator_agent = Agent(
    'openai:gpt-4o-mini',
    tools=[a2a_tool],
    system_prompt="When users ask about code, use the GitHub analysis tool..."
)

result = await coordinator_agent.run(
    "How does routing work in https://github.com/fastapi/fastapi?"
)
```

Note: This A2AToolWrapper is specific to pydantic-ai. Other frameworks would need their own wrapper implementations.

### 3. Web Frontend (Direct HTTP)

For a simple direct chat interface without any intermediate agents:

```bash
cd examples/frontend
python server.py
```

Open `http://localhost:3000` and start asking questions about repositories.

## Examples that work

Try these with any of the above methods:

```
Repository: https://github.com/fastapi/fastapi
Question: How does dependency injection work?

Repository: https://github.com/django/django  
Question: What are the main components and how do they interact?

Repository: https://github.com/pallets/flask
Question: How does the routing system work?

Repository: https://github.com/pydantic/pydantic-ai
Question: Explain the agent architecture and tool system
```

## Quick Start

```bash
git clone <this-repo>
cd github-genie
pip install -r requirements.txt

# Set up your OpenAI API key
echo "OPENAI_API_KEY=your_key_here" > .env

# Start the A2A server
python main.py
```

The server exposes the standard A2A endpoints:
- `/.well-known/agent.json` - Agent discovery card
- `/execute` - Task execution
- WebSocket streaming support

## Project Structure

```
github-genie/
├── main.py                      # A2A server entry point
├── src/
│   └── github_genie/
│       ├── agent/
│       │   ├── agent.py         # Core pydantic-ai agent
│       │   ├── tools.py         # Repository analysis tools  
│       │   └── dependencies.py  # Agent dependencies
│       └── server/              # A2A server implementation
│           ├── app.py           # A2A server + agent integration
│           ├── executor.py      # Pydantic-ai executor
│           └── progress_reporter.py  # Task progress reporting
├── examples/
│   ├── client/                  # Agent-to-agent example
│   │   ├── main.py             # Client demonstration
│   │   └── a2a_tool_wrapper.py # Pydantic-AI A2A wrapper
│   └── frontend/                # Web interface example
│       ├── index.html          # Chat interface
│       ├── script.js           # Frontend logic
│       ├── style.css           # Styling
│       └── server.py           # Static file server
└── tests/                       # Test cases
    ├── test.py                 # Repository analysis tests
    └── test_a2a.sh             # A2A protocol tests
```

## How it works

GitHub Genie uses these tools to analyze repositories:

- **clone_repository** - Downloads the repo to a temp directory
- **get_repository_structure** - Maps out the project organization  
- **list_directory_contents** - Explores specific folders
- **read_file_content** - Reads code files with line numbers
- **search_in_files** - Finds patterns across the codebase

The A2A server wraps this pydantic-ai agent and exposes it through the standard protocol, making it discoverable and usable by other AI systems.

## Testing

```bash
# Test different repository types
python tests/test.py cline           # Test with Cline repo
python tests/test.py persistence     # Test with pydantic-ai repo  
python tests/test.py git            # Test git functionality

# Test A2A integration
./tests/test_a2a.sh
```

## Implementation Notes

Built with:
- **pydantic-ai** for the core agent logic
- **a2a-sdk** for A2A protocol implementation  
- **uvicorn** and **starlette** for the HTTP server
- Standard git tools for repository operations

The agent is designed to be efficient - it doesn't read every file but strategically explores based on the question asked. For large repositories, it focuses on key files like README, package.json, requirements.txt, and main source directories.

## Contributing

Fork, create a feature branch, make your changes, test them, and open a PR. The codebase is straightforward and well-commented.

## License

MIT License - use it however you want.
