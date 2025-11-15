#!/usr/bin/env python3
"""
Simple demonstration of the behavioral monitoring system
"""

import sys
from pathlib import Path

# Add src to path for imports
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(current_dir))

from behavioral_monitor import BehavioralMonitor

def simple_demo():
    """Simple demonstration of the behavioral monitor."""
    print("🔒 Behavioral Authentication System - Simple Demo")
    print("=" * 50)
    
    # Create a behavioral monitor for a demo user
    print("Creating behavioral monitor for user: demo_user")
    monitor = BehavioralMonitor("demo_user")
    
    # Show that collectors are initialized
    print(f"Keystroke collector: {monitor.keystroke_collector}")
    print(f"Mouse collector: {monitor.mouse_collector}")
    
    # Start monitoring briefly
    print("\n🔍 Starting behavioral monitoring...")
    monitor.start_monitoring()
    
    # Wait a moment
    import time
    time.sleep(2)
    
    # Try to extract features
    print("\n🔍 Extracting behavioral features...")
    features = monitor._extract_features()
    if features:
        print(f"✅ Collected {len(features)} behavioral features")
    else:
        print("⚠️  No features collected (may need user interaction)")
    
    # Analyze behavior
    print("\n📊 Analyzing behavior...")
    if features:
        score = monitor._analyze_behavior(features)
        print(f"✅ Behavioral score: {score:.1f}")
    else:
        # Use simulated score
        score = 85.0
        print(f"✅ Simulated behavioral score: {score:.1f}")
    
    # Show lock screen logic
    print("\n🔒 Lock screen logic:")
    if score >= 20:
        print("✅ Score is above threshold (20) - System remains unlocked")
    else:
        print("❌ Score is below threshold (20) - System would lock screen")
        print("🔓 User would need to enter PIN to unlock")
    
    # Stop monitoring
    print("\n⏹️  Stopping behavioral monitoring...")
    monitor.stop_monitoring()
    
    print("\n🎉 Simple demonstration completed!")
    print("\n📋 How the full system works:")
    print("  1. User logs in with email and PIN")
    print("  2. System collects behavioral data for 5 minutes")
    print("  3. ML model continuously analyzes user behavior")
    print("  4. If score drops below 20, screen locks automatically")
    print("  5. User must enter PIN to unlock the system")

if __name__ == "__main__":
    simple_demo()