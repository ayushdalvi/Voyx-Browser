#!/usr/bin/env python3
"""
Voyx Browser - A PyQt5-based web browser with AI integration and security features.
Designed for developers and security-conscious users.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QSplitter, QAction
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile

# Import custom modules
from browser_window import BrowserWindow
from ai_panel import AIPanel
from screen_ai_panel import ScreenAIPanel
from userscript_manager import UserscriptManager
from security_manager import SecurityManager, UrlRequestInterceptor
from paywall_bypass import PaywallBypass

class VoyxBrowser(QMainWindow):
    """Main browser application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Voyx Browser")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize managers
        self.security_manager = SecurityManager()
        self.userscript_manager = UserscriptManager()
        self.paywall_bypass = PaywallBypass()
        
        # Create splitter for main layout
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(self.main_splitter)
        
        # Create browser window with tabs
        self.browser_window = BrowserWindow(self.security_manager, self.userscript_manager, self.paywall_bypass, self)
        self.main_splitter.addWidget(self.browser_window)
        
        # Create AI panel (initially hidden)
        self.ai_panel = AIPanel(self.browser_window)
        self.main_splitter.addWidget(self.ai_panel)
        self.ai_panel.hide()
        
        # Set initial sizes for the splitter (e.g., 70% for browser, 30% for AI panel)
        self.main_splitter.setSizes([int(self.width() * 0.7), int(self.width() * 0.3)])
        
        # Create Screen OCR AI panel (standalone window)
        self.screen_ai_panel = ScreenAIPanel()

        # Global shortcut to open the Screen OCR AI panel
        self.act_open_screen_ai = QAction("Open Screen OCR AI", self)
        self.act_open_screen_ai.setShortcut(QKeySequence("Ctrl+Shift+A"))
        self.act_open_screen_ai.triggered.connect(lambda: self.open_screen_ai_panel(auto_ask=False))
        self.addAction(self.act_open_screen_ai)

        # Apply initial security settings
        self.apply_security_settings()
        
    def apply_security_settings(self):
        """Apply security settings from security manager."""
        # Set up URL request interceptor for ad/tracker blocking
        interceptor = UrlRequestInterceptor(self.security_manager)
        profile = QWebEngineProfile.defaultProfile()
        profile.setUrlRequestInterceptor(interceptor)
        
    def toggle_ai_panel(self):
        """Toggle the AI panel visibility."""
        if self.ai_panel.isVisible():
            self.ai_panel.hide()
        else:
            self.ai_panel.show()

    def open_screen_ai_panel(self, auto_ask: bool = False):
        """Open the Screen OCR AI panel and feed current page selection as context."""
        try:
            tab = self.browser_window.current_tab()
            if not tab:
                self.screen_ai_panel.show_and_raise()
                return

            # Fetch selected text from the page via JS
            js = "(function(){return window.getSelection().toString();})()"
            def after_selection(sel_text):
                sel_text = sel_text or ""
                self.screen_ai_panel.show_and_raise()
                if sel_text.strip():
                    self.screen_ai_panel.set_selected_text(sel_text, auto_ask=auto_ask)
                else:
                    # If no selection, prefill with a hint and focus question
                    self.screen_ai_panel.prefill_question("Select text on screen (Ctrl+Shift+S) or paste content here.")
                    self.screen_ai_panel.focus_question_input()
            tab.page().runJavaScript(js, after_selection)
        except Exception:
            # Fallback: just show the panel
            self.screen_ai_panel.show_and_raise()

def main():
    """Main application entry point."""
    # Add Chromium command-line arguments for extension support
    sys.argv += [
        '--load-extension=' + os.path.abspath("extensions/test-extension"),
        '--enable-experimental-web-platform-features'
    ]
    app = QApplication(sys.argv)
    app.setApplicationName("Voyx Browser")
    app.setApplicationVersion("1.0.0")
    
    browser = VoyxBrowser()
    browser.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()