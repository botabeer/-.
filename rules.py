"""
rules.py - القوانين ونظام النقاط (قابل للتعديل حسب احتياجات البوت)
"""

# نظام النقاط - قابل للتعديل
POINTS = {
    'correct': 2,      # إجابة صحيحة
    'hint': -1,        # طلب تلميح
    'answer': 0,       # إظهار الإجابة
    'skip': 0,         # تخطي
    'win': 5,          # فوز في اللعبة
    'participation': 1 # نقطة المشاركة
}

# إعدادات اللعبة - قابل للتعديل
GAME_SETTINGS = {
    'rounds': 5,                    # عدد الجولات الافتراضي
    'time_limit': 60,               # الحد الزمني بالثواني
    'min_answer_length': 2,         # الحد الأدنى لطول الإجابة
    'max_leaderboard_entries': 10,  # عدد المتصدرين المعروضين
    'points_for_speed': True,       # نقاط إضافية للسرعة
    'allow_hints': True             # السماح بالتلميحات
}

# معلومات الألعاب - قابل للتعديل والتوسع
GAMES_INFO = {
    'game1': {
        'name': 'اللعبة الأولى',
        'description': 'وصف اللعبة الأولى',
        'rounds': 5,
        'supports_hint': True,
        'difficulty': 'سهل'
    },
    'game2': {
        'name': 'اللعبة الثانية',
        'description': 'وصف اللعبة الثانية',
        'rounds': 5,
        'supports_hint': True,
        'difficulty': 'متوسط'
    },
    'game3': {
        'name': 'اللعبة الثالثة',
        'description': 'وصف اللعبة الثالثة',
        'rounds': 3,
        'supports_hint': False,
        'difficulty': 'صعب'
    }
    # أضف المزيد من الألعاب هنا
}

# الأوامر المتاحة - قابل للتعديل
COMMANDS = {
    'start': ['ابدأ', 'start', 'بدء'],
    'help': ['مساعدة', 'help', 'ساعدني'],
    'stats': ['نقاطي', 'احصائياتي', 'نقاط'],
    'leaderboard': ['الصدارة', 'المتصدرين', 'القائمة'],
    'stop': ['إيقاف', 'stop', 'توقف'],
    'hint': ['لمح', 'تلميح', 'مساعدة'],
    'answer': ['جاوب', 'الجواب', 'الحل'],
    'replay': ['إعادة', 'اعادة', 'مرة اخرى'],
    'content1': ['محتوى1', 'content1'],
    'content2': ['محتوى2', 'content2'],
    'content3': ['محتوى3', 'content3'],
    'content4': ['محتوى4', 'content4']
}

# رسائل الألعاب - قابل للتعديل
GAME_MESSAGES = {
    'start': 'بدأت اللعبة',
    'correct': 'إجابة صحيحة',
    'wrong': 'إجابة خاطئة',
    'timeout': 'انتهى الوقت',
    'game_over': 'انتهت اللعبة',
    'hint_used': 'تم استخدام تلميح',
    'answer_shown': 'الإجابة الصحيحة',
    'next_round': 'الجولة التالية'
}

# إعدادات التلميحات - قابل للتعديل
HINT_SETTINGS = {
    'max_hints_per_game': 3,        # الحد الأقصى للتلميحات
    'hint_cost': POINTS['hint'],    # تكلفة التلميح
    'reveal_percentage': 0.4        # نسبة الكشف في التلميح (40%)
}

# قواعد التحقق من الإجابات - قابل للتعديل
VALIDATION_RULES = {
    'case_sensitive': False,        # حساسية الأحرف الكبيرة/الصغيرة
    'ignore_diacritics': True,      # تجاهل التشكيل
    'trim_whitespace': True,        # إزالة المسافات الزائدة
    'allow_partial_match': False,   # قبول التطابق الجزئي
    'similarity_threshold': 0.8     # عتبة التشابه للإجابات
}
