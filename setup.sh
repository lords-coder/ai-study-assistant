#!/bin/bash

# AI Study Assistant - Quick Start Script

echo "🚀 AI Study Assistant - Quick Start"
echo "=================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "✅ Python 3 is installed"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3 first."
    exit 1
fi

echo "✅ pip3 is installed"

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
SECRET_KEY=your-secret-key-here-change-this-in-production
AI_API_KEY=your-openai-api-key-here
AI_BASE_URL=https://api.openai.com/v1
DEBUG=True
EOF
    echo "✅ .env file created. Please edit it with your API key."
fi

# Create instance directory
mkdir -p instance

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your AI API key"
echo "2. Run: python3 ai_study_assistant.py"
echo "3. Open http://localhost:5000 in your browser"
echo ""
echo "🔧 If you don't have an AI API key, the app will work with fallback responses."
echo ""