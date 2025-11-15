#!/usr/bin/env python3
"""
Demonstration of the 5-minute post-login behavioral monitoring system
"""

import sys
import time
import threading
from pathlib import Path

# Add src to path for imports
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(current_dir))

from behavioral_monitor import BehavioralMonitor

def demonstrate_post_login_monitoring():
    """Demonstrate the 5-minute post-login behavioral monitoring."""
    print("🔒 Behavioral Authentication System - Post-Login Monitoring Demo")
    print("=" * 65)
    
    # Create a behavioral monitor for a demo user
    print("Creating behavioral monitor for user: demo_user")
    monitor = BehavioralMonitor("demo_user")
    
    # Start monitoring
    print("\n🔍 Starting behavioral monitoring...")
    monitor.start_monitoring()
    
    # Simulate user activity for demonstration
    print("\n📝 Simulating user activity (please type and move your mouse)...")
    print("⏳ 5-minute baseline collection will begin in 3 seconds...")
    
    # Wait a moment to let user get ready
    time.sleep(3)
    
    # Start the 5-minute baseline collection
    print("\n📊 Starting 5-minute baseline data collection...")
    print("📝 Please continue with your normal computer usage during this time.")
    print("⏳ The system will not lock during baseline collection.")
    
    # Mark start time
    start_time = time.time()
    duration = 5 * 60  # 5 minutes
    
    # Simulate the collection process
    try:
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            remaining = duration - elapsed
            progress = (elapsed / duration) * 100
            
            # Show progress
            minutes_elapsed = int(elapsed // 60)
            seconds_elapsed = int(elapsed % 60)
            minutes_remaining = int(remaining // 60)
            seconds_remaining = int(remaining % 60)
            
            print(f"\r📊 Progress: {progress:.1f}% - Elapsed: {minutes_elapsed:02d}:{seconds_elapsed:02d} - Remaining: {minutes_remaining:02d}:{seconds_remaining:02d}", end='', flush=True)
            
            # Extract features periodically to show system is working
            if int(elapsed) % 10 == 0:  # Every 10 seconds
                features = monitor._extract_features()
                if features:
                    score = monitor._analyze_behavior(features)
                    print(f"\n   🔍 Features collected: {len(features)} | ML Score: {score:.1f}")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Monitoring interrupted by user")
        monitor.stop_monitoring()
        return
    
    print(f"\n\n✅ 5-minute baseline data collection completed!")
    print("🔄 Continuing behavioral monitoring in background...")
    
    # Continue monitoring for a bit to show it's working
    print("\n🔍 Continuing behavioral monitoring (press Ctrl+C to stop)...")
    try:
        for i in range(30):  # Monitor for 30 seconds more
            # Extract features and analyze
            features = monitor._extract_features()
            if features:
                score = monitor._analyze_behavior(features)
                print(f"📊 ML Score: {score:.1f}")
                
                # Simulate lock screen if score drops below 20
                if score < 20:
                    print("🔒 Low score detected! In real system, screen would lock now.")
                    print("🔓 Screen would unlock with PIN verification.")
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Demonstration stopped by user")
    
    # Stop monitoring
    monitor.stop_monitoring()
    print("\n✅ Behavioral monitoring stopped")
    print("\n🎉 Demonstration completed successfully!")

def main():
    """Main entry point."""
    try:
        demonstrate_post_login_monitoring()
    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()