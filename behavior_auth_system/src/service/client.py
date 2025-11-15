"""
Client API for interacting with the Behavioral Authentication Service.
Provides simple interface for applications to integrate behavioral authentication.
"""

import time
import threading
import queue
from typing import Dict, Any, Optional, Callable
import logging

from .main import BehaviorAuthService

class BehaviorAuthClient:
    """Client interface for behavioral authentication service."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.service = BehaviorAuthService(config_path)
        self.logger = logging.getLogger(__name__)
        self.is_connected = False
        
        # Callback management
        self.auth_callbacks: Dict[str, Callable] = {}
        self.session_callbacks: Dict[str, Callable] = {}
        
        # Event queues
        self.auth_events = queue.Queue()
        self.session_events = queue.Queue()
        
    def connect(self) -> bool:
        """Connect to the authentication service."""
        try:
            if not self.service.start():
                return False
                
            self.is_connected = True
            self.logger.info("Connected to behavioral authentication service")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to service: {e}")
            return False
            
    def disconnect(self) -> bool:
        """Disconnect from the service."""
        try:
            if self.service:
                self.service.stop()
            self.is_connected = False
            self.logger.info("Disconnected from behavioral authentication service")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disconnecting: {e}")
            return False
            
    def create_session(self, user_id: str, device_info: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Create a new authentication session for a user."""
        try:
            if not self.is_connected:
                self.logger.error("Not connected to service")
                return None
                
            context = {}
            if device_info:
                context.update(device_info)
                
            session_id = self.service.create_user_session(user_id, context)
            
            if session_id:
                self.logger.info(f"Created session {session_id} for user {user_id}")
                self._notify_session_event('session_created', {
                    'session_id': session_id,
                    'user_id': user_id,
                    'timestamp': time.time()
                })
                
            return session_id
            
        except Exception as e:
            self.logger.error(f"Failed to create session: {e}")
            return None
            
    def authenticate(self, session_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Perform behavioral authentication for a session."""
        try:
            if not self.is_connected:
                return {'success': False, 'message': 'Not connected to service'}
                
            result = self.service.authenticate_user(session_id, context)
            
            # Notify callbacks
            self._notify_auth_event('authentication_result', {
                'session_id': session_id,
                'result': result,
                'timestamp': time.time()
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return {'success': False, 'message': f'Authentication error: {e}'}
            
    def end_session(self, session_id: str) -> bool:
        """End an authentication session."""
        try:
            if not self.is_connected or not self.service.auth_manager:
                return False
                
            success = self.service.auth_manager.end_session(session_id)
            
            if success:
                self._notify_session_event('session_ended', {
                    'session_id': session_id,
                    'timestamp': time.time()
                })
                
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to end session: {e}")
            return False
            
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an authentication session."""
        try:
            if not self.is_connected or not self.service.auth_manager:
                return None
                
            return self.service.auth_manager.get_session_status(session_id)
            
        except Exception as e:
            self.logger.error(f"Failed to get session status: {e}")
            return None
            
    def register_auth_callback(self, callback_id: str, callback: Callable) -> None:
        """Register callback for authentication events."""
        self.auth_callbacks[callback_id] = callback
        
    def register_session_callback(self, callback_id: str, callback: Callable) -> None:
        """Register callback for session events."""
        self.session_callbacks[callback_id] = callback
        
    def unregister_callback(self, callback_id: str) -> None:
        """Unregister a callback."""
        self.auth_callbacks.pop(callback_id, None)
        self.session_callbacks.pop(callback_id, None)
        
    def get_service_status(self) -> Dict[str, Any]:
        """Get overall service status."""
        try:
            if not self.service:
                return {'is_running': False, 'message': 'Service not initialized'}
                
            return self.service.get_status()
            
        except Exception as e:
            self.logger.error(f"Failed to get service status: {e}")
            return {'is_running': False, 'error': str(e)}
            
    def _notify_auth_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Notify authentication event callbacks."""
        event = {
            'type': event_type,
            'data': data,
            'timestamp': time.time()
        }
        
        # Add to event queue
        try:
            self.auth_events.put_nowait(event)
        except queue.Full:
            self.logger.warning("Auth event queue full, dropping event")
            
        # Notify callbacks
        for callback_id, callback in self.auth_callbacks.items():
            try:
                callback(event)
            except Exception as e:
                self.logger.error(f"Auth callback {callback_id} error: {e}")
                
    def _notify_session_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Notify session event callbacks."""
        event = {
            'type': event_type,
            'data': data,
            'timestamp': time.time()
        }
        
        # Add to event queue
        try:
            self.session_events.put_nowait(event)
        except queue.Full:
            self.logger.warning("Session event queue full, dropping event")
            
        # Notify callbacks
        for callback_id, callback in self.session_callbacks.items():
            try:
                callback(event)
            except Exception as e:
                self.logger.error(f"Session callback {callback_id} error: {e}")

class SimpleBehaviorAuth:
    """Simplified interface for basic behavioral authentication."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.client = BehaviorAuthClient(config_path)
        self.current_session_id = None
        self.current_user_id = None
        
    def start_authentication(self, user_id: str, device_info: Optional[Dict[str, Any]] = None) -> bool:
        """Start behavioral authentication for a user."""
        try:
            # Connect to service
            if not self.client.connect():
                return False
                
            # Create session
            session_id = self.client.create_session(user_id, device_info)
            if not session_id:
                return False
                
            self.current_session_id = session_id
            self.current_user_id = user_id
            return True
            
        except Exception as e:
            print(f"Failed to start authentication: {e}")
            return False
            
    def check_authentication(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Check current authentication status."""
        if not self.current_session_id:
            return {'success': False, 'message': 'No active session'}
            
        return self.client.authenticate(self.current_session_id, context)
        
    def stop_authentication(self) -> bool:
        """Stop behavioral authentication."""
        try:
            if self.current_session_id:
                self.client.end_session(self.current_session_id)
                self.current_session_id = None
                self.current_user_id = None
                
            self.client.disconnect()
            return True
            
        except Exception as e:
            print(f"Failed to stop authentication: {e}")
            return False
            
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        if not self.current_session_id:
            return False
            
        result = self.check_authentication()
        return result.get('success', False) and result.get('decision') in ['continue', 'monitor']

# Example usage functions
def example_basic_usage():
    """Example of basic behavioral authentication usage."""
    
    # Create simple auth instance
    auth = SimpleBehaviorAuth()
    
    # Start authentication for user
    user_id = "user123"
    device_info = {
        'device_fingerprint': 'device123',
        'ip_address': '192.168.1.100'
    }
    
    if auth.start_authentication(user_id, device_info):
        print(f"Started authentication for {user_id}")
        
        # Simulate periodic authentication checks
        for i in range(5):
            time.sleep(2)  # Wait for behavioral data collection
            
            result = auth.check_authentication()
            print(f"Authentication check {i+1}: {result.get('decision', 'unknown')}")
            
            if not auth.is_authenticated():
                print("Authentication failed - stopping")
                break
                
        # Stop authentication
        auth.stop_authentication()
        print("Authentication stopped")
    else:
        print("Failed to start authentication")

def example_advanced_usage():
    """Example of advanced behavioral authentication usage with callbacks."""
    
    # Create client with callbacks
    client = BehaviorAuthClient()
    
    # Define callback functions
    def auth_callback(event):
        print(f"Auth event: {event['type']} - {event['data']}")
        
    def session_callback(event):
        print(f"Session event: {event['type']} - {event['data']}")
        
    # Register callbacks
    client.register_auth_callback('main_auth', auth_callback)
    client.register_session_callback('main_session', session_callback)
    
    # Connect and create session
    if client.connect():
        session_id = client.create_session("user456", {'device': 'laptop'})
        
        if session_id:
            # Perform multiple authentications
            for i in range(3):
                time.sleep(3)
                result = client.authenticate(session_id)
                print(f"Authentication {i+1}: {result}")
                
            # End session and disconnect
            client.end_session(session_id)
            client.disconnect()

if __name__ == '__main__':
    # Run example
    print("Running basic usage example...")
    example_basic_usage()
    
    print("\n" + "="*50 + "\n")
    
    print("Running advanced usage example...")
    example_advanced_usage()