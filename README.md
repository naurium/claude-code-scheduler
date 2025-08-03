# Claude Code Scheduler

**Go grab coffee ☕ Take a real lunch break 🍕 Take that 3pm run 🏃 Pick up the kids 👶**  
*Your Claude session will be waiting when you get back.*

## The Magic ✨

You know that annoying 5-hour session limit? Where you have to plan your entire day around when to start coding?

**Yeah, we fixed that.**

This tiny scheduler keeps Claude ready all day. Install once, forget forever. Code whenever YOU want - not when your session window allows.

## Life, Upgraded

🍕 **Take a proper lunch break** - No more eating at your desk to "maximize session time"  
☕ **Grab coffee whenever** - Your session isn't going anywhere  
🏃 **3pm run? Do it** - Stop calculating remaining session hours  
👶 **Daycare pickup** - Handle life without session FOMO  
💤 **Sleep peacefully** - Tomorrow's session is already secured  
🌅 **6am inspiration?** - Your session is already warmed up with your coffee  
🌙 **11pm debugging?** - No session math required  

## How It Actually Works

Every 5 hours, it runs a simple command to refresh your Claude session. That's it.

**Same times every day** - Your sessions start and end at consistent times, so you can plan around them if needed. Or just ignore them completely.

The result? **Continuous 24-hour coverage**. Your computer even wakes itself up to run the commands (you won't notice).

✅ **Work from 9-5, 2-3am, or whenever**  
✅ **Weekend debugging? Saturday side projects? Always ready**  
✅ **Zero config after setup**  
✅ **Uses less resources than your Spotify tab**  
✅ **Works on Mac, Linux, and Windows**  

## Install in 30 Seconds

```bash
git clone https://github.com/naurium/claude-code-scheduler.git
cd claude-code-scheduler
python3 setup.py
```

**That's it.** Claude is now available all day. Go live your life.

### Check it's working
```bash
python3 status.py --logs
```

### Want notifications?
```bash
python3 setup.py --add-notifications
```
See [Push Notifications Setup](NOTIFICATIONS.md) for details.

### Remove it
```bash
python3 uninstall.py
```

## Requirements

- Python 3.6+
- Claude CLI installed
- Admin/sudo access (for system schedulers)
- Windows users: WSL with Claude configured inside

## Who This is For

🧑‍💻 **Night Owls** - Code at 11pm without session math  
☕ **Morning People** - 6am session ready with your coffee  
👨‍👩‍👧 **Parents** - Naptime, school hours, after bedtime - whenever works  
🏖️ **Remote Workers** - Beach coding? Mountain debugging? Always ready  
📚 **Students** - Study when you can, not when sessions allow  
🚀 **Startup Founders** - You have enough to worry about already

## The Technical Details (If You Care)

**The Problem:** Claude has 5-hour session windows. Miss your window, wait for the next one.

**Our Solution:** Run a command every 5 hours at the same times daily. Sessions stay fresh. You stay flexible.

**How:** System schedulers (launchd/systemd/Task Scheduler) + wake timers = 24/7 coverage

**The Math:** 4 commands at 5-hour intervals = continuous availability. Your machine wakes 5min early to ensure everything runs.

**Example Schedule:** Start at 6:15 AM → Sessions at 6:15, 11:15, 4:15 PM, 9:15 PM daily  
**Why It Works:** Same schedule every day means predictable availability + no planning needed

## Supported Platforms

✅ **macOS** - Dual LaunchDaemon/Agent architecture + automatic wake support  
✅ **Linux** - systemd/cron + manual wake support (rtcwake)  
✅ **Windows** - Task Scheduler + wake support (via WSL)

## Advanced Setup

Need custom schedules? Platform-specific help? See the [Setup Guide](SETUP.md).
---

### Why We Built This

We got tired of planning our lives around 5-hour windows. Of eating lunch at our desks. Of skipping that perfect-weather run because we had "2 hours left."

Coding should fit into your life, not the other way around.

**Now it does.**

*P.S. - Yes, it works on weekends. No, you won't notice when it runs. Yes, you can use 10 minutes of a 5-hour window guilt-free.*

## License

MIT - Free forever, like your schedule should be.

## Issues?

Open an issue on [GitHub](https://github.com/naurium/claude-code-scheduler/issues).