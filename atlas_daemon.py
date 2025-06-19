#!/usr/bin/env python3
"""
ATLAS Auto-Commit Daemon
Continuously monitors for git changes and applies automatic commits
"""

import os
import sys
import time
import signal
import atexit
import subprocess
from datetime import datetime
from atlas_auto_commit import trigger_atlas_auto_commit

class AtlasDaemon:
    """ATLAS Auto-Commit Background Daemon"""
    
    def __init__(self, pidfile='/tmp/atlas_daemon.pid', monitor_interval=30):
        self.pidfile = pidfile
        self.monitor_interval = monitor_interval
        self.running = True
        
    def daemonize(self):
        """Daemonize the current process"""
        try:
            # First fork
            pid = os.fork()
            if pid > 0:
                sys.exit(0)  # Exit parent
        except OSError as e:
            sys.stderr.write(f"Fork #1 failed: {e}\n")
            sys.exit(1)
            
        # Decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)
        
        try:
            # Second fork
            pid = os.fork()
            if pid > 0:
                sys.exit(0)  # Exit parent
        except OSError as e:
            sys.stderr.write(f"Fork #2 failed: {e}\n")
            sys.exit(1)
            
        # Redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        
        # Write PID file
        with open(self.pidfile, 'w') as f:
            f.write(str(os.getpid()))
            
        # Register cleanup
        atexit.register(self.cleanup)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle termination signals"""
        self.running = False
        
    def cleanup(self):
        """Clean up PID file"""
        try:
            os.remove(self.pidfile)
        except:
            pass
            
    def is_running(self):
        """Check if daemon is already running"""
        if not os.path.exists(self.pidfile):
            return False
            
        try:
            with open(self.pidfile, 'r') as f:
                pid = int(f.read().strip())
            # Check if process exists
            os.kill(pid, 0)
            return True
        except (OSError, ValueError):
            # PID file exists but process doesn't
            os.remove(self.pidfile)
            return False
            
    def stop(self):
        """Stop the daemon"""
        if not os.path.exists(self.pidfile):
            print("🤖 ATLAS: Daemon not running")
            return
            
        try:
            with open(self.pidfile, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
            print("🤖 ATLAS: Daemon stopped")
        except (OSError, ValueError):
            print("🤖 ATLAS: Daemon not running")
            
        # Clean up PID file
        try:
            os.remove(self.pidfile)
        except:
            pass
            
    def start(self):
        """Start the daemon"""
        if self.is_running():
            print("🤖 ATLAS: Daemon already running")
            return
            
        print("🤖 ATLAS: Starting auto-commit daemon...")
        self.daemonize()
        self.run()
        
    def run(self):
        """Main daemon loop"""
        print(f"🤖 ATLAS: Auto-commit daemon started (PID: {os.getpid()})")
        
        while self.running:
            try:
                # Check if ATLAS auto-commit is enabled
                from atlas_auto_commit import AtlasAutoCommit
                atlas = AtlasAutoCommit()
                
                if atlas.enabled:
                    result = trigger_atlas_auto_commit()
                    if result['action'] == 'committed':
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"🤖 ATLAS [{timestamp}]: {result['message']}")
                        
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"🤖 ATLAS [{timestamp}]: Error in daemon loop: {e}")
                time.sleep(self.monitor_interval)
                
    def restart(self):
        """Restart the daemon"""
        self.stop()
        time.sleep(1)
        self.start()
        
    def status(self):
        """Check daemon status"""
        if self.is_running():
            print("🤖 ATLAS: Daemon is running")
        else:
            print("🤖 ATLAS: Daemon is not running")

def main():
    """Main entry point"""
    daemon = AtlasDaemon()
    
    if len(sys.argv) == 1:
        # Default action: start
        daemon.start()
    elif sys.argv[1] == 'start':
        daemon.start()
    elif sys.argv[1] == 'stop':
        daemon.stop()
    elif sys.argv[1] == 'restart':
        daemon.restart()
    elif sys.argv[1] == 'status':
        daemon.status()
    else:
        print("Usage: atlas_daemon.py {start|stop|restart|status}")
        sys.exit(1)

if __name__ == "__main__":
    main()