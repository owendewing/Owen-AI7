"""
LangGraph Agent Client for Activity #1
This implements a LangGraph that can make API calls to the A2A server through the A2A protocol.
"""

import asyncio
import logging
from typing import Dict, Any, List, TypedDict, Annotated
from uuid import uuid4

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage

# A2A imports
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LangGraphAgentState(TypedDict):
    """State schema for the LangGraph agent that communicates with A2A server."""
    messages: Annotated[List, add_messages]
    a2a_response: str
    task_id: str
    context_id: str

class A2ACommunicationNode:
    """
    A LangGraph node that communicates with the A2A server.
    This is the core component that makes Activity #1 a proper LangGraph implementation.
    """
    
    def __init__(self, server_url: str = "http://localhost:10000"):
        self.server_url = server_url
        self.client = None
        self.agent_card = None
    
    async def initialize(self):
        """Initialize the A2A client and fetch agent card"""
        try:
            import httpx
            
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
    
    async def call_a2a_server(self, state: LangGraphAgentState) -> Dict[str, Any]:
        """
        LangGraph node function that communicates with the A2A server.
        This is the key function that makes this a LangGraph implementation.
        """
        try:
            if not self.client:
                await self.initialize()
            
            # Get the latest user message
            messages = state["messages"]
            latest_message = messages[-1]
            
            if isinstance(latest_message, HumanMessage):
                user_query = latest_message.content
            else:
                user_query = str(latest_message.content)
            
            # Create message payload for A2A server
            send_message_payload = {
                'message': {
                    'role': 'user',
                    'parts': [
                        {'kind': 'text', 'text': user_query}
                    ],
                    'message_id': uuid4().hex,
                },
            }
            
            # If we have existing task context, include it
            if state.get("task_id") and state.get("context_id"):
                send_message_payload['message']['task_id'] = state["task_id"]
                send_message_payload['message']['context_id'] = state["context_id"]
            
            # Create request
            request = SendMessageRequest(
                id=str(uuid4()),
                params=MessageSendParams(**send_message_payload)
            )
            
            logger.info(f"LangGraph node sending query to A2A server: {user_query}")
            
            # Send message to A2A server
            response = await self.client.send_message(request)
            
            # Extract response content
            a2a_response = "No response received"
            task_id = None
            context_id = None
            
            if hasattr(response, 'root') and hasattr(response.root, 'result'):
                result = response.root.result
                
                # Check for artifacts (the actual response content)
                if hasattr(result, 'artifacts') and result.artifacts:
                    for artifact in result.artifacts:
                        if hasattr(artifact, 'parts') and artifact.parts:
                            for part in artifact.parts:
                                if hasattr(part.root, 'text'):
                                    a2a_response = part.root.text
                                    break
                
                # Store task info for future communications
                task_id = result.id if hasattr(result, 'id') else None
                context_id = result.context_id if hasattr(result, 'context_id') else None
                
                # If no artifacts found, try to get response from other fields
                if a2a_response == "No response received":
                    if hasattr(result, 'content') and result.content:
                        a2a_response = result.content
                    elif hasattr(result, 'message') and result.message:
                        a2a_response = result.message
                    else:
                        # Log the response structure for debugging
                        logger.info(f"Response structure: {result}")
                        a2a_response = f"Response received but content not in expected format: {result}"
            
            logger.info(f"LangGraph node received response from A2A server")
            
            # Return updated state
            return {
                "a2a_response": a2a_response,
                "task_id": task_id,
                "context_id": context_id,
                "messages": [AIMessage(content=a2a_response)]
            }
            
        except Exception as e:
            logger.error(f"Error in LangGraph A2A communication node: {e}")
            error_response = f"Error communicating with A2A server: {str(e)}"
            return {
                "a2a_response": error_response,
                "messages": [AIMessage(content=error_response)]
            }

def build_langgraph_agent(server_url: str = "http://localhost:10000"):
    """
    Build a LangGraph that uses the A2A protocol to communicate with the server.
    This is the proper implementation for Activity #1.
    """
    
    # Create the A2A communication node
    a2a_node = A2ACommunicationNode(server_url)
    
    # Create the LangGraph
    workflow = StateGraph(LangGraphAgentState)
    
    # Add the A2A communication node
    workflow.add_node("communicate_with_a2a", a2a_node.call_a2a_server)
    
    # Set the entry point
    workflow.set_entry_point("communicate_with_a2a")
    
    # Set the end point
    workflow.add_edge("communicate_with_a2a", END)
    
    # Compile the graph
    app = workflow.compile()
    
    return app, a2a_node

class LangGraphAgent:
    """
    A LangGraph-based agent that demonstrates Activity #1 requirements.
    This agent uses LangGraph to orchestrate communication with the A2A server.
    """
    
    def __init__(self, name: str = "LangGraphAgent", server_url: str = "http://localhost:10000"):
        self.name = name
        self.server_url = server_url
        self.graph, self.a2a_node = build_langgraph_agent(server_url)
        self.conversation_history = []
    
    async def ask_question(self, question: str) -> str:
        """
        Ask a question using the LangGraph that communicates with the A2A server.
        This is the proper Activity #1 implementation.
        """
        try:
            # Create the initial state - start fresh for each query to avoid task completion issues
            initial_state = {
                "messages": [HumanMessage(content=question)],
                "a2a_response": "",
                "task_id": "",
                "context_id": ""
            }
            
            logger.info(f"🤖 {self.name} using LangGraph to communicate with A2A server")
            
            # Execute the LangGraph
            result = await self.graph.ainvoke(initial_state)
            
            # Store the result for potential future use
            self.conversation_history.append(result)
            
            # Return the A2A response
            return result.get("a2a_response", "No response received")
            
        except Exception as e:
            logger.error(f"Error in LangGraph agent: {e}")
            return f"Error: {str(e)}"
    
    async def reset_conversation(self):
        """Reset the conversation state"""
        self.conversation_history = []
    
    async def close(self):
        """Close the agent and its A2A client"""
        if self.a2a_node and self.a2a_node.client:
            if hasattr(self.a2a_node.client, 'httpx_client'):
                await self.a2a_node.client.httpx_client.aclose()

# Example usage and testing
async def test_langgraph_agent():
    """Test the LangGraph agent with various queries"""
    
    # Create the LangGraph agent
    agent = LangGraphAgent("LangGraphA2AAgent")
    
    try:
        # Test queries that should trigger different tools
        test_queries = [
            "What are the latest developments in AI?",
            "Find recent papers about transformers",
            "What do you know about machine learning?",
            "Can you search for information about LangGraph?"
        ]
        
        print(f"🤖 {agent.name} starting LangGraph A2A protocol test...\n")
        
        for i, query in enumerate(test_queries, 1):
            print(f"📝 Query {i}: {query}")
            print("-" * 50)
            
            response = await agent.ask_question(query)
            print(f"🤖 LangGraph Response: {response[:200]}...")
            print("\n" + "="*60 + "\n")
            
            # Small delay between queries
            await asyncio.sleep(1)
        
        print("✅ LangGraph A2A protocol test completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
    
    finally:
        await agent.close()

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_langgraph_agent()) 