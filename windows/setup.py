#!/usr/bin/env python3

import sys
import subprocess
import shutil
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from common.base import BaseSchedulerSetup


class WindowsSchedulerSetup(BaseSchedulerSetup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if hasattr(self, 'config') and 'platform_settings' in self.config:
            self.task_name = self.config['platform_settings']['windows'].get('task_name', 'ClaudeScheduler')
            self.command = self.config['platform_settings']['windows'].get('command', self.config.get('command', 'wsl claude'))
    
    def check_prerequisites(self):
        print("Checking prerequisites...")
        
        # Windows requires WSL
        wsl_check = shutil.which('wsl')
        if not wsl_check:
            print("Error: WSL (Windows Subsystem for Linux) not found.")
            print("Please install WSL and ensure claude is installed within WSL.")
            print("See: https://docs.microsoft.com/en-us/windows/wsl/install")
            return False
        print("✓ WSL found")
        print("Note: Claude must be installed and configured inside WSL")
        
        print("Prerequisites check passed!")
        return True
    
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
    
    def register(self):
        print("\n=== Registering Windows scheduler ===")
        
        scripts_dir = self.create_scripts_directory()
        platform_dir = self.script_dir / 'windows'
        
        substitutions = {
            'USERNAME': self.username,
            'HOME_DIR': str(self.home_dir),
            'COMMAND': self.command,
            'TASK_NAME': self.task_name,
            'LOG_DIR': str(self.home_dir / 'logs'),
            'SCRIPT_PATH': str(scripts_dir / 'claude_scheduler.ps1'),
            'ENABLE_WAKE': str(self.config.get('enable_wake', False)).lower(),
            'NTFY_TOPIC': self.config.get('notification_topic', '')
        }
        
        self.generate_from_template(
            platform_dir / 'scheduler.ps1.template',
            scripts_dir / 'claude_scheduler.ps1',
            substitutions
        )
        
        # Generate XML with dynamic schedule times
        xml_content = self.generate_windows_xml(
            self.task_name,
            self.username,
            str(scripts_dir / 'claude_scheduler.ps1'),
            str(self.config.get('enable_wake', False)).lower()
        )
        
        if not self.dry_run:
            xml_path = scripts_dir / f'{self.task_name}.xml'
            with open(xml_path, 'w', encoding='utf-16') as f:
                f.write(xml_content)
        else:
            if self.verbose:
                print(f"Would generate XML at: {scripts_dir / f'{self.task_name}.xml'}")
        
        if not self.dry_run:
            print("\nRegistering with Windows Task Scheduler...")
            xml_path = scripts_dir / f'{self.task_name}.xml'
            
            print(f"• Creating scheduled task '{self.task_name}'...")
            subprocess.run(['powershell', '-Command', 
                          f'Register-ScheduledTask -TaskName "{self.task_name}" -Xml (Get-Content "{xml_path}" | Out-String)'],
                          check=True)
            
            print("Windows Task Scheduler task created successfully!")
        else:
            print("Dry run - no actual registration performed")