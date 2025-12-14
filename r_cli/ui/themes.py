"""
Visual themes for R CLI.

Available themes:
- ps2: Inspired by PlayStation 2 (blue, particles)
- matrix: Green on black Matrix style
- minimal: Clean and simple
- retro: Vintage CRT colors
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Theme:
    """Visual theme definition."""

    name: str
    primary: str  # Primary color (Rich markup)
    secondary: str  # Secondary color
    accent: str  # Accent color
    success: str  # Success color
    error: str  # Error color
    warning: str  # Warning color
    dim: str  # Dimmed color
    background: Optional[str] = None  # If applicable

    # Symbols
    prompt_symbol: str = "❯"
    thinking_symbol: str = "◉"
    success_symbol: str = "✓"
    error_symbol: str = "✗"
    bullet_symbol: str = "•"


# Predefined themes
THEMES = {
    "ps2": Theme(
        name="ps2",
        primary="bold blue",
        secondary="cyan",
        accent="bright_blue",
        success="green",
        error="red",
        warning="yellow",
        dim="dim white",
        prompt_symbol="▶",
        thinking_symbol="◈",
    ),
    "matrix": Theme(
        name="matrix",
        primary="bold green",
        secondary="bright_green",
        accent="green",
        success="bright_green",
        error="red",
        warning="yellow",
        dim="dim green",
        prompt_symbol="$",
        thinking_symbol="●",
    ),
    "minimal": Theme(
        name="minimal",
        primary="bold white",
        secondary="white",
        accent="cyan",
        success="green",
        error="red",
        warning="yellow",
        dim="dim",
        prompt_symbol=">",
        thinking_symbol="·",
    ),
    "retro": Theme(
        name="retro",
        primary="bold magenta",
        secondary="cyan",
        accent="yellow",
        success="green",
        error="red",
        warning="bright_yellow",
        dim="dim magenta",
        prompt_symbol="►",
        thinking_symbol="◆",
    ),
    "cyberpunk": Theme(
        name="cyberpunk",
        primary="bold bright_magenta",
        secondary="bright_cyan",
        accent="bright_yellow",
        success="bright_green",
        error="bright_red",
        warning="bright_yellow",
        dim="dim magenta",
        prompt_symbol="»",
        thinking_symbol="◎",
    ),
}


def get_theme(name: str) -> Theme:
    """Get a theme by name."""
    return THEMES.get(name, THEMES["ps2"])


def list_themes() -> list[str]:
    """List available themes."""
    return list(THEMES.keys())
