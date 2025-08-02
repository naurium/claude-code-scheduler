#!/usr/bin/env python3

import os
import sys
import json
import platform
import subprocess
import argparse
from pathlib import Path
from datetime import datetime, timedelta

class ClaudeSchedulerStatus:
    def __init__(self, config_path='config.json', show_logs=False):
        self.show_logs = show_logs
        self.platform = platform.system().lower()
        self.script_dir = Path(__file__).parent.absolute()
        self.config_path = self.script_dir / config_path
        self.home_dir = Path.home()
        
        if self.platform == 'darwin':
            self.platform = 'macos'
        
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            
            # Detect configuration mode
            if 'schedule' in self.config:
                self.config['mode'] = 'manual'
            elif 'start_time' in self.config:
                self.config['mode'] = 'simple'
                self.config['schedule'] = self.generate_schedule_times(self.config)
            else:
                print("Warning: Invalid config - using defaults")
                self.config = self.get_default_config()
        else:
            print("Warning: config.json not found, using defaults")
            self.config = self.get_default_config()
    
    def get_default_config(self):
        config = {
            'start_time': '06:15',
            'wake_minutes_before': 5,
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
        # Generate schedule from start_time
        config['schedule'] = self.generate_schedule_times(config)
        return config
    
    def generate_schedule_times(self, config):
        """Generate 4 schedule times at 5-hour intervals from start_time"""
        start_time_str = config.get('start_time', '06:15')
        wake_minutes = config.get('wake_minutes_before', 5)
        
        # Parse start time
        hour, minute = map(int, start_time_str.split(':'))
        
        schedules = []
        for interval in [0, 5, 10, 15]:  # 0, +5h, +10h, +15h
            new_hour = (hour + interval) % 24
            schedules.append({
                'time': f"{new_hour:02d}:{minute:02d}",
                'wake_minutes_before': wake_minutes
            })
        
        return schedules
    
    def get_next_run_time(self):
        now = datetime.now()
        schedule_times = []
        
        for sched in self.config['schedule']:
            time_str = sched['time']
            hour, minute = map(int, time_str.split(':'))
            
            next_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_time <= now:
                next_time += timedelta(days=1)
            
            schedule_times.append(next_time)
        
        return min(schedule_times)
    
    def check_macos_status(self):
        print("\n=== macOS Scheduler Status ===")
        
        daemon_label = self.config['platform_settings']['macos']['daemon_label']
        
        try:
            result = subprocess.run(['sudo', 'launchctl', 'list'], 
                                  capture_output=True, text=True)
            
            if daemon_label in result.stdout:
                print(f"✓ LaunchDaemon '{daemon_label}' is loaded in launchd")
                
                lines = result.stdout.split('\n')
                for line in lines:
                    if daemon_label in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            pid = parts[0]
                            status = parts[1]
                            if pid != '-':
                                print(f"  PID: {pid}")
                            print(f"  Last exit status: {status}")
            else:
                print(f"✗ LaunchDaemon '{daemon_label}' is not loaded in launchd")
            
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
    
    def check_linux_status(self):
        print("\n=== Linux Scheduler Status ===")
        
        service_name = self.config['platform_settings']['linux']['service_name']
        
        systemd_check = subprocess.run(['systemctl', '--version'], 
                                      capture_output=True, text=True).returncode == 0
        
        if systemd_check:
            try:
                timer_status = subprocess.run(['systemctl', 'status', f'{service_name}.timer'], 
                                            capture_output=True, text=True)
                
                if 'active (waiting)' in timer_status.stdout or 'active (running)' in timer_status.stdout:
                    print(f"✓ Systemd timer '{service_name}.timer' is active")
                    
                    for line in timer_status.stdout.split('\n'):
                        if 'Trigger:' in line:
                            print(f"  {line.strip()}")
                        elif 'Active:' in line:
                            print(f"  {line.strip()}")
                else:
                    print(f"✗ Systemd timer '{service_name}.timer' is not active")
                
                service_status = subprocess.run(['systemctl', 'status', f'{service_name}.service'], 
                                              capture_output=True, text=True)
                
                for line in service_status.stdout.split('\n'):
                    if 'Main PID:' in line or 'Active:' in line:
                        print(f"  {line.strip()}")
                
            except subprocess.CalledProcessError:
                print(f"✗ Service '{service_name}' not found")
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
    
    def check_windows_status(self):
        print("\n=== Windows Scheduler Status ===")
        
        task_name = self.config['platform_settings']['windows']['task_name']
        
        try:
            result = subprocess.run(['schtasks', '/query', '/tn', task_name, '/v', '/fo', 'list'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✓ Windows Task Scheduler task '{task_name}' is registered")
                
                for line in result.stdout.split('\n'):
                    if any(key in line for key in ['Status:', 'Last Run Time:', 'Next Run Time:', 'State:']):
                        print(f"  {line.strip()}")
            else:
                print(f"✗ Windows Task Scheduler task '{task_name}' not found")
        except Exception as e:
            print(f"Error checking status: {e}")
    
    def show_recent_logs(self, lines=20):
        print(f"\n=== Recent Log Entries (last {lines} lines) ===")
        
        log_file = self.home_dir / 'logs' / 'claude_scheduler.log'
        
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    all_lines = f.readlines()
                    recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                    
                    for line in recent_lines:
                        print(line.rstrip())
            except Exception as e:
                print(f"Error reading log file: {e}")
        else:
            print(f"Log file not found: {log_file}")
    
    def check_claude_availability(self):
        print("\n=== Claude CLI Check ===")
        
        if self.platform == 'windows':
            # Windows requires WSL - check for WSL first
            import shutil
            wsl_available = shutil.which('wsl')
            
            if not wsl_available:
                print(f"✗ WSL not found")
                print(f"  Please install WSL and claude within it")
                return
            
            # WSL is available, now check for claude inside WSL
            try:
                result = subprocess.run(['wsl', 'claude', '--version'], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✓ Claude CLI is available through WSL")
                    if result.stdout:
                        print(f"  Version: {result.stdout.strip()}")
                else:
                    print(f"✗ Claude CLI not found in WSL")
                    print(f"  Please ensure claude is installed inside WSL")
            except Exception as e:
                print(f"✗ Error checking claude in WSL: {e}")
                print(f"  Please ensure claude is installed inside WSL")
        else:
            # macOS and Linux
            try:
                result = subprocess.run(['claude', '--version'], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✓ Claude CLI is available")
                    if result.stdout:
                        print(f"  Version: {result.stdout.strip()}")
                else:
                    print(f"✗ Claude CLI returned error")
            except FileNotFoundError:
                print(f"✗ Claude CLI not found in PATH")
                print(f"  Please ensure 'claude' is installed and in your PATH")
    
    def run(self):
        print("Claude Scheduler Status")
        print("=" * 50)
        
        self.check_claude_availability()
        
        if self.platform == 'macos':
            self.check_macos_status()
        elif self.platform == 'linux':
            self.check_linux_status()
        elif self.platform == 'windows':
            self.check_windows_status()
        else:
            print(f"Unsupported platform: {self.platform}")
            return
        
        print("\n=== Schedule Configuration ===")
        
        mode = self.config.get('mode', 'simple')
        if mode == 'simple':
            start_time = self.config.get('start_time', '06:15')
            print(f"Mode: SIMPLE (automatic 5-hour intervals)")
            print(f"Start time: {start_time}")
            print(f"Sessions repeat every 5 hours (4 sessions per day)")
            print(f"Wake computer: {self.config.get('wake_minutes_before', 5)} minutes before each session")
        else:
            print(f"Mode: MANUAL (custom schedule)")
            print(f"Custom times configured: {len(self.config['schedule'])} sessions")
            print(f"Wake computer: varies per session")
        
        print("\nScheduled times:")
        for sched in self.config['schedule']:
            wake_mins = sched.get('wake_minutes_before', self.config.get('wake_minutes_before', 5))
            print(f"  • {sched['time']} (wake {wake_mins} min before)")
        
        next_run = self.get_next_run_time()
        print(f"\nNext scheduled run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        
        time_until = next_run - datetime.now()
        hours, remainder = divmod(time_until.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        print(f"Time until next run: {hours}h {minutes}m")
        
        if self.show_logs:
            self.show_recent_logs()
        
        print("\n" + "=" * 50)
        print("Status check complete!")

def main():
    parser = argparse.ArgumentParser(description='Claude Scheduler Status')
    parser.add_argument('--logs', action='store_true', 
                       help='Show recent log entries')
    parser.add_argument('--config', default='config.json', 
                       help='Path to configuration file')
    
    args = parser.parse_args()
    
    status_checker = ClaudeSchedulerStatus(
        config_path=args.config,
        show_logs=args.logs
    )
    
    try:
        status_checker.run()
    except KeyboardInterrupt:
        print("\nStatus check cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()