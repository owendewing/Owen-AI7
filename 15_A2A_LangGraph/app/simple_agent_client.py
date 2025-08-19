"""
Simple Agent Client for Activity #1
This agent can make API calls to the A2A server through the A2A protocol.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List
import httpx
from pydantic import BaseModel
from uuid import uuid4

# A2A imports
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendStreamingMessageRequest,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleAgentMessage(BaseModel):
    """Message format for A2A communication"""
    role: str
    content: str

class SimpleAgentClient:
    """
    A simple agent that can communicate with the A2A server
    to fulfill Activity #1 requirements.
    """
    
    def __init__(self, server_url: str = "http://localhost:10000"):
        self.server_url = server_url
        self.client = None
        self.agent_card = None
        self.conversation_history: List[Dict[str, Any]] = []
    
    async def initialize(self):
        """Initialize the A2A client and fetch agent card"""
        try:
            # Create HTTP client with longer timeout
            httpx_client = httpx.AsyncClient(timeout=httpx.Timeout(60.0))
            
            # Initialize A2A Card Resolver
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url=self.server_url,
            )
            
            # Fetch the agent card
            logger.info(f"Fetching agent card from: {self.server_url}")
            self.agent_card = await resolver.get_agent_card()
            logger.info("Successfully fetched agent card")
            
            # Initialize A2A client
            self.client = A2AClient(
                httpx_client=httpx_client,
                agent_card=self.agent_card
            )
            logger.info("A2A client initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing A2A client: {e}")
            raise
    
    async def start_conversation(self, user_query: str) -> str:
        """
        Start a new conversation with the A2A server.
        
        Args:
            user_query: The initial user query
            
        Returns:
            The agent's response
        """
        try:
            if not self.client:
                await self.initialize()
            
            # Create message payload
            send_message_payload = {
                'message': {
                    'role': 'user',
                    'parts': [
                        {'kind': 'text', 'text': user_query}
                    ],
                    'message_id': uuid4().hex,
                },
            }
            
            # Create request
            request = SendMessageRequest(
                id=str(uuid4()),
                params=MessageSendParams(**send_message_payload)
            )
            
            logger.info(f"Starting conversation with query: {user_query}")
            
            # Send message
            response = await self.client.send_message(request)
            
            # Store conversation context
            task_id = response.root.result.id
            context_id = response.root.result.context_id
            
            self.conversation_history.append({
                "task_id": task_id,
                "context_id": context_id,
                "messages": [{"role": "user", "content": user_query}]
            })
            
            logger.info(f"Task created with ID: {task_id}")
            
            # Extract response content
            if hasattr(response, 'root') and hasattr(response.root, 'result'):
                result = response.root.result
                
                # Check for artifacts (the actual response content)
                if hasattr(result, 'artifacts') and result.artifacts:
                    for artifact in result.artifacts:
                        if hasattr(artifact, 'parts') and artifact.parts:
                            for part in artifact.parts:
                                if hasattr(part.root, 'text'):
                                    return part.root.text
                
                # Fallback to other response formats
                if hasattr(result, 'content') and result.content:
                    return result.content
                elif hasattr(result, 'message') and result.message:
                    return result.message
                else:
                    return f"Response received: {result}"
            else:
                return f"Response received: {response}"
                
        except Exception as e:
            logger.error(f"Error starting conversation: {e}")
            return f"Error: {str(e)}"
    
    async def continue_conversation(self, task_id: str, context_id: str, user_message: str) -> str:
        """
        Continue an existing conversation.
        
        Args:
            task_id: The task ID from the previous conversation
            context_id: The context ID from the previous conversation
            user_message: The new user message
            
        Returns:
            The agent's response
        """
        try:
            if not self.client:
                await self.initialize()
            
            # Create message payload for continuation
            send_message_payload = {
                'message': {
                    'role': 'user',
                    'parts': [
                        {'kind': 'text', 'text': user_message}
                    ],
                    'message_id': uuid4().hex,
                    'task_id': task_id,
                    'context_id': context_id,
                },
            }
            
            # Create request
            request = SendMessageRequest(
                id=str(uuid4()),
                params=MessageSendParams(**send_message_payload)
            )
            
            # Send message
            response = await self.client.send_message(request)
            
            # Extract response content
            if hasattr(response, 'root') and hasattr(response.root, 'result'):
                result = response.root.result
                
                # Check for artifacts (the actual response content)
                if hasattr(result, 'artifacts') and result.artifacts:
                    for artifact in result.artifacts:
                        if hasattr(artifact, 'parts') and artifact.parts:
                            for part in artifact.parts:
                                if hasattr(part.root, 'text'):
                                    return part.root.text
                
                # Fallback to other response formats
                if hasattr(result, 'content') and result.content:
                    return result.content
                elif hasattr(result, 'message') and result.message:
                    return result.message
                else:
                    return f"Response received: {result}"
            else:
                return f"Response received: {response}"
                
        except Exception as e:
            logger.error(f"Error continuing conversation: {e}")
            return f"Error: {str(e)}"
    
    async def close(self):
        """Close the HTTP client"""
        if self.client and hasattr(self.client, 'httpx_client'):
            await self.client.httpx_client.aclose()

class SimpleAgent:
    """
    A simple agent that demonstrates A2A protocol usage.
    This agent can ask questions and get responses from the A2A server.
    """
    
    def __init__(self, name: str = "SimpleAgent", server_url: str = "http://localhost:10000"):
        self.name = name
        self.client = SimpleAgentClient(server_url)
        self.current_task_id = None
        self.current_context_id = None
    
    async def ask_question(self, question: str) -> str:
        """
        Ask a question to the A2A server.
        
        Args:
            question: The question to ask
            
        Returns:
            The response from the A2A server
        """
        # For Activity #1, we'll start a new conversation for each question
        # to demonstrate the A2A protocol working
        response = await self.client.start_conversation(question)
        
        # Store the task info for potential future use
        if self.client.conversation_history:
            self.current_task_id = self.client.conversation_history[-1].get("task_id")
            self.current_context_id = self.client.conversation_history[-1].get("context_id")
        
        return response
    
    async def reset_conversation(self):
        """Reset the conversation state"""
        self.current_task_id = None
        self.current_context_id = None
        self.client.conversation_history = []
    
    async def close(self):
        """Close the agent and its client"""
        await self.client.close()

# Example usage and testing
async def test_simple_agent():
    """Test the simple agent with various queries"""
    
    # Create the simple agent
    agent = SimpleAgent("TestAgent")
    
    try:
        # Test queries that should trigger different tools
        test_queries = [
            "What are the latest developments in AI?",
            "Find recent papers about transformers",
            "What do you know about machine learning?",
            "Can you search for information about LangGraph?"
        ]
        
        print(f"🤖 {agent.name} starting A2A protocol test...\n")
        
        for i, query in enumerate(test_queries, 1):
            print(f"📝 Query {i}: {query}")
            print("-" * 50)
            
            response = await agent.ask_question(query)
            print(f"🤖 Response: {response}")
            print("\n" + "="*60 + "\n")
            
            # Small delay between queries
            await asyncio.sleep(1)
        
        print("✅ A2A protocol test completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
    
    finally:
        await agent.close()

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_simple_agent()) 