"""
Enhanced Login System with Registration and Security PIN
Implements email registration, PIN authentication, and security features.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
import re
from pathlib import Path
import base64

# Add src to path for imports - use the same approach as test_import.py
current_dir = Path(__file__).parent.parent
src_dir = current_dir
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Simple UserAuthManager for compatibility
class UserAuthManager:
    def __init__(self, *args, **kwargs):
        self.users = {}
        self.current_user = None
        
    def register_user(self, email, pin):
        if email in self.users:
            return False, "User already exists"
        if len(pin) < 6:
            return False, "PIN must be at least 6 characters"
        self.users[email] = {"pin": pin, "registered": True}
        return True, "Registration successful"
        
    def login_user(self, email, pin):
        if email not in self.users:
            return False, "Invalid email or PIN"
        if self.users[email]["pin"] != pin:
            return False, "Invalid email or PIN"
        self.current_user = {"email": email}
        return True, "Login successful"


class LoginWindow:
    """Enhanced login window with registration and security features."""
    
    def __init__(self, on_success_callback=None):
        self.root = tk.Tk()
        self.root.title("🔒 Secure Authentication - Smart Behavior System")
        
        # Set window to fullscreen as per user preference
        self.root.attributes('-fullscreen', True)
        self.root.resizable(True, True)
        
        # Additional fullscreen settings for better compatibility
        self.root.wm_attributes("-topmost", True)
        self.root.state('zoomed')  # Alternative fullscreen method
        
        # Keep window on top initially, but allow user to switch
        self.root.lift()
        self.root.focus_force()
        
        # Optional: Add fullscreen toggle for user preference (F11)
        self.root.bind('<F11>', self.toggle_fullscreen)
        
        # Initialize fullscreen state correctly
        self.is_authenticated = False
        self.is_fullscreen = True  # Start in fullscreen mode
        self.desktop_integration = True  # Enable desktop integration
        
        # Force fullscreen after a small delay to ensure it's properly set
        self.root.after(100, self._ensure_fullscreen)
        self.root.after(500, self._ensure_fullscreen)  # Additional check
        
        # Initialize auth manager
        self.auth_manager = UserAuthManager()
        self.on_success_callback = on_success_callback
        
        # Styling
        style = ttk.Style()
        style.theme_use('clam')
        
        self.setup_ui()
        
    def _ensure_fullscreen(self):
        """Ensure fullscreen is properly set."""
        try:
            if hasattr(self, 'root') and self.root:
                # Multiple checks to ensure fullscreen is set
                self.root.attributes('-fullscreen', True)
                self.root.wm_attributes("-topmost", True)
                self.root.state('zoomed')
                
                # Force window to front
                self.root.lift()
                self.root.focus_force()
        except Exception as e:
            print(f"Warning: Could not ensure fullscreen mode: {e}")
            
    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode."""
        try:
            self.is_fullscreen = not self.is_fullscreen
            self.root.attributes('-fullscreen', self.is_fullscreen)
            if self.is_fullscreen:
                self.root.wm_attributes("-topmost", True)
                self.root.state('zoomed')
            else:
                self.root.wm_attributes("-topmost", False)
        except Exception as e:
            print(f"Error toggling fullscreen: {e}")
        
    def setup_ui(self):
        """Setup the login/registration UI."""
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 30))
        
        title_label = ttk.Label(
            header_frame,
            text="🔒 Smart Behavior Authentication",
            font=("Arial", 18, "bold")
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            header_frame,
            text="Secure Login with Enhanced Monitoring",
            font=("Arial", 12)
        )
        subtitle_label.pack(pady=(5, 0))
        
        # Security notice
        security_frame = ttk.LabelFrame(main_frame, text="🛡️ Enhanced Security Features", padding="15")
        security_frame.pack(fill=tk.X, pady=(0, 20))
        
        security_features = [
            "• Background monitoring (works across all applications)",
            "• Fast typing detection (>300 WPM triggers alerts)",
            "• Tab switching monitoring (excessive switching alerts)",
            "• Camera and microphone for biometric verification",
            "• Location tracking for security context",
            "• PIN-based screen unlock when needed",
            "• Real-time behavioral analysis in background"
        ]
        
        for feature in security_features:
            feature_label = ttk.Label(security_frame, text=feature, font=("Arial", 9))
            feature_label.pack(anchor=tk.W, pady=1)
            
        # Notebook for login/register tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Login tab
        self.setup_login_tab()
        
        # Register tab
        self.setup_register_tab()
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        self.action_button = ttk.Button(
            button_frame,
            text="Login",
            command=self.handle_login,
            style="Accent.TButton"
        )
        self.action_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = ttk.Button(
            button_frame,
            text="Exit",
            command=self.root.quit
        )
        cancel_button.pack(side=tk.RIGHT)
        
        # Status bar
        self.status_var = tk.StringVar(value="Please login or register to continue")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, foreground="blue")
        status_bar.pack(pady=(10, 0))
        
        # Bind tab change
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
    def setup_login_tab(self):
        """Setup login tab."""
        login_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(login_frame, text="🔑 Login")
        
        # Email field
        ttk.Label(login_frame, text="Email Address:", font=("Arial", 12)).pack(anchor=tk.W, pady=(0, 5))
        self.login_email_var = tk.StringVar()
        self.login_email_entry = ttk.Entry(
            login_frame,
            textvariable=self.login_email_var,
            font=("Arial", 12),
            width=40
        )
        self.login_email_entry.pack(fill=tk.X, pady=(0, 15))
        
        # PIN field
        ttk.Label(login_frame, text="Security PIN:", font=("Arial", 12)).pack(anchor=tk.W, pady=(0, 5))
        self.login_pin_var = tk.StringVar()
        self.login_pin_entry = ttk.Entry(
            login_frame,
            textvariable=self.login_pin_var,
            font=("Arial", 12),
            show="*",
            width=40
        )
        self.login_pin_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Remember me
        self.remember_var = tk.BooleanVar()
        remember_check = ttk.Checkbutton(
            login_frame,
            text="Remember me on this device",
            variable=self.remember_var
        )
        remember_check.pack(anchor=tk.W, pady=(0, 15))
        
        # Desktop integration info
        desktop_info = ttk.Label(
            login_frame,
            text="ℹ️ This application integrates with your desktop environment\n"
                 "   to provide continuous background monitoring for security.",
            font=("Arial", 9),
            foreground="gray"
        )
        desktop_info.pack(anchor=tk.W, pady=(0, 15))
        
        # Login info
        info_frame = ttk.Frame(login_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        info_label = ttk.Label(
            info_frame,
            text="ℹ️ PIN Requirements:\n• Minimum 6 characters\n• Must contain numbers\n• Must contain special characters",
            font=("Arial", 9),
            foreground="gray"
        )
        info_label.pack(anchor=tk.W)
        
        # Bind Enter key
        self.login_email_entry.bind('<Return>', lambda e: self.login_pin_entry.focus())
        self.login_pin_entry.bind('<Return>', lambda e: self.handle_login())
        
    def setup_register_tab(self):
        """Setup registration tab."""
        register_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(register_frame, text="✨ Register")
        
        # Email field
        ttk.Label(register_frame, text="Email Address:", font=("Arial", 12)).pack(anchor=tk.W, pady=(0, 5))
        self.register_email_var = tk.StringVar()
        self.register_email_entry = ttk.Entry(
            register_frame,
            textvariable=self.register_email_var,
            font=("Arial", 12),
            width=40
        )
        self.register_email_entry.pack(fill=tk.X, pady=(0, 15))
        
        # PIN field
        ttk.Label(register_frame, text="Security PIN:", font=("Arial", 12)).pack(anchor=tk.W, pady=(0, 5))
        self.register_pin_var = tk.StringVar()
        self.register_pin_entry = ttk.Entry(
            register_frame,
            textvariable=self.register_pin_var,
            font=("Arial", 12),
            show="*",
            width=40
        )
        self.register_pin_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Confirm PIN field
        ttk.Label(register_frame, text="Confirm PIN:", font=("Arial", 12)).pack(anchor=tk.W, pady=(0, 5))
        self.confirm_pin_var = tk.StringVar()
        self.confirm_pin_entry = ttk.Entry(
            register_frame,
            textvariable=self.confirm_pin_var,
            font=("Arial", 12),
            show="*",
            width=40
        )
        self.confirm_pin_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Terms and conditions
        self.terms_var = tk.BooleanVar()
        terms_check = ttk.Checkbutton(
            register_frame,
            text="I agree to enhanced behavioral monitoring for security",
            variable=self.terms_var
        )
        terms_check.pack(anchor=tk.W, pady=(0, 15))
        
        # Desktop integration info
        desktop_info = ttk.Label(
            register_frame,
            text="ℹ️ This application will integrate with your desktop environment\n"
                 "   to provide continuous background monitoring for security.",
            font=("Arial", 9),
            foreground="gray"
        )
        desktop_info.pack(anchor=tk.W, pady=(0, 15))
        
        # Registration requirements
        req_frame = ttk.Frame(register_frame)
        req_frame.pack(fill=tk.X, pady=(0, 10))
        
        req_label = ttk.Label(
            req_frame,
            text="📋 Registration Requirements:\n"
                 "• Valid email address\n"
                 "• Strong PIN (6+ chars, numbers, special chars)\n"
                 "• Agreement to security monitoring\n"
                 "• Camera/microphone permissions\n"
                 "• Location access for security context",
            font=("Arial", 9),
            foreground="gray"
        )
        req_label.pack(anchor=tk.W)
        
        # Bind navigation
        self.register_email_entry.bind('<Return>', lambda e: self.register_pin_entry.focus())
        self.register_pin_entry.bind('<Return>', lambda e: self.confirm_pin_entry.focus())
        self.confirm_pin_entry.bind('<Return>', lambda e: self.handle_register())
        
    def on_tab_changed(self, event):
        """Handle tab change."""
        selected_tab = self.notebook.tab(self.notebook.select(), "text")
        
        if "Login" in selected_tab:
            self.action_button.config(text="Login", command=self.handle_login)
            self.status_var.set("Enter your credentials to login")
        else:
            self.action_button.config(text="Register", command=self.handle_register)
            self.status_var.set("Create a new account to get started")
            
    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
        
    def validate_pin(self, pin: str) -> tuple:
        """Validate PIN strength."""
        if len(pin) < 6:
            return False, "PIN must be at least 6 characters long"
        if not re.search(r'\d', pin):
            return False, "PIN must contain at least one number"
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', pin):
            return False, "PIN must contain at least one special character"
        return True, "PIN is valid"
        
    def handle_login(self):
        """Handle login attempt."""
        email = self.login_email_var.get().strip()
        pin = self.login_pin_var.get()
        
        # Validation
        if not email:
            self.status_var.set("❌ Please enter your email")
            return
            
        if not self.validate_email(email):
            self.status_var.set("❌ Please enter a valid email address")
            return
            
        if not pin:
            self.status_var.set("❌ Please enter your PIN")
            return
            
        # Attempt login
        self.status_var.set("🔄 Authenticating...")
        self.root.update()
        
        try:
            success, message = self.auth_manager.login_user(email, pin)
            
            if success:
                self.status_var.set("✅ Login successful!")
                self.is_authenticated = True
                
                # Request permissions
                self.request_permissions()
                
                # Call success callback and close
                if self.on_success_callback:
                    self.root.after(1000, lambda: self.close_with_success(email))
                else:
                    self.root.after(1000, self.root.quit)
            else:
                self.status_var.set(f"❌ {message}")
                self.login_pin_var.set("")  # Clear PIN field
                
        except Exception as e:
            self.status_var.set(f"❌ Login error: {str(e)}")
            
    def handle_register(self):
        """Handle registration attempt."""
        email = self.register_email_var.get().strip()
        pin = self.register_pin_var.get()
        confirm_pin = self.confirm_pin_var.get()
        
        # Validation
        if not email:
            self.status_var.set("❌ Please enter your email")
            return
            
        if not self.validate_email(email):
            self.status_var.set("❌ Please enter a valid email address")
            return
            
        if not pin:
            self.status_var.set("❌ Please enter a PIN")
            return
            
        pin_valid, pin_message = self.validate_pin(pin)
        if not pin_valid:
            self.status_var.set(f"❌ {pin_message}")
            return
            
        if pin != confirm_pin:
            self.status_var.set("❌ PINs do not match")
            return
            
        if not self.terms_var.get():
            self.status_var.set("❌ Please agree to enhanced monitoring")
            return
            
        # Attempt registration
        self.status_var.set("🔄 Creating account...")
        self.root.update()
        
        try:
            success, message = self.auth_manager.register_user(email, pin)
            
            if success:
                self.status_var.set("✅ Registration successful!")
                
                # Auto-login after registration
                login_success, login_message = self.auth_manager.login_user(email, pin)
                
                if login_success:
                    self.is_authenticated = True
                    
                    # Request permissions
                    self.request_permissions()
                    
                    # Call success callback and close
                    if self.on_success_callback:
                        self.root.after(1000, lambda: self.close_with_success(email))
                    else:
                        self.root.after(1000, self.root.quit)
                else:
                    self.status_var.set("✅ Registration complete. Please login.")
                    self.notebook.select(0)  # Switch to login tab
            else:
                self.status_var.set(f"❌ {message}")
                
        except Exception as e:
            self.status_var.set(f"❌ Registration error: {str(e)}")
            
    def request_permissions(self):
        """Request camera and microphone permissions."""
        try:
            # Capture user picture during login
            self.capture_user_picture()
            
            result = messagebox.askyesno(
                "Permissions Required",
                "🔒 Enhanced Security Features\n\n"
                "To provide maximum security, this system requires:\n\n"
                "📹 Camera Access: For face detection and presence monitoring\n"
                "🎤 Microphone Access: For voice pattern analysis\n"
                "⌨️ Keyboard Monitoring: For typing pattern analysis\n"
                "🖱️ Mouse Monitoring: For movement pattern analysis\n"
                "🌐 Location Access: For location-based security\n\n"
                "These features help detect:\n"
                "• Fast typing attacks (>300 WPM)\n"
                "• Excessive tab switching\n"
                "• Unauthorized access attempts\n"
                "• Behavioral anomalies\n"
                "• Location-based threats\n\n"
                "Do you grant these permissions?",
                icon='question'
            )
            
            if result:
                messagebox.showinfo(
                    "Permissions Granted",
                    "✅ Enhanced security monitoring enabled!\n\n"
                    "Your system is now protected with:\n"
                    "• Real-time behavioral analysis\n"
                    "• Fast typing detection\n"
                    "• Tab switching monitoring\n"
                    "• Biometric verification\n"
                    "• Location tracking\n"
                    "• Automatic screen locking\n\n"
                    "You will be notified of any security threats."
                )
                # Request additional permissions
                self.request_additional_permissions()
            else:
                messagebox.showwarning(
                    "Limited Security",
                    "⚠️ Some security features will be disabled.\n\n"
                    "You can enable them later in settings."
                )
                
        except Exception as e:
            print(f"Permission request error: {e}")
            
    def request_additional_permissions(self):
        """Request additional permissions for camera and microphone."""
        try:
            # Try to initialize camera and microphone
            import cv2
            import pyaudio
            
            # Test camera access
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    print("✅ Camera access granted")
                    # Save a test frame
                    import os
                    from datetime import datetime
                    pictures_dir = "user_pictures"
                    if not os.path.exists(pictures_dir):
                        os.makedirs(pictures_dir)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    test_filename = f"{pictures_dir}/test_capture_{timestamp}.jpg"
                    cv2.imwrite(test_filename, frame)
                    print(f"✅ Test image saved: {test_filename}")
                cap.release()
            else:
                print("⚠️ Camera access denied")
                
            # Test microphone access
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16,
                           channels=1,
                           rate=44100,
                           input=True,
                           frames_per_buffer=1024)
            data = stream.read(1024)
            stream.stop_stream()
            stream.close()
            p.terminate()
            print("✅ Microphone access granted")
            
        except ImportError as e:
            print(f"⚠️ Required modules not available: {e}")
            messagebox.showwarning(
                "Modules Missing",
                "Some security features require additional modules:\n"
                "• opencv-python for camera access\n"
                "• pyaudio for microphone access\n\n"
                "Install with: pip install opencv-python pyaudio"
            )
        except Exception as e:
            print(f"Permission error: {e}")
            messagebox.showwarning(
                "Permission Denied",
                "Access to camera or microphone was denied.\n"
                "Some security features will be limited."
            )
            
    def capture_user_picture(self):
        """Capture user picture during login for biometric verification."""
        try:
            # Try to import cv2 locally, but handle if not available
            try:
                import cv2
                cv2_available = True
            except ImportError:
                cv2_available = False
                print("Warning: OpenCV not available for user picture capture")
                return
                
            import os
            from datetime import datetime
            
            if not cv2_available:
                return
                
            # Create directory for user pictures if it doesn't exist
            pictures_dir = "user_pictures"
            if not os.path.exists(pictures_dir):
                os.makedirs(pictures_dir)
                
            # Initialize camera
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("Warning: Could not access camera for user picture")
                return
                
            # Capture a few frames to allow camera to adjust
            for i in range(10):
                ret, frame = cap.read()
                if not ret:
                    continue
                    
            # Capture the picture
            ret, frame = cap.read()
            if ret:
                # Save picture with timestamp and user email
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                email = self.login_email_var.get().strip() if self.login_email_var.get() else "unknown_user"
                # Sanitize email for filename
                safe_email = email.replace("@", "_").replace(".", "_")
                filename = f"{pictures_dir}/user_{safe_email}_{timestamp}.jpg"
                
                cv2.imwrite(filename, frame)
                print(f"✅ User picture captured and saved: {filename}")
                
            # Release camera
            cap.release()
            
        except Exception as e:
            print(f"User picture capture error: {e}")
            
    def close_with_success(self, email: str):
        """Close login window and call success callback."""
        if self.on_success_callback:
            self.on_success_callback(email, self.auth_manager)
        self.root.quit()
        self.root.destroy()
        
    def run(self) -> tuple:
        """Run the login window and return authentication result."""
        try:
            self.root.mainloop()
            return self.is_authenticated, self.auth_manager.current_user
        except Exception as e:
            print(f"Login window error: {e}")
            return False, None


def show_login_dialog(on_success=None):
    """Show login dialog and return authentication result."""
    login_window = LoginWindow(on_success)
    return login_window.run()

# Test the login system
if __name__ == "__main__":
    def on_login_success(email, auth_manager):
        print(f"Login successful for: {email}")
        
    authenticated, user = show_login_dialog(on_login_success)
    if authenticated:
        print("User authenticated successfully!")
    else:
        print("Authentication failed or cancelled.")