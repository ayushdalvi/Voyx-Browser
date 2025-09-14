"""
Simple Userscript Manager - Easy to use interface
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QPushButton, QTextEdit, QLabel, QLineEdit, 
                             QMessageBox, QFileDialog, QInputDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from pathlib import Path

class SimpleUserscriptManager(QDialog):
    """Simple userscript manager interface."""
    
    def __init__(self, userscript_manager, parent=None):
        super().__init__(parent)
        self.userscript_manager = userscript_manager
        self.setup_ui()
        self.load_scripts()
        
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Userscript Manager")
        self.setGeometry(200, 200, 800, 600)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("📜 Userscript Manager")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.new_btn = QPushButton("➕ New Script")
        self.install_btn = QPushButton("🌐 Install from URL")
        self.edit_btn = QPushButton("✏️ Edit Script")
        self.enable_btn = QPushButton("✅ Enable")
        self.disable_btn = QPushButton("❌ Disable")
        self.delete_btn = QPushButton("🗑️ Delete")
        
        button_layout.addWidget(self.new_btn)
        button_layout.addWidget(self.install_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.enable_btn)
        button_layout.addWidget(self.disable_btn)
        button_layout.addWidget(self.delete_btn)
        
        layout.addLayout(button_layout)
        
        # Script list
        layout.addWidget(QLabel("Your Scripts:"))
        self.script_list = QListWidget()
        layout.addWidget(self.script_list)
        
        # Script preview
        layout.addWidget(QLabel("Script Preview:"))
        self.script_preview = QTextEdit()
        self.script_preview.setMaximumHeight(200)
        self.script_preview.setReadOnly(True)
        layout.addWidget(self.script_preview)
        
        # Connect buttons
        self.new_btn.clicked.connect(self.new_script)
        self.install_btn.clicked.connect(self.install_from_url)
        self.edit_btn.clicked.connect(self.edit_script)
        self.enable_btn.clicked.connect(self.enable_script)
        self.disable_btn.clicked.connect(self.disable_script)
        self.delete_btn.clicked.connect(self.delete_script)
        self.script_list.itemClicked.connect(self.show_script_preview)
        
        # Style
        self.setStyleSheet("""
            QDialog { background-color: #f0f0f0; }
            QPushButton { 
                padding: 8px; 
                font-size: 12px; 
                border: 1px solid #ccc; 
                border-radius: 4px; 
                background-color: white; 
            }
            QPushButton:hover { background-color: #e0e0e0; }
            QListWidget { 
                border: 1px solid #ccc; 
                border-radius: 4px; 
                background-color: white; 
            }
            QTextEdit { 
                border: 1px solid #ccc; 
                border-radius: 4px; 
                background-color: white; 
            }
        """)
    
    def load_scripts(self):
        """Load scripts into the list."""
        self.script_list.clear()
        for script in self.userscript_manager.scripts:
            status = "✅" if script.enabled else "❌"
            item_text = f"{status} {script.name}"
            self.script_list.addItem(item_text)
    
    def show_script_preview(self, item):
        """Show script preview."""
        script_name = item.text().split(" ", 1)[1] if " " in item.text() else item.text()
        script = self.userscript_manager.get_script_by_name(script_name)
        if script:
            preview = f"Name: {script.name}\n"
            preview += f"Enabled: {'Yes' if script.enabled else 'No'}\n"
            preview += f"Description: {script.metadata.get('description', 'No description')}\n\n"
            preview += "Code:\n" + script.code[:500] + ("..." if len(script.code) > 500 else "")
            self.script_preview.setText(preview)
    
    def new_script(self):
        """Create a new script."""
        dialog = ScriptEditorDialog(self, "New Script")
        if dialog.exec_() == QDialog.Accepted:
            name, code = dialog.get_script_data()
            if name and code:
                if self.userscript_manager.create_script(name, code):
                    self.userscript_manager.reload_scripts()
                    self.load_scripts()
                    QMessageBox.information(self, "Success", f"Script '{name}' created!")
                else:
                    QMessageBox.warning(self, "Error", "Failed to create script")
    
    def install_from_url(self):
        """Install script from URL."""
        url, ok = QInputDialog.getText(self, "Install Script", 
                                      "Enter script URL (from Greasyfork, GitHub, etc.):")
        if not ok or not url:
            return
        
        try:
            import requests
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                content = response.text
                script_name = "downloaded_script"
                
                import re
                name_match = re.search(r'// @name\s+(.+)', content)
                if name_match:
                    script_name = name_match.group(1).strip()
                
                script_path = self.userscript_manager.scripts_dir / f"{script_name}.user.js"
                with open(script_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.userscript_manager.reload_scripts()
                self.load_scripts()
                QMessageBox.information(self, "Success", f"Script '{script_name}' installed!")
            else:
                QMessageBox.warning(self, "Error", f"Failed to download: HTTP {response.status_code}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to install script: {str(e)}")
    
    def edit_script(self):
        """Edit selected script."""
        current_item = self.script_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a script first")
            return
        
        script_name = current_item.text().split(" ", 1)[1] if " " in current_item.text() else current_item.text()
        script = self.userscript_manager.get_script_by_name(script_name)
        
        if script:
            metadata_block = "// ==UserScript==\n"
            for key, value in script.metadata.items():
                if isinstance(value, list):
                    for v in value:
                        metadata_block += f"// @{key} {v}\n"
                else:
                    metadata_block += f"// @{key} {value}\n"
            metadata_block += "// ==/UserScript==\n\n"
            
            full_code = metadata_block + script.code
            
            dialog = ScriptEditorDialog(self, f"Edit {script_name}", script_name, full_code)
            if dialog.exec_() == QDialog.Accepted:
                name, code = dialog.get_script_data()
                if name and code:
                    script_path = script.file_path if hasattr(script, 'file_path') and script.file_path else self.userscript_manager.scripts_dir / f"{name}.user.js"
                    try:
                        with open(script_path, 'w', encoding='utf-8') as f:
                            f.write(code)
                        self.userscript_manager.reload_scripts()
                        self.load_scripts()
                        QMessageBox.information(self, "Success", f"Script '{name}' updated!")
                    except Exception as e:
                        QMessageBox.warning(self, "Error", f"Failed to save script: {str(e)}")
    
    def enable_script(self):
        """Enable selected script."""
        current_item = self.script_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a script first")
            return
        
        script_name = current_item.text().split(" ", 1)[1] if " " in current_item.text() else current_item.text()
        self.userscript_manager.enable_script(script_name, True)
        self.load_scripts()
        QMessageBox.information(self, "Success", f"Script '{script_name}' enabled!")
    
    def disable_script(self):
        """Disable selected script."""
        current_item = self.script_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a script first")
            return
        
        script_name = current_item.text().split(" ", 1)[1] if " " in current_item.text() else current_item.text()
        self.userscript_manager.enable_script(script_name, False)
        self.load_scripts()
        QMessageBox.information(self, "Success", f"Script '{script_name}' disabled!")
    
    def delete_script(self):
        """Delete selected script."""
        current_item = self.script_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a script first")
            return
        
        script_name = current_item.text().split(" ", 1)[1] if " " in current_item.text() else current_item.text()
        
        reply = QMessageBox.question(self, "Confirm Delete", 
                                   f"Are you sure you want to delete '{script_name}'?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if self.userscript_manager.delete_script(script_name):
                self.load_scripts()
                QMessageBox.information(self, "Success", f"Script '{script_name}' deleted!")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete script")

class ScriptEditorDialog(QDialog):
    """Dialog for creating and editing scripts."""
    
    def __init__(self, parent=None, title="Script Editor", name="", code=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setGeometry(300, 300, 800, 600)
        
        layout = QVBoxLayout(self)
        
        # Script name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Script Name:"))
        self.name_edit = QLineEdit(name)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # Code editor
        layout.addWidget(QLabel("Script Code:"))
        self.code_edit = QTextEdit()
        self.code_edit.setFont(QFont("Consolas", 10))
        
        if not code:
            default_name = name or "My Script"
            code = f"""// ==UserScript==
// @name        {default_name}
// @namespace   VoyxBrowser
// @version     1.0
// @description My new userscript
// @author      Me
// @include     *
// ==/UserScript==

console.log('{default_name} loaded!');

// Your code here - you can:
// - Remove ads: document.querySelectorAll('.ad').forEach(el => el.remove());
// - Change colors: document.body.style.backgroundColor = 'black';
// - Add buttons: document.body.innerHTML += '<button>My Button</button>';
// - And much more!
"""
        
        self.code_edit.setText(code)
        layout.addWidget(self.code_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Save")
        cancel_btn = QPushButton("❌ Cancel")
        
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        # Style
        self.setStyleSheet("""
            QDialog { background-color: #f0f0f0; }
            QTextEdit { 
                border: 1px solid #ccc; 
                border-radius: 4px; 
                background-color: white;
                font-family: 'Consolas', 'Monaco', monospace;
            }
            QLineEdit { 
                border: 1px solid #ccc; 
                border-radius: 4px; 
                background-color: white;
                padding: 5px;
            }
            QPushButton { 
                padding: 8px 16px; 
                font-size: 12px; 
                border: 1px solid #ccc; 
                border-radius: 4px; 
                background-color: white; 
            }
            QPushButton:hover { background-color: #e0e0e0; }
        """)
    
    def get_script_data(self):
        """Get script name and code."""
        return self.name_edit.text().strip(), self.code_edit.toPlainText()