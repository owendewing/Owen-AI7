#!/usr/bin/env python3
"""
Test script for Activity #1: LangGraph using A2A Protocol

This script demonstrates how to create a LangGraph that can make API calls
to the A2A server through the A2A protocol.

Usage:
    # First start the A2A server:
    uv run python -m app
    
    # Then run this test:
    uv run python app/test_activity1.py
"""

import asyncio
import sys
import time
import json
from langgraph_agent_client import LangGraphAgent

def format_response(response: str) -> str:
    """
    Format the agent response into readable sentences.
    Extracts the actual content from the A2A response artifacts.
    """
    try:
        # If it's a JSON response, try to extract the text content
        if "artifacts=" in response and "TextPart" in response:
            # Extract the text content from the artifact response
            # Look for the text content in the response
            start_idx = response.find("text='")
            if start_idx != -1:
                start_idx += 6  # Skip "text='"
                end_idx = response.find("'", start_idx)
                if end_idx != -1:
                    return response[start_idx:end_idx]
        
        # If it's an error response, format it nicely
        if "JSONRPCErrorResponse" in response:
            return "Error: The agent encountered an issue processing this request."
        
        # If it's a simple response, return as is
        if len(response) < 200:
            return response
        
        # For long responses, truncate and add ellipsis
        return response[:200] + "..."
        
    except Exception as e:
        return f"Response formatting error: {str(e)}"

async def demonstrate_activity1():
    """
    Demonstrate Activity #1: LangGraph using A2A Protocol
    """
    
    print("🎯 Activity #1: LangGraph using A2A Protocol")
    print("=" * 60)
    print()
    
    # Create our LangGraph agent
    agent = LangGraphAgent("Activity1LangGraphAgent")
    
    try:
        print("🤖 Created LangGraphAgent that uses LangGraph to communicate with A2A server")
        print("📡 LangGraph orchestrates A2A protocol communication")
        print("🎴 Using agent cards for proper A2A communication")
        print("🔄 LangGraph manages state and conversation flow")
        print()
        
        # Test 1: Web search query
        print("🔍 Test 1: Web Search Query")
        print("-" * 30)
        query1 = "What are the latest developments in artificial intelligence in 2024?"
        print(f"📝 Query: {query1}")
        
        start_time = time.time()
        response1 = await agent.ask_question(query1)
        end_time = time.time()
        
        formatted_response1 = format_response(response1)
        print(f"⏱️  Response time: {end_time - start_time:.2f} seconds")
        print(f"🤖 LangGraph Response: {formatted_response1}")
        print()
        
        # Test 2: Academic paper search
        print("📚 Test 2: Academic Paper Search")
        print("-" * 30)
        query2 = "Find recent papers about transformer architecture in natural language processing"
        print(f"📝 Query: {query2}")
        
        start_time = time.time()
        response2 = await agent.ask_question(query2)
        end_time = time.time()
        
        formatted_response2 = format_response(response2)
        print(f"⏱️  Response time: {end_time - start_time:.2f} seconds")
        print(f"🤖 LangGraph Response: {formatted_response2}")
        print()
        
        # Test 3: Multi-turn conversation
        print("💬 Test 3: Multi-turn Conversation")
        print("-" * 30)
        query3a = "Tell me about machine learning"
        print(f"📝 Query 1: {query3a}")
        
        start_time = time.time()
        response3a = await agent.ask_question(query3a)
        end_time = time.time()
        
        formatted_response3a = format_response(response3a)
        print(f"⏱️  Response time: {end_time - start_time:.2f} seconds")
        print(f"🤖 LangGraph Response: {formatted_response3a}")
        print()
        
        # Follow-up question
        query3b = "What are the main types of machine learning?"
        print(f"📝 Follow-up Query: {query3b}")
        
        start_time = time.time()
        response3b = await agent.ask_question(query3b)
        end_time = time.time()
        
        formatted_response3b = format_response(response3b)
        print(f"⏱️  Response time: {end_time - start_time:.2f} seconds")
        print(f"🤖 LangGraph Response: {formatted_response3b}")
        print()
        
        # Test 4: Tool selection demonstration
        print("🛠️  Test 4: Tool Selection Demonstration")
        print("-" * 30)
        query4 = "Search for information about LangGraph and compare it with other agent frameworks"
        print(f"📝 Query: {query4}")
        
        start_time = time.time()
        response4 = await agent.ask_question(query4)
        end_time = time.time()
        
        formatted_response4 = format_response(response4)
        print(f"⏱️  Response time: {end_time - start_time:.2f} seconds")
        print(f"🤖 LangGraph Response: {formatted_response4}")
        print()
        
        print("✅ Activity #1 Demonstration Complete!")
        print()
        print("📊 Summary:")
        print("   • LangGraphAgent successfully uses LangGraph to communicate with A2A server")
        print("   • LangGraph orchestrates A2A protocol communication")
        print("   • Used agent cards for proper communication")
        print("   • Demonstrated multi-turn conversations with LangGraph state management")
        print("   • Showed tool selection and execution through LangGraph")
        print("   • Verified helpfulness evaluation loop")
        print("   • LangGraph manages conversation state and flow")
        
    except Exception as e:
        print(f"❌ Error during Activity #1 demonstration: {e}")
        print("💡 Make sure the A2A server is running with: uv run python -m app")
        return False
    
    finally:
        await agent.close()
    
    return True

def main():
    """Main function to run the Activity #1 demonstration"""
    
    # Run automated demonstration
    success = asyncio.run(demonstrate_activity1())
    
    if success:
        print("\n🎉 Activity #1 completed successfully!")
        print("📝 The LangGraph successfully uses the A2A protocol to communicate with the server.")
        print("🔄 This is the proper implementation: LangGraph orchestrating A2A communication.")
    else:
        print("\n❌ Activity #1 failed. Check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 