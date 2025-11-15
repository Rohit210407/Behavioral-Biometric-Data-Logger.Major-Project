"""
Mouse and touch interaction pattern collector for behavioral biometrics.
"""

import time
import threading
import math
from typing import Dict, List, Optional, Tuple, Any
from collections import deque
from dataclasses import dataclass, field

# Define the classes we need locally to avoid import issues
@dataclass
class MouseEvent:
    """Represents a mouse interaction event."""
    event_type: str  # 'move', 'click', 'scroll'
    position: Tuple[int, int]
    timestamp: float
    velocity: Optional[float] = None
    acceleration: Optional[float] = None
    pressure: Optional[float] = None  # For touch devices

@dataclass
class BiometricFeatures:
    """Container for extracted behavioral biometric features."""
    user_id: str
    session_id: str
    timestamp: float
    keystroke_features: Dict[str, float] = field(default_factory=dict)
    mouse_features: Dict[str, float] = field(default_factory=dict)
    confidence_score: float = 0.0

class BiometricCollector:
    """Abstract base class for behavioral biometric data collectors."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_active = False
        self.data_queue = None  # Simplified
        self._lock = threading.Lock()
        
    def start_collection(self) -> None:
        """Start collecting biometric data."""
        pass
        
    def stop_collection(self) -> None:
        """Stop collecting biometric data."""
        pass
        
    def get_features(self) -> Optional[BiometricFeatures]:
        """Extract features from collected data."""
        pass

class MouseCollector(BiometricCollector):
    """Collects and analyzes mouse movement and click patterns."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.mouse_buffer = deque(maxlen=config.get('sample_window', 100))
        self.last_position = None
        self.last_timestamp = None
        self.click_timestamps = deque(maxlen=20)
        
    def start_collection(self) -> None:
        """Start mouse monitoring."""
        if self.is_active:
            return
        self.is_active = True
        self._setup_mouse_listener()
        
    def stop_collection(self) -> None:
        """Stop mouse monitoring."""
        self.is_active = False
        if hasattr(self, 'listener'):
            self.listener.stop()
            
    def _setup_mouse_listener(self) -> None:
        """Set up mouse event listeners."""
        try:
            from pynput import mouse
            
            def on_move(x, y):
                if not self.is_active:
                    return
                timestamp = time.time()
                velocity, acceleration = self._calculate_motion_metrics((x, y), timestamp)
                event = MouseEvent(event_type='move', position=(x, y), timestamp=timestamp, velocity=velocity, acceleration=acceleration)
                self._add_mouse_event(event)
                
            def on_click(x, y, button, pressed):
                if not self.is_active:
                    return
                timestamp = time.time()
                if pressed:
                    self.click_timestamps.append(timestamp)
                event = MouseEvent(event_type='click', position=(x, y), timestamp=timestamp)
                self._add_mouse_event(event)
                
            self.listener = mouse.Listener(on_move=on_move, on_click=on_click)
            self.listener.start()
        except ImportError:
            raise ImportError("pynput required for mouse collection")
            
    def _calculate_motion_metrics(self, position: Tuple[int, int], 
                                timestamp: float) -> Tuple[Optional[float], Optional[float]]:
        """Calculate velocity and acceleration."""
        if self.last_position is None or self.last_timestamp is None:
            self.last_position = position
            self.last_timestamp = timestamp
            return None, None
            
        dx = position[0] - self.last_position[0]
        dy = position[1] - self.last_position[1]
        distance = math.sqrt(dx**2 + dy**2)
        dt = timestamp - self.last_timestamp
        
        velocity = distance / dt if dt > 0 else 0
        acceleration = None
        if hasattr(self, 'last_velocity') and self.last_velocity is not None:
            acceleration = (velocity - self.last_velocity) / dt if dt > 0 else 0
            
        self.last_velocity = velocity
        self.last_position = position
        self.last_timestamp = timestamp
        return velocity, acceleration
        
    def _add_mouse_event(self, event: MouseEvent) -> None:
        """Add mouse event to buffer."""
        with self._lock:
            self.mouse_buffer.append(event)
            
    def get_features(self) -> Optional[BiometricFeatures]:
        """Extract mouse features."""
        with self._lock:
            if len(self.mouse_buffer) < 10:
                return None
            features = self._extract_mouse_features()
            return BiometricFeatures(
                user_id="current_user",
                session_id="current_session", 
                timestamp=time.time(),
                mouse_features=features
            )
            
    def _extract_mouse_features(self) -> Dict[str, float]:
        """Extract numerical features from mouse events."""
        move_events = [e for e in self.mouse_buffer if e.event_type == 'move']
        velocities = [e.velocity for e in move_events if e.velocity is not None]
        
        features = {}
        if velocities:
            features.update({
                'velocity_mean': sum(velocities) / len(velocities),
                'velocity_std': self._calculate_std(velocities),
                'velocity_max': max(velocities)
            })
            
        # Click intervals
        if len(self.click_timestamps) >= 2:
            intervals = [self.click_timestamps[i] - self.click_timestamps[i-1] 
                        for i in range(1, len(self.click_timestamps))]
            features['click_interval_mean'] = sum(intervals) / len(intervals)
            
        return features
        
    @staticmethod
    def _calculate_std(values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5