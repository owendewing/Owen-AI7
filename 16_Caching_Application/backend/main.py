from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
import asyncio
from typing import List, Optional
import openai
import redis
import qdrant_client
from sentence_transformers import SentenceTransformer
import tiktoken
import PyPDF2
import io

# Initialize services
app = FastAPI(title="Python Documentation Assistant", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize Redis for caching
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

# Initialize Qdrant client
qdrant_client_instance = qdrant_client.QdrantClient(
    host=os.getenv("QDRANT_HOST", "qdrant"),
    port=int(os.getenv("QDRANT_PORT", 6333))
)

# Initialize sentence transformer
model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize tokenizer
tokenizer = tiktoken.get_encoding("cl100k_base")

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    tool_used: str
    cached: bool
    session_id: str

class DocumentUploadResponse(BaseModel):
    message: str
    documents_processed: int

# Utility functions
def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks."""
    tokens = tokenizer.encode(text)
    chunks = []
    
    for i in range(0, len(tokens), chunk_size - overlap):
        chunk_tokens = tokens[i:i + chunk_size]
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)
    
    return chunks

def load_documents():
    """Load documents from the data directory."""
    documents = []
    data_dir = "data"
    
    if not os.path.exists(data_dir):
        return documents
    
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            file_path = os.path.join(root, file)
            
            if file.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    documents.append({
                        'content': content,
                        'source': file_path
                    })
            
            elif file.endswith('.md'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    documents.append({
                        'content': content,
                        'source': file_path
                    })
            
            elif file.endswith('.pdf'):
                try:
                    with open(file_path, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        for page_num, page in enumerate(pdf_reader.pages):
                            content = page.extract_text()
                            documents.append({
                                'content': content,
                                'source': f"{file_path} (page {page_num + 1})"
                            })
                except Exception as e:
                    print(f"Error processing PDF {file_path}: {e}")
    
    return documents

def ingest_documents():
    """Process and store documents in Qdrant."""
    documents = load_documents()
    
    if not documents:
        print("No documents found to process")
        return
    
    # Create collection if it doesn't exist
    try:
        qdrant_client_instance.get_collection("python_docs")
        print("Collection 'python_docs' already exists")
    except Exception as e:
        print(f"Creating collection 'python_docs': {e}")
        try:
            qdrant_client_instance.create_collection(
                collection_name="python_docs",
                vectors_config={"size": 384, "distance": "Cosine"}
            )
            print("Collection 'python_docs' created successfully")
        except Exception as create_error:
            print(f"Error creating collection: {create_error}")
            raise
    
    # Process documents
    points = []
    for i, doc in enumerate(documents):
        # Chunk the document
        chunks = chunk_text(doc['content'])
        
        for j, chunk in enumerate(chunks):
            # Generate embedding
            embedding = model.encode(chunk).tolist()
            
            points.append({
                "id": len(points),
                "vector": embedding,
                "payload": {
                    "text": chunk,
                    "source": doc['source'],
                    "chunk_index": j
                }
            })
    
    # Upload to Qdrant
    if points:
        qdrant_client_instance.upsert(
            collection_name="python_docs",
            points=points
        )
        print(f"Processed {len(documents)} documents into {len(points)} chunks")

def search_documents(query: str, limit: int = 5):
    """Search for relevant documents."""
    try:
        # Generate query embedding
        query_embedding = model.encode(query).tolist()
        
        # Search in Qdrant
        results = qdrant_client_instance.search(
            collection_name="python_docs",
            query_vector=query_embedding,
            limit=limit
        )
        
        return [result.payload['text'] for result in results]
    except Exception as e:
        print(f"Error searching documents: {e}")
        # Try to process documents if collection doesn't exist
        try:
            print("Attempting to process documents...")
            ingest_documents()
            # Retry search
            query_embedding = model.encode(query).tolist()
            results = qdrant_client_instance.search(
                collection_name="python_docs",
                query_vector=query_embedding,
                limit=limit
            )
            return [result.payload['text'] for result in results]
        except Exception as retry_error:
            print(f"Error in retry search: {retry_error}")
            return []



def cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors."""
    import numpy as np
    a = np.array(a).flatten()
    b = np.array(b).flatten()
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))



def get_semantic_cache_response(query: str) -> Optional[str]:
    """Get cached response using Qdrant semantic search."""
    try:
        # Generate embedding for the query
        query_embedding = model.encode(query).tolist()
        
        # Search in the semantic cache collection
        results = qdrant_client_instance.search(
            collection_name="semantic_cache",
            query_vector=query_embedding,
            limit=10,  # Get more results to see what's available
            score_threshold=0.5  # Adjusted threshold for semantic matching
        )
        
        print(f"Semantic cache search for '{query}' returned {len(results)} results")
        for i, result in enumerate(results):
            print(f"  Result {i+1}: '{result.payload['question']}' (similarity: {result.score:.3f})")
        
        if results:
            best_result = results[0]
            print(f"Found semantic cache hit with similarity {best_result.score:.3f}")
            return best_result.payload['answer']
        
        return None
    except Exception as e:
        print(f"Error in semantic cache lookup: {e}")
        return None

def clear_semantic_cache():
    """Clear the semantic cache collection."""
    try:
        qdrant_client_instance.delete_collection("semantic_cache")
        print("🗑️ Cleared semantic cache collection")
    except Exception as e:
        print(f"Error clearing semantic cache: {e}")

def store_semantic_cache(query: str, answer: str):
    """Store question-answer pair in semantic cache."""
    try:
        # Generate embedding for the query
        query_embedding = model.encode(query).tolist()
        
        # Create semantic cache collection if it doesn't exist
        try:
            qdrant_client_instance.get_collection("semantic_cache")
        except:
            qdrant_client_instance.create_collection(
                collection_name="semantic_cache",
                vectors_config={"size": 384, "distance": "Cosine"}
            )
        
        # Store the question-answer pair
        point_id = len(query) + hash(query)  # Simple ID generation
        qdrant_client_instance.upsert(
            collection_name="semantic_cache",
            points=[{
                "id": point_id,
                "vector": query_embedding,
                "payload": {
                    "question": query,
                    "answer": answer
                }
            }]
        )
        print(f"Stored semantic cache for: '{query}' (ID: {point_id})")
    except Exception as e:
        print(f"Error storing semantic cache: {e}")

def search_web(query: str) -> str:
    """Search the web using Tavily API."""
    try:
        import tavily
        tavily_client = tavily.Client(api_key=os.getenv("TAVILY_API_KEY"))
        search_result = tavily_client.search(query, search_depth="basic", max_results=3)
        
        if search_result and 'results' in search_result:
            return "\n\n".join([result.get('content', '') for result in search_result['results']])
        return ""
    except Exception as e:
        print(f"Error searching web: {e}")
        return ""

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    print("🚀 Starting Python Documentation Assistant...")
    
    # Wait for services to be ready
    await asyncio.sleep(5)
    
    # Clear semantic cache on startup
    print("🗑️ Clearing semantic cache...")
    clear_semantic_cache()
    
    print("📚 Processing documents...")
    try:
        ingest_documents()
        print("✅ Documents processed successfully")
    except Exception as e:
        print(f"⚠️ Warning: Could not process documents on startup: {e}")
        print("Documents will be processed when first needed")
    
    print("✅ Application ready!")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Python Documentation Assistant is running"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint with RAG and caching."""
    query = request.message.strip()
    
    if not query:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Step 1: Check semantic cache first (vector similarity with past queries)
    print(f"🔍 Checking semantic cache for: '{query}'")
    cached_response = get_semantic_cache_response(query)
    if cached_response:
        print(f"✅ Found semantic cache hit for: '{query}'")
        return ChatResponse(
            response=cached_response,
            tool_used="semantic_cache",
            cached=True,
            session_id=request.session_id or "default"
        )
    
    print(f"❌ No semantic cache hit, falling back to RAG for: '{query}'")
    
    # Step 2: If not found in cache, perform RAG (retrieve docs + generate response)
    relevant_docs = search_documents(query)
    
    if relevant_docs:
        # Use RAG with document context
        context = "\n\n".join(relevant_docs[:3])
        
        prompt = f"""You are a helpful Python documentation assistant. Use the following context to answer the user's question. Provide a comprehensive, detailed answer that covers the key concepts.

Context:
{context}

Question: {query}

Provide a detailed answer:"""
        
        try:
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful Python documentation assistant. Provide clear, accurate, and comprehensive answers based on the context provided. Always give detailed explanations that cover the key concepts thoroughly."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3  # Lower temperature for more consistent responses
            )
            
            answer = response.choices[0].message.content
            tool_used = "rag"
            
            # Store in semantic cache for future similar queries
            store_semantic_cache(query, answer)
        except Exception as e:
            print(f"Error with OpenAI API: {e}")
            answer = "I'm sorry, I encountered an error while processing your request."
            tool_used = "error"
    else:
        # Fallback to web search
        web_results = search_web(query)
        
        if web_results:
            prompt = f"""You are a helpful Python documentation assistant. Use the following web search results to answer the user's question:

Search Results:
{web_results}

Question: {query}

Answer:"""
            
            try:
                client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                                    messages=[
                    {"role": "system", "content": "You are a helpful Python documentation assistant. Provide clear, accurate, and comprehensive answers based on the search results provided. Always give detailed explanations that cover the key concepts thoroughly."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3  # Lower temperature for more consistent responses
                )
                
                answer = response.choices[0].message.content
                tool_used = "tavily"
                
                # Store in semantic cache for future similar queries
                store_semantic_cache(query, answer)
            except Exception as e:
                print(f"Error with OpenAI API: {e}")
                answer = "I'm sorry, I encountered an error while processing your request."
                tool_used = "error"
        else:
            # Direct OpenAI response
            try:
                client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                                    messages=[
                    {"role": "system", "content": "You are a helpful Python documentation assistant. Provide clear, accurate, and comprehensive answers about Python programming. Always give detailed explanations that cover the key concepts thoroughly."},
                    {"role": "user", "content": query}
                ],
                max_tokens=1000,
                temperature=0.3  # Lower temperature for more consistent responses
                )
                
                answer = response.choices[0].message.content
                tool_used = "openai"
                
                # Store in semantic cache for future similar queries
                store_semantic_cache(query, answer)
            except Exception as e:
                print(f"Error with OpenAI API: {e}")
                answer = "I'm sorry, I encountered an error while processing your request. Please check your OpenAI API key."
                tool_used = "error"
    
    return ChatResponse(
        response=answer,
        tool_used=tool_used,
        cached=False,
        session_id=request.session_id or "default"
    )

@app.post("/upload-documents", response_model=DocumentUploadResponse)
async def upload_documents():
    """Re-upload documents endpoint."""
    try:
        ingest_documents()
        return DocumentUploadResponse(
            message="Documents processed successfully",
            documents_processed=len(load_documents())
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing documents: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 