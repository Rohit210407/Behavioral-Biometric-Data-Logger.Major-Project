#!/usr/bin/env python3
"""
Real-time behavioral monitoring service for authentic data collection.
This replaces fake/simulated data with actual keystroke and mouse tracking.
"""

import time
import threading
import json
import queue
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

from .keystroke_collector import KeystrokeCollector
from .mouse_collector import MouseCollector

@dataclass
class RealTimeStats:
    """Real-time statistics from actual user behavior."""
    keystroke_count: int = 0
    mouse_clicks: int = 0
    mouse_moves: int = 0
    session_start_time: float = 0
    last_activity_time: float = 0
    typing_speed: float = 0.0
    mouse_velocity_avg: float = 0.0
    behavioral_score: float = 0.0
    is_active: bool = False
    application_switches: int = 0  # New field for tracking application switches
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class RealTimeBehavioralMonitor:
    """
    Authentic real-time behavioral monitoring system.
    Collects actual user input data instead of fake simulations.
    Modified to work in background and collect data from all applications.
    """
    
    def __init__(self):
        self.config = {
            'sample_window': 100,
            'update_interval': 1.0,  # Update every second
            'min_events_for_analysis': 10
        }
        
        # Initialize real collectors
        self.keystroke_collector = KeystrokeCollector(self.config)
        self.mouse_collector = MouseCollector(self.config)
        
        # Real-time statistics
        self.stats = RealTimeStats()
        self.stats.session_start_time = time.time()
        
        # Event counters
        self.event_history = deque(maxlen=1000)
        self.keystroke_times = deque(maxlen=100)
        self.mouse_click_times = deque(maxlen=100)
        
        # Threading
        self.is_monitoring = False
        self.monitor_thread = None
        self._lock = threading.Lock()
        
        # Data queue for external access
        self.data_queue = queue.Queue(maxsize=10)
        
        # Desktop integration
        self.desktop_monitoring = True
        self.application_switches = 0
        self.last_active_window = None
    
    def start_monitoring(self) -> bool:
        """Start authentic behavioral monitoring in background."""
        try:
            if self.is_monitoring:
                return True
                
            print("🔍 Starting authentic behavioral monitoring in background...")
            
            # Start collectors
            self.keystroke_collector.start_collection()
            self.mouse_collector.start_collection()
            
            # Start monitoring thread
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitor_thread.start()
            
            # Start desktop monitoring thread
            self.desktop_thread = threading.Thread(target=self._desktop_monitoring_loop, daemon=True)
            self.desktop_thread.start()
            
            self.stats.is_active = True
            print("✅ Real behavioral monitoring active in background")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start monitoring: {e}")
            return False
    
    def stop_monitoring(self) -> None:
        """Stop behavioral monitoring."""
        self.is_monitoring = False
        self.stats.is_active = False
        
        if self.keystroke_collector:
            self.keystroke_collector.stop_collection()
        if self.mouse_collector:
            self.mouse_collector.stop_collection()
            
        print("🛑 Behavioral monitoring stopped")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop that processes real events."""
        while self.is_monitoring:
            try:
                # Get real features from collectors
                keystroke_features = self.keystroke_collector.get_features()
                mouse_features = self.mouse_collector.get_features()
                
                # Update statistics with real data
                self._update_real_statistics(keystroke_features, mouse_features)
                
                # Put current stats in queue for external access
                try:
                    self.data_queue.put_nowait(self.stats.to_dict())
                except queue.Full:
                    # Remove old data if queue is full
                    try:
                        self.data_queue.get_nowait()
                        self.data_queue.put_nowait(self.stats.to_dict())
                    except queue.Empty:
                        pass
                
                time.sleep(self.config['update_interval'])
                
            except Exception as e:
                print(f"⚠️ Monitoring loop error: {e}")
                time.sleep(1)
    
    def _desktop_monitoring_loop(self) -> None:
        """Monitor desktop activity including application switches."""
        try:
            import psutil
            import win32gui
            import win32process
            
            while self.is_monitoring:
                try:
                    # Get current active window
                    current_window = win32gui.GetWindowText(win32gui.GetForegroundWindow())
                    if current_window != self.last_active_window and self.last_active_window is not None:
                        self.application_switches += 1
                        print(f"🔄 Application switched to: {current_window}")
                    self.last_active_window = current_window
                    
                    time.sleep(1)  # Check every second
                    
                except Exception as e:
                    print(f"⚠️ Desktop monitoring error: {e}")
                    time.sleep(1)
                    
        except ImportError:
            print("⚠️ Desktop monitoring not available (missing psutil or win32 modules)")
    
    def _update_real_statistics(self, keystroke_features, mouse_features) -> None:
        """Update statistics using real behavioral data."""
        with self._lock:
            current_time = time.time()
            
            # Update keystroke statistics from real data
            if keystroke_features:
                # Count actual keystrokes from buffer
                keystroke_buffer = self.keystroke_collector.keystroke_buffer
                self.stats.keystroke_count = sum(1 for event in keystroke_buffer 
                                               if event.event_type == 'press')
                
                # Get real typing speed
                if 'typing_speed' in keystroke_features.keystroke_features:
                    self.stats.typing_speed = keystroke_features.keystroke_features['typing_speed']
                
                self.stats.last_activity_time = current_time
            
            # Update mouse statistics from real data  
            if mouse_features:
                # Count actual mouse events
                mouse_buffer = self.mouse_collector.mouse_buffer
                self.stats.mouse_clicks = sum(1 for event in mouse_buffer 
                                            if event.event_type == 'click')
                self.stats.mouse_moves = sum(1 for event in mouse_buffer 
                                           if event.event_type == 'move')
                
                # Get real mouse velocity
                if 'velocity_mean' in mouse_features.mouse_features:
                    self.stats.mouse_velocity_avg = mouse_features.mouse_features['velocity_mean']
                
                self.stats.last_activity_time = current_time
            
            # Add application switch count to stats
            self.stats.application_switches = self.application_switches
            
            # Calculate behavioral score based on real activity
            self.stats.behavioral_score = self._calculate_authentic_score(
                keystroke_features, mouse_features
            )
    
    def _calculate_authentic_score(self, keystroke_features, mouse_features) -> float:
        """Calculate behavioral confidence score from real data."""
        score = 0.0
        
        # Base score from recent activity
        current_time = time.time()
        time_since_activity = current_time - self.stats.last_activity_time
        
        # Score decreases if no recent activity
        if time_since_activity < 10:  # Active within 10 seconds
            score += 50.0
        elif time_since_activity < 30:  # Active within 30 seconds
            score += 30.0
        else:
            score += 10.0
        
        # Add score based on keystroke patterns
        if keystroke_features and keystroke_features.keystroke_features:
            features = keystroke_features.keystroke_features
            
            # Consistent typing patterns increase score
            if 'rhythm_consistency' in features:
                consistency = features['rhythm_consistency']
                # Lower consistency (more regular) is better
                if consistency < 0.5:
                    score += 25.0
                elif consistency < 1.0:
                    score += 15.0
                else:
                    score += 5.0
            
            # Reasonable typing speed
            if 'typing_speed' in features:
                speed = features['typing_speed']
                if 50 <= speed <= 150:  # Normal human range
                    score += 15.0
                else:
                    score += 5.0
        
        # Add score based on mouse patterns
        if mouse_features and mouse_features.mouse_features:
            features = mouse_features.mouse_features
            
            # Human-like mouse movement
            if 'velocity_mean' in features:
                velocity = features['velocity_mean']
                if 50 <= velocity <= 1000:  # Normal human range
                    score += 10.0
                else:
                    score += 2.0
        
        return min(score, 100.0)  # Cap at 100%
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Get current authentic statistics."""
        with self._lock:
            return self.stats.to_dict()
    
    def get_latest_data(self) -> Optional[Dict[str, Any]]:
        """Get latest data from queue (non-blocking)."""
        try:
            return self.data_queue.get_nowait()
        except queue.Empty:
            return None
    
    def is_user_active(self) -> bool:
        """Check if user is currently active based on real data."""
        current_time = time.time()
        return (current_time - self.stats.last_activity_time) < 30  # Active within 30 seconds
    
    def get_session_duration(self) -> float:
        """Get current session duration in seconds."""
        return time.time() - self.stats.session_start_time
    
    def reset_session(self) -> None:
        """Reset session statistics."""
        with self._lock:
            self.stats = RealTimeStats()
            self.stats.session_start_time = time.time()
            self.stats.is_active = self.is_monitoring

# Global monitor instance
_global_monitor = None

def get_monitor() -> RealTimeBehavioralMonitor:
    """Get or create global monitor instance."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = RealTimeBehavioralMonitor()
    return _global_monitor

def start_global_monitoring() -> bool:
    """Start global behavioral monitoring."""
    monitor = get_monitor()
    return monitor.start_monitoring()

def stop_global_monitoring() -> None:
    """Stop global behavioral monitoring."""
    global _global_monitor
    if _global_monitor:
        _global_monitor.stop_monitoring()

def get_real_time_data() -> Dict[str, Any]:
    """Get real-time behavioral data."""
    monitor = get_monitor()
    return monitor.get_current_stats()

if __name__ == "__main__":
    # Test the real-time monitor
    monitor = RealTimeBehavioralMonitor()
    
    print("Starting authentic behavioral monitoring test...")
    if monitor.start_monitoring():
        print("✅ Monitoring started. Type and move mouse to see real data.")
        print("Press Ctrl+C to stop...")
        
        try:
            while True:
                stats = monitor.get_current_stats()
                print(f"\r🔍 Keystrokes: {stats['keystroke_count']}, "
                      f"Clicks: {stats['mouse_clicks']}, "
                      f"Score: {stats['behavioral_score']:.1f}%", end="")
                time.sleep(1)
        except KeyboardInterrupt:
            monitor.stop_monitoring()
            print("\n🛑 Monitoring stopped.")
    else:
        print("❌ Failed to start monitoring.")