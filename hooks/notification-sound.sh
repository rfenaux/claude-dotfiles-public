#!/bin/bash
set +e  # Never use set -e in hooks — non-zero exits kill the hook

# Notification hook - play macOS sound for notifications
afplay /System/Library/Sounds/Ping.aiff &

exit 0
