---
name: discord-bot-setup
description: >
  Add the Hermes Discord bot to a new server, troubleshoot "bot not responding"
  issues, and generate invite URLs. Use when the user creates a new Discord
  server or reports the bot isn't responding in a server channel.
tags: [discord, gateway, bot, troubleshooting, setup]
triggers:
  - user creates a new Discord server and wants to connect Hermes
  - bot works in DMs but not in a server
  - bot not responding in Discord
  - need to generate a Discord bot invite URL
---

# Discord Bot Setup & Troubleshooting

## Adding Bot to a New Server

The bot must be explicitly invited to each Discord server via an OAuth2 URL.
Being connected to one server does NOT make it available in others.

### 1. Extract the bot's Client ID from the token

```bash
# The client ID is the base64-decoded first segment of the bot token
grep 'DISCORD_BOT_TOKEN' ~/.hermes/.env | cut -d= -f2 | cut -d. -f1 | tr -d "'"
# Then decode:
python3 -c "import base64; print(base64.b64decode('<FIRST_SEGMENT>==').decode())"
```

### 2. Generate the invite URL

```
https://discord.com/oauth2/authorize?client_id=<CLIENT_ID>&scope=bot&permissions=274877975552
```

Permission value `274877975552` includes:
- Send Messages, Read Message History, View Channels
- Attach Files, Embed Links, Use Slash Commands

### 3. Open URL in browser, select the target server, authorize

### 4. Restart gateway (recommended)

```bash
hermes gateway restart
```

Then verify:
```bash
sleep 10 && tail -10 ~/.hermes/logs/gateway.log
```

Look for: `[Discord] Connected as BotName#NNNN` and `Synced N slash command(s)`.

## Troubleshooting: Bot Not Responding in Server

### Diagnostic checklist (check in order)

1. **Is the bot in the server?**
   - Check Discord member list for the bot with green "online" dot
   - If missing → generate invite URL (see above) and add it

2. **Check gateway logs for inbound messages:**
   ```bash
   tail -50 ~/.hermes/logs/gateway.log | grep -i 'inbound\|discord\|error'
   ```
   - If NO inbound from the server channel → bot isn't receiving messages (permissions or not in server)
   - If inbound appears but no response → check for API errors in logs

3. **Channel permissions on Discord side:**
   - Bot needs "View Channel" and "Read Message History" in the specific channel
   - Check server Settings → Roles → bot role → channel overrides

4. **Config: `require_mention`**
   ```yaml
   # ~/.hermes/config.yaml
   discord:
     require_mention: true   # Must @mention the bot in server channels
   ```
   - DMs always work without mention
   - Server channels require @BotName if this is true

5. **Config: `DISCORD_ALLOWED_USERS`**
   ```bash
   grep 'DISCORD_ALLOWED_USERS' ~/.hermes/.env
   ```
   - This is a comma-separated list of Discord user IDs
   - User IDs are global (same across all servers) — NOT server-specific
   - If empty/unset, all users can interact

6. **`DISCORD_HOME_CHANNEL` is NOT a restriction**
   - This only sets the default channel for cron job delivery
   - It does NOT restrict which channels the bot responds in

### Common "works in DM but not server" causes

| Cause | Fix |
|-------|-----|
| Bot not invited to server | Generate invite URL and add |
| Missing channel permissions | Grant View Channel + Read Message History to bot role |
| `require_mention: true` but user isn't @mentioning | @mention the bot, or set `require_mention: false` |
| Bot role below a restrictive role | Move bot role higher in server role hierarchy |

## Key Source Code Locations

```
~/.hermes/hermes-agent/gateway/platforms/discord*.py  # Discord adapter
~/.hermes/hermes-agent/gateway/config.py              # HOME_CHANNEL resolution
~/.hermes/hermes-agent/gateway/run.py                 # Message dispatch
```

### Message filter chain (in on_message handler):
1. Ignore own messages
2. Ignore Discord system messages (pins, joins, etc.)
3. Check `DISCORD_ALLOWED_USERS` → reject if not in list
4. Check `DISCORD_ALLOW_BOTS` (default: "none")
5. Check `DISCORD_IGNORE_NO_MENTION` — if mentions exist but bot isn't mentioned, ignore
6. Pass to `_handle_message()`
