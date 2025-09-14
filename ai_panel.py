"""
AI Panel Module - Handles AI interactions using OpenRouter API.
"""

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
    QComboBox, QLabel, QSplitter, QFrame, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt5.QtGui import QFont
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
    
    def __init__(self, browser_window=None):
        super().__init__()
        self.browser_window = browser_window
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.current_model = "meta-llama/llama-3-8b-instruct:free"
        self.conversation_history = []
        self.page_content = ""
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header
        header = QLabel("🤖 Voyx AI Assistant")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # API settings
        settings_frame = QFrame()
        settings_frame.setFrameStyle(QFrame.StyledPanel)
        settings_layout = QVBoxLayout(settings_frame)
        
        # API key
        api_layout = QHBoxLayout()
        api_layout.addWidget(QLabel("API Key:"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter OpenRouter API key")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setText(self.api_key)
        api_layout.addWidget(self.api_key_input)
        settings_layout.addLayout(api_layout)
        
        # Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "meta-llama/llama-3-8b-instruct:free",
            "microsoft/phi-3-mini-4k-instruct:free",
            "google/gemma-2-9b-it:free",
            "qwen/qwen2.5-7b-instruct:free"
        ])
        self.model_combo.setCurrentText(self.current_model)
        model_layout.addWidget(self.model_combo)
        settings_layout.addLayout(model_layout)
        
        layout.addWidget(settings_frame)
        
        # Page context controls
        context_frame = QFrame()
        context_frame.setFrameStyle(QFrame.StyledPanel)
        context_layout = QHBoxLayout(context_frame)
        
        self.use_context_cb = QCheckBox("Use page context")
        self.use_context_cb.setChecked(True)
        self.selection_only_cb = QCheckBox("Selection only")
        self.refresh_btn = QPushButton("Refresh Context")
        self.summarize_btn = QPushButton("Summarize Page")
        self.summarize_selection_btn = QPushButton("Summarize Selection")
        
        context_layout.addWidget(self.use_context_cb)
        context_layout.addWidget(self.selection_only_cb)
        context_layout.addWidget(self.refresh_btn)
        context_layout.addWidget(self.summarize_btn)
        context_layout.addWidget(self.summarize_selection_btn)
        context_layout.addStretch()
        
        layout.addWidget(context_frame)
        
        # Page info
        self.page_info = QLabel("Page: No page loaded")
        self.page_info.setWordWrap(True)
        layout.addWidget(self.page_info)
        
        # Chat area
        splitter = QSplitter(Qt.Vertical)
        
        # Response area
        response_frame = QFrame()
        response_frame.setFrameStyle(QFrame.StyledPanel)
        response_layout = QVBoxLayout(response_frame)
        
        response_layout.addWidget(QLabel("AI Response:"))
        self.response_text = QTextEdit()
        self.response_text.setReadOnly(True)
        self.response_text.setFont(QFont("Arial", 10))
        response_layout.addWidget(self.response_text)
        
        splitter.addWidget(response_frame)
        
        # Input area
        input_frame = QFrame()
        input_frame.setFrameStyle(QFrame.StyledPanel)
        input_layout = QVBoxLayout(input_frame)
        
        input_layout.addWidget(QLabel("Your Question:"))
        self.input_text = QTextEdit()
        self.input_text.setMaximumHeight(100)
        self.input_text.setPlaceholderText("Ask about this page or anything else...")
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
        splitter.setSizes([300, 150])
        
        layout.addWidget(splitter)
        
        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
    def setup_connections(self):
        """Set up signal connections."""
        self.send_btn.clicked.connect(self.send_query)
        self.clear_btn.clicked.connect(self.clear_input)
        self.api_key_input.textChanged.connect(self.update_api_key)
        self.model_combo.currentTextChanged.connect(self.update_model)
        self.refresh_btn.clicked.connect(self.refresh_context)
        self.summarize_btn.clicked.connect(self.summarize_page)
        self.summarize_selection_btn.clicked.connect(self.summarize_selection)
        
        # Auto-refresh context when tab changes
        if self.browser_window:
            try:
                self.browser_window.tab_widget.currentChanged.connect(self.on_tab_changed)
                # Connect to current tab signals
                current_tab = self.browser_window.current_tab()
                if current_tab:
                    current_tab.loadFinished.connect(self.on_page_loaded)
                    current_tab.urlChanged.connect(self.on_url_changed)
            except:
                pass
        
        # Initial context refresh
        QTimer.singleShot(1000, self.refresh_context)
        
        # Auto-refresh timer
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.refresh_context)
        self.auto_refresh_timer.start(5000)  # Refresh every 5 seconds
        
    def update_api_key(self, key):
        """Update the API key."""
        self.api_key = key.strip()
        
    def update_model(self, model):
        """Update the selected model."""
        self.current_model = model
        
    def refresh_context(self):
        """Refresh page context from current tab."""
        if not self.browser_window:
            self.page_info.setText("Page: No browser context")
            return
            
        current_tab = self.browser_window.current_tab()
        if not current_tab:
            self.page_info.setText("Page: No active tab")
            return
            
        # Get basic page info
        title = current_tab.title() or "Untitled"
        url = current_tab.url().toString()
        
        # Extract page content using JavaScript
        js_code = r"""
        (function() {
            try {
                // Get page content
                let content = '';
                
                // Get selected text
                const selection = window.getSelection().toString();
                if (selection.trim()) {
                    content += 'SELECTED TEXT:\n' + selection + '\n\n';
                }
                
                // Get page title and meta
                content += 'TITLE: ' + (document.title || '') + '\n';
                content += 'URL: ' + (location.href || '') + '\n\n';
                
                // Get meta description
                const metaDesc = document.querySelector('meta[name="description"]');
                if (metaDesc) {
                    content += 'DESCRIPTION: ' + metaDesc.content + '\n\n';
                }
                
                // Get main headings
                const headings = document.querySelectorAll('h1, h2, h3');
                if (headings.length > 0) {
                    content += 'HEADINGS:\n';
                    for (let i = 0; i < Math.min(headings.length, 10); i++) {
                        const heading = headings[i];
                        content += heading.tagName + ': ' + heading.textContent.trim() + '\n';
                    }
                    content += '\n';
                }
                
                // Get main content
                let mainText = '';
                const contentSelectors = [
                    'main', 'article', '.content', '.main-content',
                    '.post-content', '.entry-content', '#content'
                ];
                
                for (const selector of contentSelectors) {
                    const element = document.querySelector(selector);
                    if (element) {
                        mainText = element.textContent || element.innerText || '';
                        break;
                    }
                }
                
                // Fallback to body
                if (!mainText && document.body) {
                    mainText = document.body.textContent || document.body.innerText || '';
                }
                
                // Clean and limit text
                if (mainText) {
                    mainText = mainText.replace(/\\s+/g, ' ').trim();
                    if (mainText.length > 4000) {
                        mainText = mainText.substring(0, 4000) + '...';
                    }
                    content += 'CONTENT:\n' + mainText;
                }
                
                return content || 'No readable content found.';
            } catch (e) {
                return 'Error extracting content: ' + e.message;
            }
        })();
        """
        
        # Execute JavaScript and handle result
        current_tab.page().runJavaScript(js_code, self.on_content_extracted)
        
        # Update page info display
        self.page_info.setText(f"Page: {title[:50]}{'...' if len(title) > 50 else ''}\nURL: {url[:60]}{'...' if len(url) > 60 else ''}")
        
    def on_content_extracted(self, result):
        """Handle extracted page content."""
        self.page_content = result or "No content extracted."
        
        # Check if there's selected text
        has_selection = 'SELECTED TEXT:' in self.page_content
        selection_status = " (Text selected)" if has_selection else ""
        
        self.status_label.setText(f"Page content updated{selection_status}")
        
        # Enable/disable selection-only features
        self.summarize_selection_btn.setEnabled(has_selection)
        if not has_selection:
            self.selection_only_cb.setChecked(False)
        
    def get_page_context(self):
        """Get current page context for AI."""
        if not self.use_context_cb.isChecked():
            return None
            
        if not self.page_content:
            return "You are a helpful AI assistant. The user is browsing the web but no page content is available."
        
        # Check if selection only mode is enabled
        if self.selection_only_cb.isChecked():
            # Extract only selected text from page content
            if 'SELECTED TEXT:' in self.page_content:
                selected_part = self.page_content.split('SELECTED TEXT:')[1].split('\n\n')[0]
                context = f"""You are an AI assistant. The user has selected specific text from a webpage. Focus your response on this selected text only.

SELECTED TEXT:
{selected_part}

Instructions:
- Focus strictly on the selected text
- Provide analysis, explanation, or answers based only on this selection
- Be concise and relevant to the selected content"""
                return context
            else:
                return "You are a helpful AI assistant. The user requested to focus on selected text, but no text is currently selected on the page."
            
        context = f"""You are an AI assistant integrated into the Voyx web browser. 
You have access to the current page content. Use this information to provide helpful, accurate responses.

CURRENT PAGE CONTENT:
{self.page_content}

Instructions:
- Answer questions about the page content when relevant
- Provide helpful information based on what's shown
- If the page content doesn't contain enough information, say so
- Be concise but comprehensive in your responses"""
        
        return context
        
    def send_query(self):
        """Send query to AI."""
        if not self.api_key:
            self.status_label.setText("Error: Please enter API key")
            return
            
        query = self.input_text.toPlainText().strip()
        if not query:
            self.status_label.setText("Error: Please enter a question")
            return
            
        self.status_label.setText("Sending request...")
        self.send_btn.setEnabled(False)
        
        # Add to conversation
        self.conversation_history.append({"role": "user", "content": query})
        self.display_conversation()
        
        # Get context
        context = self.get_page_context()
        
        # Start worker
        self.worker = AIWorker(self.api_key, self.current_model, query, context)
        self.worker.response_received.connect(self.handle_response)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()
        
    def handle_response(self, response, success):
        """Handle AI response."""
        self.send_btn.setEnabled(True)
        if success:
            self.conversation_history.append({"role": "assistant", "content": response})
            self.display_conversation()
            self.status_label.setText("Response received")
            self.input_text.clear()
        else:
            self.status_label.setText(f"Error: {response}")
            
    def handle_error(self, error_msg):
        """Handle errors."""
        self.send_btn.setEnabled(True)
        self.status_label.setText(f"Error: {error_msg}")
        
    def display_conversation(self):
        """Display conversation history."""
        self.response_text.clear()
        for message in self.conversation_history:
            if message["role"] == "user":
                self.response_text.append(f"<b>🧑 You:</b> {message['content']}\n")
            else:
                self.response_text.append(f"<b>🤖 AI:</b> {message['content']}\n")
                
        # Scroll to bottom
        cursor = self.response_text.textCursor()
        cursor.movePosition(cursor.End)
        self.response_text.setTextCursor(cursor)
        
    def clear_input(self):
        """Clear input field."""
        self.input_text.clear()
        
    def summarize_page(self):
        """Summarize current page."""
        # Check if we have content first
        if not self.page_content or 'CONTENT:' not in self.page_content:
            self.status_label.setText("Refreshing page content...")
            self.refresh_context()
            QTimer.singleShot(2000, self._do_summarize)
        else:
            self._do_summarize()
            
    def _do_summarize(self):
        """Execute page summarization."""
        if not self.page_content or self.page_content == "No content extracted." or 'CONTENT:' not in self.page_content:
            self.status_label.setText("No page content available to summarize. Try refreshing the page.")
            return
            
        self.input_text.setPlainText("Please provide a comprehensive summary of this page, including the main points, key information, and any important details.")
        self.use_context_cb.setChecked(True)
        self.selection_only_cb.setChecked(False)
        self.status_label.setText("Summarizing page content...")
        self.send_query()
    
    def summarize_selection(self):
        """Summarize only selected text."""
        if not self.page_content or 'SELECTED TEXT:' not in self.page_content:
            self.status_label.setText("No text selected. Please select text on the page first.")
            return
            
        self.input_text.setPlainText("Please provide a summary and analysis of the selected text, including key points, main ideas, and any important insights.")
        self.use_context_cb.setChecked(True)
        self.selection_only_cb.setChecked(True)
        self.send_query()
    
    def on_tab_changed(self, index):
        """Handle tab change events."""
        QTimer.singleShot(500, self.refresh_context)
        
        # Connect to new tab's signals
        if self.browser_window:
            current_tab = self.browser_window.current_tab()
            if current_tab:
                current_tab.loadFinished.connect(self.on_page_loaded)
                current_tab.urlChanged.connect(self.on_url_changed)
    
    def on_page_loaded(self, ok):
        """Handle page load completion."""
        if ok:
            QTimer.singleShot(2000, self.refresh_context)
    
    def on_url_changed(self, url):
        """Handle URL changes."""
        QTimer.singleShot(1000, self.refresh_context)