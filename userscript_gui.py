"""
Userscript Manager GUI - Tampermonkey-style interface for managing userscripts.
"""

import os
import json
import re
import requests
from pathlib import Path
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QListWidget, QListWidgetItem, QTextEdit, QPushButton,
                             QLabel, QLineEdit, QCheckBox, QComboBox, QSplitter,
                             QGroupBox, QFormLayout, QSpinBox, QMessageBox,
                             QFileDialog, QProgressBar, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMenu, QAction, QInputDialog, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSettings
from PyQt5.QtGui import QFont, QIcon, QPixmap, QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt5.QtWebEngineWidgets import QWebEngineView

class JavaScriptHighlighter(QSyntaxHighlighter):
    """JavaScript syntax highlighter for the code editor."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setColor(QColor(86, 156, 214))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = ['function', 'var', 'let', 'const', 'if', 'else', 'for', 'while', 
                   'return', 'true', 'false', 'null', 'undefined', 'new', 'this']
        for word in keywords:
            pattern = f'\\b{word}\\b'
            self.highlighting_rules.append((re.compile(pattern), keyword_format))
        
        # Strings
        string_format = QTextCharFormat()
        string_format.setColor(QColor(206, 145, 120))
        self.highlighting_rules.append((re.compile(r'".*?"'), string_format))
        self.highlighting_rules.append((re.compile(r"'.*?'"), string_format))
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setColor(QColor(106, 153, 85))
        self.highlighting_rules.append((re.compile(r'//.*'), comment_format))
        self.highlighting_rules.append((re.compile(r'/\*.*?\*/'), comment_format))
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setColor(QColor(181, 206, 168))
        self.highlighting_rules.append((re.compile(r'\b\d+\.?\d*\b'), number_format))
    
    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, format)

class ScriptDownloader(QThread):
    """Thread for downloading userscripts from URLs."""
    
    progress = pyqtSignal(int)
    finished = pyqtSignal(str, str)  # script_content, filename
    error = pyqtSignal(str)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
    
    def run(self):
        try:
            response = requests.get(self.url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            content = ""
            
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    content += chunk.decode('utf-8', errors='ignore')
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = int((downloaded / total_size) * 100)
                        self.progress.emit(progress)
            
            filename = self.url.split('/')[-1]
            if not filename.endswith('.user.js'):
                filename += '.user.js'
            
            self.finished.emit(content, filename)
            
        except Exception as e:
            self.error.emit(str(e))

class UserscriptManagerGUI(QDialog):
    """Main userscript manager interface."""
    
    def __init__(self, userscript_manager, parent=None):
        super().__init__(parent)
        self.userscript_manager = userscript_manager
        self.settings = QSettings("VoyxBrowser", "UserscriptManager")
        self.current_script = None
        self.setup_ui()
        self.load_scripts()
        
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Userscript Manager - Voyx Browser")
        self.setGeometry(100, 100, 1200, 800)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self.new_script_btn = QPushButton("New Script")
        self.import_btn = QPushButton("Import")
        self.export_btn = QPushButton("Export")
        self.install_url_btn = QPushButton("Install from URL")
        self.backup_btn = QPushButton("Backup")
        self.restore_btn = QPushButton("Restore")
        self.settings_btn = QPushButton("Settings")
        
        toolbar_layout.addWidget(self.new_script_btn)
        toolbar_layout.addWidget(self.import_btn)
        toolbar_layout.addWidget(self.export_btn)
        toolbar_layout.addWidget(self.install_url_btn)
        toolbar_layout.addWidget(self.backup_btn)
        toolbar_layout.addWidget(self.restore_btn)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.settings_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Main content area
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Scripts tab
        self.setup_scripts_tab()
        
        # Editor tab
        self.setup_editor_tab()
        
        # Statistics tab
        self.setup_statistics_tab()
        
        # Connect signals
        self.connect_signals()
        
        # Apply dark theme
        self.apply_dark_theme()
    
    def setup_scripts_tab(self):
        """Set up the scripts management tab."""
        scripts_widget = QWidget()
        layout = QHBoxLayout(scripts_widget)
        
        # Left panel - script list
        left_panel = QGroupBox("Installed Scripts")
        left_layout = QVBoxLayout(left_panel)
        
        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search scripts...")
        left_layout.addWidget(self.search_bar)
        
        # Script list
        self.script_list = QListWidget()
        self.script_list.setContextMenuPolicy(Qt.CustomContextMenu)
        left_layout.addWidget(self.script_list)
        
        # Script controls
        controls_layout = QHBoxLayout()
        self.enable_btn = QPushButton("Enable")
        self.disable_btn = QPushButton("Disable")
        self.edit_btn = QPushButton("Edit")
        self.delete_btn = QPushButton("Delete")
        
        controls_layout.addWidget(self.enable_btn)
        controls_layout.addWidget(self.disable_btn)
        controls_layout.addWidget(self.edit_btn)
        controls_layout.addWidget(self.delete_btn)
        left_layout.addLayout(controls_layout)
        
        layout.addWidget(left_panel, 1)
        
        # Right panel - script details
        right_panel = QGroupBox("Script Details")
        right_layout = QVBoxLayout(right_panel)
        
        # Script info
        self.script_info = QTextEdit()
        self.script_info.setReadOnly(True)
        self.script_info.setMaximumHeight(200)
        right_layout.addWidget(self.script_info)
        
        # Metadata editor
        metadata_group = QGroupBox("Metadata")
        metadata_layout = QFormLayout(metadata_group)
        
        self.name_edit = QLineEdit()
        self.version_edit = QLineEdit()
        self.description_edit = QLineEdit()
        self.author_edit = QLineEdit()
        self.namespace_edit = QLineEdit()
        
        metadata_layout.addRow("Name:", self.name_edit)
        metadata_layout.addRow("Version:", self.version_edit)
        metadata_layout.addRow("Description:", self.description_edit)
        metadata_layout.addRow("Author:", self.author_edit)
        metadata_layout.addRow("Namespace:", self.namespace_edit)
        
        right_layout.addWidget(metadata_group)
        
        # URL patterns
        patterns_group = QGroupBox("URL Patterns")
        patterns_layout = QVBoxLayout(patterns_group)
        
        self.include_list = QListWidget()
        self.include_list.setMaximumHeight(100)
        patterns_layout.addWidget(QLabel("Include patterns:"))
        patterns_layout.addWidget(self.include_list)
        
        include_controls = QHBoxLayout()
        self.add_include_btn = QPushButton("Add")
        self.remove_include_btn = QPushButton("Remove")
        include_controls.addWidget(self.add_include_btn)
        include_controls.addWidget(self.remove_include_btn)
        patterns_layout.addLayout(include_controls)
        
        self.exclude_list = QListWidget()
        self.exclude_list.setMaximumHeight(100)
        patterns_layout.addWidget(QLabel("Exclude patterns:"))
        patterns_layout.addWidget(self.exclude_list)
        
        exclude_controls = QHBoxLayout()
        self.add_exclude_btn = QPushButton("Add")
        self.remove_exclude_btn = QPushButton("Remove")
        exclude_controls.addWidget(self.add_exclude_btn)
        exclude_controls.addWidget(self.remove_exclude_btn)
        patterns_layout.addLayout(exclude_controls)
        
        right_layout.addWidget(patterns_group)
        
        # Save button
        self.save_metadata_btn = QPushButton("Save Metadata")
        right_layout.addWidget(self.save_metadata_btn)
        
        layout.addWidget(right_panel, 1)
        
        self.tab_widget.addTab(scripts_widget, "Scripts")
    
    def setup_editor_tab(self):
        """Set up the script editor tab."""
        editor_widget = QWidget()
        layout = QVBoxLayout(editor_widget)
        
        # Editor toolbar
        editor_toolbar = QHBoxLayout()
        
        self.editor_script_combo = QComboBox()
        self.save_script_btn = QPushButton("Save")
        self.run_script_btn = QPushButton("Test Run")
        self.format_btn = QPushButton("Format Code")
        
        editor_toolbar.addWidget(QLabel("Script:"))
        editor_toolbar.addWidget(self.editor_script_combo)
        editor_toolbar.addStretch()
        editor_toolbar.addWidget(self.format_btn)
        editor_toolbar.addWidget(self.run_script_btn)
        editor_toolbar.addWidget(self.save_script_btn)
        
        layout.addLayout(editor_toolbar)
        
        # Code editor
        self.code_editor = QTextEdit()
        self.code_editor.setFont(QFont("Consolas", 10))
        self.highlighter = JavaScriptHighlighter(self.code_editor.document())
        layout.addWidget(self.code_editor)
        
        # Status bar
        self.editor_status = QLabel("Ready")
        layout.addWidget(self.editor_status)
        
        self.tab_widget.addTab(editor_widget, "Editor")
    
    def setup_statistics_tab(self):
        """Set up the statistics tab."""
        stats_widget = QWidget()
        layout = QVBoxLayout(stats_widget)
        
        # Statistics table
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(4)
        self.stats_table.setHorizontalHeaderLabels(["Script", "Runs", "Last Run", "Status"])
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.stats_table)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Statistics")
        refresh_btn.clicked.connect(self.refresh_statistics)
        layout.addWidget(refresh_btn)
        
        self.tab_widget.addTab(stats_widget, "Statistics")
    
    def connect_signals(self):
        """Connect UI signals to handlers."""
        # Toolbar buttons
        self.new_script_btn.clicked.connect(self.new_script)
        self.import_btn.clicked.connect(self.import_script)
        self.export_btn.clicked.connect(self.export_script)
        self.install_url_btn.clicked.connect(self.install_from_url)
        self.backup_btn.clicked.connect(self.backup_scripts)
        self.restore_btn.clicked.connect(self.restore_scripts)
        self.settings_btn.clicked.connect(self.open_settings)
        
        # Script list
        self.script_list.itemClicked.connect(self.on_script_selected)
        self.script_list.customContextMenuRequested.connect(self.show_context_menu)
        self.search_bar.textChanged.connect(self.filter_scripts)
        
        # Script controls
        self.enable_btn.clicked.connect(self.enable_script)
        self.disable_btn.clicked.connect(self.disable_script)
        self.edit_btn.clicked.connect(self.edit_script)
        self.delete_btn.clicked.connect(self.delete_script)
        
        # Metadata
        self.save_metadata_btn.clicked.connect(self.save_metadata)
        self.add_include_btn.clicked.connect(self.add_include_pattern)
        self.remove_include_btn.clicked.connect(self.remove_include_pattern)
        self.add_exclude_btn.clicked.connect(self.add_exclude_pattern)
        self.remove_exclude_btn.clicked.connect(self.remove_exclude_pattern)
        
        # Editor
        self.editor_script_combo.currentTextChanged.connect(self.load_script_in_editor)
        self.save_script_btn.clicked.connect(self.save_script_code)
        self.run_script_btn.clicked.connect(self.test_run_script)
        self.format_btn.clicked.connect(self.format_code)
    
    def apply_dark_theme(self):
        """Apply dark theme to the interface."""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 8px 16px;
                border: 1px solid #555555;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: #2b2b2b;
                border-bottom: 1px solid #2b2b2b;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                padding: 6px 12px;
                border-radius: 3px;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
            }
            QPushButton:pressed {
                background-color: #1c1c1c;
            }
            QListWidget, QTextEdit, QLineEdit, QComboBox {
                background-color: #1e1e1e;
                border: 1px solid #555555;
                color: #ffffff;
                padding: 4px;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
            }
            QTableWidget {
                background-color: #1e1e1e;
                alternate-background-color: #2a2a2a;
                gridline-color: #555555;
            }
            QHeaderView::section {
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 4px;
                border: 1px solid #555555;
            }
        """)
    
    def load_scripts(self):
        """Load scripts into the interface."""
        self.script_list.clear()
        self.editor_script_combo.clear()
        
        for script in self.userscript_manager.scripts:
            item = QListWidgetItem(script.name)
            item.setData(Qt.UserRole, script)
            
            # Set icon based on enabled state
            if script.enabled:
                item.setText(f"✓ {script.name}")
                item.setForeground(QColor(0, 255, 0))
            else:
                item.setText(f"✗ {script.name}")
                item.setForeground(QColor(255, 0, 0))
            
            self.script_list.addItem(item)
            self.editor_script_combo.addItem(script.name)
    
    def filter_scripts(self, text):
        """Filter scripts based on search text."""
        for i in range(self.script_list.count()):
            item = self.script_list.item(i)
            script = item.data(Qt.UserRole)
            visible = text.lower() in script.name.lower() or text.lower() in script.metadata.get('description', '').lower()
            item.setHidden(not visible)
    
    def on_script_selected(self, item):
        """Handle script selection."""
        self.current_script = item.data(Qt.UserRole)
        self.update_script_details()
    
    def update_script_details(self):
        """Update the script details panel."""
        if not self.current_script:
            return
        
        # Update script info
        info = f"Name: {self.current_script.name}\n"
        info += f"Enabled: {'Yes' if self.current_script.enabled else 'No'}\n"
        info += f"Version: {self.current_script.metadata.get('version', 'Unknown')}\n"
        info += f"Author: {self.current_script.metadata.get('author', 'Unknown')}\n"
        info += f"Description: {self.current_script.metadata.get('description', 'No description')}\n"
        info += f"Lines of code: {len(self.current_script.code.split('\\n'))}"
        
        self.script_info.setText(info)
        
        # Update metadata fields
        self.name_edit.setText(self.current_script.name)
        self.version_edit.setText(self.current_script.metadata.get('version', ''))
        self.description_edit.setText(self.current_script.metadata.get('description', ''))
        self.author_edit.setText(self.current_script.metadata.get('author', ''))
        self.namespace_edit.setText(self.current_script.metadata.get('namespace', ''))
        
        # Update URL patterns
        self.include_list.clear()
        includes = self.current_script.metadata.get('include', [])
        if isinstance(includes, str):
            includes = [includes]
        for pattern in includes:
            self.include_list.addItem(pattern)
        
        self.exclude_list.clear()
        excludes = self.current_script.metadata.get('exclude', [])
        if isinstance(excludes, str):
            excludes = [excludes]
        for pattern in excludes:
            self.exclude_list.addItem(pattern)
    
    def new_script(self):
        """Create a new script."""
        dialog = NewScriptDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            name, template_code = dialog.get_script_data()
            if self.userscript_manager.create_script(name, template_code):
                self.userscript_manager.reload_scripts()
                self.load_scripts()
                QMessageBox.information(self, "Success", f"Script '{name}' created successfully!")
            else:
                QMessageBox.warning(self, "Error", f"Failed to create script '{name}'")
    
    def import_script(self):
        """Import a script from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Script", "", "JavaScript Files (*.js *.user.js);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                script_name = Path(file_path).stem
                script_path = self.userscript_manager.scripts_dir / f"{script_name}.user.js"
                
                with open(script_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.userscript_manager.reload_scripts()
                self.load_scripts()
                QMessageBox.information(self, "Success", f"Script imported successfully!")
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to import script: {str(e)}")
    
    def export_script(self):
        """Export selected script."""
        if not self.current_script:
            QMessageBox.warning(self, "Warning", "Please select a script to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Script", f"{self.current_script.name}.user.js",
            "JavaScript Files (*.js *.user.js);;All Files (*)"
        )
        
        if file_path:
            try:
                # Reconstruct full script with metadata
                metadata_block = "// ==UserScript==\n"
                for key, value in self.current_script.metadata.items():
                    if isinstance(value, list):
                        for v in value:
                            metadata_block += f"// @{key} {v}\n"
                    else:
                        metadata_block += f"// @{key} {value}\n"
                metadata_block += "// ==/UserScript==\n\n"
                
                full_content = metadata_block + self.current_script.code
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(full_content)
                
                QMessageBox.information(self, "Success", "Script exported successfully!")
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to export script: {str(e)}")
    
    def install_from_url(self):
        """Install script from URL."""
        url, ok = QInputDialog.getText(self, "Install from URL", "Script URL:")
        if ok and url:
            # Show progress dialog
            progress_dialog = QDialog(self)
            progress_dialog.setWindowTitle("Downloading Script")
            progress_dialog.setModal(True)
            progress_layout = QVBoxLayout(progress_dialog)
            
            progress_bar = QProgressBar()
            progress_layout.addWidget(QLabel("Downloading script..."))
            progress_layout.addWidget(progress_bar)
            
            cancel_btn = QPushButton("Cancel")
            progress_layout.addWidget(cancel_btn)
            
            progress_dialog.show()
            
            # Start download
            self.downloader = ScriptDownloader(url)
            self.downloader.progress.connect(progress_bar.setValue)
            self.downloader.finished.connect(lambda content, filename: self.on_download_finished(content, filename, progress_dialog))
            self.downloader.error.connect(lambda error: self.on_download_error(error, progress_dialog))
            cancel_btn.clicked.connect(lambda: self.downloader.terminate())
            self.downloader.start()
    
    def on_download_finished(self, content, filename, dialog):
        """Handle successful script download."""
        dialog.close()
        
        try:
            script_path = self.userscript_manager.scripts_dir / filename
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.userscript_manager.reload_scripts()
            self.load_scripts()
            QMessageBox.information(self, "Success", f"Script '{filename}' installed successfully!")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save script: {str(e)}")
    
    def on_download_error(self, error, dialog):
        """Handle download error."""
        dialog.close()
        QMessageBox.warning(self, "Download Error", f"Failed to download script: {error}")
    
    def enable_script(self):
        """Enable selected script."""
        if self.current_script:
            self.userscript_manager.enable_script(self.current_script.name, True)
            self.load_scripts()
            self.update_script_details()
    
    def disable_script(self):
        """Disable selected script."""
        if self.current_script:
            self.userscript_manager.enable_script(self.current_script.name, False)
            self.load_scripts()
            self.update_script_details()
    
    def edit_script(self):
        """Edit selected script in editor tab."""
        if self.current_script:
            self.tab_widget.setCurrentIndex(1)  # Switch to editor tab
            self.editor_script_combo.setCurrentText(self.current_script.name)
            self.load_script_in_editor(self.current_script.name)
    
    def delete_script(self):
        """Delete selected script."""
        if not self.current_script:
            return
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete '{self.current_script.name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.userscript_manager.delete_script(self.current_script.name):
                self.load_scripts()
                self.current_script = None
                self.script_info.clear()
                QMessageBox.information(self, "Success", "Script deleted successfully!")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete script.")
    
    def save_metadata(self):
        """Save script metadata."""
        if not self.current_script:
            return
        
        # Update metadata
        self.current_script.metadata['name'] = self.name_edit.text()
        self.current_script.metadata['version'] = self.version_edit.text()
        self.current_script.metadata['description'] = self.description_edit.text()
        self.current_script.metadata['author'] = self.author_edit.text()
        self.current_script.metadata['namespace'] = self.namespace_edit.text()
        
        # Update include patterns
        includes = []
        for i in range(self.include_list.count()):
            includes.append(self.include_list.item(i).text())
        self.current_script.metadata['include'] = includes
        
        # Update exclude patterns
        excludes = []
        for i in range(self.exclude_list.count()):
            excludes.append(self.exclude_list.item(i).text())
        self.current_script.metadata['exclude'] = excludes
        
        # Save to file
        self.save_script_to_file(self.current_script)
        QMessageBox.information(self, "Success", "Metadata saved successfully!")
    
    def save_script_to_file(self, script):
        """Save script with metadata to file."""
        script_path = self.userscript_manager.scripts_dir / f"{script.name}.user.js"
        
        # Reconstruct full script
        metadata_block = "// ==UserScript==\n"
        for key, value in script.metadata.items():
            if isinstance(value, list):
                for v in value:
                    metadata_block += f"// @{key} {v}\n"
            else:
                metadata_block += f"// @{key} {value}\n"
        metadata_block += "// ==/UserScript==\n\n"
        
        full_content = metadata_block + script.code
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
    
    def add_include_pattern(self):
        """Add include pattern."""
        pattern, ok = QInputDialog.getText(self, "Add Include Pattern", "URL pattern:")
        if ok and pattern:
            self.include_list.addItem(pattern)
    
    def remove_include_pattern(self):
        """Remove selected include pattern."""
        current_row = self.include_list.currentRow()
        if current_row >= 0:
            self.include_list.takeItem(current_row)
    
    def add_exclude_pattern(self):
        """Add exclude pattern."""
        pattern, ok = QInputDialog.getText(self, "Add Exclude Pattern", "URL pattern:")
        if ok and pattern:
            self.exclude_list.addItem(pattern)
    
    def remove_exclude_pattern(self):
        """Remove selected exclude pattern."""
        current_row = self.exclude_list.currentRow()
        if current_row >= 0:
            self.exclude_list.takeItem(current_row)
    
    def load_script_in_editor(self, script_name):
        """Load script code in editor."""
        script = self.userscript_manager.get_script_by_name(script_name)
        if script:
            self.code_editor.setText(script.code)
            self.editor_status.setText(f"Loaded: {script_name}")
    
    def save_script_code(self):
        """Save script code from editor."""
        script_name = self.editor_script_combo.currentText()
        if not script_name:
            return
        
        script = self.userscript_manager.get_script_by_name(script_name)
        if script:
            script.code = self.code_editor.toPlainText()
            self.save_script_to_file(script)
            self.editor_status.setText(f"Saved: {script_name}")
            QMessageBox.information(self, "Success", "Script saved successfully!")
    
    def test_run_script(self):
        """Test run the script (basic validation)."""
        code = self.code_editor.toPlainText()
        
        # Basic JavaScript syntax validation
        try:
            # Simple validation - check for basic syntax errors
            if not code.strip():
                raise ValueError("Script is empty")
            
            # Check for balanced brackets
            brackets = {'(': ')', '[': ']', '{': '}'}
            stack = []
            for char in code:
                if char in brackets:
                    stack.append(char)
                elif char in brackets.values():
                    if not stack or brackets[stack.pop()] != char:
                        raise ValueError("Unbalanced brackets")
            
            if stack:
                raise ValueError("Unbalanced brackets")
            
            self.editor_status.setText("Script validation passed!")
            QMessageBox.information(self, "Validation", "Script syntax appears to be valid!")
            
        except Exception as e:
            self.editor_status.setText(f"Validation error: {str(e)}")
            QMessageBox.warning(self, "Validation Error", f"Script validation failed: {str(e)}")
    
    def format_code(self):
        """Basic code formatting."""
        code = self.code_editor.toPlainText()
        
        # Simple formatting - add proper indentation
        lines = code.split('\n')
        formatted_lines = []
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                formatted_lines.append('')
                continue
            
            # Decrease indent for closing brackets
            if stripped.startswith('}') or stripped.startswith(']') or stripped.startswith(')'):
                indent_level = max(0, indent_level - 1)
            
            # Add indentation
            formatted_lines.append('    ' * indent_level + stripped)
            
            # Increase indent for opening brackets
            if stripped.endswith('{') or stripped.endswith('[') or stripped.endswith('('):
                indent_level += 1
        
        self.code_editor.setText('\n'.join(formatted_lines))
        self.editor_status.setText("Code formatted!")
    
    def refresh_statistics(self):
        """Refresh statistics table."""
        self.stats_table.setRowCount(len(self.userscript_manager.scripts))
        
        for i, script in enumerate(self.userscript_manager.scripts):
            self.stats_table.setItem(i, 0, QTableWidgetItem(script.name))
            self.stats_table.setItem(i, 1, QTableWidgetItem("N/A"))  # Run count not implemented
            self.stats_table.setItem(i, 2, QTableWidgetItem("N/A"))  # Last run not implemented
            self.stats_table.setItem(i, 3, QTableWidgetItem("Enabled" if script.enabled else "Disabled"))
    
    def show_context_menu(self, position):
        """Show context menu for script list."""
        item = self.script_list.itemAt(position)
        if item:
            menu = QMenu(self)
            
            enable_action = QAction("Enable", self)
            disable_action = QAction("Disable", self)
            edit_action = QAction("Edit", self)
            delete_action = QAction("Delete", self)
            export_action = QAction("Export", self)
            
            enable_action.triggered.connect(self.enable_script)
            disable_action.triggered.connect(self.disable_script)
            edit_action.triggered.connect(self.edit_script)
            delete_action.triggered.connect(self.delete_script)
            export_action.triggered.connect(self.export_script)
            
            menu.addAction(enable_action)
            menu.addAction(disable_action)
            menu.addSeparator()
            menu.addAction(edit_action)
            menu.addAction(export_action)
            menu.addSeparator()
            menu.addAction(delete_action)
            
            menu.exec_(self.script_list.mapToGlobal(position))
    
    def backup_scripts(self):
        """Backup all scripts and settings."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Backup Scripts", "userscripts_backup.json",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                backup_data = self.userscript_manager.export_settings()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(backup_data)
                QMessageBox.information(self, "Success", "Scripts backed up successfully!")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to backup scripts: {str(e)}")
    
    def restore_scripts(self):
        """Restore scripts from backup."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Restore Scripts", "", "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            reply = QMessageBox.question(
                self, "Confirm Restore",
                "This will replace all current scripts. Continue?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        backup_data = f.read()
                    
                    if self.userscript_manager.import_settings(backup_data):
                        self.load_scripts()
                        QMessageBox.information(self, "Success", "Scripts restored successfully!")
                    else:
                        QMessageBox.warning(self, "Error", "Failed to restore scripts")
                        
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to restore scripts: {str(e)}")
    
    def open_settings(self):
        """Open userscript manager settings."""
        settings_dialog = UserscriptSettingsDialog(self.userscript_manager, self)
        settings_dialog.exec_()

class UserscriptSettingsDialog(QDialog):
    """Settings dialog for userscript manager."""
    
    def __init__(self, userscript_manager, parent=None):
        super().__init__(parent)
        self.userscript_manager = userscript_manager
        self.setup_ui()
    
    def setup_ui(self):
        """Set up settings UI."""
        self.setWindowTitle("Userscript Settings")
        self.setModal(True)
        layout = QVBoxLayout(self)
        
        # General settings
        general_group = QGroupBox("General Settings")
        general_layout = QFormLayout(general_group)
        
        self.enabled_checkbox = QCheckBox()
        self.enabled_checkbox.setChecked(self.userscript_manager.enabled)
        general_layout.addRow("Enable Userscripts:", self.enabled_checkbox)
        
        layout.addWidget(general_group)
        
        # Advanced settings
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QFormLayout(advanced_group)
        
        self.auto_update_checkbox = QCheckBox()
        self.auto_update_checkbox.setChecked(self.userscript_manager.auto_update)
        advanced_layout.addRow("Auto-update scripts:", self.auto_update_checkbox)
        
        self.debug_checkbox = QCheckBox()
        self.debug_checkbox.setChecked(self.userscript_manager.debug_mode)
        advanced_layout.addRow("Debug mode:", self.debug_checkbox)
        
        layout.addWidget(advanced_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        save_btn.clicked.connect(self.save_settings)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
    
    def save_settings(self):
        """Save settings."""
        self.userscript_manager.enabled = self.enabled_checkbox.isChecked()
        self.userscript_manager.auto_update = self.auto_update_checkbox.isChecked()
        self.userscript_manager.debug_mode = self.debug_checkbox.isChecked()
        
        self.userscript_manager.settings.setValue("userscripts_enabled", self.userscript_manager.enabled)
        self.userscript_manager.settings.setValue("auto_update_enabled", self.userscript_manager.auto_update)
        self.userscript_manager.settings.setValue("debug_mode", self.userscript_manager.debug_mode)
        
        # Update auto-update timer
        if self.userscript_manager.auto_update:
            self.userscript_manager.update_timer.start(3600000)
        else:
            self.userscript_manager.update_timer.stop()
        
        self.accept()

class NewScriptDialog(QDialog):
    """Dialog for creating new scripts with templates."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI."""
        self.setWindowTitle("New Script")
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Script name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Script Name:"))
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # Template selection
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("Template:"))
        self.template_combo = QComboBox()
        
        from userscript_templates import get_template_names, get_template
        self.template_combo.addItems(get_template_names())
        template_layout.addWidget(self.template_combo)
        layout.addLayout(template_layout)
        
        # Template preview
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont("Consolas", 9))
        layout.addWidget(QLabel("Template Preview:"))
        layout.addWidget(self.preview_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        create_btn = QPushButton("Create")
        cancel_btn = QPushButton("Cancel")
        
        create_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(create_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        # Connect signals
        self.template_combo.currentTextChanged.connect(self.update_preview)
        self.name_edit.textChanged.connect(self.update_preview)
        
        # Initial preview
        self.update_preview()
    
    def update_preview(self):
        """Update template preview."""
        from userscript_templates import get_template
        
        template_name = self.template_combo.currentText()
        script_name = self.name_edit.text() or "New Script"
        
        template = get_template(template_name)
        if template:
            code = template['code'].replace('New Userscript', script_name)
            code = code.replace('// @name        New Userscript', f'// @name        {script_name}')
            self.preview_text.setText(code)
    
    def get_script_data(self):
        """Get script name and code."""
        name = self.name_edit.text() or "New Script"
        return name, self.preview_text.toPlainText()