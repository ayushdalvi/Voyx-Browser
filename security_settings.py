"""
Security Settings Panel Module - Provides a GUI for configuring security settings.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                             QCheckBox, QPushButton, QLabel, QFrame, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal

class SecuritySettingsPanel(QWidget):
    """Panel for configuring security and privacy settings."""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, security_manager):
        super().__init__()
        self.security_manager = security_manager
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Create scroll area for settings
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Connection security group
        conn_group = QGroupBox("Connection Security")
        conn_layout = QVBoxLayout(conn_group)
        
        self.https_only_cb = QCheckBox("Enforce HTTPS-only mode")
        self.https_only_cb.setToolTip("Block all non-HTTPS connections")
        conn_layout.addWidget(self.https_only_cb)
        
        scroll_layout.addWidget(conn_group)
        
        # Privacy protection group
        privacy_group = QGroupBox("Privacy Protection")
        privacy_layout = QVBoxLayout(privacy_group)
        
        self.block_ads_cb = QCheckBox("Block advertisements")
        self.block_ads_cb.setToolTip("Block known ad domains and scripts")
        privacy_layout.addWidget(self.block_ads_cb)
        
        self.block_trackers_cb = QCheckBox("Block trackers")
        self.block_trackers_cb.setToolTip("Block analytics and tracking scripts")
        privacy_layout.addWidget(self.block_trackers_cb)
        
        self.strict_privacy_cb = QCheckBox("Strict privacy mode")
        self.strict_privacy_cb.setToolTip("Enable additional privacy protections")
        privacy_layout.addWidget(self.strict_privacy_cb)
        
        scroll_layout.addWidget(privacy_group)
        
        # Paywall bypass group
        paywall_group = QGroupBox("Content Access")
        paywall_layout = QVBoxLayout(paywall_group)
        
        self.paywall_bypass_cb = QCheckBox("Enable paywall bypass")
        self.paywall_bypass_cb.setToolTip("Attempt to bypass subscription paywalls")
        paywall_layout.addWidget(self.paywall_bypass_cb)
        
        scroll_layout.addWidget(paywall_group)
        
        # Userscripts group
        userscripts_group = QGroupBox("Custom Scripts")
        userscripts_layout = QVBoxLayout(userscripts_group)
        
        self.userscripts_enabled_cb = QCheckBox("Enable userscripts")
        self.userscripts_enabled_cb.setToolTip("Allow custom JavaScript injection on pages")
        userscripts_layout.addWidget(self.userscripts_enabled_cb)
        
        scroll_layout.addWidget(userscripts_group)
        
        # Status information
        status_group = QGroupBox("Current Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("Security settings applied")
        self.status_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.status_label)
        
        scroll_layout.addWidget(status_group)
        
        # Buttons at the bottom
        buttons_layout = QHBoxLayout()
        
        self.apply_btn = QPushButton("Apply Settings")
        self.apply_btn.setDefault(True)
        
        self.reset_btn = QPushButton("Reset to Defaults")
        
        buttons_layout.addWidget(self.apply_btn)
        buttons_layout.addWidget(self.reset_btn)
        
        scroll_layout.addLayout(buttons_layout)
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        # Connect signals
        self.setup_connections()
        
    def setup_connections(self):
        """Set up signal connections."""
        self.apply_btn.clicked.connect(self.apply_settings)
        self.reset_btn.clicked.connect(self.reset_settings)
        
        # Connect checkboxes to immediate application if desired
        # For now, we'll use apply button for bulk changes
        
    def load_settings(self):
        """Load current settings from security manager."""
        settings = self.security_manager.get_settings()
        
        self.https_only_cb.setChecked(settings['https_only'])
        self.block_ads_cb.setChecked(settings['block_ads'])
        self.block_trackers_cb.setChecked(settings['block_trackers'])
        self.strict_privacy_cb.setChecked(settings['strict_privacy'])
        
        # These would need to be connected to other managers
        self.paywall_bypass_cb.setChecked(True)  # Default enabled
        self.userscripts_enabled_cb.setChecked(True)  # Default enabled
        
    def apply_settings(self):
        """Apply the current settings to the security manager."""
        self.security_manager.set_https_only(self.https_only_cb.isChecked())
        self.security_manager.set_block_ads(self.block_ads_cb.isChecked())
        self.security_manager.set_block_trackers(self.block_trackers_cb.isChecked())
        self.security_manager.set_strict_privacy(self.strict_privacy_cb.isChecked())
        
        # Emit signal to notify other components
        self.settings_changed.emit()
        
        self.status_label.setText("Settings applied successfully")
        
    def reset_settings(self):
        """Reset settings to default values."""
        self.https_only_cb.setChecked(False)
        self.block_ads_cb.setChecked(True)
        self.block_trackers_cb.setChecked(True)
        self.strict_privacy_cb.setChecked(False)
        self.paywall_bypass_cb.setChecked(True)
        self.userscripts_enabled_cb.setChecked(True)
        
        self.apply_settings()
        self.status_label.setText("Settings reset to defaults")
        
    def get_settings(self):
        """Get current settings from the panel."""
        return {
            'https_only': self.https_only_cb.isChecked(),
            'block_ads': self.block_ads_cb.isChecked(),
            'block_trackers': self.block_trackers_cb.isChecked(),
            'strict_privacy': self.strict_privacy_cb.isChecked(),
            'paywall_bypass': self.paywall_bypass_cb.isChecked(),
            'userscripts_enabled': self.userscripts_enabled_cb.isChecked()
        }