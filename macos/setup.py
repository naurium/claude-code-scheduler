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
    
    def generate_wake_daemon_plist(self, daemon_label, script_path):
        """Generate LaunchDaemon plist for wake scheduling only"""
        schedule_entries = []
        
        # Add schedule entries for wake refresh times (same as Claude execution times)
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
        
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{daemon_label}.Wake</string>
    
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
    <string>{str(Path.home() / 'Library' / 'Logs' / 'ClaudeScheduler' / 'wake_daemon.out')}</string>
    <key>StandardErrorPath</key>
    <string>{str(Path.home() / 'Library' / 'Logs' / 'ClaudeScheduler' / 'wake_daemon.err')}</string>
</dict>
</plist>"""
        
        return plist_content
    
    def generate_agent_plist(self, agent_label, script_path):
        """Generate LaunchAgent plist for Claude execution"""
        schedule_entries = []
        
        # Add schedule entries for Claude execution times
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
        
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{agent_label}.Agent</string>
    
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
    <string>{str(Path.home() / 'Library' / 'Logs' / 'ClaudeScheduler' / 'agent.out')}</string>
    <key>StandardErrorPath</key>
    <string>{str(Path.home() / 'Library' / 'Logs' / 'ClaudeScheduler' / 'agent.err')}</string>
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
            'WORKING_DIR_VALUE': self.config.get('working_directory', '~'),
            'DAEMON_LABEL': self.daemon_label,
            'LOG_DIR': str(log_dir),
            'SCRIPT_PATH': str(scripts_dir / 'claude_daemon.sh'),
            'NTFY_TOPIC': self.config.get('notification_topic', ''),
            'ENABLE_WAKE': 'true' if self.config.get('enable_wake', False) else 'false',
            'WAKE_MINUTES': str(wake_minutes),
            'SCHEDULE_TIMES': schedule_times_str
        }
        
        # Generate wake daemon script (for pmset only)
        self.generate_from_template(
            platform_dir / 'wake_daemon.sh.template',
            scripts_dir / 'wake_daemon.sh',
            substitutions
        )
        
        # Generate agent script (for Claude execution)
        self.generate_from_template(
            platform_dir / 'agent.sh.template',
            scripts_dir / 'claude_agent.sh',
            substitutions
        )
        
        # Generate wake daemon plist
        wake_daemon_plist_content = self.generate_wake_daemon_plist(
            self.daemon_label,
            str(scripts_dir / 'wake_daemon.sh')
        )
        
        # Generate agent plist
        agent_plist_content = self.generate_agent_plist(
            self.daemon_label,
            str(scripts_dir / 'claude_agent.sh')
        )
        
        if not self.dry_run:
            # Write wake daemon plist
            wake_daemon_plist_path = scripts_dir / f'{self.daemon_label}.Wake.plist'
            with open(wake_daemon_plist_path, 'w') as f:
                f.write(wake_daemon_plist_content)
            
            # Write agent plist
            agent_plist_path = scripts_dir / f'{self.daemon_label}.Agent.plist'
            with open(agent_plist_path, 'w') as f:
                f.write(agent_plist_content)
        else:
            if self.verbose:
                print(f"Would generate wake daemon plist at: {scripts_dir / f'{self.daemon_label}.Wake.plist'}")
                print(f"Would generate agent plist at: {scripts_dir / f'{self.daemon_label}.Agent.plist'}")
        
        if not self.dry_run:
            print("\nRegistering schedulers...")
            
            # 1. Install Wake Daemon (system-level, requires sudo)
            if self.config.get('enable_wake', False):
                print("\n• Installing wake daemon (requires sudo)...")
                wake_daemon_plist_path = scripts_dir / f'{self.daemon_label}.Wake.plist'
                system_wake_plist = Path(f'/Library/LaunchDaemons/{self.daemon_label}.Wake.plist')
                
                print("  - Copying wake daemon plist to LaunchDaemons...")
                subprocess.run(['sudo', 'cp', str(wake_daemon_plist_path), str(system_wake_plist)], check=True)
                subprocess.run(['sudo', 'chown', 'root:wheel', str(system_wake_plist)], check=True)
                subprocess.run(['sudo', 'chmod', '644', str(system_wake_plist)], check=True)
                
                print("  - Loading wake daemon into launchd...")
                subprocess.run(['sudo', 'launchctl', 'load', str(system_wake_plist)], check=True)
            
            # 2. Install Claude Agent (user-level, no sudo needed)
            print("\n• Installing Claude agent...")
            agent_plist_path = scripts_dir / f'{self.daemon_label}.Agent.plist'
            user_agents_dir = Path.home() / 'Library' / 'LaunchAgents'
            user_agents_dir.mkdir(parents=True, exist_ok=True)
            user_agent_plist = user_agents_dir / f'{self.daemon_label}.Agent.plist'
            
            print("  - Copying agent plist to LaunchAgents...")
            shutil.copy(str(agent_plist_path), str(user_agent_plist))
            
            print("  - Loading agent into launchd...")
            subprocess.run(['launchctl', 'load', str(user_agent_plist)], check=True)
            
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
            
            print("\nmacOS schedulers registered successfully!")
            if self.config.get('enable_wake', False):
                print("  ✓ Wake daemon installed (handles system wake scheduling)")
            print("  ✓ Claude agent installed (executes Claude with user permissions)")
        else:
            print("Dry run - no actual registration performed")