"""
Background Service module for continuous behavioral authentication monitoring.

Provides Windows service/daemon functionality for continuous operation,
client APIs, and service management capabilities.
"""

from .main import BehaviorAuthService, ServiceManager
from .client import BehaviorAuthClient, SimpleBehaviorAuth

__all__ = [
    'BehaviorAuthService',
    'ServiceManager',
    'BehaviorAuthClient', 
    'SimpleBehaviorAuth'
]

__version__ = '1.0.0'