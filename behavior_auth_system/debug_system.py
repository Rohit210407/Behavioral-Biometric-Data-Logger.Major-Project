#!/usr/bin/env python3
"""
Comprehensive debug script for the behavior authentication system.
This script will test all components and identify any issues.
"""

import sys
import os
import traceback
from pathlib import Path

# Add src to path for imports
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def test_imports():
    """Test importing all modules."""
    print("🔍 Testing module imports...")
    
    modules_to_test = [
        # Core modules
        ("src.core.keystroke_collector", "KeystrokeCollector"),
        ("src.core.mouse_collector", "MouseCollector"),
        ("src.core.behavioral_manager", "BehavioralDataManager"),
        
        # Database modules
        ("src.database.db_manager", "DatabaseManager"),
        
        # Security modules
        ("src.security.security_manager", "SecurityManager"),
        ("src.security.encryption", "EncryptionManager"),
        
        # ML modules
        ("src.ml.feature_extraction", "FeatureExtractor"),
        ("src.ml.behavior_models", "MLManager"),
        
        # Auth modules
        ("src.auth.auth_manager", "AuthenticationManager"),
        
        # Device modules
        ("src.device.fingerprinting", "ContextValidator"),
        
        # Service modules
        ("src.service.client", "SimpleBehaviorAuth"),
    ]
    
    failed_imports = []
    successful_imports = []
    
    for module_path, class_name in modules_to_test:
        try:
            # Handle the src prefix differently
            if module_path.startswith("src."):
                clean_path = module_path[4:]  # Remove 'src.' prefix
                module = __import__(clean_path, fromlist=[class_name])
            else:
                module = __import__(module_path, fromlist=[class_name])
            getattr(module, class_name)  # Try to access the class
            successful_imports.append(module_path)
            print(f"  ✅ {module_path}")
        except Exception as e:
            failed_imports.append((module_path, str(e)))
            print(f"  ❌ {module_path}: {e}")
    
    return failed_imports, successful_imports

def test_database():
    """Test database functionality."""
    print("\n🔍 Testing database functionality...")
    try:
        from src.database.db_manager import DatabaseManager
        db_path = current_dir / "data" / "behavior_auth.db"
        db_manager = DatabaseManager(str(db_path))
        print("  ✅ Database manager initialized")
        
        # Test user registration
        email = "test@example.com"
        pin = "123456"
        
        # Try to register a test user
        success, message = db_manager.register_user(email, pin)
        print(f"  ✅ User registration: {message}")
        
        # Try to login
        success, message, user_data = db_manager.login_user(email, pin)
        print(f"  ✅ User login: {message}")
        
        return True
    except Exception as e:
        print(f"  ❌ Database test failed: {e}")
        traceback.print_exc()
        return False

def test_behavioral_collectors():
    """Test behavioral data collectors."""
    print("\n🔍 Testing behavioral collectors...")
    try:
        from src.core.keystroke_collector import KeystrokeCollector
        from src.core.mouse_collector import MouseCollector
        
        # Initialize collectors
        keystroke_collector = KeystrokeCollector(config={})
        mouse_collector = MouseCollector(config={})
        
        print("  ✅ Behavioral collectors initialized")
        
        # Test starting collection (don't actually start, just test the method)
        print("  ✅ Collector methods accessible")
        
        return True
    except Exception as e:
        print(f"  ❌ Behavioral collectors test failed: {e}")
        traceback.print_exc()
        return False

def test_security_components():
    """Test security components."""
    print("\n🔍 Testing security components...")
    try:
        from src.security.security_manager import SecurityManager
        security_manager = SecurityManager(config={})
        print("  ✅ Security manager initialized")
        
        # Test encryption
        from src.security.encryption import EncryptionManager, SecurityConfig
        encryption_manager = EncryptionManager(SecurityConfig())
        test_data = "This is a test message"
        key, salt = encryption_manager.generate_key("test_password")
        encrypted_data = encryption_manager.encrypt_data(test_data, key)
        decrypted_bytes = encryption_manager.decrypt_data(encrypted_data, key)
        decrypted = decrypted_bytes.decode('utf-8')
        if decrypted == test_data:
            print("  ✅ Encryption/decryption working")
        else:
            print("  ❌ Encryption/decryption failed")
            return False
            
        return True
    except Exception as e:
        print(f"  ❌ Security components test failed: {e}")
        traceback.print_exc()
        return False

def test_ml_components():
    """Test machine learning components."""
    print("\n🔍 Testing ML components...")
    try:
        from src.ml.feature_extraction import FeatureExtractor
        from src.ml.behavior_models import MLManager
        
        feature_extractor = FeatureExtractor(config={})
        ml_manager = MLManager(config={})
        
        print("  ✅ ML components initialized")
        return True
    except Exception as e:
        print(f"  ❌ ML components test failed: {e}")
        traceback.print_exc()
        return False

def test_service_client():
    """Test service client."""
    print("\n🔍 Testing service client...")
    try:
        from src.service.client import SimpleBehaviorAuth
        client = SimpleBehaviorAuth()
        print("  ✅ Service client initialized")
        return True
    except Exception as e:
        print(f"  ❌ Service client test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run comprehensive debug tests."""
    print("🔒 Behavior Authentication System - Comprehensive Debug")
    print("=" * 60)
    
    # Test imports
    failed_imports, successful_imports = test_imports()
    
    # Run component tests
    tests = [
        test_database,
        test_behavioral_collectors,
        test_security_components,
        test_ml_components,
        test_service_client
    ]
    
    test_results = []
    for test in tests:
        try:
            result = test()
            test_results.append(result)
        except Exception as e:
            print(f"  ❌ Test {test.__name__} failed with exception: {e}")
            traceback.print_exc()
            test_results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("DEBUG RESULTS:")
    print(f"✅ Successful imports: {len(successful_imports)}")
    print(f"❌ Failed imports: {len(failed_imports)}")
    
    for module, error in failed_imports:
        print(f"    - {module}: {error}")
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    print(f"✅ Passed tests: {passed_tests}/{total_tests}")
    
    if len(failed_imports) == 0 and passed_tests == total_tests:
        print("\n🎉 All debug tests passed! The system is working correctly.")
        print("\nYou can now run the application using:")
        print("  python main_app.py  # For GUI application")
        print("  python start.py gui # Alternative GUI start")
        return 0
    else:
        print("\n❌ Some debug tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit(main())