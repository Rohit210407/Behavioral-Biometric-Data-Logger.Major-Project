"""
MongoDB Manager for Behavioral Authentication System
Handles user registration, authentication, and activity storage.
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
import hashlib
import secrets
import json
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDBManager:
    """MongoDB manager for user data and activity tracking."""
    
    def __init__(self, connection_string: str = "mongodb://localhost:27017/", database_name: str = "behavioral_auth"):
        """
        Initialize MongoDB connection.
        
        Args:
            connection_string: MongoDB connection string
            database_name: Name of the database to use
        """
        try:
            self.client = MongoClient(connection_string)
            self.db = self.client[database_name]
            
            # Collections
            self.users_collection = self.db.users
            self.activities_collection = self.db.user_activities
            self.sessions_collection = self.db.user_sessions
            self.behavioral_data_collection = self.db.behavioral_data
            
            # Create indexes for better performance
            self._create_indexes()
            
            logger.info(f"✅ Connected to MongoDB: {database_name}")
            
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise
    
    def _create_indexes(self):
        """Create database indexes for better performance."""
        try:
            # User collection indexes
            self.users_collection.create_index("email", unique=True)
            self.users_collection.create_index("created_at")
            
            # Activity collection indexes
            self.activities_collection.create_index([("user_id", 1), ("timestamp", -1)])
            self.activities_collection.create_index("session_id")
            
            # Session collection indexes
            self.sessions_collection.create_index([("user_id", 1), ("start_time", -1)])
            self.sessions_collection.create_index("session_id", unique=True)
            
            # Behavioral data indexes
            self.behavioral_data_collection.create_index([("user_id", 1), ("timestamp", -1)])
            
            logger.info("✅ Database indexes created")
            
        except Exception as e:
            logger.error(f"❌ Index creation failed: {e}")
    
    def _hash_pin(self, pin: str, salt: str = None) -> Tuple[str, str]:
        """
        Hash PIN with salt for secure storage.
        
        Args:
            pin: User's PIN
            salt: Salt for hashing (generates new if None)
            
        Returns:
            Tuple of (hashed_pin, salt)
        """
        if salt is None:
            salt = secrets.token_hex(32)
        
        # Combine PIN and salt, then hash
        combined = f"{pin}{salt}"
        hashed = hashlib.sha256(combined.encode()).hexdigest()
        
        return hashed, salt
    
    def register_user(self, email: str, pin: str, additional_data: Dict = None) -> Tuple[bool, str]:
        """
        Register a new user.
        
        Args:
            email: User's email address
            pin: User's security PIN
            additional_data: Additional user data
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Check if user already exists
            if self.users_collection.find_one({"email": email}):
                return False, "User already exists"
            
            # Validate PIN
            if len(pin) < 6:
                return False, "PIN must be at least 6 characters"
            
            # Hash the PIN
            hashed_pin, salt = self._hash_pin(pin)
            
            # Create user document
            user_doc = {
                "email": email,
                "pin_hash": hashed_pin,
                "salt": salt,
                "created_at": datetime.now(),
                "last_login": None,
                "login_count": 0,
                "is_active": True,
                "preferences": {
                    "monitoring_enabled": True,
                    "notifications_enabled": True,
                    "data_retention_days": 90
                }
            }
            
            # Add additional data if provided
            if additional_data:
                user_doc.update(additional_data)
            
            # Insert user
            result = self.users_collection.insert_one(user_doc)
            
            logger.info(f"✅ User registered: {email}")
            return True, f"User registered successfully with ID: {result.inserted_id}"
            
        except Exception as e:
            logger.error(f"❌ User registration failed: {e}")
            return False, f"Registration failed: {str(e)}"
    
    def authenticate_user(self, email: str, pin: str) -> Tuple[bool, Optional[Dict]]:
        """
        Authenticate user login.
        
        Args:
            email: User's email
            pin: User's PIN
            
        Returns:
            Tuple of (success, user_data)
        """
        try:
            # Find user
            user = self.users_collection.find_one({"email": email, "is_active": True})
            if not user:
                return False, None
            
            # Verify PIN
            hashed_pin, _ = self._hash_pin(pin, user["salt"])
            if hashed_pin != user["pin_hash"]:
                return False, None
            
            # Update login stats
            self.users_collection.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {"last_login": datetime.now()},
                    "$inc": {"login_count": 1}
                }
            )
            
            # Remove sensitive data from returned user
            user_data = {
                "user_id": str(user["_id"]),
                "email": user["email"],
                "created_at": user["created_at"],
                "last_login": datetime.now(),
                "login_count": user["login_count"] + 1,
                "preferences": user.get("preferences", {})
            }
            
            logger.info(f"✅ User authenticated: {email}")
            return True, user_data
            
        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")
            return False, None
    
    def create_session(self, user_id: str) -> str:
        """
        Create a new user session.
        
        Args:
            user_id: User's ID
            
        Returns:
            Session ID
        """
        try:
            session_id = secrets.token_urlsafe(32)
            
            session_doc = {
                "session_id": session_id,
                "user_id": user_id,
                "start_time": datetime.now(),
                "end_time": None,
                "is_active": True,
                "activities_count": 0,
                "behavioral_events": 0
            }
            
            self.sessions_collection.insert_one(session_doc)
            
            logger.info(f"✅ Session created: {session_id} for user {user_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"❌ Session creation failed: {e}")
            return None
    
    def end_session(self, session_id: str):
        """
        End a user session.
        
        Args:
            session_id: Session ID to end
        """
        try:
            self.sessions_collection.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "end_time": datetime.now(),
                        "is_active": False
                    }
                }
            )
            
            logger.info(f"✅ Session ended: {session_id}")
            
        except Exception as e:
            logger.error(f"❌ Session end failed: {e}")
    
    def log_activity(self, user_id: str, session_id: str, activity_type: str, activity_data: Dict):
        """
        Log user activity.
        
        Args:
            user_id: User's ID
            session_id: Current session ID
            activity_type: Type of activity (keystroke, mouse, window, etc.)
            activity_data: Activity details
        """
        try:
            activity_doc = {
                "user_id": user_id,
                "session_id": session_id,
                "activity_type": activity_type,
                "timestamp": datetime.now(),
                "data": activity_data
            }
            
            self.activities_collection.insert_one(activity_doc)
            
            # Update session activity count
            self.sessions_collection.update_one(
                {"session_id": session_id},
                {"$inc": {"activities_count": 1}}
            )
            
        except Exception as e:
            logger.error(f"❌ Activity logging failed: {e}")
    
    def store_behavioral_data(self, user_id: str, session_id: str, behavioral_metrics: Dict):
        """
        Store behavioral analysis data.
        
        Args:
            user_id: User's ID
            session_id: Current session ID
            behavioral_metrics: Behavioral analysis results
        """
        try:
            behavioral_doc = {
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.now(),
                "metrics": behavioral_metrics,
                "analysis_version": "1.0"
            }
            
            self.behavioral_data_collection.insert_one(behavioral_doc)
            
            # Update session behavioral events count
            self.sessions_collection.update_one(
                {"session_id": session_id},
                {"$inc": {"behavioral_events": 1}}
            )
            
        except Exception as e:
            logger.error(f"❌ Behavioral data storage failed: {e}")
    
    def get_user_activities(self, user_id: str, limit: int = 100) -> List[Dict]:
        """
        Get user's recent activities.
        
        Args:
            user_id: User's ID
            limit: Maximum number of activities to return
            
        Returns:
            List of activity documents
        """
        try:
            activities = self.activities_collection.find(
                {"user_id": user_id}
            ).sort("timestamp", -1).limit(limit)
            
            return list(activities)
            
        except Exception as e:
            logger.error(f"❌ Failed to get user activities: {e}")
            return []
    
    def get_user_sessions(self, user_id: str, limit: int = 10) -> List[Dict]:
        """
        Get user's recent sessions.
        
        Args:
            user_id: User's ID
            limit: Maximum number of sessions to return
            
        Returns:
            List of session documents
        """
        try:
            sessions = self.sessions_collection.find(
                {"user_id": user_id}
            ).sort("start_time", -1).limit(limit)
            
            return list(sessions)
            
        except Exception as e:
            logger.error(f"❌ Failed to get user sessions: {e}")
            return []
    
    def get_behavioral_patterns(self, user_id: str, days: int = 30) -> List[Dict]:
        """
        Get user's behavioral patterns over specified days.
        
        Args:
            user_id: User's ID
            days: Number of days to look back
            
        Returns:
            List of behavioral data documents
        """
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            patterns = self.behavioral_data_collection.find(
                {
                    "user_id": user_id,
                    "timestamp": {"$gte": start_date}
                }
            ).sort("timestamp", -1)
            
            return list(patterns)
            
        except Exception as e:
            logger.error(f"❌ Failed to get behavioral patterns: {e}")
            return []
    
    def update_user_preferences(self, user_id: str, preferences: Dict) -> bool:
        """
        Update user preferences.
        
        Args:
            user_id: User's ID
            preferences: New preference settings
            
        Returns:
            Success status
        """
        try:
            result = self.users_collection.update_one(
                {"_id": user_id},
                {"$set": {"preferences": preferences}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"❌ Failed to update preferences: {e}")
            return False
    
    def get_user_stats(self, user_id: str) -> Dict:
        """
        Get comprehensive user statistics.
        
        Args:
            user_id: User's ID
            
        Returns:
            Dictionary with user statistics
        """
        try:
            # Get user info
            user = self.users_collection.find_one({"_id": user_id})
            if not user:
                return {}
            
            # Count activities
            total_activities = self.activities_collection.count_documents({"user_id": user_id})
            
            # Count sessions
            total_sessions = self.sessions_collection.count_documents({"user_id": user_id})
            
            # Get recent session
            recent_session = self.sessions_collection.find_one(
                {"user_id": user_id},
                sort=[("start_time", -1)]
            )
            
            # Count behavioral events
            behavioral_events = self.behavioral_data_collection.count_documents({"user_id": user_id})
            
            stats = {
                "email": user["email"],
                "member_since": user["created_at"],
                "last_login": user.get("last_login"),
                "login_count": user.get("login_count", 0),
                "total_activities": total_activities,
                "total_sessions": total_sessions,
                "behavioral_events": behavioral_events,
                "recent_session": recent_session
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get user stats: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = 90):
        """
        Clean up old data based on retention policy.
        
        Args:
            days: Number of days to retain data
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Clean old activities
            result1 = self.activities_collection.delete_many({"timestamp": {"$lt": cutoff_date}})
            
            # Clean old behavioral data
            result2 = self.behavioral_data_collection.delete_many({"timestamp": {"$lt": cutoff_date}})
            
            # Clean old sessions
            result3 = self.sessions_collection.delete_many({"start_time": {"$lt": cutoff_date}})
            
            logger.info(f"✅ Cleanup completed: {result1.deleted_count} activities, {result2.deleted_count} behavioral records, {result3.deleted_count} sessions")
            
        except Exception as e:
            logger.error(f"❌ Data cleanup failed: {e}")
    
    def close_connection(self):
        """Close MongoDB connection."""
        try:
            self.client.close()
            logger.info("✅ MongoDB connection closed")
        except Exception as e:
            logger.error(f"❌ Error closing connection: {e}")

# Example usage and testing
if __name__ == "__main__":
    # Test the MongoDB manager
    try:
        # Initialize manager
        mongo_manager = MongoDBManager()
        
        # Test user registration
        success, message = mongo_manager.register_user(
            email="test@example.com",
            pin="123456",
            additional_data={"full_name": "Test User"}
        )
        print(f"Registration: {success}, {message}")
        
        # Test authentication
        auth_success, user_data = mongo_manager.authenticate_user("test@example.com", "123456")
        print(f"Authentication: {auth_success}")
        if user_data:
            print(f"User data: {user_data}")
            
            # Test session creation
            session_id = mongo_manager.create_session(user_data["user_id"])
            print(f"Session created: {session_id}")
            
            # Test activity logging
            mongo_manager.log_activity(
                user_data["user_id"],
                session_id,
                "keystroke",
                {"key": "a", "timestamp": datetime.now().isoformat()}
            )
            
            # Test behavioral data storage
            mongo_manager.store_behavioral_data(
                user_data["user_id"],
                session_id,
                {"typing_speed": 45, "mouse_clicks": 10, "risk_score": 0.1}
            )
            
            # Get user stats
            stats = mongo_manager.get_user_stats(user_data["user_id"])
            print(f"User stats: {stats}")
        
    except Exception as e:
        print(f"Test failed: {e}")