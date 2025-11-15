"""إعدادات البوت الموحدة"""
import os

# LINE Bot
LINE_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
LINE_SECRET = os.getenv('LINE_CHANNEL_SECRET', '')

# Gemini AI
GEMINI_KEYS = [
    os.getenv('GEMINI_API_KEY_1', ''),
    os.getenv('GEMINI_API_KEY_2', ''),
    os.getenv('GEMINI_API_KEY_3', '')
]
GEMINI_KEYS = [k for k in GEMINI_KEYS if k]
GEMINI_MODEL = 'gemini-2.0-flash-exp'

# قاعدة البيانات
DB_NAME = 'game_scores.db'

# نظام النقاط
POINTS = {
    'correct': 10,
    'hint': -2,
    'show_answer': -5,
    'perfect_bonus': 20
}

# الألوان (أسود/رمادي/أبيض)
COLORS = {
    'primary': '#000000',
    'secondary': '#666666',
    'light': '#F5F5F5',
    'white': '#FFFFFF',
    'border': '#E5E5E5'
}

# Rate Limiting
RATE_LIMIT = {'max': 30, 'window': 60}
