
"""
Browser Window Module - Handles tabbed browsing and navigation controls.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QLineEdit, QPushButton, QToolBar, QAction, QMenu,
                             QScrollArea, QFrame, QDialog, QDialogButtonBox)
from PyQt5.QtCore import QUrl, Qt, pyqtSlot
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PyQt5.QtGui import QIcon, QKeySequence

class BrowserTab(QWebEngineView):
    """Individual browser tab with custom web engine view."""
    
    def __init__(self, security_manager, userscript_manager, paywall_bypass, browser_window=None, extensions_dir="extensions"):
        super().__init__()
        # Initialize dependencies first
        self.security_manager = security_manager
        self.userscript_manager = userscript_manager
        self.paywall_bypass = paywall_bypass
        self.browser_window = browser_window
        
        # Configure web engine profile for extensions
        self.profile = QWebEngineProfile("VoyxProfile", self)
        self.profile.setPersistentStoragePath(extensions_dir)
        self.profile.setCachePath(extensions_dir + "/cache")
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
        # Enable extension support
        self.page().settings().setAttribute(QWebEngineSettings.PluginsEnabled, True)
        self.page().settings().setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        
        # Setup console logging
        self.page().javaScriptConsoleMessage = lambda level, message, line, source: print(f"CONSOLE: {message}")
        self.setUrl(QUrl("https://www.google.com"))
        
        # Verify extensions loaded
        

    
        
        # Connect signals
        self.urlChanged.connect(self.on_url_changed)
        self.loadFinished.connect(self.on_load_finished)
        
    def on_url_changed(self, url):
        """Handle URL changes."""
        # Apply security checks
        if self.security_manager.should_block_url(url):
            self.setHtml("<h1>URL Blocked</h1><p>This URL has been blocked by security settings.</p>")
            return
            
    def on_load_finished(self, ok):
        """Handle page load completion."""
        if ok:
            # Inject userscripts
            self.userscript_manager.inject_scripts(self)
            # Bypass paywalls
            self.paywall_bypass.bypass_paywall(self)
            # Apply dark theme if enabled
            if self.browser_window and self.browser_window.is_dark_theme_enabled():
                self.browser_window.inject_website_dark_theme()
            
    def createWindow(self, window_type):
        """Handle new window requests (for target=_blank links)."""
        if window_type == QWebEnginePage.WebBrowserTab:
            if self.browser_window:
                return self.browser_window.create_new_tab()
            else:
                # Fallback: create a new tab in the current tab widget
                # This might not work perfectly, but it's better than crashing
                return super().createWindow(window_type)
        return super().createWindow(window_type)

class BrowserWindow(QWidget):
    """Main browser window with tabbed interface and navigation controls."""
    
    def __init__(self, security_manager, userscript_manager, paywall_bypass, main_window=None):
        super().__init__()
        self.security_manager = security_manager
        self.userscript_manager = userscript_manager
        self.paywall_bypass = paywall_bypass
        self.main_window = main_window
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create navigation toolbar
        self.nav_toolbar = QToolBar()
        self.nav_toolbar.setMovable(False)
        layout.addWidget(self.nav_toolbar)

        # Navigation buttons
        self.back_btn = QAction("←", self)
        self.forward_btn = QAction("→", self)
        self.reload_btn = QAction("↻", self)
        self.home_btn = QAction("🏠", self)

        self.nav_toolbar.addAction(self.back_btn)
        self.nav_toolbar.addAction(self.forward_btn)
        self.nav_toolbar.addAction(self.reload_btn)
        self.nav_toolbar.addAction(self.home_btn)

        # URL bar
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter URL or search...")
        self.nav_toolbar.addWidget(self.url_bar)

        # New tab button
        self.new_tab_btn = QAction("➕", self)
        self.nav_toolbar.addAction(self.new_tab_btn)

        # Bookmark current page button
        self.bookmark_btn = QAction("🔖", self)
        self.bookmark_btn.setToolTip("Bookmark this page")
        self.nav_toolbar.addAction(self.bookmark_btn)

        # Dark theme toggle button
        self.theme_toggle_btn = QAction("🌙", self)
        self.theme_toggle_btn.setToolTip("Toggle Dark Theme")
        self.nav_toolbar.addAction(self.theme_toggle_btn)

        # AI Panel toggle button
        self.ai_toggle_btn = QAction("🤖", self)
        self.ai_toggle_btn.setToolTip("Toggle AI Panel")
        self.nav_toolbar.addAction(self.ai_toggle_btn)

        # Security settings button
        self.settings_btn = QAction("⚙️", self)
        self.settings_btn.setToolTip("Security Settings")
        self.nav_toolbar.addAction(self.settings_btn)
        
        # Create scrollable bookmarks area
        self.bookmarks_scroll_area = QScrollArea()
        self.bookmarks_scroll_area.setFixedHeight(40)
        self.bookmarks_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.bookmarks_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.bookmarks_scroll_area.setWidgetResizable(True)
        
        # Create container widget for bookmarks
        self.bookmarks_container = QWidget()
        self.bookmarks_layout = QHBoxLayout(self.bookmarks_container)
        self.bookmarks_layout.setContentsMargins(2, 2, 2, 2)
        self.bookmarks_layout.setSpacing(2)
        
        self.bookmarks_scroll_area.setWidget(self.bookmarks_container)
        layout.addWidget(self.bookmarks_scroll_area)
        
        # Initialize bookmarks list
        self.bookmarks = {
            "Google": "https://www.google.com",
            "YouTube": "https://www.youtube.com",
            "GitHub": "https://github.com"
        }
        
        # Add default bookmarks
        self.add_default_bookmarks()
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        layout.addWidget(self.tab_widget)
        
        # Create initial tab
        self.create_new_tab()
        
    def setup_connections(self):
        """Set up signal connections."""
        # Navigation buttons
        self.back_btn.triggered.connect(self.navigate_back)
        self.forward_btn.triggered.connect(self.navigate_forward)
        self.reload_btn.triggered.connect(self.reload_page)
        self.home_btn.triggered.connect(self.navigate_home)
        self.new_tab_btn.triggered.connect(self.create_new_tab)
        self.bookmark_btn.triggered.connect(self.bookmark_current_page)
        self.theme_toggle_btn.triggered.connect(self.toggle_dark_theme)
        self.ai_toggle_btn.triggered.connect(self.toggle_ai_panel)
        self.settings_btn.triggered.connect(self.open_security_settings)

        # URL bar
        self.url_bar.returnPressed.connect(self.navigate_to_url)

        # Tab widget
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
    def create_new_tab(self):
        """Create a new browser tab."""
        tab = BrowserTab(self.security_manager, self.userscript_manager, self.paywall_bypass, self, "extensions")
        index = self.tab_widget.addTab(tab, "New Tab")
        self.tab_widget.setCurrentIndex(index)
        
        # Connect tab signals
        tab.titleChanged.connect(lambda title: self.update_tab_title(index, title))
        tab.urlChanged.connect(lambda url: self.update_url_bar(url))
        
        return tab
        
    def close_tab(self, index):
        """Close a browser tab."""
        if self.tab_widget.count() > 1:
            widget = self.tab_widget.widget(index)
            widget.deleteLater()
            self.tab_widget.removeTab(index)
            
    def on_tab_changed(self, index):
        """Handle tab change events."""
        if index >= 0:
            current_tab = self.tab_widget.widget(index)
            self.update_url_bar(current_tab.url())
            
    def navigate_back(self):
        """Navigate back in current tab."""
        current_tab = self.current_tab()
        if current_tab:
            current_tab.back()
            
    def navigate_forward(self):
        """Navigate forward in current tab."""
        current_tab = self.current_tab()
        if current_tab:
            current_tab.forward()
            
    def reload_page(self):
        """Reload current page."""
        current_tab = self.current_tab()
        if current_tab:
            current_tab.reload()
            
    def navigate_home(self):
        """Navigate to home page."""
        current_tab = self.current_tab()
        if current_tab:
            current_tab.setUrl(QUrl("https://www.google.com"))
            
    def navigate_to_url(self):
        """Navigate to URL entered in the URL bar."""
        url = self.url_bar.text()
        if not url.startswith(('http://', 'https://')):
            if '.' in url:
                url = 'https://' + url
            else:
                url = 'https://www.google.com/search?q=' + url.replace(' ', '+')
                
        current_tab = self.current_tab()
        if current_tab:
            current_tab.setUrl(QUrl(url))
            
    def update_url_bar(self, url):
        """Update URL bar with current page URL."""
        if url.toString() != self.url_bar.text():
            self.url_bar.setText(url.toString())
            self.url_bar.setCursorPosition(0)
            
    def update_tab_title(self, index, title):
        """Update tab title."""
        if title:
            # Truncate long titles
            if len(title) > 20:
                title = title[:20] + '...'
            self.tab_widget.setTabText(index, title)
            
    def current_tab(self):
        """Get the current active tab."""
        index = self.tab_widget.currentIndex()
        if index >= 0:
            return self.tab_widget.widget(index)
        return None

    def toggle_ai_panel(self):
        """Toggle the AI panel visibility."""
        if self.main_window:
            self.main_window.toggle_ai_panel()

    def add_default_bookmarks(self):
        """Add default bookmarks to the bookmarks container."""
        for name, url in self.bookmarks.items():
            btn = QPushButton(name)
            btn.setToolTip(url)
            btn.setFixedHeight(30)
            btn.setProperty('url', url)
            btn.clicked.connect(lambda checked, url=url: self.navigate_to_bookmark(url))
            # Add context menu for removal
            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda pos, btn=btn: self.show_bookmark_context_menu(pos, btn))
            self.bookmarks_layout.addWidget(btn)
    
    def bookmark_current_page(self):
        """Add current page to bookmarks."""
        current_tab = self.current_tab()
        if current_tab:
            url = current_tab.url().toString()
            title = current_tab.title()
            if title and url:
                # Use page title or fallback to hostname
                if not title or title == "New Tab":
                    from urllib.parse import urlparse
                    parsed_url = urlparse(url)
                    title = parsed_url.hostname or "Bookmark"
                
                # Add to bookmarks dict
                self.bookmarks[title] = url
                
                # Create button for the bookmark
                btn = QPushButton(title)
                btn.setToolTip(url)
                btn.setFixedHeight(30)
                btn.setProperty('url', url)
                btn.clicked.connect(lambda checked, url=url: self.navigate_to_bookmark(url))
                # Add context menu for removal
                btn.setContextMenuPolicy(Qt.CustomContextMenu)
                btn.customContextMenuRequested.connect(lambda pos, btn=btn: self.show_bookmark_context_menu(pos, btn))
                self.bookmarks_layout.addWidget(btn)
    
    def navigate_to_bookmark(self, url):
        """Navigate to a bookmarked URL."""
        current_tab = self.current_tab()
        if current_tab:
            current_tab.setUrl(QUrl(url))
    
    def toggle_dark_theme(self):
        """Toggle between light and dark themes."""
        # Toggle theme state
        self.dark_theme_enabled = not getattr(self, 'dark_theme_enabled', False)
        
        if self.dark_theme_enabled:
            self.apply_dark_theme()
            self.theme_toggle_btn.setText("☀️")  # Change to sun icon for light mode
            self.theme_toggle_btn.setToolTip("Toggle Light Theme")
            # Inject dark theme into current tab
            self.inject_website_dark_theme()
        else:
            self.apply_light_theme()
            self.theme_toggle_btn.setText("🌙")  # Change to moon icon for dark mode
            self.theme_toggle_btn.setToolTip("Toggle Dark Theme")
            # Remove dark theme from current tab
            self.remove_website_dark_theme()
    
    def apply_dark_theme(self):
        """Apply dark theme styling to all widgets."""
        dark_stylesheet = """
        QMainWindow, QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
            font-family: 'Segoe UI', 'Ubuntu', sans-serif;
            font-size: 14px;
        }
        QToolBar {
            background-color: #3c3c3c;
            border: none;
            spacing: 4px;
            padding: 4px;
        }
        QLineEdit {
            background-color: #3c3c3c;
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 6px 8px;
            font-size: 14px;
            transition: border-color 0.3s ease;
        }
        QLineEdit:hover {
            border-color: #0078d4;
        }
        QTabWidget::pane {
            border: 1px solid #555555;
            background-color: #2b2b2b;
        }
        QTabWidget::tab-bar {
            alignment: left;
        }
        QTabBar::tab {
            background-color: #3c3c3c;
            color: #ffffff;
            padding: 8px 12px;
            border: 1px solid #555555;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            font-size: 13px;
            transition: all 0.2s ease;
        }
        QTabBar::tab:selected {
            background-color: #2b2b2b;
            border-bottom: 1px solid #2b2b2b;
            transform: translateY(-1px);
        }
        QTabBar::tab:hover {
            background-color: #4c4c4c;
            transform: translateY(-2px);
        }
        QAction {
            color: #ffffff;
            background-color: transparent;
            padding: 4px 6px;
            border-radius: 3px;
            transition: all 0.2s ease;
        }
        QAction:hover {
            background-color: #0078d4;
            transform: scale(1.05);
        }
        QPushButton {
            font-family: 'Segoe UI', 'Ubuntu', sans-serif;
            padding: 4px 8px;
            transition: all 0.2s ease;
        }
        QPushButton:hover {
            background-color: #0078d4;
        }
        """
        self.setStyleSheet(dark_stylesheet)
        # Apply to all child widgets
        for child in self.findChildren(QWidget):
            child.setStyleSheet(dark_stylesheet)
    
    def apply_light_theme(self):
        """Apply light theme styling (reset to default)."""
        self.setStyleSheet("")
        # Reset all child widgets
        for child in self.findChildren(QWidget):
            child.setStyleSheet("")
    
    def show_bookmark_context_menu(self, pos, button):
        """Show context menu for bookmark removal."""
        menu = QMenu(self)
        remove_action = menu.addAction("Remove Bookmark")
        action = menu.exec_(button.mapToGlobal(pos))
        if action == remove_action:
            self.remove_bookmark(button)
    
    def remove_bookmark(self, button):
        """Remove a bookmark from the list."""
        title = button.text()
        url = button.property('url')
        if title in self.bookmarks:
            del self.bookmarks[title]
        button.deleteLater()
    
    def inject_website_dark_theme(self):
        """Inject dark theme CSS into the current webpage."""
        current_tab = self.current_tab()
        if current_tab:
            dark_css = """
            html, body {
                filter: invert(1) hue-rotate(180deg);
                background-color: #000 !important;
            }
            img, video, iframe {
                filter: invert(1) hue-rotate(180deg);
            }
            """
            js = f"""
            (function() {{
                let style = document.getElementById('voyx-dark-theme');
                if (!style) {{
                    style = document.createElement('style');
                    style.id = 'voyx-dark-theme';
                    document.head.appendChild(style);
                }}
                style.textContent = `{dark_css}`;
            }})();
            """
            current_tab.page().runJavaScript(js)
    
    def remove_website_dark_theme(self):
        """Remove dark theme CSS from the current webpage."""
        current_tab = self.current_tab()
        if current_tab:
            js = """
            (function() {
                let style = document.getElementById('voyx-dark-theme');
                if (style) {
                    style.remove();
                }
            })();
            """
            current_tab.page().runJavaScript(js)
    
    def setup_animations(self):
        """Initialize UI animations."""
        # Tab change animation
        self.tab_animation = QPropertyAnimation(self.tab_widget, b"pos")
        self.tab_animation.setDuration(300)
        self.tab_animation.setEasingCurve(QEasingCurve.OutQuad)
        
        # Bookmark bar fade-in
        self.bookmark_animation = QPropertyAnimation(self.bookmarks_scroll_area, b"maximumHeight")
        self.bookmark_animation.setDuration(200)
        self.bookmark_animation.setStartValue(0)
        self.bookmark_animation.setEndValue(40)
        
        # Connect animation triggers
        self.tab_widget.currentChanged.connect(self.animate_tab_change)
        self.bookmark_btn.triggered.connect(self.animate_bookmark_bar)

    def animate_tab_change(self, index):
        """Animate tab transition."""
        if index >= 0:
            self.tab_animation.setStartValue(self.tab_widget.pos() + QPoint(20, 0))
            self.tab_animation.setEndValue(self.tab_widget.pos())
            self.tab_animation.start()

    def animate_bookmark_bar(self):
        """Toggle bookmark bar with animation."""
        current_height = self.bookmarks_scroll_area.maximumHeight()
        self.bookmark_animation.setDirection(
            QAbstractAnimation.Forward if current_height == 0 else QAbstractAnimation.Backward
        )
        self.bookmark_animation.start()

    def is_dark_theme_enabled(self):
        """Check if dark theme is currently enabled."""
        return getattr(self, 'dark_theme_enabled', False)
    
    def open_security_settings(self):
        """Open security settings dialog as popup window."""
        dialog = SecuritySettingsDialog(self.security_manager)
        dialog.exec_()

class SecuritySettingsDialog(QDialog):
    """Popup dialog for security settings configuration."""
    
    def __init__(self, security_manager):
        super().__init__()
        self.setWindowTitle("Security Settings")
        self.setWindowModality(Qt.ApplicationModal)
        self.setMinimumSize(400, 500)
        
        layout = QVBoxLayout(self)
        from security_settings import SecuritySettingsPanel
        self.settings_panel = SecuritySettingsPanel(security_manager)
        layout.addWidget(self.settings_panel)
        
        # Add dialog buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
