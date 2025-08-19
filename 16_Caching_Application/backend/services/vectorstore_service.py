import os
import glob
from typing import List, Dict, Any
from pathlib import Path
import hashlib
import json

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader, DirectoryLoader, PyPDFLoader
import markdown
from bs4 import BeautifulSoup

class VectorstoreService:
    def __init__(self):
        self.qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        self.qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        self.collection_name = "python_docs"
        
        # Initialize Qdrant client
        self.client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)
        
        # Initialize sentence transformer for embeddings
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Create collection if it doesn't exist
        self._create_collection()
    
    def _create_collection(self):
        """Create the Qdrant collection if it doesn't exist."""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=384,  # all-MiniLM-L6-v2 embedding size
                        distance=Distance.COSINE
                    )
                )
                print(f"Created collection: {self.collection_name}")
        except Exception as e:
            print(f"Error creating collection: {e}")
    
    def _load_documents(self) -> List[Dict[str, Any]]:
        """Load documents from the data directory."""
        documents = []
        data_dir = Path("data")
        
        if not data_dir.exists():
            print("Data directory not found. Creating empty data directory.")
            data_dir.mkdir(exist_ok=True)
            return documents
        
        # Load markdown files
        md_files = glob.glob(str(data_dir / "**/*.md"), recursive=True)
        for file_path in md_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Convert markdown to plain text
                html = markdown.markdown(content)
                soup = BeautifulSoup(html, 'html.parser')
                text = soup.get_text()
                
                documents.append({
                    'content': text,
                    'source': file_path,
                    'type': 'markdown'
                })
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        # Load text files
        txt_files = glob.glob(str(data_dir / "**/*.txt"), recursive=True)
        for file_path in txt_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                documents.append({
                    'content': content,
                    'source': file_path,
                    'type': 'text'
                })
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        # Load PDF files
        pdf_files = glob.glob(str(data_dir / "**/*.pdf"), recursive=True)
        for file_path in pdf_files:
            try:
                loader = PyPDFLoader(file_path)
                pages = loader.load()
                
                for i, page in enumerate(pages):
                    documents.append({
                        'content': page.page_content,
                        'source': f"{file_path} (page {i+1})",
                        'type': 'pdf'
                    })
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        return documents
    
    def _chunk_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Split documents into chunks."""
        chunks = []
        
        for doc in documents:
            # Split the document content
            doc_chunks = self.text_splitter.split_text(doc['content'])
            
            for i, chunk in enumerate(doc_chunks):
                chunks.append({
                    'content': chunk,
                    'source': doc['source'],
                    'type': doc['type'],
                    'chunk_id': i,
                    'metadata': {
                        'source': doc['source'],
                        'type': doc['type'],
                        'chunk_id': i
                    }
                })
        
        return chunks
    
    def _create_embeddings(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create embeddings for document chunks."""
        for chunk in chunks:
            # Create embedding
            embedding = self.embedding_model.encode(chunk['content'])
            chunk['embedding'] = embedding.tolist()
            
            # Create unique ID
            content_hash = hashlib.md5(chunk['content'].encode()).hexdigest()
            chunk['id'] = content_hash
        
        return chunks
    
    async def ingest_documents(self) -> int:
        """Ingest documents from the data directory into the vectorstore."""
        print("Loading documents...")
        documents = self._load_documents()
        
        if not documents:
            print("No documents found in data directory.")
            return 0
        
        print(f"Found {len(documents)} documents")
        
        print("Chunking documents...")
        chunks = self._chunk_documents(documents)
        print(f"Created {len(chunks)} chunks")
        
        print("Creating embeddings...")
        chunks_with_embeddings = self._create_embeddings(chunks)
        
        print("Uploading to Qdrant...")
        points = []
        for chunk in chunks_with_embeddings:
            point = PointStruct(
                id=chunk['id'],
                vector=chunk['embedding'],
                payload={
                    'content': chunk['content'],
                    'source': chunk['source'],
                    'type': chunk['type'],
                    'chunk_id': chunk['chunk_id'],
                    'metadata': chunk['metadata']
                }
            )
            points.append(point)
        
        # Upload in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.client.upsert(
                collection_name=self.collection_name,
                points=batch
            )
        
        print(f"Successfully uploaded {len(points)} chunks to Qdrant")
        return len(points)
    
    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documents using semantic similarity."""
        # Create query embedding
        query_embedding = self.embedding_model.encode(query)
        
        # Search in Qdrant
        search_results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding.tolist(),
            limit=top_k,
            with_payload=True
        )
        
        # Format results
        results = []
        for result in search_results:
            results.append({
                'content': result.payload['content'],
                'source': result.payload['source'],
                'score': result.score,
                'metadata': result.payload.get('metadata', {})
            })
        
        return results 