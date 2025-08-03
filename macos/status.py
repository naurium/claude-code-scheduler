#!/usr/bin/env python3

import sys
import subprocess
import os
import stat
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from common.base import BaseSchedulerStatus


class MacOSSchedulerStatus(BaseSchedulerStatus):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if hasattr(self, 'config') and 'platform_settings' in self.config:
            self.daemon_label = self.config['platform_settings']['macos'].get('daemon_label', 'ClaudeScheduler')
    
    def check_status(self):
        print("\n=== macOS Scheduler Status ===")
        
        try:
            result = subprocess.run(['sudo', 'launchctl', 'list'], 
                                  capture_output=True, text=True)
            
            if self.daemon_label in result.stdout:
                print(f"✓ LaunchDaemon '{self.daemon_label}' is loaded in launchd")
                
                lines = result.stdout.split('\n')
                for line in lines:
                    if self.daemon_label in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            pid = parts[0]
                            status = parts[1]
                            if pid != '-':
                                print(f"  PID: {pid}")
                            print(f"  Last exit status: {status}")
            else:
                print(f"✗ LaunchDaemon '{self.daemon_label}' is not loaded in launchd")
            
            print("\nWake Schedule:")
            wake_result = subprocess.run(['pmset', '-g', 'sched'], 
                                        capture_output=True, text=True)
            
            if wake_result.stdout.strip():
                for line in wake_result.stdout.strip().split('\n'):
                    if line.strip():
                        print(f"  {line.strip()}")
            else:
                print("  No wake schedules set")
            
        except subprocess.CalledProcessError as e:
            print(f"Error checking status: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
    
    def test_script(self):
        """Test run the scheduler script to verify it works"""
        print("Claude Scheduler Test Mode")
        print("=" * 50)
        print("\n=== Testing macOS Scheduler Script ===\n")
        
        # Check for script in new location
        app_support_dir = Path.home() / 'Library' / 'Application Support' / 'ClaudeScheduler'
        script_path = app_support_dir / 'claude_daemon.sh'
        
        # Fall back to old location if not found
        if not script_path.exists():
            script_path = self.script_dir / 'scripts' / 'claude_daemon.sh'
            if not script_path.exists():
                print(f"✗ Script not found in:")
                print(f"  - {app_support_dir / 'claude_daemon.sh'}")
                print(f"  - {self.script_dir / 'scripts' / 'claude_daemon.sh'}")
                print("\nSolution: Run 'python3 setup.py' to generate the script")
                return
        
        print(f"✓ Script found: {script_path}")
        
        # Check script permissions
        try:
            st = os.stat(script_path)
            mode = st.st_mode
            is_executable = bool(mode & stat.S_IXUSR)
            
            print(f"\nScript permissions: {oct(stat.S_IMODE(mode))}")
            if is_executable:
                print("✓ Script is executable")
            else:
                print("✗ Script is not executable")
                print(f"\nFix with: chmod +x {script_path}")
        except Exception as e:
            print(f"Error checking permissions: {e}")
        
        # Check if script is in Application Support (good) or Documents (bad)
        if '/Application Support/' in str(script_path):
            print("✓ Script is in Application Support (no security restrictions)")
        elif '/Documents/' in str(script_path):
            print("\n⚠️  WARNING: Script is in Documents folder")
            print("macOS may block execution from Documents due to security restrictions")
            print("\nSolution: Run 'python3 setup.py' to install to Application Support")
        
        # Test run the script
        print("\n" + "=" * 30)
        print("Testing script execution...")
        print("=" * 30 + "\n")
        
        try:
            # Run with a 5 second timeout
            result = subprocess.run(
                ['/bin/bash', str(script_path)],
                capture_output=True,
                text=True,
                timeout=5,
                env={**os.environ, 'PATH': '/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin:' + os.environ.get('PATH', '')}
            )
            
            if result.returncode == 0:
                print("✓ Script executed successfully!")
                if result.stdout:
                    print("\nScript output:")
                    print("-" * 30)
                    print(result.stdout)
                if result.stderr:
                    print("\nScript warnings/errors:")
                    print("-" * 30)
                    print(result.stderr)
            else:
                print(f"✗ Script failed with exit code: {result.returncode}")
                if result.stdout:
                    print("\nScript output:")
                    print("-" * 30)
                    print(result.stdout)
                if result.stderr:
                    print("\nScript errors:")
                    print("-" * 30)
                    print(result.stderr)
                    
                # Check for specific error patterns
                if "Operation not permitted" in result.stderr:
                    print("\n⚠️  macOS Security Block Detected!")
                    print("The script is being blocked by macOS security.")
                    print("\nSolutions:")
                    print("1. Move the project outside of Documents folder")
                    print("2. Run: sudo spctl --master-disable (temporarily disable Gatekeeper)")
                    print("3. Grant Terminal Full Disk Access in System Preferences")
                    
        except subprocess.TimeoutExpired:
            print("✓ Script is running (timed out after 5 seconds - this is normal)")
            print("The script appears to be working but takes longer than 5 seconds to complete.")
        except FileNotFoundError:
            print("✗ bash not found - this should not happen on macOS")
        except Exception as e:
            print(f"✗ Error running script: {e}")
            if "Operation not permitted" in str(e):
                print("\n⚠️  macOS is blocking script execution from Documents folder!")
                print("Move this project to ~/Development/ or another location")
        
        # Check log files
        print("\n" + "=" * 30)
        print("Checking log files...")
        print("=" * 30 + "\n")
        
        log_locations = [
            Path.home() / 'Library' / 'Logs' / 'ClaudeScheduler' / 'scheduler.log',
            Path.home() / 'Library' / 'Logs' / 'ClaudeScheduler' / 'scheduler.out',
            Path.home() / 'Library' / 'Logs' / 'ClaudeScheduler' / 'scheduler.err',
            Path.home() / 'Library' / 'Logs' / 'ClaudeScheduler' / 'claude_scheduler.log',
            # Fall back to old locations
            self.home_dir / 'logs' / 'claude_scheduler.log',
            Path('/var/log/claude-scheduler.log'),
            Path('/var/log/claude-scheduler.out'),
            Path('/var/log/claude-scheduler.err')
        ]
        
        found_logs = False
        for log_path in log_locations:
            if log_path.exists():
                found_logs = True
                print(f"✓ Log file found: {log_path}")
                try:
                    # Show last few lines
                    with open(log_path, 'r') as f:
                        lines = f.readlines()
                        if lines:
                            print(f"  Last entry: {lines[-1].strip()}")
                except PermissionError:
                    print(f"  (Permission denied reading log)")
        
        if not found_logs:
            print("✗ No log files found yet")
            print("Logs will be created after the first successful run")
        
        print("\n" + "=" * 50)
        print("Test complete!")