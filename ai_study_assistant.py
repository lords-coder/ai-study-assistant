	#!/usr/bin/env python3
"""
AI Study Assistant - Complete Python Application
A fully functional AI-powered study assistant for engineering and academic subjects
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# Flask for web interface
from flask import Flask, render_template_string, request, jsonify, session
from flask_cors import CORS

# AI integration (using OpenAI-compatible API)
import openai
import requests

# Configuration
@dataclass
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    DATABASE_URL = 'study_assistant.db'
    AI_API_KEY = os.environ.get('AI_API_KEY', 'your-api-key-here')
    AI_BASE_URL = os.environ.get('AI_BASE_URL', 'https://api.openai.com/v1')
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Database setup
class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                subject TEXT,
                confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create study_resources table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS study_resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                subject TEXT NOT NULL,
                url TEXT,
                type TEXT,
                difficulty TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        self.seed_default_resources()
    
    def seed_default_resources(self):
        """Seed default study resources"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if resources already exist
        cursor.execute("SELECT COUNT(*) FROM study_resources")
        if cursor.fetchone()[0] > 0:
            conn.close()
            return
        
        default_resources = [
            ("Khan Academy Mathematics", "Comprehensive math courses from basic arithmetic to advanced calculus", "Mathematics", "https://www.khanacademy.org/math", "Course", "Beginner"),
            ("MIT OpenCourseWare Physics", "Free physics courses from MIT including classical mechanics and quantum physics", "Physics", "https://ocw.mit.edu/courses/physics/", "Course", "Intermediate"),
            ("Introduction to Algorithms", "Classic computer science textbook covering algorithms and data structures", "Computer Science", "https://mitpress.mit.edu/book/introduction-algorithms-third-edition", "Book", "Advanced"),
            ("Engineering Mathematics", "Essential mathematical concepts for engineering students", "Engineering", "https://www.engineering.com/", "Article", "Intermediate"),
            ("Chemistry Basics", "Fundamental concepts of chemistry including atomic structure and chemical reactions", "Chemistry", "https://www.chemguide.co.uk/", "Article", "Beginner"),
            ("Biology: The Study of Life", "Introduction to biological concepts and living organisms", "Biology", "https://www.khanacademy.org/science/biology", "Course", "Beginner"),
        ]
        
        cursor.executemany('''
            INSERT INTO study_resources (title, description, subject, url, type, difficulty)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', default_resources)
        
        conn.commit()
        conn.close()

# AI Service
class AIService:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.subject_prompts = {
            'Mathematics': 'You are an expert mathematics tutor. Provide clear, step-by-step mathematical explanations with formulas and examples when applicable.',
            'Physics': 'You are an expert physics tutor. Explain physics concepts with real-world examples, equations, and practical applications.',
            'Chemistry': 'You are an expert chemistry tutor. Provide detailed chemical explanations with molecular structures, reactions, and laboratory context.',
            'Computer Science': 'You are an expert computer science tutor. Explain programming concepts, algorithms, and technical topics with code examples and best practices.',
            'Engineering': 'You are an expert engineering tutor covering all engineering disciplines. Provide practical, real-world engineering solutions with technical details.',
            'Biology': 'You are an expert biology tutor. Explain biological concepts with examples, processes, and scientific context.',
            'default': 'You are an expert academic tutor specializing in engineering and sciences. Provide comprehensive, educational answers with clear explanations and practical examples.'
        }
    
    def detect_subject(self, question: str) -> str:
        """Detect the subject from the question"""
        lower_question = question.lower()
        
        subject_keywords = {
            'Mathematics': ['math', 'calculus', 'algebra', 'geometry', 'statistics', 'probability', 'equation', 'formula', 'integral', 'derivative'],
            'Physics': ['physics', 'force', 'energy', 'motion', 'quantum', 'relativity', 'mechanics', 'wave', 'optics', 'thermodynamics'],
            'Chemistry': ['chemistry', 'chemical', 'molecule', 'atom', 'reaction', 'compound', 'element', 'bond', 'acid', 'base'],
            'Computer Science': ['programming', 'code', 'algorithm', 'data structure', 'software', 'computer', 'python', 'java', 'javascript', 'web'],
            'Engineering': ['engineering', 'civil', 'mechanical', 'electrical', 'chemical engineering', 'software engineering', 'design', 'manufacturing'],
            'Biology': ['biology', 'cell', 'genetics', 'evolution', 'organism', 'ecosystem', 'physiology', 'anatomy', 'species']
        }
        
        for subject, keywords in subject_keywords.items():
            if any(keyword in lower_question for keyword in keywords):
                return subject
        
        return 'default'
    
    async def generate_response(self, question: str, subject: Optional[str] = None) -> Dict:
        """Generate AI response for the given question"""
        try:
            detected_subject = subject or self.detect_subject(question)
            system_prompt = self.subject_prompts.get(detected_subject, self.subject_prompts['default'])
            
            # Prepare the prompt
            messages = [
                {
                    "role": "system",
                    "content": f"{system_prompt}\n\nGuidelines:\n- Provide comprehensive, accurate answers\n- Include relevant examples and practical applications\n- Explain complex concepts in simple terms\n- When appropriate, mention formulas, equations, or code snippets\n- Structure answers with clear headings and bullet points\n- Be educational and encouraging\n- If the question is unclear, ask for clarification\n- For engineering topics, consider safety and real-world constraints"
                },
                {
                    "role": "user",
                    "content": f"Question: {question}\n\nPlease provide a detailed, educational answer that helps me understand this concept thoroughly."
                }
            ]
            
            # Make API call
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-3.5-turbo",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result['choices'][0]['message']['content']
                
                return {
                    'answer': answer,
                    'detected_subject': detected_subject if detected_subject != 'default' else None,
                    'confidence': 0.85
                }
            else:
                raise Exception(f"API request failed with status {response.status_code}")
                
        except Exception as e:
            # Fallback response if AI fails
            return {
                'answer': self.generate_fallback_response(question, detected_subject),
                'detected_subject': detected_subject if detected_subject != 'default' else None,
                'confidence': 0.5
            }
    
    def generate_fallback_response(self, question: str, subject: str) -> str:
        """Generate a fallback response when AI is unavailable"""
        fallback_responses = {
            'Mathematics': f"""📐 **Mathematics Study Guide**

For your question about "{question}", here's a comprehensive approach:

**Key Mathematical Concepts:**
• Algebra: Equations, functions, and variables
• Calculus: Derivatives, integrals, and limits
• Statistics: Data analysis and probability
• Geometry: Shapes, angles, and theorems

**Study Tips:**
1. Practice daily problems to build intuition
2. Understand concepts before memorizing formulas
3. Use visual aids for complex topics
4. Apply math to real-world scenarios

**Common Formulas:**
- Quadratic Formula: x = (-b ± √(b²-4ac)) / 2a
- Pythagorean Theorem: a² + b² = c²
- Area of Circle: A = πr²

Would you like me to elaborate on any specific mathematical concept?""",
            
            'Physics': f"""⚛️ **Physics Study Guide**

Regarding your question about "{question}", here's what you need to know:

**Fundamental Physics Principles:**
• Newton's Laws of Motion
• Conservation of Energy and Momentum
• Wave Properties and Behaviors
• Electromagnetic Theory

**Key Equations:**
- F = ma (Newton's Second Law)
- E = mc² (Einstein's Equation)
- V = IR (Ohm's Law)

**Study Approach:**
1. Master the fundamentals first
2. Use diagrams and visualizations
3. Solve numerical problems regularly
4. Connect physics to everyday phenomena

Feel free to ask for more specific explanations!""",
            
            'default': f"""🎯 **General Study Advice**

For your question about "{question}", here's a structured learning approach:

**Effective Learning Strategies:**
1. **Active Learning**: Engage with material through practice
2. **Spaced Repetition**: Review material at increasing intervals
3. **Concept Mapping**: Create visual connections between ideas
4. **Practice Problems**: Apply knowledge through exercises

**Study Tips:**
• Break complex topics into smaller parts
• Use multiple learning resources
• Teach concepts to others
• Take regular breaks to maintain focus

**Time Management:**
• Use the Pomodoro Technique (25 min study, 5 min break)
• Prioritize difficult topics when fresh
• Create a consistent study schedule

Would you like more specific guidance on this topic?"""
        }
        
        return fallback_responses.get(subject, fallback_responses['default'])

# Initialize services
db = Database(app.config['DATABASE_URL'])
ai_service = AIService(app.config['AI_API_KEY'], app.config['AI_BASE_URL'])

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Study Assistant</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        .gradient-bg {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .chat-bubble {
            animation: slideIn 0.3s ease-out;
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .typing-indicator {
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 0.4; }
            50% { opacity: 1; }
        }
    </style>
</head>
<body class="bg-gray-50">
    <div id="app" class="min-h-screen flex flex-col">
        <!-- Header -->
        <header class="gradient-bg text-white p-4 shadow-lg">
            <div class="container mx-auto flex items-center justify-between">
                <div class="flex items-center gap-3">
                    <i data-lucide="brain" class="w-8 h-8"></i>
                    <div>
                        <h1 class="text-xl font-bold">AI Study Assistant</h1>
                        <p class="text-xs opacity-90">Powered by Python & AI</p>
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <span id="status" class="text-xs bg-green-400 px-2 py-1 rounded-full">Ready</span>
                </div>
            </div>
        </header>

        <!-- Subject Selection -->
        <div class="bg-white shadow-sm border-b">
            <div class="container mx-auto p-4">
                <h3 class="text-sm font-semibold mb-3 text-gray-700">Select Subject</h3>
                <div class="flex flex-wrap gap-2" id="subjectButtons">
                    <button onclick="selectSubject('')" class="subject-btn px-3 py-1 rounded-full text-sm font-medium bg-blue-500 text-white transition">
                        All Subjects
                    </button>
                    <button onclick="selectSubject('Mathematics')" class="subject-btn px-3 py-1 rounded-full text-sm font-medium bg-gray-200 text-gray-700 hover:bg-gray-300 transition">
                        📐 Mathematics
                    </button>
                    <button onclick="selectSubject('Physics')" class="subject-btn px-3 py-1 rounded-full text-sm font-medium bg-gray-200 text-gray-700 hover:bg-gray-300 transition">
                        ⚛️ Physics
                    </button>
                    <button onclick="selectSubject('Chemistry')" class="subject-btn px-3 py-1 rounded-full text-sm font-medium bg-gray-200 text-gray-700 hover:bg-gray-300 transition">
                        🧪 Chemistry
                    </button>
                    <button onclick="selectSubject('Computer Science')" class="subject-btn px-3 py-1 rounded-full text-sm font-medium bg-gray-200 text-gray-700 hover:bg-gray-300 transition">
                        💻 Computer Science
                    </button>
                    <button onclick="selectSubject('Engineering')" class="subject-btn px-3 py-1 rounded-full text-sm font-medium bg-gray-200 text-gray-700 hover:bg-gray-300 transition">
                        ⚙️ Engineering
                    </button>
                    <button onclick="selectSubject('Biology')" class="subject-btn px-3 py-1 rounded-full text-sm font-medium bg-gray-200 text-gray-700 hover:bg-gray-300 transition">
                        🧬 Biology
                    </button>
                </div>
            </div>
        </div>

        <!-- Main Content -->
        <main class="flex-1 container mx-auto p-4 max-w-4xl">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Chat Area -->
                <div class="lg:col-span-2">
                    <div class="bg-white rounded-lg shadow-lg h-[600px] flex flex-col">
                        <div class="p-4 border-b flex justify-between items-center">
                            <h2 class="font-semibold flex items-center gap-2">
                                <i data-lucide="message-circle" class="w-5 h-5"></i>
                                Study Q&A
                            </h2>
                            <div class="flex gap-2">
                                <button onclick="exportChat()" class="p-2 rounded hover:bg-gray-100 transition" title="Export Chat">
                                    <i data-lucide="download" class="w-4 h-4"></i>
                                </button>
                                <button onclick="clearChat()" class="p-2 rounded hover:bg-gray-100 transition" title="Clear Chat">
                                    <i data-lucide="trash-2" class="w-4 h-4"></i>
                                </button>
                            </div>
                        </div>
                        
                        <div id="chatContainer" class="flex-1 overflow-y-auto p-4 space-y-4">
                            <div class="text-center text-gray-500 py-8">
                                <i data-lucide="brain" class="w-16 h-16 mx-auto mb-4 text-gray-300"></i>
                                <h3 class="text-lg font-semibold mb-2">Ready to Learn?</h3>
                                <p class="text-sm mb-4">Ask any question about your studies and get instant, detailed answers.</p>
                                <div class="text-xs text-gray-400">
                                    <p>Example questions:</p>
                                    <ul class="mt-2 space-y-1">
                                        <li>• "Explain the concept of thermodynamics"</li>
                                        <li>• "How do neural networks work?"</li>
                                        <li>• "What is the difference between AC and DC current?"</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                        
                        <div class="p-4 border-t">
                            <form onsubmit="sendMessage(event)" class="flex gap-2">
                                <input 
                                    type="text" 
                                    id="messageInput"
                                    placeholder="Ask your study question..." 
                                    class="flex-1 px-4 py-2 border rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    required
                                >
                                <button type="submit" class="bg-blue-500 text-white p-2 rounded-full hover:bg-blue-600 transition">
                                    <i data-lucide="send" class="w-5 h-5"></i>
                                </button>
                            </form>
                        </div>
                    </div>
                </div>

                <!-- Sidebar -->
                <div class="space-y-4">
                    <!-- Features -->
                    <div class="bg-white rounded-lg shadow-lg p-4">
                        <h3 class="font-semibold mb-3 flex items-center gap-2">
                            <i data-lucide="star" class="w-5 h-5"></i>
                            Features
                        </h3>
                        <div class="space-y-3 text-sm">
                            <div class="flex items-start gap-3">
                                <i data-lucide="brain" class="w-5 h-5 text-blue-500 mt-0.5"></i>
                                <div>
                                    <h4 class="font-medium">AI-Powered</h4>
                                    <p class="text-xs text-gray-600">Advanced responses for academic questions</p>
                                </div>
                            </div>
                            <div class="flex items-start gap-3">
                                <i data-lucide="book-open" class="w-5 h-5 text-green-500 mt-0.5"></i>
                                <div>
                                    <h4 class="font-medium">Multi-Subject</h4>
                                    <p class="text-xs text-gray-600">Support for engineering, sciences, and more</p>
                                </div>
                            </div>
                            <div class="flex items-start gap-3">
                                <i data-lucide="database" class="w-5 h-5 text-purple-500 mt-0.5"></i>
                                <div>
                                    <h4 class="font-medium">Local Storage</h4>
                                    <p class="text-xs text-gray-600">Saves conversations for future reference</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Resources -->
                    <div class="bg-white rounded-lg shadow-lg p-4">
                        <h3 class="font-semibold mb-3 flex items-center gap-2">
                            <i data-lucide="book-open" class="w-5 h-5"></i>
                            Study Resources
                        </h3>
                        <button onclick="toggleResources()" class="w-full bg-blue-500 text-white py-2 rounded hover:bg-blue-600 transition text-sm">
                            <span id="resourceToggleText">Show Resources</span>
                        </button>
                        <div id="resourcesList" class="hidden mt-4 space-y-3 max-h-64 overflow-y-auto">
                            <!-- Resources will be loaded here -->
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script>
        // Initialize Lucide icons
        lucide.createIcons();

        // Global state
        let selectedSubject = '';
        let messages = [];
        let showResources = false;

        // Initialize app
        function init() {
            loadResources();
            loadMessages();
        }

        function selectSubject(subject) {
            selectedSubject = subject;
            
            // Update button styles
            document.querySelectorAll('.subject-btn').forEach(btn => {
                btn.className = 'subject-btn px-3 py-1 rounded-full text-sm font-medium bg-gray-200 text-gray-700 hover:bg-gray-300 transition';
            });
            
            event.target.className = 'subject-btn px-3 py-1 rounded-full text-sm font-medium bg-blue-500 text-white transition';
        }

        async function sendMessage(event) {
            event.preventDefault();
            
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message
            addMessage(message, 'user');
            input.value = '';
            
            // Show typing indicator
            showTypingIndicator();
            
            try {
                const response = await fetch('/api/ask', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        question: message,
                        subject: selectedSubject
                    }),
                });

                if (!response.ok) {
                    throw new Error('Failed to get answer');
                }

                const data = await response.json();
                hideTypingIndicator();
                addMessage(data.answer, 'assistant');
                
                // Save to localStorage
                saveMessages();
                
            } catch (error) {
                hideTypingIndicator();
                addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
            }
        }

        function addMessage(content, type) {
            const chatContainer = document.getElementById('chatContainer');
            
            // Clear welcome message if it's the first message
            if (messages.length === 0) {
                chatContainer.innerHTML = '';
            }
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `chat-bubble flex ${type === 'user' ? 'justify-end' : 'justify-start'}`;
            
            const bubbleClass = type === 'user' 
                ? 'bg-blue-500 text-white rounded-2xl rounded-br-sm max-w-[80%]' 
                : 'bg-gray-100 text-gray-800 rounded-2xl rounded-bl-sm max-w-[80%]';
            
            messageDiv.innerHTML = `
                <div class="${bubbleClass} p-3">
                    <div class="text-sm whitespace-pre-wrap">${content}</div>
                    <div class="text-xs ${type === 'user' ? 'text-blue-100' : 'text-gray-500'} mt-1">
                        ${new Date().toLocaleTimeString()}
                    </div>
                </div>
            `;
            
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
            
            // Save message
            messages.push({ content, type, timestamp: new Date().toISOString() });
            
            // Recreate icons
            lucide.createIcons();
        }

        function showTypingIndicator() {
            const chatContainer = document.getElementById('chatContainer');
            const indicator = document.createElement('div');
            indicator.id = 'typingIndicator';
            indicator.className = 'flex justify-start';
            indicator.innerHTML = `
                <div class="bg-gray-100 text-gray-800 rounded-2xl rounded-bl-sm p-3 typing-indicator">
                    <div class="flex items-center gap-2">
                        <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                        <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                        <span class="text-sm">AI is thinking...</span>
                    </div>
                </div>
            `;
            chatContainer.appendChild(indicator);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function hideTypingIndicator() {
            const indicator = document.getElementById('typingIndicator');
            if (indicator) {
                indicator.remove();
            }
        }

        function clearChat() {
            if (confirm('Are you sure you want to clear all messages?')) {
                messages = [];
                localStorage.removeItem('studyMessages');
                location.reload();
            }
        }

        function exportChat() {
            if (messages.length === 0) {
                alert('No messages to export!');
                return;
            }
            
            const chatText = messages.map(msg => 
                `[${new Date(msg.timestamp).toLocaleString()}] ${msg.type.toUpperCase()}:\n${msg.content}\n`
            ).join('\n---\n\n');
            
            const blob = new Blob([chatText], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `study-session-${new Date().toISOString().split('T')[0]}.txt`;
            a.click();
            URL.revokeObjectURL(url);
        }

        function toggleResources() {
            showResources = !showResources;
            const resourcesList = document.getElementById('resourcesList');
            const toggleText = document.getElementById('resourceToggleText');
            
            if (showResources) {
                resourcesList.classList.remove('hidden');
                toggleText.textContent = 'Hide Resources';
            } else {
                resourcesList.classList.add('hidden');
                toggleText.textContent = 'Show Resources';
            }
        }

        async function loadResources() {
            try {
                const response = await fetch('/api/resources');
                const resources = await response.json();
                
                const resourcesList = document.getElementById('resourcesList');
                resourcesList.innerHTML = resources.map(resource => `
                    <div class="p-3 border rounded-lg">
                        <h4 class="font-medium text-sm">${resource.title}</h4>
                        <p class="text-xs text-gray-600 mt-1">${resource.description}</p>
                        <div class="flex gap-2 mt-2">
                            <span class="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">${resource.subject}</span>
                            <span class="text-xs bg-gray-100 text-gray-800 px-2 py-1 rounded">${resource.type}</span>
                            <span class="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">${resource.difficulty}</span>
                        </div>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Failed to load resources:', error);
            }
        }

        function saveMessages() {
            localStorage.setItem('studyMessages', JSON.stringify(messages));
        }

        function loadMessages() {
            const saved = localStorage.getItem('studyMessages');
            if (saved) {
                messages = JSON.parse(saved);
                if (messages.length > 0) {
                    document.getElementById('chatContainer').innerHTML = '';
                    messages.forEach(msg => {
                        addMessage(msg.content, msg.type);
                    });
                }
            }
        }

        // Initialize when DOM is loaded
        document.addEventListener('DOMContentLoaded', init);
    </script>
</body>
</html>
"""

# Routes
@app.route('/')
def index():
    """Main page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/ask', methods=['POST'])
def ask_question():
    """Handle AI question requests"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        subject = data.get('subject', '')
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        # Generate AI response
        import asyncio
        response = asyncio.run(ai_service.generate_response(question, subject))
        
        # Save conversation to database
        session_id = session.get('session_id', 'default')
        conn = sqlite3.connect(app.config['DATABASE_URL'])
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversations (session_id, question, answer, subject, confidence)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, question, response['answer'], response.get('detected_subject'), response.get('confidence')))
        
        conn.commit()
        conn.close()
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error processing question: {e}")
        return jsonify({'error': 'Failed to process question'}), 500

@app.route('/api/resources', methods=['GET'])
def get_resources():
    """Get study resources"""
    try:
        conn = sqlite3.connect(app.config['DATABASE_URL'])
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT title, description, subject, url, type, difficulty
            FROM study_resources
            ORDER BY created_at DESC
        ''')
        
        resources = []
        for row in cursor.fetchall():
            resources.append({
                'title': row[0],
                'description': row[1],
                'subject': row[2],
                'url': row[3],
                'type': row[4],
                'difficulty': row[5]
            })
        
        conn.close()
        return jsonify(resources)
        
    except Exception as e:
        print(f"Error fetching resources: {e}")
        return jsonify({'error': 'Failed to fetch resources'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.before_request
def before_request():
    """Initialize session"""
    if 'session_id' not in session:
        session['session_id'] = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(datetime.now()))}"

# Main execution
if __name__ == '__main__':
    print("🚀 Starting AI Study Assistant...")
    print("📚 Features:")
    print("   • AI-powered study assistance")
    print("   • Multiple subject support")
    print("   • Conversation history")
    print("   • Study resources")
    print("   • Export functionality")
    print()
    print("🌐 Access the app at: http://localhost:5000")
    print("🔧 API Documentation:")
    print("   • POST /api/ask - Ask questions")
    print("   • GET /api/resources - Get study resources")
    print("   • GET /api/health - Health check")
    print()
    
    # Create required directories
    os.makedirs('instance', exist_ok=True)
    
    # Run the app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config['DEBUG']
    )