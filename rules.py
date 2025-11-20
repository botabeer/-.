GAMES_INFO = {
    'fast': {
        'name': 'اسرع',
        'description': 'اكتب الكلمات/العبارات باسرع وقت',
        'triggers': ['اسرع', 'سرعة', 'fast'],
        'rounds': 5,
        'supports_hint': False,
        'supports_skip': False
    },
    'lbgame': {
        'name': 'لعبة',
        'description': 'انسان حيوان نبات بلد',
        'triggers': ['لعبة', 'لعبه', 'game'],
        'rounds': 5,
        'supports_hint': True,
        'supports_skip': True
    },
    'chain': {
        'name': 'سلسلة',
        'description': 'استمر في سلسلة الكلمات',
        'triggers': ['سلسلة', 'سلسله', 'chain'],
        'rounds': 5,
        'supports_hint': True,
        'supports_skip': True
    },
    'song': {
        'name': 'اغنية',
        'description': 'خمن المغني من كلمات الاغنية',
        'triggers': ['اغنية', 'اغنيه', 'song'],
        'rounds': 5,
        'supports_hint': True,
        'supports_skip': True
    },
    'opposite': {
        'name': 'ضد',
        'description': 'ابحث عن عكس الكلمة',
        'triggers': ['ضد', 'عكس', 'opposite'],
        'rounds': 5,
        'supports_hint': True,
        'supports_skip': True
    },
    'order': {
        'name': 'ترتيب',
        'description': 'رتب العناصر بشكل صحيح',
        'triggers': ['ترتيب', 'order'],
        'rounds': 5,
        'supports_hint': True,
        'supports_skip': True
    },
    'build': {
        'name': 'تكوين',
        'description': 'كون 3 كلمات من 6 حروف',
        'triggers': ['تكوين', 'بناء', 'build'],
        'rounds': 5,
        'supports_hint': True,
        'supports_skip': True
    },
    'compatibility': {
        'name': 'توافق',
        'description': 'احسب نسبة التوافق بين اسمين',
        'triggers': ['توافق', 'تطابق', 'compatibility'],
        'rounds': 1,
        'supports_hint': False,
        'supports_skip': False
    },
    'ai': {
        'name': 'محادثة AI',
        'description': 'تحدث مع الذكاء الاصطناعي',
        'triggers': ['ai', 'محادثة', 'ذكاء'],
        'rounds': 1,
        'supports_hint': False,
        'supports_skip': False
    }
}

COMMANDS = {
    'start': ['ابدأ', 'البداية', 'start', 'بدء'],
    'stats': ['نقاطي', 'احصائياتي', 'احصائيات', 'stats'],
    'leaderboard': ['الصدارة', 'المتصدرين', 'الترتيب', 'leaderboard'],
    'stop': ['إيقاف', 'ايقاف', 'توقف', 'stop'],
    'hint': ['لمح', 'تلميح', 'hint'],
    'skip': ['تخطي', 'تخطى', 'skip']
}

POINTS = {
    'correct': 2,
    'hint': -1,
    'answer': 0,
    'skip': 0
}

COLORS = {
    'bg': '#000000',
    'card': '#1A1A1A',
    'glass': '#252525',
    'primary': '#4DD0E1',
    'accent': '#26C6DA',
    'text': '#FFFFFF',
    'muted': '#9E9E9E',
    'border': '#424242'
}
