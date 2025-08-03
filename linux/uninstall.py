#!/usr/bin/env python3

import sys
import subprocess
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from common.base import BaseSchedulerUninstall


class LinuxSchedulerUninstall(BaseSchedulerUninstall):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if hasattr(self, 'config') and 'platform_settings' in self.config:
            self.service_name = self.config['platform_settings']['linux'].get('service_name', 'claude-scheduler')
    
    def uninstall(self):
        print("\n=== Uninstalling Linux scheduler ===")
        
        systemd_check = subprocess.run(['systemctl', '--version'], 
                                      capture_output=True, text=True).returncode == 0
        
        if systemd_check:
            try:
                print("Stopping and disabling systemd timer...")
                subprocess.run(['sudo', 'systemctl', 'stop', f'{self.service_name}.timer'], 
                              capture_output=True, text=True)
                subprocess.run(['sudo', 'systemctl', 'disable', f'{self.service_name}.timer'], 
                              capture_output=True, text=True)
                
                print("Removing systemd service and timer files...")
                service_file = f'/etc/systemd/system/{self.service_name}.service'
                timer_file = f'/etc/systemd/system/{self.service_name}.timer'
                
                if Path(service_file).exists():
                    subprocess.run(['sudo', 'rm', service_file], check=True)
                if Path(timer_file).exists():
                    subprocess.run(['sudo', 'rm', timer_file], check=True)
                
                print("Reloading systemd configuration...")
                subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
                
                print("Linux systemd timer removed successfully!")
                
            except subprocess.CalledProcessError as e:
                print(f"Error during uninstallation: {e}")
                return False
        else:
            try:
                print("Removing cron entries...")
                cron_process = subprocess.Popen(['crontab', '-l'], 
                                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                current_cron, _ = cron_process.communicate()
                
                lines = current_cron.decode().split('\n')
                filtered_lines = [line for line in lines 
                                if 'claude_scheduler.sh' not in line and line.strip()]
                new_cron = '\n'.join(filtered_lines)
                
                if new_cron.strip():
                    print("Updating crontab...")
                    cron_process = subprocess.Popen(['crontab', '-'], 
                                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                    cron_process.communicate(input=new_cron.encode())
                else:
                    print("Removing empty crontab...")
                    subprocess.run(['crontab', '-r'], capture_output=True, text=True)
                
                print("Linux cron entries removed successfully!")
                
            except Exception as e:
                print(f"Error removing cron jobs: {e}")
                return False
        
        if self.remove_logs:
            log_file = self.home_dir / 'logs' / 'claude_scheduler.log'
            if log_file.exists():
                print(f"Removing log file: {log_file}")
                log_file.unlink()
        
        return True