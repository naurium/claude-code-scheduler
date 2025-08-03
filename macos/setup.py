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
            self.daemon_label = self.config['platform_settings']['macos'].get('daemon_label', 'com.claude.scheduler')
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
            
            # Add wake schedule entries if enabled
            if self.config.get('enable_wake', False) and sched.get('wake_minutes_before', 0) > 0:
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
    
    def register(self):
        print("\n=== Registering macOS scheduler ===")
        
        scripts_dir = self.create_scripts_directory()
        self.create_logs_directory()
        platform_dir = self.script_dir / 'macos'
        
        schedules = []
        wake_schedules = []
        for sched in self.config['schedule']:
            time_parts = sched['time'].split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            schedules.append(f"{hour}:{minute:02d}")
            
            if self.config.get('enable_wake', False) and sched.get('wake_minutes_before', 0) > 0:
                wake_minute = minute - sched['wake_minutes_before']
                wake_hour = hour
                if wake_minute < 0:
                    wake_minute += 60
                    wake_hour -= 1
                    if wake_hour < 0:
                        wake_hour += 24
                wake_schedules.append(f"{wake_hour}:{wake_minute:02d}")
        
        substitutions = {
            'USERNAME': self.username,
            'HOME_DIR': str(self.home_dir),
            'COMMAND': self.config['command'],
            'SCHEDULES': ','.join(schedules),
            'DAEMON_LABEL': self.daemon_label,
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
                for wake_time in wake_schedules:
                    hour, minute = wake_time.split(':')
                    tomorrow = subprocess.run(['date', '-v+1d', '+%m/%d/%y'], 
                                            capture_output=True, text=True).stdout.strip()
                    wake_cmd = f"{tomorrow} {hour}:{minute}:00"
                    subprocess.run(['sudo', 'pmset', 'schedule', 'wake', wake_cmd], check=True)
            
            print("macOS scheduler registered successfully!")
        else:
            print("Dry run - no actual registration performed")