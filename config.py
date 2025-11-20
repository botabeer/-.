# ============================================
# config.py - الإعدادات العامة للبوت
# ============================================

"""
إعدادات بوت الحوت
==================
إعدادات عامة وتوكنات وإعدادات البيئة
لا يحتوي على قوانين أو ألوان (موجودة في ملفات منفصلة)
"""

import os
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

# إعدادات LINE Bot
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', '')

# إعدادات قاعدة البيانات
DATABASE_NAME = 'whale_bot.db'
DATABASE_PATH = os.path.join(os.path.dirname(__file__), DATABASE_NAME)

# إعدادات الخادم
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
HOST = '0.0.0.0'

# إعدادات السجل (Logging)
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# إعدادات الأمان
MAX_MESSAGE_LENGTH = 500
MAX_USERNAME_LENGTH = 50

# مسارات ملفات البيانات
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
CHALLENGES_FILE = os.path.join(DATA_DIR, 'challenges.txt')
CONFESSIONS_FILE = os.path.join(DATA_DIR, 'confessions.txt')
MENTIONS_FILE = os.path.join(DATA_DIR, 'mentions.txt')
QUESTIONS_FILE = os.path.join(DATA_DIR, 'questions.txt')

# إعدادات الجلسة
SESSION_TIMEOUT = 3600  # ساعة واحدة بالثواني
CLEANUP_INTERVAL = 300  # تنظيف الجلسات كل 5 دقائق

# إعدادات التخزين المؤقت
CACHE_ENABLED = True
CACHE_TTL = 300  # 5 دقائق

# الأوامر المسموحة (الكلمات المفتاحية)
ALLOWED_COMMANDS = {
    'start': ['ابدأ', 'start', 'بدء', 'هاي'],
    'help': ['مساعدة', 'help', 'ساعدني'],
    'stats': ['نقاطي', 'احصائياتي', 'إحصائياتي'],
    'leaderboard': ['الصدارة', 'المتصدرين', 'الترتيب'],
    'stop': ['إيقاف', 'stop', 'ايقاف', 'توقف'],
    'hint': ['لمح', 'تلميح'],
    'answer': ['جاوب', 'الجواب', 'الحل'],
    'join': ['انضم', 'join', 'دخول'],
    'leave': ['انسحب', 'leave', 'خروج'],
    'replay': ['إعادة', 'اعادة', 'مرة أخرى']
}

# قائمة الألعاب المتاحة
AVAILABLE_GAMES = {
    'اسرع': 'FastTypingGame',
    'لعبة': 'HumanAnimalPlantGame',
    'سلسلة': 'ChainWordsGame',
    'اغنية': 'SongGame',
    'ضد': 'OppositeGame',
    'ترتيب': 'OrderGame',
    'تكوين': 'LettersWordsGame',
    'توافق': 'CompatibilityGame',
    'ai': 'AiChat'
}

# المحتوى الترفيهي
ENTERTAINMENT_COMMANDS = {
    'سؤال': QUESTIONS_FILE,
    'منشن': MENTIONS_FILE,
    'اعتراف': CONFESSIONS_FILE,
    'تحدي': CHALLENGES_FILE
}

# رسائل النظام العامة
MESSAGES = {
    'welcome': 'مرحباً بك في بوت الحوت! استخدم "ابدأ" لبدء اللعبة',
    'not_registered': 'يرجى التسجيل أولاً باستخدام "انضم"',
    'already_registered': 'أنت مسجل بالفعل',
    'no_active_game': 'لا توجد لعبة نشطة حالياً',
    'game_in_progress': 'يوجد لعبة قيد التقدم بالفعل',
    'invalid_command': 'أمر غير صحيح، استخدم "مساعدة" لرؤية الأوامر المتاحة',
    'error': 'حدث خطأ، يرجى المحاولة مرة أخرى',
    'timeout': 'انتهى الوقت المحدد',
    'game_stopped': 'تم إيقاف اللعبة',
    'joined': 'تم الانضمام بنجاح',
    'left': 'تم الانسحاب بنجاح'
}

# إعدادات إضافية
TIMEZONE = 'Asia/Riyadh'
LANGUAGE = 'ar'
ENCODING = 'utf-8'

# التحقق من وجود التوكنات المطلوبة
def validate_config():
    """التحقق من وجود التوكنات الضرورية"""
    if not LINE_CHANNEL_ACCESS_TOKEN:
        raise ValueError("LINE_CHANNEL_ACCESS_TOKEN is not set")
    if not LINE_CHANNEL_SECRET:
        raise ValueError("LINE_CHANNEL_SECRET is not set")
    return True

# تشغيل التحقق عند الاستيراد في بيئة الإنتاج
if not DEBUG:
    try:
        validate_config()
    except ValueError as e:
        print(f"Configuration Error: {e}")
