"""FastAPI server for the GitHub Genie chat frontend."""

import logging
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add the parent directory to the path to import from examples/client
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "client"))

# Import the agent creation function from the client example
from examples.client.main import create_coordinator_agent

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('github_genie_frontend')

app = FastAPI(title="GitHub Genie Chat")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent variable
coordinator_agent = None

class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

async def get_agent():
    """Get or create the coordinator agent using the imported function."""
    global coordinator_agent
    
    if coordinator_agent is not None:
        return coordinator_agent
    
    try:
        logger.info("Creating coordinator agent using imported function...")
        coordinator_agent = await create_coordinator_agent()
        logger.info("Agent created successfully")
        return coordinator_agent
        
    except Exception as e:
        logger.error(f"Failed to create agent: {e}", exc_info=True)
        raise

@app.post("/api/chat", response_model=ChatResponse)
async def chat(chat_message: ChatMessage) -> ChatResponse:
    """Handle chat messages."""
    try:
        agent = await get_agent()
        
        logger.info(f"Processing chat message: {chat_message.message}")
        
        # Run the agent with the user's message
        result = await agent.run(chat_message.message)
        
        logger.info("Agent response received")
        
        return ChatResponse(response=str(result.data))
        
    except Exception as e:
        logger.error(f"Error processing chat message: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing your message: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

# Serve static files
static_dir = Path(__file__).parent
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting GitHub Genie chat server...")
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=3000,
        reload=True,
        log_level="info"
    )
