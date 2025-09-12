"""
Security Manager Module - Handles security features including HTTPS enforcement,
ad/tracker blocking, and privacy controls for the browser.
"""

import re
import os
from urllib.parse import urlparse
from PyQt5.QtCore import QObject, QSettings
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor

class SecurityManager(QObject):
    """Manages security settings and URL filtering for the browser."""
    
    def __init__(self):
        super().__init__()
        self.settings = QSettings("VoyxBrowser", "Security")
        self.load_settings()
        
        # Common ad/tracker patterns
        self.ad_patterns = self.load_blocklists()
        
        # Compiled regex patterns for performance
        self.ad_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.ad_patterns]

    def load_blocklists(self):
        """Load block lists from the blocklists directory."""
        blocklists = []
        blocklists_dir = "blocklists"
        if os.path.exists(blocklists_dir):
            for filename in os.listdir(blocklists_dir):
                if filename.endswith(".txt"):
                    with open(os.path.join(blocklists_dir, filename), "r") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("!"):
                                blocklists.append(line)
        return blocklists
        
    def load_settings(self):
        """Load security settings from QSettings."""
        self.https_only = self.settings.value("https_only", False, type=bool)
        self.block_ads = self.settings.value("block_ads", True, type=bool)
        self.block_trackers = self.settings.value("block_trackers", True, type=bool)
        self.strict_privacy = self.settings.value("strict_privacy", False, type=bool)
        self.vpn_enabled = self.settings.value("vpn_enabled", False, type=bool)
        self.vpn_server = self.settings.value("vpn_server", "US Server", type=str)
        
    def save_settings(self):
        """Save security settings to QSettings."""
        self.settings.setValue("https_only", self.https_only)
        self.settings.setValue("block_ads", self.block_ads)
        self.settings.setValue("block_trackers", self.block_trackers)
        self.settings.setValue("strict_privacy", self.strict_privacy)
        self.settings.setValue("vpn_enabled", self.vpn_enabled)
        self.settings.setValue("vpn_server", self.vpn_server)
        
    def should_block_url(self, url):
        """Determine if a URL should be blocked based on security settings."""
        url_str = url.toString()
        
        # Block non-HTTPS URLs in HTTPS-only mode
        if self.https_only and url_str.startswith('http://'):
            return True
            
        # Block ads and trackers (unless VPN enabled for paywall bypass)
        if (self.block_ads or self.block_trackers) and self.is_ad_or_tracker(url_str):
            if self.vpn_enabled and self.should_bypass_via_vpn(url_str):
                return False  # Allow through VPN
            return True
            
        return False
        
    def is_ad_or_tracker(self, url):
        """Check if URL matches ad/tracker patterns."""
        for pattern in self.ad_regex:
            if pattern.search(url):
                return True
        return False
        
    def get_security_status(self, url):
        """Get security status for a given URL."""
        url_str = url.toString()
        status = {
            'is_secure': url_str.startswith('https://'),
            'has_ads': self.is_ad_or_tracker(url_str) if self.block_ads else False,
            'has_trackers': self.is_ad_or_tracker(url_str) if self.block_trackers else False
        }
        return status
        
    def set_https_only(self, enabled):
        """Enable or disable HTTPS-only mode."""
        self.https_only = enabled
        self.save_settings()
        
    def set_block_ads(self, enabled):
        """Enable or disable ad blocking."""
        self.block_ads = enabled
        self.save_settings()
        
    def set_block_trackers(self, enabled):
        """Enable or disable tracker blocking."""
        self.block_trackers = enabled
        self.save_settings()
        
    def set_strict_privacy(self, enabled):
        """Enable or disable strict privacy mode."""
        self.strict_privacy = enabled
        self.save_settings()
        
    def get_settings(self):
        """Get current security settings."""
        return {
            'https_only': self.https_only,
            'block_ads': self.block_ads,
            'block_trackers': self.block_trackers,
            'strict_privacy': self.strict_privacy,
            'vpn_enabled': self.vpn_enabled,
            'vpn_server': self.vpn_server
        }

    def set_vpn_enabled(self, enabled):
        """Enable or disable VPN routing."""
        self.vpn_enabled = enabled
        self.save_settings()

    def set_vpn_server(self, server):
        """Set VPN server location."""
        self.vpn_server = server
        self.save_settings()

    def should_bypass_via_vpn(self, url):
        """Determine if URL should be routed through VPN."""
        # Implement actual VPN routing logic here
        # For now, just allow all when VPN is enabled
        return self.vpn_enabled

class UrlRequestInterceptor(QWebEngineUrlRequestInterceptor):
    """Intercepts URL requests to block ads and enforce security policies."""
    
    def __init__(self, security_manager):
        super().__init__()
        self.security_manager = security_manager
        
    def interceptRequest(self, info):
        """Intercept and potentially block URL requests."""
        url = info.requestUrl().toString()
        
        if self.security_manager.should_block_url(url):
            info.block(True)
