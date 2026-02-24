# Trust Skill

> Temporarily enable credential handling for the current session

## Metadata

```yaml
name: trust
version: 1.0.0
triggers:
  - "/trust"
  - "trust on"
  - "trust off"
  - "enable credentials"
  - "trusted session"
author: the user
```

## Overview

Enables a "trusted session" mode that temporarily bypasses the privacy guard for credential handling. This allows working with API keys, tokens, and secrets when explicitly needed.

## Commands

| Command | Action |
|---------|--------|
| `/trust on` | Enable trusted mode (requires confirmation) |
| `/trust off` | Disable trusted mode |
| `/trust status` | Check current trust state |
| `/trust log` | View recent trust session history |

## Safety Model

1. **Explicit consent** - Requires typing `confirm` after `/trust on`
2. **Session-scoped** - Auto-expires when session ends
3. **Audit trail** - All trust enable/disable events logged
4. **Local only** - Still blocks credentials in WebFetch/external calls
5. **Passphrase option** - Can require passphrase for extra security

## Implementation

### Enable Trust (`/trust on`)

```bash
# 1. Prompt for confirmation
echo "⚠️  TRUSTED SESSION MODE"
echo "This will allow credential handling in THIS session only."
echo "Credentials will still be blocked from external API calls."
echo ""
echo "Type 'confirm' to enable:"

# 2. On confirmation, create marker
MARKER="/tmp/claude-trusted-session"
echo "$(date -Iseconds)|${PWD}|enabled" >> ~/.claude/logs/trusted-sessions.log
touch "$MARKER"

# 3. Confirm
echo "[TRUSTED SESSION ENABLED] - Credential handling allowed until session end"
```

### Disable Trust (`/trust off`)

```bash
MARKER="/tmp/claude-trusted-session"
if [[ -f "$MARKER" ]]; then
  rm "$MARKER"
  echo "$(date -Iseconds)|${PWD}|disabled" >> ~/.claude/logs/trusted-sessions.log
  echo "[TRUSTED SESSION DISABLED] - Privacy guard re-enabled"
else
  echo "Trust mode was not enabled"
fi
```

### Check Status (`/trust status`)

```bash
MARKER="/tmp/claude-trusted-session"
if [[ -f "$MARKER" ]]; then
  echo "🔓 TRUSTED SESSION ACTIVE"
  echo "Credential handling: ENABLED"
  echo "External calls: STILL BLOCKED"
else
  echo "🔒 STANDARD MODE"
  echo "Privacy guard: ACTIVE"
fi
```

## Behavior When Trust Enabled

| Action | Allowed? |
|--------|----------|
| Receive credentials in chat | ✅ Yes |
| Store credentials in env vars | ✅ Yes |
| Use credentials in local Bash | ✅ Yes |
| Pass credentials to WebFetch | ❌ No (still blocked) |
| Pass credentials to external curl | ❌ No (still blocked) |
| Log credentials to files | ⚠️  With warning |

## Audit Log Format

Location: `~/.claude/logs/trusted-sessions.log`

```
2026-02-03T19:20:00+01:00|~/project|enabled
2026-02-03T19:45:00+01:00|~/project|disabled
2026-02-03T19:45:00+01:00|~/project|session_end_cleanup
```

## Auto-Cleanup

The `SessionEnd` hook automatically removes trust markers:

```bash
# In session-end-cleanup.sh
rm -f /tmp/claude-trusted-session-* 2>/dev/null
```

## Security Notes

- Trust markers are stored in `/tmp/` which is cleared on reboot
- Simple marker file (one active trust session at a time)
- External API calls remain blocked even in trusted mode
- All trust events are logged for audit purposes

## References

- **Full guide:** `~/.claude/docs/TRUSTED_SESSION_GUIDE.md`
- **Privacy policy:** `~/.claude/security/PROTECTED_INFORMATION.md`
- **Script:** `~/.claude/scripts/trust-session.sh`
- **Hook:** `~/.claude/hooks/global-privacy-guard.sh`
