"""
Whale Bot Configuration
=======================
All project settings and constants
"""

import os
from dotenv import load_dotenv

load_dotenv()

# LINE Bot Credentials
LINE_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
LINE_SECRET = os.getenv('LINE_CHANNEL_SECRET', '')

# Server Settings
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
HOST = '0.0.0.0'

# Database
DB_PATH = 'whale_bot.db'

# File Paths
DATA_DIR = 'data'
GAMES_DIR = 'games'

# Game Rules
POINTS = {'correct': 2, 'hint': -1, 'answer': 0}
ROUNDS = 5
TIMEOUT = 30

# Available Games
GAMES = {
    'اسرع': {'name': 'أسرع', 'hint': False, 'answer': False},
    'لعبة': {'name': 'إنسان حيوان نبات', 'hint': True, 'answer': True},
    'سلسلة': {'name': 'سلسلة الكلمات', 'hint': True, 'answer': True},
    'اغنية': {'name': 'أغنية', 'hint': True, 'answer': True},
    'ضد': {'name': 'ضد', 'hint': True, 'answer': True},
    'ترتيب': {'name': 'ترتيب', 'hint': True, 'answer': True},
    'تكوين': {'name': 'تكوين كلمات', 'hint': True, 'answer': True},
    'توافق': {'name': 'توافق', 'hint': False, 'answer': False}
}

# Content Commands
CONTENT = ['سؤال', 'منشن', 'تحدي', 'اعتراف']

# Bot Commands
CMD = {
    'start': ['ابدأ', 'start'],
    'help': ['مساعدة', 'help'],
    'stats': ['نقاطي', 'احصائياتي'],
    'ranks': ['الصدارة', 'المتصدرين'],
    'stop': ['إيقاف', 'ايقاف'],
    'hint': ['لمح', 'تلميح'],
    'answer': ['جاوب', 'الحل'],
    'join': ['انضم'],
    'leave': ['انسحب']
}

# Messages
MSG = {
    'welcome': 'مرحباً في بوت الحوت',
    'no_game': 'لا توجد لعبة نشطة',
    'game_active': 'يوجد لعبة نشطة بالفعل',
    'stopped': 'تم إيقاف اللعبة',
    'invalid': 'أمر غير صحيح',
    'error': 'حدث خطأ'
}

# UI Settings
MAX_INPUT = 500
LEADERBOARD_SIZE = 10

# Logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# Developer Info
DEVELOPER = 'عبير الدوسري - 2025'
