from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, QuickReply, 
    QuickReplyButton, MessageAction, FlexSendMessage
)
import os
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import time
import random
import logging
import sys

# Logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("game-bot")

# استيراد الإعدادات
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'config'))
try:
    from config.settings import LINE_TOKEN, LINE_SECRET, GEMINI_KEYS, GEMINI_MODEL, COLORS, RATE_LIMIT
    from config.database import init_db, update_points, get_stats, get_leaderboard
    from config.helpers import normalize_text, load_file
except ImportError:
    # Fallback إذا لم تكن المجلدات موجودة
    LINE_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
    LINE_SECRET = os.getenv('LINE_CHANNEL_SECRET', '')
    GEMINI_KEYS = [os.getenv('GEMINI_API_KEY_1', ''), os.getenv('GEMINI_API_KEY_2', '')]
    GEMINI_KEYS = [k for k in GEMINI_KEYS if k]
    GEMINI_MODEL = 'gemini-2.0-flash-exp'
    COLORS = {}
    RATE_LIMIT = {'max': 30, 'window': 60}
    
    # تعريف الدوال البديلة
    import sqlite3
    import re
    
    DB_NAME = 'game_bot.db'
    INACTIVE_DAYS = 45
    
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
    
    def load_file(filename):
        try:
            filepath = os.path.join('games', filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return [line.strip() for line in f if line.strip()]
            return []
        except:
            return []
    
    def get_db_connection():
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db():
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS players
                         (user_id TEXT PRIMARY KEY, display_name TEXT,
                          total_points INTEGER DEFAULT 0, games_played INTEGER DEFAULT 0,
                          wins INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                          last_active TEXT DEFAULT CURRENT_TIMESTAMP)''')
            c.execute('''CREATE TABLE IF NOT EXISTS game_history
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT,
                          game_type TEXT, points INTEGER, won INTEGER,
                          played_at TEXT DEFAULT CURRENT_TIMESTAMP,
                          FOREIGN KEY (user_id) REFERENCES players(user_id))''')
            c.execute('''CREATE INDEX IF NOT EXISTS idx_players_points ON players(total_points DESC)''')
            c.execute('''CREATE INDEX IF NOT EXISTS idx_last_active ON players(last_active)''')
            conn.commit()
            conn.close()
            logger.info("✅ قاعدة البيانات جاهزة")
        except Exception as e:
            logger.error(f"❌ خطأ قاعدة البيانات: {e}")
    
    def update_points(user_id, display_name, points, won=False, game_type=''):
        # الألعاب التي لا تحسب نقاط
        no_points_games = ['اختلاف', 'توافق', 'سؤال', 'اعتراف', 'تحدي', 'منشن']
        if game_type in no_points_games:
            points = 0
        
        try:
            conn = get_db_connection()
            c = conn.cursor()
            now = datetime.now().isoformat()
            
            c.execute('SELECT * FROM players WHERE user_id = ?', (user_id,))
            user = c.fetchone()
            
            if user:
                c.execute('''UPDATE players SET total_points = ?, games_played = ?, wins = ?, 
                             last_active = ?, display_name = ? WHERE user_id = ?''',
                          (user['total_points'] + points, user['games_played'] + 1,
                           user['wins'] + (1 if won else 0), now, display_name, user_id))
            else:
                c.execute('''INSERT INTO players (user_id, display_name, total_points, 
                             games_played, wins, last_active) VALUES (?, ?, ?, ?, ?, ?)''',
                          (user_id, display_name, points, 1, 1 if won else 0, now))
            
            if game_type and points > 0:
                c.execute('''INSERT INTO game_history (user_id, game_type, points, won) 
                             VALUES (?, ?, ?, ?)''', (user_id, game_type, points, 1 if won else 0))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"❌ خطأ تحديث النقاط: {e}")
            return False
    
    def get_stats(user_id):
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT * FROM players WHERE user_id = ?', (user_id,))
            user = c.fetchone()
            conn.close()
            if user:
                return dict(user)
            return None
        except:
            return None
    
    def get_leaderboard(limit=10):
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('''SELECT display_name, total_points, games_played, wins 
                         FROM players ORDER BY total_points DESC LIMIT ?''', (limit,))
            leaders = c.fetchall()
            conn.close()
            return [dict(l) for l in leaders]
        except:
            return []
    
    def cleanup_inactive_users():
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

# Gemini AI
USE_AI = False
ask_gemini = None

try:
    import google.generativeai as genai
    if GEMINI_KEYS:
        genai.configure(api_key=GEMINI_KEYS[0])
        model = genai.GenerativeModel(GEMINI_MODEL)
        USE_AI = True
        logger.info(f"✅ Gemini AI - {len(GEMINI_KEYS)} مفاتيح")
        
        def ask_gemini(prompt, max_retries=2):
            for attempt in range(max_retries):
                try:
                    response = model.generate_content(prompt)
                    return response.text.strip()
                except Exception as e:
                    logger.error(f"❌ Gemini خطأ: {e}")
                    if attempt < max_retries - 1 and len(GEMINI_KEYS) > 1:
                        genai.configure(api_key=GEMINI_KEYS[(attempt + 1) % len(GEMINI_KEYS)])
            return None
except Exception as e:
    logger.warning(f"⚠️ Gemini غير متوفر: {e}")

# استيراد الألعاب
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
    logger.error(f"❌ خطأ استيراد: {e}")

app = Flask(__name__)
line_bot_api = LineBotApi(LINE_TOKEN)
handler = WebhookHandler(LINE_SECRET)

# البيانات
active_games = {}
registered_players = set()
user_message_count = defaultdict(lambda: {'count': 0, 'reset_time': datetime.now()})
user_names_cache = {}
error_log = []

games_lock = threading.Lock()
players_lock = threading.Lock()
names_cache_lock = threading.Lock()
error_log_lock = threading.Lock()

init_db()

# تحميل الملفات
QUESTIONS = load_file('questions.txt')
CHALLENGES = load_file('challenges.txt')
CONFESSIONS = load_file('confessions.txt')
MENTIONS = load_file('more_questions.txt')

# الألوان المحسّنة - iOS Style
THEME = {
    'primary': '#1C1C1E',      # أسود نصي iOS
    'secondary': '#8E8E93',    # رمادي نصي فاتح iOS
    'text': '#1C1C1E',         # نص داكن
    'text_light': '#8E8E93',   # نص فاتح
    'background': '#FFFFFF',   # خلفية بيضاء
    'surface': '#F2F2F7',      # سطح فاتح iOS
    'border': '#E0E0E0',       # حدود
    'success': '#1C1C1E',      # نجاح
    'white': '#FFFFFF'
}

def update_user_activity(user_id, display_name):
    """تحديث آخر نشاط للمستخدم"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        now = datetime.now().isoformat()
        
        c.execute('SELECT * FROM players WHERE user_id = ?', (user_id,))
        user = c.fetchone()
        
        if user:
            c.execute('UPDATE players SET last_active = ?, display_name = ? WHERE user_id = ?',
                     (now, display_name, user_id))
        else:
            c.execute('''INSERT INTO players (user_id, display_name, total_points, 
                         games_played, wins, last_active) VALUES (?, ?, 0, 0, 0, ?)''',
                     (user_id, display_name, now))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ خطأ في تحديث النشاط: {e}")
        return False

def get_profile_safe(user_id):
    """جلب الاسم بشكل آمن مع معالجة خطأ 404"""
    with names_cache_lock:
        if user_id in user_names_cache:
            return user_names_cache[user_id]
    
    try:
        profile = line_bot_api.get_profile(user_id)
        display_name = profile.display_name.strip() if profile.display_name else f"لاعب_{user_id[-4:]}"
        
        with names_cache_lock:
            user_names_cache[user_id] = display_name
        
        # تحديث في قاعدة البيانات
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT display_name FROM players WHERE user_id = ?', (user_id,))
            result = c.fetchone()
            
            if result and result['display_name'] != display_name:
                c.execute('UPDATE players SET display_name = ? WHERE user_id = ?',
                         (display_name, user_id))
                conn.commit()
                logger.info(f"🔄 تحديث اسم: {result['display_name']} → {display_name}")
            
            conn.close()
        except:
            pass
        
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
    """أزرار Quick Reply محسّنة"""
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="▪️ سؤال", text="سؤال")),
        QuickReplyButton(action=MessageAction(label="▪️ تحدي", text="تحدي")),
        QuickReplyButton(action=MessageAction(label="▪️ اعتراف", text="اعتراف")),
        QuickReplyButton(action=MessageAction(label="▪️ منشن", text="منشن")),
        QuickReplyButton(action=MessageAction(label="▫️ أغنية", text="أغنية")),
        QuickReplyButton(action=MessageAction(label="▫️ لعبة", text="لعبة")),
        QuickReplyButton(action=MessageAction(label="▫️ سلسلة", text="سلسلة")),
        QuickReplyButton(action=MessageAction(label="▫️ أسرع", text="أسرع")),
        QuickReplyButton(action=MessageAction(label="▫️ ضد", text="ضد")),
        QuickReplyButton(action=MessageAction(label="▫️ تكوين", text="تكوين")),
        QuickReplyButton(action=MessageAction(label="▫️ اختلاف", text="اختلاف")),
        QuickReplyButton(action=MessageAction(label="▫️ توافق", text="توافق"))
    ])

def get_card(title, body_content, footer_buttons=None, show_emoji=True):
    """بطاقة أساسية محسّنة بأسلوب iOS"""
    emoji = "▪️ " if show_emoji else ""
    card = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "box", "layout": "vertical", "contents": [
                    {"type": "text", "text": f"{emoji}{title}", "size": "xl", "weight": "bold", 
                     "color": THEME['white'], "align": "center"}
                ], "backgroundColor": THEME['primary'], "cornerRadius": "16px", "paddingAll": "20px"},
                {"type": "separator", "margin": "lg", "color": THEME['surface']},
                *body_content
            ],
            "backgroundColor": THEME['background'],
            "paddingAll": "24px",
            "spacing": "md"
        }
    }
    
    if footer_buttons:
        card["footer"] = {
            "type": "box",
            "layout": "horizontal",
            "contents": footer_buttons,
            "spacing": "sm",
            "backgroundColor": THEME['surface'],
            "paddingAll": "16px"
        }
    
    return card

def get_welcome_card(name):
    """بطاقة الترحيب"""
    return get_card("مرحباً بك", [
        {"type": "text", "text": name, "size": "lg", "weight": "bold", 
         "color": THEME['text'], "align": "center", "margin": "lg"},
        {"type": "separator", "margin": "lg", "color": THEME['surface']},
        {"type": "text", "text": "▫️ اختر من الأزرار أدناه", 
         "size": "sm", "color": THEME['text_light'], "align": "center", 
         "margin": "lg", "wrap": True}
    ], [
        {"type": "button", "action": {"type": "message", "label": "▪️ انضم", "text": "انضم"},
         "style": "primary", "color": THEME['primary'], "height": "sm", "flex": 1},
        {"type": "button", "action": {"type": "message", "label": "▫️ كيف ألعب", "text": "كيف ألعب"},
         "style": "secondary", "height": "sm", "flex": 1}
    ])

def get_help_card():
    """بطاقة المساعدة المحسّنة"""
    return get_card("المساعدة", [
        {"type": "box", "layout": "vertical", "contents": [
            {"type": "text", "text": "▪️ الأوامر الأساسية", "size": "md", "weight": "bold", 
             "color": THEME['text'], "margin": "md"},
            {"type": "text", "text": "▫️ انضم - التسجيل\n▫️ انسحب - الإلغاء\n▫️ نقاطي - الإحصائيات\n▫️ الصدارة - الترتيب\n▫️ إيقاف - إنهاء اللعبة", 
             "size": "xs", "color": THEME['text_light'], "wrap": True, "margin": "sm"},
            
            {"type": "separator", "margin": "lg", "color": THEME['border']},
            
            {"type": "text", "text": "▪️ أوامر اللعب", "size": "md", "weight": "bold", 
             "color": THEME['text'], "margin": "lg"},
            {"type": "text", "text": "▫️ لمح - تلميح (-1 نقطة)\n▫️ جاوب - الحل (0 نقاط)", 
             "size": "xs", "color": THEME['text_light'], "wrap": True, "margin": "sm"}
        ], "backgroundColor": THEME['surface'], "cornerRadius": "12px", "paddingAll": "16px", "margin": "lg"}
    ], [
        {"type": "button", "action": {"type": "message", "label": "▪️ نقاطي", "text": "نقاطي"},
         "style": "primary", "color": THEME['primary'], "height": "sm", "flex": 1},
        {"type": "button", "action": {"type": "message", "label": "▫️ الصدارة", "text": "الصدارة"},
         "style": "secondary", "height": "sm", "flex": 1}
    ])

def get_registration_card(name):
    """بطاقة التسجيل"""
    return get_card("تم التسجيل", [
        {"type": "text", "text": name, "size": "lg", "weight": "bold", 
         "color": THEME['text'], "align": "center", "margin": "lg"},
        {"type": "separator", "margin": "lg", "color": THEME['surface']},
        {"type": "text", "text": "▫️ يمكنك الآن اللعب وجمع النقاط", 
         "size": "sm", "color": THEME['text_light'], "align": "center", 
         "margin": "lg", "wrap": True}
    ], [
        {"type": "button", "action": {"type": "message", "label": "▪️ ابدأ اللعب", "text": "أغنية"},
         "style": "primary", "color": THEME['primary'], "height": "sm"}
    ])

def get_withdrawal_card(name):
    """بطاقة الانسحاب"""
    return get_card("تم الانسحاب", [
        {"type": "text", "text": name, "size": "lg", "weight": "bold", 
         "color": THEME['text_light'], "align": "center", "margin": "lg"},
        {"type": "separator", "margin": "lg", "color": THEME['surface']},
        {"type": "text", "text": "▫️ نتمنى رؤيتك مرة أخرى", 
         "size": "sm", "color": THEME['text_light'], "align": "center", "margin": "lg"}
    ])

def get_stats_card(user_id, name):
    """بطاقة الإحصائيات المحسّنة"""
    stats = get_stats(user_id)
    
    with players_lock:
        is_registered = user_id in registered_players
    
    status_text = "▪️ مسجل" if is_registered else "▫️ غير مسجل"
    status_color = THEME['success'] if is_registered else THEME['text_light']
    
    if not stats:
        return get_card("إحصائياتك", [
            {"type": "box", "layout": "vertical", "contents": [
                {"type": "text", "text": name, "size": "md", "color": THEME['text'], 
                 "align": "center", "weight": "bold"},
                {"type": "text", "text": status_text, "size": "xs", "weight": "bold",
                 "color": status_color, "align": "center", "margin": "sm"}
            ], "margin": "sm"},
            {"type": "separator", "margin": "lg", "color": THEME['surface']},
            {"type": "text", "text": "▫️ لم تبدأ بعد" if is_registered else "▫️ يجب التسجيل أولاً", 
             "size": "md", "color": THEME['text_light'], "align": "center", "margin": "lg"}
        ], [
            {"type": "button", "action": {"type": "message", "label": "▪️ ابدأ الآن", "text": "انضم"},
             "style": "primary", "color": THEME['primary']}
        ] if not is_registered else None)
    
    win_rate = (stats['wins'] / stats['games_played'] * 100) if stats['games_played'] > 0 else 0
    
    return get_card("إحصائياتك", [
        {"type": "box", "layout": "vertical", "contents": [
            {"type": "text", "text": name, "size": "md", "color": THEME['text'], 
             "align": "center", "weight": "bold"},
            {"type": "text", "text": status_text, "size": "xs", "weight": "bold",
             "color": status_color, "align": "center", "margin": "sm"}
        ], "margin": "sm"},
        {"type": "separator", "margin": "lg", "color": THEME['surface']},
        {"type": "box", "layout": "vertical", "contents": [
            {"type": "box", "layout": "horizontal", "contents": [
                {"type": "text", "text": "▪️ النقاط", "size": "sm", "color": THEME['text_light'], "flex": 1},
                {"type": "text", "text": str(stats['total_points']), "size": "xxl", 
                 "weight": "bold", "color": THEME['text'], "flex": 1, "align": "end"}
            ]},
            {"type": "separator", "margin": "lg", "color": THEME['border']},
            {"type": "box", "layout": "horizontal", "contents": [
                {"type": "text", "text": "▫️ الألعاب", "size": "sm", "color": THEME['text_light'], "flex": 1},
                {"type": "text", "text": str(stats['games_played']), "size": "md", 
                 "weight": "bold", "color": THEME['text'], "flex": 1, "align": "end"}
            ], "margin": "lg"},
            {"type": "box", "layout": "horizontal", "contents": [
                {"type": "text", "text": "▫️ الفوز", "size": "sm", "color": THEME['text_light'], "flex": 1},
                {"type": "text", "text": str(stats['wins']), "size": "md", 
                 "weight": "bold", "color": THEME['text'], "flex": 1, "align": "end"}
            ], "margin": "md"},
            {"type": "box", "layout": "horizontal", "contents": [
                {"type": "text", "text": "▫️ معدل الفوز", "size": "sm", "color": THEME['text_light'], "flex": 1},
                {"type": "text", "text": f"{win_rate:.0f}%", "size": "md", 
                 "weight": "bold", "color": THEME['text'], "flex": 1, "align": "end"}
            ], "margin": "md"}
        ], "backgroundColor": THEME['surface'], "cornerRadius": "12px", "paddingAll": "16px", "margin": "lg"}
    ], [
        {"type": "button", "action": {"type": "message", "label": "▪️ الصدارة", "text": "الصدارة"},
         "style": "secondary", "height": "sm", "flex": 1},
        {"type": "button", "action": {"type": "message", "label": "▫️ انسحب", "text": "انسحب"},
         "style": "secondary", "height": "sm", "flex": 1} if is_registered else None
    ])

def get_leaderboard_card():
    """بطاقة الصدارة محسّنة"""
    leaders = get_leaderboard()
    if not leaders:
        return get_card("لوحة الصدارة", [
            {"type": "text", "text": "▫️ لا توجد بيانات", "size": "md", 
             "color": THEME['text_light'], "align": "center", "margin": "xl"}
        ])
    
    items = []
    for i, l in enumerate(leaders, 1):
        if i == 1:
            bg = THEME['primary']
            tc = THEME['white']
            emoji = "🥇"
        elif i == 2:
            bg = THEME['secondary']
            tc = THEME['white']
            emoji = "🥈"
        elif i == 3:
            bg = THEME['text_light']
            tc = THEME['white']
            emoji = "🥉"
        else:
            bg = THEME['surface']
            tc = THEME['text']
            emoji = f"{i}"
        
        items.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": emoji, "size": "sm", "color": tc, "flex": 0, "weight": "bold"},
                {"type": "text", "text": l['display_name'], "size": "sm", "color": tc, 
                 "flex": 3, "margin": "md", "wrap": True},
                {"type": "text", "text": str(l['total_points']), "size": "sm", "color": tc, 
                 "flex": 1, "align": "end", "weight": "bold"}
            ],
            "backgroundColor": bg,
            "cornerRadius": "12px",
            "paddingAll": "12px",
            "margin": "sm" if i > 1 else "md"
        })
    
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "▪️ لوحة الصدارة", "size": "xl", "weight": "bold", 
                 "color": THEME['text'], "align": "center"},
                {"type": "text", "text": "▫️ أفضل اللاعبين", "size": "sm", 
                 "color": THEME['text_light'], "align": "center", "margin": "sm"},
                {"type": "separator", "margin": "lg", "color": THEME['surface']},
                {"type": "box", "layout": "vertical", "contents": items, "margin": "lg"}
            ],
            "backgroundColor": THEME['background'],
            "paddingAll": "24px"
        }
    }

def get_how_to_play_carousel():
    """بطاقات كاروسيل لشرح الألعاب"""
    games_info = [
        {
            "title": "لعبة الأغنية",
            "desc": "خمّن اسم المغني من كلمات الأغنية",
            "example": "الجواب 1: عمرو دياب\nالجواب 2: أم كلثوم",
            "command": "أغنية",
            "hint": "يدعم لمح وجاوب"
        },
        {
            "title": "إنسان حيوان نبات",
            "desc": "اكتب إنسان وحيوان ونبات وبلاد بحرف معين",
            "example": "الجواب 1: إنسان\nالجواب 2: حيوان",
            "command": "لعبة",
            "hint": "يدعم لمح وجاوب"
        },
        {
            "title": "سلسلة الكلمات",
            "desc": "اكتب كلمة تبدأ بآخر حرف من الكلمة السابقة",
            "example": "الجواب 1: قلم\nالجواب 2: ملك",
            "command": "سلسلة",
            "hint": "يدعم جاوب"
        },
        {
            "title": "الكتابة السريعة",
            "desc": "اكتب الكلمة بأسرع وقت ممكن",
            "example": "الجواب 1: سرعة\nالجواب 2: كتابة",
            "command": "أسرع",
            "hint": "لا يدعم لمح وجاوب"
        },
        {
            "title": "لعبة الأضداد",
            "desc": "اكتب عكس الكلمة المعطاة",
            "example": "الجواب 1: صغير\nالجواب 2: بارد",
            "command": "ضد",
            "hint": "يدعم لمح وجاوب"
        },
        {
            "title": "تكوين الكلمات",
            "desc": "كوّن 3 كلمات من 6 حروف",
            "example": "الجواب 1: قلم\nالجواب 2: عمر",
            "command": "تكوين",
            "hint": "يدعم جاوب"
        },
        {
            "title": "لعبة الاختلافات",
            "desc": "ابحث عن 5 اختلافات في الصورة",
            "example": "▫️ للتسلية فقط\n▫️ لا تحسب نقاط",
            "command": "اختلاف",
            "hint": "لا يدعم لمح - يدعم جاوب"
        },
        {
            "title": "لعبة التوافق",
            "desc": "اختبر نسبة التوافق بين اسمين",
            "example": "▫️ للتسلية فقط\n▫️ لا تحسب نقاط",
            "command": "توافق",
            "hint": "لا يدعم لمح وجاوب"
        }
    ]
    
    bubbles = []
    for game in games_info:
        bubble = {
            "type": "bubble",
            "size": "micro",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": f"▪️ {game['title']}", "size": "md", "weight": "bold", 
                     "color": THEME['text'], "align": "center", "wrap": True},
                    {"type": "separator", "margin": "md", "color": THEME['surface']},
                    {"type": "text", "text": game["desc"], "size": "xs", 
                     "color": THEME['text_light'], "align": "center", "margin": "md", "wrap": True},
                    {"type": "box", "layout": "vertical", "contents": [
                        {"type": "text", "text": "▫️ مثال:", "size": "xxs", 
                         "color": THEME['text_light'], "weight": "bold"},
                        {"type": "text", "text": game["example"], 
                         "size": "xxs", "color": THEME['text'], "margin": "xs", "wrap": True},
                        {"type": "separator", "margin": "sm", "color": THEME['border']},
                        {"type": "text", "text": f"▪️ الأمر: {game['command']}", 
                         "size": "xxs", "color": THEME['text_light'], "align": "center", "margin": "sm"},
                        {"type": "text", "text": f"▫️ {game['hint']}", 
                         "size": "xxs", "color": THEME['text_light'], "align": "center", "margin": "xs", "wrap": True}
                    ], "margin": "md", "backgroundColor": THEME['surface'], 
                     "cornerRadius": "8px", "paddingAll": "10px"}
                ],
                "paddingAll": "16px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "button", "action": {"type": "message", 
                     "label": "▪️ جرّب الآن", "text": game["command"]},
                     "style": "primary", "color": THEME['primary'], "height": "sm"}
                ],
                "paddingAll": "12px",
                "backgroundColor": THEME['surface']
            }
        }
        bubbles.append(bubble)
    
    return {"type": "carousel", "contents": bubbles}

def start_game(game_id, game_class, game_type, user_id, event):
    """بدء لعبة جديدة"""
    if not game_class:
        try:
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text=f"▫️ لعبة {game_type} غير متوفرة", quick_reply=get_quick_reply()))
        except:
            pass
        return False
    
    try:
        with games_lock:
            if game_class in [SongGame, HumanAnimalPlantGame, LettersWordsGame]:
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
                'last_game': game_type
            }
        
        response = game.start_game()
        if isinstance(response, TextSendMessage):
            response.quick_reply = get_quick_reply()
        elif isinstance(response, list):
            for r in response:
                if isinstance(r, TextSendMessage):
                    r.quick_reply = get_quick_reply()
        
        line_bot_api.reply_message(event.reply_token, response)
        logger.info(f"✅ بدأت {game_type}")
        return True
    except Exception as e:
        logger.error(f"❌ خطأ {game_type}: {e}")
        try:
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text="▫️ خطأ في بدء اللعبة", quick_reply=get_quick_reply()))
        except:
            pass
        return False

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
<html><head><title>بوت الحُوت</title><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#F2F2F7;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}.container{{background:#fff;border-radius:20px;box-shadow:0 4px 20px rgba(0,0,0,.08);padding:40px;max-width:500px;width:100%}}h1{{color:#1C1C1E;font-size:2em;margin-bottom:10px;text-align:center}}.status{{background:#F2F2F7;border-radius:12px;padding:20px;margin:20px 0}}.status-item{{display:flex;justify-content:space-between;padding:12px 0;border-bottom:1px solid #E0E0E0}}.status-item:last-child{{border-bottom:none}}.label{{color:#8E8E93;font-size:.9em}}.value{{color:#1C1C1E;font-weight:600}}.games-list{{background:#FAFAFA;border-radius:10px;padding:14px;margin-top:10px;font-size:.85em;color:#1C1C1E}}.footer{{text-align:center;margin-top:20px;color:#8E8E93;font-size:.8em}}</style>
</head><body><div class="container"><h1>▪️ بوت الحُوت</h1><div class="status">
<div class="status-item"><span class="label">▪️ الخادم</span><span class="value">يعمل ✓</span></div>
<div class="status-item"><span class="label">▫️ Gemini AI</span><span class="value">{'✅ مفعّل' if USE_AI else '⚠️ معطّل'}</span></div>
<div class="status-item"><span class="label">▪️ اللاعبون</span><span class="value">{len(registered_players)}</span></div>
<div class="status-item"><span class="label">▫️ ألعاب نشطة</span><span class="value">{len(active_games)}</span></div>
<div class="status-item"><span class="label">▪️ الألعاب المتوفرة</span><span class="value">{len(games_status)}/8</span></div>
</div><div class="games-list"><strong>▪️ جاهز:</strong> {', '.join(games_status) if games_status else 'لا توجد'}</div>
<div class="footer">▫️ بوت الحُوت © 2025</div></div></body></html>"""

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
        "games_loaded": {
            "song_game": SongGame is not None,
            "human_animal_plant": HumanAnimalPlantGame is not None,
            "chain_words": ChainWordsGame is not None,
            "fast_typing": FastTypingGame is not None,
            "opposite": OppositeGame is not None,
            "letters_words": LettersWordsGame is not None,
            "differences": DifferencesGame is not None,
            "compatibility": CompatibilityGame is not None
        }
    }, 200

@app.route("/callback", methods=['POST'])
def callback():
    """معالجة طلبات LINE"""
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("❌ توقيع غير صالح")
        abort(400)
    except Exception as e:
        logger.error(f"❌ خطأ webhook: {e}")
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """معالجة الرسائل"""
    try:
        user_id = event.source.user_id
        text = event.message.text.strip() if event.message.text else ""
        
        if not text:
            return
        
        if not check_rate(user_id):
            return
        
        name = get_profile_safe(user_id)
        game_id = event.source.group_id if hasattr(event.source, 'group_id') else user_id
        
        # تحديث النشاط
        update_user_activity(user_id, name)
        
        logger.info(f"📨 {name} ({user_id[-4:]}): {text[:50]}")
        
        # الأوامر الأساسية (متاحة للجميع)
        if text in ['البداية', 'ابدأ', 'start', 'البوت']:
            line_bot_api.reply_message(event.reply_token,
                FlexSendMessage(alt_text=f"مرحباً {name}",
                    contents=get_welcome_card(name), quick_reply=get_quick_reply()))
            return
        
        if text in ['كيف ألعب', 'الألعاب', 'شرح']:
            line_bot_api.reply_message(event.reply_token,
                FlexSendMessage(alt_text="دليل الألعاب",
                    contents=get_how_to_play_carousel(), quick_reply=get_quick_reply()))
            return
        
        if text in ['مساعدة', 'help']:
            line_bot_api.reply_message(event.reply_token,
                FlexSendMessage(alt_text="المساعدة",
                    contents=get_help_card(), quick_reply=get_quick_reply()))
            return
        
        if text in ['نقاطي', 'إحصائياتي', 'احصائياتي']:
            line_bot_api.reply_message(event.reply_token,
                FlexSendMessage(alt_text="إحصائياتك",
                    contents=get_stats_card(user_id, name), quick_reply=get_quick_reply()))
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
                        TextSendMessage(text=f"▪️ تم إيقاف {game_type}", quick_reply=get_quick_reply()))
                else:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="▫️ لا توجد لعبة", quick_reply=get_quick_reply()))
            return
        
        if text in ['انضم', 'تسجيل', 'join']:
            with players_lock:
                if user_id in registered_players:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text=f"▪️ أنت مسجل يا {name}", quick_reply=get_quick_reply()))
                else:
                    registered_players.add(user_id)
                    line_bot_api.reply_message(event.reply_token,
                        FlexSendMessage(alt_text="تم التسجيل",
                            contents=get_registration_card(name), quick_reply=get_quick_reply()))
                    logger.info(f"✅ انضم: {name}")
            return
        
        if text in ['انسحب', 'خروج']:
            with players_lock:
                if user_id in registered_players:
                    registered_players.remove(user_id)
                    line_bot_api.reply_message(event.reply_token,
                        FlexSendMessage(alt_text="تم الانسحاب",
                            contents=get_withdrawal_card(name), quick_reply=get_quick_reply()))
                    logger.info(f"❌ انسحب: {name}")
                else:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="▫️ غير مسجل", quick_reply=get_quick_reply()))
            return
        
        # التحقق من التسجيل قبل اللعب
        with players_lock:
            is_registered = user_id in registered_players
        
        # الأوامر النصية (للجميع)
        if text in ['سؤال', 'سوال'] and QUESTIONS:
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text=f"▪️ {random.choice(QUESTIONS)}", quick_reply=get_quick_reply()))
            return
        
        if text in ['تحدي', 'challenge'] and CHALLENGES:
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text=f"▪️ {random.choice(CHALLENGES)}", quick_reply=get_quick_reply()))
            return
        
        if text in ['اعتراف', 'confession'] and CONFESSIONS:
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text=f"▪️ {random.choice(CONFESSIONS)}", quick_reply=get_quick_reply()))
            return
        
        if text in ['منشن', 'mention'] and MENTIONS:
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text=f"▪️ {random.choice(MENTIONS)}", quick_reply=get_quick_reply()))
            return
        
        # بدء الألعاب (للمسجلين فقط)
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
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text="▫️ يجب التسجيل أولاً\n\nاكتب: انضم", 
                        quick_reply=get_quick_reply()))
                return
            
            game_class, game_type = games_map[text]
            
            # معالجة خاصة للعبة التوافق
            if text == 'توافق':
                if not CompatibilityGame:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="▫️ غير متوفرة", quick_reply=get_quick_reply()))
                    return
                
                with games_lock:
                    with players_lock:
                        participants = registered_players.copy()
                        participants.add(user_id)
                    game = CompatibilityGame(line_bot_api)
                    active_games[game_id] = {
                        'game': game,
                        'type': 'توافق',
                        'created_at': datetime.now(),
                        'participants': participants,
                        'answered_users': set(),
                        'last_game': text,
                        'waiting_for_names': True
                    }
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text="▪️ لعبة التوافق\n\n▫️ اكتب اسمين مفصولين بمسافة\n▫️ نص فقط بدون رموز\n\n▪️ مثال: اسم اسم",
                        quick_reply=get_quick_reply()))
                logger.info(f"✅ بدأت توافق")
                return
            
            start_game(game_id, game_class, game_type, user_id, event)
            return
        
        # معالجة إجابات الألعاب
        if game_id in active_games:
            game_data = active_games[game_id]
            
            # التحقق من التسجيل
            if not is_registered:
                return
            
            # معالجة خاصة للعبة التوافق
            if game_data.get('type') == 'توافق' and game_data.get('waiting_for_names'):
                cleaned_text = text.replace('@', '').strip()
                
                if '@' in text:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="▫️ اكتب الأسماء بدون @\n\n▪️ مثال: اسم اسم",
                            quick_reply=get_quick_reply()))
                    return
                
                names = cleaned_text.split()
                
                if len(names) < 2:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="▫️ يجب كتابة اسمين مفصولين بمسافة\n\n▪️ مثال: اسم اسم",
                            quick_reply=get_quick_reply()))
                    return
                
                name1 = names[0].strip()
                name2 = names[1].strip()
                
                if not name1 or not name2:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="▫️ الأسماء يجب أن تكون صحيحة",
                            quick_reply=get_quick_reply()))
                    return
                
                game = game_data['game']
                try:
                    result = game.check_answer(f"{name1} {name2}", user_id, name)
                    
                    with games_lock:
                        game_data['waiting_for_names'] = False
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
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="▫️ حدث خطأ. حاول مرة أخرى: توافق",
                            quick_reply=get_quick_reply()))
                    return
            
            # تجاهل المستخدمين الذين أجابوا (إلا لعبة أسرع)
            if game_data['type'] != 'أسرع':
                if 'answered_users' in game_data and user_id in game_data['answered_users']:
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
                    
                    # حساب النقاط حسب نوع اللعبة
                    if game_type in ['اختلاف', 'توافق']:
                        points = 0
                    
                    if points > 0:
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
                            last_game = active_games[game_id].get('last_game', 'أغنية')
                            if game_id in active_games:
                                del active_games[game_id]
                        
                        if result.get('winner_card'):
                            card = result['winner_card']
                            line_bot_api.reply_message(event.reply_token,
                                FlexSendMessage(alt_text="الفائز", contents=card, quick_reply=get_quick_reply()))
                        else:
                            response = result.get('response', TextSendMessage(text=result.get('message', '')))
                            if isinstance(response, TextSendMessage):
                                response.quick_reply = get_quick_reply()
                            line_bot_api.reply_message(event.reply_token, response)
                        return
                    
                    response = result.get('response', TextSendMessage(text=result.get('message', '')))
                    if isinstance(response, TextSendMessage):
                        response.quick_reply = get_quick_reply()
                    elif isinstance(response, list):
                        for r in response:
                            if isinstance(r, TextSendMessage):
                                r.quick_reply = get_quick_reply()
                    line_bot_api.reply_message(event.reply_token, response)
                return
            except Exception as e:
                logger.error(f"❌ خطأ إجابة: {e}")
                return
    
    except Exception as e:
        logger.error(f"❌ خطأ معالجة: {e}", exc_info=True)
        try:
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text="▫️ حدث خطأ مؤقت", quick_reply=get_quick_reply()))
        except:
            pass

def cleanup_old():
    """تنظيف الألعاب القديمة والمستخدمين غير النشطين"""
    while True:
        try:
            time.sleep(300)  # كل 5 دقائق
            now = datetime.now()
            
            # حذف الألعاب القديمة
            to_delete = []
            with games_lock:
                for gid, gdata in active_games.items():
                    if now - gdata.get('created_at', now) > timedelta(minutes=15):
                        to_delete.append(gid)
                for gid in to_delete:
                    del active_games[gid]
                if to_delete:
                    logger.info(f"🗑️ حذف {len(to_delete)} لعبة قديمة")
            
            # تنظيف ذاكرة الأسماء
            with names_cache_lock:
                if len(user_names_cache) > 1000:
                    logger.info(f"🗑️ تنظيف ذاكرة الأسماء: {len(user_names_cache)} → 0")
                    user_names_cache.clear()
            
            # حذف المستخدمين غير النشطين كل 6 ساعات
            if now.hour % 6 == 0 and now.minute < 5:
                cleanup_inactive_users()
        
        except Exception as e:
            logger.error(f"❌ خطأ تنظيف: {e}")

# بدء مهمة التنظيف
threading.Thread(target=cleanup_old, daemon=True).start()

@app.errorhandler(InvalidSignatureError)
def handle_invalid_signature(error):
    logger.error(f"❌ توقيع غير صالح: {error}")
    return 'Invalid Signature', 400

@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f"❌ خطأ: {error}", exc_info=True)
    if request.path == '/callback':
        return 'OK', 200
    return 'Internal Server Error', 500

@app.errorhandler(404)
def not_found(error):
    return 'Not Found', 404

@app.errorhandler(400)
def bad_request(error):
    logger.warning(f"⚠️ طلب غير صالح: {error}")
    return 'Bad Request', 400

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    logger.info("="*50)
    logger.info("🚀 بوت الحُوت - النسخة المحسّنة")
    logger.info(f"📌 المنفذ: {port}")
    logger.info(f"🤖 Gemini AI: {'✅ مفعّل' if USE_AI else '⚠️ معطّل'}")
    logger.info(f"📊 اللاعبون المسجلون: {len(registered_players)}")
    logger.info(f"🎮 الألعاب النشطة: {len(active_games)}")
    
    games_loaded = []
    if SongGame: games_loaded.append("أغنية")
    if HumanAnimalPlantGame: games_loaded.append("لعبة")
    if ChainWordsGame: games_loaded.append("سلسلة")
    if FastTypingGame: games_loaded.append("أسرع")
    if OppositeGame: games_loaded.append("ضد")
    if LettersWordsGame: games_loaded.append("تكوين")
    if DifferencesGame: games_loaded.append("اختلاف")
    if CompatibilityGame: games_loaded.append("توافق")
    
    logger.info(f"🎯 الألعاب المتوفرة ({len(games_loaded)}/8): {', '.join(games_loaded)}")
    logger.info("="*50)
    
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
