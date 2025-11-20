"""
UI Components
=============
Clean and professional Flex Message templates
"""

from config import GAMES, CONTENT, DEVELOPER

# Color Palette
C = {
    'bg': '#0F172A',
    'card': '#1E293B',
    'primary': '#3B82F6',
    'secondary': '#64748B',
    'success': '#10B981',
    'error': '#EF4444',
    'text': '#F1F5F9',
    'muted': '#94A3B8',
    'border': '#334155'
}

LOGO = "https://i.imgur.com/qcWILGi.jpeg"

def welcome_card():
    """Main welcome card"""
    games_list = [
        {
            "type": "button",
            "action": {"type": "message", "label": info['name'], "text": cmd},
            "style": "primary",
            "color": C['primary'],
            "height": "sm"
        }
        for cmd, info in GAMES.items()
    ]
    
    content_list = [
        {
            "type": "button",
            "action": {"type": "message", "label": item, "text": item},
            "style": "secondary",
            "color": C['secondary'],
            "height": "sm"
        }
        for item in CONTENT
    ]
    
    return {
        "type": "carousel",
        "contents": [
            {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "image",
                            "url": LOGO,
                            "size": "full",
                            "aspectMode": "cover",
                            "aspectRatio": "2:1"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "بوت الحوت",
                                    "weight": "bold",
                                    "size": "xxl",
                                    "color": C['primary'],
                                    "align": "center"
                                },
                                {
                                    "type": "separator",
                                    "margin": "md",
                                    "color": C['border']
                                },
                                {
                                    "type": "text",
                                    "text": "الألعاب المتاحة",
                                    "weight": "bold",
                                    "size": "md",
                                    "color": C['text'],
                                    "margin": "lg"
                                }
                            ] + games_list,
                            "paddingAll": "20px"
                        }
                    ],
                    "paddingAll": "0px",
                    "backgroundColor": C['card']
                }
            },
            {
                "type": "bubble",
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
                            "margin": "md",
                            "color": C['border']
                        }
                    ] + content_list + [
                        {
                            "type": "separator",
                            "margin": "lg",
                            "color": C['border']
                        },
                        {
                            "type": "text",
                            "text": DEVELOPER,
                            "size": "xxs",
                            "color": C['muted'],
                            "align": "center",
                            "margin": "md"
                        }
                    ],
                    "paddingAll": "20px",
                    "backgroundColor": C['card']
                }
            }
        ]
    }

def question_card(game_name, question, round_num, total_rounds):
    """Game question card"""
    return {
        "type": "bubble",
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
                            "size": "lg",
                            "color": C['primary']
                        },
                        {
                            "type": "text",
                            "text": f"{round_num}/{total_rounds}",
                            "size": "sm",
                            "color": C['muted'],
                            "align": "end"
                        }
                    ]
                },
                {
                    "type": "separator",
                    "margin": "md",
                    "color": C['border']
                },
                {
                    "type": "text",
                    "text": question,
                    "wrap": True,
                    "color": C['text'],
                    "size": "md",
                    "margin": "lg"
                }
            ],
            "backgroundColor": C['card'],
            "paddingAll": "20px"
        }
    }

def result_card(title, message, points=None, success=True):
    """Result card"""
    color = C['success'] if success else C['error']
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
            "color": C['border']
        },
        {
            "type": "text",
            "text": message,
            "wrap": True,
            "color": C['text'],
            "size": "md",
            "margin": "md",
            "align": "center"
        }
    ]
    
    if points is not None:
        contents.append({
            "type": "text",
            "text": f"النقاط: {points:+d}",
            "color": C['primary'],
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
            "backgroundColor": C['card'],
            "paddingAll": "20px"
        }
    }

def stats_card(name, points, played, won):
    """Player statistics card"""
    win_rate = (won / played * 100) if played > 0 else 0
    
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
                    "color": C['primary'],
                    "align": "center"
                },
                {
                    "type": "separator",
                    "margin": "md",
                    "color": C['border']
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        _stat_row("الاسم", name, C['text']),
                        _stat_row("النقاط", str(points), C['primary']),
                        _stat_row("الألعاب", str(played), C['text']),
                        _stat_row("الفوز", str(won), C['success']),
                        _stat_row("نسبة الفوز", f"{win_rate:.1f}%", C['muted'])
                    ],
                    "margin": "lg",
                    "spacing": "md"
                }
            ],
            "backgroundColor": C['card'],
            "paddingAll": "20px"
        }
    }

def ranks_card(players):
    """Leaderboard card"""
    contents = [
        {
            "type": "text",
            "text": "المتصدرون",
            "weight": "bold",
            "size": "xl",
            "color": C['primary'],
            "align": "center"
        },
        {
            "type": "separator",
            "margin": "md",
            "color": C['border']
        }
    ]
    
    for i, player in enumerate(players, 1):
        rank_color = {1: C['primary'], 2: C['text'], 3: C['muted']}.get(i, C['secondary'])
        contents.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": f"{i}.",
                    "size": "sm",
                    "color": rank_color,
                    "flex": 1
                },
                {
                    "type": "text",
                    "text": player['name'],
                    "size": "sm",
                    "color": C['text'],
                    "flex": 4
                },
                {
                    "type": "text",
                    "text": str(player['points']),
                    "size": "sm",
                    "color": C['primary'],
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
            "backgroundColor": C['card'],
            "paddingAll": "20px"
        }
    }

def _stat_row(label, value, color):
    """Helper for stat rows"""
    return {
        "type": "box",
        "layout": "horizontal",
        "contents": [
            {
                "type": "text",
                "text": f"{label}:",
                "color": C['muted'],
                "flex": 2
            },
            {
                "type": "text",
                "text": value,
                "color": color,
                "flex": 3
            }
        ]
    }
