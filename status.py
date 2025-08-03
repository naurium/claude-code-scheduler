#!/usr/bin/env python3

import sys
import platform
import argparse


def get_platform_status_class():
    """Factory function to get the appropriate platform-specific status class"""
    current_platform = platform.system().lower()
    
    if current_platform == 'darwin':
        current_platform = 'macos'
    
    if current_platform == 'macos':
        from macos.status import MacOSSchedulerStatus
        return MacOSSchedulerStatus
    elif current_platform == 'linux':
        from linux.status import LinuxSchedulerStatus
        return LinuxSchedulerStatus
    elif current_platform == 'windows':
        from windows.status import WindowsSchedulerStatus
        return WindowsSchedulerStatus
    else:
        print(f"Error: Unsupported platform {current_platform}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Claude Scheduler Status')
    parser.add_argument('--logs', action='store_true', 
                       help='Show recent log entries')
    parser.add_argument('--test', action='store_true',
                       help='Test run the scheduler script to verify it works')
    parser.add_argument('--config', default='config.json', 
                       help='Path to configuration file')
    
    args = parser.parse_args()
    
    # Get the appropriate platform-specific status class
    StatusClass = get_platform_status_class()
    
    # Create an instance with the provided arguments
    status_checker = StatusClass(
        config_path=args.config,
        show_logs=args.logs
    )
    
    try:
        if args.test:
            # Run test mode
            status_checker.test_script()
        else:
            # Normal status check
            status_checker.run()
    except KeyboardInterrupt:
        print("\nStatus check cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()