# Claude Code Scheduler

**Never lose your Claude Code session again!** 🚀

## The Problem

Claude Code has a 5-hour session limit. Once your session ends, you have to wait for a new one to start. This creates scheduling headaches - do you start coding at 7 AM to maximize morning productivity? Save it for the afternoon? What if inspiration strikes at midnight but you "wasted" your session earlier? Plus, who wants to plan their entire day around session windows?

## The Solution

Claude Code Scheduler automatically runs a simple Claude command at regular intervals throughout the day, keeping an active session ready whenever you need it. By maintaining continuous sessions, you always have Claude available without worrying about timing or availability windows.

**Translation:** Jump into coding whenever YOU want - morning, noon, or 3 AM. Claude's always ready. 🎯

## Key Benefits

✅ **Work-Life Balance** - Code from 9-5, 2-3 AM, or whenever inspiration strikes  
✅ **No More Session Planning** - Stop calculating optimal start times  
✅ **Always Available** - Claude is ready whenever you are, 24/7  
✅ **Works While You Sleep** - Wake up to a fresh, ready-to-go session  
✅ **Weekend Friendly** - Saturday morning debugging? Sunday night side project? No problem  
✅ **Cross-Platform** - Works on macOS, Linux, and Windows  
✅ **Set and Forget** - One-time setup, runs forever  
✅ **Lightweight** - Uses less resources than your Spotify web player  

## How It Works

Simply set your preferred start time, and the scheduler automatically creates 4 sessions at 5-hour intervals throughout the day.

**Important:** When you run a command at any time after the hour, Claude's session window starts from that hour and runs for 5 hours.

**Example:** Run at 6:15 AM → Session active from 6:00 AM to 11:00 AM  
**Example:** Run at 9:45 AM → Session active from 9:00 AM to 2:00 PM  
**Example:** Run at 10:01 PM → Session active from 10:00 PM to 3:00 AM

So with sessions at 6:15, 11:15, 16:15, and 21:15, you get:
- 6:15 AM command → 6 AM-11 AM session
- 11:15 AM command → 11 AM-4 PM session  
- 4:15 PM command → 4 PM-9 PM session
- 9:15 PM command → 9 PM-2 AM session

**Result:** Full 24-hour coverage with 4 strategic commands! Your computer wakes 5 minutes early to ensure everything runs smoothly.

## Quick Start

### Prerequisites
- Python 3.6+
- Claude CLI installed and working:
  - **macOS/Linux**: Claude CLI installed normally
  - **Windows**: WSL installed with Claude configured inside WSL
- Admin/sudo access

### Setup (30 seconds)

1. **Clone the repository**
```bash
git clone https://github.com/naurium/claude-code-scheduler.git
cd claude-code-scheduler
```

2. **Run the setup**
```bash
python3 setup.py
```

That's it! The scheduler is now running and will keep your Claude Code session alive.

### Check Status
```bash
python3 status.py --logs
```

### Remove
```bash
python3 uninstall.py
```

## Perfect For

🧑‍💻 **Night Owl Developers** - Start coding at 11 PM without doing session math  
☕ **Morning People** - Your 6 AM session is already warmed up with your coffee  
👨‍👩‍👧 **Parents** - Code during naptime, school hours, or after bedtime—whenever works  
🏖️ **Remote Workers** - Beach coding? Mountain cabin debugging? No problem!  
📚 **Students** - Study when you can, not when your session allows  
🚀 **Startup Founders** - Because you have enough to worry about already

## Detailed Setup

For advanced configuration, platform-specific details, and troubleshooting, see the [Setup Guide](SETUP.md).

## Real Talk: How It Solves the 5-Hour Problem

Claude Code sessions are limited to 5-hour windows starting from the hour you run a command. Without the scheduler, you have to strategically time when to start your session. With the scheduler running every 5 hours, you get:
- Continuous session availability throughout the day (sessions overlap perfectly!)
- No need to "save" your session for the right time  
- Freedom to code in short bursts or long marathons
- No more "Should I start my session now or wait?" decisions

**The Math:** Running at XX:15 gives you a session from XX:00 to XX+5:00. Four strategically timed commands ensure you always have an active or upcoming session window, providing continuous availability throughout your day.

**The best part?** You can finally:
- 🍕 Take a proper lunch break without worrying about "wasting" session time
- 🏃 Go for that run at 3 PM without calculating remaining hours
- 👶 Handle daycare pickup without session FOMO
- 💤 Sleep peacefully knowing tomorrow's session is already secured
- ☕ Have coffee with a human instead of optimizing session schedules

## Supported Platforms

| Platform | Scheduler | Wake Support | Requirements |
|----------|-----------|--------------|--------------|
| macOS | LaunchDaemons | ✅ Full | Claude CLI installed |
| Linux | systemd/cron | ✅ Full* | Claude CLI installed |
| Windows | Task Scheduler | ✅ Full | WSL + Claude in WSL |

*Linux wake support requires `rtcwake` compatibility

## Configuration

### Two Ways to Configure

#### Option 1: Simple Mode (Recommended)
Just set your preferred start time, and we'll handle the rest:

```json
{
  "start_time": "06:15",        // Your preferred first session time
  "wake_minutes_before": 5,     // Wake computer 5 min early
  "command": "claude -p \"hello\"",
  "enable_wake": true
}
```

Automatically creates 4 sessions at 5-hour intervals. Perfect for the 5-hour session limit!

#### Option 2: Manual Mode (Power Users)
Want full control? Set exact times for each session:

```json
{
  "schedule": [
    {"time": "07:00", "wake_minutes_before": 5},
    {"time": "12:30", "wake_minutes_before": 5},
    {"time": "18:00", "wake_minutes_before": 10},
    {"time": "23:45", "wake_minutes_before": 5}
  ],
  "command": "claude -p \"hello\"",
  "enable_wake": true
}
```

Set any times you want - perfect for irregular schedules or specific needs.

**Note:** Use `config.json` for simple mode (default) or rename `config.manual.example.json` to `config.json` for manual mode.

## Support

For issues, questions, or feature requests, please open an issue on [GitHub](https://github.com/naurium/claude-code-scheduler/issues).

## License

MIT License - Keep your Claude sessions alive, freely and forever!

---

### A Note on Balance

We built this because we believe coding should fit into your life, not the other way around. No more "I should start my session now to maximize the 5 hours" or "I'll wait until after lunch to begin." Whether you need 10 minutes to fix a bug or 4 hours for deep work—Claude is always ready.

**Stop planning around session windows. Start living your life. Code on your schedule.** 💪

*P.S. - Yes, it really works. Yes, even on weekends. Yes, your computer will wake up at 6:10 AM to refresh your session. No, you don't have to feel guilty about only using 30 minutes of a 5-hour window.*