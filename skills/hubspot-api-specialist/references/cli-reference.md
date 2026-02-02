# HubSpot CLI Reference

Complete reference for `hs` CLI commands.

## Installation

```bash
npm install -g @hubspot/cli
```

**Version:** Requires Node.js 18+

---

## Authentication

### Initial Setup

```bash
hs init
```

Creates `~/.hscli/config.yml` with account credentials.

### Add Another Account

```bash
hs auth
```

### Specify Account

```bash
hs auth --account=sandbox
```

### Config File Location

```
~/.hscli/config.yml
```

**Config Structure:**
```yaml
defaultPortal: production
portals:
  - name: production
    portalId: 123456
    authType: personalaccesskey
    personalAccessKey: pat-xxx
  - name: sandbox
    portalId: 789012
    authType: personalaccesskey
    personalAccessKey: pat-yyy
```

---

## Project Commands

### Create Project

```bash
# Interactive mode
hs project create

# With flags
hs project create \
  --platform-version 2025.2 \
  --name "my-app" \
  --dest my-app \
  --project-base app \
  --distribution private \
  --auth static
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--platform-version` | Platform version (2025.2 recommended) |
| `--name` | Project name |
| `--dest` | Local directory |
| `--project-base` | `app` or `cms-theme` |
| `--distribution` | `private` or `public` |
| `--auth` | `static` (private app) or `oauth` |

### Development Server

```bash
hs project dev
```

Starts local dev server with hot reload.

### Upload Project

```bash
# From project root
hs project upload

# Specify path
hs project upload path/to/project
```

### Deploy Project

```bash
# Deploy latest upload
hs project deploy

# Deploy specific build
hs project deploy --buildId=1
```

### Upload + Deploy

```bash
hs project upload && hs project deploy
```

### List Builds

```bash
hs project builds
```

### Project Logs

```bash
hs project logs
```

---

## Secrets Management

### Add Secret

```bash
hs secrets add SECRET_NAME
```

Prompts for secret value (hidden input).

### List Secrets

```bash
hs secrets list
```

### Delete Secret

```bash
hs secrets delete SECRET_NAME
```

### Update Secret

```bash
hs secrets update SECRET_NAME
```

---

## Function Logs

### Tail Logs (Real-time)

```bash
hs logs functions --tail
```

### Recent Logs

```bash
hs logs functions --latest
```

### Filter by Function

```bash
hs logs functions --function=my-function
```

---

## CMS Commands

### Upload Files

```bash
hs upload <local-path> <remote-path>

# Example
hs upload ./theme my-theme
```

### Download Files

```bash
hs fetch <remote-path> <local-path>

# Example
hs fetch my-theme ./local-theme
```

### Watch for Changes

```bash
hs watch <local-path> <remote-path>

# Example
hs watch ./theme my-theme
```

### Create Module

```bash
hs create module
```

### Create Template

```bash
hs create template
```

---

## Sandbox Commands

### Create Sandbox

```bash
hs sandbox create --name="Test Sandbox" --type=development
```

**Types:**
- `development` - Dev/test sandbox
- `standard` - Standard sandbox

### List Sandboxes

```bash
hs sandbox list
```

### Delete Sandbox

```bash
hs sandbox delete --name="Test Sandbox"
```

---

## Account Commands

### List Accounts

```bash
hs accounts list
```

### Set Default Account

```bash
hs accounts use <account-name>
```

### Remove Account

```bash
hs accounts remove <account-name>
```

---

## HubDB Commands

### List Tables

```bash
hs hubdb list
```

### Fetch Table

```bash
hs hubdb fetch <table-id> <output-file>
```

### Create Table

```bash
hs hubdb create <input-file>
```

---

## Custom Object Commands

### List Schemas

```bash
hs custom-object schema list
```

### Create Schema

```bash
hs custom-object schema create <schema-file>
```

---

## Global Flags

| Flag | Description |
|------|-------------|
| `--account=<name>` | Use specific account |
| `--config=<path>` | Custom config file path |
| `--debug` | Enable debug output |
| `--help` | Show help |

---

## Common Workflows

### New Private App with CRM Card

```bash
# 1. Create project
hs project create --platform-version 2025.2 --project-base app --distribution private --auth static

# 2. Add secrets
hs secrets add PRIVATE_APP_ACCESS_TOKEN

# 3. Develop locally
hs project dev

# 4. Deploy
hs project upload && hs project deploy
```

### New CMS Theme

```bash
# 1. Create project
hs project create --project-base cms-theme

# 2. Watch for changes
hs watch ./src <remote-theme-name>

# 3. Or upload manually
hs upload ./src <remote-theme-name>
```

### Debug Serverless Function

```bash
# Terminal 1: Dev server
hs project dev

# Terminal 2: Tail logs
hs logs functions --tail
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Not authenticated" | Run `hs auth` |
| "Portal not found" | Check `--account` flag or `hs accounts list` |
| "Build failed" | Run `npm install` in extensions/ and app.functions/ |
| "Function not found" | Check serverless.json endpoint name |
| "Permission denied" | Check private app scopes in HubSpot |

### Reset Config

```bash
rm ~/.hscli/config.yml
hs init
```

### Verbose Output

```bash
hs project upload --debug
```
