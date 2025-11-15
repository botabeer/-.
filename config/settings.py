"""
Settings Configuration
Environment variables and app configurations
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LINE Bot Credentials
LINE_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
LINE_SECRET = os.getenv('LINE_CHANNEL_SECRET', '')

# Gemini AI Configuration
GEMINI_KEYS = []
gemini_key = os.getenv('GEMINI_API_KEY', '')
if gemini_key:
    GEMINI_KEYS = [gemini_key]

# Additional Gemini keys (if multiple keys available)
for i in range(2, 6):  # Support up to 5 keys
    key = os.getenv(f'GEMINI_API_KEY_{i}', '')
    if key:
        GEMINI_KEYS.append(key)

GEMINI_MODEL = 'gemini-pro'

# Color Scheme for Flex Messages
COLORS = {
    'primary': '#1E90FF',      # Primary blue
    'secondary': '#808080',    # Secondary gray
    'white': '#FFFFFF',        # White
    'light': '#F5F5F5',        # Light gray background
    'border': '#DDDDDD'        # Border color
}

# Rate Limiting Configuration
RATE_LIMIT = {
    'max': 10,        # Maximum messages per window
    'window': 60      # Time window in seconds
}

# Database Configuration (for future use)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///game_bot.db')

# Redis Configuration (for future use)
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

# Game Settings
GAME_SETTINGS = {
    'song_game': {
        'questions': 5,
        'hint_penalty': 5,
        'base_points': 20
    },
    'opposite_game': {
        'questions': 5,
        'hint_penalty': 3,
        'base_points': 15
    },
    'chain_words': {
        'rounds': 5,
        'points_per_word': 10
    },
    'fast_typing': {
        'time_limit': 30,
        'max_points': 20,
        'min_points': 5
    },
    'human_animal_plant': {
        'points_per_category': 3,
        'categories': 4
    },
    'letters_words': {
        'words_needed': 3,
        'points_per_word': 5
    },
    'compatibility': {
        'min_compatibility': 50,
        'max_compatibility': 100,
        'points': 5
    },
    'differences': {
        'differences_count': 5
    }
}

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Flask Configuration
FLASK_ENV = os.getenv('FLASK_ENV', 'production')
DEBUG = FLASK_ENV == 'development'
PORT = int(os.getenv('PORT', 5000))

# Game Cleanup Configuration
CLEANUP_INTERVAL = 300  # 5 minutes
GAME_TIMEOUT = 900      # 15 minutes

# File Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
GAMES_DIR = os.path.join(BASE_DIR, 'games')

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(GAMES_DIR, exist_ok=True)
