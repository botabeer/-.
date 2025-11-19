import os

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

COLORS = {
    'bg': '#0A0E27',
    'topbg': '#667eea',
    'card': '#1a1f3a',
    'card2': '#0F1729',
    'text': '#E8F4FF',
    'text2': '#8FB9D8',
    'cyan': '#00D9FF',
    'glow': '#5EEBFF',
    'sep': '#2C5F8D',
    'border': '#00D9FF50',
    'glass': '#1a1f3a90',
    'gradient1': '#667eea',
    'gradient2': '#764ba2',
    'success': '#00FF88',
    'warning': '#FFB800',
    'error': '#FF4444'
}

POINTS = {
    'correct': 2,
    'hint': 1,
    'answer': 0,
    'skip': 0
}

GAME_SETTINGS = {
    'rounds': 5,
    'inactive_days': 45,
    'min_players': 1,
}

GAMES_LIST = [
    'opposite',
    'song',
    'chain',
    'order',
    'build',
    'lbgame',
]

CMDS = {
    'start': ['البداية', 'start', 'بدء', 'ابدأ'],
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

RANK_EMOJIS = {
    1: '🥇',
    2: '🥈',
    3: '🥉',
    4: '4️⃣',
    5: '5️⃣',
    6: '6️⃣',
    7: '7️⃣',
    8: '8️⃣',
    9: '9️⃣',
    10: '🔟'
}

RATE_LIMIT = {
    'max_requests': 20,
    'window': 60
}

LOGO_URL = 'https://i.imgur.com/qcWILGi.jpeg'

GEMINI_API_KEYS = [
    os.getenv('GEMINI_API_KEY_1'),
    os.getenv('GEMINI_API_KEY_2'),
    os.getenv('GEMINI_API_KEY_3')
]

GEMINI_MODEL = 'gemini-2.0-flash-exp'

def get_welcome_card():
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": COLORS['bg'],
            "paddingAll": "0px",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": COLORS['topbg'],
                    "paddingTop": "40px",
                    "paddingBottom": "160px",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "cornerRadius": "30px",
                            "backgroundColor": COLORS['bg'],
                            "paddingAll": "28px",
                            "offsetTop": "80px",
                            "borderWidth": "2px",
                            "borderColor": COLORS['border'],
                            "contents": [
                                {
                                    "type": "image",
                                    "url": LOGO_URL,
                                    "size": "150px",
                                    "align": "center",
                                    "margin": "none"
                                },
                                {
                                    "type": "text",
                                    "text": "بوت الحوت",
                                    "weight": "bold",
                                    "size": "xxl",
                                    "align": "center",
                                    "color": COLORS['glow'],
                                    "margin": "md"
                                },
                                {
                                    "type": "separator",
                                    "color": COLORS['sep'],
                                    "margin": "lg"
                                },
                                {
                                    "type": "text",
                                    "text": "الألعاب المتوفرة",
                                    "align": "center",
                                    "size": "lg",
                                    "weight": "bold",
                                    "color": COLORS['text'],
                                    "margin": "lg"
                                },
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "backgroundColor": COLORS['glass'],
                                    "cornerRadius": "18px",
                                    "paddingAll": "20px",
                                    "margin": "md",
                                    "borderWidth": "1px",
                                    "borderColor": COLORS['border'],
                                    "contents": [
                                        {"type": "text", "text": "1. ضد", "size": "sm", "color": COLORS['text'], "wrap": True},
                                        {"type": "text", "text": "اعكس الكلمة المعطاة", "size": "xs", "color": COLORS['text2'], "wrap": True, "margin": "xs"},
                                        
                                        {"type": "text", "text": "2. أغنية", "size": "sm", "color": COLORS['text'], "wrap": True, "margin": "md"},
                                        {"type": "text", "text": "تخمين المغني من كلمات الأغنية", "size": "xs", "color": COLORS['text2'], "wrap": True, "margin": "xs"},
                                        
                                        {"type": "text", "text": "3. سلسلة الكلمات", "size": "sm", "color": COLORS['text'], "wrap": True, "margin": "md"},
                                        {"type": "text", "text": "كلمة تبدأ بالحرف الأخير من السابقة", "size": "xs", "color": COLORS['text2'], "wrap": True, "margin": "xs"},
                                        
                                        {"type": "text", "text": "4. ترتيب", "size": "sm", "color": COLORS['text'], "wrap": True, "margin": "md"},
                                        {"type": "text", "text": "ترتيب العناصر حسب المطلوب", "size": "xs", "color": COLORS['text2'], "wrap": True, "margin": "xs"},
                                        
                                        {"type": "text", "text": "5. تكوين كلمات", "size": "sm", "color": COLORS['text'], "wrap": True, "margin": "md"},
                                        {"type": "text", "text": "تكوين 3 كلمات من الحروف المعطاة", "size": "xs", "color": COLORS['text2'], "wrap": True, "margin": "xs"},
                                        
                                        {"type": "text", "text": "6. لعبة", "size": "sm", "color": COLORS['text'], "wrap": True, "margin": "md"},
                                        {"type": "text", "text": "إنسان، حيوان، نبات، بلد", "size": "xs", "color": COLORS['text2'], "wrap": True, "margin": "xs"}
                                    ]
                                },
                                {
                                    "type": "separator",
                                    "color": COLORS['sep'],
                                    "margin": "lg"
                                },
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "spacing": "sm",
                                    "margin": "lg",
                                    "contents": [
                                        {
                                            "type": "button",
                                            "action": {
                                                "type": "message",
                                                "label": "🎮 ابدأ اللعب",
                                                "text": "ابدأ"
                                            },
                                            "style": "primary",
                                            "color": COLORS['cyan'],
                                            "height": "md"
                                        },
                                        {
                                            "type": "box",
                                            "layout": "horizontal",
                                            "spacing": "sm",
                                            "margin": "sm",
                                            "contents": [
                                                {
                                                    "type": "button",
                                                    "action": {
                                                        "type": "message",
                                                        "label": "📊 نقاطي",
                                                        "text": "نقاطي"
                                                    },
                                                    "style": "secondary",
                                                    "color": "#FFFFFF",
                                                    "height": "sm",
                                                    "flex": 1
                                                },
                                                {
                                                    "type": "button",
                                                    "action": {
                                                        "type": "message",
                                                        "label": "🏆 الصدارة",
                                                        "text": "الصدارة"
                                                    },
                                                    "style": "secondary",
                                                    "color": "#FFFFFF",
                                                    "height": "sm",
                                                    "flex": 1
                                                }
                                            ]
                                        },
                                        {
                                            "type": "button",
                                            "action": {
                                                "type": "message",
                                                "label": "⛔ إيقاف",
                                                "text": "إيقاف"
                                            },
                                            "style": "secondary",
                                            "color": "#FF6B6B",
                                            "height": "sm",
                                            "margin": "sm"
                                        }
                                    ]
                                },
                                {
                                    "type": "text",
                                    "text": "© بوت الحوت 2025",
                                    "align": "center",
                                    "size": "xs",
                                    "color": COLORS['text2'],
                                    "margin": "lg"
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    }

def get_help_card():
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": COLORS['bg'],
            "paddingAll": "0px",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": COLORS['topbg'],
                    "paddingTop": "35px",
                    "paddingBottom": "140px",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "cornerRadius": "25px",
                            "backgroundColor": COLORS['bg'],
                            "paddingAll": "28px",
                            "offsetTop": "55px",
                            "borderWidth": "2px",
                            "borderColor": COLORS['border'],
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "💡 المساعدة",
                                    "weight": "bold",
                                    "size": "xxl",
                                    "align": "center",
                                    "color": COLORS['glow']
                                },
                                {
                                    "type": "text",
                                    "text": "الأوامر المتاحة",
                                    "align": "center",
                                    "size": "md",
                                    "color": COLORS['text2'],
                                    "margin": "sm"
                                },
                                {
                                    "type": "separator",
                                    "color": COLORS['sep'],
                                    "margin": "lg"
                                },
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "backgroundColor": COLORS['glass'],
                                    "cornerRadius": "18px",
                                    "paddingAll": "20px",
                                    "margin": "lg",
                                    "borderWidth": "1px",
                                    "borderColor": COLORS['border'],
                                    "contents": [
                                        {"type": "text", "text": "💡 لمح", "size": "md", "color": COLORS['cyan'], "weight": "bold"},
                                        {"type": "text", "text": "يعطيك تلميح ذكي (النقاط تنخفض للنصف)", "size": "sm", "color": COLORS['text'], "wrap": True, "margin": "xs"},
                                        {"type": "separator", "color": COLORS['sep'], "margin": "md"},
                                        
                                        {"type": "text", "text": "✓ جاوب", "size": "md", "color": COLORS['cyan'], "weight": "bold", "margin": "md"},
                                        {"type": "text", "text": "يعرض الإجابة وينتقل للسؤال التالي", "size": "sm", "color": COLORS['text'], "wrap": True, "margin": "xs"},
                                        {"type": "separator", "color": COLORS['sep'], "margin": "md"},
                                        
                                        {"type": "text", "text": "🔄 إعادة", "size": "md", "color": COLORS['cyan'], "weight": "bold", "margin": "md"},
                                        {"type": "text", "text": "يعيد تشغيل اللعبة الحالية", "size": "sm", "color": COLORS['text'], "wrap": True, "margin": "xs"},
                                        {"type": "separator", "color": COLORS['sep'], "margin": "md"},
                                        
                                        {"type": "text", "text": "⛔ إيقاف", "size": "md", "color": COLORS['cyan'], "weight": "bold", "margin": "md"},
                                        {"type": "text", "text": "ينهي اللعبة الجارية فوراً", "size": "sm", "color": COLORS['text'], "wrap": True, "margin": "xs"},
                                        {"type": "separator", "color": COLORS['sep'], "margin": "md"},
                                        
                                        {"type": "text", "text": "📊 نقاطي / 🏆 الصدارة", "size": "md", "color": COLORS['cyan'], "weight": "bold", "margin": "md"},
                                        {"type": "text", "text": "عرض نقاطك أو أفضل اللاعبين", "size": "sm", "color": COLORS['text'], "wrap": True, "margin": "xs"}
                                    ]
                                },
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "backgroundColor": COLORS['card'],
                                    "cornerRadius": "15px",
                                    "paddingAll": "16px",
                                    "margin": "lg",
                                    "contents": [
                                        {"type": "text", "text": "⭐ نظام النقاط", "size": "md", "color": COLORS['glow'], "weight": "bold", "align": "center"},
                                        {"type": "text", "text": "إجابة صحيحة: +2\nمع تلميح: +1\nطلب جاوب: 0", "size": "sm", "color": COLORS['text'], "wrap": True, "margin": "md", "align": "center"}
                                    ]
                                },
                                {
                                    "type": "box",
                                    "layout": "horizontal",
                                    "spacing": "sm",
                                    "margin": "xl",
                                    "contents": [
                                        {"type": "button", "action": {"type": "message", "label": "📊 نقاطي", "text": "نقاطي"}, "style": "secondary", "color": "#FFFFFF", "height": "sm", "flex": 1},
                                        {"type": "button", "action": {"type": "message", "label": "🏆 الصدارة", "text": "الصدارة"}, "style": "primary", "color": COLORS['cyan'], "height": "sm", "flex": 1}
                                    ]
                                },
                                {"type": "text", "text": "© بوت الحوت 2025", "align": "center", "size": "xs", "color": COLORS['text2'], "margin": "lg"}
                            ]
                        }
                    ]
                }
            ]
        }
    }
