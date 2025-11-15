"""
Smart Behavior-Based Continuous Authentication System

A comprehensive security system that continuously authenticates users based on 
behavioral biometrics while integrating advanced security mechanisms.

Features:
- Behavioral Biometrics: Keystroke dynamics, mouse patterns
- Security Layer: Session integrity, encryption, device fingerprinting  
- Anomaly Detection: Real-time scoring with adaptive thresholds
- Risk-Based Authentication: Multi-factor authentication triggers
- Privacy Protection: Data encryption, differential privacy
"""

from . import core, security, ml, auth, device, service, ui

__all__ = [
    'core',
    'security', 
    'ml',
    'auth',
    'device',
    'service',
    'ui'
]

__version__ = '1.0.0'
__author__ = 'Behavior Auth Team'
__description__ = 'Smart Behavior-Based Continuous Authentication System'