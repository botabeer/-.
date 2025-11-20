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
POINTS = {'correct': 10, 'hint': -2, 'skip': 0}
ROUNDS = 5
TIMEOUT = 30

# Available Games
GAMES = {
    'اسرع': {
        'name': 'أسرع إجابة',
        'file': 'fastest.txt',
        'hint': False,
        'skip': False
    },
    'لعبة': {
        'name': 'إنسان حيوان نبات',
        'file': 'categories.txt',
        'hint': True,
        'skip': True
    },
    'سلسلة': {
        'name': 'سلسلة الكلمات',
        'file': 'chain.txt',
        'hint': True,
        'skip': True
    },
    'اغنية': {
        'name': 'تكملة الأغنية',
        'file': 'songs.txt',
        'hint': True,
        'skip': True
    },
    'ضد': {
        'name': 'عكس الكلمة',
        'file': 'opposites.txt',
        'hint': True,
        'skip': True
    },
    'ترتيب': {
        'name': 'ترتيب الحروف',
        'file': 'arrange.txt',
        'hint': True,
        'skip': True
    },
    'تكوين': {
        'name': 'تكوين كلمات',
        'file': 'formation.txt',
        'hint': True,
        'skip': True
    },
    'توافق': {
        'name': 'توافق الأفكار',
        'file': 'matching.txt',
        'hint': False,
        'skip': False
    }
}

# Content Commands
CONTENT = {
    'سؤال': 'questions.txt',
    'منشن': 'mentions.txt',
    'تحدي': 'challenges.txt',
    'اعتراف': 'confessions.txt'
}

# Bot Commands
CMD = {
    'start': ['ابدأ', 'start', 'بدء'],
    'help': ['مساعدة', 'help', 'ساعدني'],
    'stats': ['نقاطي', 'احصائياتي', 'احصائيات'],
    'ranks': ['الصدارة', 'المتصدرين', 'الترتيب'],
    'stop': ['إيقاف', 'ايقاف', 'توقف', 'stop'],
    'hint': ['لمح', 'تلميح', 'hint'],
    'skip': ['تخطي', 'تخطى', 'skip'],
}

# Messages
MSG = {
    'welcome': 'مرحباً في بوت الحوت',
    'no_game': 'لا توجد لعبة نشطة حالياً',
    'game_active': 'يوجد لعبة نشطة بالفعل',
    'stopped': 'تم إيقاف اللعبة',
    'invalid': 'أمر غير صحيح',
    'error': 'حدث خطأ، يرجى المحاولة لاحقاً',
    'correct': 'إجابة صحيحة',
    'wrong': 'إجابة خاطئة',
    'timeout': 'انتهى الوقت',
    'game_end': 'انتهت اللعبة',
    'no_players': 'لا يوجد لاعبون'
}

# UI Settings
MAX_INPUT = 500
LEADERBOARD_SIZE = 10

# Logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# Developer Info
DEVELOPER = 'عبير الدوسري - 2025'
VERSION = '1.0.0'
