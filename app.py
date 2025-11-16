"""
═══════════════════════════════════════════════════════════════
بوت الحوت - نظام ألعاب تفاعلية للمجموعات
النسخة: 3.0.0
بوت الحوت - جميع الحقوق محفوظة
═══════════════════════════════════════════════════════════════
"""

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage, QuickReply, QuickReplyButton, MessageAction
import os
import sqlite3
import logging
import sys
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import time

# إعداد اللوقر
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("whale-bot")

print("\n" + "═"*60)
print("بوت الحوت")
print("═"*60)
print("النسخة: 3.0.0")
print("بوت الحوت - جميع الحقوق محفوظة")
print("═"*60 + "\n")

# ═══════════════════════════════════════════════════════════════
# الإعدادات
# ═══════════════════════════════════════════════════════════════
LINE_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
LINE_SECRET = os.getenv('LINE_CHANNEL_SECRET', '')
GEMINI_KEYS = [k for k in [os.getenv('GEMINI_API_KEY_1', ''), os.getenv('GEMINI_API_KEY_2', ''), os.getenv('GEMINI_API_KEY_3', '')] if k]

app = Flask(__name__)
line_bot_api = LineBotApi(LINE_TOKEN) if LINE_TOKEN else None
handler = WebhookHandler(LINE_SECRET) if LINE_SECRET else None

# بيانات مشتركة
active_games = {}
registered_players = set()
user_message_count = defaultdict(lambda: {'count': 0, 'reset_time': datetime.now()})

# Gemini AI
USE_AI = False
current_key_index = 0

try:
    import google.generativeai as genai
    if GEMINI_KEYS:
        genai.configure(api_key=GEMINI_KEYS[0])
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        USE_AI = True
        logger.info(f"Gemini AI جاهز ({len(GEMINI_KEYS)} مفاتيح)")
except:
    logger.warning("Gemini غير متوفر")

def ask_gemini(prompt):
    global current_key_index
    if not USE_AI or not GEMINI_KEYS:
        return None
    for _ in range(len(GEMINI_KEYS)):
        try:
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()[:1000]
        except Exception as e:
            logger.error(f"خطأ Gemini: {e}")
            current_key_index = (current_key_index + 1) % len(GEMINI_KEYS)
            genai.configure(api_key=GEMINI_KEYS[current_key_index])
    return None

# ═══════════════════════════════════════════════════════════════
# قاعدة البيانات
# ═══════════════════════════════════════════════════════════════
DB_NAME = 'whale_bot.db'

def init_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                user_id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                total_points INTEGER DEFAULT 0,
                games_played INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                last_active TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_points ON players(total_points DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_active ON players(last_active DESC)')
        conn.commit()
        conn.close()
        logger.info("قاعدة البيانات جاهزة")
        return True
    except Exception as e:
        logger.error(f"خطأ DB: {e}")
        return False

init_db()

# ═══════════════════════════════════════════════════════════════
# دوال مساعدة
# ═══════════════════════════════════════════════════════════════
def safe_text(text, max_len=500):
    if text is None:
        return ""
    return str(text).strip()[:max_len].replace('"', '').replace("'", '')

def normalize_text(text):
    if not text:
        return ""
    text = text.strip().lower()
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    text = text.replace('ؤ', 'و').replace('ئ', 'ي').replace('ء', '')
    text = text.replace('ة', 'ه').replace('ى', 'ي')
    import re
    text = re.sub(r'[\u064B-\u065F]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text

def get_profile_safe(user_id):
    if not line_bot_api:
        return f"مستخدم{user_id[-4:]}"
    try:
        profile = line_bot_api.get_profile(user_id)
        return safe_text(profile.display_name, 50) if profile.display_name else f"مستخدم{user_id[-4:]}"
    except LineBotApiError as e:
        if e.status_code != 404:
            logger.error(f"خطأ LINE: {e}")
    except:
        pass
    return f"مستخدم{user_id[-4:]}"

def check_rate(user_id):
    now = datetime.now()
    data = user_message_count[user_id]
    if now - data['reset_time'] > timedelta(seconds=60):
        data['count'] = 0
        data['reset_time'] = now
    if data['count'] >= 10:
        return False
    data['count'] += 1
    return True

# ═══════════════════════════════════════════════════════════════
# إدارة المستخدمين
# ═══════════════════════════════════════════════════════════════
def update_user(user_id, name):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        safe_name = safe_text(name, 100)
        cursor.execute('INSERT OR REPLACE INTO players (user_id, display_name, last_active) VALUES (?, ?, ?)', (user_id, safe_name, now))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"خطأ تحديث: {e}")

def update_points(user_id, name, points, won=False):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        safe_name = safe_text(name, 100)
        cursor.execute('SELECT total_points, games_played, wins FROM players WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        if result:
            new_points = max(0, result[0] + points)
            new_games = result[1] + 1
            new_wins = result[2] + (1 if won else 0)
            cursor.execute('UPDATE players SET total_points = ?, games_played = ?, wins = ?, last_active = ?, display_name = ? WHERE user_id = ?',
                         (new_points, new_games, new_wins, now, safe_name, user_id))
        else:
            cursor.execute('INSERT INTO players (user_id, display_name, total_points, games_played, wins, last_active) VALUES (?, ?, ?, 1, ?, ?)',
                         (user_id, safe_name, max(0, points), 1 if won else 0, now))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"خطأ نقاط: {e}")

def get_stats(user_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM players WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None
    except:
        return None

def get_leaderboard(limit=10):
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT display_name, total_points, games_played, wins FROM players WHERE total_points > 0 ORDER BY total_points DESC, wins DESC LIMIT ?', (limit,))
        results = cursor.fetchall()
        conn.close()
        return [dict(row) for row in results]
    except:
        return []

def cleanup_inactive():
    try:
        cutoff = (datetime.now() - timedelta(days=45)).isoformat()
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM players WHERE last_active < ?', (cutoff,))
        count = cursor.rowcount
        conn.commit()
        conn.close()
        if count > 0:
            logger.info(f"حذف {count} مستخدم غير نشط")
    except Exception as e:
        logger.error(f"خطأ تنظيف: {e}")

def auto_cleanup():
    while True:
        try:
            time.sleep(21600)
            cleanup_inactive()
        except:
            pass

threading.Thread(target=auto_cleanup, daemon=True).start()

# ═══════════════════════════════════════════════════════════════
# Quick Reply
# ═══════════════════════════════════════════════════════════════
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
        QuickReplyButton(action=MessageAction(label="▫️ سؤال", text="سؤال")),
        QuickReplyButton(action=MessageAction(label="▫️ تحدي", text="تحدي")),
        QuickReplyButton(action=MessageAction(label="▫️ اعتراف", text="اعتراف")),
        QuickReplyButton(action=MessageAction(label="▫️ منشن", text="منشن"))
    ])

# ═══════════════════════════════════════════════════════════════
# المحتوى
# ═══════════════════════════════════════════════════════════════
def load_txt(name):
    try:
        with open(f'{name}.txt', 'r', encoding='utf-8') as f:
            return [l.strip() for l in f if l.strip()]
    except:
        return []

QUESTIONS = load_txt('questions')
CHALLENGES = load_txt('challenges')
CONFESSIONS = load_txt('confessions')
MENTIONS = load_txt('mentions')

q_idx = c_idx = cf_idx = m_idx = 0

def next_q():
    global q_idx
    if not QUESTIONS:
        return "ما رأيك بالحياة؟"
    r = QUESTIONS[q_idx % len(QUESTIONS)]
    q_idx += 1
    return r

def next_c():
    global c_idx
    if not CHALLENGES:
        return "غير اسمك"
    r = CHALLENGES[c_idx % len(CHALLENGES)]
    c_idx += 1
    return r

def next_cf():
    global cf_idx
    if not CONFESSIONS:
        return "أكثر شيء تندم عليه؟"
    r = CONFESSIONS[cf_idx % len(CONFESSIONS)]
    cf_idx += 1
    return r

def next_m():
    global m_idx
    if not MENTIONS:
        return "منشن شخص تحبه"
    r = MENTIONS[m_idx % len(MENTIONS)]
    m_idx += 1
    return r

# ═══════════════════════════════════════════════════════════════
# Flex Cards (iOS Style)
# ═══════════════════════════════════════════════════════════════
C = {
    'bg': '#F8F9FA',
    'card': '#FFFFFF',
    'text': '#212529',
    'text2': '#6C757D',
    'sep': '#DEE2E6',
    'btn': '#007AFF'
}

def welcome_card():
    return {
        "type": "bubble",
        "size": "kilo",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "بوت الحوت", "size": "xxl", "weight": "bold", "color": C['text'], "align": "center"},
                {"type": "separator", "margin": "lg", "color": C['sep']},
                {"type": "text", "text": "نظام ألعاب تفاعلية للمجموعات", "size": "sm", "color": C['text2'], "align": "center", "margin": "lg", "wrap": True},
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "الألعاب المتوفرة", "size": "md", "weight": "bold", "color": C['text']},
                        {"type": "text", "text": "▫️ أغنية: خمن المغني", "size": "xs", "color": C['text2'], "wrap": True, "margin": "md"},
                        {"type": "text", "text": "▫️ لعبة: إنسان حيوان نبات جماد بلد", "size": "xs", "color": C['text2'], "wrap": True, "margin": "sm"},
                        {"type": "text", "text": "▫️ سلسلة: كلمة بآخر حرف", "size": "xs", "color": C['text2'], "wrap": True, "margin": "sm"},
                        {"type": "text", "text": "▫️ أسرع: أسرع إجابة", "size": "xs", "color": C['text2'], "wrap": True, "margin": "sm"},
                        {"type": "text", "text": "▫️ ضد: عكس الكلمة", "size": "xs", "color": C['text2'], "wrap": True, "margin": "sm"},
                        {"type": "text", "text": "▫️ تكوين: كون 3 كلمات", "size": "xs", "color": C['text2'], "wrap": True, "margin": "sm"},
                        {"type": "text", "text": "▫️ ترتيب: رتب الحروف", "size": "xs", "color": C['text2'], "wrap": True, "margin": "sm"},
                        {"type": "text", "text": "▫️ كلمة: أطول كلمة", "size": "xs", "color": C['text2'], "wrap": True, "margin": "sm"},
                        {"type": "text", "text": "▫️ لون: خمن اللون", "size": "xs", "color": C['text2'], "wrap": True, "margin": "sm"}
                    ],
                    "backgroundColor": C['bg'],
                    "cornerRadius": "12px",
                    "paddingAll": "16px",
                    "margin": "lg"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "للتسلية (بدون نقاط)", "size": "md", "weight": "bold", "color": C['text']},
                        {"type": "text", "text": "▫️ سؤال ▫️ تحدي ▫️ اعتراف ▫️ منشن ▫️ اختلاف ▫️ توافق", "size": "xs", "color": C['text2'], "wrap": True, "margin": "md"}
                    ],
                    "backgroundColor": C['bg'],
                    "cornerRadius": "12px",
                    "paddingAll": "16px",
                    "margin": "md"
                },
                {"type": "text", "text": "بوت الحوت", "size": "xxs", "color": C['text2'], "align": "center", "margin": "lg"}
            ],
            "paddingAll": "24px"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": "المساعدة", "text": "مساعدة"}, "style": "primary", "color": C['btn']},
                {"type": "button", "action": {"type": "message", "label": "نقاطي", "text": "نقاطي"}, "style": "secondary", "margin": "sm"},
                {"type": "button", "action": {"type": "message", "label": "الصدارة", "text": "الصدارة"}, "style": "secondary", "margin": "sm"}
            ],
            "paddingAll": "16px"
        }
    }

def help_card():
    return {
        "type": "bubble",
        "size": "kilo",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "المساعدة", "size": "xl", "weight": "bold", "color": C['text'], "align": "center"},
                {"type": "separator", "margin": "lg", "color": C['sep']},
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "أوامر التسجيل", "size": "md", "weight": "bold", "color": C['text']},
                        {"type": "text", "text": "▫️ انضم: للتسجيل", "size": "xs", "color": C['text2'], "wrap": True, "margin": "md"},
                        {"type": "text", "text": "▫️ انسحب: للخروج", "size": "xs", "color": C['text2'], "wrap": True, "margin": "sm"}
                    ],
                    "backgroundColor": C['bg'],
                    "cornerRadius": "12px",
                    "paddingAll": "16px",
                    "margin": "lg"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "أوامر اللعب", "size": "md", "weight": "bold", "color": C['text']},
                        {"type": "text", "text": "▫️ لمح: تلميح (-1 نقطة)", "size": "xs", "color": C['text2'], "wrap": True, "margin": "md"},
                        {"type": "text", "text": "▫️ جاوب: عرض الحل", "size": "xs", "color": C['text2'], "wrap": True, "margin": "sm"},
                        {"type": "text", "text": "▫️ إيقاف: إنهاء اللعبة", "size": "xs", "color": C['text2'], "wrap": True, "margin": "sm"}
                    ],
                    "backgroundColor": C['bg'],
                    "cornerRadius": "12px",
                    "paddingAll": "16px",
                    "margin": "md"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "أوامر الإحصائيات", "size": "md", "weight": "bold", "color": C['text']},
                        {"type": "text", "text": "▫️ نقاطي: إحصائياتك", "size": "xs", "color": C['text2'], "wrap": True, "margin": "md"},
                        {"type": "text", "text": "▫️ الصدارة: المتصدرين", "size": "xs", "color": C['text2'], "wrap": True, "margin": "sm"}
                    ],
                    "backgroundColor": C['bg'],
                    "cornerRadius": "12px",
                    "paddingAll": "16px",
                    "margin": "md"
                },
                {"type": "text", "text": "بوت الحوت", "size": "xxs", "color": C['text2'], "align": "center", "margin": "lg"}
            ],
            "paddingAll": "24px"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": "انضم", "text": "انضم"}, "style": "primary", "color": C['btn']},
                {"type": "button", "action": {"type": "message", "label": "نقاطي", "text": "نقاطي"}, "style": "secondary", "margin": "sm"}
            ],
            "paddingAll": "16px"
        }
    }

def stats_card(user_id, name, is_reg):
    stats = get_stats(user_id)
    status = "مسجل" if is_reg else "غير مسجل"
    color_status = "#34C759" if is_reg else C['text2']
    
    if not stats:
        return {
            "type": "bubble",
            "size": "kilo",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "إحصائياتك", "size": "xl", "weight": "bold", "color": C['text'], "align": "center"},
                    {"type": "separator", "margin": "lg", "color": C['sep']},
                    {"type": "text", "text": name, "size": "md", "color": C['text'], "align": "center", "margin": "lg"},
                    {"type": "text", "text": status, "size": "xs", "color": color_status, "align": "center", "margin": "sm"},
                    {"type": "text", "text": "لم تبدأ بعد" if is_reg else "سجل أولاً", "size": "md", "color": C['text2'], "align": "center", "margin": "lg"}
                ],
                "paddingAll": "24px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "button", "action": {"type": "message", "label": "انضم", "text": "انضم"}, "style": "primary", "color": C['btn']}
                ],
                "paddingAll": "16px"
            } if not is_reg else None
        }
    
    win_rate = (stats['wins'] / stats['games_played'] * 100) if stats['games_played'] > 0 else 0
    
    return {
        "type": "bubble",
        "size": "kilo",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "إحصائياتك", "size": "xl", "weight": "bold", "color": C['text'], "align": "center"},
                {"type": "separator", "margin": "lg", "color": C['sep']},
                {"type": "text", "text": name, "size": "md", "color": C['text'], "align": "center", "margin": "lg"},
                {"type": "text", "text": status, "size": "xs", "color": color_status, "align": "center", "margin": "sm"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "box", "layout": "horizontal", "contents": [
                            {"type": "text", "text": "النقاط", "size": "sm", "color": C['text2'], "flex": 1},
                            {"type": "text", "text": str(stats['total_points']), "size": "xxl", "weight": "bold", "color": C['btn'], "flex": 1, "align": "end"}
                        ]},
                        {"type": "separator", "margin": "lg", "color": C['sep']},
                        {"type": "box", "layout": "horizontal", "contents": [
                            {"type": "text", "text": "الألعاب", "size": "sm", "color": C['text2'], "flex": 1},
                            {"type": "text", "text": str(stats['games_played']), "size": "md", "color": C['text'], "flex": 1, "align": "end"}
                        ], "margin": "lg"},
                        {"type": "box", "layout": "horizontal", "contents": [
                            {"type": "text", "text": "الفوز", "size": "sm", "color": C['text2'], "flex": 1},
                            {"type": "text", "text": str(stats['wins']), "size": "md", "color": C['text'], "flex": 1, "align": "end"}
                        ], "margin": "md"},
                        {"type": "box", "layout": "horizontal", "contents": [
                            {"type": "text", "text": "معدل الفوز", "size": "sm", "color": C['text2'], "flex": 1},
                            {"type": "text", "text": f"{win_rate:.0f}%", "size": "md", "color": C['text'], "flex": 1, "align": "end"}
                        ], "margin": "md"}
                    ],
                    "backgroundColor": C['bg'],
                    "cornerRadius": "12px",
                    "paddingAll": "16px",
                    "margin": "lg"
                }
            ],
            "paddingAll": "24px"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": "الصدارة", "text": "الصدارة"}, "style": "secondary"}
            ],
            "paddingAll": "16px"
        }
    }

def leaderboard_card():
    leaders = get_leaderboard()
    if not leaders:
        return {
            "type": "bubble",
            "size": "kilo",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "لوحة الصدارة", "size": "xl", "weight": "bold", "color": C['text'], "align": "center"},
                    {"type": "separator", "margin": "lg", "color": C['sep']},
                    {"type": "text", "text": "لا توجد بيانات", "size": "md", "color": C['text2'], "align": "center", "margin": "lg"}
                ],
                "paddingAll": "24px"
            }
        }
    
    items = []
    for i, l in enumerate(leaders, 1):
        rank = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else str(i)
        items.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": rank, "size": "sm", "weight": "bold", "flex": 0, "color": C['text']},
                {"type": "text", "text": l['display_name'], "size": "sm", "flex": 3, "margin": "md", "wrap": True, "color": C['text']},
                {"type": "text", "text": str(l['total_points']), "size": "sm", "weight": "bold", "flex": 1, "align": "end", "color": C['btn']}
            ],
            "backgroundColor": C['bg'] if i > 3 else C['card'],
            "cornerRadius": "12px",
            "paddingAll": "12px",
            "margin": "sm" if i > 1 else "md"
        })
    
    return {
        "type": "bubble",
        "size": "kilo",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "لوحة الصدارة", "size": "xl", "weight": "bold", "color": C['text'], "align": "center"},
                {"type": "separator", "margin": "lg", "color": C['sep']},
                {"type": "text", "text": "أفضل اللاعبين", "size": "sm", "color": C['text2'], "align": "center", "margin": "md"},
                {"type": "box", "layout": "vertical", "contents": items, "margin": "lg"}
            ],
            "paddingAll": "24px"
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
                {"type": "text", "text": "تم التسجيل", "size": "xl", "weight": "bold", "color": C['text'], "align": "center"},
                {"type": "separator", "margin": "lg", "color": C['sep']},
                {"type": "text", "text": name, "size": "lg", "weight": "bold", "color": "#34C759", "align": "center", "margin": "lg"},
                {"type": "text", "text": "يمكنك الآن اللعب وجمع النقاط", "size": "sm", "color": C['text2'], "align": "center", "margin": "md"}
            ],
            "paddingAll": "24px"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": "ابدأ اللعب", "text": "أغنية"}, "style": "primary", "color": C['btn']}
            ],
            "paddingAll": "16px"
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
                {"type": "text", "text": "تم الانسحاب", "size": "xl", "weight": "bold", "color": C['text'], "align": "center"},
                {"type": "separator", "margin": "lg", "color": C['sep']},
                {"type": "text", "text": name, "size": "lg", "color": C['text2'], "align": "center", "margin": "lg"},
                {"type": "text", "text": "نتمنى رؤيتك مرة أخرى", "size": "sm", "color": C['text2'], "align": "center", "margin": "md"}
            ],
            "paddingAll": "24px"
        }
    }

# ═══════════════════════════════════════════════════════════════
# معالج الرسائل
# ═══════════════════════════════════════════════════════════════
COMMANDS = ['البداية', 'ابدأ', 'start', 'مساعدة', 'help', 'انضم', 'join', 'انسحب', 'خروج', 
            'نقاطي', 'إحصائياتي', 'الصدارة', 'المتصدرين', 'إيقاف', 'stop',
            'أغنية', 'لعبة', 'سلسلة', 'أسرع', 'ضد', 'تكوين', 'ترتيب', 'كلمة', 'لون',
            'سؤال', 'سوال', 'تحدي', 'اعتراف', 'منشن', 'اختلاف', 'توافق',
            'لمح', 'تلميح', 'جاوب', 'الحل', 'الجواب']

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        user_id = event.source.user_id
        text = safe_text(event.message.text, 500) if event.message.text else ""
        
        if not text:
            return
        
        # تحقق من الأوامر فقط
        text_lower = text.strip().lower()
        if not any(cmd.lower() in text_lower or text_lower.startswith(cmd.lower()) for cmd in COMMANDS):
            # تجاهل الرسائل العادية
            return
        
        # فحص Rate Limit
        if not check_rate(user_id):
            return
        
        # جلب الاسم وتحديث النشاط
        name = get_profile_safe(user_id)
        update_user(user_id, name)
        
        # تسجيل تلقائي عند أول تفاعل
        if user_id not in registered_players:
            stats = get_stats(user_id)
            if stats:
                registered_players.add(user_id)
        
        game_id = getattr(event.source, 'group_id', user_id)
        
        # ═══════════════════════════════════════════════════════════
        # الأوامر الأساسية
        # ═══════════════════════════════════════════════════════════
        if text in ['البداية', 'ابدأ', 'start']:
            line_bot_api.reply_message(
                event.reply_token,
                FlexSendMessage(alt_text="بوت الحوت", contents=welcome_card(), quick_reply=get_qr())
            )
            return
        
        if text in ['مساعدة', 'help']:
            line_bot_api.reply_message(
                event.reply_token,
                FlexSendMessage(alt_text="المساعدة", contents=help_card(), quick_reply=get_qr())
            )
            return
        
        if text in ['نقاطي', 'إحصائياتي', 'احصائياتي']:
            is_reg = user_id in registered_players
            line_bot_api.reply_message(
                event.reply_token,
                FlexSendMessage(alt_text="إحصائياتك", contents=stats_card(user_id, name, is_reg), quick_reply=get_qr())
            )
            return
        
        if text in ['الصدارة', 'المتصدرين']:
            line_bot_api.reply_message(
                event.reply_token,
                FlexSendMessage(alt_text="لوحة الصدارة", contents=leaderboard_card(), quick_reply=get_qr())
            )
            return
        
        if text in ['إيقاف', 'stop', 'ايقاف']:
            game_data = active_games.pop(game_id, None)
            if game_data:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=f"⏹️ تم إيقاف لعبة {game_data['type']}", quick_reply=get_qr())
                )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="لا توجد لعبة نشطة", quick_reply=get_qr())
                )
            return
        
        if text in ['انضم', 'تسجيل', 'join']:
            if user_id in registered_players:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=f"أنت مسجل بالفعل يا {name}", quick_reply=get_qr())
                )
            else:
                registered_players.add(user_id)
                line_bot_api.reply_message(
                    event.reply_token,
                    FlexSendMessage(alt_text="تم التسجيل", contents=registered_card(name), quick_reply=get_qr())
                )
                logger.info(f"تسجيل: {name}")
            return
        
        if text in ['انسحب', 'خروج']:
            if user_id in registered_players:
                registered_players.remove(user_id)
                line_bot_api.reply_message(
                    event.reply_token,
                    FlexSendMessage(alt_text="تم الانسحاب", contents=withdrawal_card(name), quick_reply=get_qr())
                )
                logger.info(f"انسحاب: {name}")
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="أنت غير مسجل", quick_reply=get_qr())
                )
            return
        
        # ═══════════════════════════════════════════════════════════
        # المحتوى النصي (بدون نقاط)
        # ═══════════════════════════════════════════════════════════
        if text in ['سؤال', 'سوال']:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=next_q(), quick_reply=get_qr())
            )
            return
        
        if text in ['تحدي', 'challenge']:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=next_c(), quick_reply=get_qr())
            )
            return
        
        if text in ['اعتراف', 'confession']:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=next_cf(), quick_reply=get_qr())
            )
            return
        
        if text in ['منشن', 'mention']:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=next_m(), quick_reply=get_qr())
            )
            return
        
        # ═══════════════════════════════════════════════════════════
        # الألعاب (تحتاج تسجيل)
        # ═══════════════════════════════════════════════════════════
        is_registered = user_id in registered_players
        
        # استيراد الألعاب من games.py
        try:
            from games import start_game, check_game_answer
            
            games_map = {
                'أغنية': 'song',
                'لعبة': 'game',
                'سلسلة': 'chain',
                'أسرع': 'fast',
                'ضد': 'opposite',
                'تكوين': 'build',
                'ترتيب': 'order',
                'كلمة': 'word',
                'لون': 'color',
                'اختلاف': 'diff',
                'توافق': 'compat'
            }
            
            if text in games_map:
                if not is_registered:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="⚠️ يجب التسجيل أولاً\n\nاكتب: انضم", quick_reply=get_qr())
                    )
                    return
                
                game_type = games_map[text]
                response = start_game(game_type, game_id, active_games, line_bot_api, ask_gemini)
                
                if response:
                    line_bot_api.reply_message(event.reply_token, response)
                return
            
            # معالجة الإجابات
            if game_id in active_games:
                if not is_registered:
                    return
                
                result = check_game_answer(
                    game_id, text, user_id, name, 
                    active_games, line_bot_api, update_points
                )
                
                if result:
                    line_bot_api.reply_message(event.reply_token, result)
                return
        
        except ImportError:
            logger.error("ملف games.py غير موجود")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌ خطأ: ملف الألعاب غير موجود", quick_reply=get_qr())
            )
    
    except Exception as e:
        logger.error(f"خطأ في معالجة الرسالة: {e}", exc_info=True)

# ═══════════════════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════════════════
@app.route("/", methods=['GET'])
def home():
    return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>بوت الحوت</title>
    <style>
        * {{margin:0;padding:0;box-sizing:border-box}}
        body {{font-family:-apple-system,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}
        .container {{background:rgba(255,255,255,0.98);border-radius:24px;box-shadow:0 20px 60px rgba(0,0,0,0.3);padding:40px;max-width:600px;width:100%}}
        h1 {{color:#667eea;font-size:2.5em;margin-bottom:8px;text-align:center;font-weight:700}}
        .subtitle {{color:#64748b;font-size:1em;text-align:center;margin-bottom:30px}}
        .status {{background:#f8fafc;border-radius:16px;padding:24px;margin:20px 0}}
        .status-item {{display:flex;justify-content:space-between;align-items:center;padding:16px 0;border-bottom:1px solid #e2e8f0}}
        .status-item:last-child {{border-bottom:none}}
        .label {{color:#64748b;font-size:0.95em;font-weight:500}}
        .value {{color:#1e293b;font-weight:700;font-size:1.1em}}
        .badge {{display:inline-block;padding:6px 14px;border-radius:20px;font-size:0.85em;font-weight:600}}
        .badge.success {{background:#dcfce7;color:#16a34a}}
        .footer {{text-align:center;margin-top:30px;color:#94a3b8;font-size:0.85em}}
    </style>
</head>
<body>
    <div class="container">
        <h1>بوت الحوت</h1>
        <div class="subtitle">نظام ألعاب تفاعلية</div>
        <div class="status">
            <div class="status-item">
                <span class="label">حالة الخادم</span>
                <span class="badge success">يعمل</span>
            </div>
            <div class="status-item">
                <span class="label">الذكاء الاصطناعي</span>
                <span class="badge {'success' if USE_AI else 'warning'}">{'مفعّل' if USE_AI else 'معطّل'}</span>
            </div>
            <div class="status-item">
                <span class="label">اللاعبون المسجلون</span>
                <span class="value">{len(registered_players)}</span>
            </div>
            <div class="status-item">
                <span class="label">الألعاب النشطة</span>
                <span class="value">{len(active_games)}</span>
            </div>
        </div>
        <div class="footer">بوت الحوت © 2025</div>
    </div>
</body>
</html>"""

@app.route("/health", methods=['GET'])
def health():
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.close()
        db_status = "connected"
    except:
        db_status = "error"
    
    return {
        "status": "healthy",
        "version": "3.0.0",
        "timestamp": datetime.now().isoformat(),
        "active_games": len(active_games),
        "registered_players": len(registered_players),
        "ai_enabled": USE_AI,
        "database": db_status
    }

@app.route("/callback", methods=['POST'])
def callback():
    if not handler or not line_bot_api:
        abort(500)
    
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("توقيع غير صالح")
        abort(400)
    except Exception as e:
        logger.error(f"خطأ webhook: {e}")
    
    return 'OK'

@app.errorhandler(404)
def not_found(error):
    return {"error": "الصفحة غير موجودة"}, 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"خطأ داخلي: {error}")
    return {"error": "خطأ داخلي في الخادم"}, 500

@app.errorhandler(Exception)
def handle_exception(error):
    logger.error(f"خطأ غير متوقع: {error}", exc_info=True)
    return 'OK', 200

# ═══════════════════════════════════════════════════════════════
# التشغيل
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    
    print("\n" + "="*60)
    print("بوت الحوت جاهز")
    print(f"المنفذ: {port}")
    print(f"الذكاء الاصطناعي: {'مفعّل' if USE_AI else 'معطّل'}")
    print("="*60 + "\n")
    
    try:
        logger.info(f"بدء الخادم على المنفذ {port}")
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("تم إيقاف الخادم")
        cleanup_inactive()
    except Exception as e:
        logger.critical(f"فشل التشغيل: {e}")
        sys.exit(1)
