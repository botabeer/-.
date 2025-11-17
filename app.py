from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction, FlexSendMessage
)
import os
from datetime import datetime, timedelta
import sqlite3
from collections import defaultdict
import threading
import time
import random
import re
import logging
import sys
import traceback

# ==================== التكوين الأساسي ====================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("cosmic-bot")

# نظام ألوان 3D Experience - Dark Mode
COSMIC = {
    "primary": "#06B6D4",
    "secondary": "#0EA5E9",
    "bg": "#0a0e1a",
    "card": "#111827",
    "elevated": "#1f2937",
    "elevated_high": "#374151",
    "border": "#374151",
    "text": "#F1F5F9",
    "text_dim": "#94A3B8",
    "text_muted": "#64748B",
    "success": "#06B6D4",
    "warning": "#06B6D4",
    "error": "#06B6D4",
    "glow": "#06B6D4"
}

# شعار SVG متحرك (برج الحوت)
PISCES_SVG = """data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='1' y2='1'%3E%3Cstop offset='0' stop-color='%2306B6D4'/%3E%3Cstop offset='1' stop-color='%230EA5E9'/%3E%3C/linearGradient%3E%3CradialGradient id='glow'%3E%3Cstop offset='0' stop-color='%2306B6D4' stop-opacity='0.8'/%3E%3Cstop offset='1' stop-color='%2306B6D4' stop-opacity='0'/%3E%3C/radialGradient%3E%3C/defs%3E%3Ccircle cx='100' cy='100' r='90' fill='url(%23glow)' opacity='0.3'%3E%3Canimate attributeName='r' values='80;95;80' dur='3s' repeatCount='indefinite'/%3E%3C/circle%3E%3Cg stroke='url(%23g)' stroke-width='6' fill='none' stroke-linecap='round'%3E%3Cpath d='M60 100C60 70 40 50 40 50'/%3E%3Cpath d='M60 100C60 130 40 150 40 150'/%3E%3Cline x1='50' y1='100' x2='150' y2='100'/%3E%3Cpath d='M140 100C140 70 160 50 160 50'/%3E%3Cpath d='M140 100C140 130 160 150 160 150'/%3E%3C/g%3E%3Ccircle cx='40' cy='50' r='5' fill='%2306B6D4' filter='url(%23glow)'%3E%3Canimate attributeName='opacity' values='0.6;1;0.6' dur='2s' repeatCount='indefinite'/%3E%3C/circle%3E%3Ccircle cx='40' cy='150' r='5' fill='%2306B6D4'%3E%3Canimate attributeName='opacity' values='0.6;1;0.6' dur='2s' begin='0.5s' repeatCount='indefinite'/%3E%3C/circle%3E%3Ccircle cx='160' cy='50' r='5' fill='%2306B6D4'%3E%3Canimate attributeName='opacity' values='0.6;1;0.6' dur='2s' begin='1s' repeatCount='indefinite'/%3E%3C/circle%3E%3Ccircle cx='160' cy='150' r='5' fill='%2306B6D4'%3E%3Canimate attributeName='opacity' values='0.6;1;0.6' dur='2s' begin='1.5s' repeatCount='indefinite'/%3E%3C/circle%3E%3C/svg%3E"""

# ==================== إعداد Gemini AI ====================

USE_AI = False
ask_gemini = None

try:
    import google.generativeai as genai
    keys = [os.getenv(f'GEMINI_API_KEY_{i}', '') for i in range(1, 4)]
    keys = [k for k in keys if k]
    
    if keys:
        genai.configure(api_key=keys[0])
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        USE_AI = True
        logger.info(f"✅ Gemini AI: {len(keys)} مفاتيح")
        
        def ask_gemini(prompt, max_retries=2):
            for i in range(max_retries):
                try:
                    return model.generate_content(prompt).text.strip()
                except Exception as e:
                    logger.error(f"Gemini خطأ: {e}")
            return None
except Exception as e:
    logger.warning(f"⚠️ Gemini AI غير متوفر: {e}")

# ==================== استيراد الألعاب ====================

games = {}
game_names = ['SongGame', 'HumanAnimalPlantGame', 'ChainWordsGame', 
              'FastTypingGame', 'OppositeGame', 'LettersWordsGame',
              'DifferencesGame', 'CompatibilityGame']

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'games'))

for name in game_names:
    try:
        module = __import__(name.lower().replace('game', '_game'), fromlist=[name])
        games[name] = getattr(module, name)
        logger.info(f"✅ {name}")
    except Exception as e:
        games[name] = None
        logger.warning(f"⚠️ {name}: {e}")

# ==================== Flask & LINE Setup ====================

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET', 'SECRET'))

# البيانات المشتركة
active_games = {}
registered_players = set()
user_message_count = defaultdict(lambda: {'count': 0, 'reset_time': datetime.now()})
user_names_cache = {}
error_log = []

# الأقفال
games_lock = threading.Lock()
players_lock = threading.Lock()
names_cache_lock = threading.Lock()
error_log_lock = threading.Lock()

DB_NAME = 'game_scores.db'

# ==================== Database Functions ====================

def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = get_db()
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY, display_name TEXT,
            total_points INTEGER DEFAULT 0, games_played INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0, last_played TEXT,
            registered_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS game_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT,
            game_type TEXT, points INTEGER, won INTEGER,
            played_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_points ON users(total_points DESC)')
        conn.commit()
        conn.close()
        logger.info("✅ قاعدة البيانات جاهزة")
    except Exception as e:
        logger.error(f"❌ خطأ DB: {e}")

init_db()

def update_user_points(user_id, name, points, won=False, game_type=""):
    try:
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
        
        if user:
            conn.execute('''UPDATE users SET total_points = ?, games_played = ?, 
                wins = ?, last_played = ?, display_name = ? WHERE user_id = ?''',
                (user['total_points'] + points, user['games_played'] + 1,
                 user['wins'] + (1 if won else 0), datetime.now().isoformat(), name, user_id))
        else:
            conn.execute('''INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (user_id, name, points, 1, 1 if won else 0, datetime.now().isoformat(), 
                 datetime.now().isoformat()))
        
        if game_type:
            conn.execute('INSERT INTO game_history (user_id, game_type, points, won) VALUES (?, ?, ?, ?)',
                (user_id, game_type, points, 1 if won else 0))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ خطأ النقاط: {e}")
        return False

def get_user_stats(user_id):
    try:
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
        conn.close()
        return user
    except:
        return None

def get_leaderboard(limit=10):
    try:
        conn = get_db()
        leaders = conn.execute('''SELECT display_name, total_points, games_played, wins 
            FROM users ORDER BY total_points DESC LIMIT ?''', (limit,)).fetchall()
        conn.close()
        return leaders
    except:
        return []

# ==================== Helper Functions ====================

def normalize_text(text):
    if not text:
        return ""
    text = text.strip().lower()
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    text = text.replace('ؤ', 'و').replace('ئ', 'ي').replace('ء', '')
    text = text.replace('ة', 'ه').replace('ى', 'ي')
    text = re.sub(r'[\u064B-\u065F]', '', text)
    text = re.sub(r'\s+', '', text)
    return text

def check_rate_limit(user_id, max_msg=30, window=60):
    now = datetime.now()
    data = user_message_count[user_id]
    
    if now - data['reset_time'] > timedelta(seconds=window):
        data['count'] = 0
        data['reset_time'] = now
    
    if data['count'] >= max_msg:
        return False
    
    data['count'] += 1
    return True

def load_text_file(filename):
    try:
        path = os.path.join('games', filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"❌ ملف {filename}: {e}")
    return []

QUESTIONS = load_text_file('questions.txt')
CHALLENGES = load_text_file('challenges.txt')
CONFESSIONS = load_text_file('confessions.txt')
MENTION_QUESTIONS = load_text_file('more_questions.txt')

def log_error(err_type, message, details=None):
    try:
        with error_log_lock:
            error_log.append({
                'timestamp': datetime.now().isoformat(),
                'type': err_type,
                'message': str(message),
                'details': details or {},
                'traceback': traceback.format_exc()
            })
            if len(error_log) > 50:
                error_log.pop(0)
    except:
        pass

def ensure_user_exists(user_id):
    try:
        conn = get_db()
        if not conn.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,)).fetchone():
            name = f"لاعب_{user_id[-4:]}"
            conn.execute('INSERT INTO users (user_id, display_name) VALUES (?, ?)', (user_id, name))
            conn.commit()
            logger.info(f"🆕 مستخدم جديد: {name}")
        conn.close()
        return True
    except:
        return False

def get_user_profile_safe(user_id):
    with names_cache_lock:
        if user_id in user_names_cache:
            return user_names_cache[user_id]
    
    try:
        profile = line_bot_api.get_profile(user_id)
        name = profile.display_name.strip() if profile.display_name else None
        
        if name:
            with names_cache_lock:
                user_names_cache[user_id] = name
            
            try:
                conn = get_db()
                conn.execute('INSERT OR REPLACE INTO users (user_id, display_name) VALUES (?, ?)',
                    (user_id, name))
                conn.commit()
                conn.close()
            except:
                pass
            
            return name
    
    except LineBotApiError as e:
        if e.status_code == 404:
            logger.warning(f"⚠️ ملف غير موجود: {user_id[-4:]}")
    except Exception as e:
        logger.error(f"❌ خطأ profile: {e}")
    
    name = f"لاعب_{user_id[-4:]}"
    with names_cache_lock:
        user_names_cache[user_id] = name
    return name

# ==================== Flex Card Functions ====================

def get_quick_reply():
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="سؤال", text="سؤال")),
        QuickReplyButton(action=MessageAction(label="تحدي", text="تحدي")),
        QuickReplyButton(action=MessageAction(label="اعتراف", text="اعتراف")),
        QuickReplyButton(action=MessageAction(label="منشن", text="منشن")),
        QuickReplyButton(action=MessageAction(label="أغنية", text="أغنية")),
        QuickReplyButton(action=MessageAction(label="لعبة", text="لعبة")),
        QuickReplyButton(action=MessageAction(label="سلسلة", text="سلسلة")),
        QuickReplyButton(action=MessageAction(label="أسرع", text="أسرع")),
        QuickReplyButton(action=MessageAction(label="ضد", text="ضد")),
        QuickReplyButton(action=MessageAction(label="تكوين", text="تكوين")),
        QuickReplyButton(action=MessageAction(label="اختلاف", text="اختلاف")),
        QuickReplyButton(action=MessageAction(label="توافق", text="توافق"))
    ])

def create_3d_box(contents, margin="none"):
    """صندوق بتأثير ثلاثي الأبعاد"""
    return {
        "type": "box",
        "layout": "vertical",
        "contents": contents,
        "backgroundColor": COSMIC["elevated"],
        "cornerRadius": "16px",
        "paddingAll": "20px",
        "margin": margin,
        "borderWidth": "1px",
        "borderColor": COSMIC["border"]
    }

def create_glow_text(text, size="xl", color=None):
    """نص مع توهج"""
    return {
        "type": "text",
        "text": text,
        "size": size,
        "weight": "bold",
        "color": color or COSMIC["primary"],
        "align": "center"
    }

def make_3d_button(label, text, style="primary"):
    """زر بتأثير ثلاثي الأبعاد"""
    return {
        "type": "button",
        "action": {
            "type": "message",
            "label": label,
            "text": text
        },
        "style": style,
        "color": COSMIC["primary"] if style == "primary" else COSMIC["elevated_high"],
        "height": "md"
    }

def create_card(body_contents, footer_buttons=None):
    """دالة موحدة لإنشاء البطاقات"""
    card = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": body_contents,
            "backgroundColor": COSMIC["card"],
            "paddingAll": "24px"
        }
    }
    
    if footer_buttons:
        card["footer"] = {
            "type": "box",
            "layout": "horizontal" if len(footer_buttons) > 1 else "vertical",
            "contents": footer_buttons,
            "backgroundColor": COSMIC["card"],
            "paddingAll": "16px",
            "spacing": "sm"
        }
    
    return card

def get_welcome_card(name):
    body = [
        {
            "type": "image",
            "url": PISCES_SVG,
            "size": "full",
            "aspectRatio": "1:1",
            "aspectMode": "cover"
        },
        create_3d_box([
            {
                "type": "text",
                "text": "مرحباً بك في",
                "size": "md",
                "color": COSMIC["text_dim"],
                "align": "center"
            },
            create_glow_text("بوت الحوت", "xxl"),
            {
                "type": "separator",
                "margin": "lg",
                "color": COSMIC["border"]
            },
            {
                "type": "text",
                "text": name,
                "size": "xl",
                "weight": "bold",
                "color": COSMIC["text"],
                "align": "center",
                "margin": "lg"
            }
        ], "xl")
    ]
    
    footer = [
        make_3d_button("انضم", "انضم"),
        make_3d_button("انسحب", "انسحب", "secondary"),
        make_3d_button("العب", "أغنية")
    ]
    
    return create_card(body, footer)

def get_help_carousel():
    """كاروسيل المساعدة مع 4 بطاقات"""
    
    # البطاقة 1: الأوامر الأساسية
    card1 = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                create_glow_text("الأوامر", "xl"),
                {
                    "type": "separator",
                    "margin": "lg",
                    "color": COSMIC["border"]
                },
                create_3d_box([
                    {
                        "type": "text",
                        "text": "انضم • انسحب\nنقاطي • الصدارة\nإيقاف • مساعدة",
                        "size": "sm",
                        "color": COSMIC["text_dim"],
                        "wrap": True,
                        "align": "center"
                    }
                ], "lg")
            ],
            "backgroundColor": COSMIC["card"],
            "paddingAll": "24px"
        }
    }
    
    # البطاقة 2: أوامر النصوص
    card2 = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                create_glow_text("النصوص", "xl"),
                {
                    "type": "separator",
                    "margin": "lg",
                    "color": COSMIC["border"]
                },
                create_3d_box([
                    {
                        "type": "text",
                        "text": "سؤال • تحدي\nاعتراف • منشن",
                        "size": "sm",
                        "color": COSMIC["text_dim"],
                        "wrap": True,
                        "align": "center"
                    }
                ], "lg"),
                {
                    "type": "text",
                    "text": "مثال: اكتب \"سؤال\"",
                    "size": "xs",
                    "color": COSMIC["text_muted"],
                    "align": "center",
                    "margin": "md"
                }
            ],
            "backgroundColor": COSMIC["card"],
            "paddingAll": "24px"
        }
    }
    
    # البطاقة 3: الألعاب
    card3 = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                create_glow_text("الألعاب", "xl"),
                {
                    "type": "separator",
                    "margin": "lg",
                    "color": COSMIC["border"]
                },
                create_3d_box([
                    {
                        "type": "text",
                        "text": "أغنية • لعبة • سلسلة\nأسرع • ضد • تكوين\nاختلاف • توافق",
                        "size": "sm",
                        "color": COSMIC["text_dim"],
                        "wrap": True,
                        "align": "center"
                    }
                ], "lg"),
                {
                    "type": "text",
                    "text": "5 جولات لكل لعبة",
                    "size": "xs",
                    "color": COSMIC["text_muted"],
                    "align": "center",
                    "margin": "md"
                }
            ],
            "backgroundColor": COSMIC["card"],
            "paddingAll": "24px"
        }
    }
    
    # البطاقة 4: أثناء اللعب
    card4 = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                create_glow_text("أثناء اللعب", "xl"),
                {
                    "type": "separator",
                    "margin": "lg",
                    "color": COSMIC["border"]
                },
                create_3d_box([
                    {
                        "type": "text",
                        "text": "لمح - تلميح\nجاوب - الإجابة",
                        "size": "sm",
                        "color": COSMIC["text_dim"],
                        "wrap": True,
                        "align": "center"
                    }
                ], "lg"),
                {
                    "type": "separator",
                    "margin": "lg",
                    "color": COSMIC["border"]
                },
                {
                    "type": "text",
                    "text": "بوت الحوت © 2025",
                    "size": "xs",
                    "color": COSMIC["text_muted"],
                    "align": "center",
                    "margin": "lg"
                }
            ],
            "backgroundColor": COSMIC["card"],
            "paddingAll": "24px"
        }
    }
    
    return {
        "type": "carousel",
        "contents": [card1, card2, card3, card4]
    }

def get_registration_card(name):
    body = [
        create_3d_box([
            {
                "type": "text",
                "text": "✨",
                "size": "xxl",
                "align": "center"
            },
            create_glow_text("تم التسجيل", "xl")
        ]),
        {
            "type": "separator",
            "margin": "xl",
            "color": COSMIC["border"]
        },
        {
            "type": "text",
            "text": name,
            "size": "lg",
            "weight": "bold",
            "color": COSMIC["text"],
            "align": "center",
            "margin": "xl"
        }
    ]
    
    return create_card(body, [make_3d_button("ابدأ اللعب", "أغنية")])

def get_withdrawal_card(name):
    body = [
        {
            "type": "text",
            "text": "تم الانسحاب",
            "size": "xl",
            "weight": "bold",
            "color": COSMIC["text_muted"],
            "align": "center"
        },
        {
            "type": "separator",
            "margin": "xl",
            "color": COSMIC["border"]
        },
        {
            "type": "text",
            "text": name,
            "size": "lg",
            "color": COSMIC["text"],
            "align": "center",
            "margin": "xl"
        }
    ]
    
    return create_card(body)

def get_stats_card(user_id, name):
    stats = get_user_stats(user_id)
    
    if not stats:
        body = [
            create_glow_text("إحصائياتك", "xxl"),
            {
                "type": "separator",
                "margin": "xl",
                "color": COSMIC["border"]
            },
            {
                "type": "text",
                "text": "لم تبدأ بعد",
                "size": "md",
                "color": COSMIC["text_dim"],
                "align": "center",
                "margin": "xl"
            }
        ]
        return create_card(body, [make_3d_button("ابدأ الآن", "انضم")])
    
    win_rate = (stats['wins'] / stats['games_played'] * 100) if stats['games_played'] > 0 else 0
    
    body = [
        create_glow_text("إحصائياتك", "xxl"),
        {
            "type": "text",
            "text": name,
            "size": "sm",
            "color": COSMIC["text_dim"],
            "align": "center",
            "margin": "sm"
        },
        {
            "type": "separator",
            "margin": "xl",
            "color": COSMIC["border"]
        },
        create_3d_box([
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "text",
                        "text": "النقاط",
                        "size": "sm",
                        "color": COSMIC["text_muted"],
                        "flex": 1
                    },
                    create_glow_text(str(stats['total_points']), "xxl", COSMIC["primary"])
                ]
            }
        ], "xl"),
        create_3d_box([
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "text",
                        "text": "الألعاب",
                        "size": "sm",
                        "color": COSMIC["text_muted"],
                        "flex": 1
                    },
                    {
                        "type": "text",
                        "text": str(stats['games_played']),
                        "size": "lg",
                        "weight": "bold",
                        "color": COSMIC["text"],
                        "flex": 1,
                        "align": "end"
                    }
                ]
            }
        ], "md"),
        create_3d_box([
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "text",
                        "text": "الفوز",
                        "size": "sm",
                        "color": COSMIC["text_muted"],
                        "flex": 1
                    },
                    {
                        "type": "text",
                        "text": str(stats['wins']),
                        "size": "lg",
                        "weight": "bold",
                        "color": COSMIC["primary"],
                        "flex": 1,
                        "align": "end"
                    }
                ]
            }
        ], "md"),
        create_3d_box([
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "text",
                        "text": "معدل الفوز",
                        "size": "sm",
                        "color": COSMIC["text_muted"],
                        "flex": 1
                    },
                    {
                        "type": "text",
                        "text": f"{win_rate:.0f}%",
                        "size": "lg",
                        "weight": "bold",
                        "color": COSMIC["secondary"],
                        "flex": 1,
                        "align": "end"
                    }
                ]
            }
        ], "md")
    ]
    
    return create_card(body, [make_3d_button("الصدارة", "الصدارة")])

def get_leaderboard_card():
    leaders = get_leaderboard()
    
    if not leaders:
        body = [
            create_glow_text("لوحة الصدارة", "xxl"),
            {
                "type": "text",
                "text": "لا توجد بيانات",
                "size": "md",
                "color": COSMIC["text_dim"],
                "align": "center",
                "margin": "xl"
            }
        ]
        return create_card(body)
    
    items = []
    for i, leader in enumerate(leaders, 1):
        if i == 1:
            rank, color = "👑", COSMIC["primary"]
        elif i == 2:
            rank, color = "🥈", COSMIC["secondary"]
        elif i == 3:
            rank, color = "🥉", COSMIC["text"]
        else:
            rank, color = f"#{i}", COSMIC["text_muted"]
        
        items.append(create_3d_box([
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "text",
                        "text": rank,
                        "size": "lg",
                        "color": color,
                        "flex": 0,
                        "weight": "bold"
                    },
                    {
                        "type": "text",
                        "text": leader['display_name'],
                        "size": "sm",
                        "color": color,
                        "flex": 3,
                        "margin": "md",
                        "wrap": True,
                        "weight": "bold" if i <= 3 else "regular"
                    },
                    {
                        "type": "text",
                        "text": str(leader['total_points']),
                        "size": "lg" if i <= 3 else "md",
                        "color": color,
                        "flex": 1,
                        "align": "end",
                        "weight": "bold"
                    }
                ]
            }
        ], "sm" if i > 1 else "md"))
    
    body = [
        create_glow_text("لوحة الصدارة", "xxl"),
        {
            "type": "text",
            "text": "أفضل اللاعبين",
            "size": "sm",
            "color": COSMIC["text_dim"],
            "align": "center",
            "margin": "sm"
        },
        {
            "type": "separator",
            "margin": "xl",
            "color": COSMIC["border"]
        },
        {
            "type": "box",
            "layout": "vertical",
            "contents": items,
            "margin": "lg"
        }
    ]
    
    return create_card(body)

def get_game_card(question, round_num, total_rounds, game_type):
    """بطاقة اللعبة مع معلومات الجولة"""
    
    # تحديد الألعاب التي تدعم التلميحات
    hint_games = ['أغنية', 'لعبة', 'ضد', 'تكوين']
    
    body = [
        create_3d_box([
            {
                "type": "text",
                "text": f"الجولة {round_num}/{total_rounds}",
                "size": "sm",
                "color": COSMIC["text_muted"],
                "align": "center"
            },
            create_glow_text(game_type, "xl"),
            {
                "type": "separator",
                "margin": "md",
                "color": COSMIC["border"]
            },
            {
                "type": "text",
                "text": question,
                "size": "lg",
                "color": COSMIC["text"],
                "align": "center",
                "margin": "md",
                "wrap": True,
                "weight": "bold"
            }
        ])
    ]
    
    footer = []
    if game_type in hint_games:
        footer.append(make_3d_button("لمح", "لمح", "secondary"))
    footer.append(make_3d_button("جاوب", "جاوب", "secondary"))
    
    return create_card(body, footer if footer else None)

def get_winner_card(winner_name, winner_score, all_scores):
    score_items = []
    for i, (name, score) in enumerate(all_scores, 1):
        rank_text = f"{'🥇' if i == 1 else '🥈' if i == 2 else '🥉' if i == 3 else '#' + str(i)} المركز"
        color = COSMIC["primary"] if i == 1 else COSMIC["secondary"] if i <= 3 else COSMIC["text_muted"]
        
        score_items.append(create_3d_box([
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": rank_text,
                                "size": "xs",
                                "color": COSMIC["text_muted"]
                            },
                            {
                                "type": "text",
                                "text": name,
                                "size": "sm",
                                "color": color,
                                "weight": "bold",
                                "wrap": True
                            }
                        ],
                        "flex": 3
                    },
                    {
                        "type": "text",
                        "text": str(score),
                        "size": "xl" if i == 1 else "lg",
                        "color": color,
                        "weight": "bold",
                        "align": "end",
                        "flex": 1
                    }
                ]
            }
        ], "sm" if i > 1 else "md"))
    
    body = [
        create_3d_box([
            {
                "type": "text",
                "text": "✨",
                "size": "xxl",
                "align": "center"
            },
            create_glow_text("انتهت اللعبة", "xl")
        ]),
        {
            "type": "separator",
            "margin": "xl",
            "color": COSMIC["border"]
        },
        {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "الفائز",
                    "size": "sm",
                    "color": COSMIC["text_muted"],
                    "align": "center"
                },
                create_glow_text(winner_name, "xxl"),
                {
                    "type": "text",
                    "text": f"{winner_score} نقطة",
                    "size": "lg",
                    "weight": "bold",
                    "color": COSMIC["secondary"],
                    "align": "center",
                    "margin": "md"
                }
            ],
            "margin": "xl"
        },
        {
            "type": "separator",
            "margin": "xl",
            "color": COSMIC["border"]
        },
        {
            "type": "text",
            "text": "النتائج النهائية",
            "size": "lg",
            "weight": "bold",
            "color": COSMIC["text"],
            "margin": "xl",
            "align": "center"
        },
        {
            "type": "box",
            "layout": "vertical",
            "contents": score_items,
            "margin": "md"
        }
    ]
    
    footer = [
        make_3d_button("لعب مرة أخرى", "أغنية"),
        make_3d_button("الصدارة", "الصدارة", "secondary")
    ]
    
    return create_card(body, footer)

# ==================== Game Management ====================

def start_game(game_id, game_class, game_type, user_id, event):
    if not game_class:
        try:
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text=f"لعبة {game_type} غير متوفرة", quick_reply=get_quick_reply()))
        except:
            pass
        return False
    
    try:
        with games_lock:
            if game_class.__name__ in ['SongGame', 'HumanAnimalPlantGame', 'LettersWordsGame']:
                game = game_class(line_bot_api, use_ai=USE_AI, ask_ai=ask_gemini)
            else:
                game = game_class(line_bot_api)
            
            with players_lock:
                participants = registered_players.copy()
                participants.add(user_id)
            
            active_games[game_id] = {
                'game': game,
                'type': game_type,
                'created_at': datetime.now(),
                'participants': participants,
                'answered_users': set(),
                'round': 1,
                'total_rounds': 5
            }
        
        response = game.start_game()
        if isinstance(response, TextSendMessage):
            response.quick_reply = get_quick_reply()
        elif isinstance(response, list):
            for r in response:
                if isinstance(r, TextSendMessage):
                    r.quick_reply = get_quick_reply()
        
        line_bot_api.reply_message(event.reply_token, response)
        logger.info(f"✅ {game_type} بدأت")
        return True
    except Exception as e:
        logger.error(f"❌ خطأ بدء {game_type}: {e}")
        log_error('start_game', e, {'game_type': game_type, 'user_id': user_id[-4:]})
        return False

# ==================== Flask Routes ====================

@app.route("/", methods=['GET'])
def home():
    games_count = sum(1 for g in games.values() if g)
    
    return f"""<!DOCTYPE html>
<html dir="rtl">
<head>
    <title>بوت الحوت - 3D Experience</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, sans-serif;
            background: linear-gradient(135deg, {COSMIC['bg']}, {COSMIC['card']});
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .container {{
            background: {COSMIC['card']};
            border: 2px solid {COSMIC['border']};
            border-radius: 24px;
            box-shadow: 0 0 60px rgba(6,182,212,0.4), 0 20px 40px rgba(0,0,0,0.5);
            padding: 40px;
            max-width: 600px;
            width: 100%;
        }}
        h1 {{
            text-align: center;
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(135deg, {COSMIC['primary']}, {COSMIC['secondary']});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 30px rgba(6,182,212,0.5);
        }}
        .subtitle {{ 
            text-align: center; 
            color: {COSMIC['text_dim']}; 
            margin-bottom: 30px; 
        }}
        .status {{
            background: {COSMIC['elevated']};
            border: 1px solid {COSMIC['border']};
            border-radius: 16px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }}
        .status-item {{
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid {COSMIC['border']};
        }}
        .status-item:last-child {{ border-bottom: none; }}
        .label {{ color: {COSMIC['text_muted']}; }}
        .value {{ 
            color: {COSMIC['primary']}; 
            font-weight: bold;
            text-shadow: 0 0 10px rgba(6,182,212,0.5);
        }}
        .btn {{
            display: inline-block;
            padding: 12px 24px;
            background: {COSMIC['primary']};
            color: {COSMIC['bg']};
            text-decoration: none;
            border-radius: 12px;
            margin: 5px;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(6,182,212,0.4);
            transition: all 0.3s;
        }}
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(6,182,212,0.6);
        }}
        .footer {{ 
            text-align: center; 
            margin-top: 30px; 
            color: {COSMIC['text_muted']}; 
            font-size: 0.9em; 
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>بوت الحوت</h1>
        <p class="subtitle">3D Gaming Experience</p>
        
        <div class="status">
            <div class="status-item">
                <span class="label">الخادم</span>
                <span class="value">✅ يعمل</span>
            </div>
            <div class="status-item">
                <span class="label">Gemini AI</span>
                <span class="value">{'✅ مفعّل' if USE_AI else '⚠️ معطّل'}</span>
            </div>
            <div class="status-item">
                <span class="label">اللاعبون</span>
                <span class="value">{len(registered_players)}</span>
            </div>
            <div class="status-item">
                <span class="label">ألعاب نشطة</span>
                <span class="value">{len(active_games)}</span>
            </div>
            <div class="status-item">
                <span class="label">ألعاب متوفرة</span>
                <span class="value">{games_count}/8</span>
            </div>
            <div class="status-item">
                <span class="label">أخطاء مسجلة</span>
                <span class="value">{len(error_log)}</span>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 25px;">
            <a href="/health" class="btn">الصحة</a>
            <a href="/errors" class="btn">الأخطاء</a>
            <a href="/debug" class="btn">التشخيص</a>
        </div>
        
        <div class="footer">بوت الحوت © 2025</div>
    </div>
</body>
</html>"""

@app.route("/errors", methods=['GET'])
def view_errors():
    with error_log_lock:
        errors = list(reversed(error_log))
    
    html = f"""<!DOCTYPE html>
<html dir="rtl">
<head>
    <title>سجل الأخطاء</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            font-family: -apple-system, sans-serif;
            background: {COSMIC['bg']};
            color: {COSMIC['text']};
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: {COSMIC['card']};
            border-radius: 20px;
            padding: 30px;
            border: 2px solid {COSMIC['border']};
        }}
        h1 {{ color: {COSMIC['primary']}; margin-bottom: 20px; }}
        .error-item {{
            background: {COSMIC['elevated']};
            border-left: 4px solid {COSMIC['primary']};
            padding: 15px;
            margin: 15px 0;
            border-radius: 8px;
        }}
        .no-errors {{
            text-align: center;
            padding: 40px;
            color: {COSMIC['primary']};
        }}
        .btn {{
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            background: {COSMIC['primary']};
            color: {COSMIC['bg']};
            text-decoration: none;
            border-radius: 8px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>سجل الأخطاء</h1>
"""
    
    if not errors:
        html += '<div class="no-errors">✅ لا توجد أخطاء مسجلة</div>'
    else:
        for err in errors:
            html += f'<div class="error-item">{err.get("type", "Unknown")}: {err.get("message", "No message")}</div>'
    
    html += '<a href="/" class="btn">العودة</a></div></body></html>'
    return html

@app.route("/debug", methods=['GET'])
def debug_info():
    games_status = {name: "✅" if cls else "❌" for name, cls in games.items()}
    
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "system": {
            "active_games": len(active_games),
            "registered_players": len(registered_players),
            "cached_names": len(user_names_cache),
            "error_count": len(error_log)
        },
        "ai": {
            "enabled": USE_AI
        },
        "games": games_status
    }, 200

@app.route("/health", methods=['GET'])
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_games": len(active_games),
        "registered_players": len(registered_players),
        "ai_enabled": USE_AI
    }, 200

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    if not signature:
        abort(400)
    
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("❌ توقيع غير صالح")
        abort(400)
    except Exception as e:
        logger.error(f"❌ خطأ callback: {e}")
        log_error('callback', e)
    
    return 'OK', 200

# ==================== Message Handler ====================

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = None
    text = None
    
    try:
        user_id = event.source.user_id
        text = event.message.text.strip() if event.message.text else ""
        
        if not user_id or not text:
            return
        
        with players_lock:
            if user_id not in registered_players:
                registered_players.add(user_id)
                ensure_user_exists(user_id)
        
        if not check_rate_limit(user_id):
            return
        
        display_name = get_user_profile_safe(user_id)
        game_id = getattr(event.source, 'group_id', user_id)
        
        logger.info(f"📨 {display_name}: {text[:50]}")
        
        # ==================== الأوامر ====================
        
        if text in ['البداية', 'ابدأ', 'start', 'البوت']:
            line_bot_api.reply_message(event.reply_token,
                FlexSendMessage(alt_text=f"مرحباً {display_name}",
                    contents=get_welcome_card(display_name), quick_reply=get_quick_reply()))
            return
        
        if text in ['مساعدة', 'help']:
            line_bot_api.reply_message(event.reply_token,
                FlexSendMessage(alt_text="المساعدة", 
                    contents=get_help_carousel(), quick_reply=get_quick_reply()))
            return
        
        if text in ['نقاطي', 'إحصائياتي', 'احصائياتي']:
            line_bot_api.reply_message(event.reply_token,
                FlexSendMessage(alt_text="إحصائياتك", 
                    contents=get_stats_card(user_id, display_name), quick_reply=get_quick_reply()))
            return
        
        if text in ['الصدارة', 'المتصدرين']:
            line_bot_api.reply_message(event.reply_token,
                FlexSendMessage(alt_text="الصدارة", 
                    contents=get_leaderboard_card(), quick_reply=get_quick_reply()))
            return
        
        if text in ['إيقاف', 'stop', 'ايقاف']:
            with games_lock:
                if game_id in active_games:
                    game_type = active_games[game_id]['type']
                    del active_games[game_id]
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text=f"تم إيقاف {game_type}", quick_reply=get_quick_reply()))
                else:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="لا توجد لعبة", quick_reply=get_quick_reply()))
            return
        
        if text in ['انضم', 'تسجيل', 'join']:
            with players_lock:
                if user_id in registered_players:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text=f"أنت مسجل يا {display_name}", quick_reply=get_quick_reply()))
                else:
                    registered_players.add(user_id)
                    line_bot_api.reply_message(event.reply_token,
                        FlexSendMessage(alt_text="تم التسجيل", 
                            contents=get_registration_card(display_name), quick_reply=get_quick_reply()))
            return
        
        if text in ['انسحب', 'خروج']:
            with players_lock:
                if user_id in registered_players:
                    registered_players.remove(user_id)
                    line_bot_api.reply_message(event.reply_token,
                        FlexSendMessage(alt_text="انسحاب", 
                            contents=get_withdrawal_card(display_name), quick_reply=get_quick_reply()))
                else:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="غير مسجل", quick_reply=get_quick_reply()))
            return
        
        # أوامر نصية
        if text in ['سؤال', 'سوال'] and QUESTIONS:
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text=random.choice(QUESTIONS), quick_reply=get_quick_reply()))
            return
        
        if text in ['تحدي', 'challenge'] and CHALLENGES:
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text=random.choice(CHALLENGES), quick_reply=get_quick_reply()))
            return
        
        if text in ['اعتراف', 'confession'] and CONFESSIONS:
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text=random.choice(CONFESSIONS), quick_reply=get_quick_reply()))
            return
        
        if text in ['منشن', 'mention'] and MENTION_QUESTIONS:
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text=random.choice(MENTION_QUESTIONS), quick_reply=get_quick_reply()))
            return
        
        # الألعاب
        games_map = {
            'أغنية': (games['SongGame'], 'أغنية'),
            'لعبة': (games['HumanAnimalPlantGame'], 'لعبة'),
            'سلسلة': (games['ChainWordsGame'], 'سلسلة'),
            'أسرع': (games['FastTypingGame'], 'أسرع'),
            'ضد': (games['OppositeGame'], 'ضد'),
            'تكوين': (games['LettersWordsGame'], 'تكوين'),
            'اختلاف': (games['DifferencesGame'], 'اختلاف'),
            'توافق': (games['CompatibilityGame'], 'توافق')
        }
        
        if text in games_map:
            game_class, game_type = games_map[text]
            
            if text == 'توافق' and game_class:
                with games_lock:
                    with players_lock:
                        participants = registered_players.copy()
                        participants.add(user_id)
                    
                    active_games[game_id] = {
                        'game': game_class(line_bot_api),
                        'type': 'توافق',
                        'created_at': datetime.now(),
                        'participants': participants,
                        'answered_users': set(),
                        'last_game': text,
                        'waiting_for_names': True
                    }
                
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text="لعبة التوافق\n\nاكتب اسمين مفصولين بمسافة\nمثال: ميش عبير",
                        quick_reply=get_quick_reply()))
                return
            
            if game_id in active_games:
                active_games[game_id]['last_game'] = text
            
            start_game(game_id, game_class, game_type, user_id, event)
            return
        
        # معالجة لعبة التوافق
        if game_id in active_games:
            game_data = active_games[game_id]
            
            if game_data.get('type') == 'توافق' and game_data.get('waiting_for_names'):
                cleaned = text.replace('@', '').strip()
                
                if '@' in text:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="بدون @", quick_reply=get_quick_reply()))
                    return
                
                response = result.get('response', TextSendMessage(text=result.get('message', '')))
                if isinstance(response, TextSendMessage):
                    response.quick_reply = get_quick_reply()
                elif isinstance(response, list):
                    for r in response:
                        if isinstance(r, TextSendMessage):
                            r.quick_reply = get_quick_reply()
                
                line_bot_api.reply_message(event.reply_token, response)
                
            except Exception as e:
                logger.error(f"❌ خطأ إجابة: {e}")
                log_error('game_answer', e, {'user_id': user_id[-4:], 'game_type': game_type})
    
    except Exception as e:
        logger.error(f"❌ خطأ عام: {e}")
        log_error('handle_message', e, {
            'user_id': user_id[-4:] if user_id else 'Unknown',
            'text': text[:100] if text else 'Unknown'
        })
        
        try:
            if hasattr(event, 'reply_token') and event.reply_token:
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text="حدث خطأ مؤقت. حاول مرة أخرى.", quick_reply=get_quick_reply()))
        except:
            pass

# ==================== Cleanup Thread ====================

def cleanup_old_games():
    """تنظيف الألعاب القديمة والبيانات"""
    while True:
        try:
            time.sleep(300)  # كل 5 دقائق
            now = datetime.now()
            
            to_delete = []
            with games_lock:
                for gid, data in active_games.items():
                    if now - data.get('created_at', now) > timedelta(minutes=15):
                        to_delete.append(gid)
                
                for gid in to_delete:
                    del active_games[gid]
                
                if to_delete:
                    logger.info(f"🗑️ حذف {len(to_delete)} لعبة قديمة")
            
            with names_cache_lock:
                if len(user_names_cache) > 1000:
                    user_names_cache.clear()
                    logger.info("🧹 تنظيف الأسماء")
            
            with error_log_lock:
                if len(error_log) > 100:
                    error_log[:] = error_log[-50:]
                    logger.info("🧹 تنظيف سجل الأخطاء")
        
        except Exception as e:
            logger.error(f"❌ خطأ تنظيف: {e}")
            log_error('cleanup', e)

cleanup_thread = threading.Thread(target=cleanup_old_games, daemon=True)
cleanup_thread.start()

# ==================== Error Handlers ====================

@app.errorhandler(InvalidSignatureError)
def handle_invalid_signature(error):
    logger.error(f"❌ توقيع غير صالح: {error}")
    log_error('invalid_signature', error)
    return 'Invalid Signature', 400

@app.errorhandler(400)
def bad_request(error):
    logger.warning(f"⚠️ طلب غير صالح: {error}")
    return 'Bad Request', 400

@app.errorhandler(404)
def not_found(error):
    return 'Not Found', 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"❌ خطأ داخلي: {error}")
    log_error('internal_error', error)
    return 'Internal Server Error', 500

@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f"❌ خطأ غير متوقع: {error}")
    log_error('unexpected_error', error)
    
    if request.path == '/callback':
        return 'OK', 200
    
    return 'Internal Server Error', 500

# ==================== Syntax Checker ====================

def check_syntax():
    """فحص أخطاء الـ syntax"""
    try:
        import ast
        with open(__file__, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        logger.info("✅ لا توجد أخطاء syntax")
        return True
    except SyntaxError as e:
        logger.error(f"❌ خطأ syntax في السطر {e.lineno}: {e.msg}")
        logger.error(f"   النص: {e.text}")
        return False
    except Exception as e:
        logger.error(f"❌ خطأ في فحص الكود: {e}")
        return False

# ==================== Main ====================

if __name__ == "__main__":
    logger.info("🔍 فحص الكود...")
    if not check_syntax():
        logger.error("❌ فشل فحص الكود - توقف التشغيل")
        sys.exit(1)
    
    port = int(os.environ.get('PORT', 5000))
    
    logger.info("=" * 60)
    logger.info("🌌 بوت الحوت - 3D Experience")
    logger.info("=" * 60)
    logger.info(f"🔌 المنفذ: {port}")
    logger.info(f"🤖 AI: {'✅' if USE_AI else '⚠️'}")
    logger.info(f"📊 اللاعبون: {len(registered_players)}")
    logger.info(f"🎮 الألعاب النشطة: {len(active_games)}")
    
    loaded = [name for name, cls in games.items() if cls]
    logger.info(f"🎯 الألعاب المتوفرة ({len(loaded)}/8):")
    for name in loaded:
        logger.info(f"   ✓ {name}")
    
    if len(loaded) < len(games):
        missing = [name for name, cls in games.items() if not cls]
        logger.warning(f"⚠️ ألعاب غير متوفرة ({len(missing)}):")
        for name in missing:
            logger.warning(f"   ✗ {name}")
    
    logger.info(f"🎨 التصميم: 3D Dark Mode")
    logger.info(f"🔧 مصحح الأخطاء: مفعّل")
    logger.info("=" * 60)
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    except Exception as e:
        logger.error(f"❌ فشل تشغيل التطبيق: {e}")
        log_error('app_start', e)
        sys.exit(1)
                names = cleaned.split()
                if len(names) < 2:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="اسمين مفصولين", quick_reply=get_quick_reply()))
                    return
                
                try:
                    result = game_data['game'].check_answer(f"{names[0]} {names[1]}", user_id, display_name)
                    game_data['waiting_for_names'] = False
                    
                    with games_lock:
                        if game_id in active_games:
                            del active_games[game_id]
                    
                    if result and result.get('response'):
                        response = result['response']
                        if isinstance(response, TextSendMessage):
                            response.quick_reply = get_quick_reply()
                        line_bot_api.reply_message(event.reply_token, response)
                    return
                except Exception as e:
                    logger.error(f"❌ خطأ توافق: {e}")
                    log_error('compatibility_game', e, {'user_id': user_id[-4:]})
                    return
        
        # معالجة إجابات الألعاب
        if game_id in active_games:
            game_data = active_games[game_id]
            
            with players_lock:
                if user_id not in registered_players:
                    return
            
            if user_id in game_data.get('answered_users', set()):
                return
            
            game = game_data['game']
            game_type = game_data['type']
            
            try:
                result = game.check_answer(text, user_id, display_name)
                
                if not result:
                    return
                
                if result.get('correct'):
                    game_data.setdefault('answered_users', set()).add(user_id)
                
                points = result.get('points', 0)
                if points > 0:
                    update_user_points(user_id, display_name, points, result.get('won', False), game_type)
                
                if result.get('next_question'):
                    game_data['answered_users'] = set()
                    game_data['round'] = game_data.get('round', 1) + 1
                    next_q = game.next_question()
                    if next_q:
                        if isinstance(next_q, TextSendMessage):
                            next_q.quick_reply = get_quick_reply()
                        line_bot_api.reply_message(event.reply_token, next_q)
                    return
                
                if result.get('game_over'):
                    with games_lock:
                        last_game = active_games.get(game_id, {}).get('last_game', 'أغنية')
                        if game_id in active_games:
                            del active_games[game_id]
                    
                    if result.get('winner_card'):
                        card = result['winner_card']
                        if 'footer' in card:
                            for btn in card['footer'].get('contents', []):
                                if 'لعب' in btn.get('action', {}).get('label', ''):
                                    btn['action']['text'] = last_game
                        
                        line_bot_api.reply_message(event.reply_token,
                            FlexSendMessage(alt_text="الفائز", contents=card, quick_reply=get_quick_reply()))
                    else:
                        response = result.get('response', TextSendMessage(text=result.get('message', '')))
                        if isinstance(response, TextSendMessage):
                            response.quick_reply = get_quick_reply()
                        line_bot_api.reply_message(event.reply_token, response)
                    return
