# config.py - إعدادات بوت الحوت المحسنة

import os

# ============= قاعدة البيانات =============

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
CREATE INDEX IF NOT EXISTS idx_points ON players(points DESC);
CREATE INDEX IF NOT EXISTS idx_last_active ON players(last_active);
'''

# ============= النقاط =============

POINTS = {
    'correct': 2,
    'hint': -1,
    'answer': 0,
    'skip': 0
}

# ============= إعدادات الألعاب =============

GAME_SETTINGS = {
    'rounds': 5,
    'fast_time': 30,
    'inactive_days': 45,
    'min_players': 1,
}

# ============= قائمة الألعاب =============

GAMES_LIST = [
    'fast',      # أسرع
    'lbgame',    # لعبة
    'chain',     # سلسلة
    'song',      # أغنية
    'opposite',  # ضد
    'order',     # ترتيب
    'build',     # تكوين
    'compat',    # توافق
]

# ============= الأوامر =============

CMDS = {
    'start': ['البداية', 'start', 'بدء'],
    'help': ['مساعدة', 'help', 'الأوامر'],
    'stats': ['نقاطي', 'احصائياتي', 'stats'],
    'leaderboard': ['الصدارة', 'leaderboard', 'top'],
    'join': ['انضم', 'join'],
    'leave': ['انسحب', 'leave'],
    'stop': ['إيقاف', 'stop', 'انهاء'],
    'hint': ['لمح', 'hint', 'تلميح'],
    'answer': ['جاوب', 'answer', 'الجواب'],
    'restart': ['إعادة', 'restart']
}

# ============= الرسائل =============

MESSAGES = {
    'welcome': '🐋 مرحباً بك في بوت الحوت!\nاكتب "مساعدة" لعرض الأوامر',
    'not_registered': 'عذراً، يجب التسجيل أولاً',
    'already_registered': 'أنت مسجل بالفعل!',
    'registered': 'تم تسجيلك بنجاح! 🎉',
    'joined': 'تم انضمامك للعبة! 🎮',
    'left': 'تم انسحابك من اللعبة',
    'already_playing': 'هناك لعبة جارية! استخدم "إيقاف" لإنهائها',
    'no_active_game': 'لا توجد لعبة نشطة حالياً',
    'game_stopped': 'تم إيقاف اللعبة',
    'rate_limited': 'أنت ترسل رسائل كثيرة! انتظر قليلاً',
    'correct_answer': '✅ إجابة صحيحة! +{} نقطة',
    'wrong_answer': '❌ إجابة خاطئة',
    'game_ended': '🏁 انتهت اللعبة!\n\n',
    'hint_msg': '💡 تلميح:\n{}',
    'answer_msg': '📝 الإجابة الصحيحة:\n{}'
}

# ============= نظام الألوان المحسن =============

C = {
    'bg': '#0A0E27',       # خلفية داكنة مريحة
    'card': '#0F2440',     # كروت داكنة
    'text': '#E0F2FF',     # نص فاتح
    'text2': '#7FB3D5',    # نص ثانوي
    'cyan': '#00D9FF',     # لون رئيسي
    'glow': '#5EEBFF',     # توهج
    'sep': '#2C5F8D',      # فواصل
    'border': '#00D9FF40', # حدود شفافة
    'topbg': '#1a1f3a'     # خلفية علوية
}

# ============= الإيموجي =============

RANK_EMOJIS = {
    1: '🥇', 2: '🥈', 3: '🥉', 4: '4️⃣', 5: '5️⃣',
    6: '6️⃣', 7: '7️⃣', 8: '8️⃣', 9: '9️⃣', 10: '🔟'
}

# ============= Rate Limiter =============

RATE_LIMIT = {
    'max_requests': 10,
    'window': 60
}

# ============= URLs =============

LOGO_URL = 'https://i.imgur.com/qcWILGi.jpeg'

# ============= مفاتيح AI =============

GEMINI_API_KEYS = [
    os.getenv('GEMINI_API_KEY_1'),
    os.getenv('GEMINI_API_KEY_2'),
    os.getenv('GEMINI_API_KEY_3')
]

GEMINI_MODEL = 'gemini-2.0-flash-exp'
