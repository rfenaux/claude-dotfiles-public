#!/usr/bin/env python3
"""Claude Code Menu Bar Status Display (v2.1).

Polls ~/.claude/status/index.json every 5 seconds and displays in macOS menu bar.
Features: dynamic icon, notifications, session submenus, CTM task, context forecast,
session history, config hot-reload, interactive approvals, new session launcher.
Supports multiple concurrent sessions (MON-001).
Requires: pip3 install rumps Pillow
"""
import json
import logging
import logging.handlers
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import rumps

# --- Graceful PIL import ---
try:
    from PIL import Image, ImageDraw
    ICON_ENABLED = True
except ImportError:
    ICON_ENABLED = False

# --- Logging ---
LOG_PATH = Path.home() / ".claude" / "logs" / "menubar.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
_handler = logging.handlers.RotatingFileHandler(
    str(LOG_PATH), maxBytes=500_000, backupCount=2
)
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger = logging.getLogger("claude-menubar")
logger.addHandler(_handler)
logger.setLevel(logging.WARNING)

# --- Paths ---
STATUS_INDEX = Path.home() / ".claude" / "status" / "index.json"
LEGACY_STATUS_FILE = Path.home() / ".claude" / "status.json"
CONFIG_PATH = Path.home() / ".claude" / "config" / "menubar-config.json"
STATE_PATH = Path.home() / ".claude" / "config" / "menubar-state.json"
PROFILE_PATH = Path.home() / ".claude" / "machine-profile.json"
SWITCH_PROFILE_SCRIPT = Path.home() / ".claude" / "scripts" / "switch-profile.sh"
QUEUE_PATH = Path.home() / ".claude" / "persistent" / "queue.json"
APPROVALS_DIR = Path.home() / ".claude" / "persistent" / "approvals"
CTM_SCHEDULER = Path.home() / ".claude" / "ctm" / "scheduler.json"
CTM_INDEX = Path.home() / ".claude" / "ctm" / "index.json"
ICON_DIR = Path("/tmp/claude-menubar-icons")
POLL_INTERVAL = 5
STALE_THRESHOLD = 120  # seconds

# --- Config ---
DEFAULT_CONFIG = {
    "icon": {"enabled": True, "size": 22, "style": "circle",
             "thresholds": {"green": 50, "yellow": 80}},
    "notifications": {"enabled": True, "cooldown_minutes": 5, "sound": True,
                      "types": {
                          "context_warning": {"enabled": True, "threshold": 80},
                          "context_critical": {"enabled": True, "threshold": 90},
                          "task_completed": {"enabled": True},
                          "task_failed": {"enabled": True},
                          "load_high": {"enabled": True},
                          "deferred_completed": {"enabled": True},
                          "deferred_failed": {"enabled": True},
                      }},
    "menu": {"max_sessions_shown": 5, "show_agent_names": True,
             "enable_quick_actions": True},
}


def _load_config():
    """Load menubar config with defaults and validation."""
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                config = json.load(f)
            # Validate required keys
            for key in ("icon", "notifications", "menu"):
                if key not in config or not isinstance(config[key], dict):
                    logger.warning("Missing or invalid config key: %s, using default", key)
                    config[key] = DEFAULT_CONFIG[key]
            return config
    except (json.JSONDecodeError, IOError) as e:
        logger.warning("Failed to load config: %s", e)
    return dict(DEFAULT_CONFIG)


# =============================================================================
# IconGenerator — Template-mode icons with status-aware shapes
# =============================================================================

class IconGenerator:
    """Generates status-aware menu bar icons with template + retina support."""

    BASE_SIZE = 18
    RETINA_SIZE = 36

    def __init__(self, config):
        self.enabled = ICON_ENABLED and config.get("icon", {}).get("enabled", True)
        icon_cfg = config.get("icon", {})
        thresholds = icon_cfg.get("thresholds", {})
        self.green_max = thresholds.get("green", 50)
        self.yellow_max = thresholds.get("yellow", 80)
        self.mode = icon_cfg.get("mode", "template")
        self._cached_state = None
        ICON_DIR.mkdir(parents=True, exist_ok=True)

    def _state_for_pct(self, pct):
        if pct < self.green_max:
            return "ok"
        elif pct < self.yellow_max:
            return "warn"
        return "critical"

    def generate(self, context_pct):
        if not self.enabled:
            return None, False
        state = self._state_for_pct(context_pct)
        icon_path = ICON_DIR / f"icon-{state}.png"
        if state == self._cached_state and icon_path.exists():
            return str(icon_path), self.mode == "template"
        if self.mode == "template":
            self._draw_template(state, icon_path)
        else:
            self._draw_color(state, icon_path)
        self._cached_state = state
        return str(icon_path), self.mode == "template"

    def _draw_template(self, state, path):
        sz = self.RETINA_SIZE
        img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        m = 4
        black = (0, 0, 0, 255)
        mid_alpha = (0, 0, 0, 140)

        if state == "ok":
            draw.ellipse([m, m, sz - m, sz - m], outline=black, width=2)
            c = sz // 2
            r = 3
            draw.ellipse([c - r, c - r, c + r, c + r], fill=black)
        elif state == "warn":
            draw.ellipse([m, m, sz - m, sz - m], outline=black, width=2)
            draw.pieslice([m, m, sz - m, sz - m], start=0, end=180, fill=mid_alpha)
            draw.ellipse([m, m, sz - m, sz - m], outline=black, width=2)
        elif state == "critical":
            draw.ellipse([m, m, sz - m, sz - m], fill=black)
            cx, cy = sz // 2, sz // 2
            bar_w = 3
            draw.rectangle([cx - bar_w // 2, cy - 8, cx + bar_w // 2 + 1, cy + 2], fill=(0, 0, 0, 0))
            draw.rectangle([cx - bar_w // 2, cy + 5, cx + bar_w // 2 + 1, cy + 8], fill=(0, 0, 0, 0))

        img.save(str(path), "PNG")

    def _draw_color(self, state, path):
        sz = self.RETINA_SIZE
        img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        m = 4
        colors = {"ok": (76, 175, 80, 255), "warn": (255, 193, 7, 255), "critical": (244, 67, 54, 255)}
        draw.ellipse([m, m, sz - m, sz - m], fill=colors.get(state, (158, 158, 158, 255)))
        img.save(str(path), "PNG")


# =============================================================================
# NotificationManager — Smart macOS notifications with cooldowns
# =============================================================================

class NotificationManager:
    """Manages macOS notifications with per-type cooldowns and state persistence."""

    def __init__(self, config):
        self.enabled = config.get("notifications", {}).get("enabled", True)
        self.cooldown = config.get("notifications", {}).get("cooldown_minutes", 5) * 60
        self.sound = config.get("notifications", {}).get("sound", True)
        self.types = config.get("notifications", {}).get("types", {})
        self._state = self._load_state()

    def _load_state(self):
        try:
            if STATE_PATH.exists():
                with open(STATE_PATH) as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError, FileNotFoundError):
            pass
        return {"last_notified": {}, "known_tasks": {}, "known_deferred": [], "session_history": []}

    def _save_state(self):
        try:
            STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
            tmp = STATE_PATH.with_suffix(".tmp")
            with open(tmp, "w") as f:
                json.dump(self._state, f, indent=2, default=str)
            tmp.replace(STATE_PATH)
        except IOError as e:
            logger.warning("Failed to save state: %s", e)

    def _can_notify(self, ntype, unique_key=None):
        if not self.enabled:
            return False
        type_cfg = self.types.get(ntype, {})
        if not type_cfg.get("enabled", True):
            return False
        key = f"{ntype}:{unique_key}" if unique_key else ntype
        last = self._state.get("last_notified", {}).get(key, 0)
        return (time.time() - last) >= self.cooldown

    def _record(self, ntype, unique_key=None):
        key = f"{ntype}:{unique_key}" if unique_key else ntype
        self._state.setdefault("last_notified", {})[key] = time.time()
        self._save_state()

    def _notify(self, title, subtitle, message, ntype, unique_key=None):
        if not self._can_notify(ntype, unique_key):
            return
        try:
            rumps.notification(title=title, subtitle=subtitle, message=message, sound=self.sound)
        except RuntimeError:
            pass
        self._record(ntype, unique_key)

    def check_and_notify(self, index_data):
        if not self.enabled or not index_data:
            return

        summary = index_data.get("summary", {})
        sessions = index_data.get("sessions", [])
        max_ctx = summary.get("max_context_pct", 0)
        load_status = summary.get("load", {}).get("status", "OK")

        # Context warning/critical
        for ntype, default_thresh in [("context_warning", 80), ("context_critical", 90)]:
            threshold = self.types.get(ntype, {}).get("threshold", default_thresh)
            if max_ctx >= threshold:
                msg = "Consider wrapping up." if ntype == "context_warning" else "Auto-compact soon."
                self._notify("Context " + ntype.split("_")[1].capitalize(), f"Context at {max_ctx}%", msg, ntype)

        # Task completion — session went from active to stale/removed
        current_ids = {s.get("session_id") for s in sessions if s.get("status") == "active"}
        known = self._state.get("known_tasks", {})
        for sid, info in list(known.items()):
            if sid not in current_ids and info.get("was_active"):
                self._notify("Task Completed", info.get("task", "Unknown"), f"Session {sid[:8]} finished.", "task_completed", unique_key=sid)
                # Record to session history
                history = self._state.setdefault("session_history", [])
                history.insert(0, {
                    "session_id": sid,
                    "task": info.get("task", "Unknown"),
                    "completed_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
                })
                self._state["session_history"] = history[:10]
                known.pop(sid, None)

        for s in sessions:
            sid = s.get("session_id", "")
            known[sid] = {"task": s.get("task", "Idle"), "was_active": s.get("status") == "active"}
        self._state["known_tasks"] = known

        if load_status == "HIGH_LOAD":
            self._notify("High Load", "System under heavy load", "Agent spawning is paused.", "load_high")

        self._check_deferred()
        self._save_state()

    def _check_deferred(self):
        try:
            if not QUEUE_PATH.exists():
                return
            with open(QUEUE_PATH) as f:
                queue = json.load(f)
            tasks = queue.get("tasks", [])
        except (json.JSONDecodeError, IOError, FileNotFoundError):
            return

        known = set(self._state.get("known_deferred", []))
        for t in tasks:
            tid = t.get("id", "")
            status = t.get("status", "")
            if tid in known:
                continue
            if status == "completed":
                self._notify("Deferred Task Done", t.get("title", "Untitled"), "Background task completed.", "deferred_completed", unique_key=tid)
                known.add(tid)
            elif status == "failed":
                self._notify("Deferred Task Failed", t.get("title", "Untitled"), f"Error: {t.get('error', 'Unknown')[:80]}", "deferred_failed", unique_key=tid)
                known.add(tid)
        self._state["known_deferred"] = list(known)


# =============================================================================
# ClaudeStatusBar — Main App (v2.1)
# =============================================================================

class ClaudeStatusBar(rumps.App):
    def __init__(self):
        super().__init__("Claude", quit_button=None, template=True)
        self.title = "Claude: No Session"
        self.privacy_mode = False
        self.index_data = {}
        self._session_items = []
        self._profile_items = []
        self._approval_items = []
        self._config_mtime = 0
        self._profile_mtime = 0
        self._ctx_history = []  # (timestamp, pct) ring buffer for forecast

        # Load config and create managers
        self.config = _load_config()
        self.icon_gen = IconGenerator(self.config)
        self.notifier = NotificationManager(self.config)

        # Build menu
        self.task_item = rumps.MenuItem("\U0001f4cb Sessions: -")
        self.context_item = rumps.MenuItem("\U0001f9e0 Context: -")
        self.agents_item = rumps.MenuItem("\U0001f916 Agents: -")
        self.load_item = rumps.MenuItem("\u26a1 Load: -")
        self.ctm_item = rumps.MenuItem("\U0001f3af CTM: -")
        self.session_item = rumps.MenuItem("\U0001f5c2 Active Sessions")
        self.history_menu = rumps.MenuItem("\U0001f4dc Recent Sessions")
        self.profile_menu = rumps.MenuItem("\U0001f527 Profile")
        self._rebuild_profiles()
        self.approvals_menu = rumps.MenuItem("\u2705 No Approvals")

        # Actions
        self.new_session_item = rumps.MenuItem("\U0001f4bb New Claude Session", callback=self.open_new_session)
        self.dashboard_item = rumps.MenuItem("\U0001f310 Open Dashboard", callback=self.open_dashboard)
        self.refresh_item = rumps.MenuItem("\U0001f504 Refresh", callback=self.force_refresh)
        self.privacy_item = rumps.MenuItem("\U0001f512 Privacy Mode", callback=self.toggle_privacy)
        self.quit_item = rumps.MenuItem("\u23fb Quit", callback=rumps.quit_application)

        self.menu = [
            self.task_item,
            self.context_item,
            self.agents_item,
            self.load_item,
            self.ctm_item,
            None,
            self.session_item,
            self.history_menu,
            None,
            self.profile_menu,
            self.approvals_menu,
            None,
            self.new_session_item,
            self.dashboard_item,
            self.refresh_item,
            self.privacy_item,
            None,
            self.quit_item,
        ]

        # Start polling
        self.timer = rumps.Timer(self.update_status, POLL_INTERVAL)
        self.timer.start()
        self.update_status(None)

    # --- Config Hot-Reload ---

    def _check_config_reload(self):
        """Reload config if files changed on disk."""
        try:
            cm = CONFIG_PATH.stat().st_mtime if CONFIG_PATH.exists() else 0
            pm = PROFILE_PATH.stat().st_mtime if PROFILE_PATH.exists() else 0
            if cm != self._config_mtime or pm != self._profile_mtime:
                self.config = _load_config()
                self.icon_gen = IconGenerator(self.config)
                self.notifier = NotificationManager(self.config)
                self._rebuild_profiles()
                self._config_mtime = cm
                self._profile_mtime = pm
        except OSError:
            pass

    # --- Data Loading ---

    def _load_index(self):
        """Load index.json or fall back to legacy status.json."""
        try:
            if STATUS_INDEX.exists():
                with open(STATUS_INDEX) as f:
                    data = json.load(f)
                if data.get("sessions"):
                    return data
        except (json.JSONDecodeError, IOError, FileNotFoundError):
            pass

        try:
            if LEGACY_STATUS_FILE.exists():
                with open(LEGACY_STATUS_FILE) as f:
                    single = json.load(f)
            else:
                return None
        except (json.JSONDecodeError, IOError, FileNotFoundError):
            return None

        if single.get("disabled"):
            return {"disabled": True}

        return {
            "sessions": [{
                "session_id": single.get("session_id", "?"),
                "task": single.get("task", {}).get("name", "Idle"),
                "context_pct": single.get("context", {}).get("percentage", 0),
                "agents": single.get("agents", {}).get("active", 0),
                "status": "active",
                "updated_at": single.get("updated_at", ""),
            }],
            "summary": {
                "total_sessions": 1, "active_sessions": 1, "stale_sessions": 0,
                "total_agents": single.get("agents", {}).get("active", 0),
                "max_context_pct": single.get("context", {}).get("percentage", 0),
                "load": single.get("load", {}),
            },
        }

    # --- Icon Update ---

    def _update_icon(self, context_pct):
        icon_path, is_template = self.icon_gen.generate(context_pct)
        if icon_path:
            self.icon = icon_path
            self.template = is_template

    # --- Context Forecast ---

    def _context_forecast(self, ctx_pct):
        """Estimate time until 90% context based on recent trend."""
        now = time.time()
        self._ctx_history.append((now, ctx_pct))
        self._ctx_history = self._ctx_history[-12:]  # 60s of data at 5s polls

        if len(self._ctx_history) < 3 or ctx_pct >= 90 or ctx_pct == 0:
            return ""

        oldest_t, oldest_pct = self._ctx_history[0]
        dt = now - oldest_t
        dpct = ctx_pct - oldest_pct
        if dt < 10 or dpct <= 0:
            return ""

        rate = dpct / dt
        remaining = 90 - ctx_pct
        eta = remaining / rate

        if eta > 7200:
            return ""
        elif eta > 3600:
            return f" (~{int(eta / 3600)}h to 90%)"
        else:
            return f" (~{int(eta / 60)}m to 90%)"

    # --- CTM Task Display ---

    def _update_ctm(self):
        """Read current CTM task from scheduler."""
        try:
            if not CTM_SCHEDULER.exists():
                self.ctm_item.title = "\U0001f3af CTM: No active task"
                return
            with open(CTM_SCHEDULER) as f:
                sched = json.load(f)
            active_id = sched.get("active_agent") or ""
            if not active_id or active_id == "null":
                self.ctm_item.title = "\U0001f3af CTM: No active task"
                return
            title = active_id
            if CTM_INDEX.exists():
                with open(CTM_INDEX) as f:
                    idx = json.load(f)
                title = idx.get("agents", {}).get(active_id, {}).get("title", active_id)
            if len(title) > 35:
                title = title[:32] + "\u2026"
            queue_len = len(sched.get("priority_queue", []))
            queued = f" (+{queue_len - 1} queued)" if queue_len > 1 else ""
            self.ctm_item.title = f"\U0001f3af {title}{queued}"
        except (json.JSONDecodeError, IOError, FileNotFoundError, KeyError):
            self.ctm_item.title = "\U0001f3af CTM: -"

    # --- Main Update Loop ---

    def update_status(self, _):
        """Poll index.json and update display."""
        try:
            self._check_config_reload()
            self._update_ctm()

            index_data = self._load_index()

            if not index_data:
                self.title = "\u2014"
                self.icon = None
                self._clear_menu()
                return

            if index_data.get("disabled"):
                self.title = "Claude: Privacy"
                return

            self.index_data = index_data
            sessions = index_data.get("sessions", [])
            summary = index_data.get("summary", {})
            active_count = summary.get("active_sessions", len(sessions))
            max_ctx = summary.get("max_context_pct", 0)

            self._update_icon(max_ctx)
            self.notifier.check_and_notify(index_data)

            # Staleness check
            is_stale = False
            if sessions:
                updated_str = sessions[0].get("updated_at", "")
                if updated_str:
                    try:
                        updated_at = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
                        age = (datetime.now(timezone.utc) - updated_at).total_seconds()
                        is_stale = age > STALE_THRESHOLD
                    except (ValueError, TypeError):
                        pass

            if active_count == 0:
                self.title = "\u2014"
                self.icon = None
                self._clear_menu()
                return

            if active_count == 1 and sessions:
                s = sessions[0]
                task_name = s.get("task", "Idle")
                if self.privacy_mode:
                    task_name = "\u2022\u2022\u2022"
                elif len(task_name) > 18:
                    task_name = task_name[:15] + "\u2026"
                agent_count = s.get("agents", 0)
                agent_txt = f" \u00b7 {agent_count}a" if agent_count else ""
                self.title = f"{task_name}{agent_txt}"
            else:
                total_agents = summary.get("total_agents", 0)
                self.title = f"{active_count}s \u00b7 {total_agents}a"

            self._update_menu_multi(sessions, summary, is_stale)
            self._update_approvals()
            self._update_history()

        except Exception as e:
            self.title = "Claude: Error"
            logger.error("Update failed: %s", e, exc_info=True)

    # --- Menu Helpers ---

    def _clear_menu(self):
        self.task_item.title = "\U0001f4cb No active sessions"
        self.context_item.title = "\U0001f9e0 Context: -"
        self.agents_item.title = "\U0001f916 Agents: -"
        self.load_item.title = "\u26a1 Load: -"
        self.session_item.title = "\U0001f5c2 Active Sessions"
        self._clear_dynamic_items()

    def _clear_dynamic_items(self):
        for item in self._session_items:
            try:
                if item.title in self.menu:
                    del self.menu[item.title]
            except (KeyError, RuntimeError):
                pass
        self._session_items = []

    def _update_menu_multi(self, sessions, summary, is_stale):
        load = summary.get("load", {})
        active = summary.get("active_sessions", 0)
        stale_count = summary.get("stale_sessions", 0)

        stale_txt = f" \u00b7 {stale_count} stale" if stale_count else ""
        self.task_item.title = f"\U0001f4cb {active} active{stale_txt}"

        ctx_max = summary.get("max_context_pct", 0)
        ctx_dot = "\U0001f7e2" if ctx_max < 50 else "\U0001f7e1" if ctx_max < 80 else "\U0001f534"
        ctx_bar = self._context_bar(ctx_max)
        forecast = self._context_forecast(ctx_max)
        self.context_item.title = f"\U0001f9e0 {ctx_dot} {ctx_bar} {ctx_max}%{forecast}"

        agent_count = summary.get("total_agents", 0)
        self.agents_item.title = f"\U0001f916 {agent_count} agent{'s' if agent_count != 1 else ''} running"

        ls = load.get("status", "OK")
        ldot = {"OK": "\U0001f7e2", "CAUTION": "\U0001f7e1", "HIGH_LOAD": "\U0001f534"}.get(ls, "\u26aa")
        avg = load.get("load_avg", 0.0)
        profile = load.get("profile", "?")
        self.load_item.title = f"\u26a1 {ldot} {ls} \u00b7 {avg:.1f} avg \u00b7 {profile}"

        # Per-session submenus
        self._clear_dynamic_items()
        max_shown = self.config.get("menu", {}).get("max_sessions_shown", 5)
        quick_actions = self.config.get("menu", {}).get("enable_quick_actions", True)

        for s in sessions[:max_shown]:
            sid = s.get("session_id", "?")
            sid_short = sid[:8]
            task = "[redacted]" if self.privacy_mode else s.get("task", "Idle")
            ctx = s.get("context_pct", 0)
            agents = s.get("agents", 0)
            s_icon = "\U0001f7e2" if s.get("status") == "active" else "\u26aa"

            parent_title = f"  {s_icon} {sid_short}: {task[:25]} | {ctx}% | {agents}a"
            parent = rumps.MenuItem(parent_title)

            full_task = rumps.MenuItem(f"\U0001f4dd {task}")
            ctx_bar = self._context_bar(ctx)
            ctx_dot = "\U0001f7e2" if ctx < 50 else "\U0001f7e1" if ctx < 80 else "\U0001f534"
            ctx_item = rumps.MenuItem(f"\U0001f9e0 {ctx_dot} {ctx_bar} {ctx}%")

            parent[full_task.title] = full_task
            parent[ctx_item.title] = ctx_item

            if self.config.get("menu", {}).get("show_agent_names", True):
                agent_names = s.get("agent_names", [])
                if agent_names:
                    names_str = ", ".join(agent_names[:5])
                    agent_item = rumps.MenuItem(f"\U0001f916 {names_str}")
                    parent[agent_item.title] = agent_item

            if quick_actions:
                sep = rumps.MenuItem("\u2500" * 20)
                parent[sep.title] = sep
                dash_cb = self._make_dashboard_callback(sid)
                parent[rumps.MenuItem("\U0001f310 Open in Dashboard", callback=dash_cb).title] = rumps.MenuItem("\U0001f310 Open in Dashboard", callback=dash_cb)
                copy_cb = self._make_copy_callback(sid)
                parent[rumps.MenuItem("\U0001f4cb Copy Session ID", callback=copy_cb).title] = rumps.MenuItem("\U0001f4cb Copy Session ID", callback=copy_cb)

            self._session_items.append(parent)

        for item in reversed(self._session_items):
            try:
                self.menu.insert_after(self.session_item.title, item)
            except Exception:
                pass

        total = summary.get("total_sessions", 0)
        stale_info = " \u23f3" if is_stale else ""
        self.session_item.title = f"\U0001f5c2 {total} session{'s' if total != 1 else ''}{stale_info}"
        self.privacy_item.state = self.privacy_mode

    def _context_bar(self, pct):
        filled = int(pct / 10)
        return "[" + "\u2588" * filled + "\u2591" * (10 - filled) + "]"

    # --- Session History ---

    def _update_history(self):
        """Show last 5 completed sessions."""
        for key in list(self.history_menu.keys()):
            try:
                del self.history_menu[key]
            except (KeyError, RuntimeError):
                pass

        history = self.notifier._state.get("session_history", [])
        if not history:
            item = rumps.MenuItem("No recent sessions")
            self.history_menu[item.title] = item
            return

        for h in history[:5]:
            task = h.get("task", "Unknown")[:30]
            ts = h.get("completed_at", "?")
            item = rumps.MenuItem(f"{task} ({ts})")
            self.history_menu[item.title] = item

    # --- Profile Switcher ---

    def _rebuild_profiles(self):
        """Build profile submenu items from machine-profile.json SSOT."""
        current = "balanced"
        profile_names = []
        profile_meta = {
            "balanced": ("\u2696\ufe0f", "Default \u2014 general work"),
            "aggressive": ("\U0001f680", "More agents \u2014 higher limits"),
            "performance": ("\U0001f680", "More agents \u2014 higher limits"),
            "conservative": ("\U0001f6e1\ufe0f", "Light load \u2014 multitasking"),
        }
        try:
            if PROFILE_PATH.exists():
                with open(PROFILE_PATH) as f:
                    mp = json.load(f)
                current = mp.get("active_profile", "balanced")
                profile_names = list(mp.get("profiles", {}).keys())
        except (json.JSONDecodeError, IOError, FileNotFoundError):
            pass

        if not profile_names:
            profile_names = ["balanced", "aggressive", "conservative"]

        for item in self._profile_items:
            try:
                if item.title in self.profile_menu:
                    del self.profile_menu[item.title]
            except (KeyError, RuntimeError):
                pass
        self._profile_items = []

        for p in profile_names:
            emoji, desc = profile_meta.get(p, ("", p))
            check = "\u25c9 " if p == current else "\u25cb "
            cb = self._make_profile_callback(p)
            item = rumps.MenuItem(f"{check}{emoji} {p.capitalize()}", callback=cb)
            self.profile_menu[item.title] = item
            self._profile_items.append(item)

    def _make_profile_callback(self, profile_name):
        def callback(_):
            try:
                subprocess.Popen(
                    [str(SWITCH_PROFILE_SCRIPT), profile_name],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                try:
                    rumps.notification("Profile Switched", f"Now using: {profile_name}", "", sound=False)
                except RuntimeError:
                    pass
                self._rebuild_profiles()
            except Exception as e:
                logger.error("Profile switch error: %s", e)
        return callback

    # --- Approvals ---

    def _update_approvals(self):
        for item in self._approval_items:
            try:
                if item.title in self.approvals_menu:
                    del self.approvals_menu[item.title]
            except (KeyError, RuntimeError):
                pass
        self._approval_items = []

        pending = []
        try:
            if APPROVALS_DIR.exists():
                for f in APPROVALS_DIR.glob("*.json"):
                    try:
                        with open(f) as fh:
                            data = json.load(fh)
                        if data.get("status") == "pending":
                            pending.append((data, f))
                    except (json.JSONDecodeError, IOError):
                        continue
        except Exception:
            pass

        count = len(pending)
        self.approvals_menu.title = f"\U0001f6a8 {count} Pending" if count else "\u2705 No Approvals"

        if count == 0:
            item = rumps.MenuItem("\u2705 All clear")
            self.approvals_menu[item.title] = item
            self._approval_items.append(item)
        else:
            for a, filepath in pending[:5]:
                title = a.get("title", "Untitled")[:35]
                tid = a.get("task_id", "?")[:8]
                cb = self._make_approval_callback(a.get("task_id", ""), filepath)
                item = rumps.MenuItem(f"\u26a0\ufe0f {tid}: {title}", callback=cb)
                self.approvals_menu[item.title] = item
                self._approval_items.append(item)

    def _make_approval_callback(self, task_id, filepath):
        def callback(_):
            try:
                with open(filepath) as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError):
                rumps.alert("Error", "Could not read approval file.")
                return

            title = data.get("title", "Untitled")
            prompt = data.get("prompt", "No description")[:300]

            response = rumps.alert(
                title=f"Approve: {title}?",
                message=f"Task ID: {task_id}\n\n{prompt}\n\nClick OK to approve, Cancel to deny.",
                ok="Approve",
                cancel="Deny",
            )

            if response == 1:
                data["status"] = "approved"
                data["approved_at"] = datetime.now(timezone.utc).isoformat()
            else:
                data["status"] = "denied"
                data["denied_at"] = datetime.now(timezone.utc).isoformat()

            try:
                tmp = filepath.with_suffix(".tmp")
                with open(tmp, "w") as f:
                    json.dump(data, f, indent=2)
                tmp.replace(filepath)
            except IOError:
                rumps.alert("Error", "Could not write approval result.")

            self._update_approvals()
        return callback

    # --- Quick Action Callbacks ---

    def _make_dashboard_callback(self, session_id):
        def callback(_):
            subprocess.Popen(["open", f"http://localhost:8420?session={session_id}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return callback

    def _make_copy_callback(self, session_id):
        def callback(_):
            subprocess.run(["pbcopy"], input=session_id.encode(), check=False)
            try:
                rumps.notification("Copied", "Session ID copied to clipboard", session_id[:16], sound=False)
            except RuntimeError:
                pass
        return callback

    # --- Standard Actions ---

    def open_dashboard(self, _):
        subprocess.Popen(["open", "http://localhost:8420"])

    def open_new_session(self, _):
        """Open a new Claude session in iTerm2 (preferred) or Terminal.app."""
        try:
            # Check if iTerm2 is running
            result = subprocess.run(["pgrep", "-x", "iTerm2"], capture_output=True, timeout=2)
            if result.returncode == 0:
                subprocess.Popen([
                    "osascript", "-e",
                    'tell application "iTerm2" to create window with default profile command "claude"'
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen([
                    "osascript", "-e",
                    'tell application "Terminal" to do script "claude"'
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            logger.error("New session error: %s", e)

    def force_refresh(self, _):
        self._config_mtime = 0  # Force config reload
        self._profile_mtime = 0
        self._rebuild_profiles()
        self.update_status(None)

    def toggle_privacy(self, sender):
        self.privacy_mode = not self.privacy_mode
        sender.state = self.privacy_mode
        self.update_status(None)


if __name__ == "__main__":
    ClaudeStatusBar().run()
