# ============================================
# style.py
# ملف الستايل الكامل للبوت
# بدون أي رموز أو ايموجي
# ============================================

# --------------------------------------------
# 1) ألوان البوت (مبنية على ألوان الشعار)
# --------------------------------------------
COLORS = {
    "primary": "#4C00FF",
    "primary_dark": "#3100A8",
    "secondary": "#DCC4FF",
    "background": "#FFFFFF",
    "text": "#1E1E1E",
    "subtext": "#666666",
    "success": "#48C774",
    "danger": "#FF3860",
    "warning": "#FFDD57",
}

# --------------------------------------------
# 2) روابط الصور والشعارات
# --------------------------------------------
ASSETS = {
    "logo": "https://i.imgur.com/qcWILGi.jpeg"
}

# --------------------------------------------
# 3) الأزرار الثابتة — ألعاب رئيسية
# --------------------------------------------
MAIN_GAMES_BUTTONS = [
    {"label": "أسرع", "command": "أسرع"},
    {"label": "لعبة", "command": "لعبة"},
    {"label": "سلسلة", "command": "سلسلة"},
    {"label": "أغنية", "command": "أغنية"},
    {"label": "ضد", "command": "ضد"},
    {"label": "ترتيب", "command": "ترتيب"},
    {"label": "تكوين", "command": "تكوين"},
    {"label": "توافق", "command": "توافق"},
    {"label": "Ai", "command": "Ai"},
]

# --------------------------------------------
# 4) أزرار المحتوى الإضافي
# --------------------------------------------
EXTRA_BUTTONS = [
    {"label": "سؤال", "command": "سؤال"},
    {"label": "منشن", "command": "منشن"},
    {"label": "اعتراف", "command": "اعتراف"},
    {"label": "تحدي", "command": "تحدي"},
]

# ------------------------------------------------
# مولّد أزرار موحد
# ------------------------------------------------
def generate_buttons(buttons_list):
    btns = []
    for b in buttons_list:
        btns.append({
            "type": "button",
            "style": "primary",
            "color": COLORS["primary"],
            "action": {
                "type": "message",
                "label": b["label"],
                "text": b["command"]
            }
        })
    return btns

# ------------------------------------------------
# بطاقة ترحيب
# ------------------------------------------------
def welcome_flex():
    return {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": ASSETS["logo"],
            "size": "full",
            "aspectRatio": "20:9",
            "aspectMode": "cover"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "مرحباً بك",
                    "weight": "bold",
                    "size": "xl",
                    "color": COLORS["primary"]
                },
                {
                    "type": "text",
                    "text": "اختر أحد الألعاب أو المحتوى المتاح",
                    "size": "sm",
                    "color": COLORS["subtext"],
                    "wrap": True
                },
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": generate_buttons(MAIN_GAMES_BUTTONS + EXTRA_BUTTONS)
        }
    }

# ------------------------------------------------
# قوانين البوت
# ------------------------------------------------
def rules_flex(rules_text):
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                {
                    "type": "text",
                    "text": "قوانين البوت",
                    "weight": "bold",
                    "size": "xl",
                    "color": COLORS["primary"]
                },
                {
                    "type": "text",
                    "text": rules_text,
                    "wrap": True,
                    "color": COLORS["text"]
                }
            ]
        }
    }

# ------------------------------------------------
# عرض البروفايل
# ------------------------------------------------
def profile_flex(username, total_games, best_game, last_active):
    return {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": ASSETS["logo"],
            "size": "full",
            "aspectRatio": "20:9",
            "aspectMode": "cover"
        },
        "body": {
            "layout": "vertical",
            "type": "box",
            "contents": [
                {"type": "text", "text": username, "weight": "bold", "size": "lg"},
                {"type": "separator", "margin": "md"},
                {"type": "text", "text": f"عدد الألعاب: {total_games}", "margin": "md"},
                {"type": "text", "text": f"أفضل لعبة: {best_game}"},
                {"type": "text", "text": f"آخر نشاط: {last_active}", "margin": "sm"},
            ]
        }
    }

# ------------------------------------------------
# عرض الترتيب
# ------------------------------------------------
def leaderboard_flex(top_players):
    rows = []

    for i, p in enumerate(top_players):
        rank_color = COLORS["primary"]
        if i == 0:
            rank_color = "#FFD700"
        elif i == 1:
            rank_color = "#C0C0C0"
        elif i == 2:
            rank_color = "#CD7F32"

        rows.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": f"{i+1}", "color": rank_color, "weight": "bold"},
                {"type": "text", "text": p["name"], "margin": "sm", "flex": 3},
                {"type": "text", "text": str(p["score"]), "align": "end", "color": COLORS["primary_dark"]}
            ]
        })

    return {
        "type": "bubble",
        "body": {
            "layout": "vertical",
            "type": "box",
            "contents": [
                {"type": "text", "text": "ترتيب اللاعبين", "weight": "bold", "size": "xl", "color": COLORS["primary"]},
                {"type": "separator", "margin": "md"},
                *rows
            ]
        }
    }

# ------------------------------------------------
# بداية لعبة
# ------------------------------------------------
def start_game_flex(game_name, description):
    return {
        "type": "bubble",
        "size": "mega",
        "hero": {
            "type": "image",
            "url": ASSETS["logo"],
            "size": "full",
            "aspectMode": "cover",
            "aspectRatio": "20:9"
        },
        "body": {
            "layout": "vertical",
            "type": "box",
            "contents": [
                {"type": "text", "text": game_name, "color": COLORS["primary"], "weight": "bold", "size": "xl"},
                {"type": "text", "text": description, "wrap": True, "color": COLORS["subtext"], "margin": "md"},
            ]
        },
        "footer": {
            "layout": "vertical",
            "type": "box",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "color": COLORS["primary"],
                    "action": {"type": "message", "label": "ابدأ", "text": f"ابدأ {game_name}"}
                }
            ]
        }
    }

# ------------------------------------------------
# عرض محتوى الملفات النصية
# ------------------------------------------------
def content_display_flex(title, text):
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": title, "weight": "bold", "size": "xl", "color": COLORS["primary"]},
                {"type": "text", "text": text, "wrap": True, "margin": "md"},
            ]
        }
    }
