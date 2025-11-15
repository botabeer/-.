from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    FlexSendMessage
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("game-bot")

# إعداد Gemini AI
USE_AI = False
ask_gemini = None

try:
    import google.generativeai as genai
    GEMINI_API_KEYS = [
        os.getenv('GEMINI_API_KEY_1', ''),
        os.getenv('GEMINI_API_KEY_2', ''),
        os.getenv('GEMINI_API_KEY_3', '')
    ]
    GEMINI_API_KEYS = [key for key in GEMINI_API_KEYS if key]
    current_gemini_key_index = 0
    USE_AI = bool(GEMINI_API_KEYS)
    
    if USE_AI:
        genai.configure(api_key=GEMINI_API_KEYS[0])
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info(f"Gemini AI جاهز - {len(GEMINI_API_KEYS)} مفاتيح")
        
        def ask_gemini(prompt, max_retries=2):
            for attempt in range(max_retries):
                try:
                    response = model.generate_content(prompt)
                    return response.text.strip()
                except Exception as e:
                    logger.error(f"خطأ في Gemini (محاولة {attempt + 1}): {e}")
                    if attempt < max_retries - 1 and len(GEMINI_API_KEYS) > 1:
                        global current_gemini_key_index
                        current_gemini_key_index = (current_gemini_key_index + 1) % len(GEMINI_API_KEYS)
                        genai.configure(api_key=GEMINI_API_KEYS[current_gemini_key_index])
            return None
except Exception as e:
    USE_AI = False
    logger.warning(f"Gemini AI غير متوفر: {e}")

# استيراد الألعاب
SongGame = None
HumanAnimalPlantGame = None
ChainWordsGame = None
FastTypingGame = None
OppositeGame = None
LettersWordsGame = None
DifferencesGame = None
CompatibilityGame = None

try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'games'))
    
    try:
        from song_game import SongGame
        logger.info("تم استيراد SongGame")
    except Exception as e:
        logger.warning(f"لم يتم استيراد SongGame: {e}")
    
    try:
        from human_animal_plant_game import HumanAnimalPlantGame
        logger.info("تم استيراد HumanAnimalPlantGame")
    except Exception as e:
        logger.warning(f"لم يتم استيراد HumanAnimalPlantGame: {e}")
    
    try:
        from chain_words_game import ChainWordsGame
        logger.info("تم استيراد ChainWordsGame")
    except Exception as e:
        logger.warning(f"لم يتم استيراد ChainWordsGame: {e}")
    
    try:
        from fast_typing_game import FastTypingGame
        logger.info("تم استيراد FastTypingGame")
    except Exception as e:
        logger.warning(f"لم يتم استيراد FastTypingGame: {e}")
    
    try:
        from opposite_game import OppositeGame
        logger.info("تم استيراد OppositeGame")
    except Exception as e:
        logger.warning(f"لم يتم استيراد OppositeGame: {e}")
    
    try:
        from letters_words_game import LettersWordsGame
        logger.info("تم استيراد LettersWordsGame")
    except Exception as e:
        logger.warning(f"لم يتم استيراد LettersWordsGame: {e}")
    
    try:
        from differences_game import DifferencesGame
        logger.info("تم استيراد DifferencesGame")
    except Exception as e:
        logger.warning(f"لم يتم استيراد DifferencesGame: {e}")
    
    try:
        from compatibility_game import CompatibilityGame
        logger.info("تم استيراد CompatibilityGame")
    except Exception as e:
        logger.warning(f"لم يتم استيراد CompatibilityGame: {e}")
        
except Exception as e:
    logger.error(f"خطأ في استيراد الألعاب: {e}")

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'YOUR_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', 'YOUR_CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

active_games = {}
registered_players = set()
user_message_count = defaultdict(lambda: {'count': 0, 'reset_time': datetime.now()})
user_names_cache = {}
error_log = []

games_lock = threading.Lock()
players_lock = threading.Lock()
names_cache_lock = threading.Lock()
error_log_lock = threading.Lock()

DB_NAME = 'game_scores.db'
INACTIVE_DAYS = 45  # حذف المستخدمين غير النشطين بعد 45 يوم

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

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (user_id TEXT PRIMARY KEY, display_name TEXT,
                      total_points INTEGER DEFAULT 0, games_played INTEGER DEFAULT 0,
                      wins INTEGER DEFAULT 0, last_active TEXT,
                      registered_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS game_history
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT,
                      game_type TEXT, points INTEGER, won INTEGER,
                      played_at TEXT DEFAULT CURRENT_TIMESTAMP,
                      FOREIGN KEY (user_id) REFERENCES users(user_id))''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_user_points ON users(total_points DESC)''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_last_active ON users(last_active)''')
        conn.commit()
        conn.close()
        logger.info("قاعدة البيانات جاهزة")
    except Exception as e:
        logger.error(f"خطأ قاعدة البيانات: {e}")

init_db()

def update_user_activity(user_id, display_name):
    """تحديث نشاط المستخدم"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        now = datetime.now().isoformat()
        
        c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = c.fetchone()
        
        if user:
            c.execute('UPDATE users SET last_active = ?, display_name = ? WHERE user_id = ?',
                     (now, display_name, user_id))
        else:
            c.execute('''INSERT INTO users (user_id, display_name, total_points, 
                         games_played, wins, last_active) VALUES (?, ?, 0, 0, 0, ?)''',
                     (user_id, display_name, now))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"خطأ في تحديث النشاط: {e}")
        return False

def cleanup_inactive_users():
    """حذف المستخدمين غير النشطين"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        cutoff_date = (datetime.now() - timedelta(days=INACTIVE_DAYS)).isoformat()
        
        c.execute('SELECT COUNT(*) FROM users WHERE last_active < ?', (cutoff_date,))
        count = c.fetchone()[0]
        
        if count > 0:
            c.execute('DELETE FROM users WHERE last_active < ?', (cutoff_date,))
            c.execute('DELETE FROM game_history WHERE user_id NOT IN (SELECT user_id FROM users)')
            conn.commit()
            logger.info(f"تم حذف {count} مستخدم غير نشط")
        
        conn.close()
    except Exception as e:
        logger.error(f"خطأ في تنظيف المستخدمين: {e}")

def update_user_points(user_id, display_name, points, won=False, game_type=""):
    """تحديث نقاط المستخدم - نظام النقاط الجديد"""
    # الألعاب التي لا تحسب نقاط
    no_points_games = ['اختلاف', 'توافق', 'سؤال', 'اعتراف', 'تحدي', 'منشن']
    
    if game_type in no_points_games:
        points = 0
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        now = datetime.now().isoformat()
        
        c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = c.fetchone()
        
        if user:
            c.execute('''UPDATE users SET total_points = ?, games_played = ?, wins = ?, 
                         last_active = ?, display_name = ? WHERE user_id = ?''',
                      (user['total_points'] + points, user['games_played'] + 1,
                       user['wins'] + (1 if won else 0), now,
                       display_name, user_id))
            
            if user['display_name'] != display_name:
                logger.info(f"تحديث اسم: {user['display_name']} → {display_name}")
        else:
            c.execute('''INSERT INTO users (user_id, display_name, total_points, 
                         games_played, wins, last_active) VALUES (?, ?, ?, ?, ?, ?)''',
                      (user_id, display_name, points, 1, 1 if won else 0, now))
            logger.info(f"إضافة مستخدم جديد: {display_name}")
        
        if game_type and points > 0:
            c.execute('''INSERT INTO game_history (user_id, game_type, points, won) 
                         VALUES (?, ?, ?, ?)''', (user_id, game_type, points, 1 if won else 0))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"خطأ تحديث النقاط: {e}")
        return False

def get_user_stats(user_id):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = c.fetchone()
        conn.close()
        return user
    except Exception as e:
        logger.error(f"خطأ إحصائيات: {e}")
        return None

def get_leaderboard(limit=10):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''SELECT display_name, total_points, games_played, wins 
                     FROM users ORDER BY total_points DESC LIMIT ?''', (limit,))
        leaders = c.fetchall()
        conn.close()
        return leaders
    except Exception as e:
        logger.error(f"خطأ الصدارة: {e}")
        return []

def check_rate_limit(user_id, max_messages=30, time_window=60):
    now = datetime.now()
    user_data = user_message_count[user_id]
    if now - user_data['reset_time'] > timedelta(seconds=time_window):
        user_data['count'] = 0
        user_data['reset_time'] = now
    if user_data['count'] >= max_messages:
        return False
    user_data['count'] += 1
    return True

def load_text_file(filename):
    try:
        filepath = os.path.join('games', filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        return []
    except Exception as e:
        logger.error(f"خطأ تحميل ملف {filename}: {e}")
        return []

QUESTIONS = load_text_file('questions.txt')
CHALLENGES = load_text_file('challenges.txt')
CONFESSIONS = load_text_file('confessions.txt')
MENTION_QUESTIONS = load_text_file('more_questions.txt')

def log_error(error_type, message, details=None):
    try:
        with error_log_lock:
            error_entry = {
                'timestamp': datetime.now().isoformat(),
                'type': error_type,
                'message': str(message),
                'details': details or {}
            }
            error_log.append(error_entry)
            if len(error_log) > 50:
                error_log.pop(0)
    except:
        pass

def get_user_profile_safe(user_id):
    """جلب اسم المستخدم بشكل آمن مع معالجة خطأ 404"""
    with names_cache_lock:
        if user_id in user_names_cache:
            cached_name = user_names_cache[user_id]
            if cached_name:
                return cached_name
    
    try:
        profile = line_bot_api.get_profile(user_id)
        display_name = profile.display_name
        
        if display_name and display_name.strip():
            display_name = display_name.strip()
            
            with names_cache_lock:
                user_names_cache[user_id] = display_name
            
            try:
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('SELECT display_name FROM users WHERE user_id = ?', (user_id,))
                result = c.fetchone()
                
                if result:
                    old_name = result['display_name']
                    if old_name != display_name:
                        c.execute('UPDATE users SET display_name = ? WHERE user_id = ?',
                                  (display_name, user_id))
                        conn.commit()
                        logger.info(f"تحديث اسم: {old_name} → {display_name}")
                else:
                    c.execute('''INSERT INTO users (user_id, display_name, total_points, 
                                 games_played, wins) VALUES (?, ?, 0, 0, 0)''',
                              (user_id, display_name))
                    conn.commit()
                    logger.info(f"حفظ اسم جديد: {display_name}")
                
                conn.close()
            except Exception as e:
                logger.error(f"خطأ في تحديث الاسم: {e}")
            
            return display_name
        
        fallback_name = f"لاعب_{user_id[-4:]}"
        with names_cache_lock:
            user_names_cache[user_id] = fallback_name
        return fallback_name
    
    except LineBotApiError as e:
        fallback_name = f"لاعب_{user_id[-4:] if user_id else 'xxxx'}"
        
        if e.status_code == 404:
            logger.warning(f"ملف مستخدم غير موجود (404): {user_id[-4:]}")
        else:
            logger.error(f"خطأ LINE API ({e.status_code}): {e.message}")
        
        with names_cache_lock:
            user_names_cache[user_id] = fallback_name
        
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
            if not c.fetchone():
                c.execute('''INSERT INTO users (user_id, display_name, total_points, 
                             games_played, wins) VALUES (?, ?, 0, 0, 0)''',
                          (user_id, fallback_name))
                conn.commit()
            conn.close()
        except:
            pass
        
        return fallback_name
    
    except Exception as e:
        fallback_name = f"لاعب_{user_id[-4:] if user_id else 'xxxx'}"
        logger.error(f"خطأ غير متوقع: {e}")
        
        with names_cache_lock:
            user_names_cache[user_id] = fallback_name
        
        return fallback_name

def get_simple_welcome_card(display_name):
    """بطاقة ترحيب بسيطة بأسلوب iOS"""
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "بوت الحُوت",
                    "size": "xl",
                    "weight": "bold",
                    "color": "#1C1C1E",
                    "align": "center"
                },
                {
                    "type": "text",
                    "text": "منصة ألعاب تفاعلية",
                    "size": "sm",
                    "color": "#8E8E93",
                    "align": "center",
                    "margin": "sm"
                },
                {
                    "type": "separator",
                    "margin": "xl",
                    "color": "#F2F2F7"
                },
                {
                    "type": "text",
                    "text": f"مرحباً {display_name}",
                    "size": "lg",
                    "weight": "bold",
                    "color": "#1C1C1E",
                    "align": "center",
                    "margin": "xl"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "ابدأ",
                            "size": "md",
                            "color": "#1C1C1E",
                            "weight": "bold",
                            "action": {"type": "message", "text": "انضم"}
                        }
                    ],
                    "backgroundColor": "#F2F2F7",
                    "cornerRadius": "12px",
                    "paddingAll": "16px",
                    "margin": "xl",
                    "action": {"type": "message", "text": "انضم"}
                }
            ],
            "backgroundColor": "#FFFFFF",
            "paddingAll": "24px",
            "spacing": "md"
        }
    }

def get_help_card():
    """بطاقة مساعدة محسّنة"""
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "المساعدة",
                    "size": "xl",
                    "weight": "bold",
                    "color": "#1C1C1E",
                    "align": "center"
                },
                {
                    "type": "separator",
                    "margin": "xl",
                    "color": "#F2F2F7"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "▫️ انضم - التسجيل في البوت\n▫️ انسحب - إلغاء التسجيل\n▫️ نقاطي - عرض إحصائياتك\n▫️ الصدارة - أفضل اللاعبين\n▫️ إيقاف - إنهاء اللعبة",
                            "size": "sm",
                            "color": "#1C1C1E",
                            "wrap": True
                        }
                    ],
                    "backgroundColor": "#F2F2F7",
                    "cornerRadius": "12px",
                    "paddingAll": "16px",
                    "margin": "xl"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "أثناء اللعب:",
                            "size": "md",
                            "weight": "bold",
                            "color": "#1C1C1E",
                            "margin": "xl"
                        },
                        {
                            "type": "text",
                            "text": "▫️ لمح - تلميح (-1 نقطة)\n▫️ جاوب - عرض الحل (0 نقاط)",
                            "size": "sm",
                            "color": "#1C1C1E",
                            "wrap": True,
                            "margin": "md"
                        }
                    ]
                }
            ],
            "backgroundColor": "#FFFFFF",
            "paddingAll": "24px"
        }
    }

def get_stats_card(user_id, display_name):
    """بطاقة إحصائيات محسّنة"""
    stats = get_user_stats(user_id)
    
    with players_lock:
        is_registered = user_id in registered_players
    
    if not stats:
        return {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "إحصائياتك",
                        "size": "xl",
                        "weight": "bold",
                        "color": "#1C1C1E",
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": display_name,
                        "size": "md",
                        "color": "#8E8E93",
                        "align": "center",
                        "margin": "sm"
                    },
                    {
                        "type": "separator",
                        "margin": "xl",
                        "color": "#F2F2F7"
                    },
                    {
                        "type": "text",
                        "text": "لم تبدأ بعد" if is_registered else "يجب التسجيل أولاً",
                        "size": "md",
                        "color": "#8E8E93",
                        "align": "center",
                        "margin": "xl"
                    }
                ],
                "backgroundColor": "#FFFFFF",
                "paddingAll": "24px"
            }
        }
    
    win_rate = (stats['wins'] / stats['games_played'] * 100) if stats['games_played'] > 0 else 0
    
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "إحصائياتك",
                    "size": "xl",
                    "weight": "bold",
                    "color": "#1C1C1E",
                    "align": "center"
                },
                {
                    "type": "text",
                    "text": display_name,
                    "size": "md",
                    "color": "#8E8E93",
                    "align": "center",
                    "margin": "sm"
                },
                {
                    "type": "separator",
                    "margin": "xl",
                    "color": "#F2F2F7"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "النقاط", "size": "sm", "color": "#8E8E93", "flex": 1},
                                {"type": "text", "text": str(stats['total_points']), "size": "xxl", "weight": "bold", "color": "#1C1C1E", "flex": 1, "align": "end"}
                            ]
                        },
                        {
                            "type": "separator",
                            "margin": "lg",
                            "color": "#F2F2F7"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "الألعاب", "size": "sm", "color": "#8E8E93", "flex": 1},
                                {"type": "text", "text": str(stats['games_played']), "size": "md", "weight": "bold", "color": "#1C1C1E", "flex": 1, "align": "end"}
                            ],
                            "margin": "lg"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "الفوز", "size": "sm", "color": "#8E8E93", "flex": 1},
                                {"type": "text", "text": str(stats['wins']), "size": "md", "weight": "bold", "color": "#1C1C1E", "flex": 1, "align": "end"}
                            ],
                            "margin": "md"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "معدل الفوز", "size": "sm", "color": "#8E8E93", "flex": 1},
                                {"type": "text", "text": f"{win_rate:.0f}%", "size": "md", "weight": "bold", "color": "#1C1C1E", "flex": 1, "align": "end"}
                            ],
                            "margin": "md"
                        }
                    ],
                    "backgroundColor": "#F2F2F7",
                    "cornerRadius": "12px",
                    "paddingAll": "16px",
                    "margin": "xl"
                }
            ],
            "backgroundColor": "#FFFFFF",
            "paddingAll": "24px"
        }
    }

def get_leaderboard_card():
    """لوحة صدارة محسّنة"""
    leaders = get_leaderboard()
    if not leaders:
        return {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🏆 لوحة الصدارة",
                        "size": "xl",
                        "weight": "bold",
                        "color": "#1C1C1E",
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": "لا توجد بيانات",
                        "size": "md",
                        "color": "#8E8E93",
                        "align": "center",
                        "margin": "xl"
                    }
                ],
                "backgroundColor": "#FFFFFF",
                "paddingAll": "24px"
            }
        }
    
    player_items = []
    for i, leader in enumerate(leaders, 1):
        if i == 1:
            rank_emoji = "🥇"
            bg_color = "#F2F2F7"
        elif i == 2:
            rank_emoji = "🥈"
            bg_color = "#FAFAFA"
        elif i == 3:
            rank_emoji = "🥉"
            bg_color = "#FAFAFA"
        else:
            rank_emoji = f"{i}"
            bg_color = "#FFFFFF"
        
        player_items.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": rank_emoji,
                    "size": "md",
                    "color": "#1C1C1E",
                    "flex": 0,
                    "weight": "bold"
                },
                {
                    "type": "text",
                    "text": leader['display_name'],
                    "size": "sm",
                    "color": "#1C1C1E",
                    "flex": 3,
                    "margin": "md",
                    "wrap": True
                },
                {
                    "type": "text",
                    "text": f"{leader['total_points']}",
                    "size": "md",
                    "color": "#1C1C1E",
                    "flex": 1,
                    "align": "end",
                    "weight": "bold"
                }
            ],
            "backgroundColor": bg_color,
            "cornerRadius": "12px",
            "paddingAll": "12px",
            "margin": "sm" if i > 1 else "none"
        })
    
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "🏆 لوحة الصدارة",
                    "size": "xl",
                    "weight": "bold",
                    "color": "#1C1C1E",
                    "align": "center"
                },
                {
                    "type": "text",
                    "text": "أفضل اللاعبين",
                    "size": "sm",
                    "color": "#8E8E93",
                    "align": "center",
                    "margin": "sm"
                },
                {
                    "type": "separator",
                    "margin": "xl",
                    "color": "#F2F2F7"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": player_items,
                    "margin": "xl"
                }
            ],
            "backgroundColor": "#FFFFFF",
            "paddingAll": "24px"
        }
    }

def start_game(game_id, game_class, game_type, user_id, event):
    if game_class is None:
        try:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"لعبة {game_type} غير متوفرة حالياً")
            )
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
                'answered_users': set()
            }
        
        response = game.start_game()
        line_bot_api.reply_message(event.reply_token, response)
        logger.info(f"بدأت لعبة {game_type} للمستخدم {user_id[-4:]}")
        return True
    except Exception as e:
        logger.error(f"خطأ بدء {game_type}: {e}")
        log_error('start_game', e, {'game_type': game_type, 'user_id': user_id[-4:]})
        try:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="حدث خطأ في بدء اللعبة")
            )
        except:
            pass
        return False

@app.route("/", methods=['GET'])
def home():
    games_status = []
    if SongGame: games_status.append("أغنية")
    if HumanAnimalPlantGame: games_status.append("لعبة")
    if ChainWordsGame: games_status.append("سلسلة")
    if FastTypingGame: games_status.append("أسرع")
    if OppositeGame: games_status.append("ضد")
    if LettersWordsGame: games_status.append("تكوين")
    if DifferencesGame: games_status.append("اختلاف")
    if CompatibilityGame: games_status.append("توافق")
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>بوت الحُوت</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta charset="utf-8">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
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
                border-radius: 16px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                padding: 40px;
                max-width: 500px;
                width: 100%;
            }}
            h1 {{ 
                color: #1C1C1E; 
                font-size: 2em; 
                margin-bottom: 10px; 
                text-align: center; 
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
                padding: 10px 0;
                border-bottom: 1px solid #E5E5E5;
            }}
            .status-item:last-child {{ border-bottom: none; }}
            .label {{ color: #8E8E93; }}
            .value {{ color: #1C1C1E; font-weight: 600; }}
            .games-list {{
                background: #FAFAFA;
                border-radius: 12px;
                padding: 12px;
                margin-top: 10px;
                font-size: 0.85em;
                color: #1C1C1E;
            }}
            .footer {{ 
                text-align: center; 
                margin-top: 20px; 
                color: #8E8E93; 
                font-size: 0.8em; 
            }}
            .btn {{
                display: inline-block;
                padding: 12px 24px;
                background: #1C1C1E;
                color: white;
                text-decoration: none;
                border-radius: 12px;
                margin: 5px;
                transition: all 0.3s;
                font-weight: 600;
            }}
            .btn:hover {{ 
                background: #3A3A3C;
                transform: translateY(-2px);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>بوت الحُوت</h1>
            <div class="status">
                <div class="status-item">
                    <span class="label">حالة الخادم</span>
                    <span class="value">يعمل</span>
                </div>
                <div class="status-item">
                    <span class="label">Gemini AI</span>
                    <span class="value">{'مُفعَّل' if USE_AI else 'مُعطَّل'}</span>
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
                    <span class="label">الألعاب المتوفرة</span>
                    <span class="value">{len(games_status)}/8</span>
                </div>
            </div>
            <div class="games-list">
                <strong>الألعاب الجاهزة:</strong><br>
                {', '.join(games_status) if games_status else 'لا توجدألعاب متوفرة'}
            </div>
            <div style="text-align: center; margin-top: 20px;">
                <a href="/errors" class="btn">
                    عرض الأخطاء ({len(error_log)})
                </a>
                <a href="/health" class="btn">
                    فحص الصحة
                </a>
            </div>
            <div class="footer">بوت الحُوت - منصة ألعاب تفاعلية</div>
        </div>
    </body>
    </html>
    """

@app.route("/errors", methods=['GET'])
def view_errors():
    with error_log_lock:
        errors = list(reversed(error_log))
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>سجل الأخطاء</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: #F2F2F7;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 16px;
                padding: 30px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            }
            h1 {
                color: #1C1C1E;
                margin-bottom: 20px;
                padding-bottom: 15px;
                border-bottom: 2px solid #F2F2F7;
            }
            .error-item {
                background: #F2F2F7;
                border-left: 4px solid #8E8E93;
                padding: 15px;
                margin: 15px 0;
                border-radius: 8px;
            }
            .error-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }
            .error-type {
                font-weight: bold;
                color: #1C1C1E;
            }
            .error-time {
                color: #8E8E93;
                font-size: 0.9em;
            }
            .error-message {
                color: #1C1C1E;
                margin: 10px 0;
                padding: 10px;
                background: white;
                border-radius: 8px;
                font-family: monospace;
                font-size: 0.9em;
            }
            .no-errors {
                text-align: center;
                padding: 40px;
                color: #8E8E93;
            }
            .back-link {
                display: inline-block;
                margin-top: 20px;
                color: white;
                text-decoration: none;
                padding: 12px 24px;
                background: #1C1C1E;
                border-radius: 12px;
            }
            .back-link:hover {
                background: #3A3A3C;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>سجل الأخطاء</h1>
    """
    
    if not errors:
        html += '<div class="no-errors">لا توجد أخطاء مسجلة</div>'
    else:
        for error in errors:
            html += f"""
            <div class="error-item">
                <div class="error-header">
                    <span class="error-type">{error.get('type', 'Unknown')}</span>
                    <span class="error-time">{error.get('timestamp', 'Unknown')}</span>
                </div>
                <div class="error-message">{error.get('message', 'No message')}</div>
            </div>
            """
    
    html += """
            <a href="/" class="back-link">العودة للرئيسية</a>
        </div>
    </body>
    </html>
    """
    
    return html

@app.route("/health", methods=['GET'])
def health_check():
    with error_log_lock:
        error_count = len(error_log)
        last_error = error_log[-1] if error_log else None
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_games": len(active_games),
        "registered_players": len(registered_players),
        "cached_names": len(user_names_cache),
        "error_count": error_count,
        "last_error": last_error.get('timestamp') if last_error else None,
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
    signature = request.headers.get('X-Line-Signature')
    if not signature:
        logger.warning("طلب بدون توقيع")
        abort(400)
    
    body = request.get_data(as_text=True)
    logger.info(f"استلام webhook - الطول: {len(body)} بايت")
    
    try:
        handler.handle(body, signature)
        logger.info("تم معالجة الحدث بنجاح")
    
    except InvalidSignatureError:
        logger.error("توقيع غير صالح")
        abort(400)
    
    except Exception as e:
        logger.error(f"خطأ في معالجة الحدث: {e}", exc_info=True)
        log_error('webhook', e, {'body_length': len(body)})
    
    return 'OK', 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = None
    text = None
    display_name = None
    game_id = None
    
    try:
        user_id = event.source.user_id
        text = event.message.text.strip() if event.message.text else ""
        
        if not user_id or not text:
            return
        
        if not check_rate_limit(user_id):
            return
        
        display_name = get_user_profile_safe(user_id)
        game_id = getattr(event.source, 'group_id', user_id)
        
        # تحديث نشاط المستخدم
        update_user_activity(user_id, display_name)
        
        logger.info(f"{display_name} ({user_id[-4:]}): {text[:50]}")
        
        with players_lock:
            is_registered = user_id in registered_players
        
        # الأوامر الأساسية (متاحة للجميع)
        if text in ['البداية', 'ابدأ', 'start', 'البوت']:
            line_bot_api.reply_message(event.reply_token,
                FlexSendMessage(alt_text=f"مرحباً {display_name}",
                    contents=get_simple_welcome_card(display_name)))
            return
        
        elif text in ['مساعدة', 'help']:
            line_bot_api.reply_message(event.reply_token,
                FlexSendMessage(alt_text="المساعدة", 
                    contents=get_help_card()))
            return
        
        elif text in ['انضم', 'تسجيل', 'join']:
            with players_lock:
                if user_id in registered_players:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text=f"أنت مسجل بالفعل يا {display_name}"))
                else:
                    registered_players.add(user_id)
                    with games_lock:
                        for gid, game_data in active_games.items():
                            if 'participants' not in game_data:
                                game_data['participants'] = set()
                            game_data['participants'].add(user_id)
                    
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text=f"✓ تم التسجيل\n\nمرحباً {display_name}\nيمكنك الآن اللعب وجمع النقاط"))
                    logger.info(f"انضم: {display_name}")
            return
        
        elif text in ['انسحب', 'خروج']:
            with players_lock:
                if user_id in registered_players:
                    registered_players.remove(user_id)
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text=f"تم الانسحاب\n\nنتمنى رؤيتك مرة أخرى يا {display_name}"))
                    logger.info(f"انسحب: {display_name}")
                else:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="أنت غير مسجل"))
            return
        
        # الأوامر المتاحة للجميع (مسجلين وغير مسجلين)
        if text in ['نقاطي', 'إحصائياتي', 'احصائياتي']:
            line_bot_api.reply_message(event.reply_token,
                FlexSendMessage(alt_text="إحصائياتك", 
                    contents=get_stats_card(user_id, display_name)))
            return
        
        elif text in ['الصدارة', 'المتصدرين']:
            line_bot_api.reply_message(event.reply_token,
                FlexSendMessage(alt_text="الصدارة", 
                    contents=get_leaderboard_card()))
            return
        
        # التحقق من التسجيل قبل اللعب
        if not is_registered:
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text=f"يجب التسجيل أولاً\nاكتب: انضم"))
            return
        
        # أوامر اللعبة (للمسجلين فقط)
        if text in ['إيقاف', 'stop', 'ايقاف']:
            with games_lock:
                if game_id in active_games:
                    game_type = active_games[game_id]['type']
                    del active_games[game_id]
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text=f"تم إيقاف لعبة {game_type}"))
                else:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="لا توجد لعبة نشطة"))
            return
        
        # الألعاب الترفيهية (بدون نقاط)
        elif text in ['سؤال', 'سوال']:
            if QUESTIONS:
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text=random.choice(QUESTIONS)))
            else:
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text="ملف الأسئلة غير متوفر"))
            return
        
        elif text in ['تحدي', 'challenge']:
            if CHALLENGES:
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text=random.choice(CHALLENGES)))
            else:
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text="ملف التحديات غير متوفر"))
            return
        
        elif text in ['اعتراف', 'confession']:
            if CONFESSIONS:
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text=random.choice(CONFESSIONS)))
            else:
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text="ملف الاعترافات غير متوفر"))
            return
        
        elif text in ['منشن', 'mention']:
            if MENTION_QUESTIONS:
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text=random.choice(MENTION_QUESTIONS)))
            else:
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text="ملف المنشن غير متوفر"))
            return
        
        # خريطة الألعاب
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
            game_class, game_type = games_map[text]
            
            # معالجة خاصة للعبة التوافق
            if text == 'توافق':
                if CompatibilityGame is None:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="لعبة التوافق غير متوفرة حالياً"))
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
                    TextSendMessage(text="▪️ لعبة التوافق\n\nاكتب اسمين مفصولين بمسافة\nنص فقط بدون رموز\n\nمثال: اسم اسم"))
                logger.info("بدأت لعبة توافق")
                return
            
            if game_id in active_games:
                active_games[game_id]['last_game'] = text
            
            start_game(game_id, game_class, game_type, user_id, event)
            return
        
        # معالجة إجابات لعبة التوافق
        if game_id in active_games:
            game_data = active_games[game_id]
            
            if game_data.get('type') == 'توافق' and game_data.get('waiting_for_names'):
                cleaned_text = text.replace('@', '').strip()
                
                if '@' in text:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="اكتب الأسماء بدون @\nمثال: اسم اسم"))
                    return
                
                names = cleaned_text.split()
                
                if len(names) < 2:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="يجب كتابة اسمين مفصولين بمسافة\nمثال: اسم اسم"))
                    return
                
                name1 = names[0].strip()
                name2 = names[1].strip()
                
                if not name1 or not name2:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="الأسماء يجب أن تكون نصوص صحيحة"))
                    return
                
                game = game_data['game']
                try:
                    result = game.check_answer(f"{name1} {name2}", user_id, display_name)
                    
                    with games_lock:
                        game_data['waiting_for_names'] = False
                        if game_id in active_games:
                            del active_games[game_id]
                    
                    if result and result.get('response'):
                        response = result['response']
                        # لا تحسب نقاط للعبة التوافق
                        line_bot_api.reply_message(event.reply_token, response)
                    return
                except Exception as e:
                    logger.error(f"خطأ في لعبة التوافق: {e}")
                    log_error('compatibility_game', e, {'user': user_id[-4:]})
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="حدث خطأ. حاول مرة أخرى بكتابة: توافق"))
                    return
        
        # معالجة إجابات الألعاب الأخرى
        if game_id in active_games:
            game_data = active_games[game_id]
            
            if 'answered_users' in game_data and user_id in game_data['answered_users']:
                return
            
            game = game_data['game']
            game_type = game_data['type']
            
            try:
                result = game.check_answer(text, user_id, display_name)
                if result:
                    with games_lock:
                        if result.get('correct', False):
                            if 'answered_users' not in game_data:
                                game_data['answered_users'] = set()
                            game_data['answered_users'].add(user_id)
                    
                    # حساب النقاط حسب النظام الجديد
                    points = result.get('points', 0)
                    
                    # الألعاب التي لا تحسب نقاط
                    if game_type in ['اختلاف', 'توافق']:
                        points = 0
                    
                    if points > 0:
                        update_user_points(user_id, display_name, points,
                            result.get('won', False), game_type)
                    
                    if result.get('next_question', False):
                        with games_lock:
                            game_data['answered_users'] = set()
                        next_q = game.next_question()
                        if next_q:
                            line_bot_api.reply_message(event.reply_token, next_q)
                        return
                    
                    if result.get('game_over', False):
                        with games_lock:
                            if game_id in active_games:
                                del active_games[game_id]
                        
                        if result.get('winner_card'):
                            winner_card = result['winner_card']
                            line_bot_api.reply_message(event.reply_token,
                                FlexSendMessage(alt_text="الفائز", 
                                    contents=winner_card))
                        else:
                            response = result.get('response', TextSendMessage(text=result.get('message', '')))
                            line_bot_api.reply_message(event.reply_token, response)
                        return
                    
                    response = result.get('response', TextSendMessage(text=result.get('message', '')))
                    line_bot_api.reply_message(event.reply_token, response)
                return
            except Exception as e:
                logger.error(f"خطأ معالجة إجابة: {e}")
                log_error('check_answer', e, {'user': user_id[-4:], 'game': game_type})
                return
    
    except Exception as e:
        logger.error(f"خطأ في handle_message: {e}", exc_info=True)
        
        error_details = {
            'user_id': user_id[-4:] if user_id else 'Unknown',
            'text': text[:100] if text else 'Unknown',
            'display_name': display_name if display_name else 'Unknown'
        }
        
        log_error('handle_message', e, error_details)
        
        try:
            if hasattr(event, 'reply_token') and event.reply_token:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="حدث خطأ مؤقت. حاول مرة أخرى")
                )
        except:
            pass

def cleanup_old_games():
    """تنظيف الألعاب القديمة والمستخدمين غير النشطين"""
    while True:
        try:
            time.sleep(300)  # كل 5 دقائق
            now = datetime.now()
            
            # حذف الألعاب القديمة
            to_delete = []
            with games_lock:
                for game_id, game_data in active_games.items():
                    if now - game_data.get('created_at', now) > timedelta(minutes=15):
                        to_delete.append(game_id)
                for game_id in to_delete:
                    del active_games[game_id]
                if to_delete:
                    logger.info(f"حذف {len(to_delete)} لعبة قديمة")
            
            # تنظيف ذاكرة الأسماء
            with names_cache_lock:
                if len(user_names_cache) > 1000:
                    logger.info(f"تنظيف ذاكرة الأسماء: {len(user_names_cache)} → 0")
                    user_names_cache.clear()
            
            # حذف المستخدمين غير النشطين كل 6 ساعات
            if now.hour % 6 == 0 and now.minute < 5:
                cleanup_inactive_users()
        
        except Exception as e:
            logger.error(f"خطأ التنظيف: {e}")

cleanup_thread = threading.Thread(target=cleanup_old_games, daemon=True)
cleanup_thread.start()

@app.errorhandler(InvalidSignatureError)
def handle_invalid_signature(error):
    logger.error(f"توقيع غير صالح: {error}")
    return 'Invalid Signature', 400

@app.errorhandler(400)
def bad_request(error):
    logger.warning(f"طلب غير صالح: {error}")
    return 'Bad Request', 400

@app.errorhandler(404)
def not_found(error):
    return 'Not Found', 404

@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f"خطأ غير متوقع: {error}", exc_info=True)
    if request.path == '/callback':
        return 'OK', 200
    return 'Internal Server Error', 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    logger.info("="*50)
    logger.info("بوت الألعاب - بدء التشغيل")
    logger.info(f"المنفذ: {port}")
    logger.info(f"Gemini AI: {'مُفعَّل' if USE_AI else 'مُعطَّل'}")
    logger.info(f"اللاعبون: {len(registered_players)}")
    logger.info(f"الألعاب: {len(active_games)}")
    
    games_loaded = []
    if SongGame: games_loaded.append("أغنية")
    if HumanAnimalPlantGame: games_loaded.append("لعبة")
    if ChainWordsGame: games_loaded.append("سلسلة")
    if FastTypingGame: games_loaded.append("أسرع")
    if OppositeGame: games_loaded.append("ضد")
    if LettersWordsGame: games_loaded.append("تكوين")
    if DifferencesGame: games_loaded.append("اختلاف")
    if CompatibilityGame: games_loaded.append("توافق")
    
    logger.info(f"الألعاب المتوفرة ({len(games_loaded)}/8): {', '.join(games_loaded)}")
    logger.info("="*50)
    
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
