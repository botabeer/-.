"""
UI Components
=============
Professional Flex Message templates
Color scheme: Cyan, Gray, White, Black
"""

from config import GAMES, CONTENT, DEVELOPER

# Color Palette - Minimalist Design
C = {
    'bg': '#000000',           # Black background
    'card': '#1A1A1A',         # Dark card
    'glass': '#252525',        # Glass effect
    'primary': '#4DD0E1',      # Cyan primary
    'accent': '#26C6DA',       # Light cyan
    'text': '#FFFFFF',         # White text
    'muted': '#9E9E9E',        # Gray muted
    'border': '#424242',       # Gray border
    'shadow': '#0A0A0A'        # Deep black
}

LOGO = "https://i.imgur.com/qcWILGi.jpeg"

def welcome_card():
    """Main welcome card"""
    
    games_buttons = []
    for cmd, info in GAMES.items():
        games_buttons.append({
            "type": "button",
            "action": {"type": "message", "label": info['name'], "text": cmd},
            "style": "primary",
            "color": C['primary'],
            "height": "sm",
            "margin": "sm"
        })
    
    content_buttons = []
    for label, _ in CONTENT.items():
        content_buttons.append({
            "type": "button",
            "action": {"type": "message", "label": label, "text": label},
            "style": "secondary",
            "color": C['muted'],
            "height": "sm",
            "margin": "sm"
        })
    
    return {
        "type": "carousel",
        "contents": [
            {
                "type": "bubble",
                "size": "mega",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "image",
                                    "url": LOGO,
                                    "size": "full",
                                    "aspectMode": "cover",
                                    "aspectRatio": "16:9",
                                    "backgroundColor": C['bg']
                                }
                            ],
                            "paddingAll": "0px",
                            "cornerRadius": "16px",
                            "borderWidth": "2px",
                            "borderColor": C['primary']
                        },
                        {
                            "type": "text",
                            "text": "بوت الحوت",
                            "weight": "bold",
                            "size": "xxl",
                            "color": C['primary'],
                            "align": "center",
                            "margin": "xl"
                        },
                        {
                            "type": "text",
                            "text": "استمتع بالألعاب التفاعلية",
                            "size": "sm",
                            "color": C['muted'],
                            "align": "center",
                            "margin": "sm"
                        },
                        {
                            "type": "separator",
                            "margin": "xl",
                            "color": C['border']
                        },
                        {
                            "type": "text",
                            "text": "الألعاب المتاحة",
                            "weight": "bold",
                            "size": "lg",
                            "color": C['text'],
                            "margin": "xl",
                            "align": "center"
                        }
                    ] + games_buttons,
                    "paddingAll": "24px",
                    "backgroundColor": C['card'],
                    "spacing": "sm"
                }
            },
            {
                "type": "bubble",
                "size": "mega",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "محتوى إضافي",
                            "weight": "bold",
                            "size": "xl",
                            "color": C['primary'],
                            "align": "center"
                        },
                        {
                            "type": "separator",
                            "margin": "lg",
                            "color": C['border']
                        }
                    ] + content_buttons + [
                        {
                            "type": "separator",
                            "margin": "xl",
                            "color": C['border']
                        },
                        {
                            "type": "text",
                            "text": "الأوامر الأساسية",
                            "weight": "bold",
                            "size": "md",
                            "color": C['text'],
                            "margin": "lg",
                            "align": "center"
                        },
                        _info_row("نقاطي", "عرض احصائياتك"),
                        _info_row("الصدارة", "جدول المتصدرين"),
                        _info_row("ايقاف", "إيقاف اللعبة"),
                        {
                            "type": "separator",
                            "margin": "xl",
                            "color": C['border']
                        },
                        {
                            "type": "text",
                            "text": DEVELOPER,
                            "size": "xs",
                            "color": C['muted'],
                            "align": "center",
                            "margin": "lg"
                        }
                    ],
                    "paddingAll": "24px",
                    "backgroundColor": C['card'],
                    "spacing": "sm"
                }
            }
        ]
    }

def question_card(game_name, question, round_num, total_rounds):
    """Game question display card"""
    
    progress = round_num / total_rounds
    filled = int(progress * 5)
    
    circles = []
    for i in range(5):
        circles.append({
            "type": "text",
            "text": "●" if i < filled else "○",
            "color": C['primary'] if i < filled else C['muted'],
            "size": "md",
            "flex": 1,
            "align": "center"
        })
    
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": game_name,
                            "weight": "bold",
                            "size": "xl",
                            "color": C['primary'],
                            "flex": 4
                        },
                        {
                            "type": "text",
                            "text": f"{round_num}/{total_rounds}",
                            "size": "lg",
                            "color": C['accent'],
                            "align": "end",
                            "flex": 1,
                            "weight": "bold"
                        }
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": circles,
                    "margin": "md",
                    "spacing": "sm"
                },
                {
                    "type": "separator",
                    "margin": "lg",
                    "color": C['border']
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": question,
                            "wrap": True,
                            "color": C['text'],
                            "size": "xl",
                            "align": "center",
                            "weight": "bold"
                        }
                    ],
                    "backgroundColor": C['glass'],
                    "cornerRadius": "12px",
                    "paddingAll": "24px",
                    "margin": "xl",
                    "borderWidth": "1px",
                    "borderColor": C['primary']
                },
                {
                    "type": "text",
                    "text": "اكتب اجابتك في الدردشة",
                    "size": "sm",
                    "color": C['muted'],
                    "align": "center",
                    "margin": "lg"
                }
            ],
            "backgroundColor": C['card'],
            "paddingAll": "24px"
        }
    }

def result_card(title, message, points=None, success=True):
    """Result display card"""
    
    color = C['primary'] if success else C['muted']
    
    contents = [
        {
            "type": "text",
            "text": title,
            "weight": "bold",
            "size": "xxl",
            "color": color,
            "align": "center"
        },
        {
            "type": "separator",
            "margin": "lg",
            "color": color
        },
        {
            "type": "text",
            "text": message,
            "wrap": True,
            "color": C['text'],
            "size": "lg",
            "margin": "xl",
            "align": "center"
        }
    ]
    
    if points is not None:
        point_color = C['primary'] if points > 0 else C['muted']
        contents.append({
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": f"{points:+d}",
                    "color": point_color,
                    "size": "xxl",
                    "align": "center",
                    "weight": "bold"
                },
                {
                    "type": "text",
                    "text": "نقطة",
                    "color": C['muted'],
                    "size": "md",
                    "align": "center",
                    "margin": "sm"
                }
            ],
            "backgroundColor": C['glass'],
            "cornerRadius": "12px",
            "paddingAll": "20px",
            "margin": "xl",
            "borderWidth": "2px",
            "borderColor": point_color
        })
    
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": contents,
            "backgroundColor": C['card'],
            "paddingAll": "28px"
        }
    }

def stats_card(name, points, played, won):
    """Player statistics card"""
    
    win_rate = (won / played * 100) if played > 0 else 0
    
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "احصائياتك",
                    "weight": "bold",
                    "size": "xxl",
                    "color": C['primary'],
                    "align": "center"
                },
                {
                    "type": "separator",
                    "margin": "lg",
                    "color": C['primary']
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": name,
                            "size": "xl",
                            "color": C['text'],
                            "align": "center",
                            "weight": "bold"
                        }
                    ],
                    "backgroundColor": C['glass'],
                    "cornerRadius": "12px",
                    "paddingAll": "16px",
                    "margin": "xl",
                    "borderWidth": "1px",
                    "borderColor": C['border']
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        _stat_box("النقاط", str(points), C['primary']),
                        _stat_box("الألعاب", str(played), C['accent']),
                        _stat_box("الفوز", str(won), C['primary']),
                        _stat_box("نسبة الفوز", f"{win_rate:.0f}%", C['accent'])
                    ],
                    "margin": "xl",
                    "spacing": "md"
                }
            ],
            "backgroundColor": C['card'],
            "paddingAll": "24px"
        }
    }

def ranks_card(players):
    """Leaderboard card"""
    
    contents = [
        {
            "type": "text",
            "text": "المتصدرون",
            "weight": "bold",
            "size": "xxl",
            "color": C['primary'],
            "align": "center"
        },
        {
            "type": "separator",
            "margin": "xl",
            "color": C['primary']
        }
    ]
    
    for i, player in enumerate(players, 1):
        rank_color = C['primary'] if i <= 3 else C['text']
        
        contents.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": f"{i}",
                    "size": "lg",
                    "color": rank_color,
                    "flex": 1,
                    "weight": "bold",
                    "align": "center"
                },
                {
                    "type": "text",
                    "text": player['name'],
                    "size": "md",
                    "color": C['text'],
                    "flex": 5
                },
                {
                    "type": "text",
                    "text": str(player['points']),
                    "size": "lg",
                    "color": C['primary'],
                    "align": "end",
                    "flex": 2,
                    "weight": "bold"
                }
            ],
            "backgroundColor": C['glass'] if i <= 3 else 'transparent',
            "cornerRadius": "8px",
            "paddingAll": "16px",
            "margin": "md",
            "borderWidth": "1px" if i <= 3 else "0px",
            "borderColor": rank_color if i <= 3 else 'transparent'
        })
    
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": contents,
            "backgroundColor": C['card'],
            "paddingAll": "24px"
        }
    }

def hint_card(hint_text):
    """Hint display card"""
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "تلميح",
                    "weight": "bold",
                    "size": "xl",
                    "color": C['accent'],
                    "align": "center"
                },
                {
                    "type": "separator",
                    "margin": "md",
                    "color": C['border']
                },
                {
                    "type": "text",
                    "text": hint_text,
                    "size": "xxl",
                    "color": C['text'],
                    "align": "center",
                    "margin": "xl",
                    "weight": "bold",
                    "wrap": True
                }
            ],
            "backgroundColor": C['card'],
            "paddingAll": "24px"
        }
    }

# Helper Functions

def _info_row(label, value):
    """Info row helper"""
    return {
        "type": "box",
        "layout": "horizontal",
        "contents": [
            {
                "type": "text",
                "text": label,
                "color": C['accent'],
                "flex": 2,
                "size": "sm",
                "weight": "bold"
            },
            {
                "type": "text",
                "text": value,
                "color": C['muted'],
                "flex": 3,
                "size": "xs"
            }
        ],
        "margin": "md"
    }

def _stat_box(label, value, color):
    """Statistics box helper"""
    return {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "text",
                "text": value,
                "size": "xxl",
                "color": color,
                "align": "center",
                "weight": "bold"
            },
            {
                "type": "text",
                "text": label,
                "size": "sm",
                "color": C['muted'],
                "align": "center",
                "margin": "sm"
            }
        ],
        "backgroundColor": C['glass'],
        "cornerRadius": "12px",
        "paddingAll": "20px",
        "borderWidth": "2px",
        "borderColor": color
    }
