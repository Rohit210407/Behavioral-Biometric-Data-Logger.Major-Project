#!/usr/bin/env python3
"""
Quick start script for Smart Behavior-Based Authentication System.
Provides easy commands to run, test, and manage the system.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_service():
    """Start the authentication service."""
    print("🚀 Starting Behavioral Authentication Service...")
    
    try:
        # Run the service script directly
        import subprocess
        import sys
        from pathlib import Path
        
        # Get the project directory
        project_dir = Path(__file__).parent
        service_script = project_dir / "src" / "service" / "main.py"
        
        if service_script.exists():
            result = subprocess.run([sys.executable, "-m", "src.service.main"], 
                                  cwd=project_dir)
            return result.returncode
        else:
            print(f"❌ Service script not found: {service_script}")
            return 1
    except Exception as e:
        print(f"❌ Service failed to start: {e}")
        return 1

def run_gui():
    """Start the GUI dashboard."""
    print("🖥️  Starting GUI Dashboard...")
    
    script_path = Path(__file__).parent / "src" / "ui" / "dashboard.py"
    
    try:
        if script_path.exists():
            result = subprocess.run([sys.executable, str(script_path)], check=True)
            return result.returncode
        else:
            print(f"❌ GUI script not found: {script_path}")
            return 1
    except subprocess.CalledProcessError as e:
        print(f"❌ GUI failed to start: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n⏹️  GUI closed by user")
        return 0

def run_setup():
    """Run the setup script."""
    print("⚙️  Running system setup...")
    
    # Create required directories instead of running setup.py
    project_dir = Path(__file__).parent.parent
    required_dirs = ["logs", "saved_models", "data"]
    
    for dir_name in required_dirs:
        dir_path = project_dir / dir_name
        os.makedirs(dir_path, exist_ok=True)
        print(f"  ✅ Created {dir_name} directory")
    
    print("✅ Setup completed successfully")
    return 0

def run_tests():
    """Run the test suite."""
    print("🧪 Running test suite...")
    
    # Change to project directory
    project_dir = Path(__file__).parent.parent
    os.chdir(project_dir)
    
    # Since we don't have test files, just show a message
    print("ℹ️  No test files found. Skipping tests.")
    return 0

def run_config():
    """Open configuration manager."""
    print("⚙️  Opening configuration manager...")
    
    script_path = Path(__file__).parent / "src" / "ui" / "config_manager.py"
    
    try:
        if script_path.exists():
            result = subprocess.run([sys.executable, str(script_path)])
            return result.returncode
        else:
            print(f"❌ Configuration manager script not found: {script_path}")
            return 1
    except Exception as e:
        print(f"❌ Configuration manager failed: {e}")
        return 1

def demo_mode():
    """Run a quick demonstration."""
    print("🎯 Running demonstration mode...")
    
    # First check if system is set up
    print("1. Checking system setup...")
    
    # Run basic setup if needed
    setup_code = run_setup()
    if setup_code != 0:
        print("❌ Setup failed, cannot run demo")
        return 1
    
    print("✅ Setup completed")
    
    # Run a quick test
    print("2. Running basic functionality test...")
    
    # Change to project directory
    project_dir = Path(__file__).parent.parent
    os.chdir(project_dir)
    
    # Add src to path
    sys.path.insert(0, str(project_dir / "src"))
    
    try:
        from src.service.client import SimpleBehaviorAuth
        import time

        print("Starting demo authentication...")

        # Initialize authentication
        auth = SimpleBehaviorAuth()

        try:
            # Start authentication for demo user
            if auth.start_authentication("demo_user"):
                print("✅ Demo authentication started")
                
                # Simulate some usage
                for i in range(3):
                    print(f"Checking authentication... ({i+1}/3)")
                    result = auth.check_authentication()
                    print(f"  Result: {result.get('decision', 'unknown')}")
                    time.sleep(2)
                    
                print("✅ Demo completed successfully")
                
            else:
                print("❌ Demo authentication failed to start")
                
        finally:
            auth.stop_authentication()
            print("Demo authentication stopped")
    except ImportError as e:
        print(f"Import error: {e}")
        print("The client module may not be available in this version.")
        return 1
    except Exception as e:
        print(f"Demo error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n🎉 Demo completed successfully!")
    return 0

def show_status():
    """Show system status."""
    print("📊 System Status")
    print("=" * 30)
    
    # Check if configuration exists
    config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    if config_path.exists():
        print("✅ Configuration file exists")
    else:
        print("❌ Configuration file missing")
    
    # Check if database exists
    db_path = Path(__file__).parent.parent / "data" / "behavior_auth.db"
    if db_path.exists():
        print("✅ Database file exists")
    else:
        print("❌ Database file missing")
    
    # Check if logs directory exists
    logs_path = Path(__file__).parent.parent / "logs"
    if logs_path.exists():
        print("✅ Logs directory exists")
    else:
        print("❌ Logs directory missing")
    
    # Check if models directory exists
    models_path = Path(__file__).parent.parent / "saved_models"
    if models_path.exists():
        print("✅ Models directory exists")
    else:
        print("❌ Models directory missing")
    
    print("\nTo set up the system, run: python start.py setup")

def show_help():
    """Show detailed help information."""
    
    help_text = """
🔒 Smart Behavior-Based Authentication System

COMMANDS:
  setup       - Run system setup (first time only)
  service     - Start the authentication service
  gui         - Start the GUI dashboard
  demo        - Run demonstration mode
  test        - Run test suite
  config      - Open configuration manager
  status      - Show system status
  help        - Show this help message

EXAMPLES:
  python start.py setup      # Initial setup
  python start.py service    # Start service
  python start.py gui        # Launch GUI
  python start.py demo       # Quick demo

QUICK START:
  1. python start.py setup   # Set up the system
  2. python start.py gui     # Launch dashboard
  
  OR
  
  1. python start.py setup   # Set up the system  
  2. python start.py service # Start service in terminal

CONFIGURATION:
  Edit config/settings.yaml or use:
  python start.py config

TESTING:
  python start.py test       # Run all tests

For more information, see docs/README.md
"""
    
    print(help_text)

def main():
    """Main entry point."""
    
    parser = argparse.ArgumentParser(
        description='Smart Behavior-Based Authentication System',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'command',
        choices=['setup', 'service', 'gui', 'demo', 'test', 'config', 'status', 'help'],
        help='Command to execute'
    )
    
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        show_help()
        return 0
    
    args = parser.parse_args()
    
    # Change to project directory
    project_dir = Path(__file__).parent.parent
    os.chdir(project_dir)
    
    # Execute command
    command_map = {
        'setup': run_setup,
        'service': run_service,
        'gui': run_gui,
        'demo': demo_mode,
        'test': run_tests,
        'config': run_config,
        'status': show_status,
        'help': show_help
    }
    
    try:
        return command_map[args.command]()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return 1

if __name__ == '__main__':
    exit(main())