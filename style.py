from linebot.models import FlexSendMessage
from rules import COLORS, GAMES_INFO

def create_welcome_card():
    bubble1 = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "مرحبا بك في بوت الحوت",
                    "weight": "bold",
                    "size": "xl",
                    "color": COLORS['primary'],
                    "align": "center"
                },
                {
                    "type": "separator",
                    "margin": "md",
                    "color": COLORS['border']
                },
                {
                    "type": "text",
                    "text": "اختر لعبة:",
                    "size": "md",
                    "margin": "lg",
                    "align": "center",
                    "color": COLORS['text']
                }
            ],
            "backgroundColor": COLORS['card']
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": "اسرع", "text": "اسرع"}, "style": "primary", "color": COLORS['primary']},
                {"type": "button", "action": {"type": "message", "label": "لعبة", "text": "لعبة"}, "style": "primary", "color": COLORS['primary']},
                {"type": "button", "action": {"type": "message", "label": "سلسلة", "text": "سلسلة"}, "style": "primary", "color": COLORS['primary']},
                {"type": "button", "action": {"type": "message", "label": "اغنية", "text": "اغنية"}, "style": "primary", "color": COLORS['primary']},
                {"type": "button", "action": {"type": "message", "label": "ضد", "text": "ضد"}, "style": "primary", "color": COLORS['primary']}
            ],
            "spacing": "sm",
            "backgroundColor": COLORS['card']
        }
    }
    
    bubble2 = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "المزيد من الالعاب",
                    "weight": "bold",
                    "size": "lg",
                    "color": COLORS['primary'],
                    "align": "center"
                }
            ],
            "backgroundColor": COLORS['card']
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": "ترتيب", "text": "ترتيب"}, "style": "primary", "color": COLORS['accent']},
                {"type": "button", "action": {"type": "message", "label": "تكوين", "text": "تكوين"}, "style": "primary", "color": COLORS['accent']},
                {"type": "button", "action": {"type": "message", "label": "توافق", "text": "توافق"}, "style": "primary", "color": COLORS['accent']},
                {"type": "button", "action": {"type": "message", "label": "محادثة AI", "text": "محادثة"}, "style": "primary", "color": COLORS['accent']},
                {"type": "button", "action": {"type": "message", "label": "احصائياتي", "text": "احصائياتي"}, "style": "secondary"},
                {"type": "button", "action": {"type": "message", "label": "المتصدرين", "text": "المتصدرين"}, "style": "secondary"}
            ],
            "spacing": "sm",
            "backgroundColor": COLORS['card']
        }
    }
    
    return FlexSendMessage(
        alt_text="قائمة الالعاب",
        contents={"type": "carousel", "contents": [bubble1, bubble2]}
    )

def create_question_card(game_name, question_text, current_round, total_rounds, supports_hint):
    progress_dots = []
    for i in range(total_rounds):
        color = COLORS['primary'] if i < current_round else COLORS['muted']
        progress_dots.append({
            "type": "box",
            "layout": "vertical",
            "contents": [],
            "width": "10px",
            "height": "10px",
            "backgroundColor": color,
            "cornerRadius": "5px"
        })
        if i < total_rounds - 1:
            progress_dots.append({"type": "filler"})
    
    contents = [
        {
            "type": "text",
            "text": game_name,
            "weight": "bold",
            "size": "lg",
            "color": COLORS['primary'],
            "align": "center"
        },
        {
            "type": "box",
            "layout": "horizontal",
            "contents": progress_dots,
            "margin": "md",
            "spacing": "xs"
        },
        {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": question_text,
                    "size": "md",
                    "color": COLORS['text'],
                    "wrap": True,
                    "align": "center"
                }
            ],
            "backgroundColor": COLORS['glass'],
            "cornerRadius": "md",
            "paddingAll": "lg",
            "margin": "lg"
        },
        {
            "type": "text",
            "text": f"{current_round}/{total_rounds}",
            "size": "sm",
            "color": COLORS['muted'],
            "align": "center",
            "margin": "md"
        }
    ]
    
    if supports_hint:
        contents.append({
            "type": "text",
            "text": "اكتب 'تلميح' للحصول على مساعدة او 'تخطي' للسؤال التالي",
            "size": "xs",
            "color": COLORS['muted'],
            "align": "center",
            "margin": "md",
            "wrap": True
        })
    
    bubble = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": contents,
            "backgroundColor": COLORS['card']
        }
    }
    
    return FlexSendMessage(alt_text=f"{game_name} - السؤال {current_round}", contents=bubble)

def create_result_card(is_correct, message, points):
    color = COLORS['primary'] if is_correct else COLORS['muted']
    icon = "✓" if is_correct else "✗"
    title = "صحيح" if is_correct else "خطأ"
    
    points_text = ""
    if points > 0:
        points_text = f"+{points}"
    elif points < 0:
        points_text = str(points)
    
    contents = [
        {
            "type": "text",
            "text": icon,
            "size": "xxl",
            "color": color,
            "align": "center",
            "weight": "bold"
        },
        {
            "type": "text",
            "text": title,
            "size": "lg",
            "color": color,
            "align": "center",
            "margin": "sm"
        },
        {
            "type": "text",
            "text": message,
            "size": "md",
            "color": COLORS['text'],
            "align": "center",
            "margin": "md",
            "wrap": True
        }
    ]
    
    if points_text:
        contents.append({
            "type": "text",
            "text": points_text,
            "size": "xl",
            "color": color,
            "align": "center",
            "margin": "md",
            "weight": "bold"
        })
    
    bubble = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": contents,
            "backgroundColor": COLORS['card'],
            "paddingAll": "lg"
        }
    }
    
    return FlexSendMessage(alt_text=title, contents=bubble)

def create_stats_card(user_id, db):
    player = db.get_player(user_id)
    if not player:
        return create_welcome_card()
    
    win_rate = (player['games_won'] / player['games_played'] * 100) if player['games_played'] > 0 else 0
    rank = db.get_player_rank(user_id)
    
    bubble = {
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
                    "size": "xl",
                    "color": COLORS['primary'],
                    "align": "center"
                },
                {
                    "type": "separator",
                    "margin": "md",
                    "color": COLORS['border']
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "الاسم:", "color": COLORS['muted'], "flex": 1},
                                {"type": "text", "text": player['name'], "color": COLORS['text'], "flex": 2, "align": "end"}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "النقاط:", "color": COLORS['muted'], "flex": 1},
                                {"type": "text", "text": str(player['points']), "color": COLORS['primary'], "flex": 2, "align": "end", "weight": "bold"}
                            ],
                            "margin": "md"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "الترتيب:", "color": COLORS['muted'], "flex": 1},
                                {"type": "text", "text": f"#{rank}", "color": COLORS['accent'], "flex": 2, "align": "end"}
                            ],
                            "margin": "md"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "الالعاب:", "color": COLORS['muted'], "flex": 1},
                                {"type": "text", "text": str(player['games_played']), "color": COLORS['text'], "flex": 2, "align": "end"}
                            ],
                            "margin": "md"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "الفوز:", "color": COLORS['muted'], "flex": 1},
                                {"type": "text", "text": str(player['games_won']), "color": COLORS['text'], "flex": 2, "align": "end"}
                            ],
                            "margin": "md"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "نسبة الفوز:", "color": COLORS['muted'], "flex": 1},
                                {"type": "text", "text": f"{win_rate:.1f}%", "color": COLORS['primary'], "flex": 2, "align": "end"}
                            ],
                            "margin": "md"
                        }
                    ],
                    "backgroundColor": COLORS['glass'],
                    "cornerRadius": "md",
                    "paddingAll": "lg",
                    "margin": "lg"
                }
            ],
            "backgroundColor": COLORS['card']
        }
    }
    
    return FlexSendMessage(alt_text="احصائياتك", contents=bubble)

def create_leaderboard_card(db):
    leaders = db.get_leaderboard(10)
    
    if not leaders:
        return create_welcome_card()
    
    contents = [
        {
            "type": "text",
            "text": "المتصدرون",
            "weight": "bold",
            "size": "xl",
            "color": COLORS['primary'],
            "align": "center"
        },
        {
            "type": "separator",
            "margin": "md",
            "color": COLORS['border']
        }
    ]
    
    for i, leader in enumerate(leaders, 1):
        medal = ""
        color = COLORS['text']
        if i == 1:
            medal = "1 "
            color = "#FFD700"
        elif i == 2:
            medal = "2 "
            color = "#C0C0C0"
        elif i == 3:
            medal = "3 "
            color = "#CD7F32"
        
        contents.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": f"{medal}{i}.",
                    "color": color,
                    "flex": 1,
                    "weight": "bold" if i <= 3 else "regular"
                },
                {
                    "type": "text",
                    "text": leader['name'],
                    "color": COLORS['text'],
                    "flex": 3
                },
                {
                    "type": "text",
                    "text": str(leader['points']),
                    "color": COLORS['primary'],
                    "flex": 1,
                    "align": "end",
                    "weight": "bold"
                }
            ],
            "margin": "md"
        })
    
    bubble = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": contents,
            "backgroundColor": COLORS['card']
        }
    }
    
    return FlexSendMessage(alt_text="المتصدرون", contents=bubble)
