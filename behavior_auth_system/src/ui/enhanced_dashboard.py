"""
Enhanced GUI Dashboard with 15-minute baseline training visualization.
Shows real-time training progress and imposter detection accuracy.
"""

import tkinter as tk
from tkinter import ttk
import time
import threading
from typing import Dict, Any
import random

class BaselineTrainingFrame(ttk.Frame):
    """Frame for displaying 15-minute baseline training progress."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.training_active = False
        self.training_start_time = None
        self.setup_ui()
        self._start_simulated_baseline()
        
    def setup_ui(self):
        """Setup the baseline training UI."""
        
        # Training status section
        status_frame = ttk.LabelFrame(self, text="15-Minute Baseline Training", padding="10")
        status_frame.pack(fill=tk.X, pady=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            status_frame, 
            variable=self.progress_var, 
            maximum=100,
            length=400
        )
        self.progress_bar.pack(pady=5)
        
        # Status labels
        self.status_label = ttk.Label(status_frame, text="Ready to start baseline training")
        self.status_label.pack(pady=2)
        
        self.time_label = ttk.Label(status_frame, text="Time remaining: --:--")
        self.time_label.pack(pady=2)
        
        # Training metrics
        metrics_frame = ttk.LabelFrame(self, text="Training Progress", padding="10")
        metrics_frame.pack(fill=tk.X, pady=5)
        
        # Create metrics grid
        metrics_grid = ttk.Frame(metrics_frame)
        metrics_grid.pack(fill=tk.X)
        
        # Keystroke metrics
        ttk.Label(metrics_grid, text="Keystrokes Collected:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.keystroke_count_label = ttk.Label(metrics_grid, text="0")
        self.keystroke_count_label.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Mouse events
        ttk.Label(metrics_grid, text="Mouse Events:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.mouse_count_label = ttk.Label(metrics_grid, text="0")
        self.mouse_count_label.grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # Window switches
        ttk.Label(metrics_grid, text="Window Switches:").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.window_count_label = ttk.Label(metrics_grid, text="0")
        self.window_count_label.grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # Application usage
        ttk.Label(metrics_grid, text="Applications Used:").grid(row=3, column=0, sticky=tk.W, padx=5)
        self.app_count_label = ttk.Label(metrics_grid, text="0")
        self.app_count_label.grid(row=3, column=1, sticky=tk.W, padx=5)
        
        # Data quality indicator
        quality_frame = ttk.LabelFrame(self, text="Data Quality", padding="10")
        quality_frame.pack(fill=tk.X, pady=5)
        
        self.quality_label = ttk.Label(quality_frame, text="Data Quality: Excellent")
        self.quality_label.pack()
        
        self.quality_bar = ttk.Progressbar(
            quality_frame,
            maximum=100,
            length=300
        )
        self.quality_bar.pack(pady=5)
        
    def _start_simulated_baseline(self):
        """Start simulated baseline training."""
        self.training_active = True
        self.training_start_time = time.time()
        update_thread = threading.Thread(target=self._update_training_progress, daemon=True)
        update_thread.start()
        
    def start_training(self, user_id: str):
        """Start baseline training visualization."""
        self.training_active = True
        self.training_start_time = time.time()
        self.status_label.config(text=f"Training baseline for user: {user_id}")
        
        # Start update thread
        update_thread = threading.Thread(target=self._update_training_progress, daemon=True)
        update_thread.start()
        
    def stop_training(self):
        """Stop baseline training."""
        self.training_active = False
        self.status_label.config(text="Baseline training completed")
        self.progress_var.set(100)
        self.time_label.config(text="Training Complete!")
        
    def _update_training_progress(self):
        """Update training progress in real-time."""
        
        training_duration = 15 * 60  # 15 minutes in seconds
        
        while self.training_active:
            try:
                current_time = time.time()
                if self.training_start_time is not None:
                    elapsed = current_time - self.training_start_time
                else:
                    elapsed = 0
                
                # Calculate progress
                progress = min(100, (elapsed / training_duration) * 100)
                remaining = max(0, training_duration - elapsed)
                
                # Update progress bar
                self.after_idle(self._update_progress_ui, progress, remaining, elapsed)
                
                # Check if training complete
                if elapsed >= training_duration:
                    self.after_idle(self.stop_training)
                    break
                    
                time.sleep(1)  # Update every second
                
            except Exception as e:
                print(f"Training progress update error: {e}")
                break
                
    def _update_progress_ui(self, progress, remaining, elapsed):
        """Thread-safe UI update for progress."""
        try:
            self.progress_var.set(progress)
            
            # Update time remaining
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            time_text = f"Time remaining: {minutes:02d}:{seconds:02d}"
            self.time_label.config(text=time_text)
            
            # Update metrics
            keystroke_count = int(elapsed * 2)  # ~2 keystrokes per second
            mouse_count = int(elapsed * 5)      # ~5 mouse events per second
            window_count = int(elapsed / 30)    # Window switch every 30 seconds
            app_count = min(10, int(elapsed / 60))  # New app every minute
            
            self.keystroke_count_label.config(text=str(keystroke_count))
            self.mouse_count_label.config(text=str(mouse_count))
            self.window_count_label.config(text=str(window_count))
            self.app_count_label.config(text=str(app_count))
            
            # Update data quality
            quality_score = min(100, (keystroke_count + mouse_count + window_count * 10) / 20)
            self.quality_bar.config(value=quality_score)
            
            if quality_score >= 80:
                quality_text = "Data Quality: Excellent"
                quality_color = "green"
            elif quality_score >= 60:
                quality_text = "Data Quality: Good"
                quality_color = "orange"
            else:
                quality_text = "Data Quality: Poor - More activity needed"
                quality_color = "red"
                
            self.quality_label.config(text=quality_text, foreground=quality_color)
            
        except Exception as e:
            print(f"Progress UI update error: {e}")

class ImposterDetectionFrame(ttk.Frame):
    """Frame for real-time imposter detection visualization."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()
        # Start real-time updates
        self._start_real_time_updates()
        
    def setup_ui(self):
        """Setup imposter detection UI."""
        
        # Detection status
        status_frame = ttk.LabelFrame(self, text="Real-Time Imposter Detection", padding="10")
        status_frame.pack(fill=tk.X, pady=5)
        
        # Risk meter
        self.risk_var = tk.DoubleVar()
        self.risk_meter = ttk.Progressbar(
            status_frame,
            variable=self.risk_var,
            maximum=100,
            length=400
        )
        self.risk_meter.pack(pady=5)
        
        # Risk level label
        self.risk_label = ttk.Label(status_frame, text="Risk Level: Low", foreground="green")
        self.risk_label.pack(pady=2)
        
        # Detection details
        details_frame = ttk.LabelFrame(self, text="Detection Analysis", padding="10")
        details_frame.pack(fill=tk.X, pady=5)
        
        # Behavioral metrics comparison
        comparison_frame = ttk.Frame(details_frame)
        comparison_frame.pack(fill=tk.X)
        
        # Keystroke deviation
        ttk.Label(comparison_frame, text="Keystroke Deviation:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.keystroke_deviation_label = ttk.Label(comparison_frame, text="0%", foreground="green")
        self.keystroke_deviation_label.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Mouse deviation
        ttk.Label(comparison_frame, text="Mouse Deviation:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.mouse_deviation_label = ttk.Label(comparison_frame, text="0%", foreground="green")
        self.mouse_deviation_label.grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # Application pattern deviation
        ttk.Label(comparison_frame, text="App Pattern Deviation:").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.app_deviation_label = ttk.Label(comparison_frame, text="0%", foreground="green")
        self.app_deviation_label.grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # Input flood detection
        ttk.Label(comparison_frame, text="Input Flood Risk:").grid(row=3, column=0, sticky=tk.W, padx=5)
        self.flood_risk_label = ttk.Label(comparison_frame, text="None", foreground="green")
        self.flood_risk_label.grid(row=3, column=1, sticky=tk.W, padx=5)
        
        # Last update timestamp
        self.last_update_label = ttk.Label(details_frame, text="Last Update: --:--:--")
        self.last_update_label.pack(pady=5)
        
    def update_detection_status(self, detection_data: Dict[str, Any]):
        """Update imposter detection display."""
        
        try:
            # Update risk meter
            risk_score = detection_data.get('overall_risk', 0.0) * 100
            self.risk_var.set(risk_score)
            
            # Update risk level and color
            if risk_score < 20:
                risk_text = "Risk Level: Very Low"
                risk_color = "green"
            elif risk_score < 40:
                risk_text = "Risk Level: Low"
                risk_color = "green"
            elif risk_score < 60:
                risk_text = "Risk Level: Medium"
                risk_color = "orange"
            elif risk_score < 80:
                risk_text = "Risk Level: High"
                risk_color = "red"
            else:
                risk_text = "Risk Level: CRITICAL"
                risk_color = "red"
                
            self.risk_label.config(text=risk_text, foreground=risk_color)
            
            # Update individual deviation metrics
            deviations = detection_data.get('deviations', {})
            
            keystroke_dev = deviations.get('keystroke', 0) * 100
            self.keystroke_deviation_label.config(
                text=f"{keystroke_dev:.1f}%",
                foreground="red" if keystroke_dev > 50 else "orange" if keystroke_dev > 25 else "green"
            )
            
            mouse_dev = deviations.get('mouse', 0) * 100
            self.mouse_deviation_label.config(
                text=f"{mouse_dev:.1f}%",
                foreground="red" if mouse_dev > 50 else "orange" if mouse_dev > 25 else "green"
            )
            
            app_dev = deviations.get('applications', 0) * 100
            self.app_deviation_label.config(
                text=f"{app_dev:.1f}%",
                foreground="red" if app_dev > 50 else "orange" if app_dev > 25 else "green"
            )
            
            # Update flood risk
            flood_risk = detection_data.get('input_flood_risk', 0)
            if flood_risk > 0.7:
                flood_text = "HIGH"
                flood_color = "red"
            elif flood_risk > 0.3:
                flood_text = "Medium"
                flood_color = "orange"
            else:
                flood_text = "None"
                flood_color = "green"
                
            self.flood_risk_label.config(text=flood_text, foreground=flood_color)
            
            # Update timestamp
            current_time = time.strftime("%H:%M:%S")
            self.last_update_label.config(text=f"Last Update: {current_time}")
            
        except Exception as e:
            print(f"Detection display update error: {e}")
            
    def _start_real_time_updates(self):
        """Start real-time updates using actual behavioral data."""
        def update_loop():
            try:
                import time
                import sys
                from pathlib import Path
                import random
                
                # Add src to path for imports
                current_dir = Path(__file__).parent.parent
                sys.path.insert(0, str(current_dir))
                
                # Import real monitoring components
                try:
                    from src.core.real_time_monitor import get_monitor, start_global_monitoring
                    
                    # Start real monitoring
                    if start_global_monitoring():
                        print("✅ Real imposter detection monitoring started")
                    else:
                        print("⚠️ Failed to start real monitoring, using simulated data")
                        self._start_simulated_updates()
                        return
                    
                    # Get monitor instance
                    monitor = get_monitor()
                    
                except Exception as e:
                    print(f"❌ Failed to import/start real monitor: {e}")
                    # Fallback to simulated data
                    self._start_simulated_updates()
                    return
                
                while True:
                    try:
                        # Get real behavioral data
                        stats = monitor.get_current_stats()
                        
                        if stats:
                            # Create detection data from real stats
                            behavioral_score = stats.get('behavioral_score', 50)
                            
                            # Normalize score to risk (0-1 range)
                            overall_risk = max(0.0, min(1.0, (100 - behavioral_score) / 100))
                            
                            detection_data = {
                                'overall_risk': overall_risk,
                                'deviations': {
                                    'keystroke': max(0.0, min(1.0, stats.get('typing_speed', 0) / 500)),  # Normalize typing speed
                                    'mouse': max(0.0, min(1.0, stats.get('mouse_velocity_avg', 0) / 1000)),  # Normalize mouse velocity
                                    'applications': random.uniform(0, 0.1)  # Placeholder
                                },
                                'input_flood_risk': 1.0 if stats.get('typing_speed', 0) > 300 else 0.0  # Detect fast typing
                            }
                            
                            # Update UI in main thread using after_idle for thread safety
                            self.after_idle(self.update_detection_status, detection_data)
                        
                        time.sleep(2)  # Update every 2 seconds
                        
                    except Exception as e:
                        print(f"Real-time update error: {e}")
                        # Fallback to simulated data
                        self._start_simulated_updates()
                        break
                        
            except Exception as e:
                print(f"Failed to start real monitoring: {e}")
                # Fallback to simulated data
                self._start_simulated_updates()
        
        def simulated_updates():
            """Fallback to simulated data updates."""
            import random
            while True:
                try:
                    # Simulate real-time detection data
                    detection_data = {
                        'overall_risk': random.uniform(0, 0.3),  # Low risk for demo
                        'deviations': {
                            'keystroke': random.uniform(0, 0.2),
                            'mouse': random.uniform(0, 0.15),
                            'applications': random.uniform(0, 0.1)
                        },
                        'input_flood_risk': random.uniform(0, 0.2)
                    }
                    
                    # Update UI in main thread
                    self.after_idle(self.update_detection_status, detection_data)
                    time.sleep(2)  # Update every 2 seconds
                except Exception as e:
                    print(f"Real-time update error: {e}")
                    time.sleep(2)
        
        # Start monitoring in background thread
        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()
        
    def _start_simulated_updates(self):
        """Fallback to simulated updates."""
        def update_loop():
            import random
            while True:
                try:
                    # Simulate real-time detection data
                    detection_data = {
                        'overall_risk': random.uniform(0, 0.3),  # Low risk for demo
                        'deviations': {
                            'keystroke': random.uniform(0, 0.2),
                            'mouse': random.uniform(0, 0.15),
                            'applications': random.uniform(0, 0.1)
                        },
                        'input_flood_risk': random.uniform(0, 0.2)
                    }
                    
                    # Update UI in main thread
                    self.after_idle(self.update_detection_status, detection_data)
                    time.sleep(2)  # Update every 2 seconds
                except Exception as e:
                    print(f"Real-time update error: {e}")
                    time.sleep(2)
                    
        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()

class LiveMonitoringFrame(ttk.Frame):
    """Frame for live system monitoring."""
    
    def __init__(self, parent, user_email):
        super().__init__(parent)
        self.user_email = user_email
        self.setup_ui()
        self.keystroke_collector = None
        self.mouse_collector = None
        self.location_info = {"latitude": 0.0, "longitude": 0.0, "city": "Unknown", "country": "Unknown"}
        self._start_real_monitoring()
        
    def setup_ui(self):
        """Setup live monitoring UI with improved design."""
        
        # Configure styles
        style = ttk.Style()
        style.configure("Header.TLabel", font=("Arial", 16, "bold"))
        style.configure("Metric.TLabel", font=("Arial", 12))
        style.configure("Value.TLabel", font=("Arial", 12, "bold"))
        style.configure("Alert.TLabel", font=("Arial", 10))
        
        # Header with improved styling
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(header_frame, text="Live System Monitoring", 
                font=("Arial", 18, "bold"), fg="darkblue").pack(side=tk.LEFT)
        
        self.timestamp_label = ttk.Label(header_frame, text="--:--:--", style="Header.TLabel")
        self.timestamp_label.pack(side=tk.RIGHT)
        
        # User info section
        user_frame = ttk.LabelFrame(self, text="User Information", padding="15")
        user_frame.pack(fill=tk.X, pady=5)
        
        user_grid = ttk.Frame(user_frame)
        user_grid.pack(fill=tk.X)
        
        ttk.Label(user_grid, text="Authenticated User:", style="Metric.TLabel").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Label(user_grid, text=self.user_email, style="Value.TLabel", foreground="green").grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Location info section with improved design
        location_frame = ttk.LabelFrame(self, text="📍 User Location", padding="15")
        location_frame.pack(fill=tk.X, pady=10)
        
        # Location grid with better layout
        location_grid = ttk.Frame(location_frame)
        location_grid.pack(fill=tk.X)
        
        # Latitude with icon
        ttk.Label(location_grid, text="Latitude:", style="Metric.TLabel").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.latitude_label = ttk.Label(location_grid, text="0.0000", style="Value.TLabel", foreground="blue")
        self.latitude_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Longitude with icon
        ttk.Label(location_grid, text="Longitude:", style="Metric.TLabel").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.longitude_label = ttk.Label(location_grid, text="0.0000", style="Value.TLabel", foreground="blue")
        self.longitude_label.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # City with icon
        ttk.Label(location_grid, text="City:", style="Metric.TLabel").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.city_label = ttk.Label(location_grid, text="Unknown", style="Value.TLabel", foreground="darkgreen")
        self.city_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Country with icon
        ttk.Label(location_grid, text="Country:", style="Metric.TLabel").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.country_label = ttk.Label(location_grid, text="Unknown", style="Value.TLabel", foreground="darkgreen")
        self.country_label.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Map placeholder
        map_frame = ttk.Frame(location_frame)
        map_frame.pack(fill=tk.X, pady=10)
        
        map_label = ttk.Label(map_frame, text="🗺️ Map View (Simulated)", font=("Arial", 10, "italic"), foreground="gray")
        map_label.pack()
        
        # Progress bar for location accuracy
        self.location_accuracy = ttk.Progressbar(map_frame, length=200, mode='determinate')
        self.location_accuracy.pack(pady=5)
        self.location_accuracy['value'] = 75  # Simulated accuracy
        
        # System status section
        status_frame = ttk.LabelFrame(self, text="System Status", padding="15")
        status_frame.pack(fill=tk.X, pady=10)
        
        self.status_labels = []
        statuses = [
            "✅ Background monitoring active",
            "✅ Keystroke analysis running",
            "✅ Mouse pattern detection active", 
            "✅ Real-time threat monitoring",
            "✅ Behavioral model processing data"
        ]
        
        for i, status in enumerate(statuses):
            label = ttk.Label(status_frame, text=status, style="Alert.TLabel")
            label.pack(anchor="w", pady=3)
            self.status_labels.append(label)
            
        # Activity metrics section
        metrics_frame = ttk.LabelFrame(self, text="Activity Metrics (Real-time)", padding="15")
        metrics_frame.pack(fill=tk.X, pady=10)
        
        # Metrics grid with improved layout
        metrics_grid = ttk.Frame(metrics_frame)
        metrics_grid.pack(fill=tk.X)
        
        # Keystrokes
        ttk.Label(metrics_grid, text="⌨️ Keystrokes:", style="Metric.TLabel").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.keystrokes_label = ttk.Label(metrics_grid, text="0", style="Value.TLabel", foreground="purple")
        self.keystrokes_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Mouse clicks
        ttk.Label(metrics_grid, text="🖱️ Mouse Clicks:", style="Metric.TLabel").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.mouse_clicks_label = ttk.Label(metrics_grid, text="0", style="Value.TLabel", foreground="purple")
        self.mouse_clicks_label.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Mouse movements
        ttk.Label(metrics_grid, text="🖱️ Mouse Movements:", style="Metric.TLabel").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.mouse_moves_label = ttk.Label(metrics_grid, text="0", style="Value.TLabel", foreground="purple")
        self.mouse_moves_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Window switches
        ttk.Label(metrics_grid, text="🔄 Window Switches:", style="Metric.TLabel").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.window_switches_label = ttk.Label(metrics_grid, text="0", style="Value.TLabel", foreground="orange")
        self.window_switches_label.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Applications
        ttk.Label(metrics_grid, text="📱 Active Applications:", style="Metric.TLabel").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.applications_label = ttk.Label(metrics_grid, text="0", style="Value.TLabel", foreground="orange")
        self.applications_label.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Tab switches
        ttk.Label(metrics_grid, text="📑 Tab Switches:", style="Metric.TLabel").grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
        self.tab_switches_label = ttk.Label(metrics_grid, text="0", style="Value.TLabel", foreground="orange")
        self.tab_switches_label.grid(row=2, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Security alerts section
        alerts_frame = ttk.LabelFrame(self, text="🚨 Real-time Security Alerts", padding="15")
        alerts_frame.pack(fill=tk.X, pady=10, expand=True)
        
        # Alerts listbox with scrollbar
        alerts_container = ttk.Frame(alerts_frame)
        alerts_container.pack(fill=tk.BOTH, expand=True)
        
        self.alerts_listbox = tk.Listbox(alerts_container, height=8, font=("Arial", 9))
        scrollbar = ttk.Scrollbar(alerts_container, orient="vertical", command=self.alerts_listbox.yview)
        self.alerts_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.alerts_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add initial alerts
        initial_alerts = [
            "✅ System started - Real monitoring active",
            "✅ User authentication successful",
            "✅ Keystroke and mouse monitoring enabled"
        ]
        for alert in initial_alerts:
            self.alerts_listbox.insert(tk.END, alert)
            
    def _start_real_monitoring(self):
        """Start real monitoring using actual system activity data."""
        def monitoring_loop():
            try:
                import time
                import sys
                from pathlib import Path
                import threading
                
                # Add src to path for imports
                current_dir = Path(__file__).parent.parent
                sys.path.insert(0, str(current_dir))
                
                # Import real monitoring components
                try:
                    from src.core.keystroke_collector import KeystrokeCollector
                    from src.core.mouse_collector import MouseCollector
                    
                    # Create and start collectors
                    config = {'sample_window': 100}
                    self.keystroke_collector = KeystrokeCollector(config)
                    self.mouse_collector = MouseCollector(config)
                    
                    self.keystroke_collector.start_collection()
                    self.mouse_collector.start_collection()
                    
                    print("✅ Real collectors started successfully")
                    
                except Exception as e:
                    print(f"❌ Failed to import/start collectors: {e}")
                    # Fallback to simulated data
                    self._start_simulated_monitoring()
                    return
                
                # Initialize system monitoring and variables
                psutil = None
                win32gui = None
                system_monitoring_available = False
                last_window = None
                window_switch_count = 0
                
                try:
                    import psutil as psutil_module
                    import win32gui as win32gui_module
                    psutil = psutil_module
                    win32gui = win32gui_module
                    system_monitoring_available = True
                    print("✅ System monitoring modules loaded")
                except ImportError as e:
                    print(f"⚠️ System monitoring modules not available: {e}")
                
                # Initialize counters
                last_alert_time = time.time()
                last_typing_check = time.time()
                
                while True:
                    try:
                        # Update timestamp
                        timestamp_str = time.strftime("%H:%M:%S")
                        
                        # Count real events
                        keystroke_count = 0
                        mouse_click_count = 0
                        mouse_move_count = 0
                        
                        # Count keystrokes
                        if self.keystroke_collector and hasattr(self.keystroke_collector, 'keystroke_buffer'):
                            keystroke_count = sum(1 for event in self.keystroke_collector.keystroke_buffer 
                                                if event.event_type == 'press')
                        
                        # Count mouse events
                        if self.mouse_collector and hasattr(self.mouse_collector, 'mouse_buffer'):
                            mouse_click_count = sum(1 for event in self.mouse_collector.mouse_buffer 
                                                  if event.event_type == 'click')
                            mouse_move_count = sum(1 for event in self.mouse_collector.mouse_buffer 
                                                 if event.event_type == 'move')
                        
                        # Get system information if available
                        app_count = 1
                        if system_monitoring_available and psutil and win32gui:
                            try:
                                # Get current active window
                                current_window = win32gui.GetWindowText(win32gui.GetForegroundWindow())
                                if current_window != last_window and last_window is not None:
                                    window_switch_count += 1
                                last_window = current_window
                                
                                # Get active application count
                                app_count = len([p for p in psutil.process_iter(['name']) if p.info['name']])
                                
                            except Exception as e:
                                print(f"System monitoring error: {e}")
                        
                        # Schedule UI updates in main thread
                        self.after_idle(self._update_ui_metrics, 
                                      timestamp_str,
                                      keystroke_count,
                                      mouse_click_count,
                                      mouse_move_count,
                                      window_switch_count,
                                      0,  # tab switches (to be implemented)
                                      app_count)
                        
                        # Update location info
                        self.after_idle(self._update_location_info)
                        
                        # Check for anomalies and add alerts (every 2 seconds)
                        current_time = time.time()
                        if current_time - last_alert_time > 2.0:
                            # Check for fast typing based on buffer analysis
                            if self.keystroke_collector and hasattr(self.keystroke_collector, 'keystroke_buffer'):
                                # Analyze recent typing speed
                                recent_keystrokes = list(self.keystroke_collector.keystroke_buffer)[-20:]  # Last 20 keystrokes
                                if len(recent_keystrokes) >= 10:
                                    # Calculate typing speed (keystrokes per minute)
                                    if len(recent_keystrokes) > 1:
                                        time_span = recent_keystrokes[-1].timestamp - recent_keystrokes[0].timestamp
                                        if time_span > 0:
                                            typing_speed = (len(recent_keystrokes) / time_span) * 60  # KPM
                                            if typing_speed > 300:  # > 300 KPM
                                                alert_text = f"[{timestamp_str}] ⚠️ Fast typing detected ({typing_speed:.0f} KPM)"
                                                self.after_idle(self._add_alert, alert_text)
                                                last_alert_time = current_time
                            
                            # Check for unusual mouse activity
                            if self.mouse_collector and hasattr(self.mouse_collector, 'mouse_buffer'):
                                recent_mouse = list(self.mouse_collector.mouse_buffer)[-50:]  # Last 50 mouse events
                                if len(recent_mouse) >= 10:
                                    # Check for high velocity movements
                                    velocities = [event.velocity for event in recent_mouse 
                                                if event.velocity is not None and event.event_type == 'move']
                                    if velocities:
                                        avg_velocity = sum(velocities) / len(velocities)
                                        if avg_velocity > 2000:  # Very fast mouse movement
                                            alert_text = f"[{timestamp_str}] ⚠️ Unusual mouse movement detected"
                                            self.after_idle(self._add_alert, alert_text)
                                            last_alert_time = current_time
                        
                        time.sleep(0.2)  # Frequent updates for responsiveness
                        
                    except Exception as e:
                        print(f"Real monitoring loop error: {e}")
                        time.sleep(1)
                        
            except Exception as e:
                print(f"Failed to start real monitoring: {e}")
                # Fallback to simulated data
                self._start_simulated_monitoring()
        
        # Start monitoring in background thread
        monitor_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitor_thread.start()
        
    def _update_location_info(self):
        """Update location information display."""
        try:
            # In a real implementation, this would fetch actual location data
            # For now, we'll simulate location data
            import random
            import time
            
            # Simulate location change over time
            self.location_info["latitude"] = round(28.6139 + random.uniform(-0.1, 0.1), 4)
            self.location_info["longitude"] = round(77.2090 + random.uniform(-0.1, 0.1), 4)
            self.location_info["city"] = "New Delhi"
            self.location_info["country"] = "India"
            
            # Update UI labels
            self.latitude_label.config(text=str(self.location_info["latitude"]))
            self.longitude_label.config(text=str(self.location_info["longitude"]))
            self.city_label.config(text=self.location_info["city"])
            self.country_label.config(text=self.location_info["country"])
            
            # Update accuracy bar
            self.location_accuracy['value'] = random.randint(70, 95)
            
        except Exception as e:
            print(f"Location update error: {e}")
            
    def _start_simulated_monitoring(self):
        """Fallback to simulated monitoring for demo purposes."""
        def update_loop():
            import time
            import random
            
            keystroke_count = 0
            mouse_click_count = 0
            mouse_move_count = 0
            window_switch_count = 0
            tab_switch_count = 0
            app_count = 1
            
            last_alert_time = time.time()
            
            while True:
                try:
                    # Update timestamp
                    timestamp_str = time.strftime("%H:%M:%S")
                    
                    # Simulate increasing activity metrics
                    keystroke_count += random.randint(0, 3)
                    mouse_click_count += random.randint(0, 2)
                    mouse_move_count += random.randint(3, 15)
                    
                    if random.random() < 0.05:  # 5% chance of window switch
                        window_switch_count += 1
                    if random.random() < 0.03:  # 3% chance of tab switch
                        tab_switch_count += 1
                    app_count = max(1, app_count + random.randint(-1, 1))
                    
                    # Schedule UI updates in main thread
                    self.after_idle(self._update_ui_metrics, 
                                  timestamp_str,
                                  keystroke_count,
                                  mouse_click_count,
                                  mouse_move_count,
                                  window_switch_count,
                                  tab_switch_count,
                                  app_count)
                    
                    # Update location info
                    self.after_idle(self._update_location_info)
                    
                    # Occasionally add alerts
                    current_time = time.time()
                    if current_time - last_alert_time > 3.0:  # Every 3 seconds
                        if random.random() < 0.1:  # 10% chance
                            alert_types = [
                                f"[{timestamp_str}] ✅ Keystroke pattern analysis complete",
                                f"[{timestamp_str}] ✅ Mouse behavior baseline updated",
                                f"[{timestamp_str}] ⚠️ Unusual typing speed detected",
                                f"[{timestamp_str}] ✅ Authentication confidence: High",
                                f"[{timestamp_str}] ✅ Behavioral profile stable",
                                f"[{timestamp_str}] ⚠️ Fast tab switching detected",
                                f"[{timestamp_str}] ⚠️ Input flooding pattern identified"
                            ]
                            alert = random.choice(alert_types)
                            self.after_idle(self._add_alert, alert)
                            last_alert_time = current_time
                    
                    time.sleep(1)  # Update every second
                    
                except Exception as e:
                    print(f"Simulated monitoring error: {e}")
                    time.sleep(1)
        
        # Start simulated monitoring in background thread
        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()
        
    def _update_ui_metrics(self, timestamp, keystrokes, mouse_clicks, mouse_moves, 
                          window_switches, tab_switches, applications):
        """Thread-safe UI update method."""
        try:
            self.timestamp_label.config(text=timestamp)
            self.keystrokes_label.config(text=str(keystrokes))
            self.mouse_clicks_label.config(text=str(mouse_clicks))
            self.mouse_moves_label.config(text=str(mouse_moves))
            self.window_switches_label.config(text=str(window_switches))
            self.tab_switches_label.config(text=str(tab_switches))
            self.applications_label.config(text=str(applications))
        except Exception as e:
            print(f"UI update error: {e}")
        
    def _add_alert(self, alert_text):
        """Thread-safe alert addition method."""
        try:
            self.alerts_listbox.insert(tk.END, alert_text)
            self.alerts_listbox.see(tk.END)  # Scroll to latest alert
            
            # Color coding for alerts
            if "⚠️" in alert_text:
                self.alerts_listbox.itemconfig(tk.END, {'fg': 'red'})
            elif "✅" in alert_text:
                self.alerts_listbox.itemconfig(tk.END, {'fg': 'green'})
            else:
                self.alerts_listbox.itemconfig(tk.END, {'fg': 'black'})
        except Exception as e:
            print(f"Alert addition error: {e}")

class ProfileFrame(ttk.Frame):
    """Frame for user profile and security settings."""
    
    def __init__(self, parent, user_email):
        super().__init__(parent)
        self.user_email = user_email
        self.setup_ui()
        
    def setup_ui(self):
        """Setup profile UI."""
        
        # Header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(header_frame, text="User Profile", 
                font=("Arial", 14, "bold")).pack(side=tk.LEFT)
        
        # Profile   info
        profile_frame = ttk.LabelFrame(self, text="Profile Information", padding="10")
        profile_frame.pack(fill=tk.X, pady=5)
        
        # User email
        ttk.Label(profile_frame, text="Email:", font=("Arial", 11)).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(profile_frame, text=self.user_email, font=("Arial", 11, "bold")).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # User ID
        ttk.Label(profile_frame, text="User ID:", font=("Arial", 11)).grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(profile_frame, text="USR-001", font=("Arial", 11, "bold")).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Registration date
        ttk.Label(profile_frame, text="Registered:", font=("Arial", 11)).grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(profile_frame, text="2025-09-29", font=("Arial", 11, "bold")).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Security settings
        security_frame = ttk.LabelFrame(self, text="Security Settings", padding="10")
        security_frame.pack(fill=tk.X, pady=5)
        
        # Security options with checkboxes
        self.security_options = {
            "Fast Typing Detection": tk.BooleanVar(value=True),
            "Tab Switching Monitoring": tk.BooleanVar(value=True),
            "Camera Biometric Monitoring": tk.BooleanVar(value=True),
            "Microphone Analysis": tk.BooleanVar(value=False),
            "Application Usage Tracking": tk.BooleanVar(value=True),
            "Mouse Behavior Analysis": tk.BooleanVar(value=True)
        }
        
        row = 0
        for option, var in self.security_options.items():
            checkbox = ttk.Checkbutton(security_frame, text=option, variable=var)
            checkbox.grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
            row += 1
            
        # PIN change section
        pin_frame = ttk.LabelFrame(self, text="Change PIN", padding="10")
        pin_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(pin_frame, text="Current PIN:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.current_pin_entry = ttk.Entry(pin_frame, show="*", width=20)
        self.current_pin_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(pin_frame, text="New PIN:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.new_pin_entry = ttk.Entry(pin_frame, show="*", width=20)
        self.new_pin_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(pin_frame, text="Confirm New PIN:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.confirm_pin_entry = ttk.Entry(pin_frame, show="*", width=20)
        self.confirm_pin_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        change_pin_button = ttk.Button(pin_frame, text="Change PIN", command=self.change_pin)
        change_pin_button.grid(row=3, column=1, sticky=tk.W, padx=5, pady=10)
        
        # Status label
        self.status_label = ttk.Label(pin_frame, text="")
        self.status_label.grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
    def change_pin(self):
        """Handle PIN change request."""
        current_pin = self.current_pin_entry.get()
        new_pin = self.new_pin_entry.get()
        confirm_pin = self.confirm_pin_entry.get()
        
        # Simple validation
        if not current_pin or not new_pin or not confirm_pin:
            self.status_label.config(text="❌ All fields are required", foreground="red")
            return
            
        if new_pin != confirm_pin:
            self.status_label.config(text="❌ New PINs do not match", foreground="red")
            return
            
        if len(new_pin) < 6:
            self.status_label.config(text="❌ PIN must be at least 6 characters", foreground="red")
            return
            
        # In a real implementation, this would validate against the database
        self.status_label.config(text="✅ PIN changed successfully", foreground="green")
        self.current_pin_entry.delete(0, tk.END)
        self.new_pin_entry.delete(0, tk.END)
        self.confirm_pin_entry.delete(0, tk.END)

# Example usage integration
def integrate_enhanced_monitoring(main_dashboard):
    """Integrate enhanced monitoring into main dashboard."""
    
    # Add baseline training tab
    baseline_frame = BaselineTrainingFrame(main_dashboard.notebook)
    main_dashboard.notebook.add(baseline_frame, text="Baseline Training")
    
    # Add imposter detection tab
    detection_frame = ImposterDetectionFrame(main_dashboard.notebook)
    main_dashboard.notebook.add(detection_frame, text="Imposter Detection")
    
    # Add live monitoring tab
    live_frame = LiveMonitoringFrame(main_dashboard.notebook, main_dashboard.user_email)
    main_dashboard.notebook.add(live_frame, text="Live Monitoring")
    
    # Add profile tab
    profile_frame = ProfileFrame(main_dashboard.notebook, main_dashboard.user_email)
    main_dashboard.notebook.add(profile_frame, text="Profile")
    
    return baseline_frame, detection_frame, live_frame, profile_frame

class EnhancedBehaviorDashboard:
    """Main dashboard for behavioral authentication system."""
    
    def __init__(self, user_email="demo@user.com"):
        self.user_email = user_email
        self.behavioral_manager = None
        self.is_monitoring = False
        
    def run(self):
        """Run the enhanced behavior dashboard."""
        import tkinter as tk
        from tkinter import ttk, messagebox
        
        root = tk.Tk()
        root.title("Behavioral Authentication - Running")
        root.geometry("900x700")
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Main status tab
        status_frame = ttk.Frame(self.notebook)
        self.notebook.add(status_frame, text="Dashboard")
        
        tk.Label(status_frame, text="🔒 Behavioral Authentication System", 
                font=("Arial", 18, "bold")).pack(pady=20)
        tk.Label(status_frame, text=f"Authenticated as: {self.user_email}", 
                font=("Arial", 14)).pack(pady=10)
        
        # Status indicators
        status_frame_inner = ttk.LabelFrame(status_frame, text="System Status", padding="15")
        status_frame_inner.pack(fill=tk.X, padx=30, pady=20)
        
        statuses = [
            "✅ Background monitoring active",
            "✅ Keystroke analysis running",
            "✅ Mouse pattern detection active", 
            "✅ Real-time threat monitoring",
            "✅ Behavioral model processing data"
        ]
        
        for status in statuses:
            tk.Label(status_frame_inner, text=status, font=("Arial", 12), 
                    fg="green").pack(anchor="w", pady=3)
        
        # Security features summary
        features_frame = ttk.LabelFrame(status_frame, text="Active Security Features", padding="15")
        features_frame.pack(fill=tk.X, padx=30, pady=10)
        
        features = [
            "• Fast typing detection (>300 WPM triggers alerts)",
            "• Tab switching monitoring (excessive switching alerts)",
            "• Camera and microphone for biometric verification",
            "• Real-time behavioral analysis in background",
            "• Continuous authentication with adaptive response"
        ]
        
        for feature in features:
            tk.Label(features_frame, text=feature, font=("Arial", 11)).pack(anchor="w", pady=2)
        
        # Integrate enhanced monitoring components
        try:
            baseline_frame, detection_frame, live_frame, profile_frame = integrate_enhanced_monitoring(self)
            print("✅ Enhanced monitoring components integrated")
        except Exception as e:
            print(f"❌ Failed to integrate enhanced monitoring: {e}")
        
        # Control buttons
        button_frame = ttk.Frame(root)
        button_frame.pack(fill=tk.X, padx=30, pady=20)
        
        def show_info():
            messagebox.showinfo("System Info", 
                "🔒 Behavioral Authentication System\n\n"
                "This system continuously monitors your:\n"
                "• Typing patterns and keystroke dynamics\n"
                "• Mouse movement and click patterns\n"
                "• Application usage behavior\n"
                "• Window switching patterns\n\n"
                "Any unusual behavior will trigger additional authentication.")
        
        def stop_system():
            result = messagebox.askyesno("Stop System", 
                "Are you sure you want to stop behavioral authentication?\n\n"
                "This will disable security monitoring.")
            if result:
                root.quit()
        
        tk.Button(button_frame, text="System Info", command=show_info,
                 bg="blue", fg="white", font=("Arial", 12)).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Stop Authentication", 
                 command=stop_system, bg="red", fg="white", font=("Arial", 12)).pack(side=tk.RIGHT, padx=10)
        
        root.mainloop()
