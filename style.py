from linebot.models import FlexSendMessage, QuickReply, QuickReplyButton, MessageAction
from rules import COLORS, GAMES_INFO

# ألوان النظام الجديد - مستوحاة من الشعار
THEME = {
    'bg': '#0a1628',
    'card': '#1a2332',
    'glass': 'rgba(77, 208, 225, 0.1)',
    'primary': '#4DD0E1',
    'secondary': '#26C6DA',
    'accent': '#00BCD4',
    'text': '#FFFFFF',
    'muted': '#78909C',
    'border': '#263238',
    'glow': '#4DD0E1',
    'success': '#00E676',
    'error': '#FF5252'
}

def create_quick_buttons():
    """أزرار سريعة ثابتة"""
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="🏠 البداية", text="ابدأ")),
        QuickReplyButton(action=MessageAction(label="❓ مساعدة", text="مساعدة")),
        QuickReplyButton(action=MessageAction(label="📊 نقاطي", text="نقاطي")),
        QuickReplyButton(action=MessageAction(label="🏆 الصدارة", text="الصدارة")),
        QuickReplyButton(action=MessageAction(label="🎮 ألعاب", text="العاب")),
        QuickReplyButton(action=MessageAction(label="🎉 ترفيه", text="ترفيه"))
    ])

def create_welcome_card():
    """شاشة الترحيب الرئيسية"""
    bubble = {
        "type": "bubble",
        "size": "giga",
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
                            "url": "https://i.ibb.co/placeholder-logo.png",
                            "size": "xs",
                            "aspectRatio": "1:1",
                            "aspectMode": "cover",
                            "margin": "none"
                        }
                    ],
                    "width": "80px",
                    "height": "80px",
                    "cornerRadius": "50px",
                    "backgroundColor": THEME['glass'],
                    "margin": "none",
                    "position": "relative",
                    "offsetTop": "none"
                },
                {
                    "type": "text",
                    "text": "بوت الحوت",
                    "weight": "bold",
                    "size": "xxl",
                    "color": THEME['primary'],
                    "align": "center",
                    "margin": "xl",
                    "style": "normal",
                    "decoration": "none"
                },
                {
                    "type": "text",
                    "text": "✨ اختر ما تريد",
                    "size": "md",
                    "color": THEME['text'],
                    "align": "center",
                    "margin": "md"
                },
                {
                    "type": "separator",
                    "margin": "xl",
                    "color": THEME['border']
                }
            ],
            "paddingAll": "30px",
            "backgroundColor": THEME['card'],
            "spacing": "none"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "button",
                            "action": {"type": "message", "label": "🎮 الألعاب", "text": "العاب"},
                            "style": "primary",
                            "color": THEME['primary'],
                            "height": "sm"
                        },
                        {
                            "type": "button",
                            "action": {"type": "message", "label": "🎉 المحتوى الترفيهي", "text": "ترفيه"},
                            "style": "primary",
                            "color": THEME['secondary'],
                            "height": "sm",
                            "margin": "sm"
                        },
                        {
                            "type": "button",
                            "action": {"type": "message", "label": "📊 احصائياتي", "text": "نقاطي"},
                            "style": "secondary",
                            "height": "sm",
                            "margin": "sm"
                        },
                        {
                            "type": "button",
                            "action": {"type": "message", "label": "🏆 المتصدرين", "text": "الصدارة"},
                            "style": "secondary",
                            "height": "sm",
                            "margin": "sm"
                        },
                        {
                            "type": "button",
                            "action": {"type": "message", "label": "❓ المساعدة", "text": "مساعدة"},
                            "style": "link",
                            "height": "sm",
                            "margin": "md"
                        }
                    ]
                }
            ],
            "paddingAll": "20px",
            "backgroundColor": THEME['card'],
            "spacing": "none"
        }
    }
    
    return FlexSendMessage(
        alt_text="🐋 بوت الحوت - القائمة الرئيسية",
        contents=bubble,
        quick_reply=create_quick_buttons()
    )

def create_games_menu():
    """قائمة الألعاب"""
    bubble = {
        "type": "bubble",
        "size": "giga",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "🎮 الألعاب",
                    "weight": "bold",
                    "size": "xl",
                    "color": THEME['primary'],
                    "align": "center"
                },
                {
                    "type": "separator",
                    "margin": "lg",
                    "color": THEME['border']
                },
                {
                    "type": "text",
                    "text": "اختر لعبتك المفضلة",
                    "size": "sm",
                    "color": THEME['muted'],
                    "align": "center",
                    "margin": "md"
                }
            ],
            "paddingAll": "25px",
            "backgroundColor": THEME['card']
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": "⚡ اسرع", "text": "اسرع"}, "style": "primary", "color": THEME['primary'], "height": "sm"},
                {"type": "button", "action": {"type": "message", "label": "🎯 لعبة", "text": "لعبة"}, "style": "primary", "color": THEME['primary'], "height": "sm", "margin": "sm"},
                {"type": "button", "action": {"type": "message", "label": "⛓️ سلسلة", "text": "سلسلة"}, "style": "primary", "color": THEME['primary'], "height": "sm", "margin": "sm"},
                {"type": "button", "action": {"type": "message", "label": "🎵 اغنية", "text": "اغنية"}, "style": "primary", "color": THEME['primary'], "height": "sm", "margin": "sm"},
                {"type": "button", "action": {"type": "message", "label": "🔄 ضد", "text": "ضد"}, "style": "primary", "color": THEME['secondary'], "height": "sm", "margin": "sm"},
                {"type": "button", "action": {"type": "message", "label": "📝 ترتيب", "text": "ترتيب"}, "style": "primary", "color": THEME['secondary'], "height": "sm", "margin": "sm"},
                {"type": "button", "action": {"type": "message", "label": "🧩 تكوين", "text": "تكوين"}, "style": "primary", "color": THEME['secondary'], "height": "sm", "margin": "sm"},
                {"type": "button", "action": {"type": "message", "label": "💕 توافق", "text": "توافق"}, "style": "secondary", "height": "sm", "margin": "sm"},
                {"type": "button", "action": {"type": "message", "label": "🤖 محادثة AI", "text": "محادثة"}, "style": "secondary", "height": "sm", "margin": "sm"},
                {"type": "button", "action": {"type": "message", "label": "🏠 رجوع", "text": "ابدأ"}, "style": "link", "height": "sm", "margin": "md"}
            ],
            "paddingAll": "20px",
            "backgroundColor": THEME['card'],
            "spacing": "none"
        }
    }
    
    return FlexSendMessage(
        alt_text="🎮 قائمة الألعاب",
        contents=bubble,
        quick_reply=create_quick_buttons()
    )

def create_entertainment_menu():
    """قائمة المحتوى الترفيهي"""
    bubble = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "🎉 المحتوى الترفيهي",
                    "weight": "bold",
                    "size": "xl",
                    "color": THEME['primary'],
                    "align": "center"
                },
                {
                    "type": "separator",
                    "margin": "lg",
                    "color": THEME['border']
                },
                {
                    "type": "text",
                    "text": "محتوى ممتع لجلساتكم",
                    "size": "sm",
                    "color": THEME['muted'],
                    "align": "center",
                    "margin": "md"
                }
            ],
            "paddingAll": "25px",
            "backgroundColor": THEME['card']
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": "❓ سؤال", "text": "سؤال"}, "style": "primary", "color": THEME['accent'], "height": "sm"},
                {"type": "button", "action": {"type": "message", "label": "🎯 تحدي", "text": "تحدي"}, "style": "primary", "color": THEME['accent'], "height": "sm", "margin": "sm"},
                {"type": "button", "action": {"type": "message", "label": "💬 اعتراف", "text": "اعتراف"}, "style": "primary", "color": THEME['accent'], "height": "sm", "margin": "sm"},
                {"type": "button", "action": {"type": "message", "label": "📢 منشن", "text": "منشن"}, "style": "primary", "color": THEME['accent'], "height": "sm", "margin": "sm"},
                {"type": "button", "action": {"type": "message", "label": "🏠 رجوع", "text": "ابدأ"}, "style": "link", "height": "sm", "margin": "md"}
            ],
            "paddingAll": "20px",
            "backgroundColor": THEME['card'],
            "spacing": "none"
        }
    }
    
    return FlexSendMessage(
        alt_text="🎉 المحتوى الترفيهي",
        contents=bubble,
        quick_reply=create_quick_buttons()
    )

def create_question_card(game_name, question_text, current_round, total_rounds, supports_hint):
    """بطاقة السؤال - تصميم ثري دي زجاجي"""
    progress_dots = []
    for i in range(total_rounds):
        color = THEME['glow'] if i < current_round else THEME['muted']
        progress_dots.append({
            "type": "box",
            "layout": "vertical",
            "contents": [],
            "width": "12px",
            "height": "12px",
            "backgroundColor": color,
            "cornerRadius": "6px"
        })
        if i < total_rounds - 1:
            progress_dots.append({"type": "filler"})
    
    hint_text = []
    if supports_hint:
        hint_text = [
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {"type": "text", "text": "💡", "size": "sm", "flex": 0, "margin": "none"},
                    {"type": "text", "text": "تلميح", "size": "xs", "color": THEME['muted'], "margin": "sm"},
                    {"type": "filler"},
                    {"type": "text", "text": "⏭️", "size": "sm", "flex": 0, "margin": "none"},
                    {"type": "text", "text": "تخطي", "size": "xs", "color": THEME['muted'], "margin": "sm"}
                ],
                "margin": "lg",
                "paddingAll": "8px",
                "backgroundColor": THEME['glass'],
                "cornerRadius": "md"
            }
        ]
    
    bubble = {
        "type": "bubble",
        "size": "giga",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": game_name,
                    "weight": "bold",
                    "size": "lg",
                    "color": THEME['primary'],
                    "align": "center"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": progress_dots,
                    "margin": "lg",
                    "spacing": "sm"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": question_text,
                            "size": "md",
                            "color": THEME['text'],
                            "wrap": True,
                            "align": "center",
                            "weight": "bold"
                        }
                    ],
                    "backgroundColor": THEME['glass'],
                    "cornerRadius": "lg",
                    "paddingAll": "20px",
                    "margin": "xl",
                    "borderWidth": "1px",
                    "borderColor": THEME['primary']
                },
                {
                    "type": "text",
                    "text": f"السؤال {current_round} من {total_rounds}",
                    "size": "xs",
                    "color": THEME['muted'],
                    "align": "center",
                    "margin": "lg"
                }
            ] + hint_text,
            "paddingAll": "25px",
            "backgroundColor": THEME['card']
        }
    }
    
    return FlexSendMessage(
        alt_text=f"{game_name} - السؤال {current_round}",
        contents=bubble,
        quick_reply=create_quick_buttons()
    )

def create_result_card(is_correct, message, points):
    """بطاقة النتيجة"""
    color = THEME['success'] if is_correct else THEME['error']
    icon = "✅" if is_correct else "❌"
    title = "صحيح" if is_correct else "خطأ"
    
    points_box = []
    if points != 0:
        points_text = f"+{points}" if points > 0 else str(points)
        points_box = [
            {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": points_text,
                        "size": "xxl",
                        "color": color,
                        "align": "center",
                        "weight": "bold"
                    }
                ],
                "backgroundColor": THEME['glass'],
                "cornerRadius": "lg",
                "paddingAll": "15px",
                "margin": "lg",
                "borderWidth": "2px",
                "borderColor": color
            }
        ]
    
    bubble = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": icon,
                    "size": "xxl",
                    "align": "center"
                },
                {
                    "type": "text",
                    "text": title,
                    "size": "xl",
                    "color": color,
                    "align": "center",
                    "margin": "md",
                    "weight": "bold"
                },
                {
                    "type": "separator",
                    "margin": "lg",
                    "color": THEME['border']
                },
                {
                    "type": "text",
                    "text": message,
                    "size": "sm",
                    "color": THEME['text'],
                    "align": "center",
                    "margin": "lg",
                    "wrap": True
                }
            ] + points_box,
            "backgroundColor": THEME['card'],
            "paddingAll": "25px"
        }
    }
    
    return FlexSendMessage(
        alt_text=title,
        contents=bubble,
        quick_reply=create_quick_buttons()
    )

def create_stats_card(user_id, db):
    """بطاقة الإحصائيات"""
    player = db.get_player(user_id)
    if not player:
        return create_welcome_card()
    
    win_rate = (player['games_won'] / player['games_played'] * 100) if player['games_played'] > 0 else 0
    rank = db.get_player_rank(user_id)
    
    bubble = {
        "type": "bubble",
        "size": "giga",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "📊 احصائياتك",
                    "weight": "bold",
                    "size": "xl",
                    "color": THEME['primary'],
                    "align": "center"
                },
                {
                    "type": "separator",
                    "margin": "lg",
                    "color": THEME['border']
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        _create_stat_row("👤 الاسم", player['name'], THEME['text']),
                        _create_stat_row("⭐ النقاط", str(player['points']), THEME['primary']),
                        _create_stat_row("🏆 الترتيب", f"#{rank}", THEME['accent']),
                        _create_stat_row("🎮 الألعاب", str(player['games_played']), THEME['text']),
                        _create_stat_row("✅ الفوز", str(player['games_won']), THEME['success']),
                        _create_stat_row("📈 نسبة الفوز", f"{win_rate:.1f}%", THEME['primary'])
                    ],
                    "backgroundColor": THEME['glass'],
                    "cornerRadius": "lg",
                    "paddingAll": "20px",
                    "margin": "lg",
                    "spacing": "md",
                    "borderWidth": "1px",
                    "borderColor": THEME['primary']
                }
            ],
            "backgroundColor": THEME['card'],
            "paddingAll": "25px"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": "🏠 الرئيسية", "text": "ابدأ"}, "style": "primary", "color": THEME['primary'], "height": "sm"}
            ],
            "paddingAll": "20px",
            "backgroundColor": THEME['card']
        }
    }
    
    return FlexSendMessage(
        alt_text="📊 احصائياتك",
        contents=bubble,
        quick_reply=create_quick_buttons()
    )

def _create_stat_row(label, value, color):
    """إنشاء صف احصائيات"""
    return {
        "type": "box",
        "layout": "horizontal",
        "contents": [
            {"type": "text", "text": label, "size": "sm", "color": THEME['muted'], "flex": 3},
            {"type": "text", "text": value, "size": "sm", "color": color, "flex": 2, "align": "end", "weight": "bold"}
        ]
    }

def create_leaderboard_card(db):
    """بطاقة المتصدرين"""
    leaders = db.get_leaderboard(10)
    
    if not leaders:
        return create_welcome_card()
    
    leader_boxes = []
    for i, leader in enumerate(leaders, 1):
        medal = ""
        color = THEME['text']
        if i == 1:
            medal = "🥇 "
            color = "#FFD700"
        elif i == 2:
            medal = "🥈 "
            color = "#C0C0C0"
        elif i == 3:
            medal = "🥉 "
            color = "#CD7F32"
        
        leader_boxes.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": f"{medal}{i}", "color": color, "flex": 1, "size": "sm", "weight": "bold"},
                {"type": "text", "text": leader['name'], "color": THEME['text'], "flex": 4, "size": "sm"},
                {"type": "text", "text": str(leader['points']), "color": THEME['primary'], "flex": 2, "align": "end", "weight": "bold", "size": "sm"}
            ],
            "paddingAll": "10px",
            "backgroundColor": THEME['glass'] if i <= 3 else "transparent",
            "cornerRadius": "md",
            "margin": "sm"
        })
    
    bubble = {
        "type": "bubble",
        "size": "giga",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "🏆 المتصدرون",
                    "weight": "bold",
                    "size": "xl",
                    "color": THEME['primary'],
                    "align": "center"
                },
                {
                    "type": "separator",
                    "margin": "lg",
                    "color": THEME['border']
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": leader_boxes,
                    "margin": "lg"
                }
            ],
            "backgroundColor": THEME['card'],
            "paddingAll": "25px"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": "🏠 الرئيسية", "text": "ابدأ"}, "style": "primary", "color": THEME['primary'], "height": "sm"}
            ],
            "paddingAll": "20px",
            "backgroundColor": THEME['card']
        }
    }
    
    return FlexSendMessage(
        alt_text="🏆 المتصدرون",
        contents=bubble,
        quick_reply=create_quick_buttons()
    )

def create_entertainment_content(content_type, text):
    """بطاقة المحتوى الترفيهي"""
    icons = {
        'سؤال': '❓',
        'تحدي': '🎯',
        'اعتراف': '💬',
        'منشن': '📢'
    }
    
    icon = icons.get(content_type, '🎉')
    
    bubble = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": f"{icon} {content_type}",
                    "weight": "bold",
                    "size": "lg",
                    "color": THEME['primary'],
                    "align": "center"
                },
                {
                    "type": "separator",
                    "margin": "lg",
                    "color": THEME['border']
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": text,
                            "size": "md",
                            "color": THEME['text'],
                            "wrap": True,
                            "align": "center"
                        }
                    ],
                    "backgroundColor": THEME['glass'],
                    "cornerRadius": "lg",
                    "paddingAll": "20px",
                    "margin": "lg",
                    "borderWidth": "1px",
                    "borderColor": THEME['accent']
                }
            ],
            "backgroundColor": THEME['card'],
            "paddingAll": "25px"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": f"🔄 {content_type} جديد", "text": content_type}, "style": "primary", "color": THEME['accent'], "height": "sm"},
                {"type": "button", "action": {"type": "message", "label": "🏠 الرئيسية", "text": "ابدأ"}, "style": "link", "height": "sm", "margin": "sm"}
            ],
            "paddingAll": "20px",
            "backgroundColor": THEME['card']
        }
    }
    
    return FlexSendMessage(
        alt_text=f"{icon} {content_type}",
        contents=bubble,
        quick_reply=create_quick_buttons()
    )

def create_help_card():
    """بطاقة المساعدة"""
    bubble = {
        "type": "bubble",
        "size": "giga",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "❓ المساعدة",
                    "weight": "bold",
                    "size": "xl",
                    "color": THEME['primary'],
                    "align": "center"
                },
                {
                    "type": "separator",
                    "margin": "lg",
                    "color": THEME['border']
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        _create_help_item("🎮", "الألعاب", "العب مع أصدقائك وتنافس"),
                        _create_help_item("🎉", "الترفيه", "محتوى ممتع للجلسات"),
                        _create_help_item("✅", "انضم", "اكتب 'انضم' للمشاركة"),
                        _create_help_item("💡", "تلميح", "اكتب 'تلميح' للمساعدة"),
                        _create_help_item("⏭️", "تخطي", "اكتب 'تخطي' للسؤال التالي"),
                        _create_help_item("🛑", "إيقاف", "اكتب 'ايقاف' لإنهاء اللعبة")
                    ],
                    "spacing": "md",
                    "margin": "lg"
                }
            ],
            "backgroundColor": THEME['card'],
            "paddingAll": "25px"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": "🏠 الرئيسية", "text": "ابدأ"}, "style": "primary", "color": THEME['primary'], "height": "sm"}
            ],
            "paddingAll": "20px",
            "backgroundColor": THEME['card']
        }
    }
    
    return FlexSendMessage(
        alt_text="❓ المساعدة",
        contents=bubble,
        quick_reply=create_quick_buttons()
    )

def _create_help_item(icon, title, desc):
    """عنصر مساعدة"""
    return {
        "type": "box",
        "layout": "horizontal",
        "contents": [
            {"type": "text", "text": icon, "size": "lg", "flex": 0, "margin": "none"},
            {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": title, "size": "sm", "color": THEME['text'], "weight": "bold"},
                    {"type": "text", "text": desc, "size": "xs", "color": THEME['muted'], "wrap": True}
                ],
                "margin": "md"
            }
        ],
        "backgroundColor": THEME['glass'],
        "cornerRadius": "md",
        "paddingAll": "12px"
    }
