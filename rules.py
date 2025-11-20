# ============================================
# rules.py - القوانين الثابتة للبوت
# ============================================

"""
قوانين بوت الحوت
================
هذا الملف يحتوي على جميع القوانين الثابتة
لا يحتوي على ألوان أو ستايل
"""

# معلومات البوت
BOT_INFO = {
    'name': 'بوت الحوت',
    'version': '2.0.0',
    'developer': 'عبير الدوسري',
    'copyright': '©️ 2025',
    'description': 'بوت تفاعلي وترفيهي مدعوم بالذكاء الاصطناعي'
}

# نظام النقاط
POINTS = {
    'correct': 2,      # إجابة صحيحة
    'hint': -1,        # طلب تلميح
    'answer': 0,       # طلب جاوب
    'skip': 0          # تخطي
}

# إعدادات اللعبة
GAME_SETTINGS = {
    'rounds': 5,              # عدد الجولات
    'inactive_days': 45,      # أيام عدم النشاط قبل الحذف
    'min_players': 1,         # الحد الأدنى من اللاعبين
    'time_per_question': 30,  # الوقت لكل سؤال (ثانية)
    'max_hints': 3,           # عدد التلميحات المسموح بها
    'leaderboard_size': 10    # عدد اللاعبين في قائمة المتصدرين
}

# الألعاب المتوفرة مع أوصافها
GAMES_INFO = {
    'اسرع': {
        'name': 'أسرع',
        'description': 'أول من يكتب الكلمة أو الدعاء الصحيح يفوز',
        'rounds': 5,
        'supports_hint': False,
        'supports_answer': False,
        'difficulty': 'easy'
    },
    'لعبة': {
        'name': 'لعبة',
        'description': 'إنسان، حيوان، نبات، بلد',
        'rounds': 5,
        'supports_hint': True,
        'supports_answer': True,
        'difficulty': 'medium'
    },
    'سلسلة': {
        'name': 'سلسلة الكلمات',
        'description': 'كلمة تبدأ بالحرف الأخير من السابقة',
        'rounds': 5,
        'supports_hint': True,
        'supports_answer': True,
        'difficulty': 'medium'
    },
    'اغنية': {
        'name': 'أغنية',
        'description': 'تخمين المغني من كلمات الأغنية',
        'rounds': 5,
        'supports_hint': True,
        'supports_answer': True,
        'difficulty': 'hard'
    },
    'ضد': {
        'name': 'ضد',
        'description': 'اعكس الكلمة المعطاة',
        'rounds': 5,
        'supports_hint': True,
        'supports_answer': True,
        'difficulty': 'easy'
    },
    'ترتيب': {
        'name': 'ترتيب',
        'description': 'ترتيب العناصر حسب المطلوب',
        'rounds': 5,
        'supports_hint': True,
        'supports_answer': True,
        'difficulty': 'medium'
    },
    'تكوين': {
        'name': 'تكوين كلمات',
        'description': 'تكوين 3 كلمات من 6 حروف',
        'rounds': 5,
        'supports_hint': True,
        'supports_answer': True,
        'difficulty': 'hard'
    },
    'توافق': {
        'name': 'توافق',
        'description': 'حساب نسبة التوافق بين اسمين',
        'rounds': 1,
        'supports_hint': False,
        'supports_answer': False,
        'difficulty': 'fun'
    },
    'ai': {
        'name': 'محادثة ذكية',
        'description': 'محادثة مع الذكاء الاصطناعي Gemini',
        'rounds': 1,
        'supports_hint': False,
        'supports_answer': False,
        'difficulty': 'smart'
    }
}

# إعدادات Gemini AI
GEMINI_SETTINGS = {
    'model': 'gemini-2.0-flash-exp',
    'max_tokens': 500,
    'temperature': 0.7,
    'top_p': 0.9,
    'top_k': 40,
    'max_messages': 10,  # عدد الرسائل في المحادثة
    'api_keys': [
        'GEMINI_API_KEY_1',
        'GEMINI_API_KEY_2',
        'GEMINI_API_KEY_3'
    ],
    'system_prompt': """أنت مساعد ذكي وودود اسمك بوت الحوت. 
أنت تساعد المستخدمين بطريقة لطيفة ومحترمة.
- أجب باختصار وبشكل واضح
- استخدم اللغة العربية الفصحى
- كن مهذباً ولطيفاً
- تجنب المواضيع الحساسة
- ركز على المساعدة والترفيه"""
}

# الأوامر المتاحة
COMMANDS = {
    'start': ['ابدأ', 'start', 'بدء', 'هاي', 'السلام عليكم'],
    'help': ['مساعدة', 'help', 'ساعدني'],
    'stats': ['نقاطي', 'احصائياتي', 'إحصائياتي'],
    'leaderboard': ['الصدارة', 'المتصدرين', 'الترتيب'],
    'stop': ['إيقاف', 'stop', 'ايقاف', 'توقف'],
    'hint': ['لمح', 'تلميح'],
    'answer': ['جاوب', 'الجواب', 'الحل'],
    'join': ['انضم', 'join', 'دخول'],
    'leave': ['انسحب', 'leave', 'خروج'],
    'replay': ['إعادة', 'اعادة', 'مرة أخرى', 'العب مجددا']
}

# الرتب (بدون إيموجي)
RANK_NAMES = {
    1: 'المركز الأول',
    2: 'المركز الثاني',
    3: 'المركز الثالث',
    4: 'المركز الرابع',
    5: 'المركز الخامس',
    6: 'المركز السادس',
    7: 'المركز السابع',
    8: 'المركز الثامن',
    9: 'المركز التاسع',
    10: 'المركز العاشر'
}

# حدود الطلبات (Rate Limiting)
RATE_LIMIT = {
    'max_requests': 30,        # أقصى عدد طلبات
    'window': 60,              # في كم ثانية
    'block_duration': 300      # مدة الحظر (5 دقائق)
}

# إعدادات Redis (للتخزين المؤقت)
REDIS_SETTINGS = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'decode_responses': True,
    'cache_ttl': 3600,         # مدة التخزين (ساعة)
    'session_ttl': 7200        # مدة الجلسة (ساعتان)
}

# إعدادات PostgreSQL (للإنتاج)
POSTGRES_SETTINGS = {
    'host': 'localhost',
    'port': 5432,
    'database': 'whale_bot',
    'pool_size': 10,
    'max_overflow': 20,
    'pool_timeout': 30,
    'pool_recycle': 3600
}

# إعدادات النسخ الاحتياطي
BACKUP_SETTINGS = {
    'enabled': True,
    'interval': 'daily',       # daily, weekly, monthly
    'time': '03:00',          # وقت النسخ الاحتياطي
    'retention_days': 30,     # عدد الأيام للاحتفاظ بالنسخ
    'path': 'backups/',
    'compress': True
}

# إعدادات مراقبة الأداء
MONITORING_SETTINGS = {
    'enabled': True,
    'log_level': 'INFO',
    'metrics_interval': 60,    # ثانية
    'alert_threshold': {
        'cpu': 80,             # نسبة مئوية
        'memory': 85,          # نسبة مئوية
        'response_time': 2000  # ميلي ثانية
    }
}

# قاعدة البيانات
DB_NAME = 'whale_bot.db'

DB_SCHEMA = '''
CREATE TABLE IF NOT EXISTS players (
    user_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    points INTEGER DEFAULT 0,
    games_played INTEGER DEFAULT 0,
    games_won INTEGER DEFAULT 0,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS game_sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    game_type TEXT NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    total_points INTEGER DEFAULT 0,
    completed BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES players(user_id)
);

CREATE TABLE IF NOT EXISTS ai_conversations (
    conversation_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    message_count INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES players(user_id)
);

CREATE INDEX IF NOT EXISTS idx_players_points ON players(points DESC);
CREATE INDEX IF NOT EXISTS idx_players_last_active ON players(last_active DESC);
CREATE INDEX IF NOT EXISTS idx_game_sessions_user ON game_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_conversations_user ON ai_conversations(user_id);
'''

# رسائل النظام
SYSTEM_MESSAGES = {
    'welcome': f'''مرحباً بك في {BOT_INFO['name']}
{BOT_INFO['description']}
    
تم إنشاء هذا البوت بواسطة {BOT_INFO['developer']} {BOT_INFO['copyright']}''',
    
    'game_started': 'بدأت اللعبة',
    'game_ended': 'انتهت اللعبة',
    'correct_answer': 'إجابة صحيحة',
    'wrong_answer': 'إجابة خاطئة',
    'hint_used': 'تم استخدام التلميح',
    'answer_shown': 'الإجابة الصحيحة',
    'no_active_game': 'لا توجد لعبة نشطة',
    'already_registered': 'أنت مسجل بالفعل',
    'not_registered': 'يجب التسجيل أولاً',
    'rate_limit': 'الرجاء الانتظار قليلاً',
    'error': 'حدث خطأ، يرجى المحاولة مرة أخرى',
    'maintenance': 'البوت تحت الصيانة، يرجى المحاولة لاحقاً',
    'developer_credit': f'تم إنشاء هذا البوت بواسطة {BOT_INFO["developer"]} {BOT_INFO["copyright"]}'
}

# قوانين اللعب
GAME_RULES = f"""
{BOT_INFO['name']} - دليل الاستخدام
{'='*50}

القوانين العامة:
- البوت يرد فقط على المستخدمين المسجلين
- كل لعبة تتكون من 5 جولات (ماعدا التوافق و AI)
- بعد السؤال الخامس يتم إعلان الفائز مباشرة
- طلب جاوب يعطي الإجابة وينتقل للسؤال التالي

نظام النقاط:
- إجابة صحيحة: +2
- طلب تلميح: -1
- طلب جاوب: 0
- تخطي أو ألعاب ترفيهية: 0

الأوامر المتاحة:
- لمح: تلميح ذكي للسؤال
- جاوب: عرض الإجابة والانتقال للتالي
- إعادة: إعادة تشغيل اللعبة الحالية
- إيقاف: إنهاء اللعبة الجارية
- انضم: تسجيل في اللعبة
- انسحب: إلغاء التسجيل
- نقاطي: عرض نقاطك
- الصدارة: عرض أفضل اللاعبين

الألعاب المتاحة:
{chr(10).join([f'- {info["name"]}: {info["description"]}' for info in GAMES_INFO.values()])}

{'='*50}
{SYSTEM_MESSAGES['developer_credit']}
"""

# إعدادات Docker
DOCKER_SETTINGS = {
    'image_name': 'whale-bot',
    'version': BOT_INFO['version'],
    'port': 5000,
    'workers': 4,
    'timeout': 120
}

# إعدادات CI/CD
CICD_SETTINGS = {
    'auto_deploy': True,
    'run_tests': True,
    'test_coverage_min': 80,
    'environments': ['development', 'staging', 'production']
}

# إعدادات الاختبارات
TEST_SETTINGS = {
    'enabled': True,
    'framework': 'pytest',
    'coverage_report': True,
    'parallel_execution': True,
    'mock_external_apis': True
}

# الرسائل الترحيبية للمطور
DEVELOPER_MESSAGES = {
    'startup': f'''
{'='*60}
{BOT_INFO['name']} v{BOT_INFO['version']}
{'='*60}
Developer: {BOT_INFO['developer']}
Copyright: {BOT_INFO['copyright']}
Description: {BOT_INFO['description']}
{'='*60}
Starting bot...
''',
    'shutdown': f'''
{'='*60}
Shutting down {BOT_INFO['name']}...
Thank you for using {BOT_INFO['name']}!
{SYSTEM_MESSAGES['developer_credit']}
{'='*60}
'''
}

# إعدادات التحليلات
ANALYTICS_SETTINGS = {
    'enabled': True,
    'track_events': [
        'game_started',
        'game_completed',
        'message_sent',
        'error_occurred',
        'user_registered'
    ],
    'retention_days': 90
}

# الميزات المفعلة
FEATURES = {
    'games': True,
    'ai_chat': True,
    'leaderboard': True,
    'statistics': True,
    'entertainment': True,
    'redis_cache': False,      # سيتم تفعيلها في الإنتاج
    'postgres': False,         # سيتم تفعيلها في الإنتاج
    'monitoring': True,
    'backup': True,
    'rate_limiting': True
}
