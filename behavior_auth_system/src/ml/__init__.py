"""
Machine Learning module for behavioral biometric analysis.

Provides behavior modeling, anomaly detection, and feature extraction
for continuous authentication based on behavioral patterns.
"""

from .behavior_models import (
    BaseModel,
    BehaviorClassifier,
    AnomalyDetector,
    AdaptiveThresholds,
    MLManager,
    ModelMetrics
)
from .feature_extraction import FeatureExtractor, FeatureVector

__all__ = [
    'BaseModel',
    'BehaviorClassifier', 
    'AnomalyDetector',
    'AdaptiveThresholds',
    'MLManager',
    'ModelMetrics',
    'FeatureExtractor',
    'FeatureVector'
]

__version__ = '1.0.0'