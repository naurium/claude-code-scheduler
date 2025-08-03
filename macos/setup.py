#!/usr/bin/env python3

import sys
import subprocess
import shutil
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from common.base import BaseSchedulerSetup


class MacOSSchedulerSetup(BaseSchedulerSetup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if hasattr(self, 'config') and 'platform_settings' in self.config:
            self.daemon_label = self.config['platform_settings']['macos'].get('daemon_label', 'ClaudeScheduler')
            self.username = self.config['platform_settings']['macos'].get('username', self.username)
    
    def check_prerequisites(self):
        print("Checking prerequisites...")
        
        # Check for claude CLI
        claude_check = shutil.which('claude')
        if not claude_check:
            print(f"Error: claude command not found. Please install Claude CLI first.")
            return False
        print("✓ Claude CLI found")
        
        print("Prerequisites check passed!")
        return True
    
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
            
            # Wake schedules are handled by pmset, not in the plist
        
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
    <false/>
    
    <key>StartCalendarInterval</key>
    <array>
{chr(10).join(schedule_entries)}
    </array>
    
    <key>StandardOutPath</key>
    <string>{str(Path.home() / 'Library' / 'Logs' / 'ClaudeScheduler' / 'scheduler.out')}</string>
    <key>StandardErrorPath</key>
    <string>{str(Path.home() / 'Library' / 'Logs' / 'ClaudeScheduler' / 'scheduler.err')}</string>
</dict>
</plist>"""
        
        return plist_content
    
    def register(self):
        print("\n=== Registering macOS scheduler ===")
        
        # Use standard macOS directories
        app_support_dir = Path.home() / 'Library' / 'Application Support' / 'ClaudeScheduler'
        log_dir = Path.home() / 'Library' / 'Logs' / 'ClaudeScheduler'
        
        # Create directories
        if not self.dry_run:
            app_support_dir.mkdir(parents=True, exist_ok=True)
            log_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created app directory: {app_support_dir}")
            print(f"Created log directory: {log_dir}")
        
        scripts_dir = app_support_dir
        platform_dir = self.script_dir / 'macos'
        
        wake_schedules = []
        schedule_times_minutes = []
        wake_minutes = 5  # Default wake minutes before
        
        for sched in self.config['schedule']:
            time_parts = sched['time'].split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            
            # Calculate minutes from midnight for schedule times
            schedule_times_minutes.append(str(hour * 60 + minute))
            
            if self.config.get('enable_wake', False) and sched.get('wake_minutes_before', 0) > 0:
                wake_minutes = sched.get('wake_minutes_before', 5)
                wake_minute = minute - wake_minutes
                wake_hour = hour
                if wake_minute < 0:
                    wake_minute += 60
                    wake_hour -= 1
                    if wake_hour < 0:
                        wake_hour += 24
                wake_schedules.append(f"{wake_hour:02d}:{wake_minute:02d}")
        
        # Build schedule times array string for bash
        schedule_times_str = ' '.join(f'"{t}"' for t in schedule_times_minutes)
        
        substitutions = {
            'USERNAME': self.username,
            'HOME_DIR': str(self.home_dir),
            'COMMAND': self.config['command'],
            'DAEMON_LABEL': self.daemon_label,
            'LOG_DIR': str(log_dir),
            'SCRIPT_PATH': str(scripts_dir / 'claude_daemon.sh'),
            'NTFY_TOPIC': self.config.get('notification_topic', ''),
            'ENABLE_WAKE': 'true' if self.config.get('enable_wake', False) else 'false',
            'WAKE_MINUTES': str(wake_minutes),
            'SCHEDULE_TIMES': schedule_times_str
        }
        
        # Generate daemon script
        self.generate_from_template(
            platform_dir / 'daemon.sh.template',
            scripts_dir / 'claude_daemon.sh',
            substitutions
        )
        
        # Generate plist with dynamic schedule times
        plist_content = self.generate_macos_plist(
            self.daemon_label,
            str(scripts_dir / 'claude_daemon.sh')
        )
        
        if not self.dry_run:
            plist_path = scripts_dir / f'{self.daemon_label}.plist'
            with open(plist_path, 'w') as f:
                f.write(plist_content)
        else:
            if self.verbose:
                print(f"Would generate plist at: {scripts_dir / f'{self.daemon_label}.plist'}")
        
        if not self.dry_run:
            print("\nRegistering with launchd (requires sudo)...")
            plist_path = scripts_dir / f'{self.daemon_label}.plist'
            system_plist = Path(f'/Library/LaunchDaemons/{self.daemon_label}.plist')
            
            print("• Copying plist to LaunchDaemons...")
            subprocess.run(['sudo', 'cp', str(plist_path), str(system_plist)], check=True)
            subprocess.run(['sudo', 'chown', 'root:wheel', str(system_plist)], check=True)
            subprocess.run(['sudo', 'chmod', '644', str(system_plist)], check=True)
            
            print("• Loading into launchd...")
            subprocess.run(['sudo', 'launchctl', 'load', str(system_plist)], check=True)
            
            if self.config.get('enable_wake', False):
                print("Setting up wake schedules...")
                # Clear any existing wake schedules
                subprocess.run(['sudo', 'pmset', 'schedule', 'cancelall'], 
                             capture_output=True, text=True)
                
                # Get current time
                from datetime import datetime
                now = datetime.now()
                current_minutes = now.hour * 60 + now.minute
                
                # Set wake times for TODAY (remaining sessions)
                today = subprocess.run(['date', '+%m/%d/%y'], 
                                     capture_output=True, text=True).stdout.strip()
                wake_count = 0
                
                for sched in self.config['schedule']:
                    time_parts = sched['time'].split(':')
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    sched_minutes = hour * 60 + minute
                    
                    if sched_minutes > current_minutes:
                        wake_offset = sched.get('wake_minutes_before', 5)
                        wake_minute = minute - wake_offset
                        wake_hour = hour
                        if wake_minute < 0:
                            wake_minute += 60
                            wake_hour -= 1
                        wake_cmd = f"{today} {wake_hour:02d}:{wake_minute:02d}:00"
                        subprocess.run(['sudo', 'pmset', 'schedule', 'wake', wake_cmd], check=True)
                        wake_count += 1
                        print(f"  • Set wake for today at {wake_hour:02d}:{wake_minute:02d}")
                
                # Set wake times for TOMORROW (all sessions)
                tomorrow = subprocess.run(['date', '-v+1d', '+%m/%d/%y'], 
                                        capture_output=True, text=True).stdout.strip()
                
                for sched in self.config['schedule']:
                    time_parts = sched['time'].split(':')
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    wake_offset = sched.get('wake_minutes_before', 5)
                    wake_minute = minute - wake_offset
                    wake_hour = hour
                    if wake_minute < 0:
                        wake_minute += 60
                        wake_hour -= 1
                    wake_cmd = f"{tomorrow} {wake_hour:02d}:{wake_minute:02d}:00"
                    subprocess.run(['sudo', 'pmset', 'schedule', 'wake', wake_cmd], check=True)
                    print(f"  • Set wake for tomorrow at {wake_hour:02d}:{wake_minute:02d}")
            
            print("macOS scheduler registered successfully!")
        else:
            print("Dry run - no actual registration performed")