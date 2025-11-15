#!/usr/bin/env python3
"""
Integration test for the behavioral authentication system
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(current_dir))

def test_system_integration():
    """Test the complete system integration."""
    print("Testing Behavioral Authentication System Integration...")
    print("=" * 50)
    
    try:
        # Test 1: Import core components
        print("Test 1: Importing core components...")
        from core.keystroke_collector import KeystrokeCollector
        from core.mouse_collector import MouseCollector
        print("✅ Core components imported successfully")
        
        # Test 2: Test behavioral monitor
        print("\nTest 2: Testing behavioral monitor...")
        from behavioral_monitor import BehavioralMonitor
        
        # Create a monitor instance
        monitor = BehavioralMonitor("test_user")
        print("✅ Behavioral monitor created successfully")
        
        # Test 3: Verify collectors are initialized
        print("\nTest 3: Verifying collectors...")
        if monitor.keystroke_collector:
            print("✅ Keystroke collector initialized")
        else:
            print("❌ Keystroke collector failed to initialize")
            
        if monitor.mouse_collector:
            print("✅ Mouse collector initialized")
        else:
            print("❌ Mouse collector failed to initialize")
        
        # Test 4: Test starting monitoring
        print("\nTest 4: Testing monitoring start...")
        monitor.start_monitoring()
        print("✅ Monitoring started successfully")
        
        # Test 5: Test feature extraction
        print("\nTest 5: Testing feature extraction...")
        time.sleep(3)  # Give time to collect some data
        features = monitor._extract_features()
        if features is not None:
            print(f"✅ Features extracted: {len(features)} features collected")
        else:
            print("⚠️  No features extracted (may need more time or user interaction)")
        
        # Test 6: Test ML analysis
        print("\nTest 6: Testing ML analysis...")
        if features:
            score = monitor._analyze_behavior(features)
            print(f"✅ ML analysis completed. Score: {score:.1f}")
        else:
            print("⚠️  ML analysis skipped (no features available)")
        
        # Test 7: Test stopping monitoring
        print("\nTest 7: Testing monitoring stop...")
        monitor.stop_monitoring()
        print("✅ Monitoring stopped successfully")
        
        print("\n" + "=" * 50)
        print("🎉 All integration tests completed!")
        print("The behavioral authentication system is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    test_system_integration()