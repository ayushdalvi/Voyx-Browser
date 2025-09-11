"""
AI Panel Module - Handles AI interactions using OpenRouter API.
Provides a panel for user queries and AI responses.
"""

import json
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                             QLineEdit, QPushButton, QComboBox, QLabel, 
                             QSplitter, QScrollArea, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QTextCursor
import requests

class AIWorker(QThread):
    """Worker thread for handling AI API requests."""
    
    response_received = pyqtSignal(str, bool)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, api_key, model, prompt, context=None):
        super().__init__()
        self.api_key = api_key
        self.model = model
        self.prompt = prompt
        self.context = context
        
    def run(self):
        """Execute the AI request."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Prepare the message with optional context
            messages = []
            if self.context:
                messages.append({"role": "system", "content": self.context})
            messages.append({"role": "user", "content": self.prompt})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content']
                self.response_received.emit(ai_response, True)
            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                self.error_occurred.emit(error_msg)
                
        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(f"Network error: {str(e)}")
        except Exception as e:
            self.error_occurred.emit(f"Unexpected error: {str(e)}")

class AIPanel(QWidget):
    """AI interaction panel with OpenRouter API integration."""
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.current_model = "openai/gpt-3.5-turbo"
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # API settings section
        settings_frame = QFrame()
        settings_frame.setFrameStyle(QFrame.StyledPanel)
        settings_layout = QVBoxLayout(settings_frame)
        
        # API key input
        api_key_layout = QHBoxLayout()
        api_key_label = QLabel("API Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter OpenRouter API key")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        if self.api_key:
            self.api_key_input.setText(self.api_key)
        api_key_layout.addWidget(api_key_label)
        api_key_layout.addWidget(self.api_key_input)
        settings_layout.addLayout(api_key_layout)
        
        # Model selection
        model_layout = QHBoxLayout()
        model_label = QLabel("Model:")
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "openai/gpt-3.5-turbo",
            "openai/gpt-4",
            "anthropic/claude-2",
            "meta-llama/llama-2-70b-chat",
            "google/palm-2-chat-bison"
        ])
        self.model_combo.setCurrentText(self.current_model)
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        settings_layout.addLayout(model_layout)
        
        layout.addWidget(settings_frame)
        
        # Splitter for chat area
        splitter = QSplitter(Qt.Vertical)
        
        # Response area
        response_frame = QFrame()
        response_frame.setFrameStyle(QFrame.StyledPanel)
        response_layout = QVBoxLayout(response_frame)
        
        response_label = QLabel("AI Response:")
        self.response_text = QTextEdit()
        self.response_text.setReadOnly(True)
        self.response_text.setFont(QFont("Monospace", 10))
        response_layout.addWidget(response_label)
        response_layout.addWidget(self.response_text)
        
        splitter.addWidget(response_frame)
        
        # Input area
        input_frame = QFrame()
        input_frame.setFrameStyle(QFrame.StyledPanel)
        input_layout = QVBoxLayout(input_frame)
        
        input_label = QLabel("Your Question:")
        self.input_text = QTextEdit()
        self.input_text.setMaximumHeight(100)
        self.input_text.setPlaceholderText("Type your question here...")
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.send_btn = QPushButton("Send")
        self.send_btn.setDefault(True)
        self.clear_btn = QPushButton("Clear")
        button_layout.addWidget(self.send_btn)
        button_layout.addWidget(self.clear_btn)
        input_layout.addLayout(button_layout)
        
        splitter.addWidget(input_frame)
        splitter.setSizes([400, 200])
        
        layout.addWidget(splitter)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
    def setup_connections(self):
        """Set up signal connections."""
        self.send_btn.clicked.connect(self.send_query)
        self.clear_btn.clicked.connect(self.clear_input)
        self.api_key_input.textChanged.connect(self.update_api_key)
        self.model_combo.currentTextChanged.connect(self.update_model)
        
    def update_api_key(self, key):
        """Update the API key."""
        self.api_key = key.strip()
        os.environ["OPENROUTER_API_KEY"] = self.api_key
        
    def update_model(self, model):
        """Update the selected model."""
        self.current_model = model
        
    def send_query(self):
        """Send query to OpenRouter API."""
        if not self.api_key:
            self.status_label.setText("Error: Please enter an API key")
            return
            
        query = self.input_text.toPlainText().strip()
        if not query:
            self.status_label.setText("Error: Please enter a question")
            return
            
        self.status_label.setText("Sending request...")
        self.send_btn.setEnabled(False)
        
        # Get current page context if available
        context = self.get_page_context()
        
        # Start worker thread
        self.worker = AIWorker(self.api_key, self.current_model, query, context)
        self.worker.response_received.connect(self.handle_response)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()
        
    def handle_response(self, response, success):
        """Handle AI response."""
        self.send_btn.setEnabled(True)
        if success:
            self.response_text.setPlainText(response)
            self.status_label.setText("Response received")
        else:
            self.status_label.setText(f"Error: {response}")
            
    def handle_error(self, error_msg):
        """Handle API errors."""
        self.send_btn.setEnabled(True)
        self.status_label.setText(f"Error: {error_msg}")
        self.response_text.setPlainText(f"Error: {error_msg}")
        
    def clear_input(self):
        """Clear the input field."""
        self.input_text.clear()
        
    def get_page_context(self):
        """Get context from current web page (to be implemented with browser integration)."""
        # This will be connected to the browser to get current page content
        return "You are a helpful AI assistant integrated into a web browser. Provide concise and helpful responses."
        
    def set_page_context(self, context):
        """Set context from current web page."""
        # This method will be called by the browser to provide page context
        self.current_context = context