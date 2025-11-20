# ============================================
# rules.py - القوانين الثابتة للبوت
# ============================================

import os

# نظام النقاط
POINTS = {'correct': 2, 'hint': -1, 'answer': 0, 'skip': 0}

# إعدادات اللعبة
GAME_SETTINGS = {
    'rounds': 5,
    'inactive_days': 45,
    'min_players': 1,
    'time_per_question': 30
}

# إعدادات Gemini AI
GEMINI_CONFIG = {
    'api_keys': [
        os.getenv('GEMINI_API_KEY_1', ''),
        os.getenv('GEMINI_API_KEY_2', ''),
        os.getenv('GEMINI_API_KEY_3', '')
    ],
    'model': 'gemini-2.0-flash-exp',
    'temperature': 0.9,
    'max_tokens': 500,
    'system_instruction': 'أنت مساعد ذكي عربي ودود في بوت الحوت. تحدث بالعربية فقط، كن مختصراً وواضحاً، استخدم أسلوب ودي وممتع.'
}

# الألعاب الرئيسية
MAIN_GAMES = ['اسرع', 'لعبة', 'سلسلة', 'اغنية', 'ضد', 'ترتيب', 'تكوين', 'توافق']

# المحتوى الإضافي
EXTRA_CONTENT = ['سؤال', 'منشن', 'تحدي', 'اعتراف']

# معلومات الألعاب
GAMES_INFO = {
    'اسرع': {'name': 'أسرع', 'description': 'أول من يكتب الكلمة الصحيح يفوز', 'rounds': 5, 'supports_hint': False, 'supports_answer': False},
    'لعبة': {'name': 'لعبة', 'description': 'إنسان، حيوان، نبات، بلد', 'rounds': 5, 'supports_hint': True, 'supports_answer': True},
    'سلسلة': {'name': 'سلسلة الكلمات', 'description': 'كلمة تبدأ بالحرف الأخير', 'rounds': 5, 'supports_hint': True, 'supports_answer': True},
    'اغنية': {'name': 'أغنية', 'description': 'تخمين المغني من كلمات الأغنية', 'rounds': 5, 'supports_hint': True, 'supports_answer': True},
    'ضد': {'name': 'ضد', 'description': 'اعكس الكلمة المعطاة', 'rounds': 5, 'supports_hint': True, 'supports_answer': True},
    'ترتيب': {'name': 'ترتيب', 'description': 'ترتيب العناصر حسب المطلوب', 'rounds': 5, 'supports_hint': True, 'supports_answer': True},
    'تكوين': {'name': 'تكوين كلمات', 'description': 'تكوين 3 كلمات من 6 حروف', 'rounds': 5, 'supports_hint': True, 'supports_answer': True},
    'توافق': {'name': 'توافق', 'description': 'حساب نسبة التوافق بين اسمين', 'rounds': 1, 'supports_hint': False, 'supports_answer': False},
    'ai': {'name': 'محادثة ذكية', 'description': 'محادثة مع الذكاء الاصطناعي', 'rounds': 1, 'supports_hint': False, 'supports_answer': False}
}

# الأوامر
COMMANDS = {
    'start': ['ابدأ', 'start'], 'help': ['مساعدة', 'help'],
    'stats': ['نقاطي'], 'leaderboard': ['الصدارة'],
    'stop': ['إيقاف', 'ايقاف'], 'hint': ['لمح'],
    'answer': ['جاوب'], 'join': ['انضم'],
    'leave': ['انسحب'], 'replay': ['إعادة', 'اعادة']
}

# الرتب
RANK_NAMES = {i: f'المركز {["الأول","الثاني","الثالث","الرابع","الخامس","السادس","السابع","الثامن","التاسع","العاشر"][i-1]}' for i in range(1, 11)}

# قاعدة البيانات
DB_NAME = 'whale_bot.db'
RATE_LIMIT = {'max_requests': 20, 'window': 60}

# PostgreSQL
POSTGRES_CONFIG = {
    'enabled': os.getenv('USE_POSTGRES', 'False').lower() == 'true',
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'database': os.getenv('POSTGRES_DB', 'whale_bot'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', ''),
    'pool_size': 10, 'max_overflow': 20
}

# Redis
REDIS_CONFIG = {
    'enabled': os.getenv('USE_REDIS', 'False').lower() == 'true',
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'db': int(os.getenv('REDIS_DB', 0)),
    'password': os.getenv('REDIS_PASSWORD', None),
    'decode_responses': True, 'cache_ttl': 300
}

# المراقبة
MONITORING_CONFIG = {
    'enabled': os.getenv('ENABLE_MONITORING', 'False').lower() == 'true',
    'prometheus_port': int(os.getenv('PROMETHEUS_PORT', 8000)),
    'health_check_interval': 60
}

# النسخ الاحتياطي
BACKUP_CONFIG = {
    'enabled': os.getenv('ENABLE_BACKUP', 'False').lower() == 'true',
    'interval_hours': int(os.getenv('BACKUP_INTERVAL', 24)),
    'keep_days': int(os.getenv('BACKUP_KEEP_DAYS', 7)),
    'path': os.getenv('BACKUP_PATH', './backups')
}

# رسائل النظام
SYSTEM_MESSAGES = {
    'welcome': 'مرحباً بك في بوت الحوت',
    'game_started': 'بدأت اللعبة', 'game_ended': 'انتهت اللعبة',
    'correct_answer': 'إجابة صحيحة', 'wrong_answer': 'إجابة خاطئة',
    'no_active_game': 'لا توجد لعبة نشطة',
    'rate_limit': 'الرجاء الانتظار قليلاً',
    'error': 'حدث خطأ، يرجى المحاولة مرة أخرى'
}

# معلومات المطور
DEVELOPER_INFO = {
    'name': 'عبير الدوسري',
    'year': '2025',
    'copyright': 'تم إنشاء هذا البوت بواسطة عبير الدوسري - 2025'
}

# قوانين اللعب
GAME_RULES = """القوانين العامة:
- البوت يرد فقط على المستخدمين المسجلين
- كل لعبة تتكون من 5 جولات (ماعدا التوافق و AI)

نظام النقاط:
- إجابة صحيحة: +2
- طلب تلميح: -1
- طلب جاوب: 0

الأوامر المتاحة:
- لمح: تلميح ذكي للسؤال
- جاوب: عرض الإجابة والانتقال للتالي
- إعادة: إعادة تشغيل اللعبة الحالية
- إيقاف: إنهاء اللعبة الجارية
- نقاطي: عرض نقاطك
- الصدارة: عرض أفضل اللاعبين"""

DB_SCHEMA = '''
CREATE TABLE IF NOT EXISTS players (
    user_id TEXT PRIMARY KEY, name TEXT NOT NULL, points INTEGER DEFAULT 0,
    games_played INTEGER DEFAULT 0, games_won INTEGER DEFAULT 0,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS game_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
    game_type TEXT NOT NULL, points_earned INTEGER DEFAULT 0,
    result TEXT, played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES players(user_id)
);
CREATE INDEX IF NOT EXISTS idx_points ON players(points DESC);
CREATE INDEX IF NOT EXISTS idx_last_active ON players(last_active);
'''
