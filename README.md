# GitHub Genie 🧞‍♂️

A powerful pydantic-ai agent that analyzes GitHub repositories and answers questions about codebases. Think of it as a code-aware assistant that can clone any public repository, understand its structure, and provide detailed insights about the code.

## Features

- **Repository Analysis**: Clone and analyze any public GitHub repository
- **Code Understanding**: Navigate through project structure and understand codebase architecture
- **Question Answering**: Ask specific questions about how the code works, patterns used, or implementation details
- **A2A Server**: Deployable server that exposes the agent via the A2A (Agent-to-Agent) protocol
- **Flexible Tools**: Search files, read code with line numbers, and explore directory structures

## Quick Start

### Installation

```bash
git clone https://github.com/yourusername/github-genie.git
cd github-genie
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file with your OpenAI API key:

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Usage

#### Option 1: Start the A2A Server (Recommended)

```bash
python main.py
```

The server will start on `http://localhost:8000` and expose the agent via the A2A protocol.

#### Option 2: Direct Agent Usage

```bash
python agent/example.py
```

Or use it programmatically:

```python
import asyncio
from agent import ask_genie

async def main():
    question = """
    Repository: https://github.com/pydantic/pydantic-ai
    Question: How does the agent system work? What are the main components?
    """
    
    response = await ask_genie(question)
    print(response)

asyncio.run(main())
```

## How It Works

GitHub Genie uses several specialized tools to analyze repositories:

1. **Clone Repository**: Downloads the specified GitHub repository to a temporary directory
2. **Get Repository Structure**: Analyzes the overall project structure and key files
3. **Directory Navigation**: Explores specific directories to understand organization
4. **File Reading**: Reads code files with line numbers for detailed analysis
5. **Code Search**: Searches for specific patterns or functions across the codebase

The agent intelligently uses these tools to answer your questions about any public GitHub repository.

## Example Queries

```python
# Architecture analysis
"Repository: https://github.com/pydantic/pydantic-ai - How does the agent system work?"

# Specific implementation details
"Repository: https://github.com/fastapi/fastapi - How does dependency injection work?"

# Code patterns
"Repository: https://github.com/pallets/flask - What design patterns are used in the routing system?"

# Dependencies and structure  
"Repository: https://github.com/django/django - What are the main components and how do they interact?"
```

## A2A Server Integration

The GitHub Genie can be used as an A2A agent by other AI systems. The server exposes:

- **Agent Card**: Available at `/.well-known/agent.json`
- **Skills**: Repository analysis, code questioning, and pattern searching
- **Streaming**: Real-time response streaming for better user experience

### Example A2A Client

```python
from examples.client.a2a_tool_wrapper import A2AToolWrapper
from pydantic_ai import Agent

# Create A2A tool wrapper
a2a_wrapper = A2AToolWrapper(agent_url="http://localhost:8000")
a2a_tool = await a2a_wrapper.create_tool()

# Use in your own agent
coordinator_agent = Agent(
    'openai:gpt-4o-mini',
    tools=[a2a_tool],
    system_prompt="You can analyze GitHub repositories using the A2A tool..."
)
```

## Development

### Project Structure

```
github-genie/
├── main.py                    # Server entry point
├── agent/
│   ├── agent.py              # Core pydantic-ai agent
│   ├── tools.py              # Repository analysis tools
│   ├── dependencies.py       # Agent dependencies
│   └── example.py            # Direct usage example
├── server/                   # A2A server implementation
├── examples/
│   └── client/               # A2A client examples
└── tests/                    # Test cases
```

### Running Tests

```bash
python tests/test.py all
```

Available test commands:
- `python tests/test.py cline` - Test Cline repository analysis
- `python tests/test.py persistence` - Test pydantic-ai persistence analysis
- `python tests/test.py git` - Test git command functionality

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [pydantic-ai](https://github.com/pydantic/pydantic-ai)
- A2A protocol implementation using [A2A SDK](https://github.com/anthropics/a2a-python)
- Inspired by code analysis tools like Cursor and Cline
