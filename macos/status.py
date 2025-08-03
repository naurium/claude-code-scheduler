#!/usr/bin/env python3

import sys
import subprocess
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from common.base import BaseSchedulerStatus


class MacOSSchedulerStatus(BaseSchedulerStatus):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if hasattr(self, 'config') and 'platform_settings' in self.config:
            self.daemon_label = self.config['platform_settings']['macos'].get('daemon_label', 'com.claude.scheduler')
    
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