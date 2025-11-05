@echo off
REM AI Study Assistant - Quick Start Script for Windows

echo 🚀 AI Study Assistant - Quick Start
echo ==================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python first.
    pause
    exit /b 1
)

echo ✅ Python is installed

REM Check if pip is installed
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip is not installed. Please install pip first.
    pause
    exit /b 1
)

echo ✅ pip is installed

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed successfully

REM Create .env file if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file...
    (
        echo SECRET_KEY=your-secret-key-here-change-this-in-production
        echo AI_API_KEY=your-openai-api-key-here
        echo AI_BASE_URL=https://api.openai.com/v1
        echo DEBUG=True
    ) > .env
    echo ✅ .env file created. Please edit it with your API key.
)

REM Create instance directory
if not exist instance mkdir instance

echo.
echo 🎉 Setup complete!
echo.
echo 📋 Next steps:
echo 1. Edit .env file with your AI API key
echo 2. Run: python ai_study_assistant.py
echo 3. Open http://localhost:5000 in your browser
echo.
echo 🔧 If you don't have an AI API key, the app will work with fallback responses.
echo.
pause