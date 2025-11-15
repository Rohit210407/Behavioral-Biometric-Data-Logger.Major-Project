"""
User Interface module for Behavioral Authentication System.

Provides configuration management, graphical dashboard, and administrative
interfaces for the behavioral authentication system.
"""

from .config_manager import ConfigManager, ConfigEditor, ConfigValidationResult
# from .dashboard import BehaviorAuthGUI, SettingsDialog  # Commented out due to import issues

__all__ = [
    'ConfigManager',
    'ConfigEditor',
    'ConfigValidationResult',
    # 'BehaviorAuthGUI',
    # 'SettingsDialog'
]

__version__ = '1.0.0'