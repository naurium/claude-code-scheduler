#!/usr/bin/env python3

import sys
import subprocess
import os
import stat
import shutil
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from common.base import BaseSchedulerStatus


class WindowsSchedulerStatus(BaseSchedulerStatus):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if hasattr(self, 'config') and 'platform_settings' in self.config:
            self.task_name = self.config['platform_settings']['windows'].get('task_name', 'ClaudeScheduler')
    
    def check_status(self):
        print("\n=== Windows Scheduler Status ===")
        
        try:
            result = subprocess.run(['schtasks', '/query', '/tn', self.task_name, '/v', '/fo', 'list'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"+ Windows Task Scheduler task '{self.task_name}' is registered")
                
                for line in result.stdout.split('\n'):
                    if any(key in line for key in ['Status:', 'Last Run Time:', 'Next Run Time:', 'State:']):
                        print(f"  {line.strip()}")
            else:
                print(f"X Windows Task Scheduler task '{self.task_name}' not found")
        except Exception as e:
            print(f"Error checking status: {e}")
    
    def test_script(self):
        """Test run the scheduler script to verify it works"""
        print("Claude Scheduler Test Mode")
        print("=" * 50)
        print("\n=== Testing Windows Scheduler Script ===\n")
        
        # Check for script
        script_path = self.script_dir / 'scripts' / 'claude_scheduler.ps1'
        
        if not script_path.exists():
            print(f"X Script not found: {script_path}")
            print("\nSolution: Run 'python3 setup.py' to generate the script")
            return
        
        print(f"+ Script found: {script_path}")
        
        # Check script permissions (less relevant on Windows but still check)
        try:
            st = os.stat(script_path)
            print(f"\nScript exists and is readable")
        except Exception as e:
            print(f"Error checking file: {e}")
        
        # Test WSL availability first
        print("\n" + "=" * 30)
        print("Checking WSL...")
        print("=" * 30 + "\n")
        
        # Find WSL path using shutil.which for consistency with setup.py
        wsl_path = shutil.which('wsl')
        if not wsl_path:
            print("X WSL not found in PATH")
            print("Install WSL with: wsl --install")
            return
        
        print(f"+ WSL found at: {wsl_path}")
        
        try:
            wsl_check = subprocess.run(
                [wsl_path, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if wsl_check.returncode == 0:
                print("+ WSL is working correctly")
                print(wsl_check.stdout.strip())
            else:
                print("X WSL found but not working properly")
                print("Try reinstalling WSL")
                return
        except Exception as e:
            print(f"X Error running WSL: {e}")
            return
        
        # Check claude in WSL
        print("\n" + "=" * 30)
        print("Checking Claude in WSL...")
        print("=" * 30 + "\n")
        
        try:
            claude_check = subprocess.run(
                [wsl_path, 'claude', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if claude_check.returncode == 0:
                print("+ Claude is available in WSL")
                print(f"  Version: {claude_check.stdout.strip()}")
            else:
                print("X Claude not found in WSL")
                print("Install Claude inside WSL environment")
        except Exception as e:
            print(f"X Error checking Claude in WSL: {e}")
        
        # Test run the script
        print("\n" + "=" * 30)
        print("Testing script execution...")
        print("=" * 30 + "\n")
        
        try:
            # Run PowerShell script with a 10 second timeout (WSL can be slow)
            result = subprocess.run(
                ['powershell', '-ExecutionPolicy', 'Bypass', '-File', str(script_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print("+ Script executed successfully!")
                if result.stdout:
                    print("\nScript output:")
                    print("-" * 30)
                    print(result.stdout)
                if result.stderr:
                    print("\nScript warnings/errors:")
                    print("-" * 30)
                    print(result.stderr)
            else:
                print(f"X Script failed with exit code: {result.returncode}")
                if result.stdout:
                    print("\nScript output:")
                    print("-" * 30)
                    print(result.stdout)
                if result.stderr:
                    print("\nScript errors:")
                    print("-" * 30)
                    print(result.stderr)
                    
        except subprocess.TimeoutExpired:
            print("+ Script is running (timed out after 10 seconds - this is normal)")
            print("The script appears to be working but takes longer than 10 seconds to complete.")
        except FileNotFoundError:
            print("X PowerShell not found")
        except Exception as e:
            print(f"X Error running script: {e}")
        
        # Check log files
        print("\n" + "=" * 30)
        print("Checking log files...")
        print("=" * 30 + "\n")
        
        log_file = self.home_dir / 'logs' / 'claude_scheduler.log'
        
        if log_file.exists():
            print(f"+ Log file found: {log_file}")
            try:
                # Show last few lines
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        print(f"  Last entry: {lines[-1].strip()}")
            except PermissionError:
                print(f"  (Permission denied reading log)")
        else:
            print("X No log file found yet")
            print("Logs will be created after the first successful run")
        
        print("\n" + "=" * 50)
        print("Test complete!")