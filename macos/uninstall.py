#!/usr/bin/env python3

import sys
import subprocess
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from common.base import BaseSchedulerUninstall


class MacOSSchedulerUninstall(BaseSchedulerUninstall):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if hasattr(self, 'config') and 'platform_settings' in self.config:
            self.daemon_label = self.config['platform_settings']['macos'].get('daemon_label', 'ClaudeScheduler')
    
    def uninstall(self):
        print("\n=== Uninstalling macOS scheduler ===")
        
        errors_occurred = False
        
        try:
            # 1. Unload and remove Wake Daemon (if exists)
            wake_daemon_plist = f'/Library/LaunchDaemons/{self.daemon_label}.Wake.plist'
            if Path(wake_daemon_plist).exists():
                print("\nUnloading wake daemon...")
                result = subprocess.run(['sudo', 'launchctl', 'unload', wake_daemon_plist], 
                                      capture_output=True, text=True)
                if result.returncode != 0 and 'No such process' not in result.stderr:
                    print(f"  Warning: {result.stderr.strip()}")
                
                print("Removing wake daemon plist...")
                subprocess.run(['sudo', 'rm', wake_daemon_plist], check=True)
                print("  ✓ Wake daemon removed")
            
            # Check for old-style daemon (from previous versions)
            old_daemon_plist = f'/Library/LaunchDaemons/{self.daemon_label}.plist'
            if Path(old_daemon_plist).exists():
                print("\nRemoving old-style daemon...")
                subprocess.run(['sudo', 'launchctl', 'unload', old_daemon_plist], 
                             capture_output=True, text=True)
                subprocess.run(['sudo', 'rm', old_daemon_plist], check=True)
                print("  ✓ Old daemon removed")
            
            # 2. Unload and remove Claude Agent
            agent_plist = Path.home() / 'Library' / 'LaunchAgents' / f'{self.daemon_label}.Agent.plist'
            if agent_plist.exists():
                print("\nUnloading Claude agent...")
                result = subprocess.run(['launchctl', 'unload', str(agent_plist)], 
                                      capture_output=True, text=True)
                if result.returncode != 0 and 'No such process' not in result.stderr:
                    print(f"  Warning: {result.stderr.strip()}")
                
                print("Removing agent plist...")
                agent_plist.unlink()
                print("  ✓ Claude agent removed")
            
            # 3. Clean up any orphaned agents from testing (even without plist files)
            print("\nCleaning up any orphaned agents...")
            known_test_labels = [
                'ClaudeAgent',  # Legacy test name
                'ClaudeScheduler',  # Legacy single agent/daemon
                f'{self.daemon_label}',  # Base name without suffix
            ]
            
            for label in known_test_labels:
                result = subprocess.run(['launchctl', 'remove', label], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"  ✓ Removed orphaned agent: {label}")
            
            print("Cancelling wake schedules...")
            subprocess.run(['sudo', 'pmset', 'repeat', 'cancel'], 
                          capture_output=True, text=True)
            subprocess.run(['sudo', 'pmset', 'schedule', 'cancelall'], 
                          capture_output=True, text=True)
            
            # Clean up Application Support directory
            app_support_dir = Path.home() / 'Library' / 'Application Support' / 'ClaudeScheduler'
            if app_support_dir.exists():
                print(f"Removing application directory: {app_support_dir}")
                import shutil
                shutil.rmtree(app_support_dir)
            
            if self.remove_logs:
                # Remove new log directory
                log_dir = Path.home() / 'Library' / 'Logs' / 'ClaudeScheduler'
                if log_dir.exists():
                    print(f"Removing log directory: {log_dir}")
                    import shutil
                    shutil.rmtree(log_dir)
                
                # Also try to remove old log files
                old_log_files = [
                    self.home_dir / 'logs' / 'claude_scheduler.log',
                    Path('/var/log/claude-scheduler.log'),
                    Path('/var/log/claude-scheduler.out'),
                    Path('/var/log/claude-scheduler.err')
                ]
                for log_file in old_log_files:
                    if log_file.exists():
                        print(f"Removing old log file: {log_file}")
                        try:
                            subprocess.run(['sudo', 'rm', str(log_file)], 
                                         capture_output=True, text=True)
                        except:
                            pass
            
            if not errors_occurred:
                print("\nmacOS scheduler uninstalled successfully!")
            else:
                print("\nmacOS scheduler uninstalled with some warnings.")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error during uninstallation: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False