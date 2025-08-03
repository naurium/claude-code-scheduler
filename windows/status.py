#!/usr/bin/env python3

import sys
import subprocess
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from common.base import BaseSchedulerStatus


class WindowsSchedulerStatus(BaseSchedulerStatus):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if hasattr(self, 'config') and 'platform_settings' in self.config:
            self.task_name = self.config['platform_settings']['windows'].get('task_name', 'ClaudeScheduler')
    
    def check_status(self):
        print("\n=== Windows Scheduler Status ===")
        
        try:
            result = subprocess.run(['schtasks', '/query', '/tn', self.task_name, '/v', '/fo', 'list'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✓ Windows Task Scheduler task '{self.task_name}' is registered")
                
                for line in result.stdout.split('\n'):
                    if any(key in line for key in ['Status:', 'Last Run Time:', 'Next Run Time:', 'State:']):
                        print(f"  {line.strip()}")
            else:
                print(f"✗ Windows Task Scheduler task '{self.task_name}' not found")
        except Exception as e:
            print(f"Error checking status: {e}")