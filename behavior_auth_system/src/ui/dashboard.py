"""
Graphical User Interface for Behavioral Authentication System.
Provides monitoring dashboard and control interface.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import json
from typing import Dict, Any, Optional
import logging

from ..service import BehaviorAuthClient
from .config_manager import ConfigManager, ConfigEditor

class BehaviorAuthGUI:
    """Main GUI application for behavioral authentication system."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Smart Behavioral Authentication System")
        self.root.geometry("1000x700")
        
        # Configure logging for GUI
        self.logger = logging.getLogger(__name__)
        
        # Initialize client
        self.client = None
        self.is_connected = False
        self.current_session_id = None
        
        # GUI variables
        self.status_var = tk.StringVar(value="Disconnected")
        self.user_id_var = tk.StringVar(value="")
        self.confidence_var = tk.StringVar(value="0.0")
        self.decision_var = tk.StringVar(value="None")
        
        # Setup GUI
        self._setup_gui()
        self._setup_menu()
        
        # Start status update thread
        self.update_thread = threading.Thread(target=self._update_status_loop, daemon=True)
        self.update_thread.start()
        
    def _setup_gui(self):
        """Setup main GUI layout."""
        
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Connection section
        self._create_connection_section(main_frame, 0)
        
        # Authentication section
        self._create_auth_section(main_frame, 1)
        
        # Status section
        self._create_status_section(main_frame, 2)
        
        # Log section
        self._create_log_section(main_frame, 3)
        
    def _create_connection_section(self, parent, row):
        """Create connection control section."""
        
        # Connection frame
        conn_frame = ttk.LabelFrame(parent, text="Service Connection", padding="5")
        conn_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        conn_frame.columnconfigure(1, weight=1)
        
        # Status label
        ttk.Label(conn_frame, text="Status:").grid(row=0, column=0, sticky=tk.W, padx=5)
        status_label = ttk.Label(conn_frame, textvariable=self.status_var, foreground="red")
        status_label.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Connection buttons
        button_frame = ttk.Frame(conn_frame)
        button_frame.grid(row=0, column=2, padx=5)
        
        self.connect_btn = ttk.Button(button_frame, text="Connect", command=self._connect_service)
        self.connect_btn.pack(side=tk.LEFT, padx=2)
        
        self.disconnect_btn = ttk.Button(button_frame, text="Disconnect", command=self._disconnect_service, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=2)
        
    def _create_auth_section(self, parent, row):
        """Create authentication control section."""
        
        # Authentication frame
        auth_frame = ttk.LabelFrame(parent, text="Authentication Control", padding="5")
        auth_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        auth_frame.columnconfigure(1, weight=1)
        
        # User ID input
        ttk.Label(auth_frame, text="User ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        user_entry = ttk.Entry(auth_frame, textvariable=self.user_id_var, width=20)
        user_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Authentication buttons
        auth_button_frame = ttk.Frame(auth_frame)
        auth_button_frame.grid(row=0, column=2, padx=5)
        
        self.start_auth_btn = ttk.Button(auth_button_frame, text="Start Auth", command=self._start_authentication, state=tk.DISABLED)
        self.start_auth_btn.pack(side=tk.LEFT, padx=2)
        
        self.stop_auth_btn = ttk.Button(auth_button_frame, text="Stop Auth", command=self._stop_authentication, state=tk.DISABLED)
        self.stop_auth_btn.pack(side=tk.LEFT, padx=2)
        
        # Current session info
        ttk.Label(auth_frame, text="Session ID:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.session_label = ttk.Label(auth_frame, text="None", foreground="gray")
        self.session_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
    def _create_status_section(self, parent, row):
        """Create status monitoring section."""
        
        # Status frame
        status_frame = ttk.LabelFrame(parent, text="Authentication Status", padding="5")
        status_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        status_frame.columnconfigure(1, weight=1)
        
        # Create two columns for status info
        left_frame = ttk.Frame(status_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.N), padx=5)
        
        right_frame = ttk.Frame(status_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.N), padx=5)
        
        # Left column - Authentication metrics
        ttk.Label(left_frame, text="Confidence Score:", font=("TkDefaultFont", 9, "bold")).grid(row=0, column=0, sticky=tk.W, pady=2)
        confidence_label = ttk.Label(left_frame, textvariable=self.confidence_var, foreground="blue", font=("TkDefaultFont", 12, "bold"))
        confidence_label.grid(row=0, column=1, sticky=tk.W, padx=10, pady=2)
        
        ttk.Label(left_frame, text="Decision:", font=("TkDefaultFont", 9, "bold")).grid(row=1, column=0, sticky=tk.W, pady=2)
        decision_label = ttk.Label(left_frame, textvariable=self.decision_var, foreground="green", font=("TkDefaultFont", 10, "bold"))
        decision_label.grid(row=1, column=1, sticky=tk.W, padx=10, pady=2)
        
        # Right column - System metrics
        ttk.Label(right_frame, text="System Metrics:", font=("TkDefaultFont", 9, "bold")).grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.metrics_text = tk.Text(right_frame, height=4, width=40, font=("Courier", 8))
        self.metrics_text.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
        
        # Add scrollbar for metrics
        metrics_scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.metrics_text.yview)
        metrics_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.metrics_text.configure(yscrollcommand=metrics_scrollbar.set)
        
    def _create_log_section(self, parent, row):
        """Create log display section."""
        
        # Log frame
        log_frame = ttk.LabelFrame(parent, text="System Log", padding="5")
        log_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        parent.rowconfigure(row, weight=1)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Log control buttons
        log_button_frame = ttk.Frame(log_frame)
        log_button_frame.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        ttk.Button(log_button_frame, text="Clear Log", command=self._clear_log).pack(side=tk.LEFT, padx=2)
        ttk.Button(log_button_frame, text="Save Log", command=self._save_log).pack(side=tk.LEFT, padx=2)
        
    def _setup_menu(self):
        """Setup application menu."""
        
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Settings...", command=self._open_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="System Status", command=self._show_system_status)
        tools_menu.add_command(label="Test Authentication", command=self._test_authentication)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
        
    def _connect_service(self):
        """Connect to behavioral authentication service."""
        try:
            self.client = BehaviorAuthClient()
            
            if self.client.connect():
                self.is_connected = True
                self.status_var.set("Connected")
                self.connect_btn.config(state=tk.DISABLED)
                self.disconnect_btn.config(state=tk.NORMAL)
                self.start_auth_btn.config(state=tk.NORMAL)
                
                self._log_message("Connected to behavioral authentication service")
                
                # Register callbacks
                self.client.register_auth_callback('gui_auth', self._on_auth_event)
                self.client.register_session_callback('gui_session', self._on_session_event)
                
            else:
                messagebox.showerror("Connection Error", "Failed to connect to service")
                
        except Exception as e:
            messagebox.showerror("Connection Error", f"Connection failed: {e}")
            self._log_message(f"Connection error: {e}")
            
    def _disconnect_service(self):
        """Disconnect from service."""
        try:
            if self.client:
                self.client.disconnect()
                
            self.is_connected = False
            self.status_var.set("Disconnected")
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
            self.start_auth_btn.config(state=tk.DISABLED)
            self.stop_auth_btn.config(state=tk.DISABLED)
            
            self.current_session_id = None
            self.session_label.config(text="None")
            self.confidence_var.set("0.0")
            self.decision_var.set("None")
            
            self._log_message("Disconnected from service")
            
        except Exception as e:
            self._log_message(f"Disconnect error: {e}")
            
    def _start_authentication(self):
        """Start authentication for user."""
        user_id = self.user_id_var.get().strip()
        
        if not user_id:
            messagebox.showwarning("Input Error", "Please enter a User ID")
            return
            
        try:
            session_id = self.client.create_session(user_id)
            
            if session_id:
                self.current_session_id = session_id
                self.session_label.config(text=session_id[:16] + "...")
                self.start_auth_btn.config(state=tk.DISABLED)
                self.stop_auth_btn.config(state=tk.NORMAL)
                
                self._log_message(f"Started authentication for user: {user_id}")
                
                # Start continuous authentication
                self._start_continuous_auth()
                
            else:
                messagebox.showerror("Authentication Error", "Failed to start authentication")
                
        except Exception as e:
            messagebox.showerror("Authentication Error", f"Failed to start: {e}")
            self._log_message(f"Authentication start error: {e}")
            
    def _stop_authentication(self):
        """Stop current authentication."""
        try:
            if self.current_session_id and self.client:
                self.client.end_session(self.current_session_id)
                
            self.current_session_id = None
            self.session_label.config(text="None")
            self.start_auth_btn.config(state=tk.NORMAL)
            self.stop_auth_btn.config(state=tk.DISABLED)
            self.confidence_var.set("0.0")
            self.decision_var.set("None")
            
            self._log_message("Authentication stopped")
            
        except Exception as e:
            self._log_message(f"Stop authentication error: {e}")
            
    def _start_continuous_auth(self):
        """Start continuous authentication in background."""
        
        def auth_loop():
            while self.current_session_id and self.is_connected:
                try:
                    result = self.client.authenticate(self.current_session_id)
                    
                    # Update GUI in main thread
                    self.root.after(0, self._update_auth_display, result)
                    
                    time.sleep(2)  # Check every 2 seconds
                    
                except Exception as e:
                    self._log_message(f"Continuous auth error: {e}")
                    break
                    
        auth_thread = threading.Thread(target=auth_loop, daemon=True)
        auth_thread.start()
        
    def _update_auth_display(self, result: Dict[str, Any]):
        """Update authentication display with latest result."""
        
        confidence = result.get('confidence', 0.0)
        decision = result.get('decision', 'unknown')
        
        self.confidence_var.set(f"{confidence:.3f}")
        self.decision_var.set(decision.title())
        
        # Color-code decision
        decision_label = None
        for widget in self.root.winfo_children():
            if hasattr(widget, 'winfo_children'):
                for child in widget.winfo_children():
                    if hasattr(child, 'winfo_children'):
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, ttk.Label) and str(grandchild['textvariable']) == str(self.decision_var):
                                decision_label = grandchild
                                break
                                
        if decision_label:
            if decision == 'continue':
                decision_label.config(foreground="green")
            elif decision == 'monitor':
                decision_label.config(foreground="orange")
            elif decision == 'challenge':
                decision_label.config(foreground="red")
            else:
                decision_label.config(foreground="gray")
                
    def _update_status_loop(self):
        """Background thread to update system status."""
        
        while True:
            try:
                if self.is_connected and self.client:
                    status = self.client.get_service_status()
                    
                    # Update metrics display in main thread
                    self.root.after(0, self._update_metrics_display, status)
                    
                time.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                pass  # Ignore errors in background thread
                
    def _update_metrics_display(self, status: Dict[str, Any]):
        """Update system metrics display."""
        
        try:
            metrics_text = ""
            
            if status.get('is_running', False):
                stats = status.get('service_stats', {})
                components = status.get('components', {})
                
                metrics_text += f"Uptime: {stats.get('uptime_seconds', 0):.0f}s\n"
                metrics_text += f"Sessions: {stats.get('sessions_handled', 0)}\n"
                metrics_text += f"Auth Count: {stats.get('authentications_performed', 0)}\n"
                metrics_text += f"ML Models: {'✓' if components.get('ml_models', False) else '✗'}\n"
                metrics_text += f"Security: {'✓' if components.get('security_monitoring', False) else '✗'}\n"
                
            else:
                metrics_text = "Service not running"
                
            self.metrics_text.delete(1.0, tk.END)
            self.metrics_text.insert(1.0, metrics_text)
            
        except Exception as e:
            pass  # Ignore display errors
            
    def _on_auth_event(self, event: Dict[str, Any]):
        """Handle authentication events."""
        event_type = event.get('type', '')
        data = event.get('data', {})
        
        message = f"Auth Event: {event_type}"
        if 'result' in data:
            result = data['result']
            message += f" - {result.get('decision', 'unknown')}"
            
        self._log_message(message)
        
    def _on_session_event(self, event: Dict[str, Any]):
        """Handle session events."""
        event_type = event.get('type', '')
        self._log_message(f"Session Event: {event_type}")
        
    def _log_message(self, message: str):
        """Add message to log display."""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Add to log in main thread
        self.root.after(0, self._append_log, log_entry)
        
    def _append_log(self, message: str):
        """Append message to log (thread-safe)."""
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        
        # Limit log size
        if self.log_text.index(tk.END) > 1000:
            self.log_text.delete(1.0, "100.0")
            
    def _clear_log(self):
        """Clear log display."""
        self.log_text.delete(1.0, tk.END)
        
    def _save_log(self):
        """Save log to file."""
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                messagebox.showinfo("Save Log", "Log saved successfully")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save log: {e}")
                
    def _open_settings(self):
        """Open settings dialog."""
        SettingsDialog(self.root)
        
    def _show_system_status(self):
        """Show detailed system status."""
        if self.is_connected and self.client:
            status = self.client.get_service_status()
            status_text = json.dumps(status, indent=2)
            
            # Create status window
            status_window = tk.Toplevel(self.root)
            status_window.title("System Status")
            status_window.geometry("600x400")
            
            text_area = scrolledtext.ScrolledText(status_window, wrap=tk.WORD)
            text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_area.insert(1.0, status_text)
            text_area.config(state=tk.DISABLED)
        else:
            messagebox.showwarning("Status", "Not connected to service")
            
    def _test_authentication(self):
        """Run authentication test."""
        if not self.is_connected:
            messagebox.showwarning("Test", "Not connected to service")
            return
            
        messagebox.showinfo("Test", "Authentication test functionality would be implemented here")
        
    def _show_about(self):
        """Show about dialog."""
        about_text = """Smart Behavioral Authentication System
        
Version: 1.0.0
        
This application provides continuous behavioral authentication
using keystroke dynamics and mouse patterns for enhanced security.

Features:
• Real-time behavioral biometric analysis
• Machine learning based anomaly detection
• Adaptive security responses
• Device fingerprinting and context validation
• Privacy-preserving data collection
        """
        
        messagebox.showinfo("About", about_text)
        
    def run(self):
        """Start the GUI application."""
        self.root.mainloop()

class SettingsDialog:
    """Settings configuration dialog."""
    
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Settings")
        self.window.geometry("500x400")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Load configuration
        self.config_manager = ConfigManager()
        self.config_manager.load_config()
        
        self._setup_dialog()
        
    def _setup_dialog(self):
        """Setup settings dialog."""
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Security tab
        security_frame = ttk.Frame(notebook)
        notebook.add(security_frame, text="Security")
        self._create_security_tab(security_frame)
        
        # ML tab
        ml_frame = ttk.Frame(notebook)
        notebook.add(ml_frame, text="Machine Learning")
        self._create_ml_tab(ml_frame)
        
        # Authentication tab
        auth_frame = ttk.Frame(notebook)
        notebook.add(auth_frame, text="Authentication")
        self._create_auth_tab(auth_frame)
        
        # Button frame
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(button_frame, text="Save", command=self._save_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)
        
    def _create_security_tab(self, parent):
        """Create security settings tab."""
        
        # Session timeout
        ttk.Label(parent, text="Session Timeout (minutes):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.session_timeout = tk.StringVar(value=str(self.config_manager.get('security.session.timeout_minutes', 30)))
        ttk.Entry(parent, textvariable=self.session_timeout, width=10).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Privacy settings
        self.privacy_enabled = tk.BooleanVar(value=self.config_manager.get('security.privacy.enable_differential_privacy', True))
        ttk.Checkbutton(parent, text="Enable Differential Privacy", variable=self.privacy_enabled).grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
    def _create_ml_tab(self, parent):
        """Create ML settings tab."""
        
        # Training samples
        ttk.Label(parent, text="Min Training Samples:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.min_samples = tk.StringVar(value=str(self.config_manager.get('ml.training.min_samples', 1000)))
        ttk.Entry(parent, textvariable=self.min_samples, width=10).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Anomaly threshold
        ttk.Label(parent, text="Anomaly Threshold:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.anomaly_threshold = tk.StringVar(value=str(self.config_manager.get('ml.anomaly_detection.threshold', 0.7)))
        ttk.Entry(parent, textvariable=self.anomaly_threshold, width=10).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
    def _create_auth_tab(self, parent):
        """Create authentication settings tab."""
        
        # Confidence thresholds
        ttk.Label(parent, text="High Confidence Threshold:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.high_confidence = tk.StringVar(value=str(self.config_manager.get('authentication.confidence_levels.high', 0.9)))
        ttk.Entry(parent, textvariable=self.high_confidence, width=10).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(parent, text="Medium Confidence Threshold:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.medium_confidence = tk.StringVar(value=str(self.config_manager.get('authentication.confidence_levels.medium', 0.7)))
        ttk.Entry(parent, textvariable=self.medium_confidence, width=10).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(parent, text="Low Confidence Threshold:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.low_confidence = tk.StringVar(value=str(self.config_manager.get('authentication.confidence_levels.low', 0.5)))
        ttk.Entry(parent, textvariable=self.low_confidence, width=10).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
    def _save_settings(self):
        """Save settings to configuration."""
        try:
            # Update configuration
            self.config_manager.set('security.session.timeout_minutes', int(self.session_timeout.get()))
            self.config_manager.set('security.privacy.enable_differential_privacy', self.privacy_enabled.get())
            self.config_manager.set('ml.training.min_samples', int(self.min_samples.get()))
            self.config_manager.set('ml.anomaly_detection.threshold', float(self.anomaly_threshold.get()))
            self.config_manager.set('authentication.confidence_levels.high', float(self.high_confidence.get()))
            self.config_manager.set('authentication.confidence_levels.medium', float(self.medium_confidence.get()))
            self.config_manager.set('authentication.confidence_levels.low', float(self.low_confidence.get()))
            
            # Save to file
            if self.config_manager.save_config():
                messagebox.showinfo("Settings", "Settings saved successfully")
                self.window.destroy()
            else:
                messagebox.showerror("Settings", "Failed to save settings")
                
        except ValueError as e:
            messagebox.showerror("Settings", f"Invalid value: {e}")
        except Exception as e:
            messagebox.showerror("Settings", f"Error saving settings: {e}")

def main():
    """Main entry point for GUI application."""
    app = BehaviorAuthGUI()
    app.run()

if __name__ == '__main__':
    main()