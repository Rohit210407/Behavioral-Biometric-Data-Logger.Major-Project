"""
Adaptive Response System for handling security alerts and authentication challenges.
Implements risk-based authentication and graduated security responses.
"""

import time
import logging
import threading
from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
import uuid

class ResponseAction(Enum):
    """Available security response actions."""
    CONTINUE = "continue"
    MONITOR = "monitor"
    CHALLENGE_PIN = "challenge_pin"
    CHALLENGE_BIOMETRIC = "challenge_biometric"
    CHALLENGE_SMS = "challenge_sms"
    RESTRICT_FUNCTIONS = "restrict_functions"
    LOCK_SESSION = "lock_session"
    LOGOUT = "logout"
    ALERT_ADMIN = "alert_admin"

class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityAlert:
    """Represents a security alert with metadata."""
    alert_id: str
    alert_type: str
    severity: AlertSeverity
    timestamp: float
    user_id: str
    session_id: str
    confidence_score: float
    risk_factors: List[str]
    recommended_actions: List[ResponseAction]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'alert_id': self.alert_id,
            'alert_type': self.alert_type,
            'severity': self.severity.value,
            'timestamp': self.timestamp,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'confidence_score': self.confidence_score,
            'risk_factors': self.risk_factors,
            'recommended_actions': [action.value for action in self.recommended_actions],
            'metadata': self.metadata
        }

@dataclass
class AuthChallenge:
    """Represents an authentication challenge."""
    challenge_id: str
    challenge_type: str
    user_id: str
    session_id: str
    created_at: float
    expires_at: float
    attempts_remaining: int
    is_completed: bool = False
    is_successful: bool = False
    
class ResponseEngine:
    """Core engine for determining appropriate security responses."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Response thresholds
        self.confidence_thresholds = config.get('authentication', {}).get('confidence_levels', {})
        self.action_mappings = config.get('authentication', {}).get('actions', {})
        
        # Challenge settings
        self.challenge_types = config.get('authentication', {}).get('challenges', {}).get('types', ['pin'])
        self.max_attempts = config.get('authentication', {}).get('challenges', {}).get('max_attempts', 3)
        self.challenge_timeout = 300  # 5 minutes
        
    def analyze_risk(self, behavioral_analysis: Dict[str, Any], 
                    security_context: Dict[str, Any]) -> SecurityAlert:
        """Analyze risk and generate security alert."""
        
        # Extract key metrics
        confidence = behavioral_analysis.get('combined_confidence', 0.0)
        confidence_level = behavioral_analysis.get('confidence_level', 'very_low')
        anomaly_score = behavioral_analysis.get('anomaly_score', 1.0)
        
        # Identify risk factors
        risk_factors = []
        
        if confidence < 0.3:
            risk_factors.append('very_low_behavioral_confidence')
        elif confidence < 0.5:
            risk_factors.append('low_behavioral_confidence')
            
        if anomaly_score > 0.7:
            risk_factors.append('high_anomaly_score')
            
        # Check security context factors
        if security_context.get('device_mismatch', False):
            risk_factors.append('device_fingerprint_mismatch')
            
        if security_context.get('location_change', False):
            risk_factors.append('unusual_location')
            
        if security_context.get('time_anomaly', False):
            risk_factors.append('unusual_time_pattern')
            
        # Determine severity
        severity = self._calculate_severity(confidence, anomaly_score, risk_factors)
        
        # Recommend actions
        recommended_actions = self._recommend_actions(confidence_level, severity, risk_factors)
        
        # Create alert
        alert = SecurityAlert(
            alert_id=str(uuid.uuid4()),
            alert_type='behavioral_anomaly',
            severity=severity,
            timestamp=time.time(),
            user_id=security_context.get('user_id', 'unknown'),
            session_id=security_context.get('session_id', 'unknown'),
            confidence_score=confidence,
            risk_factors=risk_factors,
            recommended_actions=recommended_actions,
            metadata={
                'behavioral_analysis': behavioral_analysis,
                'security_context': security_context,
                'anomaly_score': anomaly_score
            }
        )
        
        return alert
        
    def _calculate_severity(self, confidence: float, anomaly_score: float, 
                          risk_factors: List[str]) -> AlertSeverity:
        """Calculate alert severity based on multiple factors."""
        
        # Base severity from confidence
        if confidence < 0.2:
            base_severity = AlertSeverity.CRITICAL
        elif confidence < 0.4:
            base_severity = AlertSeverity.HIGH
        elif confidence < 0.6:
            base_severity = AlertSeverity.MEDIUM
        else:
            base_severity = AlertSeverity.LOW
            
        # Adjust for anomaly score
        if anomaly_score > 0.8:
            if base_severity in [AlertSeverity.LOW, AlertSeverity.MEDIUM]:
                base_severity = AlertSeverity.HIGH
        
        # Adjust for risk factors
        critical_factors = [
            'device_fingerprint_mismatch',
            'very_low_behavioral_confidence'
        ]
        
        if any(factor in risk_factors for factor in critical_factors):
            if base_severity != AlertSeverity.CRITICAL:
                base_severity = AlertSeverity.HIGH
                
        return base_severity
        
    def _recommend_actions(self, confidence_level: str, severity: AlertSeverity,
                          risk_factors: List[str]) -> List[ResponseAction]:
        """Recommend appropriate response actions."""
        
        actions = []
        
        # Base actions from confidence level
        if confidence_level == 'high':
            actions.append(ResponseAction.CONTINUE)
        elif confidence_level == 'medium':
            actions.extend([ResponseAction.MONITOR, ResponseAction.CONTINUE])
        elif confidence_level == 'low':
            actions.extend([ResponseAction.CHALLENGE_PIN, ResponseAction.MONITOR])
        else:  # very_low
            actions.extend([ResponseAction.LOGOUT, ResponseAction.ALERT_ADMIN])
            
        # Additional actions based on severity
        if severity == AlertSeverity.CRITICAL:
            actions.extend([
                ResponseAction.LOGOUT,
                ResponseAction.ALERT_ADMIN,
                ResponseAction.LOCK_SESSION
            ])
        elif severity == AlertSeverity.HIGH:
            actions.extend([
                ResponseAction.CHALLENGE_BIOMETRIC,
                ResponseAction.RESTRICT_FUNCTIONS
            ])
            
        # Context-specific actions
        if 'device_fingerprint_mismatch' in risk_factors:
            actions.append(ResponseAction.CHALLENGE_SMS)
            
        if 'unusual_location' in risk_factors:
            actions.append(ResponseAction.CHALLENGE_BIOMETRIC)
            
        # Remove duplicates while preserving order
        unique_actions = []
        for action in actions:
            if action not in unique_actions:
                unique_actions.append(action)
                
        return unique_actions

class ChallengeManager:
    """Manages authentication challenges and responses."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.active_challenges: Dict[str, AuthChallenge] = {}
        self.challenge_handlers: Dict[str, Callable] = {}
        
        # Challenge settings
        self.max_attempts = config.get('authentication', {}).get('challenges', {}).get('max_attempts', 3)
        self.challenge_timeout = config.get('authentication', {}).get('challenges', {}).get('lockout_duration', 300)
        
    def create_challenge(self, challenge_type: str, user_id: str, 
                        session_id: str) -> Optional[AuthChallenge]:
        """Create a new authentication challenge."""
        
        try:
            challenge = AuthChallenge(
                challenge_id=str(uuid.uuid4()),
                challenge_type=challenge_type,
                user_id=user_id,
                session_id=session_id,
                created_at=time.time(),
                expires_at=time.time() + self.challenge_timeout,
                attempts_remaining=self.max_attempts
            )
            
            self.active_challenges[challenge.challenge_id] = challenge
            
            self.logger.info(f"Created {challenge_type} challenge for user {user_id}")
            
            return challenge
            
        except Exception as e:
            self.logger.error(f"Failed to create challenge: {e}")
            return None
            
    def process_challenge_response(self, challenge_id: str, 
                                 response: Dict[str, Any]) -> Tuple[bool, str]:
        """Process response to authentication challenge."""
        
        if challenge_id not in self.active_challenges:
            return False, "Challenge not found or expired"
            
        challenge = self.active_challenges[challenge_id]
        
        # Check if challenge has expired
        if time.time() > challenge.expires_at:
            self._cleanup_challenge(challenge_id)
            return False, "Challenge expired"
            
        # Check if challenge already completed
        if challenge.is_completed:
            return challenge.is_successful, "Challenge already completed"
            
        # Process response based on challenge type
        success, message = self._validate_challenge_response(challenge, response)
        
        # Update challenge state
        if success:
            challenge.is_completed = True
            challenge.is_successful = True
            self.logger.info(f"Challenge {challenge_id} completed successfully")
        else:
            challenge.attempts_remaining -= 1
            
            if challenge.attempts_remaining <= 0:
                challenge.is_completed = True
                challenge.is_successful = False
                self.logger.warning(f"Challenge {challenge_id} failed - no attempts remaining")
                message = "Maximum attempts exceeded"
                
        return success, message
        
    def _validate_challenge_response(self, challenge: AuthChallenge, 
                                   response: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate challenge response based on type."""
        
        challenge_type = challenge.challenge_type
        
        if challenge_type == 'pin':
            return self._validate_pin_challenge(challenge, response)
        elif challenge_type == 'biometric':
            return self._validate_biometric_challenge(challenge, response)
        elif challenge_type == 'sms':
            return self._validate_sms_challenge(challenge, response)
        else:
            return False, f"Unknown challenge type: {challenge_type}"
            
    def _validate_pin_challenge(self, challenge: AuthChallenge, 
                              response: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate PIN challenge response."""
        
        provided_pin = response.get('pin', '')
        expected_pin = response.get('expected_pin', '')  # Would come from user profile
        
        if not provided_pin:
            return False, "PIN not provided"
            
        if provided_pin == expected_pin:
            return True, "PIN verified"
        else:
            return False, "Invalid PIN"
            
    def _validate_biometric_challenge(self, challenge: AuthChallenge,
                                    response: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate biometric challenge response."""
        
        # This would integrate with actual biometric validation
        biometric_data = response.get('biometric_data')
        
        if not biometric_data:
            return False, "Biometric data not provided"
            
        # Placeholder for actual biometric validation
        # In real implementation, this would validate fingerprint, face, etc.
        confidence = response.get('biometric_confidence', 0.0)
        
        if confidence >= 0.8:
            return True, "Biometric verified"
        else:
            return False, "Biometric verification failed"
            
    def _validate_sms_challenge(self, challenge: AuthChallenge,
                              response: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate SMS challenge response."""
        
        provided_code = response.get('sms_code', '')
        expected_code = response.get('expected_code', '')  # Would be generated and sent
        
        if not provided_code:
            return False, "SMS code not provided"
            
        if provided_code == expected_code:
            return True, "SMS code verified"
        else:
            return False, "Invalid SMS code"
            
    def _cleanup_challenge(self, challenge_id: str) -> None:
        """Remove expired or completed challenge."""
        if challenge_id in self.active_challenges:
            del self.active_challenges[challenge_id]
            
    def cleanup_expired_challenges(self) -> int:
        """Clean up all expired challenges."""
        current_time = time.time()
        expired_challenges = [
            cid for cid, challenge in self.active_challenges.items()
            if current_time > challenge.expires_at or challenge.is_completed
        ]
        
        for challenge_id in expired_challenges:
            self._cleanup_challenge(challenge_id)
            
        return len(expired_challenges)

class AdaptiveResponseManager:
    """Main manager for adaptive security responses."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.response_engine = ResponseEngine(config)
        self.challenge_manager = ChallengeManager(config)
        
        # Response callbacks
        self.response_callbacks: Dict[ResponseAction, List[Callable]] = {}
        
        # Active restrictions
        self.active_restrictions: Dict[str, List[str]] = {}  # session_id -> restricted functions
        
        # Monitoring
        self.alert_history: List[SecurityAlert] = []
        self.response_history: List[Dict[str, Any]] = []
        
    def process_behavioral_analysis(self, behavioral_analysis: Dict[str, Any],
                                  security_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process behavioral analysis and determine response."""
        
        try:
            # Generate security alert
            alert = self.response_engine.analyze_risk(behavioral_analysis, security_context)
            
            # Store alert
            self.alert_history.append(alert)
            
            # Execute response actions
            response_results = self._execute_response_actions(alert)
            
            # Log response
            response_record = {
                'alert_id': alert.alert_id,
                'timestamp': time.time(),
                'actions_taken': response_results,
                'user_id': alert.user_id,
                'session_id': alert.session_id
            }
            self.response_history.append(response_record)
            
            return {
                'alert': alert.to_dict(),
                'actions_taken': response_results,
                'requires_user_action': self._requires_user_action(response_results)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process behavioral analysis: {e}")
            return {
                'error': str(e),
                'actions_taken': [],
                'requires_user_action': False
            }
            
    def _execute_response_actions(self, alert: SecurityAlert) -> List[Dict[str, Any]]:
        """Execute recommended response actions."""
        
        results = []
        
        for action in alert.recommended_actions:
            try:
                result = self._execute_single_action(action, alert)
                results.append({
                    'action': action.value,
                    'success': result.get('success', False),
                    'message': result.get('message', ''),
                    'data': result.get('data', {})
                })
                
            except Exception as e:
                self.logger.error(f"Failed to execute action {action.value}: {e}")
                results.append({
                    'action': action.value,
                    'success': False,
                    'message': str(e),
                    'data': {}
                })
                
        return results
        
    def _execute_single_action(self, action: ResponseAction, 
                             alert: SecurityAlert) -> Dict[str, Any]:
        """Execute a single response action."""
        
        if action == ResponseAction.CONTINUE:
            return {'success': True, 'message': 'Continuing normal operation'}
            
        elif action == ResponseAction.MONITOR:
            return {'success': True, 'message': 'Increased monitoring enabled'}
            
        elif action == ResponseAction.CHALLENGE_PIN:
            challenge = self.challenge_manager.create_challenge(
                'pin', alert.user_id, alert.session_id
            )
            return {
                'success': challenge is not None,
                'message': 'PIN challenge created' if challenge else 'Failed to create challenge',
                'data': {'challenge_id': challenge.challenge_id if challenge else None}
            }
            
        elif action == ResponseAction.CHALLENGE_BIOMETRIC:
            challenge = self.challenge_manager.create_challenge(
                'biometric', alert.user_id, alert.session_id
            )
            return {
                'success': challenge is not None,
                'message': 'Biometric challenge created' if challenge else 'Failed to create challenge',
                'data': {'challenge_id': challenge.challenge_id if challenge else None}
            }
            
        elif action == ResponseAction.RESTRICT_FUNCTIONS:
            restricted_functions = ['financial_transactions', 'data_export', 'admin_functions']
            self.active_restrictions[alert.session_id] = restricted_functions
            return {
                'success': True,
                'message': 'Functions restricted',
                'data': {'restricted_functions': restricted_functions}
            }
            
        elif action == ResponseAction.LOGOUT:
            return {
                'success': True,
                'message': 'User logout initiated',
                'data': {'action_required': 'logout'}
            }
            
        elif action == ResponseAction.ALERT_ADMIN:
            return {
                'success': True,
                'message': 'Administrator alert sent',
                'data': {'alert_type': 'security_incident'}
            }
            
        else:
            return {'success': False, 'message': f'Unknown action: {action.value}'}
            
    def _requires_user_action(self, response_results: List[Dict[str, Any]]) -> bool:
        """Check if any responses require user action."""
        
        user_action_responses = [
            'PIN challenge created',
            'Biometric challenge created', 
            'SMS challenge created',
            'User logout initiated'
        ]
        
        for result in response_results:
            if result.get('message') in user_action_responses:
                return True
                
        return False
        
    def register_response_callback(self, action: ResponseAction, callback: Callable) -> None:
        """Register callback for specific response action."""
        if action not in self.response_callbacks:
            self.response_callbacks[action] = []
        self.response_callbacks[action].append(callback)
        
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system response status."""
        recent_alerts = [
            alert for alert in self.alert_history
            if time.time() - alert.timestamp < 3600  # Last hour
        ]
        
        active_challenges = len(self.challenge_manager.active_challenges)
        active_restrictions_count = len(self.active_restrictions)
        
        return {
            'recent_alerts': len(recent_alerts),
            'active_challenges': active_challenges,
            'active_restrictions': active_restrictions_count,
            'last_alert': recent_alerts[-1].to_dict() if recent_alerts else None
        }