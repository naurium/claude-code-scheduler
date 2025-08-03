#!/usr/bin/env python3

import sys
import platform
import argparse


def get_platform_uninstall_class():
    """Factory function to get the appropriate platform-specific uninstall class"""
    current_platform = platform.system().lower()
    
    if current_platform == 'darwin':
        current_platform = 'macos'
    
    if current_platform == 'macos':
        from macos.uninstall import MacOSSchedulerUninstall
        return MacOSSchedulerUninstall
    elif current_platform == 'linux':
        from linux.uninstall import LinuxSchedulerUninstall
        return LinuxSchedulerUninstall
    elif current_platform == 'windows':
        from windows.uninstall import WindowsSchedulerUninstall
        return WindowsSchedulerUninstall
    else:
        print(f"Error: Unsupported platform {current_platform}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Claude Scheduler Uninstaller')
    parser.add_argument('--remove-logs', action='store_true', 
                       help='Also remove log files')
    parser.add_argument('--config', default='config.json', 
                       help='Path to configuration file')
    
    args = parser.parse_args()
    
    # Get the appropriate platform-specific uninstall class
    UninstallClass = get_platform_uninstall_class()
    
    # Create an instance with the provided arguments
    uninstaller = UninstallClass(
        config_path=args.config,
        remove_logs=args.remove_logs
    )
    
    try:
        uninstaller.run()
    except KeyboardInterrupt:
        print("\nUninstallation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()