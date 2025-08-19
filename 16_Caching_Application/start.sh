#!/bin/bash

echo "🐍 Python Documentation Assistant Setup"
echo "======================================"

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  Environment file not found!"
    echo "📝 Creating backend/.env from template..."
    cp backend/env.example backend/.env
    echo "✅ Please edit backend/.env and add your API keys:"
    echo "   - OPENAI_API_KEY"
    echo "   - TAVILY_API_KEY"
    echo ""
    echo "🔑 Get your API keys from:"
    echo "   - OpenAI: https://platform.openai.com/api-keys"
    echo "   - Tavily: https://tavily.com/"
    echo ""
    read -p "Press Enter after adding your API keys..."
fi

# Check if data directory has files
if [ ! "$(ls -A data/)" ]; then
    echo "📁 Data directory is empty. Sample documentation has been provided."
    echo "   You can add your own Python documentation files to the data/ directory."
else
    echo "📚 Found documentation files in data/ directory"
    echo "   These will be automatically processed when the application starts"
fi

echo "🚀 Starting the application..."
echo "   This will build and start all services (this may take a few minutes on first run)"
echo ""

# Start the application
docker-compose up --build

echo ""
echo "✅ Application started!"
echo "🌐 Access the application at: http://localhost:3001"
echo "📚 API documentation at: http://localhost:8001/docs"
echo ""
echo "📖 Documents are automatically processed on startup"
echo "🔄 You can manually re-upload documents using: curl -X POST http://localhost:8001/upload-documents"
echo ""
echo "To stop the application, press Ctrl+C or run: docker-compose down" 