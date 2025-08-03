#!/usr/bin/env python3

import sys
import subprocess
import shutil
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from common.base import BaseSchedulerSetup


class LinuxSchedulerSetup(BaseSchedulerSetup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.linux_method = None
        if hasattr(self, 'config') and 'platform_settings' in self.config:
            self.service_name = self.config['platform_settings']['linux'].get('service_name', 'claude-scheduler')
    
    def check_prerequisites(self):
        print("Checking prerequisites...")
        
        # Check for claude CLI
        claude_check = shutil.which('claude')
        if not claude_check:
            print(f"Error: claude command not found. Please install Claude CLI first.")
            return False
        print("✓ Claude CLI found")
        
        # Check for systemd or fall back to cron
        systemd_check = subprocess.run(['systemctl', '--version'], 
                                      capture_output=True, text=True).returncode == 0
        if systemd_check:
            self.linux_method = 'systemd'
        else:
            self.linux_method = 'cron'
        print(f"Linux scheduling method: {self.linux_method}")
        
        print("Prerequisites check passed!")
        return True
    
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
    
    def register(self):
        print("\n=== Registering Linux scheduler ===")
        
        scripts_dir = self.create_scripts_directory()
        self.create_logs_directory()
        platform_dir = self.script_dir / 'linux'
        
        schedules = []
        for sched in self.config['schedule']:
            schedules.append(sched['time'])
        
        substitutions = {
            'USERNAME': self.username,
            'HOME_DIR': str(self.home_dir),
            'COMMAND': self.config['command'],
            'SCHEDULES': ' '.join(schedules),
            'SERVICE_NAME': self.service_name,
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
                scripts_dir / f'{self.service_name}.service',
                substitutions
            )
            
            # Generate timer with dynamic schedule times
            timer_content = self.generate_linux_timer(self.service_name)
            
            if not self.dry_run:
                timer_path = scripts_dir / f'{self.service_name}.timer'
                with open(timer_path, 'w') as f:
                    f.write(timer_content)
            else:
                if self.verbose:
                    print(f"Would generate timer at: {scripts_dir / f'{self.service_name}.timer'}")
            
            if not self.dry_run:
                print("\nRegistering with systemd (requires sudo)...")
                service_path = scripts_dir / f'{self.service_name}.service'
                timer_path = scripts_dir / f'{self.service_name}.timer'
                
                print("• Copying systemd service and timer files...")
                subprocess.run(['sudo', 'cp', str(service_path), 
                              f'/etc/systemd/system/{self.service_name}.service'], check=True)
                subprocess.run(['sudo', 'cp', str(timer_path), 
                              f'/etc/systemd/system/{self.service_name}.timer'], check=True)
                
                print("• Reloading systemd configuration...")
                subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
                
                print("• Enabling and starting timer...")
                subprocess.run(['sudo', 'systemctl', 'enable', f'{self.service_name}.timer'], check=True)
                subprocess.run(['sudo', 'systemctl', 'start', f'{self.service_name}.timer'], check=True)
                
                if self.config.get('enable_wake', False) and self.config['platform_settings']['linux'].get('wake_method') == 'rtcwake':
                    print("• Note: rtcwake must be configured manually (see SETUP.md)")
                
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