"""
═══════════════════════════════════════════════════════════════
بوت الحوت - Cosmic Depth Edition
النسخة: 3.1.0 - تصميم ثلاثي الأبعاد
© Bot Al-Hout 2025
═══════════════════════════════════════════════════════════════
"""

# ═══════════════════════════════════════════════════════════════
# 🔧 التعديلات المطلوبة على ملف app.py الحالي
# ═══════════════════════════════════════════════════════════════

"""
خطوة 1️⃣: أضف هذا في قسم الثوابت (بعد الـ imports)
"""

# لوحة ألوان Cosmic Depth
COSMIC = {
    'primary': '#00d4ff',
    'secondary': '#0099ff',
    'bg_main': '#0a0e27',
    'bg_card': '#1a1f3a',
    'bg_elevated': '#2a2f45',
    'text_main': '#ffffff',
    'text_secondary': '#8b9dc3',
    'text_tertiary': '#6c7a8e',
    'text_muted': '#4a5568',
    'success': '#34C759',
    'warning': '#FF9500',
    'error': '#FF3B30',
    'border': '#2a2f45'
}

# رابط شعار برج الحوت (استبدله بصورتك)
PISCES_LOGO = "https://i.imgur.com/pisces-cosmic.png"


"""
خطوة 2️⃣: استبدل قسم Flex Cards بالكامل
احذف من "# ═══════════════ Flex Cards" إلى نهاية القسم
والصق هذا الكود بدلاً منه:
"""

# ═══════════════════════════════════════════════════════════════
# Cosmic Flex Cards
# ═══════════════════════════════════════════════════════════════

def welcome_card():
    return {
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
                            "url": PISCES_LOGO,
                            "size": "160px",
                            "aspectMode": "cover",
                            "aspectRatio": "1:1",
                            "backgroundColor": COSMIC['bg_card']
                        }
                    ],
                    "width": "180px",
                    "height": "180px",
                    "cornerRadius": "90px",
                    "borderWidth": "4px",
                    "borderColor": COSMIC['primary'],
                    "backgroundColor": COSMIC['bg_card'],
                    "alignItems": "center",
                    "justifyContent": "center",
                    "margin": "xxl"
                },
                {
                    "type": "text",
                    "text": "بوت الحوت",
                    "size": "3xl",
                    "weight": "bold",
                    "color": COSMIC['text_main'],
                    "align": "center",
                    "margin": "xl"
                },
                {
                    "type": "text",
                    "text": "3D Gaming Experience",
                    "size": "lg",
                    "color": COSMIC['text_secondary'],
                    "align": "center",
                    "margin": "md",
                    "weight": "bold"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "نظام ألعاب تفاعلية للمجموعات",
                            "size": "sm",
                            "color": COSMIC['text_tertiary'],
                            "align": "center",
                            "wrap": True
                        }
                    ],
                    "paddingAll": "md",
                    "backgroundColor": COSMIC['bg_card'],
                    "cornerRadius": "12px",
                    "margin": "lg",
                    "borderWidth": "1px",
                    "borderColor": COSMIC['border']
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "⚡ الألعاب المتوفرة", "size": "md", "weight": "bold", "color": COSMIC['primary']},
                        {"type": "separator", "margin": "md", "color": COSMIC['border']},
                        {"type": "text", "text": "▫️ أغنية • لعبة • سلسلة • أسرع", "size": "xs", "color": COSMIC['text_secondary'], "wrap": True, "margin": "md"},
                        {"type": "text", "text": "▫️ ضد • تكوين • ترتيب • كلمة • لون", "size": "xs", "color": COSMIC['text_secondary'], "wrap": True, "margin": "sm"},
                        {"type": "separator", "margin": "md", "color": COSMIC['border']},
                        {"type": "text", "text": "🎭 للتسلية", "size": "md", "weight": "bold", "color": COSMIC['primary'], "margin": "md"},
                        {"type": "text", "text": "▫️ سؤال • تحدي • اعتراف • منشن", "size": "xs", "color": COSMIC['text_secondary'], "wrap": True, "margin": "sm"}
                    ],
                    "backgroundColor": COSMIC['bg_card'],
                    "cornerRadius": "16px",
                    "paddingAll": "lg",
                    "margin": "lg",
                    "borderWidth": "2px",
                    "borderColor": COSMIC['border']
                },
                {"type": "text", "text": "© Bot Al-Hout 2025", "size": "xs", "color": COSMIC['text_muted'], "align": "center", "margin": "lg"}
            ],
            "paddingAll": "xl",
            "backgroundColor": COSMIC['bg_main']
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": "⚡ ابدأ المغامرة", "text": "ابدأ"}, "style": "primary", "color": COSMIC['primary'], "height": "sm"},
                {"type": "button", "action": {"type": "message", "label": "📖 المساعدة", "text": "مساعدة"}, "style": "secondary", "height": "sm", "margin": "sm"}
            ],
            "paddingAll": "lg",
            "backgroundColor": COSMIC['bg_main']
        }
    }


def help_card():
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "📖 مركز المساعدة", "size": "xxl", "weight": "bold", "color": COSMIC['text_main'], "align": "center"},
                {"type": "separator", "margin": "lg", "color": COSMIC['border']},
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "🎮 الألعاب", "size": "lg", "weight": "bold", "color": COSMIC['primary']},
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {"type": "text", "text": "▫️ أغنية - خمن المغني", "size": "sm", "color": COSMIC['text_secondary'], "wrap": True},
                                {"type": "text", "text": "▫️ لعبة - إنسان حيوان نبات", "size": "sm", "color": COSMIC['text_secondary'], "wrap": True, "margin": "sm"},
                                {"type": "text", "text": "▫️ سلسلة - كلمة بآخر حرف", "size": "sm", "color": COSMIC['text_secondary'], "wrap": True, "margin": "sm"},
                                {"type": "text", "text": "▫️ أسرع - أسرع إجابة", "size": "sm", "color": COSMIC['text_secondary'], "wrap": True, "margin": "sm"}
                            ],
                            "margin": "md",
                            "paddingStart": "md"
                        }
                    ],
                    "backgroundColor": COSMIC['bg_card'],
                    "cornerRadius": "16px",
                    "paddingAll": "lg",
                    "margin": "lg",
                    "borderWidth": "2px",
                    "borderColor": COSMIC['border']
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "👤 الحساب", "size": "lg", "weight": "bold", "color": COSMIC['primary']},
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {"type": "text", "text": "▫️ انضم - للتسجيل", "size": "sm", "color": COSMIC['text_secondary'], "wrap": True},
                                {"type": "text", "text": "▫️ نقاطي - عرض النقاط", "size": "sm", "color": COSMIC['text_secondary'], "wrap": True, "margin": "sm"},
                                {"type": "text", "text": "▫️ الصدارة - المتصدرين", "size": "sm", "color": COSMIC['text_secondary'], "wrap": True, "margin": "sm"}
                            ],
                            "margin": "md",
                            "paddingStart": "md"
                        }
                    ],
                    "backgroundColor": COSMIC['bg_card'],
                    "cornerRadius": "16px",
                    "paddingAll": "lg",
                    "margin": "md",
                    "borderWidth": "2px",
                    "borderColor": COSMIC['border']
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "⚙️ النظام", "size": "lg", "weight": "bold", "color": COSMIC['primary']},
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {"type": "text", "text": "▫️ لمح - تلميح (-1 نقطة)", "size": "sm", "color": COSMIC['text_secondary'], "wrap": True},
                                {"type": "text", "text": "▫️ جاوب - عرض الحل", "size": "sm", "color": COSMIC['text_secondary'], "wrap": True, "margin": "sm"},
                                {"type": "text", "text": "▫️ إيقاف - إنهاء اللعبة", "size": "sm", "color": COSMIC['text_secondary'], "wrap": True, "margin": "sm"}
                            ],
                            "margin": "md",
                            "paddingStart": "md"
                        }
                    ],
                    "backgroundColor": COSMIC['bg_card'],
                    "cornerRadius": "16px",
                    "paddingAll": "lg",
                    "margin": "md",
                    "borderWidth": "2px",
                    "borderColor": COSMIC['border']
                },
                {"type": "text", "text": "© Bot Al-Hout 2025", "size": "xs", "color": COSMIC['text_muted'], "align": "center", "margin": "lg"}
            ],
            "paddingAll": "xl",
            "backgroundColor": COSMIC['bg_main']
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": "⚡ ابدأ اللعب", "text": "أغنية"}, "style": "primary", "color": COSMIC['primary'], "height": "sm"}
            ],
            "paddingAll": "lg",
            "backgroundColor": COSMIC['bg_main']
        }
    }


def stats_card(user_id, name, is_reg):
    if not is_reg:
        return {
            "type": "bubble",
            "size": "kilo",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "⚠️", "size": "xxl", "align": "center"},
                    {"type": "text", "text": "غير مسجل", "size": "xl", "weight": "bold", "color": COSMIC['text_main'], "align": "center", "margin": "md"},
                    {"type": "separator", "margin": "lg", "color": COSMIC['border']},
                    {"type": "text", "text": name, "size": "md", "color": COSMIC['text_secondary'], "align": "center", "margin": "lg"},
                    {"type": "text", "text": "سجل أولاً لتبدأ اللعب", "size": "sm", "color": COSMIC['text_tertiary'], "align": "center", "margin": "md"}
                ],
                "paddingAll": "xl",
                "backgroundColor": COSMIC['bg_main']
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "button", "action": {"type": "message", "label": "⚡ انضم الآن", "text": "انضم"}, "style": "primary", "color": COSMIC['primary']}
                ],
                "paddingAll": "lg",
                "backgroundColor": COSMIC['bg_main']
            }
        }
    
    stats = get_stats(user_id)
    if not stats:
        stats = {'total_points': 0, 'games_played': 0, 'wins': 0}
    
    points = stats['total_points']
    games = stats['games_played']
    wins = stats['wins']
    win_rate = (wins / games * 100) if games > 0 else 0
    
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
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {"type": "text", "text": "مرحباً", "size": "sm", "color": COSMIC['text_secondary']},
                                {"type": "text", "text": name[:15], "size": "xxl", "weight": "bold", "color": COSMIC['text_main'], "margin": "xs", "wrap": True}
                            ],
                            "flex": 1
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [{"type": "text", "text": "🏆", "size": "xxl", "align": "center"}],
                            "width": "60px",
                            "height": "60px",
                            "backgroundColor": COSMIC['bg_card'],
                            "cornerRadius": "16px",
                            "justifyContent": "center",
                            "borderWidth": "3px",
                            "borderColor": COSMIC['primary']
                        }
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {"type": "text", "text": "النقاط", "size": "xs", "color": COSMIC['text_secondary'], "align": "center"},
                                {"type": "text", "text": f"{points:,}", "size": "xxl", "weight": "bold", "color": COSMIC['primary'], "align": "center", "margin": "md"},
                                {"type": "text", "text": "⭐", "size": "lg", "align": "center", "margin": "sm"}
                            ],
                            "backgroundColor": COSMIC['bg_card'],
                            "cornerRadius": "16px",
                            "paddingAll": "lg",
                            "flex": 1,
                            "borderWidth": "2px",
                            "borderColor": COSMIC['border']
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {"type": "text", "text": "الألعاب", "size": "xs", "color": COSMIC['text_secondary'], "align": "center"},
                                {"type": "text", "text": str(games), "size": "xxl", "weight": "bold", "color": COSMIC['primary'], "align": "center", "margin": "md"},
                                {"type": "text", "text": "🎮", "size": "lg", "align": "center", "margin": "sm"}
                            ],
                            "backgroundColor": COSMIC['bg_card'],
                            "cornerRadius": "16px",
                            "paddingAll": "lg",
                            "flex": 1,
                            "margin": "md",
                            "borderWidth": "2px",
                            "borderColor": COSMIC['border']
                        }
                    ],
                    "margin": "xl"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "معدل الفوز", "size": "sm", "color": COSMIC['text_secondary'], "flex": 1},
                                {"type": "text", "text": f"{win_rate:.0f}%", "size": "sm", "weight": "bold", "color": COSMIC['primary'], "align": "end"}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "box", "layout": "vertical", "contents": [], "backgroundColor": COSMIC['primary'], "height": "8px", "cornerRadius": "4px", "width": f"{min(win_rate, 100):.0f}%"}
                            ],
                            "backgroundColor": COSMIC['border'],
                            "height": "8px",
                            "cornerRadius": "4px",
                            "margin": "sm"
                        }
                    ],
                    "backgroundColor": COSMIC['bg_card'],
                    "cornerRadius": "12px",
                    "paddingAll": "md",
                    "margin": "xl",
                    "borderWidth": "1px",
                    "borderColor": COSMIC['border']
                }
            ],
            "paddingAll": "xl",
            "backgroundColor": COSMIC['bg_main']
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": "⚡ ابدأ اللعب", "text": "أغنية"}, "style": "primary", "color": COSMIC['primary'], "height": "sm"},
                {"type": "button", "action": {"type": "message", "label": "🏆 الصدارة", "text": "الصدارة"}, "style": "secondary", "height": "sm", "margin": "sm"}
            ],
            "paddingAll": "lg",
            "backgroundColor": COSMIC['bg_main']
        }
    }


def leaderboard_card():
    leaders = get_leaderboard()
    
    if not leaders:
        return {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "🏆 لوحة الصدارة", "size": "xxl", "weight": "bold", "color": COSMIC['text_main'], "align": "center"},
                    {"type": "separator", "margin": "lg", "color": COSMIC['border']},
                    {"type": "text", "text": "لا توجد بيانات بعد", "size": "md", "color": COSMIC['text_secondary'], "align": "center", "margin": "xl"}
                ],
                "paddingAll": "xl",
                "backgroundColor": COSMIC['bg_main']
            }
        }
    
    items = []
    for i, leader in enumerate(leaders, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else str(i)
        
        items.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": emoji, "size": "md", "weight": "bold", "flex": 0, "color": COSMIC['primary']},
                {"type": "text", "text": leader['display_name'][:20], "size": "sm", "flex": 3, "margin": "md", "wrap": True, "color": COSMIC['text_main']},
                {"type": "text", "text": f"{leader['total_points']:,}", "size": "sm", "weight": "bold", "flex": 1, "align": "end", "color": COSMIC['primary']}
            ],
            "backgroundColor": COSMIC['bg_card'] if i > 3 else COSMIC['bg_elevated'],
            "cornerRadius": "12px",
            "paddingAll": "md",
            "margin": "sm" if i > 1 else "md",
            "borderWidth": "2px" if i <= 3 else "1px",
            "borderColor": COSMIC['primary'] if i <= 3 else COSMIC['border']
        })
    
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "🏆 لوحة الصدارة", "size": "xxl", "weight": "bold", "color": COSMIC['text_main'], "align": "center"},
                {"type": "separator", "margin": "lg", "color": COSMIC['border']},
                {"type": "text", "text": "أفضل اللاعبين", "size": "sm", "color": COSMIC['text_secondary'], "align": "center", "margin": "md"},
                {"type": "box", "layout": "vertical", "contents": items, "margin": "lg"}
            ],
            "paddingAll": "xl",
            "backgroundColor": COSMIC['bg_main']
        }
    }


def registered_card(name):
    return {
        "type": "bubble",
        "size": "kilo",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "✨", "size": "xxl", "align": "center"},
                {"type": "text", "text": "تم التسجيل بنجاح", "size": "xl", "weight": "bold", "color": COSMIC['text_main'], "align": "center", "margin": "md"},
                {"type": "separator", "margin": "lg", "color": COSMIC['border']},
                {"type": "text", "text": name, "size": "lg", "weight": "bold", "color": COSMIC['success'], "align": "center", "margin": "lg"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "يمكنك الآن:", "size": "sm", "color": COSMIC['text_secondary'], "weight": "bold"},
                        {"type": "text", "text": "⚡ اللعب وجمع النقاط", "size": "xs", "color": COSMIC['text_secondary'], "margin": "sm"},
                        {"type": "text", "text": "🏆 الظهور في لوحة الصدارة", "size": "xs", "color": COSMIC['text_secondary'], "margin": "sm"}
                    ],
                    "backgroundColor": COSMIC['bg_card'],
                    "cornerRadius": "12px",
                    "paddingAll": "md",
                    "margin": "lg",
                    "borderWidth": "1px",
                    "borderColor": COSMIC['border']
                }
            ],
            "paddingAll": "xl",
            "backgroundColor": COSMIC['bg_main']
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": "⚡ ابدأ اللعب", "text": "أغنية"}, "style": "primary", "color": COSMIC['primary'], "height": "sm"}
            ],
            "paddingAll": "lg",
            "backgroundColor": COSMIC['bg_main']
        }
    }


def withdrawal_card(name):
    return {
        "type": "bubble",
        "size": "kilo",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "👋", "size": "xxl", "align": "center"},
                {"type": "text", "text": "تم الانسحاب", "size": "xl", "weight": "bold", "color": COSMIC['text_main'], "align": "center", "margin": "md"},
                {"type": "separator", "margin": "lg", "color": COSMIC['border']},
                {"type": "text", "text": name, "size": "lg", "color": COSMIC['text_secondary'], "align": "center", "margin": "lg"},
                {"type": "text", "text": "نتمنى رؤيتك مرة أخرى", "size": "sm", "color": COSMIC['text_tertiary'], "align": "center", "margin": "md"}
            ],
            "paddingAll": "xl",
            "backgroundColor": COSMIC['bg_main']
        }
    }


"""
خطوة 3️⃣: استبدل دالة get_qr() القديمة بهذه النسخة
"""

def get_qr():
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="▫️ أغنية", text="أغنية")),
        QuickReplyButton(action=MessageAction(label="▫️ لعبة", text="لعبة")),
        QuickReplyButton(action=MessageAction(label="▫️ سلسلة", text="سلسلة")),
        QuickReplyButton(action=MessageAction(label="▫️ أسرع", text="أسرع")),
        QuickReplyButton(action=MessageAction(label="▫️ ضد", text="ضد")),
        QuickReplyButton(action=MessageAction(label="▫️ تكوين", text="تكوين")),
        QuickReplyButton(action=MessageAction(label="▫️ ترتيب", text="ترتيب")),
        QuickReplyButton(action=MessageAction(label="▫️ كلمة", text="كلمة")),
        QuickReplyButton(action=MessageAction(label="▫️ لون", text="لون")),
        QuickReplyButton(action=MessageAction(label="🏆 متصدرين", text="الصدارة")),
        QuickReplyButton(action=MessageAction(label="⚙️ نقاطي", text="نقاطي")),
        QuickReplyButton(action=MessageAction(label="❓ مساعدة", text="مساعدة"))
    ])


"""
═══════════════════════════════════════════════════════════════
✅ التعديلات اكتملت!

📝 ملخص التغييرات:
1. أضفنا لوحة ألوان COSMIC
2. استبدلنا جميع بطاقات Flex بالتصميم الجديد
3. حدّثنا الأزرار السريعة

🎨 للتخصيص:
- عدّل قاموس COSMIC لتغيير الألوان
- استبدل PISCES_LOGO برابط صورتك
- جرّب ألوان مختلفة حسب ذوقك

🚀 للاختبار:
1. احفظ الملف
2. أعد تشغيل البوت
3. جرّب الأوامر: البداية، مساعدة، نقاطي، الصدارة

© Bot Al-Hout 2025 | Cosmic Depth Design System
═══════════════════════════════════════════════════════════════
"""
