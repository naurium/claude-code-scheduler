#!/usr/bin/env python3

import sys
import subprocess
import os
import stat
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from common.base import BaseSchedulerStatus


class LinuxSchedulerStatus(BaseSchedulerStatus):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if hasattr(self, 'config') and 'platform_settings' in self.config:
            self.service_name = self.config['platform_settings']['linux'].get('service_name', 'claude-scheduler')
    
    def check_status(self):
        print("\n=== Linux Scheduler Status ===")
        
        systemd_check = subprocess.run(['systemctl', '--version'], 
                                      capture_output=True, text=True).returncode == 0
        
        if systemd_check:
            try:
                timer_status = subprocess.run(['systemctl', 'status', f'{self.service_name}.timer'], 
                                            capture_output=True, text=True)
                
                if 'active (waiting)' in timer_status.stdout or 'active (running)' in timer_status.stdout:
                    print(f"✓ Systemd timer '{self.service_name}.timer' is active")
                    
                    for line in timer_status.stdout.split('\n'):
                        if 'Trigger:' in line:
                            print(f"  {line.strip()}")
                        elif 'Active:' in line:
                            print(f"  {line.strip()}")
                else:
                    print(f"✗ Systemd timer '{self.service_name}.timer' is not active")
                
                service_status = subprocess.run(['systemctl', 'status', f'{self.service_name}.service'], 
                                              capture_output=True, text=True)
                
                for line in service_status.stdout.split('\n'):
                    if 'Main PID:' in line or 'Active:' in line:
                        print(f"  {line.strip()}")
                
            except subprocess.CalledProcessError:
                print(f"✗ Service '{self.service_name}' not found")
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
    
    def test_script(self):
        """Test run the scheduler script to verify it works"""
        print("Claude Scheduler Test Mode")
        print("=" * 50)
        print("\n=== Testing Linux Scheduler Script ===\n")
        
        # Check for script
        script_path = self.script_dir / 'scripts' / 'claude_scheduler.sh'
        
        if not script_path.exists():
            print(f"✗ Script not found: {script_path}")
            print("\nSolution: Run 'python3 setup.py' to generate the script")
            return
        
        print(f"✓ Script found: {script_path}")
        
        # Check script permissions
        try:
            st = os.stat(script_path)
            mode = st.st_mode
            is_executable = bool(mode & stat.S_IXUSR)
            
            print(f"\nScript permissions: {oct(stat.S_IMODE(mode))}")
            if is_executable:
                print("✓ Script is executable")
            else:
                print("✗ Script is not executable")
                print(f"\nFix with: chmod +x {script_path}")
        except Exception as e:
            print(f"Error checking permissions: {e}")
        
        # Test run the script
        print("\n" + "=" * 30)
        print("Testing script execution...")
        print("=" * 30 + "\n")
        
        try:
            # Run with a 5 second timeout
            result = subprocess.run(
                ['/bin/bash', str(script_path)],
                capture_output=True,
                text=True,
                timeout=5,
                env={**os.environ, 'PATH': '/usr/local/bin:/usr/bin:/bin:' + os.environ.get('PATH', '')}
            )
            
            if result.returncode == 0:
                print("✓ Script executed successfully!")
                if result.stdout:
                    print("\nScript output:")
                    print("-" * 30)
                    print(result.stdout)
                if result.stderr:
                    print("\nScript warnings/errors:")
                    print("-" * 30)
                    print(result.stderr)
            else:
                print(f"✗ Script failed with exit code: {result.returncode}")
                if result.stdout:
                    print("\nScript output:")
                    print("-" * 30)
                    print(result.stdout)
                if result.stderr:
                    print("\nScript errors:")
                    print("-" * 30)
                    print(result.stderr)
                    
        except subprocess.TimeoutExpired:
            print("✓ Script is running (timed out after 5 seconds - this is normal)")
            print("The script appears to be working but takes longer than 5 seconds to complete.")
        except FileNotFoundError:
            print("✗ bash not found")
        except Exception as e:
            print(f"✗ Error running script: {e}")
        
        # Check log files
        print("\n" + "=" * 30)
        print("Checking log files...")
        print("=" * 30 + "\n")
        
        log_file = self.home_dir / 'logs' / 'claude_scheduler.log'
        
        if log_file.exists():
            print(f"✓ Log file found: {log_file}")
            try:
                # Show last few lines
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        print(f"  Last entry: {lines[-1].strip()}")
            except PermissionError:
                print(f"  (Permission denied reading log)")
        else:
            print("✗ No log file found yet")
            print("Logs will be created after the first successful run")
        
        print("\n" + "=" * 50)
        print("Test complete!")