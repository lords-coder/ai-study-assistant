AI Study Assistant - Complete Python Application
A fully functional AI-powered study assistant built with Python, Flask, and AI integration.

🚀 Quick Start
1. Install Dependencies
bash

Line Wrapping

Collapse
Copy
1
pip install -r requirements.txt
2. Set Up Environment Variables
Create a .env file:

env

Line Wrapping

Collapse
Copy
1
2
3
4
SECRET_KEY=your-secret-key-here
AI_API_KEY=your-openai-api-key-here
AI_BASE_URL=https://api.openai.com/v1
DEBUG=True
3. Run the Application
bash

Line Wrapping

Collapse
Copy
1
python ai_study_assistant.py
4. Access the App
Open your browser and go to: http://localhost:5000

📚 Features
🤖 AI-Powered Learning
Intelligent Responses: Advanced AI answers for academic questions
Subject Detection: Automatically identifies the subject from your questions
Contextual Understanding: Provides detailed, educational explanations
📖 Multi-Subject Support
Mathematics: Algebra, Calculus, Statistics, Geometry
Physics: Mechanics, Thermodynamics, Electromagnetism, Quantum
Chemistry: Organic, Inorganic, Physical, Analytical
Computer Science: Programming, Algorithms, Data Structures
Engineering: Civil, Mechanical, Electrical, Chemical
Biology: Molecular, Cellular, Ecology, Evolution
💾 Data Management
SQLite Database: Local storage for conversations and resources
Session Management: Tracks user sessions and conversation history
Export Functionality: Download study sessions as text files
🎨 User Interface
Modern Design: Clean, responsive web interface
Real-time Chat: Interactive conversation with AI
Mobile Friendly: Works on all devices
Dark/Light Theme: Easy on the eyes
🔧 Technical Details
Architecture
Backend: Python with Flask
Database: SQLite for local storage
AI Integration: OpenAI-compatible API
Frontend: HTML, Tailwind CSS, JavaScript
API Endpoints
GET / - Main web interface
POST /api/ask - Ask AI questions
GET /api/resources - Get study resources
GET /api/health - Health check
Database Schema
conversations - Stores chat history
study_resources - Educational materials
sessions - User session tracking
🛠️ Configuration
Environment Variables
SECRET_KEY: Flask secret key for sessions
AI_API_KEY: OpenAI API key (or compatible)
AI_BASE_URL: AI API base URL
DEBUG: Enable debug mode
Customization
Modify subject_prompts in AIService class
Add new subjects and keywords
Customize the HTML template
Extend database schema as needed
📱 Usage
Asking Questions
Select a subject (optional)
Type your question in the chat
Get instant AI-powered answers
Export conversations for later review
Example Questions
"Explain the concept of thermodynamics"
"How do neural networks work?"
"What is the difference between AC and DC current?"
"Help me understand calculus derivatives"
🔒 Security
Session-based authentication
Input validation and sanitization
Error handling and logging
CORS protection
🚀 Deployment
Local Development
bash

Line Wrapping

Collapse
Copy
1
python ai_study_assistant.py
Production Deployment
bash

Line Wrapping

Collapse
Copy
1
2
3
4
5
6
7
# Set production environment variables
export DEBUG=False
export SECRET_KEY=your-production-secret-key

# Use a production WSGI server
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 ai_study_assistant:app
Docker Deployment
dockerfile

Line Wrapping

Collapse
Copy
1
2
3
4
5
6
7
8
9
10
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ai_study_assistant.py .
EXPOSE 5000

CMD ["python", "ai_study_assistant.py"]
🤝 Contributing
Fork the repository
Create a feature branch
Make your changes
Test thoroughly
Submit a pull request
📄 License
This project is open source and available under the MIT License.

🆘 Troubleshooting
Common Issues
Port 5000 already in use: Change the port in the app.run() call
API key issues: Verify your AI API key and base URL
Database errors: Ensure write permissions for the database file
Import errors: Install all required dependencies
Getting Help
Check the console output for error messages
Verify environment variables are set correctly
Ensure all dependencies are installed
Test with a simple question first
🌟 What's Next?
Planned Features
 User authentication and profiles
 File upload for document analysis
 Voice input/output support
 Multi-language support
 Advanced analytics dashboard
 Collaborative study sessions
Version History
v1.0.0: Initial release with core AI study features
🎓 Start your learning journey with AI Study Assistant - Your Python-powered tutor for academic success!