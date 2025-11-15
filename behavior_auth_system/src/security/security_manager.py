"""
Security Manager - Coordinates all security components and policies.
Provides unified security interface for the authentication system.
"""

import time
import logging
import threading
from typing import Dict, Any, Optional, List, Tuple, Callable
from dataclasses import dataclass
from enum import Enum

from .encryption import SessionManager, PrivacyProtection, EncryptionManager, SecurityConfig

class SecurityLevel(Enum):
    """Security threat levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityEvent:
    """Represents a security event or alert."""
    event_type: str
    severity: SecurityLevel
    timestamp: float
    user_id: str
    session_id: str
    description: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage."""
        return {
            'event_type': self.event_type,
            'severity': self.severity.value,
            'timestamp': self.timestamp,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'description': self.description,
            'metadata': self.metadata
        }

class SecurityManager:
    """Main security manager coordinating all security components."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize security components
        self.session_manager = SessionManager(config)
        self.privacy_protection = PrivacyProtection(config)
        self.encryption_manager = EncryptionManager(SecurityConfig())
        
        # Security monitoring
        self.security_events: List[SecurityEvent] = []
        self.event_callbacks: List[Callable] = []
        self.monitoring_active = False
        self._lock = threading.Lock()
        
        # Security policies
        self.max_failed_attempts = config.get('authentication', {}).get('challenges', {}).get('max_attempts', 3)
        self.lockout_duration = config.get('authentication', {}).get('challenges', {}).get('lockout_duration', 300)
        self.failed_attempts: Dict[str, List[float]] = {}  # user_id -> timestamps
        
    def start_monitoring(self) -> None:
        """Start security monitoring."""
        self.monitoring_active = True
        self.logger.info("Security monitoring started")
        
        # Start cleanup thread
        cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        cleanup_thread.start()
        
    def stop_monitoring(self) -> None:
        """Stop security monitoring."""
        self.monitoring_active = False
        self.logger.info("Security monitoring stopped")
        
    def create_secure_session(self, user_id: str, device_fingerprint: Optional[str] = None,
                            ip_address: Optional[str] = None) -> Optional[str]:
        """Create a new secure session with validation."""
        try:
            # Check if user is locked out
            if self._is_user_locked_out(user_id):
                self._log_security_event(
                    'session_creation_blocked',
                    SecurityLevel.HIGH,
                    user_id,
                    'Session creation blocked - user locked out',
                    {'reason': 'lockout_active'}
                )
                return None
                
            # Create session
            token = self.session_manager.create_session(
                user_id, device_fingerprint, ip_address
            )
            
            self._log_security_event(
                'session_created',
                SecurityLevel.LOW,
                user_id,
                f'New session created: {token.session_id}',
                {
                    'session_id': token.session_id,
                    'device_fingerprint': device_fingerprint,
                    'ip_address': ip_address
                }
            )
            
            return token.session_id
            
        except Exception as e:
            self.logger.error(f"Failed to create secure session: {e}")
            return None
            
    def validate_session(self, session_id: str, device_fingerprint: Optional[str] = None,
                        ip_address: Optional[str] = None) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Validate session with security checks."""
        try:
            token = self.session_manager.validate_session(
                session_id, device_fingerprint, ip_address
            )
            
            if not token:
                self._log_security_event(
                    'session_validation_failed',
                    SecurityLevel.MEDIUM,
                    'unknown',
                    f'Session validation failed: {session_id}',
                    {'session_id': session_id}
                )
                return False, None
                
            # Additional security checks
            security_context = self._assess_session_security(token, device_fingerprint, ip_address)
            
            return True, {
                'user_id': token.user_id,
                'session_id': token.session_id,
                'security_level': security_context['security_level'],
                'risk_score': security_context['risk_score'],
                'requires_additional_auth': security_context['requires_additional_auth']
            }
            
        except Exception as e:
            self.logger.error(f"Session validation error: {e}")
            return False, None
            
    def record_authentication_failure(self, user_id: str, reason: str) -> bool:
        """Record authentication failure and check for lockout."""
        with self._lock:
            current_time = time.time()
            
            if user_id not in self.failed_attempts:
                self.failed_attempts[user_id] = []
                
            # Add current failure
            self.failed_attempts[user_id].append(current_time)
            
            # Clean old attempts (outside lockout window)
            self.failed_attempts[user_id] = [
                t for t in self.failed_attempts[user_id]
                if current_time - t < self.lockout_duration
            ]
            
            # Check if lockout threshold reached
            if len(self.failed_attempts[user_id]) >= self.max_failed_attempts:
                self._log_security_event(
                    'user_locked_out',
                    SecurityLevel.HIGH,
                    user_id,
                    f'User locked out after {self.max_failed_attempts} failed attempts',
                    {
                        'failed_attempts': len(self.failed_attempts[user_id]),
                        'reason': reason,
                        'lockout_duration': self.lockout_duration
                    }
                )
                return True  # User is now locked out
                
            self._log_security_event(
                'authentication_failed',
                SecurityLevel.MEDIUM,
                user_id,
                f'Authentication failed: {reason}',
                {
                    'reason': reason,
                    'attempts_count': len(self.failed_attempts[user_id])
                }
            )
            
            return False
            
    def secure_data(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Apply security and privacy protection to behavioral data."""
        try:
            # Apply privacy protection
            if 'keystroke_features' in data:
                data['keystroke_features'] = self.privacy_protection.anonymize_keystroke_data(
                    data['keystroke_features']
                )
                
            if 'mouse_features' in data:
                data['mouse_features'] = self.privacy_protection.anonymize_mouse_data(
                    data['mouse_features']
                )
                
            # Add security metadata
            data['security_metadata'] = {
                'protected_at': time.time(),
                'user_id_hash': self.encryption_manager.hash_data(user_id)[0],
                'privacy_level': 'anonymized' if self.privacy_protection.hash_inputs else 'raw'
            }
            
            return data
            
        except Exception as e:
            self.logger.error(f"Data security processing failed: {e}")
            return data
            
    def add_security_callback(self, callback: Callable) -> None:
        """Add callback for security events."""
        self.event_callbacks.append(callback)
        
    def get_security_status(self) -> Dict[str, Any]:
        """Get overall security status."""
        active_sessions = len(self.session_manager.active_sessions)
        recent_events = len([
            e for e in self.security_events
            if time.time() - e.timestamp < 3600  # Last hour
        ])
        
        locked_users = sum(1 for user_id in self.failed_attempts.keys() if self._is_user_locked_out(user_id))
        
        return {
            'monitoring_active': self.monitoring_active,
            'active_sessions': active_sessions,
            'recent_security_events': recent_events,
            'locked_users': locked_users,
            'last_cleanup': getattr(self, 'last_cleanup', None)
        }
        
    def _is_user_locked_out(self, user_id: str) -> bool:
        """Check if user is currently locked out."""
        if user_id not in self.failed_attempts:
            return False
            
        current_time = time.time()
        recent_failures = [
            t for t in self.failed_attempts[user_id]
            if current_time - t < self.lockout_duration
        ]
        
        return len(recent_failures) >= self.max_failed_attempts
        
    def _assess_session_security(self, token, device_fingerprint: Optional[str],
                               ip_address: Optional[str]) -> Dict[str, Any]:
        """Assess security context of a session."""
        risk_score = 0.0
        security_level = SecurityLevel.LOW
        requires_additional_auth = False
        
        # Device fingerprint check
        if device_fingerprint and token.device_fingerprint:
            if device_fingerprint != token.device_fingerprint:
                risk_score += 0.3
                security_level = SecurityLevel.MEDIUM
                
        # IP address change check
        if ip_address and token.ip_address:
            if ip_address != token.ip_address:
                risk_score += 0.2
                
        # Session age check
        session_age = time.time() - token.created_at
        if session_age > 3600:  # More than 1 hour
            risk_score += 0.1
            
        # Determine security level and actions
        if risk_score >= 0.5:
            security_level = SecurityLevel.HIGH
            requires_additional_auth = True
        elif risk_score >= 0.3:
            security_level = SecurityLevel.MEDIUM
            
        return {
            'security_level': security_level.value,
            'risk_score': risk_score,
            'requires_additional_auth': requires_additional_auth
        }
        
    def _log_security_event(self, event_type: str, severity: SecurityLevel,
                          user_id: str, description: str, metadata: Dict[str, Any]) -> None:
        """Log security event."""
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            timestamp=time.time(),
            user_id=user_id,
            session_id=metadata.get('session_id', 'unknown'),
            description=description,
            metadata=metadata
        )
        
        self.security_events.append(event)
        self.logger.warning(f"Security Event: {event_type} - {description}")
        
        # Notify callbacks
        for callback in self.event_callbacks:
            try:
                callback(event)
            except Exception as e:
                self.logger.error(f"Security callback error: {e}")
                
    def _cleanup_loop(self) -> None:
        """Background cleanup of expired sessions and old events."""
        while self.monitoring_active:
            try:
                time.sleep(300)  # Run every 5 minutes
                
                # Cleanup expired sessions
                expired_count = self.session_manager.cleanup_expired_sessions()
                if expired_count > 0:
                    self.logger.info(f"Cleaned up {expired_count} expired sessions")
                    
                # Cleanup old security events (keep last 1000)
                if len(self.security_events) > 1000:
                    self.security_events = self.security_events[-1000:]
                    
                # Cleanup old failed attempts
                current_time = time.time()
                for user_id in list(self.failed_attempts.keys()):
                    self.failed_attempts[user_id] = [
                        t for t in self.failed_attempts[user_id]
                        if current_time - t < self.lockout_duration
                    ]
                    if not self.failed_attempts[user_id]:
                        del self.failed_attempts[user_id]
                        
                self.last_cleanup = current_time
                
            except Exception as e:
                self.logger.error(f"Cleanup loop error: {e}")
                
        self.logger.info("Security cleanup loop stopped")