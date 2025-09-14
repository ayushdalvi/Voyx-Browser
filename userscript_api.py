"""
Userscript API - Provides Tampermonkey/Greasemonkey API compatibility.
"""

import json
import os
import requests
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal, QSettings, QTimer
from PyQt5.QtWidgets import QMessageBox, QSystemTrayIcon
from PyQt5.QtGui import QIcon

class UserscriptAPI(QObject):
    """Provides GM_* API functions for userscripts."""
    
    notification_requested = pyqtSignal(str, str, int)  # title, text, timeout
    
    def __init__(self):
        super().__init__()
        self.storage_dir = Path("userscripts/storage")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.settings = QSettings("VoyxBrowser", "UserscriptAPI")
    
    def get_api_code(self, script_name):
        """Get the JavaScript API code for injection."""
        return f"""
// Greasemonkey/Tampermonkey API Implementation
(function() {{
    'use strict';
    const SCRIPT_NAME = '{script_name}';
    const API_ENDPOINT = 'userscript_api';
    
    // Storage functions
    window.GM_getValue = function(key, defaultValue) {{
        try {{
            const stored = localStorage.getItem('GM_' + SCRIPT_NAME + '_' + key);
            return stored !== null ? JSON.parse(stored) : defaultValue;
        }} catch (e) {{
            return defaultValue;
        }}
    }};
    
    window.GM_setValue = function(key, value) {{
        try {{
            localStorage.setItem('GM_' + SCRIPT_NAME + '_' + key, JSON.stringify(value));
            return true;
        }} catch (e) {{
            return false;
        }}
    }};
    
    window.GM_deleteValue = function(key) {{
        try {{
            localStorage.removeItem('GM_' + SCRIPT_NAME + '_' + key);
            return true;
        }} catch (e) {{
            return false;
        }}
    }};
    
    window.GM_listValues = function() {{
        const keys = [];
        const prefix = 'GM_' + SCRIPT_NAME + '_';
        for (let i = 0; i < localStorage.length; i++) {{
            const key = localStorage.key(i);
            if (key && key.startsWith(prefix)) {{
                keys.push(key.substring(prefix.length));
            }}
        }}
        return keys;
    }};
    
    // HTTP request function
    window.GM_xmlhttpRequest = function(details) {{
        return new Promise((resolve, reject) => {{
            const xhr = new XMLHttpRequest();
            
            xhr.open(details.method || 'GET', details.url, true);
            
            // Set headers
            if (details.headers) {{
                for (const [key, value] of Object.entries(details.headers)) {{
                    xhr.setRequestHeader(key, value);
                }}
            }}
            
            // Set response type
            if (details.responseType) {{
                xhr.responseType = details.responseType;
            }}
            
            // Set timeout
            if (details.timeout) {{
                xhr.timeout = details.timeout;
            }}
            
            // Event handlers
            xhr.onload = function() {{
                const response = {{
                    status: xhr.status,
                    statusText: xhr.statusText,
                    responseText: xhr.responseText,
                    responseXML: xhr.responseXML,
                    response: xhr.response,
                    readyState: xhr.readyState,
                    responseHeaders: xhr.getAllResponseHeaders()
                }};
                
                if (details.onload) details.onload(response);
                resolve(response);
            }};
            
            xhr.onerror = function() {{
                const response = {{
                    status: xhr.status,
                    statusText: xhr.statusText,
                    readyState: xhr.readyState
                }};
                
                if (details.onerror) details.onerror(response);
                reject(response);
            }};
            
            xhr.ontimeout = function() {{
                const response = {{
                    status: xhr.status,
                    statusText: 'timeout',
                    readyState: xhr.readyState
                }};
                
                if (details.ontimeout) details.ontimeout(response);
                reject(response);
            }};
            
            xhr.onprogress = function(e) {{
                if (details.onprogress) details.onprogress(e);
            }};
            
            xhr.onreadystatechange = function() {{
                if (details.onreadystatechange) details.onreadystatechange(xhr);
            }};
            
            // Send request
            xhr.send(details.data || null);
        }});
    }};
    
    // Style injection
    window.GM_addStyle = function(css) {{
        const style = document.createElement('style');
        style.type = 'text/css';
        style.textContent = css;
        style.setAttribute('data-gm-style', SCRIPT_NAME);
        
        const head = document.head || document.getElementsByTagName('head')[0];
        head.appendChild(style);
        
        return style;
    }};
    
    // Resource loading
    window.GM_getResourceText = function(name) {{
        // This would need to be implemented with actual resource storage
        console.warn('GM_getResourceText not fully implemented');
        return '';
    }};
    
    window.GM_getResourceURL = function(name) {{
        // This would need to be implemented with actual resource storage
        console.warn('GM_getResourceURL not fully implemented');
        return '';
    }};
    
    // Notification
    window.GM_notification = function(details) {{
        if (typeof details === 'string') {{
            details = {{ text: details }};
        }}
        
        const notification = {{
            title: details.title || 'Userscript Notification',
            text: details.text || '',
            timeout: details.timeout || 5000,
            onclick: details.onclick
        }};
        
        // Try to use browser notifications
        if ('Notification' in window && Notification.permission === 'granted') {{
            const browserNotification = new Notification(notification.title, {{
                body: notification.text,
                icon: details.image
            }});
            
            if (notification.onclick) {{
                browserNotification.onclick = notification.onclick;
            }}
            
            if (notification.timeout > 0) {{
                setTimeout(() => browserNotification.close(), notification.timeout);
            }}
        }} else {{
            // Fallback to console
            console.log(`[GM Notification] ${{notification.title}}: ${{notification.text}}`);
        }}
        
        return notification;
    }};
    
    // Tab management
    window.GM_openInTab = function(url, options) {{
        options = options || {{}};
        
        const link = document.createElement('a');
        link.href = url;
        link.target = options.active === false ? '_blank' : '_blank';
        link.rel = 'noopener noreferrer';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        return {{
            close: function() {{
                // Cannot close tabs opened this way
                console.warn('Cannot close tab opened with GM_openInTab');
            }}
        }};
    }};
    
    // Clipboard access
    window.GM_setClipboard = function(data, info) {{
        if (navigator.clipboard && navigator.clipboard.writeText) {{
            navigator.clipboard.writeText(data).catch(e => {{
                console.error('Failed to write to clipboard:', e);
            }});
        }} else {{
            // Fallback method
            const textArea = document.createElement('textarea');
            textArea.value = data;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            try {{
                document.execCommand('copy');
            }} catch (err) {{
                console.error('Failed to copy to clipboard:', err);
            }}
            
            document.body.removeChild(textArea);
        }}
    }};
    
    // Menu commands (simplified)
    window.GM_registerMenuCommand = function(name, fn, accessKey) {{
        console.log(`Menu command registered: ${{name}}`);
        // Store for potential context menu integration
        window._gmMenuCommands = window._gmMenuCommands || [];
        window._gmMenuCommands.push({{ name, fn, accessKey }});
        return name;
    }};
    
    window.GM_unregisterMenuCommand = function(menuCmdId) {{
        if (window._gmMenuCommands) {{
            window._gmMenuCommands = window._gmMenuCommands.filter(cmd => cmd.name !== menuCmdId);
        }}
    }};
    
    // Logging
    window.GM_log = function(...args) {{
        console.log('[GM]', ...args);
    }};
    
    // Info object
    window.GM_info = {{
        script: {{
            name: SCRIPT_NAME,
            namespace: 'VoyxBrowser',
            version: '1.0',
            description: 'Userscript',
            author: 'Unknown'
        }},
        scriptMetaStr: '',
        scriptHandler: 'Voyx Browser',
        version: '1.0'
    }};
    
    // Modern GM API (GM.*)
    window.GM = {{
        getValue: window.GM_getValue,
        setValue: window.GM_setValue,
        deleteValue: window.GM_deleteValue,
        listValues: window.GM_listValues,
        xmlHttpRequest: window.GM_xmlhttpRequest,
        addStyle: window.GM_addStyle,
        getResourceText: window.GM_getResourceText,
        getResourceURL: window.GM_getResourceURL,
        notification: window.GM_notification,
        openInTab: window.GM_openInTab,
        setClipboard: window.GM_setClipboard,
        registerMenuCommand: window.GM_registerMenuCommand,
        unregisterMenuCommand: window.GM_unregisterMenuCommand,
        log: window.GM_log,
        info: window.GM_info
    }};
    
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {{
        Notification.requestPermission();
    }}
    
}})();(cmd => cmd.name !== menuCmdId);
        }}
    }};
    
    // Logging
    window.GM_log = function(...args) {{
        console.log('[GM]', ...args);
    }};
    
    // Info object
    window.GM_info = {{
        script: {{
            name: SCRIPT_NAME,
            namespace: 'VoyxBrowser',
            version: '1.0',
            description: 'Userscript',
            author: 'Unknown'
        }},
        scriptMetaStr: '',
        scriptHandler: 'Voyx Browser',
        version: '1.0'
    }};
    
    // Modern GM API (GM.*)
    window.GM = {{
        getValue: window.GM_getValue,
        setValue: window.GM_setValue,
        deleteValue: window.GM_deleteValue,
        listValues: window.GM_listValues,
        xmlHttpRequest: window.GM_xmlhttpRequest,
        addStyle: window.GM_addStyle,
        getResourceText: window.GM_getResourceText,
        getResourceURL: window.GM_getResourceURL,
        notification: window.GM_notification,
        openInTab: window.GM_openInTab,
        setClipboard: window.GM_setClipboard,
        registerMenuCommand: window.GM_registerMenuCommand,
        unregisterMenuCommand: window.GM_unregisterMenuCommand,
        log: window.GM_log,
        info: window.GM_info
    }};
    
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {{
        Notification.requestPermission();
    }}
    
}})();
"""
    
    def show_notification(self, title, text, timeout=5000):
        """Show a system notification."""
        try:
            if QSystemTrayIcon.isSystemTrayAvailable():
                tray = QSystemTrayIcon()
                tray.show()
                tray.showMessage(title, text, QSystemTrayIcon.Information, timeout)
            else:
                # Fallback to message box
                msg = QMessageBox()
                msg.setWindowTitle(title)
                msg.setText(text)
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
        except Exception as e:
            print(f"Failed to show notification: {e}")
    
    def handle_xhr_request(self, details):
        """Handle GM_xmlhttpRequest from userscripts."""
        try:
            method = details.get('method', 'GET')
            url = details.get('url')
            headers = details.get('headers', {})
            data = details.get('data')
            timeout = details.get('timeout', 30)
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                timeout=timeout
            )
            
            return {
                'status': response.status_code,
                'statusText': response.reason,
                'responseText': response.text,
                'responseHeaders': dict(response.headers)
            }
            
        except Exception as e:
            return {
                'status': 0,
                'statusText': str(e),
                'responseText': '',
                'responseHeaders': {}
            }
    
    def get_stored_value(self, script_name, key, default_value=None):
        """Get stored value for a script."""
        storage_file = self.storage_dir / f"{script_name}.json"
        
        try:
            if storage_file.exists():
                with open(storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get(key, default_value)
        except Exception as e:
            print(f"Error reading stored value: {e}")
        
        return default_value
    
    def set_stored_value(self, script_name, key, value):
        """Set stored value for a script."""
        storage_file = self.storage_dir / f"{script_name}.json"
        
        try:
            data = {}
            if storage_file.exists():
                with open(storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            data[key] = value
            
            with open(storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error storing value: {e}")
            return False
    
    def delete_stored_value(self, script_name, key):
        """Delete stored value for a script."""
        storage_file = self.storage_dir / f"{script_name}.json"
        
        try:
            if storage_file.exists():
                with open(storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if key in data:
                    del data[key]
                    
                    with open(storage_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error deleting stored value: {e}")
            return False
    
    def list_stored_values(self, script_name):
        """List all stored keys for a script."""
        storage_file = self.storage_dir / f"{script_name}.json"
        
        try:
            if storage_file.exists():
                with open(storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return list(data.keys())
        except Exception as e:
            print(f"Error listing stored values: {e}")
        
        return []