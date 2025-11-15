#!/usr/bin/env python3
"""
Test script for dashboard updates with system monitoring
"""

import time
import psutil
import win32gui

def test_system_monitoring():
    """Test system monitoring functionality."""
    print("Testing system monitoring...")
    
    # Test window monitoring
    print("Current active window:", win32gui.GetWindowText(win32gui.GetForegroundWindow()))
    
    # Test application counting
    app_count = len([p for p in psutil.process_iter(['name']) if p.info['name']])
    print(f"Active applications: {app_count}")
    
    # Test CPU and memory info
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    print(f"CPU usage: {cpu_percent}%")
    print(f"Memory usage: {memory_info.percent}%")
    
    print("✅ System monitoring test completed successfully")

if __name__ == "__main__":
    test_system_monitoring()