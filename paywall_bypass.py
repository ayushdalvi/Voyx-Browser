"""
Paywall Bypass Module - Detects and bypasses common paywall implementations.
Provides tools to unlock subscription content on various websites.
"""

import re
from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWebEngineWidgets import QWebEngineView

class PaywallBypass(QObject):
    """Handles detection and bypass of common paywall implementations."""
    
    def __init__(self):
        super().__init__()
        self.enabled = True
        self.common_patterns = self.load_bypass_patterns()
        
    def load_bypass_patterns(self):
        """Load common paywall bypass patterns and techniques."""
        return [
            {
                'name': 'Overlay Removal',
                'selectors': [
                    '.paywall-overlay',
                    '.subscription-overlay',
                    '.premium-content-blocker',
                    '[class*="paywall"]',
                    '[class*="premium"]',
                    '[class*="subscribe"]',
                    '.article-locked',
                    '.content-locked'
                ],
                'action': 'remove'
            },
            {
                'name': 'Modal Dismissal',
                'selectors': [
                    '.modal-backdrop',
                    '.modal-overlay',
                    '.lightbox-overlay',
                    '.popup-overlay',
                    '.overlay-container'
                ],
                'action': 'remove'
            },
            {
                'name': 'Scroll Unlock',
                'selectors': [
                    'body[style*="overflow: hidden"]',
                    'html[style*="overflow: hidden"]',
                    '.scroll-lock'
                ],
                'action': 'unlock_scroll'
            },
            {
                'name': 'Content Reveal',
                'selectors': [
                    '.blurred-content',
                    '.faded-content',
                    '.truncated-content',
                    '[style*="blur"]',
                    '[style*="opacity: 0.5"]'
                ],
                'action': 'reveal'
            },
            {
                'name': 'Cookie Bypass',
                'patterns': [
                    r'news\.com',
                    r'washingtonpost\.com',
                    r'nytimes\.com',
                    r'wsj\.com',
                    r'ft\.com',
                    r'bloomberg\.com'
                ],
                'action': 'set_cookies'
            },
            {
                'name': 'Disable JavaScript',
                'patterns': [
                    r'example\.com'
                ],
                'action': 'disable_javascript'
            }
        ]
    
    def bypass_paywall(self, web_view):
        """Attempt to bypass paywalls on the current page."""
        if not self.enabled or not isinstance(web_view, QWebEngineView):
            return
            
        current_url = web_view.url().toString()
        
        # Execute bypass techniques
        for pattern in self.common_patterns:
            if 'patterns' in pattern and self.url_matches_pattern(current_url, pattern['patterns']):
                self.execute_bypass_action(web_view, pattern['action'])
            elif 'selectors' in pattern:
                self.execute_bypass_action(web_view, pattern['action'], pattern['selectors'])
    
    def url_matches_pattern(self, url, patterns):
        """Check if URL matches any of the given patterns."""
        for pattern in patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False
    
    def execute_bypass_action(self, web_view, action, selectors=None):
        """Execute the appropriate bypass action."""
        js_code = self.generate_js_code(action, selectors)
        if js_code:
            web_view.page().runJavaScript(js_code)
    
    def generate_js_code(self, action, selectors=None):
        """Generate JavaScript code for the bypass action."""
        if action == 'remove' and selectors:
            return self.generate_removal_js(selectors)
        elif action == 'unlock_scroll':
            return """
                document.body.style.overflow = 'auto';
                document.body.style.position = 'static';
                document.documentElement.style.overflow = 'auto';
                document.documentElement.style.position = 'static';
            """
        elif action == 'reveal' and selectors:
            return self.generate_reveal_js(selectors)
        elif action == 'set_cookies':
            return """
                // Set cookies to mimic premium access
                document.cookie = "subscription=premium; path=/; domain=" + window.location.hostname;
                document.cookie = "user_status=subscribed; path=/; domain=" + window.location.hostname;
                document.cookie = "paywall=bypassed; path=/; domain=" + window.location.hostname;
            """
        elif action == 'disable_javascript':
            return """
                // Disable JavaScript on the page
                window.eval = function() {};
                setTimeout(function() {
                    window.eval = window.old_eval;
                }, 1000);
            """
        return None
    
    def generate_removal_js(self, selectors):
        """Generate JavaScript to remove elements."""
        js_lines = []
        for selector in selectors:
            js_lines.append(f"""
                document.querySelectorAll('{selector}').forEach(element => {{
                    element.remove();
                }});
            """)
        return "\n".join(js_lines)
    
    def generate_reveal_js(self, selectors):
        """Generate JavaScript to reveal hidden content."""
        js_lines = []
        for selector in selectors:
            js_lines.append(f"""
                document.querySelectorAll('{selector}').forEach(element => {{
                    element.style.filter = 'none';
                    element.style.opacity = '1';
                    element.style.webkitFilter = 'none';
                    element.classList.remove('blurred', 'faded', 'truncated');
                }});
            """)
        return "\n".join(js_lines)
    
    def enable(self, enabled):
        """Enable or disable the paywall bypass."""
        self.enabled = enabled
    
    def is_enabled(self):
        """Check if paywall bypass is enabled."""
        return self.enabled
    
    def add_custom_pattern(self, name, patterns, action, selectors=None):
        """Add a custom bypass pattern."""
        pattern = {
            'name': name,
            'action': action
        }
        
        if patterns:
            pattern['patterns'] = patterns
        if selectors:
            pattern['selectors'] = selectors
            
        self.common_patterns.append(pattern)
    
    def remove_pattern(self, name):
        """Remove a bypass pattern by name."""
        self.common_patterns = [p for p in self.common_patterns if p['name'] != name]
