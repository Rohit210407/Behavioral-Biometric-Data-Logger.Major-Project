"""
Background Service for Continuous Behavioral Authentication Monitoring.
Implements Windows service and daemon functionality for continuous operation.
"""

import os
import sys
import time
import signal
import logging
import threading
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

# Add src to path for imports
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

# Try absolute imports first, then relative imports
try:
    from src.core import BehavioralDataManager
    from src.security import SecurityManager  
    from src.ml import MLManager, FeatureExtractor
    from src.auth import AuthenticationManager
    from src.device import ContextValidator
except ImportError:
    # Fallback to relative imports
    from core import BehavioralDataManager
    from security import SecurityManager  
    from ml import MLManager, FeatureExtractor
    from auth import AuthenticationManager
    from device import ContextValidator

class BehaviorAuthService:
    """Main background service for behavioral authentication."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Service state
        self.is_running = False
        self.shutdown_event = threading.Event()
        
        # Initialize components
        self.auth_manager = None
        self.context_validator = None
        self.security_manager = None
        
        # Performance monitoring
        self.service_stats = {
            'start_time': 0,
            'uptime_seconds': 0,
            'sessions_handled': 0,
            'authentications_performed': 0,
            'last_heartbeat': 0
        }
        
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent.parent.parent
        return str(current_dir / 'config' / 'settings.yaml')
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"Failed to load config from {self.config_path}: {e}")
            return self._get_default_config()
            
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if file loading fails."""
        return {
            'app': {'name': 'Behavior Auth Service', 'debug': False, 'log_level': 'INFO'},
            'service': {'monitoring': {'interval_seconds': 1}},
            'logging': {'level': 'INFO', 'file': 'logs/service.log'}
        }
        
    def _setup_logging(self) -> None:
        """Setup service logging."""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        log_file = log_config.get('file', 'logs/service.log')
        
        # Create logs directory
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler() if self.config.get('app', {}).get('debug', False) else logging.NullHandler()
            ]
        )
        
    def start(self) -> bool:
        """Start the background service."""
        try:
            if self.is_running:
                self.logger.warning("Service already running")
                return False
                
            self.logger.info("Starting Behavioral Authentication Service")
            print("DEBUG: Starting Behavioral Authentication Service")
            
            # Initialize core components
            print("DEBUG: Initializing core components")
            self.auth_manager = AuthenticationManager(self.config)
            self.context_validator = ContextValidator(self.config)
            self.security_manager = self.auth_manager.security_manager
            print("DEBUG: Core components initialized")
            
            # Start security monitoring
            print("DEBUG: Starting security monitoring")
            self.security_manager.start_monitoring()
            print("DEBUG: Security monitoring started")
            
            # Load pre-trained ML models if available
            try:
                print("DEBUG: Loading pre-trained models")
                self.auth_manager.ml_manager.load_models()
                self.logger.info("Pre-trained models loaded successfully")
                print("DEBUG: Pre-trained models loaded successfully")
            except Exception as e:
                self.logger.warning(f"Could not load pre-trained models: {e}")
                print(f"DEBUG: Could not load pre-trained models: {e}")
                
            # Set service state
            self.is_running = True
            self.service_stats['start_time'] = int(time.time())
            
            # Start monitoring threads
            print("DEBUG: Starting monitoring threads")
            self._start_monitoring_threads()
            print("DEBUG: Monitoring threads started")
            
            self.logger.info("Behavioral Authentication Service started successfully")
            print("DEBUG: Behavioral Authentication Service started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start service: {e}")
            print(f"DEBUG: Failed to start service: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def stop(self) -> bool:
        """Stop the background service."""
        try:
            if not self.is_running:
                self.logger.warning("Service not running")
                return False
                
            self.logger.info("Stopping Behavioral Authentication Service")
            
            # Signal shutdown
            self.shutdown_event.set()
            self.is_running = False
            
            # Shutdown components
            if self.auth_manager:
                self.auth_manager.shutdown()
                
            self.logger.info("Behavioral Authentication Service stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping service: {e}")
            return False
            
    def _start_monitoring_threads(self) -> None:
        """Start background monitoring threads."""
        
        # Heartbeat thread
        heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
        # Statistics update thread
        stats_thread = threading.Thread(target=self._stats_update_loop, daemon=True)
        stats_thread.start()
        
        self.logger.info("Monitoring threads started")
        
    def _heartbeat_loop(self) -> None:
        """Background heartbeat for service health monitoring."""
        interval = self.config.get('service', {}).get('monitoring', {}).get('interval_seconds', 30)
        
        while self.is_running and not self.shutdown_event.is_set():
            try:
                self.service_stats['last_heartbeat'] = int(time.time())
                self.service_stats['uptime_seconds'] = int(time.time() - self.service_stats['start_time'])
                
                # Log heartbeat periodically
                if int(self.service_stats['uptime_seconds']) % 300 == 0:  # Every 5 minutes
                    self.logger.info(f"Service heartbeat - Uptime: {self.service_stats['uptime_seconds']}s")
                    
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Heartbeat error: {e}")
                time.sleep(interval)
                
    def _stats_update_loop(self) -> None:
        """Update service statistics periodically."""
        
        while self.is_running and not self.shutdown_event.is_set():
            try:
                if self.auth_manager:
                    # Get system metrics
                    metrics = self.auth_manager.get_system_metrics()
                    
                    # Update statistics
                    auth_stats = metrics.get('authentication_stats', {})
                    self.service_stats['authentications_performed'] = auth_stats.get('total_authentications', 0)
                    self.service_stats['sessions_handled'] = metrics.get('active_sessions', 0)
                    
                time.sleep(60)  # Update every minute
                
            except Exception as e:
                self.logger.error(f"Stats update error: {e}")
                time.sleep(60)
                
    def get_status(self) -> Dict[str, Any]:
        """Get current service status."""
        status = {
            'is_running': self.is_running,
            'service_stats': self.service_stats.copy(),
            'components': {}
        }
        
        if self.auth_manager:
            status['components']['auth_manager'] = True
            status['components']['security_monitoring'] = self.security_manager.monitoring_active if self.security_manager else False
            status['components']['ml_models'] = self.auth_manager.ml_manager.behavior_classifier.is_trained if hasattr(self.auth_manager.ml_manager, 'behavior_classifier') else False
            
        return status
        
    def create_user_session(self, user_id: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Create new user session through service."""
        try:
            if not self.auth_manager:
                self.logger.error("Auth manager not initialized")
                return None
                
            device_fingerprint = context.get('device_fingerprint') if context else None
            ip_address = context.get('ip_address') if context else None
            
            session_id = self.auth_manager.start_authentication_session(
                user_id, device_fingerprint, ip_address
            )
            
            if session_id:
                self.service_stats['sessions_handled'] += 1
                self.logger.info(f"Created session {session_id} for user {user_id}")
                
            return session_id
            
        except Exception as e:
            self.logger.error(f"Failed to create user session: {e}")
            return None
            
    def authenticate_user(self, session_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Perform user authentication through service."""
        try:
            if not self.auth_manager:
                return {'success': False, 'message': 'Service not initialized'}
                
            result = self.auth_manager.authenticate_continuously(session_id, context)
            self.service_stats['authentications_performed'] += 1
            
            return result.to_dict()
            
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return {'success': False, 'message': f'Authentication error: {e}'}

class ServiceManager:
    """Manages service lifecycle and provides control interface."""
    
    def __init__(self):
        self.service = None
        self.logger = logging.getLogger(__name__)
        
    def install_service(self) -> bool:
        """Install service for automatic startup (Windows)."""
        try:
            if os.name == 'nt':  # Windows
                # This would integrate with Windows Service Control Manager
                # For now, we'll create a simple startup script
                return self._create_startup_script()
            else:
                # Linux/Unix daemon installation
                return self._create_systemd_service()
                
        except Exception as e:
            self.logger.error(f"Service installation failed: {e}")
            return False
            
    def _create_startup_script(self) -> bool:
        """Create Windows startup script."""
        try:
            import winreg
            
            # Create batch file
            script_dir = Path(__file__).parent.parent.parent
            script_path = script_dir / 'scripts' / 'start_service.bat'
            
            os.makedirs(script_path.parent, exist_ok=True)
            
            with open(script_path, 'w') as f:
                f.write(f'@echo off\n')
                f.write(f'cd /d "{script_dir}"\n')
                f.write(f'python -m src.service.main\n')
                
            self.logger.info(f"Startup script created: {script_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Startup script creation failed: {e}")
            return False
            
    def _create_systemd_service(self) -> bool:
        """Create systemd service file for Linux."""
        try:
            service_content = f"""[Unit]
Description=Behavioral Authentication Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={Path(__file__).parent.parent.parent}
ExecStart=/usr/bin/python3 -m src.service.main
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""
            
            service_file = '/etc/systemd/system/behavior-auth.service'
            
            with open(service_file, 'w') as f:
                f.write(service_content)
                
            # Enable service
            os.system('systemctl daemon-reload')
            os.system('systemctl enable behavior-auth.service')
            
            self.logger.info("Systemd service created and enabled")
            return True
            
        except Exception as e:
            self.logger.error(f"Systemd service creation failed: {e}")
            return False
            
    def start_service(self, config_path: Optional[str] = None) -> bool:
        """Start the service."""
        try:
            self.service = BehaviorAuthService(config_path)
            return self.service.start()
        except Exception as e:
            self.logger.error(f"Failed to start service: {e}")
            return False
            
    def stop_service(self) -> bool:
        """Stop the service."""
        try:
            if self.service:
                return self.service.stop()
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop service: {e}")
            return False
            
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status."""
        if self.service:
            return self.service.get_status()
        return {'is_running': False, 'message': 'Service not initialized'}

# Global variable to store service manager
_service_manager = None

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    global _service_manager
    print(f"\nReceived signal {signum}. Shutting down gracefully...")
    if _service_manager:
        _service_manager.stop_service()
    sys.exit(0)

def main():
    """Main entry point for service."""
    global _service_manager
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create service manager
    _service_manager = ServiceManager()
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Behavioral Authentication Service')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--install', action='store_true', help='Install service')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    try:
        if args.install:
            print("Installing Behavioral Authentication Service...")
            success = _service_manager.install_service()
            if success:
                print("Service installed successfully")
            else:
                print("Service installation failed")
            return
            
        print("Starting Behavioral Authentication Service...")
        
        # Start service
        success = _service_manager.start_service(args.config)
        
        if not success:
            print("Failed to start service")
            return
            
        print("Service started successfully. Press Ctrl+C to stop.")
        
        # Keep service running
        try:
            while True:
                time.sleep(1)
                status = _service_manager.get_service_status()
                if not status.get('is_running', False):
                    break
        except KeyboardInterrupt:
            pass
            
        print("Stopping service...")
        _service_manager.stop_service()
        print("Service stopped")
        
    except Exception as e:
        print(f"Service error: {e}")
        
if __name__ == '__main__':
    main()