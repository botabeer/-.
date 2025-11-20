# ============================================
# style.py - الستايل والتصاميم
# ============================================

from rules import MAIN_GAMES, EXTRA_CONTENT, GAMES_INFO, DEVELOPER_INFO, GAME_RULES

COLORS = {
    'bg': '#0A0E27', 'card': '#0F2440', 'text': '#E0F2FF',
    'text2': '#7FB3D5', 'cyan': '#00D9FF', 'glow': '#5EEBFF',
    'sep': '#2C5F8D', 'border': '#00D9FF40', 'success': '#00FF88',
    'error': '#FF4466', 'warning': '#FFB800'
}

LOGO_URL = "https://i.imgur.com/qcWILGi.jpeg"

def create_welcome_flex():
    """كارد الترحيب الرئيسي مع جميع الألعاب والمحتوى"""
    games_buttons = []
    for i, game in enumerate(MAIN_GAMES, 1):
        games_buttons.append({
            "type": "button",
            "action": {"type": "message", "label": f"{i}. {GAMES_INFO[game]['name']}", "text": game},
            "style": "primary" if i <= 4 else "secondary",
            "color": COLORS['cyan'], "height": "sm"
        })
    
    extra_buttons = []
    for content in EXTRA_CONTENT:
        extra_buttons.append({
            "type": "button",
            "action": {"type": "message", "label": f"- {content}", "text": content},
            "style": "secondary", "color": COLORS['text2'], "height": "sm"
        })
    
    extra_buttons.append({
        "type": "button",
        "action": {"type": "message", "label": "Ai محادثة ذكية", "text": "ai"},
        "style": "primary", "color": COLORS['success'], "height": "sm"
    })
    
    return {
        "type": "carousel",
        "contents": [
            {
                "type": "bubble",
                "body": {
                    "type": "box", "layout": "vertical",
                    "contents": [
                        {"type": "image", "url": LOGO_URL, "size": "full", "aspectMode": "cover", "aspectRatio": "2:1"},
                        {"type": "box", "layout": "vertical", "contents": [
                            {"type": "text", "text": "بوت الحوت", "weight": "bold", "size": "xxl", "color": COLORS['cyan'], "align": "center"},
                            {"type": "separator", "margin": "md", "color": COLORS['sep']},
                            {"type": "text", "text": "ألعاب رئيسية:", "weight": "bold", "size": "md", "color": COLORS['text'], "margin": "lg"}
                        ] + games_buttons, "paddingAll": "20px"}
                    ], "paddingAll": "0px", "backgroundColor": COLORS['card']
                }
            },
            {
                "type": "bubble",
                "body": {
                    "type": "box", "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "محتوى إضافي", "weight": "bold", "size": "xl", "color": COLORS['cyan'], "align": "center"},
                        {"type": "separator", "margin": "md", "color": COLORS['sep']}
                    ] + extra_buttons + [
                        {"type": "separator", "margin": "lg", "color": COLORS['sep']},
                        {"type": "text", "text": DEVELOPER_INFO['copyright'], "size": "xxs", "color": COLORS['text2'], "align": "center", "margin": "md"}
                    ], "paddingAll": "20px", "backgroundColor": COLORS['card']
                }
            }
        ]
    }

def create_help_flex():
    """نافذة المساعدة"""
    return {
        "type": "bubble",
        "body": {
            "type": "box", "layout": "vertical",
            "contents": [
                {"type": "text", "text": "الأوامر المتاحة", "weight": "bold", "size": "xl", "color": COLORS['cyan'], "align": "center"},
                {"type": "separator", "margin": "md", "color": COLORS['sep']},
                {"type": "text", "text": GAME_RULES, "wrap": True, "color": COLORS['text'], "size": "sm", "margin": "lg"},
                {"type": "separator", "margin": "lg", "color": COLORS['sep']},
                {"type": "box", "layout": "horizontal", "spacing": "sm", "margin": "lg", "contents": [
                    {"type": "button", "action": {"type": "message", "label": "انضم", "text": "انضم"}, "style": "primary", "color": COLORS['cyan'], "flex": 1},
                    {"type": "button", "action": {"type": "message", "label": "انسحب", "text": "انسحب"}, "style": "secondary", "flex": 1}
                ]},
                {"type": "box", "layout": "horizontal", "spacing": "sm", "margin": "sm", "contents": [
                    {"type": "button", "action": {"type": "message", "label": "إيقاف", "text": "إيقاف"}, "style": "secondary", "flex": 1},
                    {"type": "button", "action": {"type": "message", "label": "نقاطي", "text": "نقاطي"}, "style": "secondary", "flex": 1}
                ]},
                {"type": "box", "layout": "horizontal", "spacing": "sm", "margin": "sm", "contents": [
                    {"type": "button", "action": {"type": "message", "label": "الصدارة", "text": "الصدارة"}, "style": "primary", "color": COLORS['success'], "flex": 1},
                    {"type": "button", "action": {"type": "message", "label": "ابدأ", "text": "ابدأ"}, "style": "primary", "color": COLORS['cyan'], "flex": 1}
                ]},
                {"type": "separator", "margin": "lg", "color": COLORS['sep']},
                {"type": "text", "text": DEVELOPER_INFO['copyright'], "size": "xxs", "color": COLORS['text2'], "align": "center", "margin": "md"}
            ], "paddingAll": "20px", "backgroundColor": COLORS['card']
        }
    }

def create_game_question_card(game_name, question_text, round_num, total_rounds, supports_hint=True):
    """كارد السؤال في اللعبة"""
    contents = [
        {"type": "box", "layout": "horizontal", "contents": [
            {"type": "text", "text": game_name, "weight": "bold", "size": "lg", "color": COLORS['cyan']},
            {"type": "text", "text": f"{round_num}/{total_rounds}", "size": "sm", "color": COLORS['text2'], "align": "end"}
        ]},
        {"type": "separator", "margin": "md", "color": COLORS['sep']},
        {"type": "text", "text": question_text, "wrap": True, "color": COLORS['text'], "size": "md", "margin": "lg"}
    ]
    
    if supports_hint:
        contents.append({"type": "box", "layout": "horizontal", "contents": [
            {"type": "button", "action": {"type": "message", "label": "لمح", "text": "لمح"}, "style": "secondary", "color": COLORS['warning'], "flex": 1},
            {"type": "button", "action": {"type": "message", "label": "جاوب", "text": "جاوب"}, "style": "primary", "color": COLORS['cyan'], "flex": 1}
        ], "spacing": "sm", "margin": "lg"})
    
    return {"type": "bubble", "body": {"type": "box", "layout": "vertical", "contents": contents, "backgroundColor": COLORS['card'], "paddingAll": "20px"}}

def create_result_card(title, message, points=None, is_success=True):
    """كارد النتيجة"""
    color = COLORS['success'] if is_success else COLORS['error']
    contents = [
        {"type": "text", "text": title, "weight": "bold", "size": "xl", "color": color, "align": "center"},
        {"type": "separator", "margin": "md", "color": COLORS['sep']},
        {"type": "text", "text": message, "wrap": True, "color": COLORS['text'], "size": "md", "margin": "md", "align": "center"}
    ]
    if points is not None:
        contents.append({"type": "text", "text": f"النقاط: {points:+d}", "color": COLORS['cyan'], "size": "lg", "margin": "md", "align": "center", "weight": "bold"})
    return {"type": "bubble", "body": {"type": "box", "layout": "vertical", "contents": contents, "backgroundColor": COLORS['card'], "paddingAll": "20px"}}

def create_leaderboard_card(players):
    """كارد المتصدرين"""
    contents = [
        {"type": "text", "text": "المتصدرون", "weight": "bold", "size": "xl", "color": COLORS['cyan'], "align": "center"},
        {"type": "separator", "margin": "md", "color": COLORS['sep']}
    ]
    for name, points, rank in players[:10]:
        rank_colors = {1: COLORS['warning'], 2: COLORS['text'], 3: COLORS['text2']}
        rank_color = rank_colors.get(rank, COLORS['text2'])
        contents.append({"type": "box", "layout": "horizontal", "contents": [
            {"type": "text", "text": f"{rank}.", "size": "sm", "color": rank_color, "flex": 1},
            {"type": "text", "text": name, "size": "sm", "color": COLORS['text'], "flex": 4},
            {"type": "text", "text": str(points), "size": "sm", "color": COLORS['cyan'], "align": "end", "flex": 2}
        ], "margin": "md"})
    return {"type": "bubble", "body": {"type": "box", "layout": "vertical", "contents": contents, "backgroundColor": COLORS['card'], "paddingAll": "20px"}}

def create_stats_card(name, points, games_played, games_won):
    """كارد الإحصائيات"""
    win_rate = (games_won / games_played * 100) if games_played > 0 else 0
    return {"type": "bubble", "body": {"type": "box", "layout": "vertical", "contents": [
        {"type": "text", "text": "إحصائياتك", "weight": "bold", "size": "xl", "color": COLORS['cyan'], "align": "center"},
        {"type": "separator", "margin": "md", "color": COLORS['sep']},
        {"type": "box", "layout": "vertical", "contents": [
            {"type": "box", "layout": "horizontal", "contents": [
                {"type": "text", "text": "الاسم:", "color": COLORS['text2'], "flex": 2},
                {"type": "text", "text": name, "color": COLORS['text'], "flex": 3}
            ]},
            {"type": "box", "layout": "horizontal", "contents": [
                {"type": "text", "text": "النقاط:", "color": COLORS['text2'], "flex": 2},
                {"type": "text", "text": str(points), "color": COLORS['cyan'], "flex": 3, "weight": "bold"}
            ], "margin": "md"},
            {"type": "box", "layout": "horizontal", "contents": [
                {"type": "text", "text": "الألعاب:", "color": COLORS['text2'], "flex": 2},
                {"type": "text", "text": str(games_played), "color": COLORS['text'], "flex": 3}
            ], "margin": "md"},
            {"type": "box", "layout": "horizontal", "contents": [
                {"type": "text", "text": "الفوز:", "color": COLORS['text2'], "flex": 2},
                {"type": "text", "text": str(games_won), "color": COLORS['success'], "flex": 3}
            ], "margin": "md"},
            {"type": "box", "layout": "horizontal", "contents": [
                {"type": "text", "text": "نسبة الفوز:", "color": COLORS['text2'], "flex": 2},
                {"type": "text", "text": f"{win_rate:.1f}%", "color": COLORS['warning'], "flex": 3}
            ], "margin": "md"}
        ], "margin": "lg"}
    ], "backgroundColor": COLORS['card'], "paddingAll": "20px"}}
