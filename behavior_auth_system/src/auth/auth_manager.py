"""
Authentication Manager - Coordinates behavioral authentication and security responses.
Main interface for the behavioral authentication system.
"""

import time
import logging
import threading
from typing import Dict, Any, Optional, Tuple, List, Callable
from dataclasses import dataclass

# Fix the imports to use relative imports
from .adaptive_response import AdaptiveResponseManager, ResponseAction
from ..core import BehavioralDataManager, BiometricFeatures
from ..security import SecurityManager
from ..ml import MLManager, FeatureExtractor

@dataclass
class AuthenticationResult:
    """Result of an authentication attempt."""
    success: bool
    confidence: float
    user_id: str
    session_id: str
    decision: str  # continue, monitor, challenge, logout
    message: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'success': self.success,
            'confidence': self.confidence,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'decision': self.decision,
            'message': self.message,
            'metadata': self.metadata
        }

class AuthenticationManager:
    """Main manager for behavioral authentication system."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize core components
        self.behavioral_manager = BehavioralDataManager(config)
        self.security_manager = SecurityManager(config)
        self.ml_manager = MLManager(config)
        self.feature_extractor = FeatureExtractor(config)
        self.response_manager = AdaptiveResponseManager(config)
        
        # Authentication state
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.feature_history: Dict[str, List[Dict[str, float]]] = {}
        
        # Callbacks
        self.auth_callbacks: List[Callable] = []
        
        # Performance monitoring
        self.auth_stats = {
            'total_authentications': 0,
            'successful_authentications': 0,
            'challenged_authentications': 0,
            'failed_authentications': 0,
            'average_confidence': 0.0
        }
        
    def start_authentication_session(self, user_id: str, device_fingerprint: Optional[str] = None,
                                   ip_address: Optional[str] = None) -> Optional[str]:
        """Start a new behavioral authentication session."""
        
        try:
            # Create secure session
            session_id = self.security_manager.create_secure_session(
                user_id, device_fingerprint, ip_address
            )
            
            if not session_id:
                self.logger.error(f"Failed to create secure session for user {user_id}")
                return None
                
            # Start behavioral data collection
            if not self.behavioral_manager.start_session(user_id, session_id):
                self.logger.error(f"Failed to start behavioral session for user {user_id}")
                self.security_manager.session_manager.invalidate_session(session_id)
                return None
                
            # Initialize session state
            self.active_sessions[session_id] = {
                'user_id': user_id,
                'start_time': time.time(),
                'last_authentication': time.time(),
                'authentication_count': 0,
                'device_fingerprint': device_fingerprint,
                'ip_address': ip_address
            }
            
            # Initialize feature history
            self.feature_history[session_id] = []
            
            # Register for behavioral data callbacks
            self.behavioral_manager.add_feature_callback(
                lambda features: self._process_behavioral_features(features)
            )
            
            self.logger.info(f"Started authentication session {session_id} for user {user_id}")
            return session_id
            
        except Exception as e:
            self.logger.error(f"Failed to start authentication session: {e}")
            return None
            
    def authenticate_continuously(self, session_id: str, 
                                context: Optional[Dict[str, Any]] = None) -> AuthenticationResult:
        """Perform continuous behavioral authentication."""
        
        try:
            # Validate session
            session_valid, session_info = self.security_manager.validate_session(
                session_id,
                context.get('device_fingerprint') if context else None,
                context.get('ip_address') if context else None
            )
            
            if not session_valid or session_info is None:
                return AuthenticationResult(
                    success=False,
                    confidence=0.0,
                    user_id='unknown',
                    session_id=session_id,
                    decision='logout',
                    message='Session validation failed',
                    metadata={'reason': 'invalid_session'}
                )
                
            user_id = session_info['user_id']
            
            # Get current behavioral features
            behavioral_features = self.behavioral_manager.get_current_features()
            
            if not behavioral_features:
                return AuthenticationResult(
                    success=True,
                    confidence=0.5,
                    user_id=user_id,
                    session_id=session_id,
                    decision='monitor',
                    message='Insufficient behavioral data',
                    metadata={'reason': 'no_behavioral_data'}
                )
                
            # Extract ML features
            session_duration = time.time() - self.active_sessions[session_id]['start_time']
            feature_vector = self.feature_extractor.extract_features(
                behavioral_features.to_dict(),
                session_duration,
                self.feature_history.get(session_id, [])
            )
            
            # Perform ML analysis
            ml_analysis = self.ml_manager.analyze_behavior(
                feature_vector.features,
                context.get('context', 'default') if context else 'default'
            )
            
            # Create security context
            security_context = {
                'user_id': user_id,
                'session_id': session_id,
                'device_fingerprint': context.get('device_fingerprint') if context else None,
                'ip_address': context.get('ip_address') if context else None,
                'session_age': session_duration,
                'requires_additional_auth': session_info.get('requires_additional_auth', False) if session_info else False
            }
            
            # Process through adaptive response system
            response_result = self.response_manager.process_behavioral_analysis(
                ml_analysis, security_context
            )
            
            # Update session state
            self._update_session_state(session_id, feature_vector.features, ml_analysis)
            
            # Update authentication statistics
            self._update_auth_stats(ml_analysis)
            
            # Create authentication result
            auth_result = AuthenticationResult(
                success=ml_analysis['decision'] in ['continue', 'monitor'],
                confidence=ml_analysis['combined_confidence'],
                user_id=user_id,
                session_id=session_id,
                decision=ml_analysis['decision'],
                message=self._get_decision_message(ml_analysis['decision']),
                metadata={
                    'ml_analysis': ml_analysis,
                    'response_result': response_result,
                    'security_context': security_context,
                    'feature_count': len(feature_vector.features)
                }
            )
            
            # Notify callbacks
            self._notify_auth_callbacks(auth_result)
            
            return auth_result
            
        except Exception as e:
            self.logger.error(f"Continuous authentication failed: {e}")
            return AuthenticationResult(
                success=False,
                confidence=0.0,
                user_id='unknown',
                session_id=session_id,
                decision='logout',
                message='Authentication system error',
                metadata={'error': str(e)}
            )
            
    def handle_challenge_response(self, challenge_id: str, 
                                response: Dict[str, Any]) -> Tuple[bool, str]:
        """Handle response to authentication challenge."""
        
        try:
            success, message = self.response_manager.challenge_manager.process_challenge_response(
                challenge_id, response
            )
            
            self.logger.info(f"Challenge {challenge_id} response: {message}")
            
            # Update statistics
            if success:
                self.auth_stats['successful_authentications'] += 1
            else:
                self.auth_stats['failed_authentications'] += 1
                
            return success, message
            
        except Exception as e:
            self.logger.error(f"Challenge response handling failed: {e}")
            return False, f"Challenge processing error: {e}"
            
    def end_session(self, session_id: str) -> bool:
        """End authentication session and cleanup."""
        
        try:
            # Stop behavioral data collection
            self.behavioral_manager.stop_session()
            
            # Invalidate security session
            self.security_manager.session_manager.invalidate_session(session_id)
            
            # Cleanup session state
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
                
            if session_id in self.feature_history:
                del self.feature_history[session_id]
                
            self.logger.info(f"Ended authentication session {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to end session {session_id}: {e}")
            return False
            
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session status and metrics."""
        
        if session_id not in self.active_sessions:
            return None
            
        session = self.active_sessions[session_id]
        behavioral_stats = self.behavioral_manager.get_session_stats()
        security_status = self.security_manager.get_security_status()
        response_status = self.response_manager.get_system_status()
        
        return {
            'session_id': session_id,
            'user_id': session['user_id'],
            'duration': time.time() - session['start_time'],
            'authentication_count': session['authentication_count'],
            'last_authentication': session['last_authentication'],
            'behavioral_stats': behavioral_stats,
            'security_status': security_status,
            'response_status': response_status,
            'is_active': True
        }
        
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get overall system performance metrics."""
        
        return {
            'authentication_stats': self.auth_stats,
            'active_sessions': len(self.active_sessions),
            'ml_models_trained': self.ml_manager.behavior_classifier.is_trained,
            'security_monitoring': self.security_manager.monitoring_active,
            'behavioral_collection': self.behavioral_manager.is_running
        }
        
    def add_authentication_callback(self, callback: Callable) -> None:
        """Add authentication callback."""
        self.auth_callbacks.append(callback)
        
    def _process_behavioral_features(self, features: BiometricFeatures) -> None:
        """Process incoming behavioral features."""
        
        try:
            # Add to ML training data (with appropriate labels)
            # This is a simplified example - in practice, labels would come from
            # validation mechanisms or user feedback
            if features.confidence_score > 0.8:
                label = 1  # Legitimate user
            else:
                label = 0  # Potential anomaly
                
            feature_vector = self.feature_extractor.extract_features(features.to_dict())
            self.ml_manager.add_training_sample(feature_vector.features, label)
            
        except Exception as e:
            self.logger.error(f"Failed to process behavioral features: {e}")
            
    def _update_session_state(self, session_id: str, features: Dict[str, float],
                            ml_analysis: Dict[str, Any]) -> None:
        """Update session state with new data."""
        
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session['last_authentication'] = time.time()
            session['authentication_count'] += 1
            
            # Update feature history
            if session_id in self.feature_history:
                self.feature_history[session_id].append(features)
                
                # Keep only recent history
                max_history = 100
                if len(self.feature_history[session_id]) > max_history:
                    self.feature_history[session_id] = self.feature_history[session_id][-max_history:]
                    
    def _update_auth_stats(self, ml_analysis: Dict[str, Any]) -> None:
        """Update authentication statistics."""
        
        self.auth_stats['total_authentications'] += 1
        
        decision = ml_analysis['decision']
        confidence = ml_analysis['combined_confidence']
        
        if decision == 'continue':
            self.auth_stats['successful_authentications'] += 1
        elif decision in ['challenge', 'monitor']:
            self.auth_stats['challenged_authentications'] += 1
        else:  # logout
            self.auth_stats['failed_authentications'] += 1
            
        # Update rolling average confidence
        total = self.auth_stats['total_authentications']
        current_avg = self.auth_stats['average_confidence']
        self.auth_stats['average_confidence'] = ((current_avg * (total - 1)) + confidence) / total
        
    def _get_decision_message(self, decision: str) -> str:
        """Get human-readable message for authentication decision."""
        
        messages = {
            'continue': 'Authentication successful - continuing normal operation',
            'monitor': 'Authentication successful - enhanced monitoring enabled',
            'challenge': 'Additional authentication required',
            'logout': 'Authentication failed - session terminated'
        }
        
        return messages.get(decision, f'Unknown decision: {decision}')
        
    def _notify_auth_callbacks(self, auth_result: AuthenticationResult) -> None:
        """Notify registered authentication callbacks."""
        
        for callback in self.auth_callbacks:
            try:
                callback(auth_result)
            except Exception as e:
                self.logger.error(f"Authentication callback error: {e}")
                
    def shutdown(self) -> None:
        """Shutdown authentication system gracefully."""
        
        try:
            # End all active sessions
            for session_id in list(self.active_sessions.keys()):
                self.end_session(session_id)
                
            # Stop security monitoring
            self.security_manager.stop_monitoring()
            
            self.logger.info("Authentication system shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")