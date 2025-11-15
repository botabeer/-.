"""
Config Package
Contains all configuration and settings for the LINE Bot
"""

from .settings import (
    LINE_TOKEN,
    LINE_SECRET,
    GEMINI_KEYS,
    GEMINI_MODEL,
    COLORS,
    RATE_LIMIT
)

from .database import (
    init_db,
    update_points,
    get_stats,
    get_leaderboard
)

from .helpers import (
    normalize_text,
    load_file
)

__all__ = [
    'LINE_TOKEN',
    'LINE_SECRET',
    'GEMINI_KEYS',
    'GEMINI_MODEL',
    'COLORS',
    'RATE_LIMIT',
    'init_db',
    'update_points',
    'get_stats',
    'get_leaderboard',
    'normalize_text',
    'load_file'
]
