"""
Core behavioral biometrics module for keystroke and mouse pattern capture.
Implements real-time behavioral data collection with privacy protection.
"""

import time
import threading
import queue
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import deque
import hashlib
import json

@dataclass
class KeystrokeEvent:
    """Represents a single keystroke event with timing data."""
    key: str
    event_type: str  # 'press' or 'release'
    timestamp: float
    dwell_time: Optional[float] = None  # Time key was held down
    flight_time: Optional[float] = None  # Time since previous key release
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'key_hash': hashlib.sha256(self.key.encode()).hexdigest()[:8],  # Privacy: hash key
            'event_type': self.event_type,
            'timestamp': self.timestamp,
            'dwell_time': self.dwell_time,
            'flight_time': self.flight_time
        }

@dataclass
class MouseEvent:
    """Represents a mouse interaction event."""
    event_type: str  # 'move', 'click', 'scroll'
    position: Tuple[int, int]
    timestamp: float
    velocity: Optional[float] = None
    acceleration: Optional[float] = None
    pressure: Optional[float] = None  # For touch devices
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'event_type': self.event_type,
            'position': self.position,
            'timestamp': self.timestamp,
            'velocity': self.velocity,
            'acceleration': self.acceleration,
            'pressure': self.pressure
        }

@dataclass
class BiometricFeatures:
    """Container for extracted behavioral biometric features."""
    user_id: str
    session_id: str
    timestamp: float
    keystroke_features: Dict[str, float] = field(default_factory=dict)
    mouse_features: Dict[str, float] = field(default_factory=dict)
    confidence_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/transmission."""
        return {
            'user_id': self.user_id,
            'session_id': self.session_id,
            'timestamp': self.timestamp,
            'keystroke_features': self.keystroke_features,
            'mouse_features': self.mouse_features,
            'confidence_score': self.confidence_score
        }

class BiometricCollector(ABC):
    """Abstract base class for behavioral biometric data collectors."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_active = False
        self.data_queue = queue.Queue(maxsize=1000)
        self._lock = threading.Lock()
        
    @abstractmethod
    def start_collection(self) -> None:
        """Start collecting biometric data."""
        pass
        
    @abstractmethod
    def stop_collection(self) -> None:
        """Stop collecting biometric data."""
        pass
        
    @abstractmethod
    def get_features(self) -> Optional[BiometricFeatures]:
        """Extract features from collected data."""
        pass

class KeystrokeCollector(BiometricCollector):
    """Collects and analyzes keystroke dynamics for behavioral authentication."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.keystroke_buffer = deque(maxlen=config.get('sample_window', 50))
        self.key_press_times = {}  # Track key press times for dwell calculation
        self.last_release_time = None
        
    def start_collection(self) -> None:
        """Start keystroke monitoring."""
        if self.is_active:
            return
            
        self.is_active = True
        self._setup_keystroke_listener()
        
    def stop_collection(self) -> None:
        """Stop keystroke monitoring."""
        self.is_active = False
        if hasattr(self, 'listener'):
            self.listener.stop()
            
    def _setup_keystroke_listener(self) -> None:
        """Set up the keystroke event listener."""
        try:
            from pynput import keyboard
            
            def on_press(key):
                if not self.is_active:
                    return
                    
                timestamp = time.time()
                key_str = self._key_to_string(key)
                
                # Store press time for dwell calculation
                self.key_press_times[key_str] = timestamp
                
                # Calculate flight time (time since last key release)
                flight_time = None
                if self.last_release_time:
                    flight_time = timestamp - self.last_release_time
                
                event = KeystrokeEvent(
                    key=key_str,
                    event_type='press',
                    timestamp=timestamp,
                    flight_time=flight_time
                )
                
                self._add_keystroke_event(event)
                
            def on_release(key):
                if not self.is_active:
                    return
                    
                timestamp = time.time()
                key_str = self._key_to_string(key)
                
                # Calculate dwell time
                dwell_time = None
                if key_str in self.key_press_times:
                    dwell_time = timestamp - self.key_press_times[key_str]
                    del self.key_press_times[key_str]
                
                event = KeystrokeEvent(
                    key=key_str,
                    event_type='release',
                    timestamp=timestamp,
                    dwell_time=dwell_time
                )
                
                self._add_keystroke_event(event)
                self.last_release_time = timestamp
                
            self.listener = keyboard.Listener(
                on_press=on_press,
                on_release=on_release
            )
            self.listener.start()
            
        except ImportError:
            raise ImportError("pynput library is required for keystroke collection")
            
    def _key_to_string(self, key) -> str:
        """Convert key object to string representation."""
        try:
            return key.char if hasattr(key, 'char') and key.char else str(key)
        except AttributeError:
            return str(key)
            
    def _add_keystroke_event(self, event: KeystrokeEvent) -> None:
        """Add keystroke event to buffer thread-safely."""
        with self._lock:
            self.keystroke_buffer.append(event)
            
    def get_features(self) -> Optional[BiometricFeatures]:
        """Extract keystroke dynamics features from collected data."""
        with self._lock:
            if len(self.keystroke_buffer) < 10:  # Need minimum events
                return None
                
            # Extract timing features
            features = self._extract_keystroke_features()
            
            return BiometricFeatures(
                user_id="current_user",  # Will be set by session manager
                session_id="current_session",  # Will be set by session manager
                timestamp=time.time(),
                keystroke_features=features
            )
            
    def _extract_keystroke_features(self) -> Dict[str, float]:
        """Extract numerical features from keystroke events."""
        dwell_times = []
        flight_times = []
        
        for event in self.keystroke_buffer:
            if event.dwell_time is not None:
                dwell_times.append(event.dwell_time)
            if event.flight_time is not None:
                flight_times.append(event.flight_time)
                
        features = {}
        
        # Dwell time statistics
        if dwell_times:
            features.update({
                'dwell_mean': sum(dwell_times) / len(dwell_times),
                'dwell_std': self._calculate_std(dwell_times),
                'dwell_min': min(dwell_times),
                'dwell_max': max(dwell_times)
            })
            
        # Flight time statistics
        if flight_times:
            features.update({
                'flight_mean': sum(flight_times) / len(flight_times),
                'flight_std': self._calculate_std(flight_times),
                'flight_min': min(flight_times),
                'flight_max': max(flight_times)
            })
            
        # Typing rhythm features
        features.update(self._extract_rhythm_features())
        
        return features
        
    def _extract_rhythm_features(self) -> Dict[str, float]:
        """Extract typing rhythm and consistency features."""
        events = list(self.keystroke_buffer)
        if len(events) < 5:
            return {}
            
        # Calculate inter-keystroke intervals
        intervals = []
        for i in range(1, len(events)):
            interval = events[i].timestamp - events[i-1].timestamp
            intervals.append(interval)
            
        if not intervals:
            return {}
            
        # Rhythm consistency (coefficient of variation)
        mean_interval = sum(intervals) / len(intervals)
        std_interval = self._calculate_std(intervals)
        rhythm_consistency = std_interval / mean_interval if mean_interval > 0 else 0
        
        # Typing speed (keys per minute)
        total_time = events[-1].timestamp - events[0].timestamp
        typing_speed = (len(events) / total_time) * 60 if total_time > 0 else 0
        
        return {
            'rhythm_consistency': rhythm_consistency,
            'typing_speed': typing_speed,
            'mean_interval': mean_interval,
            'interval_variance': std_interval ** 2
        }
        
    @staticmethod
    def _calculate_std(values: List[float]) -> float:
        """Calculate standard deviation of values."""
        if len(values) < 2:
            return 0.0
            
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5