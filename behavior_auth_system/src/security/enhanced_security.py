"""
Enhanced Security Module
Implements fast typing detection, tab switching monitoring, screen locking, and biometric access.
"""

import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import hashlib
import re
import cv2
import numpy as np
from collections import deque
from typing import Dict, List, Any, Optional, Tuple
import logging
import subprocess
import platform

class UserAuthManager:
    """Handles user registration, login, and PIN management."""
    
    def __init__(self, db_path: str = "data/users.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.current_user = None
        self.session_active = False
        self._init_database()
        
    def _init_database(self):
        """Initialize user database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    pin_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    failed_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP NULL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    session_end TIMESTAMP NULL,
                    ip_address TEXT,
                    device_info TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            
    def _hash_pin(self, pin: str, salt: bytes) -> str:
        """Hash PIN with salt using PBKDF2."""
        return hashlib.pbkdf2_hmac('sha256', pin.encode(), salt, 100000).hex()
        
    def _generate_salt(self) -> bytes:
        """Generate random salt."""
        import os
        return os.urandom(32)
        
    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
        
    def _validate_pin(self, pin: str) -> Tuple[bool, str]:
        """Validate PIN strength."""
        if len(pin) < 6:
            return False, "PIN must be at least 6 characters long"
        if not re.search(r'\d', pin):
            return False, "PIN must contain at least one number"
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', pin):
            return False, "PIN must contain at least one special character"
        return True, "PIN is valid"
        
    def register_user(self, email: str, pin: str) -> Tuple[bool, str]:
        """Register new user."""
        try:
            # Validate email
            if not self._validate_email(email):
                return False, "Invalid email format"
                
            # Validate PIN
            pin_valid, pin_message = self._validate_pin(pin)
            if not pin_valid:
                return False, pin_message
                
            # Check if user exists
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
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
            conn.commit()
            conn.close()
            
            self.logger.info(f"User registered successfully: {email}")
            return True, "Registration successful"
            
        except Exception as e:
            self.logger.error(f"Registration failed: {e}")
            return False, "Registration failed"
            
    def login_user(self, email: str, pin: str) -> Tuple[bool, str]:
        """Authenticate user login."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, pin_hash, salt, failed_attempts, locked_until
                FROM users WHERE email = ?
            ''', (email,))
            
            result = cursor.fetchone()
            if not result:
                conn.close()
                return False, "Invalid email or PIN"
                
            user_id, stored_hash, salt_hex, failed_attempts, locked_until = result
            
            # Check if account is locked
            if locked_until:
                lock_time = time.mktime(time.strptime(locked_until, '%Y-%m-%d %H:%M:%S'))
                if time.time() < lock_time:
                    conn.close()
                    return False, "Account is temporarily locked"
                    
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
                cursor.execute('''
                    INSERT INTO user_sessions (user_id, ip_address, device_info)
                    VALUES (?, ?, ?)
                ''', (user_id, "localhost", platform.platform()))
                
                conn.commit()
                conn.close()
                
                self.current_user = {"id": user_id, "email": email}
                self.session_active = True
                
                self.logger.info(f"User logged in successfully: {email}")
                return True, "Login successful"
                
            else:
                # Failed login
                failed_attempts += 1
                locked_until = None
                
                if failed_attempts >= 3:
                    # Lock account for 5 minutes
                    lock_time = time.time() + 300
                    locked_until = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(lock_time))
                    
                cursor.execute('''
                    UPDATE users SET failed_attempts = ?, locked_until = ? WHERE id = ?
                ''', (failed_attempts, locked_until, user_id))
                
                conn.commit()
                conn.close()
                
                return False, f"Invalid PIN. {3 - failed_attempts} attempts remaining"
                
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            return False, "Login failed"
            
    def logout_user(self):
        """Logout current user."""
        if self.current_user:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE user_sessions SET session_end = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND session_end IS NULL
                ''', (self.current_user["id"],))
                
                conn.commit()
                conn.close()
                
                self.logger.info(f"User logged out: {self.current_user['email']}")
                
            except Exception as e:
                self.logger.error(f"Logout error: {e}")
                
        self.current_user = None
        self.session_active = False

class FastTypingDetector:
    """Detects suspiciously fast typing patterns."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.wpm_threshold = config.get('words_per_minute_threshold', 300)
        self.monitoring_window = config.get('monitoring_window_seconds', 60)
        self.consecutive_alerts_to_lock = config.get('consecutive_alerts_to_lock', 2)
        
        self.keystroke_buffer = deque(maxlen=1000)
        self.alert_count = 0
        self.last_alert_time = 0
        self.logger = logging.getLogger(__name__)
        
    def add_keystroke(self, timestamp: float):
        """Add keystroke for fast typing analysis."""
        self.keystroke_buffer.append(timestamp)
        self._check_typing_speed()
        
    def _check_typing_speed(self):
        """Check if typing speed exceeds threshold."""
        if len(self.keystroke_buffer) < 10:
            return False
            
        current_time = time.time()
        
        # Get keystrokes in monitoring window
        window_keystrokes = [
            ts for ts in self.keystroke_buffer
            if current_time - ts <= self.monitoring_window
        ]
        
        if len(window_keystrokes) < 10:
            return False
            
        # Calculate WPM (assuming 5 characters per word)
        time_span = max(window_keystrokes) - min(window_keystrokes)
        if time_span > 0:
            characters_per_second = len(window_keystrokes) / time_span
            wpm = (characters_per_second * 60) / 5
            
            if wpm > self.wpm_threshold:
                self._handle_fast_typing_alert(wpm)
                return True
                
        return False
        
    def _handle_fast_typing_alert(self, wpm: float):
        """Handle fast typing detection."""
        current_time = time.time()
        
        # Reset alert count if enough time has passed
        if current_time - self.last_alert_time > 300:  # 5 minutes
            self.alert_count = 0
            
        self.alert_count += 1
        self.last_alert_time = current_time
        
        self.logger.warning(f"Fast typing detected: {wpm:.1f} WPM (threshold: {self.wpm_threshold})")
        
        if self.alert_count >= self.consecutive_alerts_to_lock:
            return "LOCK_SCREEN"
        else:
            return "ALERT"

class TabSwitchingDetector:
    """Detects excessive tab switching patterns."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.switches_per_minute_threshold = config.get('switches_per_minute_threshold', 20)
        self.monitoring_window = config.get('monitoring_window_seconds', 30)
        self.suspicious_threshold = config.get('suspicious_pattern_threshold', 5)
        
        self.tab_switches = deque(maxlen=200)
        self.alert_count = 0
        self.logger = logging.getLogger(__name__)
        
    def add_tab_switch(self, timestamp: float, from_tab: str, to_tab: str):
        """Add tab switch event."""
        self.tab_switches.append({
            'timestamp': timestamp,
            'from': from_tab,
            'to': to_tab
        })
        self._check_switching_pattern()
        
    def _check_switching_pattern(self):
        """Check for excessive tab switching."""
        current_time = time.time()
        
        # Get recent switches
        recent_switches = [
            switch for switch in self.tab_switches
            if current_time - switch['timestamp'] <= self.monitoring_window
        ]
        
        if len(recent_switches) < 5:
            return False
            
        # Calculate switches per minute
        time_span = self.monitoring_window / 60
        switches_per_minute = len(recent_switches) / time_span
        
        if switches_per_minute > self.switches_per_minute_threshold:
            return self._handle_excessive_switching(switches_per_minute)
            
        # Check for repetitive switching pattern
        if self._detect_repetitive_pattern(recent_switches):
            return self._handle_suspicious_pattern()
            
        return False
        
    def _detect_repetitive_pattern(self, switches: List[Dict]) -> bool:
        """Detect repetitive tab switching patterns."""
        if len(switches) < 6:
            return False
            
        # Look for A->B->A->B pattern
        patterns = []
        for i in range(len(switches) - 1):
            pattern = (switches[i]['from'], switches[i]['to'])
            patterns.append(pattern)
            
        # Count repeated patterns
        pattern_counts = {}
        for pattern in patterns:
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
            
        # Check if any pattern repeats too much
        max_repeats = max(pattern_counts.values()) if pattern_counts else 0
        return max_repeats >= self.suspicious_threshold
        
    def _handle_excessive_switching(self, rate: float):
        """Handle excessive tab switching."""
        self.alert_count += 1
        self.logger.warning(f"Excessive tab switching detected: {rate:.1f} switches/minute")
        
        if self.alert_count >= 2:
            return "LOCK_SCREEN"
        else:
            return "ALERT"
            
    def _handle_suspicious_pattern(self):
        """Handle suspicious switching pattern."""
        self.logger.warning("Suspicious tab switching pattern detected")
        return "LOCK_SCREEN"

class BiometricMonitor:
    """Monitors camera and microphone for additional security."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.camera_enabled = config.get('camera_enabled', True)
        self.microphone_enabled = config.get('microphone_enabled', True)
        self.face_recognition = config.get('face_recognition', True)
        
        self.camera = None
        self.is_monitoring = False
        self.last_face_detection = 0
        self.face_absent_threshold = 30  # seconds
        self.logger = logging.getLogger(__name__)
        
    def start_monitoring(self):
        """Start biometric monitoring."""
        if not self.camera_enabled:
            return False
            
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                self.logger.error("Camera not available")
                return False
                
            self.is_monitoring = True
            monitor_thread = threading.Thread(target=self._monitor_camera, daemon=True)
            monitor_thread.start()
            
            self.logger.info("Biometric monitoring started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start biometric monitoring: {e}")
            return False
            
    def stop_monitoring(self):
        """Stop biometric monitoring."""
        self.is_monitoring = False
        if self.camera:
            self.camera.release()
            self.camera = None
            
    def _monitor_camera(self):
        """Monitor camera for face detection."""
        face_cascade = None
        
        try:
            # Load OpenCV face detector
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        except Exception as e:
            self.logger.error(f"Failed to load face cascade: {e}")
            return
            
        while self.is_monitoring and self.camera:
            try:
                ret, frame = self.camera.read()
                if not ret:
                    continue
                    
                # Convert to grayscale for face detection
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Detect faces
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                
                current_time = time.time()
                
                if len(faces) > 0:
                    self.last_face_detection = current_time
                else:
                    # Check if face has been absent too long
                    if (current_time - self.last_face_detection > self.face_absent_threshold and
                        self.last_face_detection > 0):
                        self.logger.warning("User absence detected via camera")
                        # Could trigger security action here
                        
                time.sleep(1)  # Check every second
                
            except Exception as e:
                self.logger.error(f"Camera monitoring error: {e}")
                time.sleep(5)

class ScreenLockManager:
    """Manages screen locking and unlocking."""
    
    def __init__(self, auth_manager: UserAuthManager):
        self.auth_manager = auth_manager
        self.is_locked = False
        self.lock_window = None
        self.logger = logging.getLogger(__name__)
        
    def lock_screen(self, reason: str = "Security threat detected"):
        """Lock the screen immediately."""
        if self.is_locked:
            return
            
        self.is_locked = True
        self.logger.warning(f"Screen locked: {reason}")
        
        # Create lock screen window
        self._create_lock_screen(reason)
        
    def _create_lock_screen(self, reason: str):
        """Create full-screen lock window."""
        self.lock_window = tk.Toplevel()
        self.lock_window.title("System Locked")
        self.lock_window.attributes('-fullscreen', True)
        self.lock_window.attributes('-topmost', True)
        self.lock_window.configure(bg='black')
        
        # Disable window controls
        self.lock_window.protocol("WM_DELETE_WINDOW", lambda: None)
        self.lock_window.bind('<Alt-F4>', lambda e: "break")
        
        # Create lock screen UI
        main_frame = tk.Frame(self.lock_window, bg='black')
        main_frame.pack(expand=True, fill=tk.BOTH)
        
        # Warning message
        warning_label = tk.Label(
            main_frame,
            text="🔒 SYSTEM LOCKED",
            font=("Arial", 32, "bold"),
            fg="red",
            bg="black"
        )
        warning_label.pack(pady=50)
        
        reason_label = tk.Label(
            main_frame,
            text=f"Reason: {reason}",
            font=("Arial", 16),
            fg="white",
            bg="black"
        )
        reason_label.pack(pady=10)
        
        # PIN entry
        pin_frame = tk.Frame(main_frame, bg='black')
        pin_frame.pack(pady=50)
        
        tk.Label(
            pin_frame,
            text="Enter your PIN to unlock:",
            font=("Arial", 14),
            fg="white",
            bg="black"
        ).pack()
        
        self.pin_entry = tk.Entry(
            pin_frame,
            font=("Arial", 16),
            show="*",
            width=20,
            justify='center'
        )
        self.pin_entry.pack(pady=10)
        self.pin_entry.focus()
        
        unlock_button = tk.Button(
            pin_frame,
            text="Unlock",
            font=("Arial", 14),
            command=self._attempt_unlock,
            bg="darkblue",
            fg="white",
            width=15
        )
        unlock_button.pack(pady=10)
        
        # Bind Enter key
        self.pin_entry.bind('<Return>', lambda e: self._attempt_unlock())
        
        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="",
            font=("Arial", 12),
            fg="red",
            bg="black"
        )
        self.status_label.pack(pady=10)
        
    def _attempt_unlock(self):
        """Attempt to unlock with entered PIN."""
        if not self.auth_manager.current_user:
            self.status_label.config(text="No active user session")
            return
            
        pin = self.pin_entry.get()
        email = self.auth_manager.current_user["email"]
        
        success, message = self.auth_manager.login_user(email, pin)
        
        if success:
            self._unlock_screen()
        else:
            self.status_label.config(text=message)
            self.pin_entry.delete(0, tk.END)
            
    def _unlock_screen(self):
        """Unlock the screen."""
        self.is_locked = False
        
        if self.lock_window:
            self.lock_window.destroy()
            self.lock_window = None
            
        self.logger.info("Screen unlocked successfully")

class SecurityManager:
    """Main security manager coordinating all security components."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.auth_manager = UserAuthManager()
        self.fast_typing_detector = FastTypingDetector(config.get('fast_typing_detection', {}))
        self.tab_switch_detector = TabSwitchingDetector(config.get('tab_switching_detection', {}))
        self.biometric_monitor = BiometricMonitor(config.get('biometric_monitoring', {}))
        self.screen_lock_manager = ScreenLockManager(self.auth_manager)
        
        self.monitoring_active = False
        
    def start_security_monitoring(self):
        """Start all security monitoring."""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        
        # Start biometric monitoring
        if self.config.get('biometric_monitoring', {}).get('camera_enabled', True):
            self.biometric_monitor.start_monitoring()
            
        self.logger.info("Security monitoring started")
        
    def stop_security_monitoring(self):
        """Stop all security monitoring."""
        self.monitoring_active = False
        self.biometric_monitor.stop_monitoring()
        self.logger.info("Security monitoring stopped")
        
    def process_keystroke(self, timestamp: float, key: str):
        """Process keystroke for security analysis."""
        if not self.monitoring_active:
            return
            
        # Check fast typing
        result = self.fast_typing_detector.add_keystroke(timestamp)
        if result == "LOCK_SCREEN":
            self.screen_lock_manager.lock_screen("Fast typing detected (>300 WPM)")
            
    def process_tab_switch(self, timestamp: float, from_tab: str, to_tab: str):
        """Process tab switch for security analysis."""
        if not self.monitoring_active:
            return
            
        result = self.tab_switch_detector.add_tab_switch(timestamp, from_tab, to_tab)
        if result == "LOCK_SCREEN":
            self.screen_lock_manager.lock_screen("Excessive tab switching detected")
            
    def require_authentication(self) -> Tuple[bool, str]:
        """Check if user is authenticated."""
        if not self.auth_manager.session_active:
            return False, "Authentication required"
        return True, "User authenticated"
        
    def is_screen_locked(self) -> bool:
        """Check if screen is currently locked."""
        return self.screen_lock_manager.is_locked