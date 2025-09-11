#!/usr/bin/env python3
"""
Voyx Browser - A PyQt5-based web browser with AI integration and security features.
Designed for developers and security-conscious users.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile

# Import custom modules
from browser_window import BrowserWindow
from ai_panel import AIPanel
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
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create browser window with tabs
        self.browser_window = BrowserWindow(self.security_manager, self.userscript_manager, self.paywall_bypass, self)
        layout.addWidget(self.browser_window)
        
        # Create AI panel (initially hidden)
        self.ai_panel = AIPanel()
        layout.addWidget(self.ai_panel)
        self.ai_panel.hide()
        
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

def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Voyx Browser")
    app.setApplicationVersion("1.0.0")
    
    browser = VoyxBrowser()
    browser.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()