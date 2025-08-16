"""A2A Tool Wrapper for pydantic-ai agents."""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from uuid import uuid4

import httpx
from pydantic import BaseModel
from pydantic_ai import Tool

# Import A2A client components with correct imports
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
)
from a2a.client.helpers import create_text_message_object

logger = logging.getLogger('a2a_tool_wrapper')


class A2ASkill(BaseModel):
    """Represents a skill from an A2A agent card."""
    name: str
    description: Optional[str] = None
    examples: Optional[List[str]] = None
    tags: List[str] = []


class A2AAgentCard(BaseModel):
    """Represents an A2A agent card for tool creation."""
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    url: str
    skills: List[A2ASkill] = []


@dataclass
class A2AToolWrapper:
    """Wrapper that creates pydantic-ai tools from A2A agents."""
    
    agent_url: str
    timeout: float = 600.0
    
    async def fetch_agent_card(self) -> AgentCard:
        """Fetch the agent card from the A2A agent using A2ACardResolver."""
        logger.info(f"Fetching agent card from: {self.agent_url}")
        
        async with httpx.AsyncClient(timeout=self.timeout) as httpx_client:
            # Initialize A2ACardResolver
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url=self.agent_url.rstrip('/'),
            )

            try:
                # Fetch public agent card
                agent_card = await resolver.get_agent_card()
                logger.info(f"Successfully fetched agent card: {agent_card.name}")
                
                # Try to get extended card if supported
                if agent_card.supports_authenticated_extended_card:
                    try:
                        logger.info("Attempting to fetch authenticated extended card")
                        auth_headers = {
                            'Authorization': 'Bearer dummy-token-for-extended-card'
                        }
                        extended_card = await resolver.get_agent_card(
                            relative_card_path='/agent/authenticatedExtendedCard',
                            http_kwargs={'headers': auth_headers},
                        )
                        logger.info("Successfully fetched extended agent card")
                        return extended_card
                    except Exception as e:
                        logger.warning(f"Failed to fetch extended card: {e}. Using public card.")
                
                return agent_card
                
            except Exception as e:
                logger.error(f"Failed to fetch agent card: {e}")
                raise
    
    def create_tool_from_agent_card(self, agent_card: AgentCard) -> Tool:
        """Create a pydantic-ai tool from an A2A agent card."""
        
        async def a2a_agent_tool(message: str) -> str:
            """Send a message to the A2A agent and return the response."""
            return await self._send_message_to_a2a_agent(message, agent_card)
        
        # Create tool description based on agent card
        tool_description = f"Send a message to the {agent_card.name} agent"
        if agent_card.description:
            tool_description += f": {agent_card.description}"
        
        # Add skills information to description
        if agent_card.skills:
            skills_desc = ", ".join([f"{skill.name}" for skill in agent_card.skills])
            tool_description += f"\nAvailable skills: {skills_desc}"
        
        # Create the tool name - sanitize for valid identifier
        tool_name = f"a2a_{agent_card.name.lower().replace(' ', '_').replace('-', '_')}"
        
        return Tool(
            function=a2a_agent_tool,
            name=tool_name,
            description=tool_description,
        )
    
    async def _send_message_to_a2a_agent(self, message: str, agent_card: AgentCard) -> str:
        """Send a message to the A2A agent and return the response."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as httpx_client:
                # Initialize A2AClient
                client = A2AClient(
                    httpx_client=httpx_client, 
                    agent_card=agent_card
                )
                
                logger.info(f"Sending message to A2A agent: {message}")
                
                # Create the message using the helper function
                a2a_message = create_text_message_object(content=message)
                
                # Create message send parameters
                send_params = MessageSendParams(message=a2a_message)
                
                # Construct the send message request
                request = SendMessageRequest(
                    id=str(uuid4()),
                    params=send_params
                )
                
                # Send the message
                response = await client.send_message(request)
                
                logger.info("Received response from A2A agent")
                
                # Extract text from the response
                response_text = self._extract_text_from_response(response)
                
                return response_text
                
        except Exception as e:
            logger.error(f"Error communicating with A2A agent: {e}")
            return f"Error communicating with A2A agent: {str(e)}"
    
    def _extract_text_from_response(self, response: Any) -> str:
        """Extract text content from A2A response."""
        try:
            # The response should be a Task or Message object
            if hasattr(response, 'result'):
                result = response.result
            else:
                result = response
            
            # If it's a Task, look for the latest message in history or artifacts
            if hasattr(result, 'history') and result.history:
                # Get the last message from an agent
                for message in reversed(result.history):
                    if hasattr(message, 'role') and message.role == 'agent':
                        return self._extract_text_from_message(message)
            
            # If it's a Message directly
            if hasattr(result, 'parts'):
                return self._extract_text_from_message(result)
            
            # If it's a Task with artifacts
            if hasattr(result, 'artifacts') and result.artifacts:
                for artifact in result.artifacts:
                    if hasattr(artifact, 'parts'):
                        text = self._extract_text_from_parts(artifact.parts)
                        if text:
                            return text
            
            # Fallback: convert to string
            return str(result)
            
        except Exception as e:
            logger.error(f"Error extracting text from response: {e}")
            return f"Error parsing response: {str(e)}"
    
    def _extract_text_from_message(self, message: Any) -> str:
        """Extract text from a message's parts."""
        if hasattr(message, 'parts'):
            return self._extract_text_from_parts(message.parts)
        return str(message)
    
    def _extract_text_from_parts(self, parts: List[Any]) -> str:
        """Extract text content from a list of parts."""
        text_parts = []
        
        for part in parts:
            # Handle Part union types
            if hasattr(part, 'root'):
                part_content = part.root
            else:
                part_content = part
            
            # Extract text from TextPart
            if hasattr(part_content, 'kind') and part_content.kind == 'text':
                text_parts.append(part_content.text)
            elif hasattr(part_content, 'text'):
                text_parts.append(part_content.text)
            # Handle DataPart
            elif hasattr(part_content, 'kind') and part_content.kind == 'data':
                if hasattr(part_content, 'data'):
                    # Convert structured data to string
                    text_parts.append(str(part_content.data))
            # Handle FilePart or other types
            elif hasattr(part_content, 'kind'):
                text_parts.append(f"[{part_content.kind} content]")
        
        return '\n'.join(text_parts) if text_parts else "No response content"
    
    async def create_tool(self) -> Tool:
        """Create a pydantic-ai tool from the A2A agent.
        
        This is the main method to call to get a tool for your pydantic-ai agent.
        """
        agent_card = await self.fetch_agent_card()
        return self.create_tool_from_agent_card(agent_card)
