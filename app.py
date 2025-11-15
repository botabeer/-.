"""
بوت الحوت - نظام ألعاب تفاعلية على LINE
نسخة محسّنة ونظيفة مع معالجة أفضل للأخطاء وتنظيم الكود
"""

# ═══════════════════════════════════════════════════════════════
# المكتبات المطلوبة
# ═══════════════════════════════════════════════════════════════
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
# إعدادات Logging
# ═══════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("game-bot")

# ═══════════════════════════════════════════════════════════════
# الثوابت والإعدادات
# ═══════════════════════════════════════════════════════════════
# إعدادات LINE و Gemini
LINE_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
LINE_SECRET = os.getenv('LINE_CHANNEL_SECRET', '')
GEMINI_KEYS = [
    os.getenv('GEMINI_API_KEY_1', ''),
    os.getenv('GEMINI_API_KEY_2', '')
]
GEMINI_KEYS = [k for k in GEMINI_KEYS if k]

# إعدادات النظام
RATE_LIMIT = {'max': 30, 'window': 60}
DB_NAME = 'game_bot.db'
INACTIVE_DAYS = 45
GAME_TIMEOUT_MINUTES = 15
CLEANUP_INTERVAL_SECONDS = 300
NAMES_CACHE_MAX = 1000

# نظام الألوان (iOS Style)
THEME = {
    'primary': '#1C1C1E',
    'text': '#1C1C1E',
    'text_light': '#8E8E93',
    'surface': '#F2F2F7',
    'white': '#FFFFFF'
}

# الألعاب التي لا تحسب نقاط
NO_POINTS_GAMES = ['اختلاف', 'توافق', 'سؤال', 'اعتراف', 'تحدي', 'منشن']

# ═══════════════════════════════════════════════════════════════
# قاعدة البيانات
# ═══════════════════════════════════════════════════════════════
def get_db_connection():
    """إنشاء اتصال بقاعدة البيانات"""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """تهيئة قاعدة البيانات"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # جدول اللاعبين
        c.execute('''
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
        c.execute('''
            CREATE TABLE IF NOT EXISTS game_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                game_type TEXT NOT NULL,
                points INTEGER DEFAULT 0,
                won INTEGER DEFAULT 0,
                played_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES players(user_id)
            )
        ''')
        
        # الفهارس لتحسين الأداء
        c.execute('CREATE INDEX IF NOT EXISTS idx_players_points ON players(total_points DESC)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_last_active ON players(last_active)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_game_history_user ON game_history(user_id)')
        
        conn.commit()
        conn.close()
        logger.info("✅ قاعدة البيانات جاهزة")
        return True
    except Exception as e:
        logger.error(f"❌ خطأ في تهيئة قاعدة البيانات: {e}")
        return False

# ═══════════════════════════════════════════════════════════════
# دوال مساعدة
# ═══════════════════════════════════════════════════════════════
def normalize_text(text):
    """تطبيع النص العربي للمقارنة"""
    if not text:
        return ""
    
    text = text.strip().lower()
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    text = text.replace('ؤ', 'و').replace('ئ', 'ي').replace('ء', '')
    text = text.replace('ة', 'ه').replace('ى', 'ي')
    text = re.sub(r'[\u064B-\u065F]', '', text)
    text = re.sub(r'\s+', '', text)
    
    return text

def load_file(filename):
    """تحميل ملف نصي من مجلد games"""
    try:
        filepath = os.path.join('games', filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        logger.warning(f"⚠️ الملف غير موجود: {filename}")
        return []
    except Exception as e:
        logger.error(f"❌ خطأ في تحميل {filename}: {e}")
        return []

# ═══════════════════════════════════════════════════════════════
# إدارة المستخدمين
# ═══════════════════════════════════════════════════════════════
def update_user_activity(user_id, display_name):
    """تحديث آخر نشاط للمستخدم"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        now = datetime.now().isoformat()
        
        c.execute('SELECT user_id FROM players WHERE user_id = ?', (user_id,))
        exists = c.fetchone()
        
        if exists:
            c.execute(
                'UPDATE players SET last_active = ?, display_name = ? WHERE user_id = ?',
                (now, display_name, user_id)
            )
        else:
            c.execute(
                'INSERT INTO players (user_id, display_name, last_active) VALUES (?, ?, ?)',
                (user_id, display_name, now)
            )
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ خطأ في تحديث النشاط: {e}")
        return False

def update_points(user_id, display_name, points, won=False, game_type=''):
    """تحديث نقاط اللاعب"""
    if game_type in NO_POINTS_GAMES:
        points = 0
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        now = datetime.now().isoformat()
        
        c.execute('SELECT * FROM players WHERE user_id = ?', (user_id,))
        user = c.fetchone()
        
        if user:
            new_points = user['total_points'] + points
            new_games = user['games_played'] + 1
            new_wins = user['wins'] + (1 if won else 0)
            
            c.execute('''
                UPDATE players 
                SET total_points = ?, games_played = ?, wins = ?, 
                    last_active = ?, display_name = ? 
                WHERE user_id = ?
            ''', (new_points, new_games, new_wins, now, display_name, user_id))
        else:
            c.execute('''
                INSERT INTO players (user_id, display_name, total_points, games_played, wins, last_active) 
                VALUES (?, ?, ?, 1, ?, ?)
            ''', (user_id, display_name, points, 1 if won else 0, now))
        
        if game_type and points > 0:
            c.execute(
                'INSERT INTO game_history (user_id, game_type, points, won) VALUES (?, ?, ?, ?)',
                (user_id, game_type, points, 1 if won else 0)
            )
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ خطأ في تحديث النقاط: {e}")
        return False

def get_stats(user_id):
    """جلب إحصائيات اللاعب"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM players WHERE user_id = ?', (user_id,))
        user = c.fetchone()
        conn.close()
        return dict(user) if user else None
    except Exception as e:
        logger.error(f"❌ خطأ في جلب الإحصائيات: {e}")
        return None

def get_leaderboard(limit=10):
    """جلب لوحة الصدارة"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            SELECT display_name, total_points, games_played, wins 
            FROM players 
            ORDER BY total_points DESC 
            LIMIT ?
        ''', (limit,))
        leaders = c.fetchall()
        conn.close()
        return [dict(l) for l in leaders]
    except Exception as e:
        logger.error(f"❌ خطأ في جلب الصدارة: {e}")
        return []

def cleanup_inactive_users():
    """حذف المستخدمين غير النشطين"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        cutoff_date = (datetime.now() - timedelta(days=INACTIVE_DAYS)).isoformat()
        
        c.execute('SELECT COUNT(*) FROM players WHERE last_active < ?', (cutoff_date,))
        count = c.fetchone()[0]
        
        if count > 0:
            c.execute('DELETE FROM players WHERE last_active < ?', (cutoff_date,))
            c.execute('DELETE FROM game_history WHERE user_id NOT IN (SELECT user_id FROM players)')
            conn.commit()
            logger.info(f"🗑️ تم حذف {count} مستخدم غير نشط")
        
        conn.close()
    except Exception as e:
        logger.error(f"❌ خطأ في تنظيف المستخدمين: {e}")

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
        logger.info(f"✅ Gemini AI - {len(GEMINI_KEYS)} مفاتيح")
        
        def ask_gemini(prompt, max_retries=2):
            """استدعاء Gemini AI مع إعادة المحاولة"""
            for attempt in range(max_retries):
                try:
                    response = model.generate_content(prompt)
                    return response.text.strip()
                except Exception as e:
                    logger.error(f"❌ Gemini خطأ (محاولة {attempt + 1}): {e}")
                    if attempt < max_retries - 1 and len(GEMINI_KEYS) > 1:
                        genai.configure(api_key=GEMINI_KEYS[(attempt + 1) % len(GEMINI_KEYS)])
            return None
except Exception as e:
    logger.warning(f"⚠️ Gemini غير متوفر: {e}")

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
    logger.info("✅ تم استيراد جميع الألعاب")
except Exception as e:
    logger.error(f"❌ خطأ في استيراد الألعاب: {e}")

# ═══════════════════════════════════════════════════════════════
# Flask و LINE Bot
# ═══════════════════════════════════════════════════════════════
app = Flask(__name__)
line_bot_api = LineBotApi(LINE_TOKEN)
handler = WebhookHandler(LINE_SECRET)

# البيانات المشتركة
active_games = {}
registered_players = set()
user_message_count = defaultdict(lambda: {'count': 0, 'reset_time': datetime.now()})
user_names_cache = {}

# Locks للأمان
games_lock = threading.Lock()
players_lock = threading.Lock()
names_cache_lock = threading.Lock()

# تهيئة قاعدة البيانات
init_db()

# تحميل الملفات
QUESTIONS = load_file('questions.txt')
CHALLENGES = load_file('challenges.txt')
CONFESSIONS = load_file('confessions.txt')
MENTIONS = load_file('more_questions.txt')

# ═══════════════════════════════════════════════════════════════
# دوال LINE Bot
# ═══════════════════════════════════════════════════════════════
def get_profile_safe(user_id):
    """جلب الاسم بشكل آمن مع معالجة الأخطاء"""
    # التحقق من الذاكرة المؤقتة
    with names_cache_lock:
        if user_id in user_names_cache:
            return user_names_cache[user_id]
    
    try:
        profile = line_bot_api.get_profile(user_id)
        display_name = profile.display_name.strip() if profile.display_name else f"لاعب_{user_id[-4:]}"
        
        with names_cache_lock:
            user_names_cache[user_id] = display_name
        
        return display_name
    
    except LineBotApiError as e:
        fallback_name = f"لاعب_{user_id[-4:]}"
        
        if e.status_code == 404:
            logger.warning(f"⚠️ ملف غير موجود (404): {user_id[-4:]}")
        else:
            logger.error(f"❌ خطأ LINE API ({e.status_code}): {e.message}")
        
        with names_cache_lock:
            user_names_cache[user_id] = fallback_name
        
        return fallback_name
    
    except Exception as e:
        fallback_name = f"لاعب_{user_id[-4:]}"
        logger.error(f"❌ خطأ غير متوقع: {e}")
        
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
# بطاقات Flex Message
# ═══════════════════════════════════════════════════════════════
def get_card(title, body_content, footer_buttons=None):
    """بطاقة أساسية محسّنة"""
    card = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [{
                        "type": "text",
                        "text": title,
                        "size": "xl",
                        "weight": "bold",
                        "color": THEME['white'],
                        "align": "center"
                    }],
                    "backgroundColor": THEME['primary'],
                    "cornerRadius": "16px",
                    "paddingAll": "20px"
                },
                *body_content
            ],
            "backgroundColor": THEME['white'],
            "paddingAll": "24px",
            "spacing": "md"
        }
    }
    
    if footer_buttons:
        valid_buttons = [btn for btn in footer_buttons if btn is not None]
        if valid_buttons:
            card["footer"] = {
                "type": "box",
                "layout": "horizontal",
                "contents": valid_buttons,
                "spacing": "sm",
                "backgroundColor": THEME['surface'],
                "paddingAll": "16px"
            }
    
    return card

def get_welcome_card(name):
    """بطاقة الترحيب"""
    return get_card("مرحباً بك", [
        {
            "type": "text",
            "text": name,
            "size": "lg",
            "weight": "bold",
            "color": THEME['text'],
            "align": "center",
            "margin": "lg"
        },
        {
            "type": "text",
            "text": "اختر من الأزرار أدناه",
            "size": "sm",
            "color": THEME['text_light'],
            "align": "center",
            "margin": "md",
            "wrap": True
        }
    ], [
        {
            "type": "button",
            "action": {"type": "message", "label": "انضم", "text": "انضم"},
            "style": "primary",
            "color": THEME['primary'],
            "height": "sm",
            "flex": 1
        },
        {
            "type": "button",
            "action": {"type": "message", "label": "المساعدة", "text": "مساعدة"},
            "style": "secondary",
            "height": "sm",
            "flex": 1
        }
    ])

def get_help_card():
    """بطاقة المساعدة"""
    return get_card("المساعدة", [
        {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "الأوامر الأساسية",
                    "size": "md",
                    "weight": "bold",
                    "color": THEME['text'],
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "انضم - التسجيل\nانسحب - الإلغاء\nنقاطي - الإحصائيات\nالصدارة - الترتيب\nإيقاف - إنهاء اللعبة",
                    "size": "xs",
                    "color": THEME['text_light'],
                    "wrap": True,
                    "margin": "sm"
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
                    "text": "لمح - تلميح (-1 نقطة)\nجاوب - الحل (0 نقاط)",
                    "size": "xs",
                    "color": THEME['text_light'],
                    "wrap": True,
                    "margin": "sm"
                },
                {
                    "type": "text",
                    "text": "بوت الحوت",
                    "size": "xs",
                    "color": THEME['text_light'],
                    "align": "center",
                    "margin": "xl"
                }
            ],
            "backgroundColor": THEME['surface'],
            "cornerRadius": "12px",
            "paddingAll": "16px",
            "margin": "lg"
        }
    ], [
        {
            "type": "button",
            "action": {"type": "message", "label": "نقاطي", "text": "نقاطي"},
            "style": "primary",
            "color": THEME['primary'],
            "height": "sm",
            "flex": 1
        },
        {
            "type": "button",
            "action": {"type": "message", "label": "الصدارة", "text": "الصدارة"},
            "style": "secondary",
            "height": "sm",
            "flex": 1
        }
    ])

def get_registration_card(name):
    """بطاقة التسجيل"""
    return get_card("تم التسجيل", [
        {
            "type": "text",
            "text": name,
            "size": "lg",
            "weight": "bold",
            "color": THEME['text'],
            "align": "center",
            "margin": "lg"
        },
        {
            "type": "text",
            "text": "يمكنك الآن اللعب وجمع النقاط",
            "size": "sm",
            "color": THEME['text_light'],
            "align": "center",
            "margin": "md",
            "wrap": True
        }
    ], [
        {
            "type": "button",
            "action": {"type": "message", "label": "ابدأ اللعب", "text": "أغنية"},
            "style": "primary",
            "color": THEME['primary'],
            "height": "sm"
        }
    ])

def get_withdrawal_card(name):
    """بطاقة الانسحاب"""
    return get_card("تم الانسحاب", [
        {
            "type": "text",
            "text": name,
            "size": "lg",
            "weight": "bold",
            "color": THEME['text_light'],
            "align": "center",
            "margin": "lg"
        },
        {
            "type": "text",
            "text": "نتمنى رؤيتك مرة أخرى",
            "size": "sm",
            "color": THEME['text_light'],
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
    status_color = THEME['primary'] if is_registered else THEME['text_light']
    
    if not stats:
        footer = [{
            "type": "button",
            "action": {"type": "message", "label": "ابدأ الآن", "text": "انضم"},
            "style": "primary",
            "color": THEME['primary']
        }] if not is_registered else None
        
        return get_card("إحصائياتك", [
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
                        "weight": "bold",
                        "color": status_color,
                        "align": "center",
                        "margin": "sm"
                    }
                ],
                "margin": "sm"
            },
            {
                "type": "text",
                "text": "لم تبدأ بعد" if is_registered else "يجب التسجيل أولاً",
                "size": "md",
                "color": THEME['text_light'],
                "align": "center",
                "margin": "lg"
            }
        ], footer)
    
    win_rate = (stats['wins'] / stats['games_played'] * 100) if stats['games_played'] > 0 else 0
    
    footer_buttons = [
        {
            "type": "button",
            "action": {"type": "message", "label": "الصدارة", "text": "الصدارة"},
            "style": "secondary",
            "height": "sm",
            "flex": 1
        }
    ]
    
    if is_registered:
        footer_buttons.append({
            "type": "button",
            "action": {"type": "message", "label": "انسحب", "text": "انسحب"},
            "style": "secondary",
            "height": "sm",
            "flex": 1
        })
    
    return get_card("إحصائياتك", [
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
                    "weight": "bold",
                    "color": status_color,
                    "align": "center",
                    "margin": "sm"
                }
            ],
            "margin": "sm"
        },
        {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "النقاط", "size": "sm", "color": THEME['text_light'], "flex": 1},
                        {"type": "text", "text": str(stats['total_points']), "size": "xxl", "weight": "bold", "color": THEME['text'], "flex": 1, "align": "end"}
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "الألعاب", "size": "sm", "color": THEME['text_light'], "flex": 1},
                        {"type": "text", "text": str(stats['games_played']), "size": "md", "weight":
