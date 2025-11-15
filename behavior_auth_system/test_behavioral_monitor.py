#!/usr/bin/env python3
"""
Test script for behavioral monitor
"""

import sys
from pathlib import Path

# Add src to path for imports
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(current_dir))

from behavioral_monitor import BehavioralMonitor

def test_behavioral_monitor():
    """Test the behavioral monitor functionality."""
    print("Testing Behavioral Monitor...")
    
    # Create a monitor instance
    monitor = BehavioralMonitor("test_user")
    
    # Test initialization
    print("Monitor initialized successfully")
    print(f"User ID: {monitor.user_id}")
    print(f"Keystroke collector: {monitor.keystroke_collector}")
    print(f"Mouse collector: {monitor.mouse_collector}")
    
    print("✅ Test completed successfully")

if __name__ == "__main__":
    test_behavioral_monitor()