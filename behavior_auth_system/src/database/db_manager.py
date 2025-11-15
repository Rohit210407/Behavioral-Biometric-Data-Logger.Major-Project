"""
Database Manager for Smart Behavior Authentication System
Handles user data, behavioral patterns, security events, and system logs.
"""

import sqlite3
import hashlib
import os
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

class DatabaseManager:
    """Comprehensive database manager for the authentication system."""
    
    def __init__(self, db_path: str = "data/behavior_auth.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)
        
        self._init_database()
        self.logger.info(f"Database initialized: {db_path}")
        
    def _init_database(self):
        """Initialize all database tables."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    pin_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    failed_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP NULL,
                    is_active BOOLEAN DEFAULT 1,
                    profile_complete BOOLEAN DEFAULT 0
                )
            ''')
            
            # User sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    session_token TEXT UNIQUE,
                    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    session_end TIMESTAMP NULL,
                    ip_address TEXT,
                    device_info TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Behavioral baseline data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS behavioral_baselines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    collection_start TIMESTAMP,
                    collection_end TIMESTAMP,
                    keystroke_patterns TEXT,  -- JSON
                    mouse_patterns TEXT,      -- JSON
                    window_patterns TEXT,     -- JSON
                    tab_switching_patterns TEXT,  -- JSON
                    application_usage TEXT,  -- JSON
                    timing_patterns TEXT,     -- JSON
                    activity_rhythm TEXT,     -- JSON
                    is_complete BOOLEAN DEFAULT 0,
                    accuracy_score FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Security events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    event_type TEXT NOT NULL,  -- FAST_TYPING, TAB_FLOODING, SCREEN_LOCK, etc.
                    event_details TEXT,        -- JSON with event data
                    risk_level TEXT,           -- LOW, MEDIUM, HIGH, CRITICAL
                    action_taken TEXT,         -- ALERT, LOCK_SCREEN, LOGOUT, etc.
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved BOOLEAN DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Real-time behavioral data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS behavioral_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    session_id INTEGER,
                    event_type TEXT,          -- keystroke, mouse_move, mouse_click, window_switch, etc.
                    event_data TEXT,          -- JSON with detailed event data
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed BOOLEAN DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (session_id) REFERENCES user_sessions (id)
                )
            ''')
            
            # System configuration
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_key TEXT UNIQUE NOT NULL,
                    config_value TEXT,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Audit logs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Insert default system configuration
            default_configs = [
                ('fast_typing_threshold', '300', 'Words per minute threshold for fast typing detection'),
                ('tab_switching_threshold', '20', 'Tab switches per 30 seconds threshold'),
                ('baseline_duration_minutes', '15', 'Duration for baseline behavioral training'),
                ('max_failed_attempts', '3', 'Maximum failed login attempts before lockout'),
                ('lockout_duration_minutes', '5', 'Account lockout duration in minutes'),
                ('session_timeout_minutes', '30', 'Session timeout duration'),
            ]
            
            for key, value, desc in default_configs:
                cursor.execute('''
                    INSERT OR IGNORE INTO system_config (config_key, config_value, description)
                    VALUES (?, ?, ?)
                ''', (key, value, desc))
            
            conn.commit()
            conn.close()
            
            self.logger.info("Database tables initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise
            
    def _hash_pin(self, pin: str, salt: bytes) -> str:
        """Hash PIN with salt using PBKDF2."""
        return hashlib.pbkdf2_hmac('sha256', pin.encode(), salt, 100000).hex()
        
    def _generate_salt(self) -> bytes:
        """Generate random salt."""
        return os.urandom(32)
        
    def register_user(self, email: str, pin: str) -> Tuple[bool, str]:
        """Register a new user."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                conn.close()
                return False, "User already exists"
                
            # Create user
            salt = self._generate_salt()
            pin_hash = self._hash_pin(pin, salt)
            
            cursor.execute('''
                INSERT INTO users (email, pin_hash, salt)
                VALUES (?, ?, ?)
            ''', (email, pin_hash, salt.hex()))
            
            user_id = cursor.lastrowid
            
            # Log the registration
            self._log_audit(cursor, user_id, "USER_REGISTERED", f"New user registered: {email}")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"User registered successfully: {email}")
            return True, "Registration successful"
            
        except Exception as e:
            self.logger.error(f"User registration failed: {e}")
            return False, f"Registration failed: {str(e)}"
            
    def login_user(self, email: str, pin: str) -> Tuple[bool, str, Optional[Dict]]:
        """Authenticate user login."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, pin_hash, salt, failed_attempts, locked_until, is_active
                FROM users WHERE email = ?
            ''', (email,))
            
            result = cursor.fetchone()
            if not result:
                conn.close()
                return False, "Invalid email or PIN", None
                
            user_id, stored_hash, salt_hex, failed_attempts, locked_until, is_active = result
            
            # Check if account is active
            if not is_active:
                conn.close()
                return False, "Account is deactivated", None
                
            # Check if account is locked
            if locked_until:
                lock_time = datetime.fromisoformat(locked_until)
                if datetime.now() < lock_time:
                    conn.close()
                    return False, "Account is temporarily locked", None
                    
            # Verify PIN
            salt = bytes.fromhex(salt_hex)
            pin_hash = self._hash_pin(pin, salt)
            
            if pin_hash == stored_hash:
                # Successful login
                cursor.execute('''
                    UPDATE users SET last_login = CURRENT_TIMESTAMP, 
                    failed_attempts = 0, locked_until = NULL WHERE id = ?
                ''', (user_id,))
                
                # Create session
                session_token = self._generate_session_token()
                cursor.execute('''
                    INSERT INTO user_sessions (user_id, session_token, ip_address, device_info)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, session_token, "localhost", "Enhanced Security Demo"))
                
                session_id = cursor.lastrowid
                
                # Log successful login
                self._log_audit(cursor, user_id, "LOGIN_SUCCESS", f"User logged in: {email}")
                
                conn.commit()
                conn.close()
                
                user_data = {
                    "id": user_id,
                    "email": email,
                    "session_token": session_token,
                    "session_id": session_id
                }
                
                self.logger.info(f"User logged in successfully: {email}")
                return True, "Login successful", user_data
                
            else:
                # Failed login
                failed_attempts += 1
                locked_until = None
                
                if failed_attempts >= 3:
                    # Lock account for 5 minutes
                    lock_time = datetime.now() + timedelta(minutes=5)
                    locked_until = lock_time.isoformat()
                    
                cursor.execute('''
                    UPDATE users SET failed_attempts = ?, locked_until = ? WHERE id = ?
                ''', (failed_attempts, locked_until, user_id))
                
                # Log failed login
                self._log_audit(cursor, user_id, "LOGIN_FAILED", f"Failed login attempt: {email}")
                
                conn.commit()
                conn.close()
                
                remaining = 3 - failed_attempts
                message = f"Invalid PIN. {remaining} attempts remaining" if remaining > 0 else "Account locked for 5 minutes"
                return False, message, None
                
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            return False, f"Login failed: {str(e)}", None
            
    def _generate_session_token(self) -> str:
        """Generate secure session token."""
        import secrets
        return secrets.token_urlsafe(32)
        
    def _log_audit(self, cursor, user_id: int, action: str, details: str):
        """Log audit event."""
        cursor.execute('''
            INSERT INTO audit_logs (user_id, action, details, ip_address)
            VALUES (?, ?, ?, ?)
        ''', (user_id, action, details, "localhost"))
        
    def save_baseline_data(self, user_id: int, baseline_data: Dict[str, Any]) -> bool:
        """Save behavioral baseline data."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO behavioral_baselines (
                    user_id, collection_start, collection_end,
                    keystroke_patterns, mouse_patterns, window_patterns,
                    tab_switching_patterns, application_usage, timing_patterns,
                    activity_rhythm, is_complete, accuracy_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                baseline_data.get('collection_start'),
                baseline_data.get('collection_end'),
                json.dumps(baseline_data.get('keystroke_patterns', {})),
                json.dumps(baseline_data.get('mouse_patterns', {})),
                json.dumps(baseline_data.get('window_patterns', {})),
                json.dumps(baseline_data.get('tab_switching_patterns', {})),
                json.dumps(baseline_data.get('application_usage', {})),
                json.dumps(baseline_data.get('timing_patterns', {})),
                json.dumps(baseline_data.get('activity_rhythm', {})),
                baseline_data.get('is_complete', False),
                baseline_data.get('accuracy_score', 0.0)
            ))
            
            # Update user profile completion status
            cursor.execute('''
                UPDATE users SET profile_complete = 1 WHERE id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Baseline data saved for user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save baseline data: {e}")
            return False
            
    def log_security_event(self, user_id: int, event_type: str, event_details: Dict[str, Any], 
                          risk_level: str, action_taken: str) -> bool:
        """Log security event."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO security_events (user_id, event_type, event_details, risk_level, action_taken)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, event_type, json.dumps(event_details), risk_level, action_taken))
            
            conn.commit()
            conn.close()
            
            self.logger.warning(f"Security event logged: {event_type} for user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to log security event: {e}")
            return False
            
    def save_behavioral_event(self, user_id: int, session_id: int, event_type: str, event_data: Dict[str, Any]) -> bool:
        """Save real-time behavioral event."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO behavioral_data (user_id, session_id, event_type, event_data)
                VALUES (?, ?, ?, ?)
            ''', (user_id, session_id, event_type, json.dumps(event_data)))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save behavioral event: {e}")
            return False
            
    def get_user_baseline(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user's behavioral baseline."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT keystroke_patterns, mouse_patterns, window_patterns,
                       tab_switching_patterns, application_usage, timing_patterns,
                       activity_rhythm, accuracy_score
                FROM behavioral_baselines 
                WHERE user_id = ? AND is_complete = 1
                ORDER BY created_at DESC LIMIT 1
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'keystroke_patterns': json.loads(result[0]) if result[0] else {},
                    'mouse_patterns': json.loads(result[1]) if result[1] else {},
                    'window_patterns': json.loads(result[2]) if result[2] else {},
                    'tab_switching_patterns': json.loads(result[3]) if result[3] else {},
                    'application_usage': json.loads(result[4]) if result[4] else {},
                    'timing_patterns': json.loads(result[5]) if result[5] else {},
                    'activity_rhythm': json.loads(result[6]) if result[6] else {},
                    'accuracy_score': result[7]
                }
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get user baseline: {e}")
            return None
            
    def get_security_events(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent security events for user."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT event_type, event_details, risk_level, action_taken, timestamp
                FROM security_events 
                WHERE user_id = ?
                ORDER BY timestamp DESC LIMIT ?
            ''', (user_id, limit))
            
            results = cursor.fetchall()
            conn.close()
            
            events = []
            for result in results:
                events.append({
                    'event_type': result[0],
                    'event_details': json.loads(result[1]) if result[1] else {},
                    'risk_level': result[2],
                    'action_taken': result[3],
                    'timestamp': result[4]
                })
                
            return events
            
        except Exception as e:
            self.logger.error(f"Failed to get security events: {e}")
            return []
            
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            
            # User count
            cursor.execute("SELECT COUNT(*) FROM users")
            stats['total_users'] = cursor.fetchone()[0]
            
            # Active sessions
            cursor.execute("SELECT COUNT(*) FROM user_sessions WHERE session_end IS NULL")
            stats['active_sessions'] = cursor.fetchone()[0]
            
            # Security events today
            cursor.execute('''
                SELECT COUNT(*) FROM security_events 
                WHERE date(timestamp) = date('now')
            ''')
            stats['security_events_today'] = cursor.fetchone()[0]
            
            # Completed baselines
            cursor.execute("SELECT COUNT(*) FROM behavioral_baselines WHERE is_complete = 1")
            stats['completed_baselines'] = cursor.fetchone()[0]
            
            conn.close()
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            return {}
            
    def cleanup_old_data(self, days_to_keep: int = 30) -> bool:
        """Clean up old data."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Clean old behavioral data
            cursor.execute('''
                DELETE FROM behavioral_data 
                WHERE timestamp < ? AND processed = 1
            ''', (cutoff_date.isoformat(),))
            
            # Clean old audit logs
            cursor.execute('''
                DELETE FROM audit_logs 
                WHERE timestamp < ?
            ''', (cutoff_date.isoformat(),))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Cleaned up data older than {days_to_keep} days")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
            return False