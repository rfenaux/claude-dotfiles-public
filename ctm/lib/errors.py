"""
CTM Error Handling

Provides structured error handling with:
- Error codes and categories
- Graceful degradation strategies
- Recovery actions
- User-friendly error messages

Error codes follow the pattern CTM-XXX where:
- CTM-0XX: Configuration errors
- CTM-1XX: Agent errors
- CTM-2XX: Scheduler errors
- CTM-3XX: Memory errors
- CTM-4XX: Integration errors
- CTM-5XX: Hook errors
"""

import json
import traceback
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum

from config import get_ctm_dir


class ErrorSeverity(Enum):
    LOW = "low"           # Cosmetic, doesn't affect functionality
    MEDIUM = "medium"     # Degraded functionality, workaround exists
    HIGH = "high"         # Feature broken, needs attention
    CRITICAL = "critical" # System unusable, immediate action needed


@dataclass
class CTMError:
    """Structured CTM error."""
    code: str
    message: str
    severity: ErrorSeverity
    details: Optional[str] = None
    recovery_hint: Optional[str] = None
    timestamp: Optional[str] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity.value,
            "details": self.details,
            "recovery_hint": self.recovery_hint,
            "timestamp": self.timestamp
        }

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


# Error catalog
ERROR_CATALOG = {
    # Configuration errors (0XX)
    "CTM-001": ("Config file not found", ErrorSeverity.MEDIUM, "Run 'ctm hooks install' to initialize"),
    "CTM-002": ("Config file corrupted", ErrorSeverity.HIGH, "Run 'ctm repair --config'"),
    "CTM-003": ("Invalid config value", ErrorSeverity.MEDIUM, "Check config.json syntax"),

    # Agent errors (1XX)
    "CTM-101": ("Agent not found", ErrorSeverity.LOW, "Check agent ID with 'ctm list --all'"),
    "CTM-102": ("Agent file corrupted", ErrorSeverity.HIGH, "Run 'ctm repair --agents'"),
    "CTM-103": ("Agent already exists", ErrorSeverity.LOW, "Use a different title"),
    "CTM-104": ("Agent state invalid", ErrorSeverity.MEDIUM, "Run 'ctm repair --agents'"),
    "CTM-105": ("Too many agents", ErrorSeverity.MEDIUM, "Complete or cancel some agents"),

    # Scheduler errors (2XX)
    "CTM-201": ("Scheduler state corrupted", ErrorSeverity.HIGH, "Run 'ctm repair --scheduler'"),
    "CTM-202": ("Priority calculation failed", ErrorSeverity.MEDIUM, "Queue will use default order"),
    "CTM-203": ("No active agent", ErrorSeverity.LOW, "Use 'ctm spawn' to create one"),

    # Memory errors (3XX)
    "CTM-301": ("Working memory full", ErrorSeverity.MEDIUM, "Oldest agents will be evicted"),
    "CTM-302": ("Token budget exceeded", ErrorSeverity.MEDIUM, "Some context will be trimmed"),
    "CTM-303": ("Memory state corrupted", ErrorSeverity.HIGH, "Run 'ctm repair --memory'"),

    # Integration errors (4XX)
    "CTM-401": ("Project memory not found", ErrorSeverity.LOW, "Initialize with memory-init skill"),
    "CTM-402": ("RAG not available", ErrorSeverity.LOW, "Indexing disabled for this project"),
    "CTM-403": ("Consolidation failed", ErrorSeverity.MEDIUM, "Check project permissions"),
    "CTM-404": ("DECISIONS.md not writable", ErrorSeverity.MEDIUM, "Check file permissions"),

    # Hook errors (5XX)
    "CTM-501": ("Hook not installed", ErrorSeverity.LOW, "Run 'ctm hooks install'"),
    "CTM-502": ("Hook execution failed", ErrorSeverity.MEDIUM, "Check hook script permissions"),
    "CTM-503": ("Hook timeout", ErrorSeverity.MEDIUM, "Hook took too long, skipped"),

    # Index errors (6XX)
    "CTM-601": ("Index corrupted", ErrorSeverity.HIGH, "Run 'ctm repair --index'"),
    "CTM-602": ("Index out of sync", ErrorSeverity.MEDIUM, "Run 'ctm repair --index'"),
}


def create_error(code: str, details: Optional[str] = None) -> CTMError:
    """Create a CTMError from the catalog."""
    if code in ERROR_CATALOG:
        message, severity, hint = ERROR_CATALOG[code]
        return CTMError(
            code=code,
            message=message,
            severity=severity,
            details=details,
            recovery_hint=hint
        )
    else:
        return CTMError(
            code=code,
            message="Unknown error",
            severity=ErrorSeverity.MEDIUM,
            details=details,
            recovery_hint="Check logs for details"
        )


class ErrorLogger:
    """Logs errors to file for debugging."""

    def __init__(self):
        self.log_path = get_ctm_dir() / "logs" / "errors.log"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, error: CTMError, exception: Optional[Exception] = None) -> None:
        """Log an error to file."""
        entry = {
            **error.to_dict(),
            "exception": str(exception) if exception else None,
            "traceback": traceback.format_exc() if exception else None
        }

        with open(self.log_path, 'a') as f:
            f.write(json.dumps(entry) + "\n")

    def get_recent(self, count: int = 10) -> list:
        """Get recent errors."""
        if not self.log_path.exists():
            return []

        errors = []
        with open(self.log_path, 'r') as f:
            for line in f:
                try:
                    errors.append(json.loads(line))
                except:
                    pass

        return errors[-count:]

    def clear(self) -> None:
        """Clear error log."""
        if self.log_path.exists():
            self.log_path.unlink()


def handle_error(code: str, details: Optional[str] = None,
                 exception: Optional[Exception] = None,
                 silent: bool = False) -> CTMError:
    """
    Handle an error: create, log, and optionally print.

    Args:
        code: Error code from catalog
        details: Additional context
        exception: Python exception if any
        silent: If True, don't print to stdout

    Returns:
        CTMError instance
    """
    error = create_error(code, details)

    # Log to file
    logger = ErrorLogger()
    logger.log(error, exception)

    # Print unless silent
    if not silent:
        print(f"Error: {error}")
        if error.recovery_hint:
            print(f"  Hint: {error.recovery_hint}")

    return error


def safe_execute(func: Callable, fallback: Any = None,
                 error_code: str = "CTM-000") -> Any:
    """
    Execute a function with error handling.

    Args:
        func: Function to execute
        fallback: Value to return on error
        error_code: Error code to use if exception occurs

    Returns:
        Function result or fallback on error
    """
    try:
        return func()
    except Exception as e:
        handle_error(error_code, str(e), e, silent=True)
        return fallback


class GracefulDegradation:
    """
    Provides fallback behavior when components fail.
    """

    @staticmethod
    def get_config_or_default(key: str, default: Any) -> Any:
        """Get config value with fallback to default."""
        try:
            from config import load_config
            config = load_config()
            return config.get(key, default)
        except:
            return default

    @staticmethod
    def get_scheduler_or_none():
        """Get scheduler with fallback to None."""
        try:
            from scheduler import get_scheduler
            return get_scheduler()
        except:
            return None

    @staticmethod
    def get_agent_or_none(agent_id: str):
        """Get agent with fallback to None."""
        try:
            from agents import get_agent
            return get_agent(agent_id)
        except:
            return None

    @staticmethod
    def list_agents_or_empty(**kwargs) -> list:
        """List agents with fallback to empty list."""
        try:
            from agents import list_agents
            return list_agents(**kwargs)
        except:
            return []
