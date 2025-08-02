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

The scheduler supports two configuration modes:

#### Simple Mode (Default - Recommended for Most Users)
Edit `config.json` with just a start time:
```json
{
  "start_time": "06:15",        // Your preferred first session time
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
- Logs to `~/logs/claude_scheduler.log`

### Linux
- Uses systemd timers (modern distros) or cron (older systems)
- Wake from sleep via `rtcwake` (if available)
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

## Configuration Options

### Mode Selection
The scheduler supports two modes - choose ONE:

#### Simple Mode Configuration
Use `start_time` for automatic 5-hour intervals:
```json
{
  "start_time": "HH:MM",          // 24-hour format for first session
  "wake_minutes_before": 5,       // Minutes to wake before each task
  "command": "claude -p \"hello\"",  // Command to run
  "enable_wake": true              // Enable wake from sleep
}
```

#### Manual Mode Configuration  
Use `schedule` array for custom times:
```json
{
  "schedule": [                   // Array of custom session times
    {"time": "HH:MM", "wake_minutes_before": N},
    {"time": "HH:MM", "wake_minutes_before": N}
  ],
  "command": "claude -p \"hello\"",  // Command to run
  "enable_wake": true              // Enable wake from sleep
}
```

**Important:** Do NOT use both `start_time` and `schedule` in the same config!

### Platform Settings
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
    "daemon_label": "com.claude.scheduler",
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

### Claude not found

**macOS:**
```bash
which claude
```
If not found, install Claude CLI and ensure it's in PATH.

**Linux:**
```bash
which claude
```
If claude is installed but not found by the scheduler:

1. **Option 1: Use full path in config.json**
   ```bash
   # Find claude's location
   which claude
   # Example output: /home/youruser/.local/bin/claude
   ```
   Then update `config.json`:
   ```json
   {
     "command": "/home/youruser/.local/bin/claude -p \"hello\""
   }
   ```

2. **Option 2: Claude is in non-standard location**
   - The scheduler looks in: `~/.local/bin`, `~/.npm-global/bin`, `~/.yarn/bin`, `/usr/local/bin`, `/usr/bin`
   - If Claude is elsewhere, use the full path (Option 1)

**Windows:**
```powershell
# Test WSL is installed
wsl --version

# Test claude works in WSL
wsl claude --version
```
If WSL not found, install it: `wsl --install`
If claude not found in WSL, install it inside WSL environment.

### Permission denied
The installer requires administrator/sudo privileges. On Unix systems, you'll be prompted for your password.

### Wake not working

**macOS:**
- Mac must be plugged in (for laptops)
- Check wake schedule: `pmset -g sched`

**Linux:**
- Verify rtcwake support: `sudo rtcwake -m show`
- May require BIOS/UEFI wake timer support

**Windows:**
- Enable wake timers in Power Options
- Check task properties in Task Scheduler

### Checking logs

**macOS/Linux:**
```bash
tail -f ~/logs/claude_scheduler.log
```

**Windows:**
```powershell
Get-Content "$env:USERPROFILE\logs\claude_scheduler.log" -Tail 20 -Wait
```

## Manual Testing

Test the scheduler script directly:

**macOS/Linux:**
```bash
./scripts/claude_scheduler.sh
```

**Windows:**
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\claude_scheduler.ps1
```