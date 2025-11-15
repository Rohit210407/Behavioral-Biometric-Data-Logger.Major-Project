"""
Specialized behavioral analyzers for advanced imposter detection.
"""

import time
import statistics
from collections import deque, defaultdict
from typing import Dict, List, Any, Optional

class InputFloodDetector:
    """Detects suspicious input flooding patterns."""
    
    def __init__(self):
        self.keystroke_timestamps = deque(maxlen=100)
        self.click_timestamps = deque(maxlen=50)
        self.flood_threshold = 20  # keystrokes per second
        self.suspicious_patterns = []
        
    def add_keystroke(self, timestamp: float):
        """Add keystroke timestamp for flood detection."""
        self.keystroke_timestamps.append(timestamp)
        self._check_flood_pattern()
        
    def add_click(self, timestamp: float):
        """Add click timestamp for flood detection."""
        self.click_timestamps.append(timestamp)
        
    def _check_flood_pattern(self):
        """Check for input flooding patterns."""
        if len(self.keystroke_timestamps) < 10:
            return
            
        # Check last 1 second
        current_time = time.time()
        recent_keystrokes = [
            ts for ts in self.keystroke_timestamps 
            if current_time - ts <= 1.0
        ]
        
        if len(recent_keystrokes) > self.flood_threshold:
            self.suspicious_patterns.append({
                'type': 'input_flood',
                'timestamp': current_time,
                'rate': len(recent_keystrokes),
                'severity': 'high'
            })
            
        # Check for robotic patterns (too consistent timing)
        if len(self.keystroke_timestamps) >= 20:
            intervals = [
                self.keystroke_timestamps[i] - self.keystroke_timestamps[i-1]
                for i in range(1, min(21, len(self.keystroke_timestamps)))
            ]
            
            if len(intervals) > 5:
                std_dev = statistics.stdev(intervals)
                if std_dev < 0.01:  # Too consistent (robotic)
                    self.suspicious_patterns.append({
                        'type': 'robotic_input',
                        'timestamp': current_time,
                        'consistency': std_dev,
                        'severity': 'medium'
                    })
                    
    def get_suspicion_score(self) -> float:
        """Get current suspicion score (0.0 to 1.0)."""
        if not self.suspicious_patterns:
            return 0.0
            
        current_time = time.time()
        recent_patterns = [
            p for p in self.suspicious_patterns
            if current_time - p['timestamp'] <= 30.0  # Last 30 seconds
        ]
        
        if not recent_patterns:
            return 0.0
            
        # Calculate score based on severity and frequency
        score = 0.0
        for pattern in recent_patterns:
            if pattern['severity'] == 'high':
                score += 0.4
            elif pattern['severity'] == 'medium':
                score += 0.2
            else:
                score += 0.1
                
        return min(1.0, score)

class TypingRhythmAnalyzer:
    """Analyzes typing rhythm and patterns."""
    
    def __init__(self):
        self.keystroke_intervals = deque(maxlen=200)
        self.typing_bursts = []
        self.pause_patterns = []
        self.baseline_rhythm = None
        
    def add_keystroke(self, timestamp: float):
        """Add keystroke for rhythm analysis."""
        if self.keystroke_intervals:
            interval = timestamp - self.keystroke_intervals[-1]
            self.keystroke_intervals.append(interval)
            self._analyze_typing_pattern(timestamp, interval)
        else:
            self.keystroke_intervals.append(timestamp)
            
    def _analyze_typing_pattern(self, timestamp: float, interval: float):
        """Analyze typing patterns and rhythms."""
        
        # Detect typing bursts
        if interval < 0.1:  # Fast typing
            if not self.typing_bursts or timestamp - self.typing_bursts[-1]['end'] > 2.0:
                # New burst
                self.typing_bursts.append({
                    'start': timestamp,
                    'end': timestamp,
                    'keystrokes': 1
                })
            else:
                # Continue burst
                self.typing_bursts[-1]['end'] = timestamp
                self.typing_bursts[-1]['keystrokes'] += 1
                
        # Detect pauses
        elif interval > 2.0:  # Long pause
            self.pause_patterns.append({
                'timestamp': timestamp,
                'duration': interval,
                'type': 'thinking' if interval < 10.0 else 'distraction'
            })
            
    def get_baseline_patterns(self) -> Dict[str, float]:
        """Get baseline typing rhythm patterns."""
        if len(self.keystroke_intervals) < 50:
            return {}
            
        intervals = list(self.keystroke_intervals)
        
        patterns = {
            'mean_interval': statistics.mean(intervals),
            'std_interval': statistics.stdev(intervals) if len(intervals) > 1 else 0,
            'median_interval': statistics.median(intervals),
            'typing_burst_frequency': len(self.typing_bursts) / (time.time() - (self.keystroke_intervals[0] if self.keystroke_intervals else time.time())) * 60,
            'average_burst_length': statistics.mean([b['keystrokes'] for b in self.typing_bursts]) if self.typing_bursts else 0,
            'pause_frequency': len(self.pause_patterns) / (time.time() - (self.keystroke_intervals[0] if self.keystroke_intervals else time.time())) * 60,
            'rhythm_consistency': self._calculate_rhythm_consistency()
        }
        
        self.baseline_rhythm = patterns
        return patterns
        
    def _calculate_rhythm_consistency(self) -> float:
        """Calculate typing rhythm consistency score."""
        if len(self.keystroke_intervals) < 20:
            return 0.5
            
        # Analyze pattern regularity
        intervals = list(self.keystroke_intervals)[-20:]  # Last 20 intervals
        
        # Calculate coefficient of variation
        mean_interval = statistics.mean(intervals)
        if mean_interval == 0:
            return 0.0
            
        std_interval = statistics.stdev(intervals)
        cv = std_interval / mean_interval
        
        # Convert to consistency score (lower CV = higher consistency)
        consistency = max(0.0, 1.0 - cv)
        return consistency

class MultitaskingAnalyzer:
    """Analyzes multitasking behavior patterns."""
    
    def __init__(self):
        self.window_switches = deque(maxlen=100)
        self.application_timeline = []
        self.multitask_intensity = []
        
    def update(self, active_processes: int, active_apps: int):
        """Update multitasking metrics."""
        timestamp = time.time()
        
        intensity = {
            'timestamp': timestamp,
            'active_processes': active_processes,
            'active_apps': active_apps,
            'intensity_score': self._calculate_intensity_score(active_processes, active_apps)
        }
        
        self.multitask_intensity.append(intensity)
        
        # Keep only recent data
        cutoff_time = timestamp - 300  # Last 5 minutes
        self.multitask_intensity = [
            m for m in self.multitask_intensity 
            if m['timestamp'] > cutoff_time
        ]
        
    def _calculate_intensity_score(self, processes: int, apps: int) -> float:
        """Calculate multitasking intensity score."""
        # Normalize based on typical ranges
        process_score = min(1.0, processes / 100.0)
        app_score = min(1.0, apps / 10.0)
        
        return (process_score + app_score) / 2.0
        
    def get_baseline_patterns(self) -> Dict[str, float]:
        """Get baseline multitasking patterns."""
        if not self.multitask_intensity:
            return {}
            
        intensities = [m['intensity_score'] for m in self.multitask_intensity]
        
        return {
            'average_intensity': statistics.mean(intensities),
            'intensity_variance': statistics.variance(intensities) if len(intensities) > 1 else 0,
            'max_intensity': max(intensities),
            'intensity_trend': self._calculate_trend(intensities)
        }
        
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend direction (-1 to 1)."""
        if len(values) < 2:
            return 0.0
            
        # Simple linear regression slope
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(values)
        
        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
            
        slope = numerator / denominator
        return max(-1.0, min(1.0, slope * 10))  # Normalize

class BehaviorPatternMatcher:
    """Advanced pattern matching for imposter detection."""
    
    def __init__(self):
        self.known_patterns = {}
        self.anomaly_threshold = 0.3
        
    def compare_keystroke_patterns(self, current: Dict[str, float], baseline: Dict[str, float]) -> float:
        """Compare current keystroke patterns with baseline."""
        if not baseline or not current:
            return 0.5
            
        deviations = []
        
        for key in baseline:
            if key in current:
                baseline_val = baseline[key]
                current_val = current[key]
                
                if baseline_val == 0:
                    deviation = 1.0 if current_val != 0 else 0.0
                else:
                    deviation = abs(current_val - baseline_val) / baseline_val
                    
                deviations.append(min(1.0, deviation))
                
        return statistics.mean(deviations) if deviations else 0.5
        
    def compare_mouse_patterns(self, current: Dict[str, float], baseline: Dict[str, float]) -> float:
        """Compare mouse movement patterns."""
        if not baseline or not current:
            return 0.5
            
        # Focus on key metrics
        key_metrics = ['velocity_mean', 'click_frequency', 'movement_smoothness']
        deviations = []
        
        for metric in key_metrics:
            if metric in baseline and metric in current:
                baseline_val = baseline[metric]
                current_val = current[metric]
                
                if baseline_val == 0:
                    deviation = 1.0 if current_val != 0 else 0.0
                else:
                    # Use relative deviation with caps
                    deviation = min(1.0, abs(current_val - baseline_val) / baseline_val)
                    
                deviations.append(deviation)
                
        return statistics.mean(deviations) if deviations else 0.5
        
    def compare_application_patterns(self, current: Dict[str, Any], baseline: Dict[str, Any]) -> float:
        """Compare application usage patterns."""
        if not baseline or not current:
            return 0.5
            
        # Calculate Jaccard similarity for applications
        baseline_apps = set(baseline.keys())
        current_apps = set(current.keys())
        
        if not baseline_apps and not current_apps:
            return 0.0
            
        intersection = len(baseline_apps.intersection(current_apps))
        union = len(baseline_apps.union(current_apps))
        
        jaccard_similarity = intersection / union if union > 0 else 0.0
        
        # Convert similarity to deviation (0 = identical, 1 = completely different)
        return 1.0 - jaccard_similarity
        
    def compare_timing_patterns(self, current: Dict[str, float], baseline: Dict[str, float]) -> float:
        """Compare timing and rhythm patterns."""
        if not baseline or not current:
            return 0.5
            
        # Focus on rhythm consistency and pause patterns
        timing_metrics = ['rhythm_consistency', 'pause_frequency', 'typing_burst_frequency']
        deviations = []
        
        for metric in timing_metrics:
            if metric in baseline and metric in current:
                baseline_val = baseline[metric]
                current_val = current[metric]
                
                # Timing patterns are more sensitive
                if baseline_val == 0:
                    deviation = 1.0 if current_val != 0 else 0.0
                else:
                    deviation = min(1.0, abs(current_val - baseline_val) / baseline_val)
                    
                deviations.append(deviation)
                
        return statistics.mean(deviations) if deviations else 0.5
        
    def detect_behavioral_anomalies(self, activity_events: List[Any]) -> List[Dict[str, Any]]:
        """Detect specific behavioral anomalies."""
        anomalies = []
        
        if len(activity_events) < 10:
            return anomalies
            
        # Check for impossible typing speeds
        keystroke_events = [e for e in activity_events if e.event_type == 'keystroke']
        if len(keystroke_events) >= 10:
            intervals = []
            for i in range(1, min(11, len(keystroke_events))):
                interval = keystroke_events[i].timestamp - keystroke_events[i-1].timestamp
                intervals.append(interval)
                
            if intervals:
                min_interval = min(intervals)
                if min_interval < 0.05:  # Less than 50ms between keystrokes
                    anomalies.append({
                        'type': 'impossible_typing_speed',
                        'severity': 'high',
                        'details': f'Minimum interval: {min_interval:.3f}s'
                    })
                    
        # Check for unnatural mouse movements
        mouse_events = [e for e in activity_events if e.event_type == 'mouse_move']
        if len(mouse_events) >= 5:
            velocities = [e.data.get('velocity', 0) for e in mouse_events[-5:]]
            if velocities:
                max_velocity = max(velocities)
                if max_velocity > 5000:  # Unrealistic mouse speed
                    anomalies.append({
                        'type': 'unrealistic_mouse_speed',
                        'severity': 'medium',
                        'details': f'Max velocity: {max_velocity:.1f} px/s'
                    })
                    
        return anomalies