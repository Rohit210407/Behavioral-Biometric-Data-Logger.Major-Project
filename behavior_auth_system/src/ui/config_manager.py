"""
Configuration Management for Behavioral Authentication System.
Provides centralized configuration loading, validation, and management.
"""

import os
import yaml
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, asdict

@dataclass
class ConfigValidationResult:
    """Result of configuration validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
class ConfigManager:
    """Manages application configuration with validation and defaults."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path or self._get_default_config_path()
        self.config = {}
        self.schema = self._get_config_schema()
        
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent.parent.parent
        return str(current_dir / 'config' / 'settings.yaml')
        
    def load_config(self) -> bool:
        """Load configuration from file."""
        try:
            if not os.path.exists(self.config_path):
                self.logger.warning(f"Config file not found: {self.config_path}")
                self.config = self._get_default_config()
                return self.save_config()  # Save default config
                
            with open(self.config_path, 'r') as f:
                if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                    self.config = yaml.safe_load(f)
                else:
                    self.config = json.load(f)
                    
            # Validate configuration
            validation = self.validate_config()
            if not validation.is_valid:
                self.logger.error(f"Invalid configuration: {validation.errors}")
                return False
                
            if validation.warnings:
                for warning in validation.warnings:
                    self.logger.warning(f"Config warning: {warning}")
                    
            self.logger.info("Configuration loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self.config = self._get_default_config()
            return False
            
    def save_config(self) -> bool:
        """Save current configuration to file."""
        try:
            # Create config directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                    yaml.dump(self.config, f, default_flow_style=False, indent=2)
                else:
                    json.dump(self.config, f, indent=2)
                    
            self.logger.info(f"Configuration saved to {self.config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False
            
    def validate_config(self) -> ConfigValidationResult:
        """Validate current configuration against schema."""
        errors = []
        warnings = []
        
        try:
            # Check required sections
            required_sections = ['app', 'security', 'biometrics', 'ml', 'authentication']
            for section in required_sections:
                if section not in self.config:
                    errors.append(f"Missing required section: {section}")
                    
            # Validate security settings
            if 'security' in self.config:
                security = self.config['security']
                
                # Check encryption settings
                if 'encryption' in security:
                    enc = security['encryption']
                    if enc.get('iterations', 0) < 10000:
                        warnings.append("Low PBKDF2 iterations - consider increasing for better security")
                        
                # Check session settings
                if 'session' in security:
                    session = security['session']
                    if session.get('timeout_minutes', 0) > 480:  # 8 hours
                        warnings.append("Very long session timeout - consider shorter duration")
                        
            # Validate ML settings
            if 'ml' in self.config:
                ml = self.config['ml']
                
                if 'training' in ml:
                    training = ml['training']
                    min_samples = training.get('min_samples', 0)
                    if min_samples < 100:
                        warnings.append("Low minimum training samples - may affect model quality")
                        
            # Validate authentication thresholds
            if 'authentication' in self.config:
                auth = self.config['authentication']
                
                if 'confidence_levels' in auth:
                    levels = auth['confidence_levels']
                    high = levels.get('high', 0)
                    medium = levels.get('medium', 0)
                    low = levels.get('low', 0)
                    
                    if not (low <= medium <= high):
                        errors.append("Authentication confidence levels must be: low <= medium <= high")
                        
        except Exception as e:
            errors.append(f"Configuration validation error: {e}")
            
        return ConfigValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
        
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'security.session.timeout_minutes')."""
        try:
            keys = key_path.split('.')
            value = self.config
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
                    
            return value
            
        except Exception:
            return default
            
    def set(self, key_path: str, value: Any) -> bool:
        """Set configuration value using dot notation."""
        try:
            keys = key_path.split('.')
            config_ref = self.config
            
            # Navigate to parent
            for key in keys[:-1]:
                if key not in config_ref:
                    config_ref[key] = {}
                config_ref = config_ref[key]
                
            # Set value
            config_ref[keys[-1]] = value
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set config value {key_path}: {e}")
            return False
            
    def update_section(self, section: str, updates: Dict[str, Any]) -> bool:
        """Update an entire configuration section."""
        try:
            if section not in self.config:
                self.config[section] = {}
                
            self.config[section].update(updates)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update section {section}: {e}")
            return False
            
    def get_schema(self) -> Dict[str, Any]:
        """Get configuration schema for validation."""
        return self.schema
        
    def _get_config_schema(self) -> Dict[str, Any]:
        """Define configuration schema for validation."""
        return {
            "type": "object",
            "required": ["app", "security", "biometrics", "ml", "authentication"],
            "properties": {
                "app": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "version": {"type": "string"},
                        "debug": {"type": "boolean"}
                    }
                },
                "security": {
                    "type": "object",
                    "properties": {
                        "encryption": {
                            "type": "object",
                            "properties": {
                                "algorithm": {"type": "string"},
                                "iterations": {"type": "integer", "minimum": 10000}
                            }
                        },
                        "session": {
                            "type": "object",
                            "properties": {
                                "timeout_minutes": {"type": "integer", "minimum": 1}
                            }
                        }
                    }
                }
            }
        }
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "app": {
                "name": "Smart Behavior Auth System",
                "version": "1.0.0",
                "debug": False,
                "log_level": "INFO"
            },
            "security": {
                "encryption": {
                    "algorithm": "AES-256-GCM",
                    "key_derivation": "PBKDF2",
                    "iterations": 100000,
                    "salt_length": 32
                },
                "session": {
                    "timeout_minutes": 30,
                    "idle_timeout_minutes": 15,
                    "max_concurrent_sessions": 3,
                    "token_refresh_interval": 5
                },
                "privacy": {
                    "enable_differential_privacy": True,
                    "noise_epsilon": 0.1,
                    "hash_raw_inputs": True
                }
            },
            "biometrics": {
                "keystroke": {
                    "sample_window": 50,
                    "features": ["dwell_time", "flight_time", "typing_speed", "rhythm_patterns"]
                },
                "mouse": {
                    "sample_window": 100,
                    "features": ["velocity", "acceleration", "click_intervals", "movement_smoothness"]
                }
            },
            "ml": {
                "models": {
                    "primary": "random_forest",
                    "anomaly_detector": "isolation_forest"
                },
                "training": {
                    "min_samples": 1000,
                    "retrain_interval_hours": 24,
                    "validation_split": 0.2
                },
                "anomaly_detection": {
                    "contamination": 0.1,
                    "threshold": 0.7,
                    "adaptive_threshold": True
                },
                "features": {
                    "window_size": 100,
                    "overlap": 0.5
                }
            },
            "authentication": {
                "confidence_levels": {
                    "high": 0.9,
                    "medium": 0.7,
                    "low": 0.5
                },
                "actions": {
                    "high_confidence": "continue",
                    "medium_confidence": "monitor",
                    "low_confidence": "challenge",
                    "very_low_confidence": "logout"
                },
                "challenges": {
                    "types": ["pin", "biometric", "sms"],
                    "max_attempts": 3,
                    "lockout_duration": 300
                }
            },
            "device": {
                "fingerprinting": {
                    "enabled": True,
                    "components": ["hardware_id", "screen_resolution", "timezone", "network_interfaces"]
                },
                "geolocation": {
                    "enabled": True,
                    "max_distance_km": 100,
                    "vpn_detection": True
                },
                "time_patterns": {
                    "enable_analysis": True,
                    "unusual_hours_threshold": 0.1
                }
            },
            "service": {
                "monitoring": {
                    "interval_seconds": 1,
                    "batch_size": 50,
                    "max_memory_mb": 100
                },
                "storage": {
                    "local_db": "data/behavior.db",
                    "backup_interval_hours": 6,
                    "retention_days": 30
                },
                "notifications": {
                    "enabled": True,
                    "types": ["security_alert", "anomaly_detected", "session_timeout"]
                }
            },
            "logging": {
                "level": "INFO",
                "file": "logs/behavior_auth.log",
                "max_size_mb": 10,
                "backup_count": 5,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }

class ConfigEditor:
    """Interactive configuration editor."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
    def edit_interactive(self) -> bool:
        """Interactive configuration editing."""
        print("=== Behavioral Authentication Configuration Editor ===")
        print()
        
        while True:
            self._show_main_menu()
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == '1':
                self._edit_security_settings()
            elif choice == '2':
                self._edit_ml_settings()
            elif choice == '3':
                self._edit_authentication_settings()
            elif choice == '4':
                self._edit_device_settings()
            elif choice == '5':
                self._view_current_config()
            elif choice == '6':
                self._save_and_exit()
                break
            else:
                print("Invalid choice. Please try again.")
                
        return True
        
    def _show_main_menu(self):
        """Show main configuration menu."""
        print("\nConfiguration Sections:")
        print("1. Security Settings")
        print("2. Machine Learning Settings")
        print("3. Authentication Settings")
        print("4. Device & Context Settings")
        print("5. View Current Configuration")
        print("6. Save and Exit")
        
    def _edit_security_settings(self):
        """Edit security configuration."""
        print("\n=== Security Settings ===")
        
        # Session timeout
        current_timeout = self.config_manager.get('security.session.timeout_minutes', 30)
        print(f"Current session timeout: {current_timeout} minutes")
        new_timeout = input(f"New session timeout (minutes) [{current_timeout}]: ").strip()
        
        if new_timeout:
            try:
                timeout_val = int(new_timeout)
                if 1 <= timeout_val <= 1440:  # 1 minute to 24 hours
                    self.config_manager.set('security.session.timeout_minutes', timeout_val)
                    print("✓ Session timeout updated")
                else:
                    print("⚠ Invalid timeout range (1-1440 minutes)")
            except ValueError:
                print("⚠ Invalid number format")
                
        # Privacy settings
        current_privacy = self.config_manager.get('security.privacy.enable_differential_privacy', True)
        print(f"Current differential privacy: {'Enabled' if current_privacy else 'Disabled'}")
        privacy_choice = input("Enable differential privacy? (y/n): ").strip().lower()
        
        if privacy_choice in ['y', 'n']:
            self.config_manager.set('security.privacy.enable_differential_privacy', privacy_choice == 'y')
            print("✓ Privacy setting updated")
            
    def _edit_ml_settings(self):
        """Edit ML configuration."""
        print("\n=== Machine Learning Settings ===")
        
        # Minimum training samples
        current_samples = self.config_manager.get('ml.training.min_samples', 1000)
        print(f"Current minimum training samples: {current_samples}")
        new_samples = input(f"New minimum samples [{current_samples}]: ").strip()
        
        if new_samples:
            try:
                samples_val = int(new_samples)
                if samples_val >= 10:
                    self.config_manager.set('ml.training.min_samples', samples_val)
                    print("✓ Training samples updated")
                else:
                    print("⚠ Minimum samples must be at least 10")
            except ValueError:
                print("⚠ Invalid number format")
                
        # Anomaly threshold
        current_threshold = self.config_manager.get('ml.anomaly_detection.threshold', 0.7)
        print(f"Current anomaly threshold: {current_threshold}")
        new_threshold = input(f"New anomaly threshold (0.0-1.0) [{current_threshold}]: ").strip()
        
        if new_threshold:
            try:
                threshold_val = float(new_threshold)
                if 0.0 <= threshold_val <= 1.0:
                    self.config_manager.set('ml.anomaly_detection.threshold', threshold_val)
                    print("✓ Anomaly threshold updated")
                else:
                    print("⚠ Threshold must be between 0.0 and 1.0")
            except ValueError:
                print("⚠ Invalid number format")
                
    def _edit_authentication_settings(self):
        """Edit authentication configuration."""
        print("\n=== Authentication Settings ===")
        
        # Confidence levels
        levels = ['high', 'medium', 'low']
        for level in levels:
            current_val = self.config_manager.get(f'authentication.confidence_levels.{level}', 0.5)
            print(f"Current {level} confidence threshold: {current_val}")
            new_val = input(f"New {level} threshold (0.0-1.0) [{current_val}]: ").strip()
            
            if new_val:
                try:
                    val = float(new_val)
                    if 0.0 <= val <= 1.0:
                        self.config_manager.set(f'authentication.confidence_levels.{level}', val)
                        print(f"✓ {level.capitalize()} threshold updated")
                    else:
                        print("⚠ Threshold must be between 0.0 and 1.0")
                except ValueError:
                    print("⚠ Invalid number format")
                    
    def _edit_device_settings(self):
        """Edit device configuration."""
        print("\n=== Device & Context Settings ===")
        
        # Geolocation
        current_geo = self.config_manager.get('device.geolocation.enabled', True)
        print(f"Current geolocation: {'Enabled' if current_geo else 'Disabled'}")
        geo_choice = input("Enable geolocation validation? (y/n): ").strip().lower()
        
        if geo_choice in ['y', 'n']:
            self.config_manager.set('device.geolocation.enabled', geo_choice == 'y')
            print("✓ Geolocation setting updated")
            
        # Max distance
        if geo_choice == 'y' or current_geo:
            current_dist = self.config_manager.get('device.geolocation.max_distance_km', 100)
            print(f"Current max distance change: {current_dist} km")
            new_dist = input(f"New max distance (km) [{current_dist}]: ").strip()
            
            if new_dist:
                try:
                    dist_val = int(new_dist)
                    if dist_val > 0:
                        self.config_manager.set('device.geolocation.max_distance_km', dist_val)
                        print("✓ Max distance updated")
                    else:
                        print("⚠ Distance must be positive")
                except ValueError:
                    print("⚠ Invalid number format")
                    
    def _view_current_config(self):
        """View current configuration."""
        print("\n=== Current Configuration ===")
        print(yaml.dump(self.config_manager.config, default_flow_style=False, indent=2))
        input("\nPress Enter to continue...")
        
    def _save_and_exit(self):
        """Save configuration and exit."""
        print("\nSaving configuration...")
        
        # Validate before saving
        validation = self.config_manager.validate_config()
        
        if not validation.is_valid:
            print("⚠ Configuration has errors:")
            for error in validation.errors:
                print(f"  - {error}")
            choice = input("Save anyway? (y/n): ").strip().lower()
            if choice != 'y':
                return
                
        if validation.warnings:
            print("⚠ Configuration warnings:")
            for warning in validation.warnings:
                print(f"  - {warning}")
                
        if self.config_manager.save_config():
            print("✓ Configuration saved successfully!")
        else:
            print("⚠ Failed to save configuration")

def create_default_config_file(config_path: str) -> bool:
    """Create a default configuration file."""
    try:
        config_manager = ConfigManager()
        config_manager.config_path = config_path
        config_manager.config = config_manager._get_default_config()
        return config_manager.save_config()
    except Exception as e:
        print(f"Failed to create default config: {e}")
        return False

if __name__ == '__main__':
    # Interactive configuration
    config_manager = ConfigManager()
    config_manager.load_config()
    
    editor = ConfigEditor(config_manager)
    editor.edit_interactive()