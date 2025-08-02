#!/usr/bin/env python3

import os
import sys
import json
import platform
import subprocess
import shutil
import argparse
from pathlib import Path
import getpass
from string import Template
import time

class ClaudeSchedulerSetup:
    def __init__(self, config_path='config.json', dry_run=False, verbose=False, 
                 notification_topic=None, remove_notifications=False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.notification_topic = notification_topic
        self.remove_notifications = remove_notifications
        self.platform = platform.system().lower()
        self.username = getpass.getuser()
        self.home_dir = Path.home()
        self.script_dir = Path(__file__).parent.absolute()
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
        if not self.config_path.exists():
            print(f"Error: Configuration file {self.config_path} not found")
            sys.exit(1)
        
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        
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
    
    def check_prerequisites(self):
        print("Checking prerequisites...")
        
        if self.platform not in ['macos', 'linux', 'windows']:
            print(f"Error: Unsupported platform {self.platform}")
            return False
        
        # Windows requires WSL
        if self.platform == 'windows':
            wsl_check = shutil.which('wsl')
            if not wsl_check:
                print("Error: WSL (Windows Subsystem for Linux) not found.")
                print("Please install WSL and ensure claude is installed within WSL.")
                print("See: https://docs.microsoft.com/en-us/windows/wsl/install")
                return False
            print("✓ WSL found")
            print("Note: Claude must be installed and configured inside WSL")
        else:
            # macOS and Linux check for claude directly
            claude_check = shutil.which('claude')
            if not claude_check:
                print(f"Error: claude command not found. Please install Claude CLI first.")
                return False
            print("✓ Claude CLI found")
        
        if self.platform == 'linux':
            systemd_check = subprocess.run(['systemctl', '--version'], 
                                          capture_output=True, text=True).returncode == 0
            if systemd_check:
                self.linux_method = 'systemd'
            else:
                self.linux_method = 'cron'
            print(f"Linux scheduling method: {self.linux_method}")
        
        print("Prerequisites check passed!")
        return True
    
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
        
        with open(template_path, 'r') as f:
            template = Template(f.read())
        
        content = template.safe_substitute(substitutions)
        
        if not self.dry_run:
            with open(output_path, 'w') as f:
                f.write(content)
            if self.platform != 'windows':
                os.chmod(output_path, 0o755)
    
    def generate_macos_plist(self, daemon_label, script_path):
        """Generate plist XML with dynamic schedule times"""
        schedule_entries = []
        
        # Add schedule entries for command execution times
        for sched in self.config['schedule']:
            time_parts = sched['time'].split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            
            schedule_entries.append(f"""        <dict>
            <key>Hour</key>
            <integer>{hour}</integer>
            <key>Minute</key>
            <integer>{minute}</integer>
        </dict>""")
            
            # Add wake schedule entries if enabled
            if self.config['enable_wake'] and sched.get('wake_minutes_before', 0) > 0:
                wake_minute = minute - sched['wake_minutes_before']
                wake_hour = hour
                if wake_minute < 0:
                    wake_minute += 60
                    wake_hour -= 1
                    if wake_hour < 0:
                        wake_hour += 24
                
                schedule_entries.append(f"""        <dict>
            <key>Hour</key>
            <integer>{wake_hour}</integer>
            <key>Minute</key>
            <integer>{wake_minute}</integer>
        </dict>""")
        
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{daemon_label}</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>{script_path}</string>
    </array>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>StartCalendarInterval</key>
    <array>
{chr(10).join(schedule_entries)}
    </array>
    
    <key>StandardOutPath</key>
    <string>/var/log/claude-scheduler.out</string>
    <key>StandardErrorPath</key>
    <string>/var/log/claude-scheduler.err</string>
</dict>
</plist>"""
        
        return plist_content
    
    def register_macos(self):
        print("\n=== Registering macOS scheduler ===")
        
        scripts_dir = self.create_scripts_directory()
        self.create_logs_directory()
        platform_dir = self.script_dir / 'macos'
        
        username = self.config['platform_settings']['macos'].get('username', self.username)
        daemon_label = self.config['platform_settings']['macos']['daemon_label']
        
        schedules = []
        wake_schedules = []
        for sched in self.config['schedule']:
            time_parts = sched['time'].split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            schedules.append(f"{hour}:{minute:02d}")
            
            if self.config['enable_wake'] and sched.get('wake_minutes_before', 0) > 0:
                wake_minute = minute - sched['wake_minutes_before']
                wake_hour = hour
                if wake_minute < 0:
                    wake_minute += 60
                    wake_hour -= 1
                    if wake_hour < 0:
                        wake_hour += 24
                wake_schedules.append(f"{wake_hour}:{wake_minute:02d}")
        
        substitutions = {
            'USERNAME': username,
            'HOME_DIR': str(self.home_dir),
            'COMMAND': self.config['command'],
            'SCHEDULES': ','.join(schedules),
            'DAEMON_LABEL': daemon_label,
            'LOG_DIR': str(self.home_dir / 'logs'),
            'SCRIPT_PATH': str(scripts_dir / 'claude_daemon.sh'),
            'NTFY_TOPIC': self.config.get('notification_topic', '')
        }
        
        # Generate daemon script
        self.generate_from_template(
            platform_dir / 'daemon.sh.template',
            scripts_dir / 'claude_daemon.sh',
            substitutions
        )
        
        # Generate plist with dynamic schedule times
        plist_content = self.generate_macos_plist(
            daemon_label,
            str(scripts_dir / 'claude_daemon.sh')
        )
        
        if not self.dry_run:
            plist_path = scripts_dir / f'{daemon_label}.plist'
            with open(plist_path, 'w') as f:
                f.write(plist_content)
        else:
            if self.verbose:
                print(f"Would generate plist at: {scripts_dir / f'{daemon_label}.plist'}")
        
        if not self.dry_run:
            print("\nRegistering with launchd (requires sudo)...")
            plist_path = scripts_dir / f'{daemon_label}.plist'
            system_plist = Path(f'/Library/LaunchDaemons/{daemon_label}.plist')
            
            print("• Copying plist to LaunchDaemons...")
            subprocess.run(['sudo', 'cp', str(plist_path), str(system_plist)], check=True)
            subprocess.run(['sudo', 'chown', 'root:wheel', str(system_plist)], check=True)
            subprocess.run(['sudo', 'chmod', '644', str(system_plist)], check=True)
            
            print("• Loading into launchd...")
            subprocess.run(['sudo', 'launchctl', 'load', str(system_plist)], check=True)
            
            if self.config['enable_wake']:
                print("Setting up wake schedules...")
                for wake_time in wake_schedules:
                    hour, minute = wake_time.split(':')
                    tomorrow = subprocess.run(['date', '-v+1d', '+%m/%d/%y'], 
                                            capture_output=True, text=True).stdout.strip()
                    wake_cmd = f"{tomorrow} {hour}:{minute}:00"
                    subprocess.run(['sudo', 'pmset', 'schedule', 'wake', wake_cmd], check=True)
            
            print("macOS scheduler registered successfully!")
        else:
            print("Dry run - no actual registration performed")
    
    def generate_linux_timer(self, service_name):
        """Generate systemd timer with dynamic schedule times"""
        on_calendar_entries = []
        
        for sched in self.config['schedule']:
            time = sched['time']
            on_calendar_entries.append(f"OnCalendar=*-*-* {time}:00")
        
        timer_content = f"""[Unit]
Description=Claude Scheduler Timer
Requires={service_name}.service

[Timer]
{chr(10).join(on_calendar_entries)}
AccuracySec=1s
Persistent=true

[Install]
WantedBy=timers.target"""
        
        return timer_content
    
    def register_linux(self):
        print("\n=== Registering Linux scheduler ===")
        
        scripts_dir = self.create_scripts_directory()
        self.create_logs_directory()
        platform_dir = self.script_dir / 'linux'
        
        service_name = self.config['platform_settings']['linux']['service_name']
        
        schedules = []
        for sched in self.config['schedule']:
            schedules.append(sched['time'])
        
        substitutions = {
            'USERNAME': self.username,
            'HOME_DIR': str(self.home_dir),
            'COMMAND': self.config['command'],
            'SCHEDULES': ' '.join(schedules),
            'SERVICE_NAME': service_name,
            'LOG_DIR': str(self.home_dir / 'logs'),
            'SCRIPT_PATH': str(scripts_dir / 'claude_scheduler.sh'),
            'NTFY_TOPIC': self.config.get('notification_topic', '')
        }
        
        self.generate_from_template(
            platform_dir / 'scheduler.sh.template',
            scripts_dir / 'claude_scheduler.sh',
            substitutions
        )
        
        if self.linux_method == 'systemd':
            self.generate_from_template(
                platform_dir / 'claude-scheduler.service.template',
                scripts_dir / f'{service_name}.service',
                substitutions
            )
            
            # Generate timer with dynamic schedule times
            timer_content = self.generate_linux_timer(service_name)
            
            if not self.dry_run:
                timer_path = scripts_dir / f'{service_name}.timer'
                with open(timer_path, 'w') as f:
                    f.write(timer_content)
            else:
                if self.verbose:
                    print(f"Would generate timer at: {scripts_dir / f'{service_name}.timer'}")
            
            if not self.dry_run:
                print("\nRegistering with systemd (requires sudo)...")
                service_path = scripts_dir / f'{service_name}.service'
                timer_path = scripts_dir / f'{service_name}.timer'
                
                print("• Copying systemd service and timer files...")
                subprocess.run(['sudo', 'cp', str(service_path), 
                              f'/etc/systemd/system/{service_name}.service'], check=True)
                subprocess.run(['sudo', 'cp', str(timer_path), 
                              f'/etc/systemd/system/{service_name}.timer'], check=True)
                
                print("• Reloading systemd configuration...")
                subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
                
                print("• Enabling and starting timer...")
                subprocess.run(['sudo', 'systemctl', 'enable', f'{service_name}.timer'], check=True)
                subprocess.run(['sudo', 'systemctl', 'start', f'{service_name}.timer'], check=True)
                
                if self.config['enable_wake'] and self.config['platform_settings']['linux']['wake_method'] == 'rtcwake':
                    print("• Setting up wake schedules with rtcwake...")
                
                print("Linux systemd timer activated successfully!")
        else:
            if not self.dry_run:
                print("\nRegistering with cron...")
                cron_entry = ""
                for sched in self.config['schedule']:
                    hour, minute = sched['time'].split(':')
                    cron_entry += f"{minute} {hour} * * * {scripts_dir}/claude_scheduler.sh\n"
                
                print("• Reading existing crontab...")
                cron_process = subprocess.Popen(['crontab', '-l'], 
                                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                current_cron, _ = cron_process.communicate()
                
                print("• Adding scheduler entries...")
                new_cron = current_cron.decode() + cron_entry
                
                cron_process = subprocess.Popen(['crontab', '-'], 
                                               stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                cron_process.communicate(input=new_cron.encode())
                
                print("Linux cron scheduler registered successfully!")
        
        if self.dry_run:
            print("Dry run - no actual registration performed")
    
    def generate_windows_xml(self, task_name, username, script_path, enable_wake):
        """Generate Windows Task Scheduler XML with dynamic schedule times"""
        trigger_entries = []
        
        for sched in self.config['schedule']:
            time = sched['time']
            trigger_entries.append(f"""    <CalendarTrigger>
      <StartBoundary>2024-01-01T{time}:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>""")
        
        xml_content = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>2024-01-01T00:00:00</Date>
    <Author>{username}</Author>
    <Description>Claude Scheduler - Runs claude command at scheduled times</Description>
  </RegistrationInfo>
  <Triggers>
{chr(10).join(trigger_entries)}
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>{username}</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>{enable_wake}</WakeToRun>
    <ExecutionTimeLimit>PT1H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>powershell.exe</Command>
      <Arguments>-ExecutionPolicy Bypass -File "{script_path}"</Arguments>
    </Exec>
  </Actions>
</Task>"""
        
        return xml_content
    
    def register_windows(self):
        print("\n=== Registering Windows scheduler ===")
        
        scripts_dir = self.create_scripts_directory()
        platform_dir = self.script_dir / 'windows'
        
        task_name = self.config['platform_settings']['windows']['task_name']
        command = self.config['platform_settings']['windows']['command']
        
        substitutions = {
            'USERNAME': self.username,
            'HOME_DIR': str(self.home_dir),
            'COMMAND': command,
            'TASK_NAME': task_name,
            'LOG_DIR': str(self.home_dir / 'logs'),
            'SCRIPT_PATH': str(scripts_dir / 'claude_scheduler.ps1'),
            'ENABLE_WAKE': str(self.config['enable_wake']).lower(),
            'NTFY_TOPIC': self.config.get('notification_topic', '')
        }
        
        self.generate_from_template(
            platform_dir / 'scheduler.ps1.template',
            scripts_dir / 'claude_scheduler.ps1',
            substitutions
        )
        
        # Generate XML with dynamic schedule times
        xml_content = self.generate_windows_xml(
            task_name,
            self.username,
            str(scripts_dir / 'claude_scheduler.ps1'),
            str(self.config['enable_wake']).lower()
        )
        
        if not self.dry_run:
            xml_path = scripts_dir / f'{task_name}.xml'
            with open(xml_path, 'w', encoding='utf-16') as f:
                f.write(xml_content)
        else:
            if self.verbose:
                print(f"Would generate XML at: {scripts_dir / f'{task_name}.xml'}")
        
        if not self.dry_run:
            print("\nRegistering with Windows Task Scheduler...")
            xml_path = scripts_dir / f'{task_name}.xml'
            
            print(f"• Creating scheduled task '{task_name}'...")
            subprocess.run(['powershell', '-Command', 
                          f'Register-ScheduledTask -TaskName "{task_name}" -Xml (Get-Content "{xml_path}" | Out-String)'],
                          check=True)
            
            print("Windows Task Scheduler task created successfully!")
        else:
            print("Dry run - no actual registration performed")
    
    def save_config(self):
        """Save the updated config file with notification settings"""
        if not self.dry_run:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            if self.verbose:
                print(f"Configuration saved to {self.config_path}")
    
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
        
        if self.platform == 'macos':
            self.register_macos()
        elif self.platform == 'linux':
            self.register_linux()
        elif self.platform == 'windows':
            self.register_windows()
        
        print("\n" + "=" * 50)
        print("Setup complete!")
        print(f"Run 'python status.py' to check the scheduler status")
        print(f"Run 'python uninstall.py' to remove the scheduler")
        
        if self.notification_topic:
            print(f"\nNotifications enabled! Test with:")
            print(f"  curl -d 'Test notification' ntfy.sh/{self.notification_topic}")

def main():
    parser = argparse.ArgumentParser(description='Claude Scheduler Setup')
    parser.add_argument('--dry-run', action='store_true', help='Preview registration without making changes')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output')
    parser.add_argument('--config', default='config.json', help='Path to configuration file')
    parser.add_argument('--add-notifications', dest='notification_topic', 
                       help='Enable push notifications with specified ntfy.sh topic')
    parser.add_argument('--remove-notifications', action='store_true',
                       help='Remove push notifications from scheduler')
    
    args = parser.parse_args()
    
    setup = ClaudeSchedulerSetup(
        config_path=args.config,
        dry_run=args.dry_run,
        verbose=args.verbose,
        notification_topic=args.notification_topic,
        remove_notifications=args.remove_notifications
    )
    
    try:
        setup.run()
    except KeyboardInterrupt:
        print("\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()