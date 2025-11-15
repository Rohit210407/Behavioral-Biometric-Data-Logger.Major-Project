"""
Advanced Activity Monitor - Comprehensive user behavior tracking for imposter detection.
Includes 15-minute baseline training and sophisticated behavioral pattern analysis.
"""

import time
import threading
import psutil
import win32gui
import win32process
import statistics
from collections import deque, defaultdict
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import logging

# Import behavioral analyzers
from .behavioral_analyzers import InputFloodDetector, TypingRhythmAnalyzer, MultitaskingAnalyzer

@dataclass
class ActivityEvent:
    """Enhanced activity event with comprehensive metadata."""
    timestamp: float
    event_type: str  # 'keystroke', 'mouse', 'window', 'tab', 'app'
    data: Dict[str, Any]
    session_context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BaselineProfile:
    """User's 15-minute baseline behavioral profile."""
    user_id: str
    collection_start: float
    collection_end: float
    keystroke_patterns: Dict[str, float]
    mouse_patterns: Dict[str, float]
    window_patterns: Dict[str, Any]
    tab_switching_patterns: Dict[str, float]
    application_usage: Dict[str, Any]
    timing_patterns: Dict[str, float]
    activity_rhythm: Dict[str, float]
    is_complete: bool = False

class AdvancedActivityMonitor:
    """Comprehensive activity monitoring with baseline training."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Training period (15 minutes)
        self.baseline_duration = config.get('baseline_duration_minutes', 15) * 60
        self.is_baseline_complete = False
        self.baseline_start_time = None
        
        # Activity buffers
        self.activity_buffer = deque(maxlen=10000)
        self.keystroke_buffer = deque(maxlen=1000)
        self.mouse_buffer = deque(maxlen=2000)
        self.window_buffer = deque(maxlen=500)
        
        # Pattern tracking
        self.keystroke_patterns = defaultdict(list)
        self.mouse_velocity_history = deque(maxlen=100)
        self.window_focus_times = {}
        self.application_usage = defaultdict(float)
        self.tab_switches = []
        
        # Advanced metrics
        self.input_flood_detector = InputFloodDetector()
        self.typing_rhythm_analyzer = TypingRhythmAnalyzer()
        self.multitask_analyzer = MultitaskingAnalyzer()
        
        # Monitoring state
        self.is_monitoring = False
        self.current_window = None
        self.last_activity_time = time.time()
        
    def start_baseline_collection(self, user_id: str) -> bool:
        """Start 15-minute baseline data collection."""
        try:
            self.baseline_start_time = time.time()
            self.is_monitoring = True
            self.user_id = user_id
            
            self.logger.info(f"Starting 15-minute baseline collection for user: {user_id}")
            
            # Start monitoring threads
            self._start_monitoring_threads()
            
            # Schedule baseline completion
            baseline_timer = threading.Timer(
                self.baseline_duration, 
                self._complete_baseline_collection
            )
            baseline_timer.start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start baseline collection: {e}")
            return False
            
    def _start_monitoring_threads(self):
        """Start all monitoring threads."""
        
        # Keystroke monitoring
        keystroke_thread = threading.Thread(target=self._monitor_keystrokes, daemon=True)
        keystroke_thread.start()
        
        # Mouse monitoring  
        mouse_thread = threading.Thread(target=self._monitor_mouse, daemon=True)
        mouse_thread.start()
        
        # Window/application monitoring
        window_thread = threading.Thread(target=self._monitor_windows, daemon=True)
        window_thread.start()
        
        # System activity monitoring
        system_thread = threading.Thread(target=self._monitor_system_activity, daemon=True)
        system_thread.start()
        
        self.logger.info("All monitoring threads started")
        
    def _monitor_keystrokes(self):
        """Enhanced keystroke monitoring with advanced patterns."""
        try:
            from pynput import keyboard
            
            def on_press(key):
                if not self.is_monitoring:
                    return
                    
                timestamp = time.time()
                key_str = str(key).replace("'", "")
                
                # Advanced keystroke analysis
                event_data = {
                    'key': key_str,
                    'action': 'press',
                    'window': self.current_window,
                    'time_since_last': timestamp - self.last_activity_time
                }
                
                self._record_activity('keystroke', event_data)
                
                # Update rhythm analyzer
                self.typing_rhythm_analyzer.add_keystroke(timestamp)
                
                # Check for input flooding
                self.input_flood_detector.add_keystroke(timestamp)
                
                self.last_activity_time = timestamp
                
            def on_release(key):
                if not self.is_monitoring:
                    return
                    
                timestamp = time.time()
                key_str = str(key).replace("'", "")
                
                event_data = {
                    'key': key_str,
                    'action': 'release',
                    'window': self.current_window
                }
                
                self._record_activity('keystroke', event_data)
                
            self.keyboard_listener = keyboard.Listener(
                on_press=on_press,
                on_release=on_release
            )
            self.keyboard_listener.start()
            
        except Exception as e:
            self.logger.error(f"Keystroke monitoring error: {e}")
            
    def _monitor_mouse(self):
        """Enhanced mouse monitoring with movement analysis."""
        try:
            from pynput import mouse
            import win32api
            
            last_pos = win32api.GetCursorPos()
            last_time = time.time()
            
            def on_move(x, y):
                if not self.is_monitoring:
                    return
                    
                nonlocal last_pos, last_time
                current_time = time.time()
                
                # Calculate movement metrics
                dx = x - last_pos[0]
                dy = y - last_pos[1]
                distance = (dx**2 + dy**2)**0.5
                dt = current_time - last_time
                
                velocity = distance / dt if dt > 0 else 0
                self.mouse_velocity_history.append(velocity)
                
                event_data = {
                    'position': (x, y),
                    'velocity': velocity,
                    'distance': distance,
                    'direction': self._calculate_direction(dx, dy),
                    'window': self.current_window
                }
                
                self._record_activity('mouse_move', event_data)
                
                last_pos = (x, y)
                last_time = current_time
                self.last_activity_time = current_time
                
            def on_click(x, y, button, pressed):
                if not self.is_monitoring:
                    return
                    
                event_data = {
                    'position': (x, y),
                    'button': str(button),
                    'pressed': pressed,
                    'window': self.current_window,
                    'double_click': self._detect_double_click(time.time())
                }
                
                self._record_activity('mouse_click', event_data)
                self.last_activity_time = time.time()
                
            self.mouse_listener = mouse.Listener(
                on_move=on_move,
                on_click=on_click
            )
            self.mouse_listener.start()
            
        except Exception as e:
            self.logger.error(f"Mouse monitoring error: {e}")
            
    def _monitor_windows(self):
        """Monitor window focus, tab switching, and application usage."""
        
        last_window = None
        window_start_time = time.time()
        
        while self.is_monitoring:
            try:
                # Get current window
                hwnd = win32gui.GetForegroundWindow()
                window_title = win32gui.GetWindowText(hwnd)
                
                if window_title != last_window:
                    current_time = time.time()
                    
                    # Record window switch
                    if last_window:
                        # Calculate time spent in previous window
                        time_spent = current_time - window_start_time
                        self.window_focus_times[last_window] = time_spent
                        
                        # Check for tab switching (browser behavior)
                        if self._is_browser_tab_switch(last_window, window_title):
                            self.tab_switches.append({
                                'timestamp': current_time,
                                'from': last_window,
                                'to': window_title,
                                'time_spent': time_spent
                            })
                            
                            self._record_activity('tab_switch', {
                                'from_tab': last_window,
                                'to_tab': window_title,
                                'switch_speed': time_spent
                            })
                    
                    # Get application info
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        process = psutil.Process(pid)
                        app_name = process.name()
                        
                        self.application_usage[app_name] += 1
                        
                        event_data = {
                            'window_title': window_title,
                            'application': app_name,
                            'switch_type': self._classify_window_switch(last_window or "", window_title)
                        }
                        
                        self._record_activity('window_switch', event_data)
                        
                    except Exception:
                        pass
                    
                    self.current_window = window_title
                    last_window = window_title
                    window_start_time = current_time
                    
                time.sleep(0.1)  # Check every 100ms
                
            except Exception as e:
                self.logger.error(f"Window monitoring error: {e}")
                time.sleep(1)
                
    def _monitor_system_activity(self):
        """Monitor system-level activity patterns."""
        
        while self.is_monitoring:
            try:
                current_time = time.time()
                
                # System resource usage
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_info = psutil.virtual_memory()
                
                # Network activity
                network_io = psutil.net_io_counters()
                
                # Detect multitasking intensity
                active_processes = len([p for p in psutil.process_iter(['name']) 
                                      if p.info['name']])
                
                system_data = {
                    'cpu_usage': cpu_percent,
                    'memory_percent': memory_info.percent,
                    'active_processes': active_processes,
                    'network_activity': {
                        'bytes_sent': network_io.bytes_sent,
                        'bytes_recv': network_io.bytes_recv
                    }
                }
                
                self._record_activity('system_activity', system_data)
                
                # Update multitasking analyzer
                self.multitask_analyzer.update(active_processes, len(self.application_usage))
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self.logger.error(f"System monitoring error: {e}")
                time.sleep(5)
                
    def _record_activity(self, event_type: str, data: Dict[str, Any]):
        """Record activity event with timestamp."""
        
        event = ActivityEvent(
            timestamp=time.time(),
            event_type=event_type,
            data=data,
            session_context={
                'baseline_progress': self._get_baseline_progress(),
                'session_duration': time.time() - (self.baseline_start_time or time.time())
            }
        )
        
        self.activity_buffer.append(event)
        
    def _complete_baseline_collection(self):
        """Complete baseline collection and generate user profile."""
        
        self.logger.info("Completing 15-minute baseline collection")
        
        try:
            # Generate comprehensive baseline profile
            baseline_profile = self._generate_baseline_profile()
            
            self.is_baseline_complete = True
            self.baseline_profile = baseline_profile
            
            self.logger.info(f"Baseline profile generated with {len(self.activity_buffer)} events")
            
            # Continue monitoring for real-time comparison
            self._switch_to_monitoring_mode()
            
        except Exception as e:
            self.logger.error(f"Failed to complete baseline collection: {e}")
            
    def _generate_baseline_profile(self) -> BaselineProfile:
        """Generate comprehensive baseline profile from collected data."""
        
        # Analyze keystroke patterns
        keystroke_patterns = self.typing_rhythm_analyzer.get_baseline_patterns()
        
        # Analyze mouse patterns
        mouse_patterns = self._analyze_mouse_baseline()
        
        # Analyze window/application patterns
        window_patterns = self._analyze_window_baseline()
        
        # Analyze tab switching patterns
        tab_patterns = self._analyze_tab_switching_baseline()
        
        # Analyze application usage
        app_usage = dict(self.application_usage)
        
        # Analyze timing patterns
        timing_patterns = self._analyze_timing_baseline()
        
        # Calculate activity rhythm
        activity_rhythm = self._calculate_activity_rhythm()
        
        return BaselineProfile(
            user_id=self.user_id,
            collection_start=self.baseline_start_time or time.time(),
            collection_end=time.time(),
            keystroke_patterns=keystroke_patterns,
            mouse_patterns=mouse_patterns,
            window_patterns=window_patterns,
            tab_switching_patterns=tab_patterns,
            application_usage=app_usage,
            timing_patterns=timing_patterns,
            activity_rhythm=activity_rhythm,
            is_complete=True
        )
        
    def get_real_time_deviation_score(self) -> float:
        """Calculate real-time deviation from baseline profile."""
        
        if not self.is_baseline_complete:
            return 0.5  # Neutral score during baseline
            
        try:
            current_patterns = self._extract_current_patterns()
            deviation_scores = []
            
            # Compare keystroke patterns
            keystroke_deviation = self._compare_keystroke_patterns(
                current_patterns['keystroke'], 
                self.baseline_profile.keystroke_patterns
            )
            deviation_scores.append(('keystroke', keystroke_deviation, 0.25))
            
            # Compare mouse patterns
            mouse_deviation = self._compare_mouse_patterns(
                current_patterns['mouse'],
                self.baseline_profile.mouse_patterns
            )
            deviation_scores.append(('mouse', mouse_deviation, 0.20))
            
            # Compare application usage
            app_deviation = self._compare_application_patterns(
                current_patterns['applications'],
                self.baseline_profile.application_usage
            )
            deviation_scores.append(('applications', app_deviation, 0.15))
            
            # Compare tab switching
            tab_deviation = self._compare_tab_patterns(
                current_patterns['tab_switching'],
                self.baseline_profile.tab_switching_patterns
            )
            deviation_scores.append(('tab_switching', tab_deviation, 0.15))
            
            # Compare timing patterns
            timing_deviation = self._compare_timing_patterns(
                current_patterns['timing'],
                self.baseline_profile.timing_patterns
            )
            deviation_scores.append(('timing', timing_deviation, 0.15))
            
            # Check for input flooding
            flood_score = self.input_flood_detector.get_suspicion_score()
            deviation_scores.append(('input_flood', flood_score, 0.10))
            
            # Calculate weighted average
            total_score = sum(score * weight for _, score, weight in deviation_scores)
            
            self.logger.debug(f"Deviation scores: {[(name, score) for name, score, _ in deviation_scores]}")
            
            return min(1.0, max(0.0, total_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating deviation score: {e}")
            return 0.5
            
    # Helper methods for pattern analysis
    def _get_baseline_progress(self) -> float:
        """Get baseline collection progress (0.0 to 1.0)."""
        if not self.baseline_start_time:
            return 0.0
        elapsed = time.time() - self.baseline_start_time
        return min(1.0, elapsed / self.baseline_duration)
        
    def _calculate_direction(self, dx: float, dy: float) -> str:
        """Calculate mouse movement direction."""
        import math
        if dx == 0 and dy == 0:
            return 'none'
        angle = math.atan2(dy, dx) * 180 / math.pi
        if -22.5 <= angle < 22.5:
            return 'right'
        elif 22.5 <= angle < 67.5:
            return 'down-right'
        elif 67.5 <= angle < 112.5:
            return 'down'
        elif 112.5 <= angle < 157.5:
            return 'down-left'
        elif 157.5 <= angle or angle < -157.5:
            return 'left'
        elif -157.5 <= angle < -112.5:
            return 'up-left'
        elif -112.5 <= angle < -67.5:
            return 'up'
        else:
            return 'up-right'
            
    def _detect_double_click(self, timestamp: float) -> bool:
        """Detect if this is a double click."""
        if not hasattr(self, 'last_click_time'):
            self.last_click_time = 0
        
        is_double = timestamp - self.last_click_time < 0.5
        self.last_click_time = timestamp
        return is_double
        
    def _is_browser_tab_switch(self, from_title: str, to_title: str) -> bool:
        """Detect if this is a browser tab switch."""
        browser_indicators = ['Chrome', 'Firefox', 'Edge', 'Safari', 'Opera']
        
        for browser in browser_indicators:
            if (browser in from_title and browser in to_title and 
                from_title != to_title):
                return True
        return False
        
    def _classify_window_switch(self, from_window: str, to_window: str) -> str:
        """Classify the type of window switch."""
        if not from_window:
            return 'initial'
        
        if self._is_browser_tab_switch(from_window, to_window):
            return 'tab_switch'
        elif any(app in from_window and app in to_window 
                for app in ['Word', 'Excel', 'PowerPoint']):
            return 'office_switch'
        else:
            return 'application_switch'
            
    def _switch_to_monitoring_mode(self):
        """Switch from baseline collection to real-time monitoring."""
        self.logger.info("Switching to real-time monitoring mode")
        # Continue monitoring but focus on comparison with baseline
        
    def _analyze_mouse_baseline(self) -> Dict[str, float]:
        """Analyze mouse movement patterns from baseline."""
        if not self.mouse_velocity_history:
            return {}
            
        velocities = list(self.mouse_velocity_history)
        
        return {
            'velocity_mean': statistics.mean(velocities) if velocities else 0,
            'velocity_std': statistics.stdev(velocities) if len(velocities) > 1 else 0,
            'velocity_max': max(velocities) if velocities else 0,
            'click_frequency': len(self.mouse_buffer) / (time.time() - self.baseline_start_time) * 60 if self.baseline_start_time else 0,
            'movement_smoothness': self._calculate_movement_smoothness(velocities)
        }
        
    def _calculate_movement_smoothness(self, velocities: List[float]) -> float:
        """Calculate mouse movement smoothness score."""
        if len(velocities) < 2:
            return 1.0
            
        # Calculate smoothness based on velocity variation
        velocity_changes = [abs(velocities[i] - velocities[i-1]) 
                           for i in range(1, len(velocities))]
        
        if not velocity_changes:
            return 1.0
            
        avg_change = statistics.mean(velocity_changes)
        max_velocity = max(velocities) if velocities else 1
        
        # Normalize: lower change relative to max velocity = smoother
        smoothness = 1.0 - min(1.0, avg_change / max_velocity)
        return smoothness
        
    def _analyze_window_baseline(self) -> Dict[str, Any]:
        """Analyze window focus and switching patterns."""
        total_time = time.time() - (self.baseline_start_time or time.time())
        
        return {
            'average_window_time': statistics.mean(list(self.window_focus_times.values())) if self.window_focus_times else 0,
            'window_switch_frequency': len(self.window_focus_times) / (total_time / 60) if total_time > 0 else 0,
            'unique_windows': len(self.window_focus_times),
            'focus_distribution': dict(self.window_focus_times)
        }
        
    def _analyze_tab_switching_baseline(self) -> Dict[str, float]:
        """Analyze tab switching patterns."""
        if not self.tab_switches:
            return {}
            
        switch_speeds = [switch['time_spent'] for switch in self.tab_switches]
        total_time = time.time() - (self.baseline_start_time or time.time())
        
        return {
            'tab_switch_frequency': len(self.tab_switches) / (total_time / 60) if total_time > 0 else 0,
            'average_switch_speed': statistics.mean(switch_speeds) if switch_speeds else 0,
            'switch_speed_variance': statistics.variance(switch_speeds) if len(switch_speeds) > 1 else 0
        }
        
    def _analyze_timing_baseline(self) -> Dict[str, float]:
        """Analyze timing patterns from collected data."""
        # Get patterns from rhythm analyzer
        return self.typing_rhythm_analyzer.get_baseline_patterns()
        
    def _calculate_activity_rhythm(self) -> Dict[str, float]:
        """Calculate overall activity rhythm patterns."""
        if len(self.activity_buffer) < 10:
            return {}
            
        # Analyze activity distribution over time
        events_by_hour = defaultdict(int)
        events_by_minute = defaultdict(int)
        
        for event in self.activity_buffer:
            hour = int((event.timestamp - self.baseline_start_time) // 3600) if self.baseline_start_time else 0
            minute = int((event.timestamp - self.baseline_start_time) // 60) if self.baseline_start_time else 0
            
            events_by_hour[hour] += 1
            events_by_minute[minute] += 1
            
        return {
            'activity_consistency': self._calculate_activity_consistency(events_by_minute),
            'peak_activity_hour': max(events_by_hour.items(), key=lambda x: x[1])[0] if events_by_hour else 0,
            'activity_variance': statistics.variance(list(events_by_minute.values())) if len(events_by_minute) > 1 else 0
        }
        
    def _calculate_activity_consistency(self, events_by_minute: Dict[int, int]) -> float:
        """Calculate activity consistency score."""
        if len(events_by_minute) < 2:
            return 1.0
            
        values = list(events_by_minute.values())
        mean_activity = statistics.mean(values)
        
        if mean_activity == 0:
            return 1.0
            
        std_activity = statistics.stdev(values)
        cv = std_activity / mean_activity
        
        # Convert to consistency score (lower CV = higher consistency)
        return max(0.0, 1.0 - cv)
        
    def _extract_current_patterns(self) -> Dict[str, Dict[str, float]]:
        """Extract current behavior patterns for comparison."""
        current_time = time.time()
        recent_cutoff = current_time - 300  # Last 5 minutes
        
        # Get recent events
        recent_events = [e for e in self.activity_buffer if e.timestamp > recent_cutoff]
        
        # Extract keystroke patterns
        keystroke_patterns = self.typing_rhythm_analyzer.get_baseline_patterns()
        
        # Extract mouse patterns  
        mouse_patterns = self._analyze_mouse_baseline()
        
        # Extract application patterns
        app_patterns = dict(self.application_usage)
        
        # Extract timing patterns
        timing_patterns = self._analyze_timing_baseline()
        
        # Extract tab switching patterns
        tab_patterns = self._analyze_tab_switching_baseline()
        
        return {
            'keystroke': keystroke_patterns,
            'mouse': mouse_patterns,
            'applications': app_patterns,
            'timing': timing_patterns,
            'tab_switching': tab_patterns
        }
        
    def _compare_keystroke_patterns(self, current: Dict[str, float], baseline: Dict[str, float]) -> float:
        """Compare keystroke patterns."""
        from .behavioral_analyzers import BehaviorPatternMatcher
        matcher = BehaviorPatternMatcher()
        return matcher.compare_keystroke_patterns(current, baseline)
        
    def _compare_mouse_patterns(self, current: Dict[str, float], baseline: Dict[str, float]) -> float:
        """Compare mouse patterns."""
        from .behavioral_analyzers import BehaviorPatternMatcher
        matcher = BehaviorPatternMatcher()
        return matcher.compare_mouse_patterns(current, baseline)
        
    def _compare_application_patterns(self, current: Dict[str, Any], baseline: Dict[str, Any]) -> float:
        """Compare application usage patterns."""
        from .behavioral_analyzers import BehaviorPatternMatcher
        matcher = BehaviorPatternMatcher()
        return matcher.compare_application_patterns(current, baseline)
        
    def _compare_tab_patterns(self, current: Dict[str, float], baseline: Dict[str, float]) -> float:
        """Compare tab switching patterns."""
        if not baseline or not current:
            return 0.5
            
        # Simple comparison of tab switching frequency
        baseline_freq = baseline.get('tab_switch_frequency', 0)
        current_freq = current.get('tab_switch_frequency', 0)
        
        if baseline_freq == 0 and current_freq == 0:
            return 0.0
        elif baseline_freq == 0:
            return 1.0
        else:
            deviation = abs(current_freq - baseline_freq) / baseline_freq
            return min(1.0, deviation)
            
    def _compare_timing_patterns(self, current: Dict[str, float], baseline: Dict[str, float]) -> float:
        """Compare timing patterns."""
        from .behavioral_analyzers import BehaviorPatternMatcher
        matcher = BehaviorPatternMatcher()
        return matcher.compare_timing_patterns(current, baseline)