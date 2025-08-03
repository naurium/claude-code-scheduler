# Claude Code Scheduler - Detailed Setup Guide

## Requirements

- Python 3.6 or higher
- Claude CLI installed and working:
  - **macOS/Linux**: Claude CLI installed normally in PATH
  - **Windows**: WSL (Windows Subsystem for Linux) with Claude installed inside WSL
- Administrator/sudo privileges for scheduler registration

## Setup

### 1. Clone the repository
```bash
git clone https://github.com/naurium/claude-code-scheduler.git
cd claude-code-scheduler
```

### 2. Configure (Choose Your Mode)

The scheduler supports two configuration modes (it will create config.json automatically on first run):

#### Simple Mode (Default - Recommended for Most Users)
After running setup.py, edit `config.json` with just a start time:
```json
{
  "start_time": "06:15",        // Your preferred first session time (24-hour format)
  "wake_minutes_before": 5,     // Wake computer 5 min early  
  "command": "claude -p \"hello\"",
  "enable_wake": true
}
```

The scheduler automatically creates 4 sessions at 5-hour intervals:
- Start at 6:15 AM → Sessions at 6:15, 11:15, 16:15, 21:15
- Start at 9:00 AM → Sessions at 9:00, 14:00, 19:00, 00:00
- Start at 10:00 PM → Sessions at 22:00, 03:00, 08:00, 13:00

**Perfect for:** Regular schedules, work-life balance, simplicity

#### Manual Mode (Advanced - Full Control)
For custom schedules, use the `schedule` array instead:
```json
{
  "schedule": [
    {"time": "07:00", "wake_minutes_before": 5},
    {"time": "12:30", "wake_minutes_before": 5},
    {"time": "18:00", "wake_minutes_before": 10},
    {"time": "23:45", "wake_minutes_before": 3}
  ],
  "command": "claude -p \"hello\"",
  "enable_wake": true
}
```

**Perfect for:** Irregular schedules, specific timing needs, different wake times per session

**To use manual mode:** 
1. Copy `config.manual.example.json` to `config.json`
2. Edit the times to match your needs
3. Run `python3 setup.py`

**Important:** Do NOT use both `start_time` and `schedule` in the same config!

### 3. Register Scheduler
```bash
python3 setup.py
```

The setup will:
- Detect your operating system
- Check prerequisites
- Register the appropriate scheduler with your system
- Set up wake times (if supported)

### 4. Check Status
```bash
python3 status.py
```

View status with recent logs:
```bash
python3 status.py --logs
```

Test the scheduler script to diagnose issues:
```bash
python3 status.py --test
```
The `--test` flag will:
- Check if scripts exist and have proper permissions
- Attempt to run the scheduler script
- Show clear error messages if there are issues
- Help identify security restrictions (like macOS Documents folder blocking)

### 5. Remove
```bash
python3 uninstall.py
```

Remove with logs:
```bash
python3 uninstall.py --remove-logs
```

## Platform-Specific Information

### macOS
- Uses LaunchDaemons for scheduling
- Supports wake from sleep via `pmset`
- Requires sudo for registration
- Logs to `~/Library/Logs/ClaudeScheduler/`
- Scripts installed to `~/Library/Application Support/ClaudeScheduler/`

### Linux
- Uses systemd timers (modern distros) or cron (older systems)
- Wake from sleep requires manual `rtcwake` configuration (see Troubleshooting section)
- Requires sudo for systemd installation
- Logs to `~/logs/claude_scheduler.log`

### Windows
- Uses Task Scheduler
- **Requires WSL (Windows Subsystem for Linux)**
- Claude must be installed and configured inside WSL
- Runs `wsl claude` command through PowerShell
- Supports wake from sleep (if enabled in power settings)
- May require administrator privileges
- Logs to `%USERPROFILE%\logs\claude_scheduler.log`

**Windows Setup Prerequisites:**
1. Install WSL: `wsl --install` (in admin PowerShell)
2. Install Claude inside WSL environment
3. Test that `wsl claude -p "hello"` works from PowerShell

## Advanced Configuration

### Platform Settings
You can customize platform-specific settings in config.json:
```json
"platform_settings": {
  "windows": {
    "task_name": "ClaudeScheduler",
    "command": "claude.exe -p \"hello\""
  },
  "linux": {
    "service_name": "claude-scheduler",
    "wake_method": "rtcwake"  // or "none"
  },
  "macos": {
    "daemon_label": "ClaudeScheduler",
    "username": "auto"  // or specify username
  }
}
```

## Advanced Usage

### Dry Run
Preview what will be registered without making changes:
```bash
python3 setup.py --dry-run
```

### Verbose Mode
See detailed registration output:
```bash
python3 setup.py --verbose
```

### Custom Config
Use a different configuration file:
```bash
python3 setup.py --config my-config.json
```

### Push Notifications
Get notified when Claude runs or if something breaks:
```bash
python3 setup.py --add-notifications YOUR_TOPIC_NAME
```

This adds push notifications to your phone/desktop using the free ntfy.sh service. 
See [Push Notifications Setup](NOTIFICATIONS.md) for the complete guide.

## Troubleshooting

### Claude command not found

If the scheduler can't find claude, first locate it:

```bash
# macOS/Linux
which claude

# Windows (in WSL)
wsl which claude
```

Then update `config.json` with the full path:
```json
{
  "command": "/home/youruser/.local/bin/claude -p \"hello\""
}
```

The scheduler automatically searches these common directories:
- `~/.local/bin` (pip/pipx installations)
- `~/.npm-global/bin` (npm global)
- `~/.yarn/bin` (yarn global)
- `/usr/local/bin` (system-wide)
- `/opt/homebrew/bin` (macOS Homebrew)

If Claude is installed elsewhere, you must use the full path.

### Permission denied
The installer requires administrator/sudo privileges. On Unix systems, you'll be prompted for your password.

### macOS "Operation not permitted" error
If you see this error when the scheduler tries to run:
- The script is likely in a protected folder (Documents, Desktop, Downloads)
- Run `python3 setup.py` to reinstall - scripts will be copied to `~/Library/Application Support/ClaudeScheduler/`
- This location has no security restrictions
- Use `python3 status.py --test` to verify the fix

### Wake not working

**macOS:**
- Mac must be plugged in (for laptops)
- Check wake schedule: `pmset -g sched`

**Linux:**
- rtcwake must be configured manually (not automatic like macOS)
- Verify rtcwake support: `sudo rtcwake -m show`
- May require BIOS/UEFI wake timer support

To manually set a wake timer on Linux:
```bash
# Wake at 6:10 AM tomorrow (5 minutes before 6:15 session)
sudo rtcwake -m no -t $(date +%s -d "tomorrow 06:10")

# Or set a recurring wake with cron (add to root's crontab)
sudo crontab -e
# Add this line to wake at 6:10 AM daily:
10 6 * * * /usr/sbin/rtcwake -m no -t $(date +%s -d "tomorrow 06:10")
```

Note: rtcwake only sets one wake time. For multiple daily wakes, you'd need to set the next wake after each session runs.

**Windows:**
- Enable wake timers in Power Options
- Check task properties in Task Scheduler

### Checking logs

**macOS:**
```bash
tail -f ~/Library/Logs/ClaudeScheduler/scheduler.log
# Or check all logs:
ls -la ~/Library/Logs/ClaudeScheduler/
```

**Linux:**
```bash
tail -f ~/logs/claude_scheduler.log
```

**Windows:**
```powershell
Get-Content "$env:USERPROFILE\logs\claude_scheduler.log" -Tail 20 -Wait
```

## Manual Testing

Test the scheduler script directly:

**macOS:**
```bash
python3 status.py --test
# Or run directly if installed:
~/Library/Application\ Support/ClaudeScheduler/claude_daemon.sh
```

**Linux:**
```bash
./scripts/claude_scheduler.sh
```

**Windows:**
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\claude_scheduler.ps1
```