"""
Behavioral Data Manager - Coordinates keystroke and mouse data collection.
Provides unified interface for behavioral biometric data capture.
"""

import time
import threading
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import queue

from .keystroke_collector import KeystrokeCollector, BiometricFeatures
from .mouse_collector import MouseCollector
from .advanced_activity_monitor import AdvancedActivityMonitor, BaselineProfile
from .behavioral_analyzers import BehaviorPatternMatcher

@dataclass
class BehaviorSession:
    """Represents a behavioral authentication session."""
    session_id: str
    user_id: str
    start_time: float
    features_collected: int = 0
    is_active: bool = True
    confidence_score: float = 0.0

class BehavioralDataManager:
    """Main manager for coordinating behavioral biometric data collection."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize collectors
        self.keystroke_collector = KeystrokeCollector(config.get('biometrics', {}).get('keystroke', {}))
        self.mouse_collector = MouseCollector(config.get('biometrics', {}).get('mouse', {}))
        
        # Initialize advanced activity monitor for 15-minute baseline
        self.activity_monitor = AdvancedActivityMonitor(config)
        self.pattern_matcher = BehaviorPatternMatcher()
        
        # Baseline training state
        self.baseline_mode = True
        self.baseline_complete = False
        self.user_baseline_profile = None
        
        # Session management
        self.current_session: Optional[BehaviorSession] = None
        self.feature_callbacks: List[Callable[[BiometricFeatures], None]] = []
        
        # Data processing
        self.feature_queue = queue.Queue(maxsize=100)
        self.processing_thread = None
        self.is_running = False
        
        # Feature extraction settings
        self.feature_window = config.get('ml', {}).get('features', {}).get('window_size', 100)
        self.collection_interval = config.get('service', {}).get('monitoring', {}).get('interval_seconds', 1)
        
    def start_session(self, user_id: str, session_id: str) -> bool:
        """Start a new behavioral authentication session."""
        try:
            if self.current_session and self.current_session.is_active:
                self.logger.warning(f"Session already active: {self.current_session.session_id}")
                return False
                
            self.current_session = BehaviorSession(
                session_id=session_id,
                user_id=user_id,
                start_time=time.time()
            )
            
            # Start data collection
            self.is_running = True
            self.keystroke_collector.start_collection()
            self.mouse_collector.start_collection()
            
            # Start 15-minute baseline training
            if not self.activity_monitor.start_baseline_collection(user_id):
                self.logger.error("Failed to start baseline collection")
                return False
                
            self.logger.info(f"Started 15-minute baseline training for user: {user_id}")
            
            # Start feature processing thread
            self.processing_thread = threading.Thread(target=self._process_features_loop, daemon=True)
            self.processing_thread.start()
            
            self.logger.info(f"Started behavioral session: {session_id} for user: {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start session: {e}")
            return False
            
    def stop_session(self) -> bool:
        """Stop the current behavioral session."""
        try:
            if not self.current_session:
                self.logger.warning("No active session to stop")
                return False
                
            # Stop data collection
            self.is_running = False
            self.keystroke_collector.stop_collection()
            self.mouse_collector.stop_collection()
            
            # Mark session as inactive
            if self.current_session:
                self.current_session.is_active = False
                
            self.logger.info(f"Stopped behavioral session: {self.current_session.session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop session: {e}")
            return False
            
    def add_feature_callback(self, callback: Callable[[BiometricFeatures], None]) -> None:
        """Add callback function to receive extracted features."""
        self.feature_callbacks.append(callback)
        
    def get_current_features(self) -> Optional[BiometricFeatures]:
        """Get the most recent behavioral features with enhanced analysis."""
        if not self.current_session or not self.current_session.is_active:
            return None
            
        # Get basic features from collectors
        keystroke_features = self.keystroke_collector.get_features()
        mouse_features = self.mouse_collector.get_features()
        
        # Get advanced activity analysis
        if self.activity_monitor.is_baseline_complete:
            # Real-time imposter detection
            deviation_score = self.activity_monitor.get_real_time_deviation_score()
            baseline_status = "monitoring"
        else:
            # Still in baseline training
            progress = self.activity_monitor._get_baseline_progress()
            deviation_score = 0.5  # Neutral during training
            baseline_status = f"training_{progress:.1%}"
        
        # Merge features
        combined_features = BiometricFeatures(
            user_id=self.current_session.user_id,
            session_id=self.current_session.session_id,
            timestamp=time.time()
        )
        
        if keystroke_features:
            combined_features.keystroke_features = keystroke_features.keystroke_features
            
        if mouse_features:
            combined_features.mouse_features = mouse_features.mouse_features
            
        # Add enhanced behavioral analysis
        combined_features.keystroke_features['deviation_score'] = deviation_score
        combined_features.keystroke_features['imposter_risk'] = self._calculate_imposter_risk(deviation_score)
        
        # Calculate enhanced confidence score
        data_quality = 0.0
        if combined_features.keystroke_features:
            data_quality += 0.4
        if combined_features.mouse_features:
            data_quality += 0.3
        if self.activity_monitor.is_baseline_complete:
            data_quality += 0.3
            
        # Adjust confidence based on deviation
        base_confidence = data_quality
        deviation_penalty = deviation_score * 0.5  # Penalty for high deviation
        combined_features.confidence_score = max(0.0, base_confidence - deviation_penalty)
        
        return combined_features
        
    def _calculate_imposter_risk(self, deviation_score: float) -> float:
        """Calculate imposter risk based on deviation score."""
        # Convert deviation score to risk level
        if deviation_score < 0.2:
            return 0.1  # Low risk
        elif deviation_score < 0.5:
            return 0.3  # Medium risk
        elif deviation_score < 0.8:
            return 0.7  # High risk
        else:
            return 0.9  # Very high risk
        
    def _process_features_loop(self) -> None:
        """Background thread for continuous feature processing."""
        self.logger.info("Started feature processing loop")
        
        while self.is_running:
            try:
                time.sleep(self.collection_interval)
                
                if not self.current_session or not self.current_session.is_active:
                    continue
                    
                # Extract current features
                features = self.get_current_features()
                if features:
                    # Update session stats
                    self.current_session.features_collected += 1
                    self.current_session.confidence_score = features.confidence_score
                    
                    # Send to callbacks
                    for callback in self.feature_callbacks:
                        try:
                            callback(features)
                        except Exception as e:
                            self.logger.error(f"Feature callback error: {e}")
                            
                    # Add to processing queue
                    try:
                        self.feature_queue.put_nowait(features)
                    except queue.Full:
                        self.logger.warning("Feature queue full, dropping oldest data")
                        try:
                            self.feature_queue.get_nowait()  # Remove oldest
                            self.feature_queue.put_nowait(features)  # Add new
                        except queue.Empty:
                            pass
                            
            except Exception as e:
                self.logger.error(f"Error in feature processing loop: {e}")
                
        self.logger.info("Feature processing loop stopped")
        
    def get_session_stats(self) -> Optional[Dict[str, Any]]:
        """Get statistics about the current session."""
        if not self.current_session:
            return None
            
        duration = time.time() - self.current_session.start_time
        
        return {
            'session_id': self.current_session.session_id,
            'user_id': self.current_session.user_id,
            'duration_seconds': duration,
            'features_collected': self.current_session.features_collected,
            'is_active': self.current_session.is_active,
            'confidence_score': self.current_session.confidence_score,
            'collection_rate': self.current_session.features_collected / duration if duration > 0 else 0
        }
        
    def export_session_data(self) -> List[Dict[str, Any]]:
        """Export collected feature data for analysis."""
        features_list = []
        
        # Drain the feature queue
        while not self.feature_queue.empty():
            try:
                features = self.feature_queue.get_nowait()
                features_list.append(features.to_dict())
            except queue.Empty:
                break
                
        return features_list
        
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure cleanup."""
        self.stop_session()