"""
Security module providing encryption, session management, and data protection.
Implements AES-256 encryption, session integrity, and privacy protection mechanisms.
"""

import os
import time
import hashlib
import secrets
import base64
import json
from typing import Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend

@dataclass
class SecurityConfig:
    """Security configuration parameters."""
    algorithm: str = "AES-256-GCM"
    key_derivation: str = "PBKDF2"
    iterations: int = 100000
    salt_length: int = 32
    key_length: int = 32  # 256 bits

class EncryptionManager:
    """Handles all encryption and decryption operations."""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.backend = default_backend()
        
    def generate_key(self, password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """Generate encryption key from password using PBKDF2."""
        if salt is None:
            salt = os.urandom(self.config.salt_length)
            
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.config.key_length,
            salt=salt,
            iterations=self.config.iterations,
            backend=self.backend
        )
        
        key = kdf.derive(password.encode())
        return key, salt
        
    def encrypt_data(self, data: Union[str, bytes], key: bytes) -> Dict[str, str]:
        """Encrypt data using AES-256-GCM."""
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        # Generate random IV
        iv = os.urandom(12)  # GCM recommended IV length
        
        # Create cipher
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        
        # Encrypt data
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        # Return encrypted data with metadata
        return {
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
            'iv': base64.b64encode(iv).decode('utf-8'),
            'tag': base64.b64encode(encryptor.tag).decode('utf-8'),
            'algorithm': self.config.algorithm
        }
        
    def decrypt_data(self, encrypted_data: Dict[str, str], key: bytes) -> bytes:
        """Decrypt data using AES-256-GCM."""
        ciphertext = base64.b64decode(encrypted_data['ciphertext'])
        iv = base64.b64decode(encrypted_data['iv'])
        tag = base64.b64decode(encrypted_data['tag'])
        
        # Create cipher
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=self.backend)
        decryptor = cipher.decryptor()
        
        # Decrypt data
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext
        
    def hash_data(self, data: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
        """Create secure hash of data for privacy protection."""
        if salt is None:
            salt = os.urandom(16)
            
        hash_obj = hashlib.sha256()
        hash_obj.update(salt + data.encode('utf-8'))
        
        return hash_obj.hexdigest(), base64.b64encode(salt).decode('utf-8')

@dataclass
class SessionToken:
    """Secure session token with metadata."""
    token_id: str
    user_id: str
    session_id: str
    created_at: float
    expires_at: float
    last_activity: float
    device_fingerprint: Optional[str] = None
    ip_address: Optional[str] = None
    
    def is_valid(self) -> bool:
        """Check if token is still valid."""
        now = time.time()
        return now < self.expires_at
        
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return not self.is_valid()
        
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = time.time()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'token_id': self.token_id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'created_at': self.created_at,
            'expires_at': self.expires_at,
            'last_activity': self.last_activity,
            'device_fingerprint': self.device_fingerprint,
            'ip_address': self.ip_address
        }

class SessionManager:
    """Manages secure authentication sessions with integrity checks."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.encryption_manager = EncryptionManager(SecurityConfig())
        self.active_sessions: Dict[str, SessionToken] = {}
        self.session_timeout = config.get('security', {}).get('session', {}).get('timeout_minutes', 30) * 60
        self.idle_timeout = config.get('security', {}).get('session', {}).get('idle_timeout_minutes', 15) * 60
        self.max_concurrent = config.get('security', {}).get('session', {}).get('max_concurrent_sessions', 3)
        
    def create_session(self, user_id: str, device_fingerprint: Optional[str] = None,
                      ip_address: Optional[str] = None) -> SessionToken:
        """Create a new secure session."""
        # Check concurrent session limit
        user_sessions = [s for s in self.active_sessions.values() if s.user_id == user_id]
        if len(user_sessions) >= self.max_concurrent:
            # Remove oldest session
            oldest = min(user_sessions, key=lambda s: s.created_at)
            self.invalidate_session(oldest.session_id)
            
        # Generate unique identifiers
        session_id = secrets.token_urlsafe(32)
        token_id = secrets.token_urlsafe(16)
        
        now = time.time()
        token = SessionToken(
            token_id=token_id,
            user_id=user_id,
            session_id=session_id,
            created_at=now,
            expires_at=now + self.session_timeout,
            last_activity=now,
            device_fingerprint=device_fingerprint,
            ip_address=ip_address
        )
        
        self.active_sessions[session_id] = token
        return token
        
    def validate_session(self, session_id: str, device_fingerprint: Optional[str] = None,
                        ip_address: Optional[str] = None) -> Optional[SessionToken]:
        """Validate session and check security parameters."""
        if session_id not in self.active_sessions:
            return None
            
        token = self.active_sessions[session_id]
        
        # Check expiration
        if token.is_expired():
            self.invalidate_session(session_id)
            return None
            
        # Check idle timeout
        if time.time() - token.last_activity > self.idle_timeout:
            self.invalidate_session(session_id)
            return None
            
        # Check device fingerprint if provided
        if device_fingerprint and token.device_fingerprint:
            if device_fingerprint != token.device_fingerprint:
                self.invalidate_session(session_id)
                return None
                
        # Check IP address consistency (optional - may trigger additional verification)
        if ip_address and token.ip_address:
            if ip_address != token.ip_address:
                # Could implement geolocation check here
                pass
                
        # Update activity and return valid token
        token.update_activity()
        return token
        
    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate and remove session."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True
        return False
        
    def cleanup_expired_sessions(self) -> int:
        """Remove all expired sessions."""
        expired_sessions = [
            sid for sid, token in self.active_sessions.items()
            if token.is_expired() or (time.time() - token.last_activity > self.idle_timeout)
        ]
        
        for session_id in expired_sessions:
            self.invalidate_session(session_id)
            
        return len(expired_sessions)
        
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information."""
        if session_id not in self.active_sessions:
            return None
            
        token = self.active_sessions[session_id]
        return {
            'session_id': session_id,
            'user_id': token.user_id,
            'created_at': token.created_at,
            'expires_at': token.expires_at,
            'last_activity': token.last_activity,
            'time_remaining': max(0, token.expires_at - time.time()),
            'idle_time': time.time() - token.last_activity,
            'is_valid': token.is_valid()
        }

class PrivacyProtection:
    """Implements privacy protection mechanisms for behavioral data."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enable_differential_privacy = config.get('security', {}).get('privacy', {}).get('enable_differential_privacy', True)
        self.noise_epsilon = config.get('security', {}).get('privacy', {}).get('noise_epsilon', 0.1)
        self.hash_inputs = config.get('security', {}).get('privacy', {}).get('hash_raw_inputs', True)
        self.encryption_manager = EncryptionManager(SecurityConfig())
        
    def add_differential_privacy_noise(self, value: float, sensitivity: float = 1.0) -> float:
        """Add calibrated noise for differential privacy."""
        if not self.enable_differential_privacy:
            return value
            
        # Laplace mechanism for differential privacy
        scale = sensitivity / self.noise_epsilon
        noise = secrets.SystemRandom().gauss(0, scale)
        return value + noise
        
    def anonymize_keystroke_data(self, keystroke_data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize keystroke data while preserving behavioral patterns."""
        anonymized = keystroke_data.copy()
        
        # Hash actual key values if enabled
        if self.hash_inputs and 'key' in anonymized:
            anonymized['key_hash'], _ = self.encryption_manager.hash_data(anonymized['key'])
            del anonymized['key']
            
        # Add noise to timing features
        for feature in ['dwell_time', 'flight_time']:
            if feature in anonymized and anonymized[feature] is not None:
                anonymized[feature] = self.add_differential_privacy_noise(
                    anonymized[feature], sensitivity=0.01  # 10ms sensitivity
                )
                
        return anonymized
        
    def anonymize_mouse_data(self, mouse_data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize mouse data while preserving movement patterns."""
        anonymized = mouse_data.copy()
        
        # Remove absolute coordinates, keep relative movements
        if 'position' in anonymized:
            del anonymized['position']
            
        # Add noise to motion features
        for feature in ['velocity', 'acceleration']:
            if feature in anonymized and anonymized[feature] is not None:
                anonymized[feature] = self.add_differential_privacy_noise(
                    anonymized[feature], sensitivity=1.0  # 1 pixel/sec sensitivity
                )
                
        return anonymized