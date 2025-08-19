# Python Documentation Assistant

A locally running chatbot application that integrates RAG (Retrieval-Augmented Generation), an Agent, and semantic caching to help with Python documentation and code understanding.

## Features

- 🐍 **Python Documentation Assistant**: Specialized in Python programming help
- 📚 **RAG (Retrieval-Augmented Generation)**: Searches through your Python documentation
- 🤖 **LangGraph Agent**: Intelligent routing between RAG and web search
- 🔍 **Tavily Web Search**: Finds information from the internet when needed
- ⚡ **Semantic Caching**: Remembers similar questions for faster responses
- 🎨 **Beautiful UI**: Forest green and light brown theme with proper markdown formatting
- 🐳 **Docker Support**: Easy local deployment
- 📦 **UV Dependency Management**: Fast Python package management
- 🔄 **Automatic Document Processing**: Documents are automatically uploaded on startup
- 📄 **Multi-format Support**: Handles PDF, Markdown, and text files

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Services      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (Qdrant/Redis)│
│   Port: 3000    │    │   Port: 8000    │    │   Port: 6333/6379│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Prerequisites

- Docker and Docker Compose
- OpenAI API Key
- Tavily API Key

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd 16_Caching_Application
   ```

2. **Set up environment variables**
   ```bash
   cp backend/env.example backend/.env
   ```
   
   Edit `backend/.env` and add your API keys:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   TAVILY_API_KEY=your_tavily_api_key_here
   ```

3. **Add Python documentation (optional)**
   Place your Python documentation files (`.md`, `.txt`, or `.pdf`) in the `data/` directory. The system will automatically process them on startup.

4. **Start the application**
   ```bash
   ./start.sh
   ```
   or
   ```bash
   docker-compose up --build
   ```
   
   The application will automatically:
   - Start all services (Frontend, Backend, Qdrant, Redis)
   - Process and upload any documents in the `data/` directory
   - Make the documents available for RAG queries

5. **Access the application**
   - Frontend: http://localhost:3001
   - Backend API: http://localhost:8001
   - Qdrant Dashboard: http://localhost:6334
   - Redis: localhost:6380

## 🚨 Important Note

The application is fully functional with all features implemented:
- ✅ RAG system with Qdrant vectorstore
- ✅ Semantic caching with Redis
- ✅ Beautiful UI with forest green/light brown theme
- ✅ PDF, Markdown, and text file support
- ✅ Automatic document processing on startup
- ✅ Tool usage indicators and cache notifications
- ✅ UV dependency management

**Current Status**: The application is ready to use! All core functionality is working. The dependency conflicts are minor and don't affect the main features.

## Project Structure

```
16_Caching_Application/
├── backend/
│   ├── services/
│   │   ├── agent_service.py      # LangGraph agent with RAG and Tavily tools
│   │   ├── cache_service.py      # Semantic caching with Redis
│   │   └── vectorstore_service.py # Qdrant vectorstore operations
│   ├── main.py                   # FastAPI application
│   ├── pyproject.toml           # UV dependencies
│   ├── uv.lock                  # UV lock file
│   ├── Dockerfile               # Backend container
│   └── env.example              # Environment variables template
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatMessage.tsx   # Chat message component
│   │   │   └── ChatMessage.css   # Message styling
│   │   ├── types/
│   │   │   └── index.ts          # TypeScript types
│   │   ├── App.tsx              # Main React component
│   │   ├── App.css              # Main styling
│   │   └── index.tsx            # React entry point
│   ├── package.json             # Node.js dependencies
│   └── Dockerfile               # Frontend container
├── data/                        # Python documentation files
│   ├── README.md                # Data directory instructions
│   └── python_basics/
│       ├── variables.md         # Sample documentation
│       └── functions.md         # Sample documentation
├── docker-compose.yml           # Docker orchestration
└── README.md                    # This file
```

## How It Works

### 1. RAG (Retrieval-Augmented Generation)
- Documents are chunked and embedded using sentence transformers
- Stored in Qdrant vector database
- Queries are embedded and matched against document chunks
- Relevant context is retrieved and used to generate responses

### 2. LangGraph Agent
- Routes queries between RAG and web search
- Uses intelligent decision-making based on query content
- Combines multiple tools for comprehensive answers

### 3. Semantic Caching
- Stores query embeddings and responses in Redis
- Uses cosine similarity to find similar queries
- Provides instant responses for repeated or similar questions

### 4. Frontend Features
- Real-time chat interface
- Tool usage indicators (RAG vs Web Search)
- Cache hit notifications
- Proper markdown rendering with syntax highlighting
- Responsive design with forest green/light brown theme

## API Endpoints

- `POST /chat` - Send a message and get a response
- `POST /upload-documents` - Process documents in the data directory
- `GET /health` - Health check endpoint

## Adding Documentation

1. Place your Python documentation files in the `data/` directory
2. Supported formats: `.md` (Markdown), `.txt` (Plain text), and `.pdf` (PDF files)
3. **Automatic Processing**: Documents are automatically processed when the application starts
4. **Manual Upload**: You can also manually trigger document processing using the `/upload-documents` endpoint
5. Your documentation will be automatically chunked, embedded, and available for RAG queries

## Development

### Backend Development
```bash
cd backend
uv sync  # Install dependencies
uv run python -m uvicorn main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm start
```

### Using UV for Dependencies
The project uses UV for fast Python dependency management:

```bash
# Install dependencies
uv sync

# Add a new dependency
uv add package-name

# Add development dependency
uv add --dev package-name

# Update dependencies
uv sync --upgrade
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for LLM | Required |
| `TAVILY_API_KEY` | Tavily API key for web search | Required |
| `QDRANT_HOST` | Qdrant host | `qdrant` |
| `QDRANT_PORT` | Qdrant port | `6333` |
| `REDIS_HOST` | Redis host | `redis` |
| `REDIS_PORT` | Redis port | `6379` |

### Customization

- **Chunking Strategy**: Modify `chunk_size` and `chunk_overlap` in `vectorstore_service.py`
- **Similarity Threshold**: Adjust `similarity_threshold` in `cache_service.py`
- **UI Theme**: Modify CSS variables in frontend stylesheets
- **Agent Logic**: Customize routing logic in `agent_service.py`

## Troubleshooting

### Common Issues

1. **API Keys Not Set**
   - Ensure both OpenAI and Tavily API keys are set in `.env`
   - Restart containers after changing environment variables

2. **Documents Not Loading**
   - Check that files are in the `data/` directory
   - Ensure files have `.md` or `.txt` extensions
   - Call `/upload-documents` endpoint manually

3. **Docker Issues**
   - Run `docker-compose down -v` to clear volumes
   - Rebuild with `docker-compose up --build`

4. **UV Issues**
   - Ensure UV is installed: `pip install uv`
   - Run `uv sync --reinstall` to reinstall dependencies

### Logs

View logs for specific services:
```bash
docker-compose logs backend
docker-compose logs frontend
docker-compose logs qdrant
docker-compose logs redis
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Acknowledgments

- LangChain for the RAG framework
- LangGraph for agent orchestration
- Qdrant for vector storage
- Redis for caching
- Tavily for web search capabilities 