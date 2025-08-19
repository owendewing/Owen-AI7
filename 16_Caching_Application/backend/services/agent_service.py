import os
import uuid
from typing import Tuple, List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from tavily import TavilyClient
import json

class AgentService:
    def __init__(self, vectorstore_service, cache_service):
        self.vectorstore_service = vectorstore_service
        self.cache_service = cache_service
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize Tavily client
        self.tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        
        # Create the agent graph
        self.agent = self._create_agent()
    
    def _create_agent(self):
        """Create the LangGraph agent with RAG and Tavily tools."""
        
        # Define the state
        class AgentState:
            def __init__(self):
                self.messages = []
                self.tool_results = []
                self.current_tool = None
                self.final_answer = None
        
        # Define tools
        async def rag_tool(state):
            """RAG tool for searching Python documentation."""
            query = state.messages[-1].content
            
            # Search the vectorstore
            results = await self.vectorstore_service.search(query, top_k=5)
            
            if results:
                # Format the results
                context = "\n\n".join([
                    f"Source: {result['source']}\nContent: {result['content']}"
                    for result in results
                ])
                
                # Generate response using LLM
                system_prompt = """You are a helpful Python documentation assistant. 
                Use the provided context to answer the user's question about Python.
                If the context doesn't contain enough information, say so.
                Always provide accurate and helpful information."""
                
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=f"Context:\n{context}\n\nQuestion: {query}")
                ]
                
                response = self.llm.invoke(messages)
                
                state.tool_results.append({
                    "tool": "RAG",
                    "result": response.content,
                    "sources": [result['source'] for result in results]
                })
                state.current_tool = "RAG"
            else:
                state.tool_results.append({
                    "tool": "RAG",
                    "result": "No relevant documentation found in the knowledge base.",
                    "sources": []
                })
                state.current_tool = "RAG"
            
            return state
        
        async def tavily_tool(state):
            """Tavily search tool for web search."""
            query = state.messages[-1].content
            
            try:
                # Search using Tavily
                search_result = self.tavily_client.search(
                    query=query,
                    search_depth="basic",
                    max_results=5
                )
                
                # Extract relevant information
                if search_result.get('results'):
                    context = "\n\n".join([
                        f"Title: {result.get('title', 'N/A')}\nContent: {result.get('content', 'N/A')}"
                        for result in search_result['results']
                    ])
                    
                    # Generate response using LLM
                    system_prompt = """You are a helpful Python documentation assistant.
                    Use the provided web search results to answer the user's question about Python.
                    Focus on providing accurate and relevant information."""
                    
                    messages = [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=f"Search Results:\n{context}\n\nQuestion: {query}")
                    ]
                    
                    response = self.llm.invoke(messages)
                    
                    state.tool_results.append({
                        "tool": "Tavily",
                        "result": response.content,
                        "sources": [result.get('url', 'N/A') for result in search_result['results']]
                    })
                    state.current_tool = "Tavily"
                else:
                    state.tool_results.append({
                        "tool": "Tavily",
                        "result": "No relevant information found through web search.",
                        "sources": []
                    })
                    state.current_tool = "Tavily"
                    
            except Exception as e:
                state.tool_results.append({
                    "tool": "Tavily",
                    "result": f"Error searching the web: {str(e)}",
                    "sources": []
                })
                state.current_tool = "Tavily"
            
            return state
        
        async def router(state):
            """Route to the appropriate tool based on the query."""
            query = state.messages[-1].content.lower()
            
            # Simple routing logic - can be enhanced
            if any(keyword in query for keyword in ['python', 'code', 'function', 'class', 'module', 'library']):
                return "rag_tool"
            else:
                return "tavily_tool"
        
        async def final_answer(state):
            """Generate the final answer."""
            if state.tool_results:
                latest_result = state.tool_results[-1]
                state.final_answer = latest_result["result"]
            else:
                state.final_answer = "I couldn't find a suitable answer to your question."
            
            return state
        
        # Create the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("router", router)
        workflow.add_node("rag_tool", rag_tool)
        workflow.add_node("tavily_tool", tavily_tool)
        workflow.add_node("final_answer", final_answer)
        
        # Add edges
        workflow.add_edge("router", "rag_tool")
        workflow.add_edge("router", "tavily_tool")
        workflow.add_edge("rag_tool", "final_answer")
        workflow.add_edge("tavily_tool", "final_answer")
        workflow.add_edge("final_answer", END)
        
        return workflow.compile()
    
    async def process_query(self, query: str, session_id: str = None) -> Tuple[str, str, bool, str]:
        """Process a user query through the agent with caching."""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Check cache first
        cached_response, cached_tool, similarity = await self.cache_service.get_cached_response(query)
        
        if cached_response:
            return cached_response, cached_tool, True, session_id
        
        # Process through agent
        try:
            # Initialize state
            state = {
                "messages": [HumanMessage(content=query)],
                "tool_results": [],
                "current_tool": None,
                "final_answer": None
            }
            
            # Run the agent
            result = await self.agent.ainvoke(state)
            
            # Extract results
            response = result["final_answer"]
            tool_used = result.get("current_tool", "Unknown")
            
            # Cache the response
            await self.cache_service.cache_response(query, response, tool_used)
            
            return response, tool_used, False, session_id
            
        except Exception as e:
            error_response = f"I encountered an error while processing your query: {str(e)}"
            return error_response, "Error", False, session_id 