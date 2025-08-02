#!/usr/bin/env python3

import os
import sys
import json
import platform
import subprocess
import argparse
from pathlib import Path

class ClaudeSchedulerUninstall:
    def __init__(self, config_path='config.json', remove_logs=False):
        self.remove_logs = remove_logs
        self.platform = platform.system().lower()
        self.script_dir = Path(__file__).parent.absolute()
        self.config_path = self.script_dir / config_path
        self.home_dir = Path.home()
        
        if self.platform == 'darwin':
            self.platform = 'macos'
        
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        else:
            print("Warning: config.json not found, using defaults")
            self.config = self.get_default_config()
    
    def get_default_config(self):
        return {
            'platform_settings': {
                'macos': {
                    'daemon_label': 'com.claude.scheduler'
                },
                'linux': {
                    'service_name': 'claude-scheduler'
                },
                'windows': {
                    'task_name': 'ClaudeScheduler'
                }
            }
        }
    
    def uninstall_macos(self):
        print("\n=== Uninstalling macOS scheduler ===")
        
        daemon_label = self.config['platform_settings']['macos']['daemon_label']
        plist_path = f'/Library/LaunchDaemons/{daemon_label}.plist'
        
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
            
        except subprocess.CalledProcessError as e:
            print(f"Error during uninstallation: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False
        
        return True
    
    def uninstall_linux(self):
        print("\n=== Uninstalling Linux scheduler ===")
        
        service_name = self.config['platform_settings']['linux']['service_name']
        
        systemd_check = subprocess.run(['systemctl', '--version'], 
                                      capture_output=True, text=True).returncode == 0
        
        if systemd_check:
            try:
                print("Stopping and disabling systemd timer...")
                subprocess.run(['sudo', 'systemctl', 'stop', f'{service_name}.timer'], 
                              capture_output=True, text=True)
                subprocess.run(['sudo', 'systemctl', 'disable', f'{service_name}.timer'], 
                              capture_output=True, text=True)
                
                print("Removing systemd service and timer files...")
                service_file = f'/etc/systemd/system/{service_name}.service'
                timer_file = f'/etc/systemd/system/{service_name}.timer'
                
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
    
    def uninstall_windows(self):
        print("\n=== Uninstalling Windows scheduler ===")
        
        task_name = self.config['platform_settings']['windows']['task_name']
        
        try:
            print(f"Removing Windows Task Scheduler task '{task_name}'...")
            result = subprocess.run(['schtasks', '/delete', '/tn', task_name, '/f'], 
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
    
    def clean_scripts_directory(self):
        scripts_dir = self.script_dir / 'scripts'
        if scripts_dir.exists():
            print(f"Cleaning scripts directory: {scripts_dir}")
            import shutil
            shutil.rmtree(scripts_dir)
    
    def run(self):
        print("Claude Scheduler Uninstaller")
        print("=" * 50)
        
        confirm = input("Are you sure you want to uninstall the Claude Scheduler? (yes/no): ")
        if confirm.lower() not in ['yes', 'y']:
            print("Uninstallation cancelled.")
            return
        
        success = False
        
        if self.platform == 'macos':
            success = self.uninstall_macos()
        elif self.platform == 'linux':
            success = self.uninstall_linux()
        elif self.platform == 'windows':
            success = self.uninstall_windows()
        else:
            print(f"Unsupported platform: {self.platform}")
            sys.exit(1)
        
        if success:
            self.clean_scripts_directory()
            print("\n" + "=" * 50)
            print("Uninstallation complete!")
        else:
            print("\n" + "=" * 50)
            print("Uninstallation encountered errors. Please check the messages above.")

def main():
    parser = argparse.ArgumentParser(description='Claude Scheduler Uninstaller')
    parser.add_argument('--remove-logs', action='store_true', 
                       help='Also remove log files')
    parser.add_argument('--config', default='config.json', 
                       help='Path to configuration file')
    
    args = parser.parse_args()
    
    uninstaller = ClaudeSchedulerUninstall(
        config_path=args.config,
        remove_logs=args.remove_logs
    )
    
    try:
        uninstaller.run()
    except KeyboardInterrupt:
        print("\nUninstallation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()