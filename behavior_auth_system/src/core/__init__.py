"""
Core behavioral biometrics collection module.

This module provides the fundamental components for capturing and analyzing
behavioral biometric data including keystroke dynamics and mouse patterns.
"""

from .keystroke_collector import KeystrokeCollector, KeystrokeEvent, BiometricFeatures
from .mouse_collector import MouseCollector, MouseEvent
from .behavioral_manager import BehavioralDataManager, BehaviorSession
from .advanced_activity_monitor import AdvancedActivityMonitor, BaselineProfile, ActivityEvent
from .behavioral_analyzers import InputFloodDetector, TypingRhythmAnalyzer, MultitaskingAnalyzer, BehaviorPatternMatcher

__all__ = [
    'KeystrokeCollector',
    'MouseCollector', 
    'BehavioralDataManager',
    'KeystrokeEvent',
    'MouseEvent',
    'BiometricFeatures',
    'BehaviorSession',
    'AdvancedActivityMonitor',
    'BaselineProfile',
    'ActivityEvent',
    'InputFloodDetector',
    'TypingRhythmAnalyzer',
    'MultitaskingAnalyzer',
    'BehaviorPatternMatcher'
]

__version__ = '1.0.0'