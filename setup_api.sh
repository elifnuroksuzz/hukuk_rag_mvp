#!/bin/bash
# FastAPI Setup Script

echo "🚀 Setting up Hukuk RAG API..."

# Create API directory structure
mkdir -p api
mkdir -p api/routers
mkdir -p logs
mkdir -p temp_uploads

# Install FastAPI dependencies
echo "📦 Installing FastAPI dependencies..."
pip install -r api_requirements.txt

# Move main.py to api directory
mv api/main.py ./main.py 2>/dev/null || echo "main.py already in place"

echo "✅ API setup complete!"
echo ""
echo "🔧 To start the API server:"
echo "   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "🧪 To test the API:"
echo "   python test_api.py"
echo ""
echo "📖 API Documentation will be available at:"
echo "   http://localhost:8000/docs"