"""
CTM CLI Styling

Provides consistent styling for CLI output with:
- ANSI color codes
- Box drawing characters
- Status indicators
- Formatted tables
"""

import sys
from typing import Optional


# Check if terminal supports colors
def supports_color() -> bool:
    """Check if the terminal supports ANSI colors."""
    if not hasattr(sys.stdout, "isatty"):
        return False
    if not sys.stdout.isatty():
        return False
    return True


# ANSI color codes
class Colors:
    """ANSI escape codes for colors."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright foreground
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"


# Check once at import time
_USE_COLOR = supports_color()


def color(text: str, *codes: str) -> str:
    """Apply color codes to text if terminal supports it."""
    if not _USE_COLOR:
        return text
    return f"{''.join(codes)}{text}{Colors.RESET}"


def bold(text: str) -> str:
    """Make text bold."""
    return color(text, Colors.BOLD)


def dim(text: str) -> str:
    """Make text dim."""
    return color(text, Colors.DIM)


def success(text: str) -> str:
    """Style as success (green)."""
    return color(text, Colors.GREEN)


def error(text: str) -> str:
    """Style as error (red)."""
    return color(text, Colors.RED)


def warning(text: str) -> str:
    """Style as warning (yellow)."""
    return color(text, Colors.YELLOW)


def info(text: str) -> str:
    """Style as info (cyan)."""
    return color(text, Colors.CYAN)


def muted(text: str) -> str:
    """Style as muted (dim)."""
    return color(text, Colors.BRIGHT_BLACK)


# Status icons with colors
class Icons:
    """Status icons for CLI output."""
    SUCCESS = "✓"
    ERROR = "✗"
    WARNING = "⚠"
    INFO = "ℹ"
    ACTIVE = "▶"
    PAUSED = "⏸"
    BLOCKED = "⊘"
    COMPLETED = "✓"
    CANCELLED = "✗"
    PENDING = "○"
    ARROW = "→"
    BULLET = "•"


def status_icon(status: str) -> str:
    """Get colored icon for agent status."""
    icons = {
        "active": color(Icons.ACTIVE, Colors.GREEN),
        "paused": color(Icons.PAUSED, Colors.YELLOW),
        "blocked": color(Icons.BLOCKED, Colors.RED),
        "completed": color(Icons.COMPLETED, Colors.BRIGHT_BLACK),
        "cancelled": color(Icons.CANCELLED, Colors.BRIGHT_BLACK),
    }
    return icons.get(status, Icons.PENDING)


def priority_color(score: float) -> str:
    """Get color code based on priority score."""
    if score >= 0.8:
        return Colors.RED
    elif score >= 0.6:
        return Colors.YELLOW
    elif score >= 0.4:
        return Colors.GREEN
    else:
        return Colors.BRIGHT_BLACK


# Box drawing
def header(title: str) -> str:
    """Create a styled header."""
    line = "═" * (len(title) + 4)
    return f"{bold(line)}\n{bold('══')} {bold(title)} {bold('══')}\n{bold(line)}"


def section(title: str) -> str:
    """Create a styled section header."""
    return f"\n{bold(color(f'── {title} ──', Colors.CYAN))}"


def box(content: str, title: Optional[str] = None) -> str:
    """Create a box around content."""
    lines = content.split("\n")
    width = max(len(line) for line in lines) + 2

    top = f"╭{'─' * width}╮"
    if title:
        top = f"╭─ {title} {'─' * (width - len(title) - 3)}╮"
    bottom = f"╰{'─' * width}╯"

    boxed = [top]
    for line in lines:
        padding = width - len(line) - 1
        boxed.append(f"│ {line}{' ' * padding}│")
    boxed.append(bottom)

    return "\n".join(boxed)


# Progress bar
def progress_bar(pct: int, width: int = 20) -> str:
    """Create a progress bar."""
    filled = int(width * pct / 100)
    empty = width - filled

    bar = "█" * filled + "░" * empty

    if pct >= 80:
        bar = color(bar, Colors.GREEN)
    elif pct >= 50:
        bar = color(bar, Colors.YELLOW)
    else:
        bar = color(bar, Colors.BRIGHT_BLACK)

    return f"[{bar}] {pct}%"


# Table formatting
def table(rows: list, headers: Optional[list] = None) -> str:
    """Create a simple table."""
    if not rows:
        return ""

    # Calculate column widths
    all_rows = [headers] + rows if headers else rows
    num_cols = len(all_rows[0])
    widths = [0] * num_cols

    for row in all_rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    # Build table
    lines = []

    if headers:
        header_line = "  ".join(
            bold(str(h).ljust(widths[i])) for i, h in enumerate(headers)
        )
        lines.append(header_line)
        lines.append("─" * (sum(widths) + 2 * (num_cols - 1)))

    for row in rows:
        line = "  ".join(
            str(cell).ljust(widths[i]) for i, cell in enumerate(row)
        )
        lines.append(line)

    return "\n".join(lines)
