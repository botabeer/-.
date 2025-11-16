"""بطاقات Flex Messages"""
‏from linebot.models import QuickReply, QuickReplyButton, MessageAction
‏from typing import Optional, Dict
‏import logging

‏logger = logging.getLogger("whale-bot")

‏def get_quick_reply() -> QuickReply:
    """أزرار Quick Reply"""
‏    return QuickReply(items=[
‏        QuickReplyButton(action=MessageAction(label="▪️ سؤال", text="سؤال")),
‏        QuickReplyButton(action=MessageAction(label="▪️ تحدي", text="تحدي")),
‏        QuickReplyButton(action=MessageAction(label="▪️ اعتراف", text="اعتراف")),
‏        QuickReplyButton(action=MessageAction(label="▪️ منشن", text="منشن")),
‏        QuickReplyButton(action=MessageAction(label="▪️ أغنية", text="أغنية")),
‏        QuickReplyButton(action=MessageAction(label="▪️ لعبة", text="لعبة")),
‏        QuickReplyButton(action=MessageAction(label="▪️ سلسلة", text="سلسلة")),
‏        QuickReplyButton(action=MessageAction(label="▪️ أسرع", text="أسرع")),
‏        QuickReplyButton(action=MessageAction(label="▪️ ضد", text="ضد")),
‏        QuickReplyButton(action=MessageAction(label="▪️ تكوين", text="تكوين")),
‏        QuickReplyButton(action=MessageAction(label="▪️ اختلاف", text="اختلاف")),
‏        QuickReplyButton(action=MessageAction(label="▪️ توافق", text="توافق"))
    ])

‏def create_card(title: str, body_content: list, footer_buttons: Optional[list] = None) -> dict:
    """إنشاء بطاقة نظيفة"""
‏    from config import THEME
    
‏    body = {
‏        "type": "box",
‏        "layout": "vertical",
‏        "contents": [
            {
‏                "type": "text",
‏                "text": title,
‏                "size": "xl",
‏                "weight": "bold",
‏                "color": THEME['text'],
‏                "align": "center"
            },
            {
‏                "type": "separator",
‏                "margin": "xl",
‏                "color": THEME['border']
            }
        ],
‏        "backgroundColor": THEME['card'],
‏        "paddingAll": "24px",
‏        "spacing": "lg"
    }
    
‏    body["contents"].extend(body_content if isinstance(body_content, list) else [body_content])
    
‏    card = {
‏        "type": "bubble",
‏        "size": "kilo",
‏        "body": body
    }
    
‏    if footer_buttons and len(footer_buttons) > 0:
‏        card["footer"] = {
‏            "type": "box",
‏            "layout": "vertical",
‏            "contents": footer_buttons,
‏            "spacing": "sm",
‏            "paddingAll": "20px",
‏            "backgroundColor": THEME['card']
        }
    
‏    return card

‏def create_button(label: str, text: str, style: str = "primary") -> dict:
    """إنشاء زر"""
‏    from config import THEME
    
‏    color = THEME['accent'] if style == "primary" else THEME['text_secondary']
‏    return {
‏        "type": "button",
‏        "action": {
‏            "type": "message",
‏            "label": label,
‏            "text": text
        },
‏        "style": style,
‏        "color": color,
‏        "height": "sm"
    }

‏def get_welcome_card(name: str) -> dict:
    """بطاقة الترحيب"""
‏    from config import THEME
    
‏    return create_card("مرحباً", [
        {
‏            "type": "text",
‏            "text": name,
‏            "size": "lg",
‏            "color": THEME['text'],
‏            "align": "center",
‏            "margin": "xl",
‏            "weight": "bold"
        },
        {
‏            "type": "text",
‏            "text": "اختر من الأزرار أدناه",
‏            "size": "sm",
‏            "color": THEME['text_secondary'],
‏            "align": "center",
‏            "margin": "md"
        }
    ], [
‏        create_button("انضم", "انضم", "primary"),
‏        {"type": "separator", "margin": "md", "color": THEME['border']},
‏        create_button("المساعدة", "مساعدة", "secondary")
    ])

‏def get_help_card() -> dict:
    """بطاقة المساعدة"""
‏    from config import THEME
    
‏    return create_card("المساعدة", [
        {
‏            "type": "box",
‏            "layout": "vertical",
‏            "contents": [
                {
‏                    "type": "text",
‏                    "text": "الأوامر الأساسية",
‏                    "size": "md",
‏                    "weight": "bold",
‏                    "color": THEME['text']
                },
                {
‏                    "type": "text",
‏                    "text": "انضم - للتسجيل\nانسحب - للإلغاء\nنقاطي - الإحصائيات\nالصدارة - الترتيب\nإيقاف - إنهاء اللعبة",
‏                    "size": "xs",
‏                    "color": THEME['text_secondary'],
‏                    "wrap": True,
‏                    "margin": "md"
                }
            ],
‏            "margin": "xl",
‏            "paddingAll": "16px",
‏            "backgroundColor": THEME['bg'],
‏            "cornerRadius": "12px"
        }
    ], [
‏        create_button("نقاطي", "نقاطي", "primary"),
‏        {"type": "separator", "margin": "md", "color": THEME['border']},
‏        create_button("الصدارة", "الصدارة", "secondary")
    ])

‏def get_registration_card(name: str) -> dict:
    """بطاقة التسجيل"""
‏    from config import THEME
    
‏    return create_card("تم التسجيل ✅", [
        {
‏            "type": "text",
‏            "text": name,
‏            "size": "lg",
‏            "weight": "bold",
‏            "color": "#34C759",
‏            "align": "center",
‏            "margin": "xl"
        },
        {
‏            "type": "text",
‏            "text": "يمكنك الآن اللعب وجمع النقاط",
‏            "size": "sm",
‏            "color": THEME['text_secondary'],
‏            "align": "center",
‏            "margin": "md"
        }
‏    ], [create_button("ابدأ اللعب", "أغنية", "primary")])

‏def get_withdrawal_card(name: str) -> dict:
    """بطاقة الانسحاب"""
‏    from config import THEME
    
‏    return create_card("تم الانسحاب", [
        {
‏            "type": "text",
‏            "text": name,
‏            "size": "lg",
‏            "color": THEME['text_secondary'],
‏            "align": "center",
‏            "margin": "xl"
        },
        {
‏            "type": "text",
‏            "text": "نتمنى رؤيتك مرة أخرى",
‏            "size": "sm",
‏            "color": THEME['text_secondary'],
‏            "align": "center",
‏            "margin": "md"
        }
    ])

‏def get_stats_card(user_id: str, name: str, registered_players: set) -> dict:
    """بطاقة الإحصائيات"""
‏    from config import THEME
‏    from managers import UserManager
    
‏    stats = UserManager.get_stats(user_id)
‏    is_registered = user_id in registered_players
    
‏    status_text = "مسجل" if is_registered else "غير مسجل"
‏    status_color = "#34C759" if is_registered else THEME['text_secondary']
    
‏    if not stats:
‏        footer = [create_button("ابدأ الآن", "انضم", "primary")] if not is_registered else None
        
‏        return create_card("إحصائياتك", [
            {
‏                "type": "box",
‏                "layout": "vertical",
‏                "contents": [
                    {
‏                        "type": "text",
‏                        "text": name,
‏                        "size": "md",
‏                        "color": THEME['text'],
‏                        "align": "center",
‏                        "weight": "bold"
                    },
                    {
‏                        "type": "text",
‏                        "text": status_text,
‏                        "size": "xs",
‏                        "color": status_color,
‏                        "align": "center",
‏                        "margin": "sm"
                    }
                ],
‏                "margin": "xl"
            },
            {
‏                "type": "text",
‏                "text": "لم تبدأ بعد" if is_registered else "يجب التسجيل أولاً",
‏                "size": "md",
‏                "color": THEME['text_secondary'],
‏                "align": "center",
‏                "margin": "xl"
            }
‏        ], footer)
    
‏    win_rate = (stats['wins'] / stats['games_played'] * 100) if stats['games_played'] > 0 else 0
    
‏    footer_buttons = [create_button("الصدارة", "الصدارة", "secondary")]
‏    if is_registered:
‏        footer_buttons.extend([
‏            {"type": "separator", "margin": "md", "color": THEME['border']},
‏            create_button("انسحب", "انسحب", "secondary")
        ])
    
‏    return create_card("إحصائياتك", [
        {
‏            "type": "box",
‏            "layout": "vertical",
‏            "contents": [
                {
‏                    "type": "text",
‏                    "text": name,
‏                    "size": "md",
‏                    "color": THEME['text'],
‏                    "align": "center",
‏                    "weight": "bold"
                },
                {
‏                    "type": "text",
‏                    "text": status_text,
‏                    "size": "xs",
‏                    "color": status_color,
‏                    "align": "center",
‏                    "margin": "sm"
                }
            ],
‏            "margin": "xl"
        },
        {
‏            "type": "box",
‏            "layout": "vertical",
‏            "contents": [
                {
‏                    "type": "box",
‏                    "layout": "horizontal",
‏                    "contents": [
                        {
‏                            "type": "text",
‏                            "text": "النقاط",
‏                            "size": "sm",
‏                            "color": THEME['text_secondary'],
‏                            "flex": 1
                        },
                        {
‏                            "type": "text",
‏                            "text": str(stats['total_points']),
‏                            "size": "xxl",
‏                            "weight": "bold",
‏                            "color": THEME['accent'],
‏                            "flex": 1,
‏                            "align": "end"
                        }
                    ]
                },
‏                {"type": "separator", "margin": "lg", "color": THEME['border']},
                {
‏                    "type": "box",
‏                    "layout": "horizontal",
‏                    "contents": [
‏                        {"type": "text", "text": "الألعاب", "size": "sm", "color": THEME['text_secondary'], "flex": 1},
‏                        {"type": "text", "text": str(stats['games_played']), "size": "md", "color": THEME['text'], "flex": 1, "align": "end"}
                    ],
‏                    "margin": "lg"
                },
                {
‏                    "type": "box",
‏                    "layout": "horizontal",
‏                    "contents": [
‏                        {"type": "text", "text": "الفوز", "size": "sm", "color": THEME['text_secondary'], "flex": 1},
‏                        {"type": "text", "text": str(stats['wins']), "size": "md", "color": THEME['text'], "flex": 1, "align": "end"}
                    ],
‏                    "margin": "md"
                },
                {
‏                    "type": "box",
‏                    "layout": "horizontal",
‏                    "contents": [
‏                        {"type": "text", "text": "معدل الفوز", "size": "sm", "color": THEME['text_secondary'], "flex": 1},
‏                        {"type": "text", "text": f"{win_rate:.0f}%", "size": "md", "color": THEME['text'], "flex": 1, "align": "end"}
                    ],
‏                    "margin": "md"
                }
            ],
‏            "margin": "xl",
‏            "paddingAll": "16px",
‏            "backgroundColor": THEME['bg'],
‏            "cornerRadius": "12px"
        }
‏    ], footer_buttons)

‏def get_leaderboard_card() -> dict:
    """بطاقة الصدارة"""
‏    from config import THEME
‏    from managers import UserManager
    
‏    leaders = UserManager.get_leaderboard()
    
‏    if not leaders:
‏        return create_card("لوحة الصدارة", [
            {
‏                "type": "text",
‏                "text": "لا توجد بيانات",
‏                "size": "md",
‏                "color": THEME['text_secondary'],
‏                "align": "center",
‏                "margin": "xl"
            }
        ])
    
‏    items = []
‏    for i, leader in enumerate(leaders, 1):
‏        rank = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else str(i)
        
‏        items.append({
‏            "type": "box",
‏            "layout": "horizontal",
‏            "contents": [
‏                {"type": "text", "text": rank, "size": "sm", "weight": "bold", "flex": 0, "color": THEME['text']},
‏                {"type": "text", "text": leader['display_name'], "size": "sm", "flex": 3, "margin": "md", "wrap": True, "color": THEME['text']},
‏                {"type": "text", "text": str(leader['total_points']), "size": "sm", "weight": "bold", "flex": 1, "align": "end", "color": THEME['accent']}
            ],
‏            "paddingAll": "12px",
‏            "backgroundColor": THEME['bg'] if i > 3 else THEME['card'],
‏            "cornerRadius": "12px",
‏            "margin": "sm" if i > 1 else "md"
        })
    
‏    return create_card("لوحة الصدارة 🏆", [
        {
‏            "type": "text",
‏            "text": "أفضل اللاعبين",
‏            "size": "sm",
‏            "color": THEME['text_secondary'],
‏            "align": "center",
‏            "margin": "md"
        },
        {
‏            "type": "box",
‏            "layout": "vertical",
‏            "contents": items,
‏            "margin": "lg"
        }
    
