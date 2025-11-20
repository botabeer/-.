"""
rules.py - القوانين ونظام النقاط (قابل للتعديل حسب احتياجات البوت)
"""

# نظام النقاط
POINTS = {
    'correct': 2,      # إجابة صحيحة
    'hint': -1,        # طلب تلميح
    'answer': 0,       # إظهار الإجابة
    'skip': 0,         # تخطي
    'win': 5,          # فوز في اللعبة
    'participation': 1 # نقطة المشاركة
}

# إعدادات اللعبة العامة
GAME_SETTINGS = {
    'rounds': 5,
    'time_limit': 60,
    'min_answer_length': 2,
    'max_leaderboard_entries': 10,
    'points_for_speed': True,
    'allow_hints': True
}

# معلومات الألعاب
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
}

# الأوامر المتاحة
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

# رسائل الألعاب
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

# إعدادات التلميحات
HINT_SETTINGS = {
    'max_hints_per_game': 3,
    'hint_cost': POINTS['hint'],
    'reveal_percentage': 0.4
}

# قواعد التحقق من الإجابات
VALIDATION_RULES = {
    'case_sensitive': False,
    'ignore_diacritics': True,
    'trim_whitespace': True,
    'allow_partial_match': False,
    'similarity_threshold': 0.8
}

# رسائل النظام المطلوبة في app.py
SYSTEM_MESSAGES = {
    'not_registered': 'يجب التسجيل أولاً لاستخدام البوت.',
    'no_active_game': 'لا توجد لعبة نشطة حالياً.',
    'game_stopped': 'تم إيقاف اللعبة بنجاح.',
    'invalid_command': 'عذراً، الأمر غير معروف.',
    'error': 'حدث خطأ غير متوقع.'
}

# قواعد اللعبة العامة (يستخدمها أمر المساعدة)
GAME_RULES = """
قواعد اللعب:
- أجب على الأسئلة قبل انتهاء الوقت.
- يمكنك طلب تلميح ولكنه يكلف نقاطا.
- يمكنك إظهار الإجابة دون الحصول على نقاط.
- يتم حساب النقاط في نهاية كل لعبة.
"""
