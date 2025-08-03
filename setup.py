#!/usr/bin/env python3

import sys
import platform
import argparse


def get_platform_setup_class():
    """Factory function to get the appropriate platform-specific setup class"""
    current_platform = platform.system().lower()
    
    if current_platform == 'darwin':
        current_platform = 'macos'
    
    if current_platform == 'macos':
        from macos.setup import MacOSSchedulerSetup
        return MacOSSchedulerSetup
    elif current_platform == 'linux':
        from linux.setup import LinuxSchedulerSetup
        return LinuxSchedulerSetup
    elif current_platform == 'windows':
        from windows.setup import WindowsSchedulerSetup
        return WindowsSchedulerSetup
    else:
        print(f"Error: Unsupported platform {current_platform}")
        sys.exit(1)

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
    
    # Get the appropriate platform-specific setup class
    SetupClass = get_platform_setup_class()
    
    # Create an instance with the provided arguments
    setup = SetupClass(
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