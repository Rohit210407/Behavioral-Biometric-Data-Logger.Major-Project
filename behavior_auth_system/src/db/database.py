#!/usr/bin/env python3
"""
Database module for storing user data, monitoring data, and system information.
"""

import sqlite3
import hashlib
import time
from datetime import datetime
from pathlib import Path

class DatabaseManager:
    """Manages all database operations for the behavioral authentication system."""
    
    def __init__(self, db_path="behavioral_auth.db"):
        """Initialize database connection and create tables if they don't exist."""
        self.db_path = db_path
        self.init_database()
        
    def get_connection(self):
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
        
    def init_database(self):
        """Initialize the database with required tables."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                pin_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                employee_id TEXT UNIQUE,
                department TEXT,
                role TEXT,
                phone TEXT,
                location TEXT,
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create monitoring_data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitoring_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                keystroke_count INTEGER DEFAULT 0,
                mouse_clicks INTEGER DEFAULT 0,
                mouse_moves INTEGER DEFAULT 0,
                behavioral_score REAL DEFAULT 95.0,
                session_start TIMESTAMP,
                session_end TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create keystroke_events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keystroke_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                key_pressed TEXT,
                key_code INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create mouse_events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mouse_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,  -- 'move' or 'click'
                x_position INTEGER,
                y_position INTEGER,
                button TEXT,  -- for click events
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create system_logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                log_level TEXT,
                message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create baseline_profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS baseline_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                typing_speed_avg REAL,
                typing_speed_std REAL,
                mouse_movement_avg REAL,
                mouse_click_rate REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Insert default user if not exists
        default_pin_hash = hashlib.sha256("123456".encode()).hexdigest()
        cursor.execute('''
            INSERT OR IGNORE INTO users 
            (email, pin_hash, name, employee_id, department, role, phone, location, last_login)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            "user@example.com",
            default_pin_hash,
            "John Doe",
            "EMP001",
            "Security",
            "Analyst",
            "+1-234-567-8900",
            "Building A, Floor 3",
            "2025-09-28 14:30:22"
        ))
        
        conn.commit()
        conn.close()
        
    def register_user(self, email, pin, name, employee_id=None, department="General", 
                     role="User", phone="", location=""):
        """Register a new user in the database."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            pin_hash = hashlib.sha256(pin.encode()).hexdigest()
            
            cursor.execute('''
                INSERT INTO users 
                (email, pin_hash, name, employee_id, department, role, phone, location)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (email, pin_hash, name, employee_id, department, role, phone, location))
            
            user_id = cursor.lastrowid
            conn.commit()
            return True, user_id
        except sqlite3.IntegrityError as e:
            if "email" in str(e).lower():
                return False, "Email already exists"
            elif "employee_id" in str(e).lower():
                return False, "Employee ID already exists"
            else:
                return False, "Registration failed"
        except Exception as e:
            return False, f"Registration error: {str(e)}"
        finally:
            conn.close()
            
    def authenticate_user(self, email, pin):
        """Authenticate a user by email and PIN."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            pin_hash = hashlib.sha256(pin.encode()).hexdigest()
            
            cursor.execute('''
                SELECT * FROM users WHERE email = ? AND pin_hash = ?
            ''', (email, pin_hash))
            
            user = cursor.fetchone()
            if user:
                # Update last login time
                cursor.execute('''
                    UPDATE users SET last_login = ? WHERE id = ?
                ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user['id']))
                conn.commit()
                return True, dict(user)
            else:
                return False, "Invalid email or PIN"
        except Exception as e:
            return False, f"Authentication error: {str(e)}"
        finally:
            conn.close()
            
    def get_user_by_email(self, email):
        """Get user information by email."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            return dict(user) if user else None
        except Exception as e:
            print(f"Error fetching user: {e}")
            return None
        finally:
            conn.close()
            
    def update_user_profile(self, user_id, **kwargs):
        """Update user profile information."""
        if not kwargs:
            return False, "No data to update"
            
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Build dynamic update query
            fields = []
            values = []
            for key, value in kwargs.items():
                if key in ['name', 'employee_id', 'department', 'role', 'phone', 'location']:
                    fields.append(f"{key} = ?")
                    values.append(value)
                    
            if not fields:
                return False, "No valid fields to update"
                
            values.append(user_id)
            query = f"UPDATE users SET {', '.join(fields)} WHERE id = ?"
            
            cursor.execute(query, values)
            conn.commit()
            
            if cursor.rowcount > 0:
                return True, "Profile updated successfully"
            else:
                return False, "No changes made"
        except Exception as e:
            return False, f"Update error: {str(e)}"
        finally:
            conn.close()
            
    def log_monitoring_data(self, user_id, keystroke_count=0, mouse_clicks=0, 
                           mouse_moves=0, behavioral_score=95.0, session_start=None, session_end=None):
        """Log monitoring data for a user."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO monitoring_data 
                (user_id, keystroke_count, mouse_clicks, mouse_moves, behavioral_score, session_start, session_end)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, keystroke_count, mouse_clicks, mouse_moves, behavioral_score, session_start, session_end))
            
            conn.commit()
            return True, cursor.lastrowid
        except Exception as e:
            return False, f"Logging error: {str(e)}"
        finally:
            conn.close()
            
    def log_keystroke_event(self, user_id, key_pressed, key_code=None):
        """Log a keystroke event."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO keystroke_events (user_id, key_pressed, key_code)
                VALUES (?, ?, ?)
            ''', (user_id, key_pressed, key_code))
            
            conn.commit()
            return True, cursor.lastrowid
        except Exception as e:
            return False, f"Keystroke logging error: {str(e)}"
        finally:
            conn.close()
            
    def log_mouse_event(self, user_id, event_type, x_position, y_position, button=None):
        """Log a mouse event."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO mouse_events (user_id, event_type, x_position, y_position, button)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, event_type, x_position, y_position, button))
            
            conn.commit()
            return True, cursor.lastrowid
        except Exception as e:
            return False, f"Mouse event logging error: {str(e)}"
        finally:
            conn.close()
            
    def log_system_event(self, user_id, log_level, message):
        """Log a system event."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO system_logs (user_id, log_level, message)
                VALUES (?, ?, ?)
            ''', (user_id, log_level, message))
            
            conn.commit()
            return True, cursor.lastrowid
        except Exception as e:
            return False, f"System event logging error: {str(e)}"
        finally:
            conn.close()
