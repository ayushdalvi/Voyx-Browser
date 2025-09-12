"""
Userscript Manager Module - Tampermonkey-style userscript injection system.
Allows users to create, manage, and inject custom JavaScript into web pages.
"""

import os
import json
import re
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSlot, QSettings
from PyQt5.QtWebEngineWidgets import QWebEngineView

class Userscript:
    """Represents a single userscript with metadata and code."""
    
    def __init__(self, name, code, metadata=None):
        self.name = name
        self.code = code
        self.metadata = metadata or {}
        self.enabled = True
        
    @classmethod
    def from_file(cls, file_path):
        """Create a userscript from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse metadata block (if present)
            metadata = {}
            code = content
            
            # Look for metadata block in comments
            metadata_match = re.search(
                r'// ==UserScript==\s*(.*?)\s*// ==/UserScript==',
                content, re.DOTALL
            )
            
            if metadata_match:
                metadata_block = metadata_match.group(1)
                # Parse metadata lines
                for line in metadata_block.split('\n'):
                    line = line.strip()
                    if line.startswith('// @'):
                        parts = line[4:].split(None, 1)
                        if len(parts) >= 1:
                            key = parts[0].lower()
                            value = parts[1] if len(parts) > 1 else True
                            metadata[key] = value
                
                # Extract code after metadata block
                code = content[metadata_match.end():].strip()
                
            return cls(Path(file_path).stem, code, metadata)
            
        except Exception as e:
            print(f"Error loading userscript {file_path}: {e}")
            return None
            
    def _pattern_to_regex(self, pattern):
        """Convert userscript pattern to regex pattern."""
        if not pattern or not isinstance(pattern, str):
            return None
            
        # Escape regex special characters except * and ?
        # Convert * to .* and ? to . in regex
        regex_pattern = re.escape(pattern)
        regex_pattern = regex_pattern.replace(r'\*', '.*').replace(r'\?', '.')
        
        # Anchor to start and end if pattern doesn't have wildcards at boundaries
        if not regex_pattern.startswith('.*'):
            regex_pattern = '^' + regex_pattern
        if not regex_pattern.endswith('.*'):
            regex_pattern = regex_pattern + '$'
            
        return regex_pattern
        
    def matches_url(self, url):
        """Check if this userscript should run on the given URL."""
        if not self.enabled:
            return False
            
        # Check include/exclude patterns
        include_patterns = self.metadata.get('include', [])
        exclude_patterns = self.metadata.get('exclude', [])
        
        # Convert to list if single pattern
        if isinstance(include_patterns, str):
            include_patterns = [include_patterns]
        if isinstance(exclude_patterns, str):
            exclude_patterns = [exclude_patterns]
            
        # Check if URL matches any exclude pattern
        for pattern in exclude_patterns:
            regex_pattern = self._pattern_to_regex(pattern)
            if regex_pattern and re.search(regex_pattern, url):
                return False
                
        # Check if URL matches any include pattern
        for pattern in include_patterns:
            regex_pattern = self._pattern_to_regex(pattern)
            if regex_pattern and re.search(regex_pattern, url):
                return True
                
        # If no include patterns, run on all pages
        return len(include_patterns) == 0
        
    def get_injection_code(self):
        """Get the JavaScript code for injection."""
        if not self.enabled:
            return ""
            
        # Wrap in IIFE to avoid polluting global scope
        return f"""
(function() {{
    'use strict';
    {self.code}
}})();
"""

class UserscriptManager(QObject):
    """Manages userscripts and their injection into web pages."""
    
    def __init__(self):
        super().__init__()
        self.scripts = []
        self.scripts_dir = Path("userscripts")
        self.settings = QSettings("VoyxBrowser", "Userscripts")
        self.enabled = self.settings.value("userscripts_enabled", True, type=bool)
        self.load_scripts()
        
    def load_scripts(self):
        """Load all userscripts from the scripts directory."""
        # Create scripts directory if it doesn't exist
        self.scripts_dir.mkdir(exist_ok=True)
        
        self.scripts.clear()
        
        # Load scripts from directory
        for script_file in self.scripts_dir.glob("*.user.js"):
            script = Userscript.from_file(script_file)
            if script:
                # Load enabled state from settings
                enabled = self.settings.value(f"script_{script.name}_enabled", True, type=bool)
                script.enabled = enabled
                self.scripts.append(script)
                
        # Create example script if none exist
        if not self.scripts:
            self.create_example_script()
            
    def create_example_script(self):
        """Create an example userscript."""
        example_script = """// ==UserScript==
// @name        Example Userscript
// @namespace   VoyxBrowser
// @version     1.0
// @description Example userscript for Voyx Browser
// @author      Voyx Browser
// @include     *
// ==/UserScript==

// This is an example userscript
console.log('Example userscript loaded!');

// Remove annoying elements
document.querySelectorAll('.ad, .popup, [class*="advertisement"]').forEach(el => {
    el.style.display = 'none';
});
"""
        
        example_path = self.scripts_dir / "example.user.js"
        with open(example_path, 'w', encoding='utf-8') as f:
            f.write(example_script)
            
        script = Userscript.from_file(example_path)
        if script:
            self.scripts.append(script)
            
    def inject_scripts(self, web_view):
        """Inject all matching userscripts into a web view."""
        if not self.enabled or not isinstance(web_view, QWebEngineView):
            return
            
        current_url = web_view.url().toString()
        
        for script in self.scripts:
            if script.matches_url(current_url):
                injection_code = script.get_injection_code()
                if injection_code:
                    web_view.page().runJavaScript(injection_code)
                    
    def get_script_by_name(self, name):
        """Get a script by its name."""
        for script in self.scripts:
            if script.name == name:
                return script
        return None
        
    def enable_script(self, name, enabled):
        """Enable or disable a script."""
        script = self.get_script_by_name(name)
        if script:
            script.enabled = enabled
            self.settings.setValue(f"script_{name}_enabled", enabled)
            
    def create_script(self, name, code, metadata=None):
        """Create a new userscript."""
        script_path = self.scripts_dir / f"{name}.user.js"
        
        # Add metadata block if provided
        full_code = ""
        if metadata:
            full_code += "// ==UserScript==\n"
            for key, value in metadata.items():
                if value is True:
                    full_code += f"// @{key}\n"
                else:
                    full_code += f"// @{key} {value}\n"
            full_code += "// ==/UserScript==\n\n"
            
        full_code += code
        
        try:
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(full_code)
                
            script = Userscript.from_file(script_path)
            if script:
                self.scripts.append(script)
                return True
                
        except Exception as e:
            print(f"Error creating script {name}: {e}")
            
        return False
        
    def delete_script(self, name):
        """Delete a userscript."""
        script = self.get_script_by_name(name)
        if script:
            script_path = self.scripts_dir / f"{name}.user.js"
            try:
                script_path.unlink()
                self.scripts.remove(script)
                return True
            except Exception as e:
                print(f"Error deleting script {name}: {e}")
        return False
        
    def get_all_scripts(self):
        """Get all userscripts with their metadata."""
        return [
            {
                'name': script.name,
                'enabled': script.enabled,
                'metadata': script.metadata,
                'code': script.code
            }
            for script in self.scripts
        ]
        
    def reload_scripts(self):
        """Reload all userscripts from disk."""
        self.load_scripts()
