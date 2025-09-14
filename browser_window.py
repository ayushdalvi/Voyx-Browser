
"""
Browser Window Module - Handles tabbed browsing and navigation controls.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QLineEdit, QPushButton, QToolBar, QAction, QMenu,
                             QScrollArea, QFrame, QDialog, QDialogButtonBox, QMessageBox)
from PyQt5.QtCore import QUrl, Qt, pyqtSlot, QPropertyAnimation, QRect, QEasingCurve
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PyQt5.QtGui import QIcon, QKeySequence


import os

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
        self.page().settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        
        # Setup console logging
        self.page().javaScriptConsoleMessage = lambda level, message, line, source: print(f"CONSOLE: {message}")
        self.setUrl(QUrl.fromLocalFile(os.path.abspath("search.html")))
        
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

        # Navigation buttons only
        self.back_btn = QAction("←", self)
        self.forward_btn = QAction("→", self)
        self.reload_btn = QAction("↻", self)
        self.home_btn = QAction("🏠", self)

        self.nav_toolbar.addAction(self.back_btn)
        self.nav_toolbar.addAction(self.forward_btn)
        self.nav_toolbar.addAction(self.reload_btn)
        self.nav_toolbar.addAction(self.home_btn)

        # Browser theme toggle button
        self.theme_toggle_btn = QAction("🌌", self)
        self.theme_toggle_btn.setToolTip("Toggle Browser Theme")
        self.nav_toolbar.addAction(self.theme_toggle_btn)

        # AI Panel toggle button
        self.ai_toggle_btn = QAction("🤖", self)
        self.ai_toggle_btn.setToolTip("Toggle AI Panel")
        self.nav_toolbar.addAction(self.ai_toggle_btn)

        # Screen OCR AI button
        self.ocr_ai_btn = QAction("📷", self)
        self.ocr_ai_btn.setToolTip("Open Screen OCR AI Panel (Ctrl+Shift+A)")
        self.ocr_ai_btn.setShortcut(QKeySequence("Ctrl+Shift+A"))
        self.nav_toolbar.addAction(self.ocr_ai_btn)

        # Security settings button
        self.settings_btn = QAction("⚙️", self)
        self.settings_btn.setToolTip("Security Settings")
        self.nav_toolbar.addAction(self.settings_btn)
        
        # Userscript manager button
        self.userscript_btn = QAction("📜", self)
        self.userscript_btn.setToolTip("Userscript Manager")
        self.nav_toolbar.addAction(self.userscript_btn)
        
        # Paywall bypass button
        self.paywall_btn = QAction("🔓", self)
        self.paywall_btn.setToolTip("Bypass Paywall")
        self.nav_toolbar.addAction(self.paywall_btn)
        
        # Ad blocker button
        self.adblock_btn = QAction("🛡️", self)
        self.adblock_btn.setToolTip("Toggle Ad Blocker")
        self.nav_toolbar.addAction(self.adblock_btn)
        
        # Dark mode button (separate from theme toggle)
        self.darkmode_btn = QAction("🌙", self)
        self.darkmode_btn.setToolTip("Toggle Website Dark Mode")
        self.nav_toolbar.addAction(self.darkmode_btn)

        # Add animations to buttons
        self.add_button_animations()
        
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
        
        # Add bookmark button to bookmarks area
        self.bookmark_btn = QPushButton("🔖")
        self.bookmark_btn.setToolTip("Bookmark this page")
        self.bookmark_btn.setFixedHeight(30)
        self.bookmarks_layout.addWidget(self.bookmark_btn)
        
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
        
        # Tab widget with new tab button
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        
        # Add new tab button to tab widget
        self.new_tab_btn = QPushButton("➕")
        self.new_tab_btn.setToolTip("New Tab")
        self.new_tab_btn.setFixedSize(30, 30)
        self.tab_widget.setCornerWidget(self.new_tab_btn)
        
        layout.addWidget(self.tab_widget)
        
        # Create footer with address bar
        footer_layout = QHBoxLayout()
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter URL or search...")
        footer_layout.addWidget(self.url_bar)
        layout.addLayout(footer_layout)
        
        # Create initial tab
        self.create_new_tab()
        
    def setup_connections(self):
        """Set up signal connections."""
        # Navigation buttons
        self.back_btn.triggered.connect(self.navigate_back)
        self.forward_btn.triggered.connect(self.navigate_forward)
        self.reload_btn.triggered.connect(self.reload_page)
        self.home_btn.triggered.connect(self.navigate_home)
        self.new_tab_btn.clicked.connect(self.create_new_tab)
        self.bookmark_btn.clicked.connect(self.bookmark_current_page)
        self.theme_toggle_btn.triggered.connect(self.toggle_dark_theme)
        self.ai_toggle_btn.triggered.connect(self.toggle_ai_panel)
        self.ocr_ai_btn.triggered.connect(self.open_screen_ai_panel)
        self.settings_btn.triggered.connect(self.open_security_settings)
        self.userscript_btn.triggered.connect(self.open_userscript_manager)
        self.paywall_btn.triggered.connect(self.bypass_paywall_manual)
        self.adblock_btn.triggered.connect(self.toggle_adblock_manual)
        self.darkmode_btn.triggered.connect(self.toggle_darkmode_manual)

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

        # Animate the new tab
        self.animate_tab_creation(index)
        
        # Connect tab signals
        tab.titleChanged.connect(lambda title: self.update_tab_title(index, title))
        tab.urlChanged.connect(lambda url: self.update_url_bar(url))
        
        return tab
        
    def close_tab(self, index):
        """Close a browser tab."""
        if self.tab_widget.count() > 1:
            self.animate_tab_closing(index)
            widget = self.tab_widget.widget(index)
            widget.deleteLater()
            self.tab_widget.removeTab(index)
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
            current_tab.setUrl(QUrl.fromLocalFile(os.path.abspath("search.html")))
            
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

    def open_screen_ai_panel(self):
        """Open the external Screen OCR AI panel and feed current selection."""
        if self.main_window:
            self.main_window.open_screen_ai_panel(auto_ask=False)

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
                # Prompt user for bookmark name
                dialog = QDialog(self)
                dialog.setWindowTitle("Add Bookmark")
                layout = QVBoxLayout(dialog)

                # Input for bookmark name
                name_input = QLineEdit(dialog)
                name_input.setText(title)
                layout.addWidget(name_input)

                # Dialog buttons
                button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
                button_box.accepted.connect(dialog.accept)
                button_box.rejected.connect(dialog.reject)
                layout.addWidget(button_box)

                if dialog.exec_() == QDialog.Accepted:
                    bookmark_name = name_input.text()
                    if not bookmark_name:
                        # Fallback to hostname if name is empty
                        from urllib.parse import urlparse
                        parsed_url = urlparse(url)
                        bookmark_name = parsed_url.hostname or "Bookmark"
                    
                    # Add to bookmarks dict
                    self.bookmarks[bookmark_name] = url
                    
                    # Create button for the bookmark
                    btn = QPushButton(bookmark_name)
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
        """Apply Opera GX-like theme styling to all widgets."""
        opera_gx_stylesheet = """
        QMainWindow, QWidget {
            background-color: #0d0d0d;
            color: #e6e6e6;
            font-family: 'Roboto', sans-serif;
            font-size: 14px;
        }
        QToolBar {
            background-color: #1a1a1a;
            border: 1px solid #ff003c;
            spacing: 4px;
            padding: 4px;
        }
        QLineEdit {
            background-color: #1a1a1a;
            color: #e6e6e6;
            border: 1px solid #ff003c;
            border-radius: 0px;
            padding: 6px 8px;
            font-size: 14px;
        }
        QLineEdit:hover {
            border-color: #00f0ff;
        }
        QTabWidget::pane {
            border: 1px solid #ff003c;
            background-color: #0d0d0d;
        }
        QTabWidget::tab-bar {
            alignment: left;
        }
        QTabBar::tab {
            background-color: #1a1a1a;
            color: #e6e6e6;
            padding: 8px 12px;
            border: 1px solid #ff003c;
            border-bottom: none;
            border-top-left-radius: 0px;
            border-top-right-radius: 0px;
            font-size: 13px;
        }
        QTabBar::tab:selected {
            background-color: #0d0d0d;
            border-bottom: 1px solid #0d0d0d;
            color: #00f0ff;
        }
        QTabBar::tab:hover {
            background-color: #2a2a2a;
            color: #ff003c;
        }
        QAction {
            color: #e6e6e6;
            background-color: transparent;
            padding: 4px 6px;
            border-radius: 0px;
        }
        QAction:hover {
            background-color: #00f0ff;
            color: #0d0d0d;
        }
        QPushButton {
            background-color: #1a1a1a;
            color: #e6e6e6;
            border: 1px solid #ff003c;
            padding: 4px 8px;
        }
        QPushButton:hover {
            background-color: #00f0ff;
            color: #0d0d0d;
        }
        """
        self.setStyleSheet(opera_gx_stylesheet)
        # Apply to all child widgets
        for child in self.findChildren(QWidget):
            child.setStyleSheet(opera_gx_stylesheet)
    
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
                    document.documentElement.appendChild(style);
                }}
                style.textContent = `{dark_css}`;
            }})();
            """
            current_tab.page().runJavaScript(js)
    
    def inject_adblock_css(self):
        """Inject ad-blocking CSS into the current page."""
        css = """
        .masthead-ad,
        .player-ads,
        .ad-slot,
        .ytd-ad-slot-renderer {
            display: none !important;
        }
        """
        js = f"""
        (function() {{
            let style = document.createElement('style');
            style.id = 'voyx-adblock-styles';
            style.textContent = `{css}`;
            document.documentElement.appendChild(style);
        }})();
        """
        self.page().runJavaScript(js)

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

    def animate_button_enter(self, button, animation):
        """Animate a button when the mouse enters it."""
        animation.setStartValue(button.geometry())
        animation.setEndValue(button.geometry().adjusted(-2, -2, 2, 2))
        animation.start()

    def animate_button_leave(self, button, animation):
        """Animate a button when the mouse leaves it."""
        animation.setStartValue(button.geometry())
        animation.setEndValue(button.geometry().adjusted(2, 2, -2, -2))
        animation.start()

    def add_button_animations(self):
        """Add animations to the toolbar buttons."""
        for action in self.nav_toolbar.actions():
            button = self.nav_toolbar.widgetForAction(action)
            if button:
                animation = QPropertyAnimation(button, b"geometry")
                animation.setDuration(100)
                button.enterEvent = lambda event, button=button, animation=animation: self.animate_button_enter(button, animation)
                button.leaveEvent = lambda event, button=button, animation=animation: self.animate_button_leave(button, animation)

    def animate_tab_closing(self, index):
        """Animate the closing of a tab."""
        widget = self.tab_widget.widget(index)
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(500)
        animation.setStartValue(widget.geometry())
        animation.setEndValue(QRect(widget.x(), widget.y() - 50, widget.width(), widget.height()))
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        animation.finished.connect(lambda: self.tab_widget.removeTab(index))
        animation.start()

    def animate_tab_creation(self, index):
        """Animate the creation of a new tab."""
        widget = self.tab_widget.widget(index)
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(500)
        animation.setStartValue(QRect(widget.x(), widget.y() - 50, widget.width(), widget.height()))
        animation.setEndValue(widget.geometry())
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        animation.start()

    def is_dark_theme_enabled(self):
        """Check if dark theme is currently enabled."""
        return getattr(self, 'dark_theme_enabled', False)
    
    def toggle_ad_blocker(self):
        """Toggle ad blocker on/off."""
        current_state = self.security_manager.block_ads
        self.security_manager.set_block_ads(not current_state)
        
        # Update button appearance
        if self.security_manager.block_ads:
            self.adblock_toggle_btn.setText("🛡️")
            self.adblock_toggle_btn.setToolTip("Ad Blocker: Enabled")
        else:
            self.adblock_toggle_btn.setText("❌")
            self.adblock_toggle_btn.setToolTip("Ad Blocker: Disabled")
            
        # Reload current page to apply changes
        current_tab = self.current_tab()
        if current_tab:
            current_tab.reload()
   
    def load_search_engines(self):
        """Load search engines from JSON configuration."""
        config_path = os.path.join("config", "search_engines.json")
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    user_engines = json.load(f)
                    # Validate engine format
                    valid_engines = {k: v for k, v in user_engines.items()
                                   if isinstance(k, str) and isinstance(v, str) and '{query}' in v}
                    self.search_engines.update(valid_engines)
                    self.url_bar.addItems(valid_engines.keys())
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading search engines: {str(e)}")
   
    def update_suggestions(self, text):
       """Update dropdown with search suggestions and URL history."""
       self.url_bar.clear()
       # Add matching search engines
       for engine in self.search_engines:
           if text.lower() in engine.lower():
               self.url_bar.addItem(engine)
       # Add URL history matches
       for i in range(self.url_bar.count()):
           item = self.url_bar.itemText(i)
           if text.lower() in item.lower() and item not in self.search_engines:
               self.url_bar.addItem(item)

    def open_security_settings(self):
        """Open security settings dialog as popup window."""
        dialog = SecuritySettingsDialog(self.security_manager)
        dialog.exec_()
    
    def open_userscript_manager(self):
        """Open userscript manager GUI."""
        try:
            gui = self.userscript_manager.open_manager_gui(self)
            if gui:
                gui.exec_()
        except Exception as e:
            print(f"Error opening userscript manager: {e}")
            QMessageBox.warning(self, "Error", f"Could not open userscript manager: {str(e)}")
    
    def bypass_paywall_manual(self):
        """Manually trigger paywall bypass."""
        current_tab = self.current_tab()
        if current_tab:
            bypass_script = """
            // Manual paywall bypass
            (function() {
                console.log('Manual paywall bypass triggered!');
                
                // Remove paywall elements
                const selectors = [
                    '.paywall', '.subscription-wall', '.premium-wall', '.login-wall',
                    '.overlay', '.modal', '.popup', '.backdrop',
                    '[class*="paywall"]', '[class*="subscription"]', '[class*="premium"]',
                    '[class*="overlay"]', '[class*="modal"]'
                ];
                
                selectors.forEach(selector => {
                    document.querySelectorAll(selector).forEach(el => {
                        el.remove();
                        console.log('Removed:', selector);
                    });
                });
                
                // Restore scroll
                document.body.style.overflow = 'auto';
                document.documentElement.style.overflow = 'auto';
                
                // Remove blur effects
                document.querySelectorAll('*').forEach(el => {
                    if (el.style.filter && el.style.filter.includes('blur')) {
                        el.style.filter = 'none';
                    }
                });
                
                // Show hidden content
                document.querySelectorAll('.premium-content, .paid-content, .subscriber-content').forEach(el => {
                    el.style.display = 'block';
                    el.style.visibility = 'visible';
                    el.style.opacity = '1';
                });
                
                alert('Paywall bypass attempted!');
            })();
            """
            
            current_tab.page().runJavaScript(bypass_script)
            QMessageBox.information(self, "Paywall Bypass", "Paywall bypass script executed!")
    
    def toggle_adblock_manual(self):
        """Manually trigger ad blocker."""
        current_tab = self.current_tab()
        if current_tab:
            adblock_script = """
            // Manual ad blocker trigger
            (function() {
                console.log('Manual ad blocker triggered!');
                
                const adSelectors = [
                    '.ad', '.ads', '.advertisement', '.banner-ad', '.google-ad',
                    '.sponsored', '.promo', '.promotion', '.commercial',
                    '[class*="ad-"]', '[class*="ads-"]', '[class*="advertisement"]',
                    '[id*="ad-"]', '[id*="ads-"]', '[id*="advertisement"]',
                    '.adsbygoogle', '.ad-slot', '.ad-container',
                    '.popup-ad', '.overlay-ad', '.modal-ad',
                    '.newsletter-popup', '.subscription-popup',
                    '.cookie-banner', '.cookie-notice', '.gdpr-banner'
                ];
                
                let blocked = 0;
                adSelectors.forEach(selector => {
                    document.querySelectorAll(selector).forEach(el => {
                        el.remove();
                        blocked++;
                    });
                });
                
                // Block autoplay videos
                document.querySelectorAll('video[autoplay]').forEach(video => {
                    video.autoplay = false;
                    video.pause();
                    blocked++;
                });
                
                alert(`Ad Blocker: Removed ${blocked} elements!`);
            })();
            """
            
            current_tab.page().runJavaScript(adblock_script)
            QMessageBox.information(self, "Ad Blocker", "Ad blocking script executed!")
    
    def toggle_darkmode_manual(self):
        """Manually trigger dark mode."""
        current_tab = self.current_tab()
        if current_tab:
            darkmode_script = """
            // Manual dark mode trigger
            (function() {
                console.log('Manual dark mode triggered!');
                
                const isDark = document.documentElement.classList.contains('voyx-manual-dark');
                
                if (isDark) {
                    // Remove dark mode
                    document.documentElement.classList.remove('voyx-manual-dark');
                    document.documentElement.style.filter = '';
                    document.body.style.backgroundColor = '';
                    document.body.style.color = '';
                    alert('Dark mode disabled!');
                } else {
                    // Apply dark mode
                    document.documentElement.classList.add('voyx-manual-dark');
                    document.documentElement.style.filter = 'invert(0.9) hue-rotate(180deg)';
                    document.body.style.backgroundColor = '#1a1a1a';
                    document.body.style.color = '#e0e0e0';
                    
                    // Preserve images and videos
                    document.querySelectorAll('img, video, iframe, svg').forEach(el => {
                        el.style.filter = 'invert(1) hue-rotate(180deg)';
                    });
                    
                    alert('Dark mode enabled!');
                }
            })();
            """
            
            current_tab.page().runJavaScript(darkmode_script)
            QMessageBox.information(self, "Dark Mode", "Dark mode toggle executed!")

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