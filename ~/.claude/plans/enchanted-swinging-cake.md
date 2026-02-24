# Plan: Public Repo Installer + README Overhaul

**Context:** The `claude-dotfiles-public` sync (Feb 24 commit) inadvertently included private dotfiles-sync/backup scripts. This plan removes those, creates a proper interactive installer, and rewrites the README for non-technical users.

---

## Phase 1: Remove Private Dotfiles Infrastructure

### 1.1 Delete 3 files entirely

```bash
rm /Users/raphael/claude-dotfiles-public/scripts/dotfiles-sync.sh
rm /Users/raphael/claude-dotfiles-public/scripts/dotfiles-backup.sh
rm /Users/raphael/claude-dotfiles-public/hooks/claude-config-backup.sh
```

**Why:** These use a bare git repo at `~/.dotfiles.git` and push to owner's private GitHub. Zero value to public users; potential confusion.

### 1.2 Strip LaunchAgent block from `scripts/dotfiles-install-deps.sh`

Remove lines 173–189 (the `# 8. Load LaunchAgent` block):
```bash
# 8. Load LaunchAgent (macOS only)
if [ "$OS" = "Darwin" ] && [ -f "$HOME/Library/LaunchAgents/com.raphael.dotfiles-backup.plist" ]; then
    ...
fi
```

Replace with nothing. The surrounding summary block stays.

### 1.3 Remove hook entry from `settings.example.json`

In the `SessionEnd` array, remove this entry:
```json
{
  "type": "command",
  "command": "${HOME}/.claude/hooks/claude-config-backup.sh",
  "timeout": 15000
},
```

### 1.4 Sanitize `CLAUDE.md` (3 spots)

**File:** `/Users/raphael/claude-dotfiles-public/CLAUDE.md`

**Line 745** — Remove the entire table row:
```
| `dotfiles-sync.sh` / `dotfiles-backup.sh` | Pull/push dotfiles to GitHub |
```

**Lines 758–762** — Remove the "Dashboard & Dotfiles" section block that references the private git workflow and warning about `dotfiles-sync.sh`. Replace the warning with:
```
**Dashboard:** http://localhost:8420
```

**Line 785** — Remove bullet:
```
- `~/.claude/projects/TAXES_CONTEXT.md` - Belgian tax context
```

---

## Phase 2: Create `install.sh` (interactive installer)

**File:** `/Users/raphael/claude-dotfiles-public/install.sh`

### Architecture

```
install.sh
├── [A] Color helpers + NO_COLOR fallback
├── [B] Arg parsing: --yes, --prefix PATH, --no-deps, --help
├── [C] Prerequisites check: claude CLI, python3 3.11+, git
├── [D] Welcome banner (what will be installed)
├── [E] Ask install path  (default ~/.claude)
├── [F] Handle existing dir: [b]ackup, [m]erge, [a]bort
├── [G] rsync repo → install path (exclude .git, install.sh, README.md)
├── [H] chmod +x hooks/*.sh, scripts/*.sh, ctm/scripts/*
├── [I] Bootstrap settings.json from example (if not exists)
├── [J] Run dotfiles-install-deps.sh (unless --no-deps)
├── [K] Ask: Install Ollama? (Y/n)
├── [L] Ask: OpenAI key? Google key? → append to ~/.zshrc or ~/.bashrc
├── [M] Run validate-setup.sh --quick
└── [N] Print first-session instructions
```

### Key behaviors

| Flag | Behavior |
|------|----------|
| `--yes` | Accept all defaults; skip optional Ollama/API prompts; use merge mode on existing dirs |
| `--prefix PATH` | Override install location (default `~/.claude`) |
| `--no-deps` | Skip running `dotfiles-install-deps.sh` |

**Merge mode** (default when existing dir detected in `--yes` mode):
- `rsync -rq --ignore-existing` — adds new files, never overwrites existing

**Backup mode** (interactive choice):
- `cp -r $INSTALL_PREFIX $INSTALL_PREFIX.backup.$(date +%Y%m%d-%H%M%S)` then full copy

**Permissions:** `find hooks/ scripts/ ctm/scripts/ -name "*.sh" -o -name "*.py" | xargs chmod +x`

**API keys:** Append `export KEY="..."` to `~/.zshrc` (detect shell via `$SHELL`, fallback to checking `.bashrc` exists).

**Ollama:**
- Check `command -v ollama`; if missing, install via `brew install ollama` (macOS) or `curl | sh` (Linux)
- Then `ollama pull mxbai-embed-large`
- Fail gracefully with manual instructions if it fails

### Script must
- Work on macOS and Linux
- Be non-destructive by default (merge mode = never overwrite)
- Make `install.sh` itself `chmod +x` in the repo (add to git)

---

## Phase 3: Rewrite `README.md`

**Target:** Non-technical users can understand what this is and install it. Developers get the detail they need. Scannable.

### Structure

```
# Claude Code Dotfiles
> Hook: value prop in one line

## What is this?        ← 3 sentences, plain language
## Who is this for?     ← 4 bullet points
## What you get         ← benefit table (not feature dump)
## Prerequisites        ← table: tool | why | how to install
## Quick Install        ← 3 options: curl pipe, manual clone, --yes flag
## First Session        ← numbered steps + 3 commands to try
## Key Features         ← CTM + RAG, Agents, Hooks, Self-Healing
## Directory Structure  ← keep existing
## Customizing          ← how to add agent, disable hook, adjust permissions
## Troubleshooting      ← 4 common issues with exact commands
## Documentation Table  ← keep existing
## License / Acknowledgments
```

### Key copy changes from current README

| Current (feature dump) | Rewrite (benefit-driven) |
|------------------------|--------------------------|
| "148 Agents - Specialized AI agents for every use case" | "Claude routes complex requests to domain experts — you don't have to think about which agent" |
| Jumps to `git clone` as step 1 | Prerequisites table first, then Quick Install with one-liner |
| No troubleshooting | 4 sections: hooks not running, RAG issues, CTM PATH, settings not applying |
| No "What is this?" | 3-sentence plain-language intro |
| Missing Ollama guidance if not installed | Prereqs table + Troubleshooting |

---

## Execution Order

```
Commit 1: "chore: remove private dotfiles sync scripts"
  - rm scripts/dotfiles-sync.sh
  - rm scripts/dotfiles-backup.sh
  - rm hooks/claude-config-backup.sh

Commit 2: "chore: strip private references from config"
  - scripts/dotfiles-install-deps.sh (remove lines 173-189)
  - settings.example.json (remove claude-config-backup.sh)
  - CLAUDE.md (remove 3 spots: table row, warning block, TAXES_CONTEXT)

Commit 3: "feat: add interactive install.sh"
  - Create install.sh, chmod +x

Commit 4: "docs: rewrite README for non-technical users"
  - Full README rewrite
```

---

## Verification

```bash
# 1. Confirm private files gone
ls /Users/raphael/claude-dotfiles-public/scripts/dotfiles-sync.sh  # should 404
ls /Users/raphael/claude-dotfiles-public/hooks/claude-config-backup.sh  # should 404

# 2. Confirm no rfenaux or private refs
grep -r "rfenaux\|TAXES_CONTEXT\|LaunchAgent\|dotfiles-backup" \
  /Users/raphael/claude-dotfiles-public/ \
  --exclude-dir=.git \
  --exclude="outgoing-data-guard.py"  # this one has regex, keep

# 3. Test installer (fresh)
TMPDIR=$(mktemp -d)
bash /Users/raphael/claude-dotfiles-public/install.sh \
  --yes --prefix "$TMPDIR/test-claude" --no-deps
ls "$TMPDIR/test-claude/agents/" | wc -l    # expect ~143
ls "$TMPDIR/test-claude/hooks/"  | wc -l    # expect ~60
cat "$TMPDIR/test-claude/settings.json" | python3 -m json.tool > /dev/null  # valid JSON
find "$TMPDIR/test-claude/hooks" -name "*.sh" -not -executable | wc -l  # expect 0

# 4. Test merge mode (existing dir preserved)
echo "my custom" > "$TMPDIR/test-claude/MYFILE.txt"
bash /Users/raphael/claude-dotfiles-public/install.sh \
  --yes --prefix "$TMPDIR/test-claude" --no-deps
cat "$TMPDIR/test-claude/MYFILE.txt"  # should still say "my custom"

# 5. Test --help flag
bash /Users/raphael/claude-dotfiles-public/install.sh --help  # should print usage

rm -rf "$TMPDIR"
```
