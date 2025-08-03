#!/usr/bin/env python3

import sys
import subprocess
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from common.base import BaseSchedulerUninstall


class WindowsSchedulerUninstall(BaseSchedulerUninstall):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if hasattr(self, 'config') and 'platform_settings' in self.config:
            self.task_name = self.config['platform_settings']['windows'].get('task_name', 'ClaudeScheduler')
    
    def uninstall(self):
        print("\n=== Uninstalling Windows scheduler ===")
        
        try:
            print(f"Removing Windows Task Scheduler task '{self.task_name}'...")
            result = subprocess.run(['schtasks', '/delete', '/tn', self.task_name, '/f'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("Windows Task Scheduler task removed successfully!")
            else:
                print(f"Task may not exist or error occurred: {result.stderr}")
            
            if self.remove_logs:
                log_file = self.home_dir / 'logs' / 'claude_scheduler.log'
                if log_file.exists():
                    print(f"Removing log file: {log_file}")
                    log_file.unlink()
            
            return True
            
        except Exception as e:
            print(f"Error during uninstallation: {e}")
            return False