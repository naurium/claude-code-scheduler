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
            self.daemon_label = self.config['platform_settings']['macos'].get('daemon_label', 'com.claude.scheduler')
    
    def uninstall(self):
        print("\n=== Uninstalling macOS scheduler ===")
        
        plist_path = f'/Library/LaunchDaemons/{self.daemon_label}.plist'
        
        try:
            print("Unloading from launchd...")
            subprocess.run(['sudo', 'launchctl', 'unload', plist_path], 
                          capture_output=True, text=True)
            
            print("Removing LaunchDaemon plist...")
            subprocess.run(['sudo', 'rm', plist_path], check=True)
            
            print("Cancelling wake schedules...")
            subprocess.run(['sudo', 'pmset', 'repeat', 'cancel'], 
                          capture_output=True, text=True)
            subprocess.run(['sudo', 'pmset', 'schedule', 'cancelall'], 
                          capture_output=True, text=True)
            
            if self.remove_logs:
                log_files = [
                    self.home_dir / 'logs' / 'claude_scheduler.log',
                    Path('/var/log/claude-scheduler.log'),
                    Path('/var/log/claude-scheduler.out'),
                    Path('/var/log/claude-scheduler.err')
                ]
                for log_file in log_files:
                    if log_file.exists():
                        print(f"Removing log file: {log_file}")
                        subprocess.run(['sudo', 'rm', str(log_file)], 
                                     capture_output=True, text=True)
            
            print("macOS scheduler uninstalled successfully!")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error during uninstallation: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False