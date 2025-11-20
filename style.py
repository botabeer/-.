# ============================================
# style.py - الستايل والألوان والتصاميم
# ============================================

"""
ستايل بوت الحوت
================
هذا الملف يحتوي على:
- الألوان المستخدمة
- تصاميم Flex Messages
- الأزرار
- القوالب الجاهزة
"""

# الألوان الرئيسية
COLORS = {
    'bg': '#0A0E27',           # خلفية داكنة
    'card': '#0F2440',         # خلفية الكارد
    'text': '#E0F2FF',         # نص أبيض مائل للأزرق
    'text2': '#7FB3D5',        # نص ثانوي
    'cyan': '#00D9FF',         # سماوي مضيء
    'glow': '#5EEBFF',         # توهج
    'sep': '#2C5F8D',          # فاصل
    'border': '#00D9FF40',     # حدود شفافة
    'success': '#00FF88',      # نجاح
    'error': '#FF4466',        # خطأ
    'warning': '#FFB800'       # تحذير
}

# رابط الشعار
LOGO_URL = "https://i.imgur.com/qcWILGi.jpeg"

# الأزرار الرئيسية
BUTTONS_MAIN = [
    {"label": "ابدأ", "text": "ابدأ", "style": "primary", "color": COLORS['cyan']},
    {"label": "انضم", "text": "انضم", "style": "secondary", "color": COLORS['text']},
    {"label": "انسحب", "text": "انسحب", "style": "secondary", "color": COLORS['text']},
    {"label": "إيقاف", "text": "إيقاف", "style": "secondary", "color": COLORS['error']}
]

# أزرار التلميح والإجابة
BUTTONS_HINT_ANSWER = [
    {"label": "لمح", "text": "لمح", "style": "secondary", "color": COLORS['warning']},
    {"label": "جاوب", "text": "جاوب", "style": "primary", "color": COLORS['cyan']}
]

# أزرار الإحصائيات
BUTTONS_STATS = [
    {"label": "نقاطي", "text": "نقاطي", "style": "secondary", "color": COLORS['text']},
    {"label": "الصدارة", "text": "الصدارة", "style": "primary", "color": COLORS['cyan']}
]


def create_welcome_card():
    """
    كارد الترحيب الأولي
    """
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "image",
                    "url": LOGO_URL,
                    "size": "full",
                    "aspectMode": "cover",
                    "aspectRatio": "2:1",
                    "gravity": "top"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "مرحباً بك في بوت الحوت",
                            "weight": "bold",
                            "size": "xl",
                            "color": COLORS['text'],
                            "align": "center"
                        },
                        {
                            "type": "separator",
                            "margin": "md",
                            "color": COLORS['sep']
                        },
                        {
                            "type": "text",
                            "text": "اختر لعبة أو محتوى ترفيهي",
                            "size": "sm",
                            "color": COLORS['text2'],
                            "align": "center",
                            "margin": "md"
                        }
                    ],
                    "spacing": "sm",
                    "paddingAll": "13px"
                }
            ],
            "paddingAll": "0px",
            "backgroundColor": COLORS['card']
        }
    }


def create_game_question_card(game_name, question_text, round_num, total_rounds, supports_hint=True):
    """
    كارد السؤال في اللعبة
    
    Args:
        game_name: اسم اللعبة
        question_text: نص السؤال
        round_num: رقم الجولة الحالية
        total_rounds: إجمالي الجولات
        supports_hint: هل اللعبة تدعم التلميح والإجابة
    """
    contents = [
        {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": game_name,
                    "weight": "bold",
                    "size": "lg",
                    "color": COLORS['cyan']
                },
                {
                    "type": "text",
                    "text": f"{round_num}/{total_rounds}",
                    "size": "sm",
                    "color": COLORS['text2'],
                    "align": "end"
                }
            ]
        },
        {
            "type": "separator",
            "margin": "md",
            "color": COLORS['sep']
        },
        {
            "type": "text",
            "text": question_text,
            "wrap": True,
            "color": COLORS['text'],
            "size": "md",
            "margin": "lg"
        }
    ]
    
    if supports_hint:
        contents.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "message",
                        "label": "لمح",
                        "text": "لمح"
                    },
                    "style": "secondary",
                    "color": COLORS['warning']
                },
                {
                    "type": "button",
                    "action": {
                        "type": "message",
                        "label": "جاوب",
                        "text": "جاوب"
                    },
                    "style": "primary",
                    "color": COLORS['cyan']
                }
            ],
            "spacing": "sm",
            "margin": "lg"
        })
    
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": contents,
            "backgroundColor": COLORS['card'],
            "paddingAll": "20px"
        }
    }


def create_result_card(title, message, points=None, is_success=True):
    """
    كارد النتيجة
    """
    color = COLORS['success'] if is_success else COLORS['error']
    
    contents = [
        {
            "type": "text",
            "text": title,
            "weight": "bold",
            "size": "xl",
            "color": color,
            "align": "center"
        },
        {
            "type": "separator",
            "margin": "md",
            "color": COLORS['sep']
        },
        {
            "type": "text",
            "text": message,
            "wrap": True,
            "color": COLORS['text'],
            "size": "md",
            "margin": "md",
            "align": "center"
        }
    ]
    
    if points is not None:
        contents.append({
            "type": "text",
            "text": f"النقاط: {points:+d}",
            "color": COLORS['cyan'],
            "size": "lg",
            "margin": "md",
            "align": "center",
            "weight": "bold"
        })
    
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": contents,
            "backgroundColor": COLORS['card'],
            "paddingAll": "20px"
        }
    }


def create_leaderboard_card(players):
    """
    كارد المتصدرين
    
    Args:
        players: قائمة اللاعبين [(name, points, rank), ...]
    """
    contents = [
        {
            "type": "text",
            "text": "المتصدرون",
            "weight": "bold",
            "size": "xl",
            "color": COLORS['cyan'],
            "align": "center"
        },
        {
            "type": "separator",
            "margin": "md",
            "color": COLORS['sep']
        }
    ]
    
    for name, points, rank in players[:10]:
        rank_colors = {1: COLORS['warning'], 2: COLORS['text'], 3: COLORS['text2']}
        rank_color = rank_colors.get(rank, COLORS['text2'])
        
        contents.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": f"{rank}.",
                    "size": "sm",
                    "color": rank_color,
                    "flex": 1
                },
                {
                    "type": "text",
                    "text": name,
                    "size": "sm",
                    "color": COLORS['text'],
                    "flex": 4
                },
                {
                    "type": "text",
                    "text": str(points),
                    "size": "sm",
                    "color": COLORS['cyan'],
                    "align": "end",
                    "flex": 2
                }
            ],
            "margin": "md"
        })
    
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": contents,
            "backgroundColor": COLORS['card'],
            "paddingAll": "20px"
        }
    }


def create_stats_card(name, points, games_played, games_won):
    """
    كارد الإحصائيات الشخصية
    """
    win_rate = (games_won / games_played * 100) if games_played > 0 else 0
    
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "إحصائياتك",
                    "weight": "bold",
                    "size": "xl",
                    "color": COLORS['cyan'],
                    "align": "center"
                },
                {
                    "type": "separator",
                    "margin": "md",
                    "color": COLORS['sep']
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "الاسم:", "color": COLORS['text2'], "flex": 2},
                                {"type": "text", "text": name, "color": COLORS['text'], "flex": 3}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "النقاط:", "color": COLORS['text2'], "flex": 2},
                                {"type": "text", "text": str(points), "color": COLORS['cyan'], "flex": 3, "weight": "bold"}
                            ],
                            "margin": "md"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "الألعاب:", "color": COLORS['text2'], "flex": 2},
                                {"type": "text", "text": str(games_played), "color": COLORS['text'], "flex": 3}
                            ],
                            "margin": "md"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "الفوز:", "color": COLORS['text2'], "flex": 2},
                                {"type": "text", "text": str(games_won), "color": COLORS['success'], "flex": 3}
                            ],
                            "margin": "md"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "نسبة الفوز:", "color": COLORS['text2'], "flex": 2},
                                {"type": "text", "text": f"{win_rate:.1f}%", "color": COLORS['warning'], "flex": 3}
                            ],
                            "margin": "md"
                        }
                    ],
                    "margin": "lg"
                }
            ],
            "backgroundColor": COLORS['card'],
            "paddingAll": "20px"
        }
    }
