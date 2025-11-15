"""
بوت الحوت - نظام ألعاب تفاعلية على LINE
نسخة محسّنة ومتكاملة بتصميم iOS نظيف
"""

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, QuickReply, 
    QuickReplyButton, MessageAction, FlexSendMessage
)
import os
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import time
import random
import logging
import sys
import re

# ═══════════════════════════════════════════════════════════════
# إعدادات النظام
# ═══════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("whale-bot")

# الثوابت
LINE_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
LINE_SECRET = os.getenv('LINE_CHANNEL_SECRET', '')
GEMINI_KEYS = [k for k in [
    os.getenv('GEMINI_API_KEY_1', ''),
    os.getenv('GEMINI_API_KEY_2', '')
] if k]

RATE_LIMIT = {'max': 30, 'window': 60}
DB_NAME = 'game_bot.db'
INACTIVE_DAYS = 45
GAME_TIMEOUT_MINUTES = 15
CLEANUP_INTERVAL_SECONDS = 300
NAMES_CACHE_MAX = 1000

# نظام الألوان iOS Style
THEME = {
    'bg': '#F2F2F7',
    'card': '#FFFFFF',
    'text': '#000000',
    'text_secondary': '#8E8E93',
    'accent': '#007AFF',
    'success': '#34C759',
    'danger': '#FF3B30',
    'separator': '#D1D1D6'
}

NO_POINTS_GAMES = ['اختلاف', 'توافق', 'سؤال', 'اعتراف', 'تحدي', 'منشن']

# ═══════════════════════════════════════════════════════════════
# قاعدة البيانات
# ═══════════════════════════════════════════════════════════════
def get_db():
    """اتصال آمن بقاعدة البيانات"""
    try:
        conn = sqlite3.connect(DB_NAME, check_same_thread=False, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"فشل الاتصال بقاعدة البيانات: {e}")
        return None

def init_db():
    """تهيئة قاعدة البيانات مع معالجة الأخطاء"""
    try:
        conn = get_db()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # جدول اللاعبين
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                user_id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                total_points INTEGER DEFAULT 0,
                games_played INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_active TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول تاريخ الألعاب
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                game_type TEXT NOT NULL,
                points INTEGER DEFAULT 0,
                won INTEGER DEFAULT 0,
                played_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES players(user_id) ON DELETE CASCADE
            )
        ''')
        
        # الفهارس
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_points ON players(total_points DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_active ON players(last_active)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_history ON game_history(user_id, played_at)')
        
        conn.commit()
        conn.close()
        logger.info("قاعدة البيانات جاهزة")
        return True
    except Exception as e:
        logger.error(f"خطأ في تهيئة قاعدة البيانات: {e}")
        return False

# ═══════════════════════════════════════════════════════════════
# دوال مساعدة
# ═══════════════════════════════════════════════════════════════
def safe_text(text):
    """تنظيف النص من الأحرف الخطرة"""
    if not text:
        return ""
    # إزالة الأحرف الخاصة التي قد تسبب مشاكل
    text = str(text).strip()
    text = text.replace('"', '').replace("'", '').replace('\\', '')
    return text[:500]  # حد أقصى 500 حرف

def normalize_text(text):
    """تطبيع النص العربي للمقارنة"""
    if not text:
        return ""
    
    text = text.strip().lower()
    # توحيد الألف
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    # توحيد الواو والياء
    text = text.replace('ؤ', 'و').replace('ئ', 'ي').replace('ء', '')
    # توحيد التاء والياء
    text = text.replace('ة', 'ه').replace('ى', 'ي')
    # إزالة التشكيل
    text = re.sub(r'[\u064B-\u065F]', '', text)
    # إزالة المسافات الزائدة
    text = re.sub(r'\s+', ' ', text)
    
    return text

def load_file(filename):
    """تحميل ملف نصي بشكل آمن"""
    try:
        filepath = os.path.join('games', filename)
        if not os.path.exists(filepath):
            logger.warning(f"الملف غير موجود: {filename}")
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [safe_text(line) for line in f if line.strip()]
            logger.info(f"تم تحميل {len(lines)} سطر من {filename}")
            return lines
    except Exception as e:
        logger.error(f"خطأ في تحميل {filename}: {e}")
        return []

# ═══════════════════════════════════════════════════════════════
# إدارة المستخدمين
# ═══════════════════════════════════════════════════════════════
def update_user_activity(user_id, display_name):
    """تحديث آخر نشاط للمستخدم"""
    try:
        conn = get_db()
        if not conn:
            return False
        
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        safe_name = safe_text(display_name)
        
        cursor.execute('SELECT user_id FROM players WHERE user_id = ?', (user_id,))
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute(
                'UPDATE players SET last_active = ?, display_name = ? WHERE user_id = ?',
                (now, safe_name, user_id)
            )
        else:
            cursor.execute(
                'INSERT INTO players (user_id, display_name, last_active) VALUES (?, ?, ?)',
                (user_id, safe_name, now)
            )
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"خطأ في تحديث النشاط: {e}")
        return False

def update_points(user_id, display_name, points, won=False, game_type=''):
    """تحديث نقاط اللاعب"""
    if game_type in NO_POINTS_GAMES:
        points = 0
    
    try:
        conn = get_db()
        if not conn:
            return False
        
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        safe_name = safe_text(display_name)
        
        cursor.execute('SELECT * FROM players WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        
        if user:
            new_points = max(0, user['total_points'] + points)
            new_games = user['games_played'] + 1
            new_wins = user['wins'] + (1 if won else 0)
            
            cursor.execute('''
                UPDATE players 
                SET total_points = ?, games_played = ?, wins = ?, 
                    last_active = ?, display_name = ? 
                WHERE user_id = ?
            ''', (new_points, new_games, new_wins, now, safe_name, user_id))
        else:
            cursor.execute('''
                INSERT INTO players 
                (user_id, display_name, total_points, games_played, wins, last_active) 
                VALUES (?, ?, ?, 1, ?, ?)
            ''', (user_id, safe_name, max(0, points), 1 if won else 0, now))
        
        if game_type and points != 0:
            cursor.execute(
                'INSERT INTO game_history (user_id, game_type, points, won) VALUES (?, ?, ?, ?)',
                (user_id, game_type, points, 1 if won else 0)
            )
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"خطأ في تحديث النقاط: {e}")
        return False

def get_stats(user_id):
    """جلب إحصائيات اللاعب"""
    try:
        conn = get_db()
        if not conn:
            return None
        
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM players WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    except Exception as e:
        logger.error(f"خطأ في جلب الإحصائيات: {e}")
        return None

def get_leaderboard(limit=10):
    """جلب لوحة الصدارة"""
    try:
        conn = get_db()
        if not conn:
            return []
        
        cursor = conn.cursor()
        cursor.execute('''
            SELECT display_name, total_points, games_played, wins 
            FROM players 
            WHERE total_points > 0
            ORDER BY total_points DESC, wins DESC 
            LIMIT ?
        ''', (limit,))
        leaders = cursor.fetchall()
        conn.close()
        return [dict(l) for l in leaders]
    except Exception as e:
        logger.error(f"خطأ في جلب الصدارة: {e}")
        return []

def cleanup_inactive_users():
    """حذف المستخدمين غير النشطين"""
    try:
        conn = get_db()
        if not conn:
            return
        
        cursor = conn.cursor()
        cutoff_date = (datetime.now() - timedelta(days=INACTIVE_DAYS)).isoformat()
        
        cursor.execute('SELECT COUNT(*) FROM players WHERE last_active < ?', (cutoff_date,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            cursor.execute('DELETE FROM players WHERE last_active < ?', (cutoff_date,))
            cursor.execute(
                'DELETE FROM game_history WHERE user_id NOT IN (SELECT user_id FROM players)'
            )
            conn.commit()
            logger.info(f"تم حذف {count} مستخدم غير نشط")
        
        conn.close()
    except Exception as e:
        logger.error(f"خطأ في تنظيف المستخدمين: {e}")

# ═══════════════════════════════════════════════════════════════
# Gemini AI
# ═══════════════════════════════════════════════════════════════
USE_AI = False
ask_gemini = None

try:
    import google.generativeai as genai
    if GEMINI_KEYS:
        genai.configure(api_key=GEMINI_KEYS[0])
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        USE_AI = True
        logger.info(f"Gemini AI جاهز ({len(GEMINI_KEYS)} مفاتيح)")
        
        def ask_gemini(prompt, max_retries=2):
            """استدعاء Gemini AI مع إعادة المحاولة"""
            for attempt in range(max_retries):
                try:
                    response = model.generate_content(prompt)
                    if response and response.text:
                        return response.text.strip()
                except Exception as e:
                    logger.error(f"خطأ Gemini (محاولة {attempt + 1}): {e}")
                    if attempt < max_retries - 1 and len(GEMINI_KEYS) > 1:
                        genai.configure(api_key=GEMINI_KEYS[(attempt + 1) % len(GEMINI_KEYS)])
            return None
except ImportError:
    logger.warning("مكتبة Gemini غير مثبتة")
except Exception as e:
    logger.warning(f"Gemini غير متوفر: {e}")

# ═══════════════════════════════════════════════════════════════
# استيراد الألعاب
# ═══════════════════════════════════════════════════════════════
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'games'))

SongGame = HumanAnimalPlantGame = ChainWordsGame = FastTypingGame = None
OppositeGame = LettersWordsGame = DifferencesGame = CompatibilityGame = None

try:
    from song_game import SongGame
    from human_animal_plant_game import HumanAnimalPlantGame
    from chain_words_game import ChainWordsGame
    from fast_typing_game import FastTypingGame
    from opposite_game import OppositeGame
    from letters_words_game import LettersWordsGame
    from differences_game import DifferencesGame
    from compatibility_game import CompatibilityGame
    logger.info("تم استيراد جميع الألعاب بنجاح")
except ImportError as e:
    logger.error(f"خطأ في استيراد الألعاب: {e}")
except Exception as e:
    logger.error(f"خطأ غير متوقع في استيراد الألعاب: {e}")

# ═══════════════════════════════════════════════════════════════
# Flask و LINE Bot
# ═══════════════════════════════════════════════════════════════
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

line_bot_api = LineBotApi(LINE_TOKEN) if LINE_TOKEN else None
handler = WebhookHandler(LINE_SECRET) if LINE_SECRET else None

# البيانات المشتركة
active_games = {}
registered_players = set()
user_message_count = defaultdict(lambda: {'count': 0, 'reset_time': datetime.now()})
user_names_cache = {}

# Locks للأمان
games_lock = threading.Lock()
players_lock = threading.Lock()
names_cache_lock = threading.Lock()

# تهيئة النظام
if not init_db():
    logger.critical("فشل في تهيئة قاعدة البيانات")

# تحميل الملفات
QUESTIONS = load_file('questions.txt')
CHALLENGES = load_file('challenges.txt')
CONFESSIONS = load_file('confessions.txt')
MENTIONS = load_file('more_questions.txt')

# ═══════════════════════════════════════════════════════════════
# دوال LINE Bot
# ═══════════════════════════════════════════════════════════════
def get_profile_safe(user_id):
    """جلب اسم المستخدم بشكل آمن"""
    with names_cache_lock:
        if user_id in user_names_cache:
            return user_names_cache[user_id]
    
    fallback_name = f"لاعب {user_id[-4:]}"
    
    if not line_bot_api:
        return fallback_name
    
    try:
        profile = line_bot_api.get_profile(user_id)
        display_name = safe_text(profile.display_name) if profile.display_name else fallback_name
        
        with names_cache_lock:
            user_names_cache[user_id] = display_name
        
        return display_name
    except LineBotApiError as e:
        if e.status_code != 404:
            logger.error(f"خطأ LINE API ({e.status_code}): {e.message}")
    except Exception as e:
        logger.error(f"خطأ غير متوقع في جلب الملف: {e}")
    
    with names_cache_lock:
        user_names_cache[user_id] = fallback_name
    
    return fallback_name

def check_rate(user_id):
    """فحص معدل الرسائل"""
    now = datetime.now()
    data = user_message_count[user_id]
    
    if now - data['reset_time'] > timedelta(seconds=RATE_LIMIT['window']):
        data['count'] = 0
        data['reset_time'] = now
    
    if data['count'] >= RATE_LIMIT['max']:
        return False
    
    data['count'] += 1
    return True

def get_quick_reply():
    """أزرار Quick Reply"""
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

# ═══════════════════════════════════════════════════════════════
# بطاقات Flex - iOS Style
# ═══════════════════════════════════════════════════════════════
def create_card(title, body_content, footer_buttons=None):
    """إنشاء بطاقة iOS نظيفة"""
    body = {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "text",
                "text": title,
                "size": "xl",
                "weight": "bold",
                "color": THEME['text'],
                "align": "center"
            },
            {
                "type": "separator",
                "margin": "xl",
                "color": THEME['separator']
            }
        ],
        "backgroundColor": THEME['card'],
        "paddingAll": "24px",
        "spacing": "lg"
    }
    
    if isinstance(body_content, list):
        body["contents"].extend(body_content)
    else:
        body["contents"].append(body_content)
    
    card = {
        "type": "bubble",
        "size": "kilo",
        "body": body
    }
    
    if footer_buttons and len(footer_buttons) > 0:
        card["footer"] = {
            "type": "box",
            "layout": "vertical",
            "contents": footer_buttons,
            "spacing": "sm",
            "paddingAll": "20px",
            "backgroundColor": THEME['card']
        }
    
    return card

def create_button(label, text, style="primary"):
    """إنشاء زر iOS"""
    color = THEME['accent'] if style == "primary" else THEME['text_secondary']
    return {
        "type": "button",
        "action": {
            "type": "message",
            "label": label,
            "text": text
        },
        "style": style,
        "color": color,
        "height": "sm"
    }

def get_welcome_card(name):
    """بطاقة الترحيب"""
    return create_card("مرحباً", [
        {
            "type": "text",
            "text": name,
            "size": "lg",
            "color": THEME['text'],
            "align": "center",
            "margin": "xl",
            "weight": "bold"
        },
        {
            "type": "text",
            "text": "اختر من الأزرار أدناه",
            "size": "sm",
            "color": THEME['text_secondary'],
            "align": "center",
            "margin": "md"
        }
    ], [
        create_button("انضم", "انضم", "primary"),
        {"type": "separator", "margin": "md", "color": THEME['separator']},
        create_button("المساعدة", "مساعدة", "secondary")
    ])

def get_help_card():
    """بطاقة المساعدة"""
    return create_card("المساعدة", [
        {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "الأوامر الأساسية",
                    "size": "md",
                    "weight": "bold",
                    "color": THEME['text']
                },
                {
                    "type": "text",
                    "text": "انضم - للتسجيل في النظام\nانسحب - للإلغاء\nنقاطي - عرض الإحصائيات\nالصدارة - عرض الترتيب\nإيقاف - إنهاء اللعبة الحالية",
                    "size": "xs",
                    "color": THEME['text_secondary'],
                    "wrap": True,
                    "margin": "md"
                },
                {
                    "type": "separator",
                    "margin": "lg",
                    "color": THEME['separator']
                },
                {
                    "type": "text",
                    "text": "أوامر اللعب",
                    "size": "md",
                    "weight": "bold",
                    "color": THEME['text'],
                    "margin": "lg"
                },
                {
                    "type": "text",
                    "text": "لمح - طلب تلميح خلال اللعبة\nجاوب - عرض الحل الكامل",
                    "size": "xs",
                    "color": THEME['text_secondary'],
                    "wrap": True,
                    "margin": "md"
                }
            ],
            "margin": "xl",
            "paddingAll": "16px",
            "backgroundColor": THEME['bg'],
            "cornerRadius": "12px"
        }
    ], [
        create_button("نقاطي", "نقاطي", "primary"),
        {"type": "separator", "margin": "md", "color": THEME['separator']},
        create_button("الصدارة", "الصدارة", "secondary")
    ])

def get_registration_card(name):
    """بطاقة التسجيل"""
    return create_card("تم التسجيل", [
        {
            "type": "text",
            "text": name,
            "size": "lg",
            "weight": "bold",
            "color": THEME['success'],
            "align": "center",
            "margin": "xl"
        },
        {
            "type": "text",
            "text": "يمكنك الآن اللعب وجمع النقاط",
            "size": "sm",
            "color": THEME['text_secondary'],
            "align": "center",
            "margin": "md"
        }
    ], [
        create_button("ابدأ اللعب", "أغنية", "primary")
    ])

def get_withdrawal_card(name):
    """بطاقة الانسحاب"""
    return create_card("تم الانسحاب", [
        {
            "type": "text",
            "text": name,
            "size": "lg",
            "color": THEME['text_secondary'],
            "align": "center",
            "margin": "xl"
        },
        {
            "type": "text",
            "text": "نتمنى رؤيتك مرة أخرى",
            "size": "sm",
            "color": THEME['text_secondary'],
            "align": "center",
            "margin": "md"
        }
    ])

def get_stats_card(user_id, name):
    """بطاقة الإحصائيات"""
    stats = get_stats(user_id)
    
    with players_lock:
        is_registered = user_id in registered_players
    
    status_text = "مسجل" if is_registered else "غير مسجل"
    status_color = THEME['success'] if is_registered else THEME['text_secondary']
    
    if not stats:
        footer = [create_button("ابدأ الآن", "انضم", "primary")] if not is_registered else None
        
        return create_card("إحصائياتك", [
            {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": name,
                        "size": "md",
                        "color": THEME['text'],
                        "align": "center",
                        "weight": "bold"
                    },
                    {
                        "type": "text",
                        "text": status_text,
                        "size": "xs",
                        "color": status_color,
                        "align": "center",
                        "margin": "sm"
                    }
                ],
                "margin": "xl"
            },
            {
                "type": "text",
                "text": "لم تبدأ بعد" if is_registered else "يجب التسجيل أولاً",
                "size": "md",
                "color": THEME['text_secondary'],
                "align": "center",
                "margin": "xl"
            }
        ], footer)
    
    win_rate = (stats['wins'] / stats['games_played'] * 100) if stats['games_played'] > 0 else 0
    
    footer_buttons = [create_button("الصدارة", "الصدارة", "secondary")]
    if is_registered:
        footer_buttons.extend([
            {"type": "separator", "margin": "md", "color": THEME['separator']},
            create_button("انسحب", "انسحب", "secondary")
        ])
    
    return create_card("إحصائياتك", [
        {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": name,
                    "size": "md",
                    "color": THEME['text'],
                    "align": "center",
                    "weight": "bold"
                },
                {
                    "type": "text",
                    "text": status_text,
                    "size": "xs",
                    "color": status_color,
                    "align": "center",
                    "margin": "sm"
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
                        {
                            "type": "text",
                            "text": "النقاط",
                            "size": "sm",
                            "color": THEME['text_secondary'],
                            "flex": 1
                        },
                        {
                            "type": "text",
                            "text": str(stats['total_points']),
                            "size": "xxl",
                            "weight": "bold",
                            "color": THEME['accent'],
                            "flex": 1,
                            "align": "end"
                        }
                    ]
                },
                {
                    "type": "separator",
                    "margin": "lg",
                    "color": THEME['separator']
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "الألعاب",
                            "size": "sm",
                            "color": THEME['text_secondary'],
                            "flex": 1
                        },
                        {
                            "type": "text",
                            "text": str(stats['games_played']),
                            "size": "md",
                            "color": THEME['text'],
                            "flex": 1,
                            "align": "end"
                        }
                    ],
                    "margin": "lg"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "الفوز",
                            "size": "sm",
                            "color": THEME['text_secondary'],
                            "flex": 1
                        },
                        {
                            "type": "text",
                            "text": str(stats['wins']),
                            "size": "md",
                            "color": THEME['text'],
                            "flex": 1,
                            "align": "end"
                        }
                    ],
                    "margin": "md"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "معدل الفوز",
                            "size": "sm",
                            "color": THEME['text_secondary'],
                            "flex": 1
                        },
                        {
                            "type": "text",
                            "text": f"{win_rate:.0f}%",
                            "size": "md",
                            "color": THEME['text'],
                            "flex": 1,
                            "align": "end"
                        }
                    ],
                    "margin": "md"
                }
            ],
            "margin": "xl",
            "paddingAll": "16px",
            "backgroundColor": THEME['bg'],
            "cornerRadius": "12px"
        }
    ], footer_buttons)

def get_leaderboard_card():
    """بطاقة الصدارة"""
    leaders = get_leaderboard()
    
    if not leaders:
        return create_card("لوحة الصدارة", [
            {
                "type": "text",
                "text": "لا توجد بيانات",
                "size": "md",
                "color": THEME['text_secondary'],
                "align": "center",
                "margin": "xl"
            }
        ])
    
    items = []
    for i, leader in enumerate(leaders, 1):
        if i == 1:
            rank = "🥇"
        elif i == 2:
            rank = "🥈"
        elif i == 3:
            rank = "🥉"
        else:
            rank = str(i)
        
        items.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": rank,
                    "size": "sm",
                    "weight": "bold",
                    "flex": 0,
                    "color": THEME['text']
                },
                {
                    "type": "text",
                    "text": leader['display_name'],
                    "size": "sm",
                    "flex": 3,
                    "margin": "md",
                    "wrap": True,
                    "color": THEME['text']
                },
                {
                    "type": "text",
                    "text": str(leader['total_points']),
                    "size": "sm",
                    "weight": "bold",
                    "flex": 1,
                    "align": "end",
                    "color": THEME['accent']
                }
            ],
            "paddingAll": "12px",
            "backgroundColor": THEME['bg'] if i > 3 else THEME['card'],
            "cornerRadius": "12px",
            "margin": "sm" if i > 1 else "md"
        })
    
    return create_card("لوحة الصدارة", [
        {
            "type": "text",
            "text": "أفضل اللاعبين",
            "size": "sm",
            "color": THEME['text_secondary'],
            "align": "center",
            "margin": "md"
        },
        {
            "type": "box",
            "layout": "vertical",
            "contents": items,
            "margin": "lg"
        }
    ])

# ═══════════════════════════════════════════════════════════════
# إدارة الألعاب
# ═══════════════════════════════════════════════════════════════
def start_game(game_id, game_class, game_type, user_id, event):
    """بدء لعبة جديدة"""
    if not game_class:
        try:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"لعبة {game_type} غير متوفرة حالياً",
                    quick_reply=get_quick_reply()
                )
            )
        except Exception as e:
            logger.error(f"خطأ في إرسال رسالة: {e}")
        return False
    
    try:
        with games_lock:
            # إنشاء اللعبة
            if game_class in [SongGame, HumanAnimalPlantGame, LettersWordsGame]:
                game = game_class(line_bot_api, use_ai=USE_AI, ask_ai=ask_gemini)
            else:
                game = game_class(line_bot_api)
            
            # إضافة المشاركين
            with players_lock:
                participants = registered_players.copy()
                participants.add(user_id)
            
            # حفظ اللعبة
            active_games[game_id] = {
                'game': game,
                'type': game_type,
                'created_at': datetime.now(),
                'participants': participants,
                'answered_users': set(),
                'last_game': game_type
            }
        
        # بدء اللعبة
        response = game.start_game()
        
        # إضافة Quick Reply
        if isinstance(response, TextSendMessage):
            response.quick_reply = get_quick_reply()
        elif isinstance(response, list):
            for r in response:
                if isinstance(r, TextSendMessage):
                    r.quick_reply = get_quick_reply()
        
        line_bot_api.reply_message(event.reply_token, response)
        logger.info(f"بدأت لعبة {game_type} للمستخدم {user_id[-4:]}")
        return True
    
    except Exception as e:
        logger.error(f"خطأ في بدء لعبة {game_type}: {e}")
        try:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="حدث خطأ في بدء اللعبة، يرجى المحاولة مرة أخرى",
                    quick_reply=get_quick_reply()
                )
            )
        except:
            pass
        return False

# ═══════════════════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════════════════
@app.route("/", methods=['GET'])
def home():
    """الصفحة الرئيسية"""
    games_status = []
    if SongGame: games_status.append("أغنية")
    if HumanAnimalPlantGame: games_status.append("لعبة")
    if ChainWordsGame: games_status.append("سلسلة")
    if FastTypingGame: games_status.append("أسرع")
    if OppositeGame: games_status.append("ضد")
    if LettersWordsGame: games_status.append("تكوين")
    if DifferencesGame: games_status.append("اختلاف")
    if CompatibilityGame: games_status.append("توافق")
    
    return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>بوت الحوت</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #F2F2F7;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .container {{
            background: #FFFFFF;
            border-radius: 20px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.08);
            padding: 40px;
            max-width: 500px;
            width: 100%;
        }}
        h1 {{
            color: #000000;
            font-size: 2em;
            margin-bottom: 8px;
            text-align: center;
        }}
        .subtitle {{
            color: #8E8E93;
            font-size: 0.9em;
            text-align: center;
            margin-bottom: 30px;
        }}
        .status {{
            background: #F2F2F7;
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
        }}
        .status-item {{
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #D1D1D6;
        }}
        .status-item:last-child {{
            border-bottom: none;
        }}
        .label {{
            color: #8E8E93;
            font-size: 0.9em;
        }}
        .value {{
            color: #000000;
            font-weight: 600;
        }}
        .success {{
            color: #34C759;
        }}
        .warning {{
            color: #FF9500;
        }}
        .games-list {{
            background: #F2F2F7;
            border-radius: 10px;
            padding: 14px;
            margin-top: 10px;
            font-size: 0.85em;
            color: #000000;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #8E8E93;
            font-size: 0.8em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>بوت الحوت</h1>
        <div class="subtitle">نظام ألعاب تفاعلية</div>
        <div class="status">
            <div class="status-item">
                <span class="label">حالة الخادم</span>
                <span class="value success">يعمل</span>
            </div>
            <div class="status-item">
                <span class="label">Gemini AI</span>
                <span class="value {'success' if USE_AI else 'warning'}">{'مفعّل' if USE_AI else 'معطّل'}</span>
            </div>
            <div class="status-item">
                <span class="label">اللاعبون المسجلون</span>
                <span class="value">{len(registered_players)}</span>
            </div>
            <div class="status-item">
                <span class="label">الألعاب النشطة</span>
                <span class="value">{len(active_games)}</span>
            </div>
            <div class="status-item">
                <span class="label">الألعاب المتوفرة</span>
                <span class="value">{len(games_status)} من 8</span>
            </div>
        </div>
        <div class="games-list">
            <strong>الألعاب الجاهزة:</strong> {', '.join(games_status) if games_status else 'لا توجد ألعاب'}
        </div>
        <div class="footer">بوت الحوت 2025</div>
    </div>
</body>
</html>"""

@app.route("/health", methods=['GET'])
def health():
    """فحص صحة الخادم"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_games": len(active_games),
        "registered_players": len(registered_players),
        "cached_names": len(user_names_cache),
        "ai_enabled": USE_AI,
        "database": "connected" if get_db() else "disconnected"
    }, 200

@app.route("/callback", methods=['POST'])
def callback():
    """معالجة طلبات LINE"""
    if not handler or not line_bot_api:
        logger.error("LINE Bot غير مهيأ بشكل صحيح")
        abort(500)
    
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("توقيع غير صالح")
        abort(400)
    except Exception as e:
        logger.error(f"خطأ في معالجة webhook: {e}")
    
    return 'OK'

# ═══════════════════════════════════════════════════════════════
# معالج الرسائل
# ═══════════════════════════════════════════════════════════════
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """معالجة الرسائل الواردة"""
    try:
        user_id = event.source.user_id
        text = safe_text(event.message.text) if event.message.text else ""
        
        if not text or not check_rate(user_id):
            return
        
        name = get_profile_safe(user_id)
        game_id = getattr(event.source, 'group_id', user_id)
        
        # تحديث النشاط
        update_user_activity(user_id, name)
        logger.info(f"رسالة من {name} ({user_id[-4:]}): {text[:50]}")
        
        # ═══════════════════════════════════════════════════════════
        # الأوامر الأساسية
        # ═══════════════════════════════════════════════════════════
        if text in ['البداية', 'ابدأ', 'start', 'البوت']:
            line_bot_api.reply_message(
                event.reply_token,
                FlexSendMessage(
                    alt_text=f"مرحباً {name}",
                    contents=get_welcome_card(name),
                    quick_reply=get_quick_reply()
                )
            )
            return
        
        if text in ['مساعدة', 'help', 'كيف ألعب']:
            line_bot_api.reply_message(
                event.reply_token,
                FlexSendMessage(
                    alt_text="المساعدة",
                    contents=get_help_card(),
                    quick_reply=get_quick_reply()
                )
            )
            return
        
        if text in ['نقاطي', 'إحصائياتي', 'احصائياتي']:
            line_bot_api.reply_message(
                event.reply_token,
                FlexSendMessage(
                    alt_text="إحصائياتك",
                    contents=get_stats_card(user_id, name),
                    quick_reply=get_quick_reply()
                )
            )
            return
        
        if text in ['الصدارة', 'المتصدرين']:
            line_bot_api.reply_message(
                event.reply_token,
                FlexSendMessage(
                    alt_text="لوحة الصدارة",
                    contents=get_leaderboard_card(),
                    quick_reply=get_quick_reply()
                )
            )
            return
        
        if text in ['إيقاف', 'stop', 'ايقاف']:
            with games_lock:
                if game_id in active_games:
                    game_type = active_games[game_id]['type']
                    del active_games[game_id]
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text=f"تم إيقاف لعبة {game_type}",
                            quick_reply=get_quick_reply()
                        )
                    )
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="لا توجد لعبة نشطة",
                            quick_reply=get_quick_reply()
                        )
                    )
            return
        
        if text in ['انضم', 'تسجيل', 'join']:
            with players_lock:
                if user_id in registered_players:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text=f"أنت مسجل بالفعل يا {name}",
                            quick_reply=get_quick_reply()
                        )
                    )
                else:
                    registered_players.add(user_id)
                    line_bot_api.reply_message(
                        event.reply_token,
                        FlexSendMessage(
                            alt_text="تم التسجيل",
                            contents=get_registration_card(name),
                            quick_reply=get_quick_reply()
                        )
                    )
                    logger.info(f"تسجيل لاعب جديد: {name} ({user_id[-4:]})")
            return
        
        if text in ['انسحب', 'خروج']:
            with players_lock:
                if user_id in registered_players:
                    registered_players.remove(user_id)
                    line_bot_api.reply_message(
                        event.reply_token,
                        FlexSendMessage(
                            alt_text="تم الانسحاب",
                            contents=get_withdrawal_card(name),
                            quick_reply=get_quick_reply()
                        )
                    )
                    logger.info(f"انسحاب لاعب: {name} ({user_id[-4:]})")
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="أنت غير مسجل",
                            quick_reply=get_quick_reply()
                        )
                    )
            return
        
        # ═══════════════════════════════════════════════════════════
        # الأوامر النصية للجميع
        # ═══════════════════════════════════════════════════════════
        if text in ['سؤال', 'سوال'] and QUESTIONS:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=random.choice(QUESTIONS),
                    quick_reply=get_quick_reply()
                )
            )
            return
        
        if text in ['تحدي', 'challenge'] and CHALLENGES:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=random.choice(CHALLENGES),
                    quick_reply=get_quick_reply()
                )
            )
            return
        
        if text in ['اعتراف', 'confession'] and CONFESSIONS:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=random.choice(CONFESSIONS),
                    quick_reply=get_quick_reply()
                )
            )
            return
        
        if text in ['منشن', 'mention'] and MENTIONS:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=random.choice(MENTIONS),
                    quick_reply=get_quick_reply()
                )
            )
            return
        
        # ═══════════════════════════════════════════════════════════
        # بدء الألعاب (للمسجلين فقط)
        # ═══════════════════════════════════════════════════════════
        with players_lock:
            is_registered = user_id in registered_players
        
        games_map = {
            'أغنية': (SongGame, 'أغنية'),
            'لعبة': (HumanAnimalPlantGame, 'لعبة'),
            'سلسلة': (ChainWordsGame, 'سلسلة'),
            'أسرع': (FastTypingGame, 'أسرع'),
            'ضد': (OppositeGame, 'ضد'),
            'تكوين': (LettersWordsGame, 'تكوين'),
            'اختلاف': (DifferencesGame, 'اختلاف'),
            'توافق': (CompatibilityGame, 'توافق')
        }
        
        if text in games_map:
            if not is_registered:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="يجب التسجيل أولاً\n\nاكتب: انضم",
                        quick_reply=get_quick_reply()
                    )
                )
                return
            
            game_class, game_type = games_map[text]
            
            # معالجة خاصة للعبة التوافق
            if text == 'توافق':
                if not CompatibilityGame:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="اللعبة غير متوفرة",
                            quick_reply=get_quick_reply()
                        )
                    )
                    return
                
                with games_lock:
                    game = CompatibilityGame(line_bot_api)
                    active_games[game_id] = {
                        'game': game,
                        'type': 'توافق',
                        'created_at': datetime.now(),
                        'participants': {user_id},
                        'answered_users': set(),
                        'last_game': text,
                        'waiting_for_names': True
                    }
                
                response = game.start_game()
                if isinstance(response, FlexSendMessage):
                    line_bot_api.reply_message(event.reply_token, response)
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="لعبة التوافق\n\nاكتب اسمين مفصولين بمسافة\nمثال: أحمد فاطمة",
                            quick_reply=get_quick_reply()
                        )
                    )
                logger.info(f"بدأت لعبة توافق")
                return
            
            start_game(game_id, game_class, game_type, user_id, event)
            return
        
        # ═══════════════════════════════════════════════════════════
        # معالجة إجابات الألعاب
        # ═══════════════════════════════════════════════════════════
        if game_id in active_games:
            if not is_registered:
                return
            
            game_data = active_games[game_id]
            
            # معالجة لعبة التوافق
            if game_data.get('type') == 'توافق' and game_data.get('waiting_for_names'):
                cleaned_text = text.replace('@', '').strip()
                
                if '@' in text:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="اكتب الأسماء بدون @\nمثال: أحمد فاطمة",
                            quick_reply=get_quick_reply()
                        )
                    )
                    return
                
                names = cleaned_text.split()
                if len(names) < 2:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="يجب كتابة اسمين\nمثال: أحمد فاطمة",
                            quick_reply=get_quick_reply()
                        )
                    )
                    return
                
                game = game_data['game']
                try:
                    result = game.check_answer(f"{names[0]} {names[1]}", user_id, name)
                    
                    with games_lock:
                        if game_id in active_games:
                            del active_games[game_id]
                    
                    if result and result.get('response'):
                        line_bot_api.reply_message(event.reply_token, result['response'])
                    return
                except Exception as e:
                    logger.error(f"خطأ في لعبة التوافق: {e}")
                    return
            
            # باقي الألعاب
            if game_data['type'] != 'أسرع':
                if user_id in game_data.get('answered_users', set()):
                    return
            
            game = game_data['game']
            game_type = game_data['type']
            
            try:
                result = game.check_answer(text, user_id, name)
                if result:
                    if result.get('correct', False):
                        with games_lock:
                            if 'answered_users' not in game_data:
                                game_data['answered_users'] = set()
                            game_data['answered_users'].add(user_id)
                    
                    points = result.get('points', 0)
                    if game_type in NO_POINTS_GAMES:
                        points = 0
                    
                    if points != 0:
                        update_points(user_id, name, points, result.get('won', False), game_type)
                    
                    if result.get('next_question', False):
                        with games_lock:
                            game_data['answered_users'] = set()
                        next_q = game.next_question()
                        if next_q:
                            if isinstance(next_q, TextSendMessage):
                                next_q.quick_reply = get_quick_reply()
                            line_bot_api.reply_message(event.reply_token, next_q)
                        return
                    
                    if result.get('game_over', False):
                        with games_lock:
                            if game_id in active_games:
                                del active_games[game_id]
                        
                        response = result.get('response', TextSendMessage(
                            text=result.get('message', '')))
                        if isinstance(response, TextSendMessage):
                            response.quick_reply = get_quick_reply()
                        line_bot_api.reply_message(event.reply_token, response)
                        return
                    
                    response = result.get('response', TextSendMessage(
                        text=result.get('message', '')))
                    if isinstance(response, TextSendMessage):
                        response.quick_reply = get_quick_reply()
                    elif isinstance(response, list):
                        for r in response:
                            if isinstance(r, TextSendMessage):
                                r.quick_reply = get_quick_reply()
                    line_bot_api.reply_message(event.reply_token, response)
                return
            except Exception as e:
                logger.error(f"خطأ في معالجة الإجابة: {e}")
    
    except Exception as e:
        logger.error(f"خطأ في معالجة الرسالة: {e}", exc_info=True)

# ═══════════════════════════════════════════════════════════════
# التنظيف التلقائي
# ═══════════════════════════════════════════════════════════════
def cleanup_task():
    """مهمة التنظيف التلقائي"""
    while True:
        try:
            time.sleep(CLEANUP_INTERVAL_SECONDS)
            now = datetime.now()
            
            # تنظيف الألعاب القديمة
            to_delete = []
            with games_lock:
                for gid, gdata in active_games.items():
                    age = now - gdata.get('created_at', now)
                    if age > timedelta(minutes=GAME_TIMEOUT_MINUTES):
                        to_delete.append(gid)
                
                for gid in to_delete:
                    del active_games[gid]
                
                if to_delete:
                    logger.info(f"تم حذف {len(to_delete)} لعبة قديمة")
            
            # تنظيف ذاكرة الأسماء
            with names_cache_lock:
                if len(user_names_cache) > NAMES_CACHE_MAX:
                    logger.info(f"تنظيف ذاكرة الأسماء ({len(user_names_cache)} عنصر)")
                    user_names_cache.clear()
            
            # تنظيف المستخدمين غير النشطين (كل 6 ساعات)
            if now.hour % 6 == 0 and now.minute < 5:
                cleanup_inactive_users()
        
        except Exception as e:
            logger.error(f"خطأ في مهمة التنظيف: {e}")

# بدء خيط التنظيف
cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
cleanup_thread.start()

# ═══════════════════════════════════════════════════════════════
# معالج الأخطاء
# ═══════════════════════════════════════════════════════════════
@app.errorhandler(404)
def not_found(error):
    """معالج خطأ 404"""
    return {"error": "الصفحة غير موجودة"}, 404

@app.errorhandler(500)
def internal_error(error):
    """معالج خطأ 500"""
    logger.error(f"خطأ داخلي في الخادم: {error}")
    return {"error": "خطأ داخلي في الخادم"}, 500

@app.errorhandler(Exception)
def handle_exception(error):
    """معالج الأخطاء العام"""
    logger.error(f"خطأ غير متوقع: {error}", exc_info=True)
    return 'OK', 200

# ═══════════════════════════════════════════════════════════════
# التشغيل
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    
    # طباعة معلومات النظام
    print("\n" + "="*60)
    print("بوت الحوت - نظام ألعاب تفاعلية")
    print("="*60)
    print(f"المنفذ: {port}")
    print(f"Gemini AI: {'مفعّل' if USE_AI else 'معطّل'}")
    
    games_count = sum([
        1 for g in [
            SongGame, HumanAnimalPlantGame, ChainWordsGame, 
            FastTypingGame, OppositeGame, LettersWordsGame, 
            DifferencesGame, CompatibilityGame
        ] if g
    ])
    print(f"الألعاب المتوفرة: {games_count}/8")
    
    print(f"قاعدة البيانات: {'متصلة' if get_db() else 'غير متصلة'}")
    print(f"LINE Bot: {'جاهز' if line_bot_api and handler else 'غير مهيأ'}")
    print("="*60 + "\n")
    
    # التحقق من المتطلبات الأساسية
    if not LINE_TOKEN or not LINE_SECRET:
        logger.critical("متغيرات LINE غير موجودة")
        print("تحذير: يجب تعيين LINE_CHANNEL_ACCESS_TOKEN و LINE_CHANNEL_SECRET")
    
    if not games_count:
        logger.warning("لا توجد ألعاب متوفرة")
    
    # تشغيل الخادم
    try:
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            threaded=True,
            use_reloader=False
        )
    except Exception as e:
        logger.critical(f"فشل في تشغيل الخادم: {e}")
        sys.exit(1)
