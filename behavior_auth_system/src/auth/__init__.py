"""
Authentication module for behavioral biometric authentication system.

Provides adaptive response management, challenge handling, and continuous
authentication coordination for the behavioral authentication system.
"""

from .adaptive_response import (
    AdaptiveResponseManager,
    ResponseEngine,
    ChallengeManager,
    SecurityAlert,
    AuthChallenge,
    ResponseAction,
    AlertSeverity
)
from .auth_manager import AuthenticationManager, AuthenticationResult

__all__ = [
    'AdaptiveResponseManager',
    'ResponseEngine',
    'ChallengeManager',
    'AuthenticationManager',
    'SecurityAlert',
    'AuthChallenge',
    'AuthenticationResult',
    'ResponseAction',
    'AlertSeverity'
]

__version__ = '1.0.0'