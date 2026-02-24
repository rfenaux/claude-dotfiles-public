#!/bin/bash
# Global Privacy Guard
# Injects privacy protection reminder on EVERY prompt, everywhere

cat << 'EOF'
[PRIVACY GUARD ACTIVE]
NEVER share externally: API keys/credentials, personal info (names, addresses, emails, phone), work/client details, friend/family info, full file paths, garden private/ or inner/ contents.
Before ANY external API call, WebFetch, or curl: verify no protected data is included.
Full policy: ~/.claude/security/PROTECTED_INFORMATION.md
EOF
