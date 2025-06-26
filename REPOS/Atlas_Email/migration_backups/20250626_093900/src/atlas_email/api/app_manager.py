"""
Web App Manager Module
Handles starting, stopping, and restarting the web application in background mode
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path


class WebAppManager:
    """Manages the FastAPI web application as a background process"""
    
    def __init__(self):
        self.app_dir = Path(__file__).parent
        self.pid_file = self.app_dir / "webapp.pid"
        self.log_file = self.app_dir / "webapp.log"
        self.web_app_script = self.app_dir / "web_app.py"
        
    def get_web_app_status(self):
        """Check if web app is currently running"""
        if not self.pid_file.exists():
            return False, None, None
            
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process is actually running
            if self._pid_exists(pid):
                return True, pid, None
            
            # PID file exists but process is not running
            self.pid_file.unlink()  # Remove stale PID file
            return False, None, None
            
        except (FileNotFoundError, ValueError):
            # PID file is corrupted or process doesn't exist
            if self.pid_file.exists():
                self.pid_file.unlink()
            return False, None, None
    
    def _pid_exists(self, pid):
        """Check if a process with given PID exists"""
        try:
            os.kill(pid, 0)  # Send null signal to check if process exists
            return True
        except OSError:
            return False
    
    def start_web_app(self):
        """Start the web application in background mode"""
        running, pid, _ = self.get_web_app_status()
        
        if running:
            print(f"⚠️  Web app is already running (PID: {pid})")
            print("🌐 Access it at: http://localhost:8000")
            return True
        
        if not self.web_app_script.exists():
            print(f"❌ Web app script not found: {self.web_app_script}")
            return False
        
        print("🚀 Starting web application in background...")
        
        try:
            # Start the web app as a background process
            with open(self.log_file, 'w') as log:
                if os.name == 'nt':  # Windows
                    # On Windows, create a new process group
                    process = subprocess.Popen([
                        sys.executable, str(self.web_app_script)
                    ], 
                    stdout=log, 
                    stderr=subprocess.STDOUT,
                    cwd=str(self.app_dir),
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                    )
                else:  # Unix-like systems
                    # On Unix, detach from parent process
                    process = subprocess.Popen([
                        sys.executable, str(self.web_app_script)
                    ], 
                    stdout=log, 
                    stderr=subprocess.STDOUT,
                    cwd=str(self.app_dir),
                    preexec_fn=os.setsid
                    )
            
            # Write PID to file
            with open(self.pid_file, 'w') as f:
                f.write(str(process.pid))
            
            # Give it a moment to start
            time.sleep(2)
            
            # Verify it started successfully
            running, pid, _ = self.get_web_app_status()
            if running:
                print("✅ Web application started successfully!")
                print(f"🆔 Process ID: {pid}")
                print("🌐 Access at: http://localhost:8000")
                print(f"📄 Logs: {self.log_file}")
                return True
            else:
                print("❌ Failed to start web application")
                # Show recent log entries
                self._show_recent_logs()
                return False
                
        except Exception as e:
            print(f"❌ Error starting web app: {e}")
            return False
    
    def stop_web_app(self):
        """Stop the web application"""
        running, pid, _ = self.get_web_app_status()
        
        if not running:
            print("ℹ️  Web app is not currently running")
            return True
        
        print(f"🛑 Stopping web application (PID: {pid})...")
        
        try:
            # Graceful shutdown first (SIGTERM on Unix, SIGBREAK on Windows)
            if os.name == 'nt':  # Windows
                os.kill(pid, signal.CTRL_BREAK_EVENT)
            else:  # Unix-like systems
                os.kill(pid, signal.SIGTERM)
            
            # Wait up to 10 seconds for graceful shutdown
            for i in range(10):
                if not self._pid_exists(pid):
                    print("✅ Web application stopped gracefully")
                    break
                time.sleep(1)
            else:
                # Force kill if graceful shutdown fails
                print("⚠️  Graceful shutdown timed out, forcing termination...")
                try:
                    if os.name == 'nt':  # Windows
                        os.kill(pid, signal.SIGTERM)  # Best we can do on Windows
                    else:  # Unix-like systems
                        os.kill(pid, signal.SIGKILL)
                    time.sleep(2)
                    print("✅ Web application forcefully terminated")
                except OSError:
                    print("✅ Process already terminated")
            
            # Clean up PID file
            if self.pid_file.exists():
                self.pid_file.unlink()
            
            return True
            
        except Exception as e:
            print(f"❌ Error stopping web app: {e}")
            # Try to clean up PID file anyway
            if self.pid_file.exists():
                self.pid_file.unlink()
            return False
    
    def restart_web_app(self):
        """Restart the web application"""
        print("🔄 Restarting web application...")
        
        # Stop if running
        self.stop_web_app()
        
        # Wait a moment
        time.sleep(1)
        
        # Start again
        return self.start_web_app()
    
    def get_web_app_info(self):
        """Get detailed information about the web app process"""
        running, pid, _ = self.get_web_app_status()
        
        if not running:
            return {
                'running': False,
                'pid': None,
                'uptime': None,
                'memory_usage': None,
                'log_size': self._get_log_size()
            }
        
        # Simple version without detailed process info
        return {
            'running': True,
            'pid': pid,
            'uptime': 'Unknown',
            'memory_usage': 'Unknown',
            'log_size': self._get_log_size()
        }
    
    def _get_log_size(self):
        """Get the size of the log file"""
        try:
            if self.log_file.exists():
                return self.log_file.stat().st_size / 1024  # KB
            return 0
        except Exception:
            return 0
    
    def _show_recent_logs(self, lines=10):
        """Show recent log entries"""
        try:
            if self.log_file.exists():
                print(f"\n📄 Recent log entries ({lines} lines):")
                with open(self.log_file, 'r') as f:
                    all_lines = f.readlines()
                    recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                    for line in recent_lines:
                        print(f"   {line.rstrip()}")
            else:
                print("📄 No log file found")
        except Exception as e:
            print(f"❌ Error reading log file: {e}")
    
    def show_logs(self, lines=20):
        """Show recent log entries (public method)"""
        self._show_recent_logs(lines)


def web_app_management_menu():
    """Web App Management Menu"""
    from atlas_email.utils.general import display_application_header, get_user_choice, clear_screen
    
    manager = WebAppManager()
    
    while True:
        clear_screen()
        display_application_header("WEB APP MANAGEMENT")
        
        # Get current status
        info = manager.get_web_app_info()
        
        if info['running']:
            print("🟢 Status: RUNNING")
            print(f"🆔 Process ID: {info['pid']}")
            if info['uptime'] != 'Unknown':
                uptime_str = f"{info['uptime']:.0f} seconds"
                if info['uptime'] > 60:
                    uptime_str = f"{info['uptime']/60:.1f} minutes"
                print(f"⏰ Uptime: {uptime_str}")
            else:
                print("⏰ Uptime: Running (details not available)")
            if info['memory_usage'] != 'Unknown':
                print(f"💾 Memory: {info['memory_usage']:.1f} MB")
            else:
                print("💾 Memory: In use (details not available)")
            print("🌐 URL: http://localhost:8000")
        else:
            print("🔴 Status: STOPPED")
        
        if info['log_size'] > 0:
            print(f"📄 Log size: {info['log_size']:.1f} KB")
        
        print()
        print("1. 🚀 Start Web App")
        print("2. 🛑 Stop Web App") 
        print("3. 🔄 Restart Web App")
        print("4. 📄 View Recent Logs")
        print("5. ℹ️  Show Detailed Status")
        print("6. 🌐 Open in Browser")
        print("0. ⬅️  Back to Main Menu")
        print()
        
        choice = get_user_choice("Select option (0-6, or Enter to go back):", ['0', '1', '2', '3', '4', '5', '6'], allow_enter=True)
        
        if choice is None or choice == '0':
            break
        elif choice == '1':
            clear_screen()
            display_application_header("START WEB APP")
            manager.start_web_app()
            input("\nPress Enter to continue...")
        elif choice == '2':
            clear_screen()
            display_application_header("STOP WEB APP")
            manager.stop_web_app()
            input("\nPress Enter to continue...")
        elif choice == '3':
            clear_screen()
            display_application_header("RESTART WEB APP")
            manager.restart_web_app()
            input("\nPress Enter to continue...")
        elif choice == '4':
            clear_screen()
            display_application_header("WEB APP LOGS")
            lines = input("\nHow many log lines to show? (default 20): ").strip()
            try:
                lines = int(lines) if lines else 20
            except ValueError:
                lines = 20
            print()
            manager.show_logs(lines)
            input("\nPress Enter to continue...")
        elif choice == '5':
            clear_screen()
            _show_detailed_status(manager)
            input("\nPress Enter to continue...")
        elif choice == '6':
            clear_screen()
            display_application_header("OPEN IN BROWSER")
            _open_in_browser(manager)
            input("\nPress Enter to continue...")


def _show_detailed_status(manager):
    """Show detailed web app status"""
    from atlas_email.utils.general import display_application_header
    
    display_application_header("DETAILED WEB APP STATUS")
    
    info = manager.get_web_app_info()
    running, pid, _ = manager.get_web_app_status()
    
    print(f"🏃 Running: {'Yes' if info['running'] else 'No'}")
    
    if info['running']:
        print(f"🆔 Process ID: {info['pid']}")
        
        if info['uptime'] != 'Unknown':
            uptime_hours = info['uptime'] / 3600
            uptime_minutes = (info['uptime'] % 3600) / 60
            uptime_seconds = info['uptime'] % 60
            print(f"⏰ Uptime: {uptime_hours:.0f}h {uptime_minutes:.0f}m {uptime_seconds:.0f}s")
        else:
            print("⏰ Uptime: Process is running")
        
        if info['memory_usage'] != 'Unknown':
            print(f"💾 Memory Usage: {info['memory_usage']:.2f} MB")
        else:
            print("💾 Memory Usage: Available (process is running)")
        
        print("🔌 Default Port: 8000")
    
    print(f"📄 Log File: {manager.log_file}")
    print(f"📄 Log Size: {info['log_size']:.1f} KB")
    print(f"🆔 PID File: {manager.pid_file}")
    print(f"🌐 Web URL: http://localhost:8000")


def _open_in_browser(manager):
    """Open web app in browser"""
    running, _, _ = manager.get_web_app_status()
    
    if not running:
        print("❌ Web app is not running. Please start it first.")
        return
    
    try:
        import webbrowser
        url = "http://localhost:8000"
        print(f"🌐 Opening {url} in your default browser...")
        webbrowser.open(url)
        print("✅ Browser opened (if available)")
    except Exception as e:
        print(f"❌ Failed to open browser: {e}")
        print("🌐 Please manually open: http://localhost:8000")