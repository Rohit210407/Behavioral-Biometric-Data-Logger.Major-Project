"""
Feature extraction and preprocessing for behavioral biometric data.
Converts raw behavioral data into ML-ready feature vectors.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass

@dataclass
class FeatureVector:
    """Container for extracted feature vector."""
    features: Dict[str, float]
    metadata: Dict[str, Any]
    timestamp: float
    user_id: str
    session_id: str

class FeatureExtractor:
    """Extracts ML features from behavioral biometric data."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.window_size = config.get('ml', {}).get('features', {}).get('window_size', 100)
        self.overlap = config.get('ml', {}).get('features', {}).get('overlap', 0.5)
        
    def extract_keystroke_features(self, keystroke_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract features from keystroke dynamics."""
        features = {}
        
        # Direct timing features
        if 'dwell_mean' in keystroke_data:
            features['ks_dwell_mean'] = keystroke_data['dwell_mean']
            features['ks_dwell_std'] = keystroke_data.get('dwell_std', 0)
            features['ks_dwell_range'] = keystroke_data.get('dwell_max', 0) - keystroke_data.get('dwell_min', 0)
            
        if 'flight_mean' in keystroke_data:
            features['ks_flight_mean'] = keystroke_data['flight_mean']
            features['ks_flight_std'] = keystroke_data.get('flight_std', 0)
            features['ks_flight_range'] = keystroke_data.get('flight_max', 0) - keystroke_data.get('flight_min', 0)
            
        # Rhythm and consistency features
        if 'rhythm_consistency' in keystroke_data:
            features['ks_rhythm_consistency'] = keystroke_data['rhythm_consistency']
            
        if 'typing_speed' in keystroke_data:
            features['ks_typing_speed'] = keystroke_data['typing_speed']
            
        # Derived features
        if 'dwell_mean' in keystroke_data and 'flight_mean' in keystroke_data:
            dwell_mean = keystroke_data['dwell_mean']
            flight_mean = keystroke_data['flight_mean']
            
            # Ratio features
            if flight_mean > 0:
                features['ks_dwell_flight_ratio'] = dwell_mean / flight_mean
            else:
                features['ks_dwell_flight_ratio'] = 0
                
            # Total keystroke time
            features['ks_total_time'] = dwell_mean + flight_mean
            
        # Variability features
        if 'dwell_std' in keystroke_data and 'dwell_mean' in keystroke_data:
            dwell_mean = keystroke_data['dwell_mean']
            if dwell_mean > 0:
                features['ks_dwell_cv'] = keystroke_data['dwell_std'] / dwell_mean
            else:
                features['ks_dwell_cv'] = 0
                
        return features
        
    def extract_mouse_features(self, mouse_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract features from mouse dynamics."""
        features = {}
        
        # Velocity features
        if 'velocity_mean' in mouse_data:
            features['mouse_velocity_mean'] = mouse_data['velocity_mean']
            features['mouse_velocity_std'] = mouse_data.get('velocity_std', 0)
            features['mouse_velocity_max'] = mouse_data.get('velocity_max', 0)
            
        # Acceleration features
        if 'acceleration_mean' in mouse_data:
            features['mouse_accel_mean'] = mouse_data['acceleration_mean']
            features['mouse_accel_std'] = mouse_data.get('acceleration_std', 0)
            
        # Click pattern features
        if 'click_interval_mean' in mouse_data:
            features['mouse_click_interval'] = mouse_data['click_interval_mean']
            
        # Movement smoothness
        if 'movement_smoothness' in mouse_data:
            features['mouse_smoothness'] = mouse_data['movement_smoothness']
            
        # Derived movement features
        if 'velocity_mean' in mouse_data and 'velocity_std' in mouse_data:
            vel_mean = mouse_data['velocity_mean']
            vel_std = mouse_data['velocity_std']
            
            # Coefficient of variation for velocity
            if vel_mean > 0:
                features['mouse_velocity_cv'] = vel_std / vel_mean
            else:
                features['mouse_velocity_cv'] = 0
                
        # Jerk features (rate of change of acceleration)
        if 'jerk_mean' in mouse_data:
            features['mouse_jerk_mean'] = mouse_data['jerk_mean']
            features['mouse_jerk_std'] = mouse_data.get('jerk_std', 0)
            
        return features
        
    def extract_temporal_features(self, data: Dict[str, Any], session_duration: float) -> Dict[str, float]:
        """Extract time-based contextual features."""
        features = {}
        
        # Session context
        features['session_duration'] = session_duration
        features['session_duration_log'] = np.log1p(session_duration)
        
        # Time of day features (if timestamp available)
        if 'timestamp' in data:
            import datetime
            dt = datetime.datetime.fromtimestamp(data['timestamp'])
            
            features['hour_of_day'] = dt.hour
            features['day_of_week'] = dt.weekday()
            features['is_weekend'] = 1.0 if dt.weekday() >= 5 else 0.0
            
            # Cyclical encoding for time features
            features['hour_sin'] = np.sin(2 * np.pi * dt.hour / 24)
            features['hour_cos'] = np.cos(2 * np.pi * dt.hour / 24)
            features['dow_sin'] = np.sin(2 * np.pi * dt.weekday() / 7)
            features['dow_cos'] = np.cos(2 * np.pi * dt.weekday() / 7)
            
        # Activity level features
        if 'features_collected' in data:
            features['activity_rate'] = data['features_collected'] / max(session_duration, 1)
            
        return features
        
    def extract_statistical_features(self, feature_history: List[Dict[str, float]]) -> Dict[str, float]:
        """Extract statistical features from feature history."""
        if not feature_history:
            return {}
            
        features = {}
        
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(feature_history)
        
        # For each feature, calculate statistical measures
        for column in df.columns:
            if df[column].dtype in ['float64', 'int64']:
                prefix = f"hist_{column}"
                
                # Basic statistics
                features[f"{prefix}_mean"] = df[column].mean()
                features[f"{prefix}_std"] = df[column].std()
                features[f"{prefix}_median"] = df[column].median()
                features[f"{prefix}_min"] = df[column].min()
                features[f"{prefix}_max"] = df[column].max()
                
                # Advanced statistics
                features[f"{prefix}_skew"] = df[column].skew()
                features[f"{prefix}_kurtosis"] = df[column].kurtosis()
                
                # Percentiles
                features[f"{prefix}_q25"] = df[column].quantile(0.25)
                features[f"{prefix}_q75"] = df[column].quantile(0.75)
                features[f"{prefix}_iqr"] = features[f"{prefix}_q75"] - features[f"{prefix}_q25"]
                
                # Trend features (if enough data points)
                if len(df) >= 10:
                    # Linear trend slope
                    x = np.arange(len(df))
                    slope = np.polyfit(x, df[column].values, 1)[0]
                    features[f"{prefix}_trend"] = slope
                    
        return features
        
    def combine_features(self, keystroke_features: Dict[str, float],
                        mouse_features: Dict[str, float],
                        temporal_features: Dict[str, float],
                        statistical_features: Dict[str, float]) -> Dict[str, float]:
        """Combine all feature types into a single feature vector."""
        combined = {}
        
        # Add all feature types
        combined.update(keystroke_features)
        combined.update(mouse_features)
        combined.update(temporal_features)
        combined.update(statistical_features)
        
        # Handle missing values
        for key, value in combined.items():
            if pd.isna(value) or np.isinf(value):
                combined[key] = 0.0
                
        return combined
        
    def extract_features(self, behavioral_data: Dict[str, Any],
                        session_duration: float = 0,
                        feature_history: Optional[List[Dict[str, float]]] = None) -> FeatureVector:
        """Extract complete feature vector from behavioral data."""
        try:
            # Extract features from each modality
            keystroke_features = {}
            if 'keystroke_features' in behavioral_data:
                keystroke_features = self.extract_keystroke_features(
                    behavioral_data['keystroke_features']
                )
                
            mouse_features = {}
            if 'mouse_features' in behavioral_data:
                mouse_features = self.extract_mouse_features(
                    behavioral_data['mouse_features']
                )
                
            # Extract temporal features
            temporal_features = self.extract_temporal_features(
                behavioral_data, session_duration
            )
            
            # Extract statistical features from history
            statistical_features = {}
            if feature_history:
                statistical_features = self.extract_statistical_features(feature_history)
                
            # Combine all features
            combined_features = self.combine_features(
                keystroke_features, mouse_features, temporal_features, statistical_features
            )
            
            # Create feature vector
            feature_vector = FeatureVector(
                features=combined_features,
                metadata={
                    'keystroke_feature_count': len(keystroke_features),
                    'mouse_feature_count': len(mouse_features),
                    'temporal_feature_count': len(temporal_features),
                    'statistical_feature_count': len(statistical_features),
                    'total_feature_count': len(combined_features)
                },
                timestamp=behavioral_data.get('timestamp', 0),
                user_id=behavioral_data.get('user_id', ''),
                session_id=behavioral_data.get('session_id', '')
            )
            
            return feature_vector
            
        except Exception as e:
            self.logger.error(f"Feature extraction failed: {e}")
            # Return empty feature vector on error
            return FeatureVector(
                features={},
                metadata={'error': str(e)},
                timestamp=behavioral_data.get('timestamp', 0),
                user_id=behavioral_data.get('user_id', ''),
                session_id=behavioral_data.get('session_id', '')
            )
            
    def normalize_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """Apply feature normalization and scaling."""
        normalized = {}
        
        for key, value in features.items():
            # Apply bounds to prevent extreme values
            if 'velocity' in key or 'speed' in key:
                normalized[key] = min(max(value, 0), 10000)  # Cap velocity features
            elif 'time' in key or 'interval' in key:
                normalized[key] = min(max(value, 0), 5.0)  # Cap timing features at 5 seconds
            elif 'ratio' in key or 'cv' in key:
                normalized[key] = min(max(value, 0), 10.0)  # Cap ratio features
            else:
                normalized[key] = value
                
        return normalized