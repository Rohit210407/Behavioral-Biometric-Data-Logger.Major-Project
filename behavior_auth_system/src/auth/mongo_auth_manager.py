"""
MongoDB-integrated Authentication Manager
Replaces the simple auth manager with MongoDB persistence.
"""

import sys
import os
from pathlib import Path
from typing import Dict, Optional, Tuple
import time
import threading

# Add database path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

try:
    from database.mongo_manager import MongoDBManager
except ImportError:
    print("Warning: MongoDB manager not available, using fallback")
    MongoDBManager = None

class MongoAuthManager:
    """Enhanced authentication manager with MongoDB integration."""
    
    def __init__(self, mongo_connection: str = "mongodb://localhost:27017/"):
        """
        Initialize with MongoDB connection.
        
        Args:
            mongo_connection: MongoDB connection string
        """
        self.current_user = None
        self.current_session = None
        self.activity_buffer = []
        self.buffer_lock = threading.Lock()
        
        # Initialize MongoDB manager
        try:
            if MongoDBManager:
                self.mongo_manager = MongoDBManager(mongo_connection)
                self.is_connected = True
                print("✅ MongoDB authentication manager initialized")
            else:
                raise ImportError("MongoDB manager not available")
                
        except Exception as e:
            print(f"⚠️ MongoDB connection failed, using fallback: {e}")
            self.mongo_manager = None
            self.is_connected = False
            # Fallback to simple in-memory storage
            self.users = {"test@example.com": "123456"}
    
    def register_user(self, email: str, pin: str, additional_data: Dict = None) -> Tuple[bool, str]:
        """
        Register a new user with MongoDB persistence.
        
        Args:
            email: User's email address
            pin: User's security PIN
            additional_data: Additional user information
            
        Returns:
            Tuple of (success, message)
        """
        if self.is_connected:
            return self.mongo_manager.register_user(email, pin, additional_data)
        else:
            # Fallback registration
            if email in self.users:
                return False, "User already exists"
            if len(pin) < 6:
                return False, "PIN must be at least 6 characters"
            self.users[email] = pin
            return True, "Registration successful (using fallback storage)"
    
    def login_user(self, email: str, pin: str) -> Tuple[bool, str]:
        """
        Authenticate user and create session.
        
        Args:
            email: User's email
            pin: User's PIN
            
        Returns:
            Tuple of (success, message)
        """
        if self.is_connected:
            # MongoDB authentication
            success, user_data = self.mongo_manager.authenticate_user(email, pin)
            if success:
                self.current_user = user_data
                # Create session
                session_id = self.mongo_manager.create_session(user_data["user_id"])
                self.current_session = {
                    "session_id": session_id,
                    "user_id": user_data["user_id"],
                    "start_time": time.time()
                }
                # Start activity buffer flushing
                self._start_activity_flusher()
                return True, "Login successful"
            else:
                return False, "Invalid email or PIN"
        else:
            # Fallback authentication
            if email not in self.users:
                return False, "Invalid email or PIN"
            if self.users[email] != pin:
                return False, "Invalid email or PIN"
            self.current_user = {"email": email, "user_id": email}
            return True, "Login successful (using fallback storage)"
    
    def logout_user(self):
        """Logout current user and end session."""
        if self.is_connected and self.current_session:
            # End MongoDB session
            self.mongo_manager.end_session(self.current_session["session_id"])
            # Flush remaining activities
            self._flush_activity_buffer()
        
        self.current_user = None
        self.current_session = None
    
    def log_activity(self, activity_type: str, activity_data: Dict):
        """
        Log user activity to MongoDB.
        
        Args:
            activity_type: Type of activity (keystroke, mouse, window, etc.)
            activity_data: Activity details
        """
        if not self.current_user:
            return
        
        if self.is_connected and self.current_session:
            # Add to buffer for batch processing
            activity = {
                "user_id": self.current_user["user_id"],
                "session_id": self.current_session["session_id"],
                "activity_type": activity_type,
                "data": activity_data,
                "timestamp": time.time()
            }
            
            with self.buffer_lock:
                self.activity_buffer.append(activity)
    
    def store_behavioral_metrics(self, metrics: Dict):
        """
        Store behavioral analysis metrics.
        
        Args:
            metrics: Behavioral analysis results
        """
        if not self.current_user or not self.is_connected:
            return
        
        if self.current_session:
            self.mongo_manager.store_behavioral_data(
                self.current_user["user_id"],
                self.current_session["session_id"],
                metrics
            )
    
    def get_user_history(self, days: int = 7) -> Dict:
        """
        Get user's activity history.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary with user history data
        """
        if not self.current_user or not self.is_connected:
            return {"activities": [], "sessions": [], "behavioral_data": []}
        
        user_id = self.current_user["user_id"]
        
        return {
            "activities": self.mongo_manager.get_user_activities(user_id, limit=200),
            "sessions": self.mongo_manager.get_user_sessions(user_id, limit=10),
            "behavioral_data": self.mongo_manager.get_behavioral_patterns(user_id, days=days)
        }
    
    def get_user_stats(self) -> Dict:
        """
        Get current user's statistics.
        
        Returns:
            Dictionary with user statistics
        """
        if not self.current_user:
            return {}
        
        if self.is_connected:
            return self.mongo_manager.get_user_stats(self.current_user["user_id"])
        else:
            return {
                "email": self.current_user["email"],
                "login_count": 1,
                "total_activities": 0,
                "storage_type": "fallback"
            }
    
    def update_user_preferences(self, preferences: Dict) -> bool:
        """
        Update user preferences.
        
        Args:
            preferences: New preference settings
            
        Returns:
            Success status
        """
        if not self.current_user or not self.is_connected:
            return False
        
        return self.mongo_manager.update_user_preferences(
            self.current_user["user_id"],
            preferences
        )
    
    def _start_activity_flusher(self):
        """Start background thread to flush activity buffer periodically."""
        def flush_periodically():
            while self.current_session:
                time.sleep(5)  # Flush every 5 seconds
                self._flush_activity_buffer()
        
        flush_thread = threading.Thread(target=flush_periodically, daemon=True)
        flush_thread.start()
    
    def _flush_activity_buffer(self):
        """Flush buffered activities to MongoDB."""
        if not self.is_connected or not self.activity_buffer:
            return
        
        with self.buffer_lock:
            activities_to_flush = self.activity_buffer.copy()
            self.activity_buffer.clear()
        
        # Batch insert activities
        for activity in activities_to_flush:
            try:
                self.mongo_manager.log_activity(
                    activity["user_id"],
                    activity["session_id"],
                    activity["activity_type"],
                    activity["data"]
                )
            except Exception as e:
                print(f"Failed to log activity: {e}")
    
    def get_connection_status(self) -> Dict:
        """
        Get connection status information.
        
        Returns:
            Dictionary with connection details
        """
        return {
            "mongodb_connected": self.is_connected,
            "current_user": self.current_user["email"] if self.current_user else None,
            "session_active": bool(self.current_session),
            "activities_buffered": len(self.activity_buffer) if self.activity_buffer else 0
        }
    
    def close(self):
        """Close all connections and clean up."""
        if self.current_session:
            self.logout_user()
        
        if self.is_connected and self.mongo_manager:
            self.mongo_manager.close_connection()

# Fallback simple auth manager for cases where MongoDB is not available
class SimpleAuthManager:
    """Simple fallback authentication manager."""
    
    def __init__(self):
        self.users = {"test@example.com": "123456"}
        self.current_user = None
    
    def register_user(self, email: str, pin: str, additional_data: Dict = None) -> Tuple[bool, str]:
        if email in self.users:
            return False, "User already exists"
        if len(pin) < 6:
            return False, "PIN must be at least 6 characters"
        self.users[email] = pin
        return True, "Registration successful"
    
    def login_user(self, email: str, pin: str) -> Tuple[bool, str]:
        if email not in self.users:
            return False, "Invalid email or PIN"
        if self.users[email] != pin:
            return False, "Invalid email or PIN"
        self.current_user = {"email": email}
        return True, "Login successful"
    
    def log_activity(self, activity_type: str, activity_data: Dict):
        pass  # No-op for simple manager
    
    def store_behavioral_metrics(self, metrics: Dict):
        pass  # No-op for simple manager
    
    def get_user_history(self, days: int = 7) -> Dict:
        return {"activities": [], "sessions": [], "behavioral_data": []}
    
    def get_user_stats(self) -> Dict:
        return {"email": self.current_user["email"]} if self.current_user else {}
    
    def get_connection_status(self) -> Dict:
        return {
            "mongodb_connected": False,
            "current_user": self.current_user["email"] if self.current_user else None,
            "session_active": False,
            "activities_buffered": 0
        }
    
    def close(self):
        pass

# Factory function to create appropriate auth manager
def create_auth_manager(use_mongodb: bool = True, mongo_connection: str = "mongodb://localhost:27017/") -> object:
    """
    Create appropriate authentication manager.
    
    Args:
        use_mongodb: Whether to try MongoDB integration
        mongo_connection: MongoDB connection string
        
    Returns:
        Authentication manager instance
    """
    if use_mongodb:
        try:
            return MongoAuthManager(mongo_connection)
        except Exception as e:
            print(f"⚠️ MongoDB auth manager failed, using simple manager: {e}")
            return SimpleAuthManager()
    else:
        return SimpleAuthManager()

# Example usage
if __name__ == "__main__":
    # Test MongoDB auth manager
    auth_manager = create_auth_manager(use_mongodb=True)
    
    print("Connection status:", auth_manager.get_connection_status())
    
    # Test registration
    success, message = auth_manager.register_user("demo@test.com", "password123")
    print(f"Registration: {success}, {message}")
    
    # Test login
    success, message = auth_manager.login_user("demo@test.com", "password123")
    print(f"Login: {success}, {message}")
    
    if success:
        # Test activity logging
        auth_manager.log_activity("keystroke", {"key": "hello", "speed": 45})
        auth_manager.log_activity("mouse", {"x": 100, "y": 200, "clicks": 1})
        
        # Test behavioral metrics
        auth_manager.store_behavioral_metrics({
            "typing_speed": 45,
            "mouse_velocity": 1.2,
            "risk_score": 0.1
        })
        
        # Get user stats
        stats = auth_manager.get_user_stats()
        print("User stats:", stats)
        
        # Logout
        auth_manager.logout_user()
    
    # Clean up
    auth_manager.close()