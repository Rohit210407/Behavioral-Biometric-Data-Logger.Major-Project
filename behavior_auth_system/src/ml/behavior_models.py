"""
Machine Learning module for behavioral biometric analysis and anomaly detection.
Implements user behavior modeling and real-time anomaly scoring.
"""

import numpy as np
import pandas as pd
import pickle
import logging
import time
import os
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

try:
    from sklearn.ensemble import RandomForestClassifier, IsolationForest
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import classification_report, confusion_matrix
    import joblib
except ImportError:
    logging.warning("scikit-learn not available. ML features will be limited.")

@dataclass
class ModelMetrics:
    """Container for model performance metrics."""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    training_samples: int
    model_version: str
    created_at: float

class BaseModel(ABC):
    """Abstract base class for behavioral models."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = []
        
    @abstractmethod
    def train(self, features: List[Dict[str, Any]], labels: Optional[List[int]] = None) -> bool:
        """Train the model with provided features."""
        pass
        
    @abstractmethod
    def predict(self, features: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Make prediction on new features."""
        pass
        
    def save_model(self, filepath: str) -> bool:
        """Save trained model to file."""
        try:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'is_trained': self.is_trained,
                'config': self.config,
                'saved_at': time.time()
            }
            joblib.dump(model_data, filepath)
            self.logger.info(f"Model saved to {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save model: {e}")
            return False
            
    def load_model(self, filepath: str) -> bool:
        """Load trained model from file."""
        try:
            if not os.path.exists(filepath):
                self.logger.warning(f"Model file not found: {filepath}")
                return False
                
            model_data = joblib.load(filepath)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']
            self.is_trained = model_data['is_trained']
            
            self.logger.info(f"Model loaded from {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            return False

class BehaviorClassifier(BaseModel):
    """Classifies user behavior patterns for authentication."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model = RandomForestClassifier(
            n_estimators=config.get('n_estimators', 100),
            max_depth=config.get('max_depth', None),
            random_state=42
        )
        
    def train(self, features: List[Dict[str, Any]], labels: List[int]) -> bool:
        """Train behavior classification model."""
        try:
            if len(features) < self.config.get('min_samples', 50):
                self.logger.warning(f"Insufficient training samples: {len(features)}")
                return False
                
            # Convert features to DataFrame
            df = pd.DataFrame(features)
            
            # Handle missing values
            df = df.fillna(df.mean())
            
            # Store feature names
            self.feature_names = list(df.columns)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(df.values)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, labels, test_size=0.2, random_state=42, stratify=labels
            )
            
            # Train model
            self.model.fit(X_train, y_train)
            
            # Evaluate
            train_score = self.model.score(X_train, y_train)
            test_score = self.model.score(X_test, y_test)
            
            self.logger.info(f"Model trained - Train accuracy: {train_score:.3f}, Test accuracy: {test_score:.3f}")
            
            self.is_trained = True
            return True
            
        except Exception as e:
            self.logger.error(f"Training failed: {e}")
            return False
            
    def predict(self, features: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Predict user authenticity probability."""
        if not self.is_trained:
            return 0.0, {'error': 'Model not trained'}
            
        try:
            # Convert to DataFrame and align with training features
            df = pd.DataFrame([features])
            df = df.reindex(columns=self.feature_names, fill_value=0)
            
            # Scale features
            X_scaled = self.scaler.transform(df.values)
            
            # Get prediction probability
            probabilities = self.model.predict_proba(X_scaled)[0]
            confidence = float(probabilities[1]) if len(probabilities) > 1 else float(probabilities[0])
            
            # Get feature importance for explanation
            feature_importance = dict(zip(
                self.feature_names,
                self.model.feature_importances_
            ))
            
            return confidence, {
                'prediction': 'authentic' if confidence > 0.5 else 'anomalous',
                'feature_importance': feature_importance,
                'model_type': 'RandomForest'
            }
            
        except Exception as e:
            self.logger.error(f"Prediction failed: {e}")
            return 0.0, {'error': str(e)}

class AnomalyDetector(BaseModel):
    """Detects anomalous behavior patterns using unsupervised learning."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.contamination = config.get('contamination', 0.1)
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_estimators=100
        )
        
    def train(self, features: List[Dict[str, Any]], labels: Optional[List[int]] = None) -> bool:
        """Train anomaly detection model (unsupervised)."""
        try:
            if len(features) < self.config.get('min_samples', 100):
                self.logger.warning(f"Insufficient training samples: {len(features)}")
                return False
                
            # Convert features to DataFrame
            df = pd.DataFrame(features)
            df = df.fillna(df.mean())
            
            self.feature_names = list(df.columns)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(df.values)
            
            # Train model
            self.model.fit(X_scaled)
            
            # Calculate baseline scores
            scores = self.model.decision_function(X_scaled)
            self.threshold = np.percentile(scores, self.contamination * 100)
            
            self.logger.info(f"Anomaly detector trained with {len(features)} samples")
            self.logger.info(f"Anomaly threshold: {self.threshold:.3f}")
            
            self.is_trained = True
            return True
            
        except Exception as e:
            self.logger.error(f"Anomaly detector training failed: {e}")
            return False
            
    def predict(self, features: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Predict anomaly score (higher = more anomalous)."""
        if not self.is_trained:
            return 1.0, {'error': 'Model not trained'}
            
        try:
            # Convert to DataFrame and align with training features
            df = pd.DataFrame([features])
            df = df.reindex(columns=self.feature_names, fill_value=0)
            
            # Scale features
            X_scaled = self.scaler.transform(df.values)
            
            # Get anomaly score
            score = self.model.decision_function(X_scaled)[0]
            
            # Normalize score to 0-1 range (1 = most anomalous)
            normalized_score = max(0, (self.threshold - score) / abs(self.threshold))
            normalized_score = min(1.0, normalized_score)
            
            # Determine if anomalous
            is_anomaly = score < self.threshold
            
            return normalized_score, {
                'is_anomaly': is_anomaly,
                'raw_score': float(score),
                'threshold': self.threshold,
                'model_type': 'IsolationForest'
            }
            
        except Exception as e:
            self.logger.error(f"Anomaly prediction failed: {e}")
            return 1.0, {'error': str(e)}

class AdaptiveThresholds:
    """Manages adaptive thresholds for different contexts."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.thresholds = {
            'high_confidence': config.get('authentication', {}).get('confidence_levels', {}).get('high', 0.9),
            'medium_confidence': config.get('authentication', {}).get('confidence_levels', {}).get('medium', 0.7),
            'low_confidence': config.get('authentication', {}).get('confidence_levels', {}).get('low', 0.5)
        }
        self.context_adjustments = {}
        self.learning_rate = 0.1
        
    def adjust_threshold(self, context: str, feedback: str, current_score: float) -> None:
        """Adjust threshold based on feedback."""
        if context not in self.context_adjustments:
            self.context_adjustments[context] = 0.0
            
        # Adjust based on feedback
        if feedback == 'false_positive':  # Legitimate user flagged as anomalous
            self.context_adjustments[context] -= self.learning_rate * current_score
        elif feedback == 'false_negative':  # Attacker passed as legitimate
            self.context_adjustments[context] += self.learning_rate * (1 - current_score)
            
        # Keep adjustments within reasonable bounds
        self.context_adjustments[context] = max(-0.3, min(0.3, self.context_adjustments[context]))
        
    def get_threshold(self, level: str, context: str = 'default') -> float:
        """Get adjusted threshold for given level and context."""
        base_threshold = self.thresholds.get(level, 0.7)
        adjustment = self.context_adjustments.get(context, 0.0)
        
        # Apply adjustment
        adjusted_threshold = base_threshold + adjustment
        
        # Ensure threshold stays within valid range
        return max(0.1, min(0.95, adjusted_threshold))

class MLManager:
    """Main manager for machine learning components."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize models
        self.behavior_classifier = BehaviorClassifier(config.get('ml', {}))
        self.anomaly_detector = AnomalyDetector(config.get('ml', {}))
        self.adaptive_thresholds = AdaptiveThresholds(config)
        
        # Training data storage
        self.training_data = []
        self.model_path = config.get('ml', {}).get('model_path', 'saved_models/')
        
        # Auto-retrain settings
        self.retrain_interval = config.get('ml', {}).get('training', {}).get('retrain_interval_hours', 24) * 3600
        self.last_training = 0
        
    def add_training_sample(self, features: Dict[str, Any], label: int) -> None:
        """Add new training sample."""
        sample = {
            'features': features,
            'label': label,
            'timestamp': time.time()
        }
        self.training_data.append(sample)
        
        # Check if auto-retrain needed
        if self._should_retrain():
            self._retrain_models()
            
    def analyze_behavior(self, features: Dict[str, Any], context: str = 'default') -> Dict[str, Any]:
        """Analyze behavior using both classifier and anomaly detector."""
        # Get predictions from both models
        auth_confidence, auth_details = self.behavior_classifier.predict(features)
        anomaly_score, anomaly_details = self.anomaly_detector.predict(features)
        
        # Combine results
        combined_confidence = (auth_confidence + (1 - anomaly_score)) / 2
        
        # Get adaptive thresholds
        high_threshold = self.adaptive_thresholds.get_threshold('high_confidence', context)
        medium_threshold = self.adaptive_thresholds.get_threshold('medium_confidence', context)
        low_threshold = self.adaptive_thresholds.get_threshold('low_confidence', context)
        
        # Determine authentication decision
        if combined_confidence >= high_threshold:
            decision = 'continue'
            confidence_level = 'high'
        elif combined_confidence >= medium_threshold:
            decision = 'monitor'
            confidence_level = 'medium'
        elif combined_confidence >= low_threshold:
            decision = 'challenge'
            confidence_level = 'low'
        else:
            decision = 'logout'
            confidence_level = 'very_low'
            
        return {
            'decision': decision,
            'confidence_level': confidence_level,
            'combined_confidence': combined_confidence,
            'auth_confidence': auth_confidence,
            'anomaly_score': anomaly_score,
            'thresholds': {
                'high': high_threshold,
                'medium': medium_threshold,
                'low': low_threshold
            },
            'details': {
                'classifier': auth_details,
                'anomaly_detector': anomaly_details
            }
        }
        
    def _should_retrain(self) -> bool:
        """Check if models should be retrained."""
        if not self.behavior_classifier.is_trained or not self.anomaly_detector.is_trained:
            return len(self.training_data) >= self.config.get('ml', {}).get('training', {}).get('min_samples', 100)
            
        time_since_training = time.time() - self.last_training
        return time_since_training >= self.retrain_interval and len(self.training_data) > 0
        
    def _retrain_models(self) -> bool:
        """Retrain models with accumulated data."""
        try:
            if len(self.training_data) < 50:
                return False
                
            # Prepare training data
            features = [sample['features'] for sample in self.training_data]
            labels = [sample['label'] for sample in self.training_data]
            
            # Train models
            classifier_success = self.behavior_classifier.train(features, labels)
            anomaly_success = self.anomaly_detector.train(features)
            
            if classifier_success and anomaly_success:
                self.last_training = time.time()
                self.logger.info(f"Models retrained with {len(self.training_data)} samples")
                
                # Save models
                self._save_models()
                
                # Clear training data to prevent memory growth
                self.training_data = self.training_data[-1000:]  # Keep last 1000 samples
                
                return True
                
        except Exception as e:
            self.logger.error(f"Model retraining failed: {e}")
            
        return False
        
    def _save_models(self) -> None:
        """Save trained models to disk."""
        os.makedirs(self.model_path, exist_ok=True)
        
        classifier_path = os.path.join(self.model_path, 'behavior_classifier.pkl')
        anomaly_path = os.path.join(self.model_path, 'anomaly_detector.pkl')
        
        self.behavior_classifier.save_model(classifier_path)
        self.anomaly_detector.save_model(anomaly_path)
        
    def load_models(self) -> bool:
        """Load pre-trained models from disk."""
        classifier_path = os.path.join(self.model_path, 'behavior_classifier.pkl')
        anomaly_path = os.path.join(self.model_path, 'anomaly_detector.pkl')
        
        classifier_loaded = self.behavior_classifier.load_model(classifier_path)
        anomaly_loaded = self.anomaly_detector.load_model(anomaly_path)
        
        return classifier_loaded and anomaly_loaded