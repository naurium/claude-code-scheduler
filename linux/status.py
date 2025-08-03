#!/usr/bin/env python3

import sys
import subprocess
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from common.base import BaseSchedulerStatus


class LinuxSchedulerStatus(BaseSchedulerStatus):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if hasattr(self, 'config') and 'platform_settings' in self.config:
            self.service_name = self.config['platform_settings']['linux'].get('service_name', 'claude-scheduler')
    
    def check_status(self):
        print("\n=== Linux Scheduler Status ===")
        
        systemd_check = subprocess.run(['systemctl', '--version'], 
                                      capture_output=True, text=True).returncode == 0
        
        if systemd_check:
            try:
                timer_status = subprocess.run(['systemctl', 'status', f'{self.service_name}.timer'], 
                                            capture_output=True, text=True)
                
                if 'active (waiting)' in timer_status.stdout or 'active (running)' in timer_status.stdout:
                    print(f"✓ Systemd timer '{self.service_name}.timer' is active")
                    
                    for line in timer_status.stdout.split('\n'):
                        if 'Trigger:' in line:
                            print(f"  {line.strip()}")
                        elif 'Active:' in line:
                            print(f"  {line.strip()}")
                else:
                    print(f"✗ Systemd timer '{self.service_name}.timer' is not active")
                
                service_status = subprocess.run(['systemctl', 'status', f'{self.service_name}.service'], 
                                              capture_output=True, text=True)
                
                for line in service_status.stdout.split('\n'):
                    if 'Main PID:' in line or 'Active:' in line:
                        print(f"  {line.strip()}")
                
            except subprocess.CalledProcessError:
                print(f"✗ Service '{self.service_name}' not found")
        else:
            try:
                cron_result = subprocess.run(['crontab', '-l'], 
                                           capture_output=True, text=True)
                
                if 'claude_scheduler.sh' in cron_result.stdout:
                    print("✓ Cron entries are registered")
                    print("\nCron schedule:")
                    for line in cron_result.stdout.split('\n'):
                        if 'claude_scheduler.sh' in line:
                            print(f"  {line}")
                else:
                    print("✗ No cron entries found")
            except:
                print("✗ Unable to check cron status")