import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("game-bot")

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction,
    FlexSendMessage, ImageSendMessage
)
import os
from datetime import datetime, timedelta
import sqlite3
from collections import defaultdict
import threading
import time
import json
import random
import re

# إعداد Gemini AI
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
        model = genai.GenerativeModel('gemini-pro')
        logger.info(f"✅ Gemini AI جاهز - {len(GEMINI_API_KEYS)} مفاتيح")
except Exception as e:
    USE_AI = False
    logger.error(f"❌ خطأ في تحميل Gemini: {e}")

def get_gemini_api_key():
    """الحصول على مفتاح Gemini API الحالي"""
    global current_gemini_key_index
    if GEMINI_API_KEYS:
        return GEMINI_API_KEYS[current_gemini_key_index]
    return None

def switch_gemini_key():
    """التبديل إلى المفتاح التالي"""
    global current_gemini_key_index, model
    if len(GEMINI_API_KEYS) > 1:
        current_gemini_key_index = (current_gemini_key_index + 1) % len(GEMINI_API_KEYS)
        genai.configure(api_key=GEMINI_API_KEYS[current_gemini_key_index])
        model = genai.GenerativeModel('gemini-pro')
        logger.info(f"تم التبديل إلى مفتاح Gemini رقم: {current_gemini_key_index + 1}")
        return True
    return False

def ask_gemini(prompt, max_retries=2):
    """سؤال Gemini AI مع إعادة المحاولة"""
    if not USE_AI:
        return None
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"خطأ في Gemini (محاولة {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                switch_gemini_key()
            else:
                return None
    return None

# استيراد الألعاب
try:
    from games.song_game import SongGame
    from games.human_animal_plant_game import HumanAnimalPlantGame
    from games.chain_words_game import ChainWordsGame
    from games.fast_typing_game import FastTypingGame
    from games.opposite_game import OppositeGame
    from games.letters_words_game import LettersWordsGame
    from games.differences_game import DifferencesGame
    from games.compatibility_game import CompatibilityGame
    logger.info("✅ تم استيراد الألعاب")
except Exception as e:
    logger.error(f"❌ خطأ استيراد الألعاب: {e}")

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'YOUR_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', 'YOUR_CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

active_games = {}
registered_players = set()
user_message_count = defaultdict(lambda: {'count': 0, 'reset_time': datetime.now()})

games_lock = threading.Lock()
players_lock = threading.Lock()

DB_NAME = 'game_scores.db'

def normalize_text(text):
    """تطبيع النص لقبول جميع أشكال الحروف"""
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
                      wins INTEGER DEFAULT 0, last_played TEXT,
                      registered_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS game_history
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT,
                      game_type TEXT, points INTEGER, won INTEGER,
                      played_at TEXT DEFAULT CURRENT_TIMESTAMP,
                      FOREIGN KEY (user_id) REFERENCES users(user_id))''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_user_points ON users(total_points DESC)''')
        conn.commit()
        conn.close()
        logger.info("✅ قاعدة البيانات جاهزة")
    except Exception as e:
        logger.error(f"❌ خطأ قاعدة البيانات: {e}")

init_db()

def update_user_points(user_id, display_name, points, won=False, game_type=""):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = c.fetchone()
        
        if user:
            c.execute('''UPDATE users SET total_points = ?, games_played = ?, wins = ?, 
                         last_played = ?, display_name = ? WHERE user_id = ?''',
                      (user['total_points'] + points, user['games_played'] + 1,
                       user['wins'] + (1 if won else 0), datetime.now().isoformat(),
                       display_name, user_id))
        else:
            c.execute('''INSERT INTO users (user_id, display_name, total_points, 
                         games_played, wins, last_played) VALUES (?, ?, ?, ?, ?, ?)''',
                      (user_id, display_name, points, 1, 1 if won else 0, datetime.now().isoformat()))
        
        if game_type:
            c.execute('''INSERT INTO game_history (user_id, game_type, points, won) 
                         VALUES (?, ?, ?, ?)''', (user_id, game_type, points, 1 if won else 0))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ خطأ تحديث النقاط: {e}")
        return False

def get_user_stats(user_id):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = c.fetchone()
        conn.close()
        return user
    except:
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
    except:
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
    except:
        return []

QUESTIONS = load_text_file('questions.txt')
CHALLENGES = load_text_file('challenges.txt')
CONFESSIONS = load_text_file('confessions.txt')
MORE_QUESTIONS = load_text_file('more_questions.txt')

def get_user_profile_safe(user_id):
    try:
        profile = line_bot_api.get_profile(user_id)
        return profile.display_name
    except:
        return "مستخدم"

def get_quick_reply():
    """الأزرار الثابتة"""
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="▫️أغنية", text="أغنية")),
        QuickReplyButton(action=MessageAction(label="▫️لعبة", text="لعبة")),
        QuickReplyButton(action=MessageAction(label="▫️سلسلة", text="سلسلة")),
        QuickReplyButton(action=MessageAction(label="▫️أسرع", text="أسرع")),
        QuickReplyButton(action=MessageAction(label="▫️ضد", text="ضد")),
        QuickReplyButton(action=MessageAction(label="▫️تكوين", text="تكوين")),
        QuickReplyButton(action=MessageAction(label="▫️اختلاف", text="اختلاف")),
        QuickReplyButton(action=MessageAction(label="▫️توافق", text="توافق")),
        QuickReplyButton(action=MessageAction(label="▪️سؤال", text="سؤال")),
        QuickReplyButton(action=MessageAction(label="▪️تحدي", text="تحدي")),
        QuickReplyButton(action=MessageAction(label="▪️اعتراف", text="اعتراف")),
        QuickReplyButton(action=MessageAction(label="▪️اكثر", text="اكثر")),
        QuickReplyButton(action=MessageAction(label="▪️مساعدة", text="مساعدة"))
    ])

def get_help_card():
    """بطاقة المساعدة مع حقوق"""
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "دليل الاستخدام",
                    "size": "xl",
                    "weight": "bold",
                    "color": "#000000",
                    "align": "center"
                },
                {
                    "type": "separator",
                    "margin": "xl",
                    "color": "#CCCCCC"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "الأوامر الأساسية",
                            "size": "md",
                            "weight": "bold",
                            "color": "#000000",
                            "margin": "lg"
                        },
                        {
                            "type": "text",
                            "text": "▫️ انضم - التسجيل في البوت\n▫️ انسحب - إلغاء التسجيل\n▫️ نقاطي - عرض إحصائياتك\n▫️ الصدارة - أفضل اللاعبين\n▫️ إيقاف - إنهاء اللعبة\n▫️ مساعدة - عرض هذا الدليل",
                            "size": "sm",
                            "color": "#333333",
                            "wrap": True,
                            "margin": "md"
                        }
                    ],
                    "backgroundColor": "#F5F5F5",
                    "cornerRadius": "10px",
                    "paddingAll": "16px",
                    "margin": "lg"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "أثناء اللعب",
                            "size": "md",
                            "weight": "bold",
                            "color": "#000000",
                            "margin": "lg"
                        },
                        {
                            "type": "text",
                            "text": "▫️ لمح - الحصول على تلميح\n▫️ جاوب - عرض الإجابة",
                            "size": "sm",
                            "color": "#333333",
                            "wrap": True,
                            "margin": "md"
                        }
                    ],
                    "backgroundColor": "#F5F5F5",
                    "cornerRadius": "10px",
                    "paddingAll": "16px",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "بوت الحُوت",
                    "size": "xs",
                    "color": "#999999",
                    "align": "center",
                    "margin": "xl"
                }
            ],
            "backgroundColor": "#FFFFFF",
            "paddingAll": "20px"
        },
        "footer": {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "button",
                    "action": {"type": "message", "label": "انضم", "text": "انضم"},
                    "style": "primary",
                    "color": "#000000",
                    "height": "sm"
                },
                {
                    "type": "button",
                    "action": {"type": "message", "label": "نقاطي", "text": "نقاطي"},
                    "style": "secondary",
                    "height": "sm"
                },
                {
                    "type": "button",
                    "action": {"type": "message", "label": "الصدارة", "text": "الصدارة"},
                    "style": "secondary",
                    "height": "sm"
                }
            ],
            "spacing": "sm",
            "backgroundColor": "#F5F5F5",
            "paddingAll": "16px"
        }
    }

def get_stats_card(user_id, display_name):
    """بطاقة الإحصائيات"""
    stats = get_user_stats(user_id)
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
                        "color": "#000000",
                        "align": "center"
                    },
                    {
                        "type": "separator",
                        "margin": "xl",
                        "color": "#CCCCCC"
                    },
                    {
                        "type": "text",
                        "text": "لم تبدأ بعد",
                        "size": "md",
                        "color": "#666666",
                        "align": "center",
                        "margin": "xl"
                    },
                    {
                        "type": "button",
                        "action": {"type": "message", "label": "ابدأ الآن", "text": "انضم"},
                        "style": "primary",
                        "color": "#000000",
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
                    "color": "#000000",
                    "align": "center"
                },
                {
                    "type": "text",
                    "text": display_name,
                    "size": "md",
                    "color": "#666666",
                    "align": "center",
                    "margin": "sm"
                },
                {
                    "type": "separator",
                    "margin": "xl",
                    "color": "#CCCCCC"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "النقاط", "size": "sm", "color": "#666666", "flex": 1},
                                {"type": "text", "text": str(stats['total_points']), "size": "xxl", "weight": "bold", "color": "#000000", "flex": 1, "align": "end"}
                            ]
                        },
                        {
                            "type": "separator",
                            "margin": "lg",
                            "color": "#E5E5E5"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "الألعاب", "size": "sm", "color": "#666666", "flex": 1},
                                {"type": "text", "text": str(stats['games_played']), "size": "md", "weight": "bold", "color": "#000000", "flex": 1, "align": "end"}
                            ],
                            "margin": "lg"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "الفوز", "size": "sm", "color": "#666666", "flex": 1},
                                {"type": "text", "text": str(stats['wins']), "size": "md", "weight": "bold", "color": "#000000", "flex": 1, "align": "end"}
                            ],
                            "margin": "md"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "معدل الفوز", "size": "sm", "color": "#666666", "flex": 1},
                                {"type": "text", "text": f"{win_rate:.0f}%", "size": "md", "weight": "bold", "color": "#000000", "flex": 1, "align": "end"}
                            ],
                            "margin": "md"
                        }
                    ],
                    "backgroundColor": "#F5F5F5",
                    "cornerRadius": "10px",
                    "paddingAll": "16px",
                    "margin": "xl"
                }
            ],
            "backgroundColor": "#FFFFFF",
            "paddingAll": "20px"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": {"type": "message", "label": "الصدارة", "text": "الصدارة"},
                    "style": "secondary",
                    "height": "sm"
                }
            ],
            "backgroundColor": "#F5F5F5",
            "paddingAll": "12px"
        }
    }

def get_leaderboard_card():
    """لوحة الصدارة"""
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
                        "text": "لوحة الصدارة",
                        "size": "xl",
                        "weight": "bold",
                        "color": "#000000",
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": "لا توجد بيانات",
                        "size": "md",
                        "color": "#666666",
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
            bg_color = "#000000"
            text_color = "#FFFFFF"
            rank = "▪️"
        elif i == 2:
            bg_color = "#333333"
            text_color = "#FFFFFF"
            rank = "▪️"
        elif i == 3:
            bg_color = "#666666"
            text_color = "#FFFFFF"
            rank = "▪️"
        else:
            bg_color = "#F5F5F5"
            text_color = "#000000"
            rank = "▫️"
        
        player_items.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": f"{rank} {i}", "size": "sm", "color": text_color, "flex": 0, "weight": "bold"},
                {"type": "text", "text": leader['display_name'], "size": "sm", "color": text_color, "flex": 3, "margin": "md", "wrap": True},
                {"type": "text", "text": str(leader['total_points']), "size": "sm", "color": text_color, "flex": 1, "align": "end", "weight": "bold"}
            ],
            "backgroundColor": bg_color,
            "cornerRadius": "8px",
            "paddingAll": "12px",
            "margin": "sm" if i > 1 else "md"
        })
    
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "لوحة الصدارة",
                    "size": "xl",
                    "weight": "bold",
                    "color": "#000000",
                    "align": "center"
                },
                {
                    "type": "text",
                    "text": "أفضل اللاعبين",
                    "size": "sm",
                    "color": "#666666",
                    "align": "center",
                    "margin": "sm"
                },
                {
                    "type": "separator",
                    "margin": "xl",
                    "color": "#CCCCCC"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": player_items,
                    "margin": "lg"
                }
            ],
            "backgroundColor": "#FFFFFF",
            "paddingAll": "20px"
        }
    }

def get_winner_card(winner_name, winner_score, all_scores):
    """بطاقة الفائز"""
    score_items = []
    for i, (name, score) in enumerate(all_scores, 1):
        score_items.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": f"▫️ {i}", "size": "sm", "color": "#666666", "flex": 0},
                {"type": "text", "text": name, "size": "sm", "color": "#333333", "flex": 3, "margin": "md"},
                {"type": "text", "text": f"{score} نقطة", "size": "sm", "color": "#000000", "flex": 2, "align": "end", "weight": "bold"}
            ],
            "margin": "md" if i > 1 else "none"
        })
    
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "انتهت اللعبة",
                    "size": "xl",
                    "weight": "bold",
                    "color": "#000000",
                    "align": "center"
                },
                {
                    "type": "separator",
                    "margin": "xl",
                    "color": "#CCCCCC"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "الفائز",
                            "size": "sm",
                            "color": "#666666",
                            "align": "center"
                        },
                        {
                            "type": "text",
                            "text": winner_name,
                            "size": "xxl",
                            "weight": "bold",
                            "color": "#000000",
                            "align": "center",
                            "margin": "sm"
                        },
                        {
                            "type": "text",
                            "text": f"{winner_score} نقطة",
                            "size": "lg",
                            "color": "#666666",
                            "align": "center",
                            "margin": "sm"
                        }
                    ],
                    "backgroundColor": "#F5F5F5",
                    "cornerRadius": "10px",
                    "paddingAll": "20px",
                    "margin": "xl"
                },
                {
                    "type": "text",
                    "text": "النتائج النهائية",
                    "size": "md",
                    "weight": "bold",
                    "color": "#000000",
                    "margin": "xl"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": score_items,
                    "backgroundColor": "#FAFAFA",
                    "cornerRadius": "8px",
                    "paddingAll": "12px",
                    "margin": "md"
                }
            ],
            "backgroundColor": "#FFFFFF",
            "paddingAll": "20px"
        }
    }

def start_game(game_id, game_class, game_type, user_id, event):
    """بدء لعبة جديدة"""
    try:
        with games_lock:
            # تمرير دوال AI للألعاب
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
        if isinstance(response, TextSendMessage):
            response.quick_reply = get_quick_reply()
        elif isinstance(response, list):
            for r in response:
                if isinstance(r, TextSendMessage):
                    r.quick_reply = get_quick_reply()
        line_bot_api.reply_message(event.reply_token, response)
        logger.info(f"✅ بدأت لعبة {game_type}")
        return True
    except Exception as e:
        logger.error(f"❌ خطأ بدء {game_type}: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="حدث خطأ", quick_reply=get_quick_reply())
        )
        return False

@app.route("/", methods=['GET'])
def home():
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>LINE Bot</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, sans-serif;
                background: linear-gradient(135deg, #2c2c2c 0%, #1a1a1a 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            .container {{
                background: white;
                border-radius: 16px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                padding: 40px;
                max-width: 500px;
                width: 100%;
            }}
            h1 {{ color: #000; font-size: 2em; margin-bottom: 10px; text-align: center; }}
            .status {{
                background: #F5F5F5;
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
            }}
            .status-item {{
                display: flex;
                justify-content: space-between;
                padding: 10px 0;
                border-bottom: 1px solid #DDD;
            }}
            .status-item:last-child {{ border-bottom: none; }}
            .label {{ color: #666; }}
            .value {{ color: #000; font-weight: bold; }}
            .footer {{ text-align: center; margin-top: 20px; color: #999; font-size: 0.8em; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>بوت الحُوت</h1>
            <div class="status">
                <div class="status-item">
                    <span class="label">حالة الخادم</span>
                    <span class="value">▪️ يعمل</span>
                </div>
                <div class="status-item">
                    <span class="label">AI Status</span>
                    <span class="value">{'✅ مفعّل' if USE_AI else '❌ معطّل'}</span>
                </div>
                <div class="status-item">
                    <span class="label">اللاعبون</span>
                    <span class="value">▫️ {len(registered_players)}</span>
                </div>
                <div class="status-item">
                    <span class="label">ألعاب نشطة</span>
                    <span class="value">▫️ {len(active_games)}</span>
                </div>
            </div>
            <div class="footer">بوت الحُوت - منصة ألعاب تفاعلية</div>
        </div>
    </body>
    </html>
    """

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
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    except Exception as e:
        logger.error(f"❌ خطأ webhook: {e}")
    return 'OK'

@app.before_request
def validate_request():
    if request.path == '/callback' and request.method == 'POST':
        if not request.headers.get('X-Line-Signature'):
            abort(400)

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """معالج الرسائل"""
    try:
        user_id = event.source.user_id
        text = event.message.text.strip()
        
        if not check_rate_limit(user_id):
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text="انتظر قليلاً", quick_reply=get_quick_reply()))
            return
        
        display_name = get_user_profile_safe(user_id)
        game_id = event.source.group_id if hasattr(event.source, 'group_id') else user_id
        
        # الأوامر الأساسية
        if text in ['البداية', 'ابدأ', 'start', 'البوت']:
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text=f"مرحباً {display_name}\n\nاستخدم الأزرار أدناه",
                    quick_reply=get_quick_reply()))
            return
        
        elif text in ['مساعدة', 'help']:
            line_bot_api.reply_message(event.reply_token,
                FlexSendMessage(alt_text="المساعدة", 
                    contents=get_help_card(), quick_reply=get_quick_reply()))
            return
        
        elif text in ['نقاطي', 'إحصائياتي']:
            line_bot_api.reply_message(event.reply_token,
                FlexSendMessage(alt_text="إحصائياتك", 
                    contents=get_stats_card(user_id, display_name), quick_reply=get_quick_reply()))
            return
        
        elif text in ['الصدارة', 'المتصدرين']:
            line_bot_api.reply_message(event.reply_token,
                FlexSendMessage(alt_text="الصدارة", 
                    contents=get_leaderboard_card(), quick_reply=get_quick_reply()))
            return
        
        elif text in ['إيقاف', 'stop']:
            with games_lock:
                if game_id in active_games:
                    del active_games[game_id]
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="▪️ تم إيقاف اللعبة", quick_reply=get_quick_reply()))
                else:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="لا توجد لعبة نشطة", quick_reply=get_quick_reply()))
            return
        
        elif text in ['انضم', 'تسجيل', 'join']:
            with players_lock:
                if user_id in registered_players:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text=f"▪️ أنت مسجل بالفعل يا {display_name}",
                            quick_reply=get_quick_reply()))
                else:
                    registered_players.add(user_id)
                    with games_lock:
                        for gid, game_data in active_games.items():
                            if 'participants' not in game_data:
                                game_data['participants'] = set()
                            game_data['participants'].add(user_id)
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text=f"▪️ تم تسجيلك بنجاح يا {display_name}",
                            quick_reply=get_quick_reply()))
                    logger.info(f"✅ انضم: {display_name}")
            return
        
        elif text in ['انسحب', 'خروج']:
            with players_lock:
                if user_id in registered_players:
                    registered_players.remove(user_id)
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text=f"▫️ تم انسحابك يا {display_name}",
                            quick_reply=get_quick_reply()))
                else:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="أنت غير مسجل", quick_reply=get_quick_reply()))
            return
        
        # الأوامر النصية
        elif text in ['سؤال', 'سوال']:
            if QUESTIONS:
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text=random.choice(QUESTIONS), quick_reply=get_quick_reply()))
            else:
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text="ملف الأسئلة غير متوفر", quick_reply=get_quick_reply()))
            return
        
        elif text in ['تحدي', 'challenge']:
            if CHALLENGES:
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text=random.choice(CHALLENGES), quick_reply=get_quick_reply()))
            else:
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text="ملف التحديات غير متوفر", quick_reply=get_quick_reply()))
            return
        
        elif text in ['اعتراف', 'confession']:
            if CONFESSIONS:
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text=random.choice(CONFESSIONS), quick_reply=get_quick_reply()))
            else:
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text="ملف الاعترافات غير متوفر", quick_reply=get_quick_reply()))
            return
        
        elif text in ['اكثر', 'أكثر', 'more']:
            if MORE_QUESTIONS:
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text=random.choice(MORE_QUESTIONS), quick_reply=get_quick_reply()))
            else:
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text="ملف الأسئلة الإضافية غير متوفر", quick_reply=get_quick_reply()))
            return
        
        # الألعاب
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
            
            if text == 'توافق':
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
                        'answered_users': set()
                    }
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text="▪️ لعبة التوافق\n\nاكتب اسمين مفصولين بمسافة\nمثال: أحمد فاطمة",
                        quick_reply=get_quick_reply()))
                return
            
            start_game(game_id, game_class, game_type, user_id, event)
            return
        
        # معالجة إجابات الألعاب
        if game_id in active_games:
            game_data = active_games[game_id]
            
            with players_lock:
                is_registered = user_id in registered_players
            
            if not is_registered:
                return
            
            if 'answered_users' in game_data and user_id in game_data['answered_users']:
                return
            
            game = game_data['game']
            game_type = game_data['type']
            
            try:
                result = game.check_answer(text, user_id, display_name)
                if result:
                    if result.get('correct', False):
                        if 'answered_users' not in game_data:
                            game_data['answered_users'] = set()
                        game_data['answered_users'].add(user_id)
                    
                    points = result.get('points', 0)
                    if points > 0:
                        update_user_points(user_id, display_name, points,
                            result.get('won', False), game_type)
                    
                    if result.get('next_question', False):
                        game_data['answered_users'] = set()
                        next_q = game.next_question()
                        if isinstance(next_q, TextSendMessage):
                            next_q.quick_reply = get_quick_reply()
                        line_bot_api.reply_message(event.reply_token, next_q)
                        return
                    
                    if result.get('game_over', False):
                        with games_lock:
                            if game_id in active_games:
                                del active_games[game_id]
                        
                        if result.get('winner_card'):
                            line_bot_api.reply_message(event.reply_token,
                                FlexSendMessage(alt_text="الفائز", 
                                    contents=result['winner_card'], quick_reply=get_quick_reply()))
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
                logger.error(f"❌ خطأ معالجة اللعبة: {e}")
                return
    
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")

def cleanup_old_games():
    while True:
        try:
            time.sleep(300)
            now = datetime.now()
            to_delete = []
            with games_lock:
                for game_id, game_data in active_games.items():
                    if now - game_data.get('created_at', now) > timedelta(minutes=15):
                        to_delete.append(game_id)
                for game_id in to_delete:
                    del active_games[game_id]
                    logger.info(f"🗑️ حذف لعبة قديمة: {game_id}")
        except Exception as e:
            logger.error(f"❌ خطأ التنظيف: {e}")

cleanup_thread = threading.Thread(target=cleanup_old_games, daemon=True)
cleanup_thread.start()

@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f"❌ خطأ: {error}", exc_info=True)
    return 'Internal Server Error', 500

@app.errorhandler(404)
def not_found(error):
    return 'Not Found', 404

@app.errorhandler(400)
def bad_request(error):
    return 'Bad Request', 400

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 بوت الحُوت - المنفذ {port}")
    logger.info(f"🤖 AI: {'مفعّل' if USE_AI else 'معطّل'}")
    logger.info(f"📊 اللاعبون: {len(registered_players)}")
    logger.info(f"🎮 الألعاب النشطة: {len(active_games)}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
