#!/usr/bin/env python3

import os
import sys
import json
import platform
import subprocess
import shutil
import stat
from pathlib import Path
import getpass
from string import Template
from datetime import datetime, timedelta
from abc import ABC, abstractmethod


class BaseSchedulerSetup(ABC):
    def __init__(self, config_path='config.json', dry_run=False, verbose=False, 
                 notification_topic=None, remove_notifications=False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.notification_topic = notification_topic
        self.remove_notifications = remove_notifications
        self.platform = platform.system().lower()
        self.username = getpass.getuser()
        self.home_dir = Path.home()
        self.script_dir = Path(__file__).parent.parent.absolute()
        self.config_path = self.script_dir / config_path
        self.config = self.load_config()
        
        # Handle notification settings
        if self.notification_topic:
            self.config['notification_topic'] = self.notification_topic
            print(f"Notifications will be sent to: ntfy.sh/{self.notification_topic}")
        elif self.remove_notifications:
            self.config.pop('notification_topic', None)
            print("Notifications will be disabled")
        
        if self.verbose:
            print(f"Platform detected: {self.platform}")
            print(f"Username: {self.username}")
            print(f"Home directory: {self.home_dir}")
    
    def load_config(self):
        first_time_setup = False
        if not self.config_path.exists():
            # Try to copy from config.example.json
            example_path = self.script_dir / 'config.example.json'
            if example_path.exists():
                print("No config.json found. Let's set up your schedule!")
                shutil.copy(example_path, self.config_path)
                first_time_setup = True
            else:
                print(f"Error: Neither {self.config_path} nor {example_path} found")
                sys.exit(1)
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # If first time setup and in simple mode, prompt for start time
        if first_time_setup and 'start_time' in config and 'schedule' not in config:
            if not self.dry_run:  # Only prompt in real runs
                print("\nWhat time would you like your first Claude session?")
                while True:
                    user_time = input("Enter time in 24-hour format (e.g., 06:15): ").strip()
                    # Basic validation
                    if ':' in user_time and len(user_time.split(':')) == 2:
                        try:
                            hours, minutes = user_time.split(':')
                            h = int(hours)
                            m = int(minutes)
                            if 0 <= h <= 23 and 0 <= m <= 59:
                                config['start_time'] = user_time
                                # Generate and show the 4 sessions
                                schedule = self.generate_schedule_times(config)
                                print(f"\nThis will create 4 daily sessions at:")
                                for sched in schedule:
                                    print(f"  - {sched['time']}")
                                print()
                                # Save the updated config
                                with open(self.config_path, 'w', encoding='utf-8') as f:
                                    json.dump(config, f, indent=2)
                                print(f"Config saved to {self.config_path}\n")
                                break
                        except ValueError:
                            pass
                    print("Invalid time format. Please use HH:MM (e.g., 09:00)")
            else:
                print(f"Created {self.config_path} with default start time {config['start_time']}")
        
        if self.platform == 'darwin':
            self.platform = 'macos'
        
        # Validate command to prevent injection attacks
        self.validate_command(config)
        
        # Detect configuration mode
        if 'schedule' in config:
            # Manual mode - user has specified exact times
            print("Using MANUAL mode - custom schedule times")
            if self.verbose:
                print("Schedule times:")
                for sched in config['schedule']:
                    print(f"  - {sched['time']} (wake {sched.get('wake_minutes_before', 5)} min before)")
        elif 'start_time' in config:
            # Auto mode - generate 4 schedule times from start_time
            print(f"Using SIMPLE mode - generating 4 sessions from {config['start_time']}")
            config['schedule'] = self.generate_schedule_times(config)
        else:
            print("Error: config.json must contain either 'start_time' (simple mode) or 'schedule' (manual mode)")
            sys.exit(1)
        
        return config
    
    def validate_command(self, config):
        """Validate command to prevent injection attacks"""
        command = config.get('command', '')
        
        # Extract the actual command (first word)
        cmd_parts = command.split()
        if not cmd_parts:
            print("Error: No command specified in config")
            sys.exit(1)
        
        cmd = cmd_parts[0]
        
        # Allow full paths to claude executable
        if '/' in cmd or '\\' in cmd:
            # It's a path - just ensure it contains 'claude' somewhere
            if 'claude' not in cmd.lower():
                print(f"Error: Command path '{cmd}' doesn't appear to be a claude executable")
                print("For security, only 'claude' commands are allowed")
                sys.exit(1)
        else:
            # It's a command name - must be exactly 'claude'
            if cmd != 'claude':
                print(f"Error: Command '{cmd}' is not allowed")
                print("For security, only 'claude' commands are allowed")
                sys.exit(1)
        
        # Also validate Windows command if present
        if self.platform == 'windows' and 'platform_settings' in config:
            win_cmd = config.get('platform_settings', {}).get('windows', {}).get('command', '')
            if win_cmd and win_cmd != command:
                # Windows has a different command, validate it too
                win_cmd_parts = win_cmd.split()
                if win_cmd_parts:
                    win_cmd_name = win_cmd_parts[0]
                    if '/' in win_cmd_name or '\\' in win_cmd_name:
                        if 'claude' not in win_cmd_name.lower():
                            print(f"Error: Windows command path '{win_cmd_name}' doesn't appear to be a claude executable")
                            sys.exit(1)
                    elif win_cmd_name != 'claude':
                        print(f"Error: Windows command '{win_cmd_name}' is not allowed")
                        sys.exit(1)
        
        if self.verbose:
            print(f"Command validation passed: {cmd}")
    
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
        
        if self.verbose:
            print(f"Generated schedule times from {start_time_str}:")
            for sched in schedules:
                print(f"  - {sched['time']} (wake {sched['wake_minutes_before']} min before)")
        
        return schedules
    
    def create_scripts_directory(self):
        scripts_dir = self.script_dir / 'scripts'
        if not self.dry_run:
            scripts_dir.mkdir(exist_ok=True)
        print(f"Scripts directory: {scripts_dir}")
        return scripts_dir
    
    def create_logs_directory(self):
        logs_dir = self.home_dir / 'logs'
        if not self.dry_run:
            logs_dir.mkdir(exist_ok=True)
            if self.verbose:
                print(f"Logs directory created: {logs_dir}")
        return logs_dir
    
    def generate_from_template(self, template_path, output_path, substitutions):
        if self.verbose:
            print(f"Generating {output_path} from {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template = Template(f.read())
        
        content = template.safe_substitute(substitutions)
        
        if not self.dry_run:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            if self.platform != 'windows':
                os.chmod(output_path, 0o755)
    
    def save_config(self):
        """Save the updated config file with notification settings"""
        if not self.dry_run:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            if self.verbose:
                print(f"Configuration saved to {self.config_path}")
    
    @abstractmethod
    def check_prerequisites(self):
        """Platform-specific prerequisite checks"""
        pass
    
    @abstractmethod
    def register(self):
        """Platform-specific registration logic"""
        pass
    
    def run(self):
        print("Claude Scheduler Setup")
        print("=" * 50)
        
        if self.dry_run:
            print("*** DRY RUN MODE - No changes will be made ***\n")
        
        if not self.check_prerequisites():
            sys.exit(1)
        
        # Save updated config with notification settings
        if self.notification_topic or self.remove_notifications:
            self.save_config()
        
        self.register()
        
        print("\n" + "=" * 50)
        print("Setup complete!")
        print(f"Run 'python status.py' to check the scheduler status")
        print(f"Run 'python uninstall.py' to remove the scheduler")
        
        if self.notification_topic:
            print(f"\nNotifications enabled! Test with:")
            print(f"  curl -d 'Test notification' ntfy.sh/{self.notification_topic}")


class BaseSchedulerStatus(ABC):
    def __init__(self, config_path='config.json', show_logs=False):
        self.show_logs = show_logs
        self.platform = platform.system().lower()
        self.script_dir = Path(__file__).parent.parent.absolute()
        self.config_path = self.script_dir / config_path
        self.home_dir = Path.home()
        
        if self.platform == 'darwin':
            self.platform = 'macos'
        
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
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
                    'daemon_label': 'ClaudeScheduler'
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
    
    def show_recent_logs(self, lines=20):
        print(f"\n=== Recent Log Entries (last {lines} lines) ===")
        
        log_file = self.home_dir / 'logs' / 'claude_scheduler.log'
        
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
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
            wsl_path = shutil.which('wsl')
            
            if not wsl_path:
                print("X WSL not found")
                print(f"  Please install WSL and claude within it")
                return
            
            # WSL is available, now check for claude inside WSL with proper PATH
            try:
                # Use the same PATH setup as the PowerShell script
                wsl_command = "source ~/.bashrc 2>/dev/null; source ~/.nvm/nvm.sh 2>/dev/null; export PATH='$HOME/.nvm/versions/node/v20.19.3/bin:$HOME/.local/bin:$HOME/.npm-global/bin:/usr/local/bin:/usr/bin:/bin'; claude --version"
                result = subprocess.run([wsl_path, 'bash', '-c', wsl_command], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("+ Claude CLI is available through WSL")
                    if result.stdout:
                        print(f"  Version: {result.stdout.strip()}")
                else:
                    print("X Claude CLI not found in WSL")
                    print(f"  Please ensure claude is installed inside WSL")
            except Exception as e:
                print(f"X Error checking claude in WSL: {e}")
                print(f"  Please ensure claude is installed inside WSL")
        else:
            # macOS and Linux
            try:
                result = subprocess.run(['claude', '--version'], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("+ Claude CLI is available")
                    if result.stdout:
                        print(f"  Version: {result.stdout.strip()}")
                else:
                    print("X Claude CLI returned error")
            except FileNotFoundError:
                print("X Claude CLI not found in PATH")
                print(f"  Please ensure 'claude' is installed and in your PATH")
    
    @abstractmethod
    def check_status(self):
        """Platform-specific status checking"""
        pass
    
    @abstractmethod
    def test_script(self):
        """Test run the scheduler script to verify it works"""
        pass
    
    def run(self):
        print("Claude Scheduler Status")
        print("=" * 50)
        
        self.check_claude_availability()
        self.check_status()
        
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
            print(f"  - {sched['time']} (wake {wake_mins} min before)")
        
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


class BaseSchedulerUninstall(ABC):
    def __init__(self, config_path='config.json', remove_logs=False):
        self.remove_logs = remove_logs
        self.platform = platform.system().lower()
        self.script_dir = Path(__file__).parent.parent.absolute()
        self.config_path = self.script_dir / config_path
        self.home_dir = Path.home()
        
        if self.platform == 'darwin':
            self.platform = 'macos'
        
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            print("Warning: config.json not found, using defaults")
            self.config = self.get_default_config()
    
    def get_default_config(self):
        return {
            'platform_settings': {
                'macos': {
                    'daemon_label': 'ClaudeScheduler'
                },
                'linux': {
                    'service_name': 'claude-scheduler'
                },
                'windows': {
                    'task_name': 'ClaudeScheduler'
                }
            }
        }
    
    def clean_scripts_directory(self):
        scripts_dir = self.script_dir / 'scripts'
        if scripts_dir.exists():
            print(f"Cleaning scripts directory: {scripts_dir}")
            shutil.rmtree(scripts_dir)
    
    @abstractmethod
    def uninstall(self):
        """Platform-specific uninstall logic"""
        pass
    
    def run(self):
        print("Claude Scheduler Uninstaller")
        print("=" * 50)
        
        confirm = input("Are you sure you want to uninstall the Claude Scheduler? (yes/no): ")
        if confirm.lower() not in ['yes', 'y']:
            print("Uninstallation cancelled.")
            return
        
        success = self.uninstall()
        
        if success:
            self.clean_scripts_directory()
            print("\n" + "=" * 50)
            print("Uninstallation complete!")
        else:
            print("\n" + "=" * 50)
            print("Uninstallation encountered errors. Please check the messages above.")