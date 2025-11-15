#!/usr/bin/env python3
"""
Test script to verify that core components of the behavior authentication system work correctly.
"""

import sys
from pathlib import Path

# Add src to path for imports
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def test_database():
    """Test database connectivity."""
    print("Testing database connectivity...")
    try:
        from database.db_manager import DatabaseManager
        db_path = current_dir / "data" / "behavior_auth.db"
        db_manager = DatabaseManager(str(db_path))
        print("✅ Database manager initialized successfully")
        
        # Test database stats
        stats = db_manager.get_database_stats()
        print(f"✅ Database stats: {stats}")
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_behavioral_collectors():
    """Test behavioral data collectors."""
    print("\nTesting behavioral collectors...")
    try:
        from core.keystroke_collector import KeystrokeCollector
        from core.mouse_collector import MouseCollector
        
        keystroke_collector = KeystrokeCollector(config={})
        mouse_collector = MouseCollector(config={})
        
        print("✅ Behavioral collectors initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Behavioral collectors test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_security_components():
    """Test security components."""
    print("\nTesting security components...")
    try:
        from security.security_manager import SecurityManager
        security_manager = SecurityManager(config={})
        print("✅ Security manager initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Security components test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🔒 Behavior Authentication System - Component Tests")
    print("=" * 50)
    
    tests = [
        test_database,
        test_behavioral_collectors,
        test_security_components
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("Test Results:")
    passed = sum(results)
    total = len(results)
    print(f"✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The system is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit(main())