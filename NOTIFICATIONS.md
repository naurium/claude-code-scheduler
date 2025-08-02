# Push Notifications Setup

**Get notified when Claude runs. Know if something breaks. Peace of mind in your pocket.** 📱

## ⚠️ Important: Topics Are PUBLIC

**ntfy.sh topics are publicly accessible** - anyone who knows your topic name can:
- Send you notifications
- See notifications sent to that topic (if they're listening)

### Use Random Topic Names!

**Best Practice:** Use the random topic that ntfy.sh generates for you:
1. Visit https://ntfy.sh
2. Click "Subscribe to topic"
3. Use the generated random topic (like `wT3zr8K2BdPM`)

**Avoid:** Using predictable names like `john-claude` or `mycompany-scheduler`

## Why Add Notifications?

Your scheduler runs silently in the background. That's great until you wonder: "Is it actually working?" 

With push notifications, you'll know:
- ✅ **Confirmation** - "Yep, Claude ran at 6am as planned"
- ❌ **Instant alerts** - Something broke? Know immediately
- 📊 **Track patterns** - See your actual Claude usage over time
- 🔕 **Or stay silent** - Notifications are completely optional

## Quick Setup (5 minutes)

We use **ntfy.sh** - a free, simple push notification service. No account needed.

### 1. Get Your Random Topic

**Recommended:** Visit https://ntfy.sh and use their auto-generated topic name

**Or:** Create your own unguessable topic (like `xK9mP2qR7claude`)

### 2. Subscribe on Your Devices

**Phone:**
- Install the ntfy app (iOS/Android)
- Subscribe to your topic

**Desktop:**
- Visit `https://ntfy.sh/your-topic-name`
- Click "Subscribe"

### 3. Test It Works

```bash
# Replace with your random topic from step 1
curl -d "Test from Claude Scheduler" ntfy.sh/YOUR_RANDOM_TOPIC
```

Did you get it? Great! Let's integrate it.

### 4. Add to Your Scheduler

Run this command with your random topic:

```bash
python3 setup.py --add-notifications YOUR_RANDOM_TOPIC
```

**Example with random topic:**
```bash
python3 setup.py --add-notifications wT3zr8K2BdPM
```

That's it! You'll now get notifications every time Claude runs.

## What You'll See

**Success notification:**
```
✅ Claude session refreshed at 11:00 AM
```

**Error notification (high priority):**
```
⚠️ Claude scheduler failed - check logs
```

## Manual Setup (Advanced)

If you prefer to configure manually or the automatic setup doesn't work:

### macOS/Linux

Edit your scheduler script to add notification calls:

```bash
# After successful Claude command
curl -d "✅ Claude session refreshed at $(date '+%H:%M')" ntfy.sh/YOUR_TOPIC

# On error
curl -d "⚠️ Claude scheduler failed" -H "Priority: high" ntfy.sh/YOUR_TOPIC
```

### Windows

Add to your PowerShell script:

```powershell
# After successful Claude command
Invoke-RestMethod -Uri "https://ntfy.sh/YOUR_TOPIC" -Method Post -Body "✅ Claude session refreshed"

# On error
Invoke-RestMethod -Uri "https://ntfy.sh/YOUR_TOPIC" -Method Post -Body "⚠️ Claude scheduler failed" -Headers @{"Priority"="high"}
```

## Customization Options

### Richer Notifications

```bash
# With title and tags
curl -d "Session refreshed successfully" \
     -H "Title: Claude Scheduler" \
     -H "Tags: success,checkmark" \
     ntfy.sh/YOUR_TOPIC

# With device info
curl -d "Claude ran on $(hostname) at $(date)" \
     ntfy.sh/YOUR_TOPIC
```

### Alternative Services

**Prefer Slack?**
```bash
curl -X POST -H 'Content-type: application/json' \
     --data '{"text":"Claude session refreshed"}' \
     YOUR_SLACK_WEBHOOK_URL
```

**Discord fan?**
```bash
curl -H "Content-Type: application/json" \
     -d '{"content":"Claude session refreshed"}' \
     YOUR_DISCORD_WEBHOOK_URL
```

**Mac-only (local notifications):**
```bash
osascript -e 'display notification "Claude ran" with title "Scheduler"'
```

## Privacy & Security

- **Topics are public** - Always use random/unguessable topic names
- **No personal data** - Notifications only say "success" or "error" 
- **Don't share your topic** - Treat it like a password
- **Rate limits** - ntfy.sh allows plenty for scheduler use
- **Self-host option** - Run your own ntfy server if needed for complete privacy

## Troubleshooting

### Not Getting Notifications?

1. **Test ntfy directly:**
```bash
curl -d "Test message" ntfy.sh/YOUR_TOPIC
```

2. **Check logs:**
```bash
python3 status.py --logs
```

3. **Verify subscription:**
- Re-subscribe on your devices
- Try a different topic name

4. **Network issues:**
```bash
ping ntfy.sh
```

## Turn Off Notifications

```bash
python3 setup.py --remove-notifications
```

Or just unsubscribe from the topic on your devices.

---

### The Real Benefit

Stop wondering if your scheduler is working. Stop checking logs manually. Get a simple notification and move on with your day.

**It's not about monitoring. It's about not having to think about it.**

## Questions?

See an issue? Open it on [GitHub](https://github.com/naurium/claude-code-scheduler/issues).