"""Simplified FastAPI server for the GitHub Genie chat frontend."""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('github_genie_frontend')

app = FastAPI(title="GitHub Genie Chat Frontend")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    
    logger.info("Starting GitHub Genie chat frontend server...")
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=3000,
        reload=True,
        log_level="info"
    )
