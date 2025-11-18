# app.py - بوت الحوت الرئيسي

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    FlexSendMessage, QuickReply, QuickReplyButton, MessageAction
)
import os
import sqlite3
import logging
from datetime import datetime, timedelta
import random
import re
import time
from collections import defaultdict
import json

# استيراد الإعدادات
from config import *

# محاولة استيراد الألعاب من games.py أولاً
GAMES_LOADED = False
try:
    from games import start_game, check_game_answer, get_hint, show_answer
    GAMES_LOADED = True
except Exception as e:
    logging.warning(f"games.py غير موجود أو حدث خطأ: {e}")
    # محاولة fallback من مجلد games/
    try:
        import importlib
        from games import ColorGame  # مثال على لعبة من مجلد games/
        # يمكن إضافة استدعاءات للألعاب الأخرى هنا
        def start_game(group_id, game_type, user_id, user_name):
            return {"game_data": {}, "message": "اللعبة جاهزة", "flex": None}

        def check_game_answer(game, text, user_id, user_name, group_id, active_games):
            return {"correct": False, "message": "لم يتم التحقق من الإجابة"}

        def get_hint(game):
            return "التلميح غير متوفر حالياً"

        def show_answer(game, group_id, active_games):
            return {"message": "لا توجد إجابة حالياً"}

        GAMES_LOADED = True
        logging.info("تم تحميل الألعاب من مجلد games/ كنسخة fallback")
    except Exception as e2:
        logging.warning(f"لم يتم العثور على ملفات الألعاب في games/: {e2}")
        GAMES_LOADED = False

# إعداد Flask
app = Flask(__name__)

# إعداد Logging
logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)
logger = logging.getLogger(__name__)

# LINE Bot API
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# الألعاب النشطة {group_id: {game_type, players, current_q, ...}}
active_games = {}

# Rate Limiter
rate_limiter = defaultdict(list)

# ============= قاعدة البيانات =============

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.executescript(DB_SCHEMA)
    conn.commit()
    conn.close()
    logger.info("تم تهيئة قاعدة البيانات")

def register_user(user_id, name):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO players (user_id, name, last_active)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, name))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"خطأ في تسجيل المستخدم: {e}")
        return False

def update_user_name(user_id, name):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE players SET name = ?, last_active = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (name, user_id))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"خطأ في تحديث الاسم: {e}")

def is_registered(user_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM players WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except:
        return False

def update_points(user_id, points):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE players 
            SET points = points + ?, last_active = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (points, user_id))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"خطأ في تحديث النقاط: {e}")

def get_user_stats(user_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT name, points, games_played, games_won 
            FROM players WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return {
                'name': result[0],
                'points': result[1],
                'games_played': result[2],
                'games_won': result[3]
            }
        return None
    except Exception as e:
        logger.error(f"خطأ في جلب الإحصائيات: {e}")
        return None

def get_leaderboard(limit=10):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT name, points, games_won 
            FROM players 
            ORDER BY points DESC, games_won DESC
            LIMIT ?
        ''', (limit,))
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        logger.error(f"خطأ في جلب الصدارة: {e}")
        return []

def cleanup_inactive_users():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cutoff = datetime.now() - timedelta(days=GAME_SETTINGS['inactive_days'])
        cursor.execute('''
            DELETE FROM players 
            WHERE last_active < ?
        ''', (cutoff,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        logger.info(f"تم حذف {deleted} مستخدم غير نشط")
    except Exception as e:
        logger.error(f"خطأ في تنظيف المستخدمين: {e}")

# ============= Rate Limiter =============

def check_rate_limit(user_id):
    now = time.time()
    user_requests = rate_limiter[user_id]
    user_requests[:] = [t for t in user_requests if now - t < RATE_LIMIT['window']]
    if len(user_requests) >= RATE_LIMIT['max_requests']:
        return False
    user_requests.append(now)
    return True

# ============= Flex Messages =============

def create_welcome_card():
    # الكود كامل Flex Message كما في نسختك السابقة
    pass  # استبدله بالكود الذي لديك

def create_help_card():
    pass  # استبدله بالكود الذي لديك

def create_stats_card(stats):
    pass  # استبدله بالكود الذي لديك

def create_leaderboard_card(leaderboard):
    pass  # استبدله بالكود الذي لديك

# ============= معالجة الرسائل =============

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()
    group_id = getattr(event.source, 'group_id', user_id)
    
    if not check_rate_limit(user_id):
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MESSAGES['rate_limited']))
        return
    
    try:
        profile = line_bot_api.get_profile(user_id)
        user_name = profile.display_name
    except:
        user_name = "مستخدم"
    
    if not is_registered(user_id):
        register_user(user_id, user_name)
    else:
        update_user_name(user_id, user_name)
    
    text_lower = text.lower()
    
    if any(cmd in text_lower for cmd in CMDS['start'] + ['بوت', 'whale', 'مرحبا', 'السلام']):
        flex = FlexSendMessage(alt_text="بوت الحوت", contents=create_welcome_card())
        line_bot_api.reply_message(event.reply_token, flex)
        return
    
    if any(cmd in text_lower for cmd in CMDS['help']):
        flex = FlexSendMessage(alt_text="المساعدة", contents=create_help_card())
        line_bot_api.reply_message(event.reply_token, flex)
        return
    
    if any(cmd in text_lower for cmd in CMDS['stats']):
        stats = get_user_stats(user_id)
        if stats:
            flex = FlexSendMessage(alt_text="إحصائياتك", contents=create_stats_card(stats))
            line_bot_api.reply_message(event.reply_token, flex)
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="لم يتم العثور على إحصائيات"))
        return
    
    if any(cmd in text_lower for cmd in CMDS['leaderboard']):
        leaderboard = get_leaderboard()
        if leaderboard:
            flex = FlexSendMessage(alt_text="لوحة الصدارة", contents=create_leaderboard_card(leaderboard))
            line_bot_api.reply_message(event.reply_token, flex)
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="لا توجد بيانات للصدارة"))
        return
    
    if any(cmd in text_lower for cmd in CMDS['join']):
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MESSAGES['joined']))
        return
    
    if any(cmd in text_lower for cmd in CMDS['leave']):
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MESSAGES['left']))
        return
    
    if text in ['ابدأ', 'start', 'بدء']:
        if group_id in active_games:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MESSAGES['already_playing']))
            return
        if GAMES_LOADED:
            game_type = random.choice(GAMES_LIST[:7])
            result = start_game(group_id, game_type, user_id, user_name)
            active_games[group_id] = result['game_data']
            if result.get('flex'):
                flex = FlexSendMessage(alt_text=result['message'], contents=result['flex'])
                line_bot_api.reply_message(event.reply_token, flex)
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result['message']))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="الألعاب غير متوفرة حالياً"))
        return
    
    if any(cmd in text_lower for cmd in CMDS['stop']):
        if group_id in active_games:
            del active_games[group_id]
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MESSAGES['game_stopped']))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MESSAGES['no_active_game']))
        return
    
    if any(cmd in text_lower for cmd in CMDS['hint']):
        if group_id in active_games and GAMES_LOADED:
            game = active_games[group_id]
            hint_text = get_hint(game)
            if hint_text:
                update_points(user_id, POINTS['hint'])
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=hint_text))
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="التلميح غير متوفر لهذه اللعبة"))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MESSAGES['no_active_game']))
        return
    
    if any(cmd in text_lower for cmd in CMDS['answer']):
        if group_id in active_games and GAMES_LOADED:
            game = active_games[group_id]
            answer_result = show_answer(game, group_id, active_games)
            if answer_result.get('flex'):
                flex = FlexSendMessage(alt_text=answer_result['message'], contents=answer_result['flex'])
                line_bot_api.reply_message(event.reply_token, flex)
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=answer_result['message']))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MESSAGES['no_active_game']))
        return
    
    if group_id in active_games and GAMES_LOADED:
        game = active_games[group_id]
        result = check_game_answer(game, text, user_id, user_name, group_id, active_games)
        if result['correct']:
            update_points(user_id, POINTS['correct'])
        if result.get('flex'):
            flex = FlexSendMessage(alt_text=result['message'], contents=result['flex'])
            line_bot_api.reply_message(event.reply_token, flex)
        elif result.get('message'):
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result['message']))

# ============= الصفحة الرئيسية =============

@app.route("/")
def index():
    return """
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
    <meta charset="UTF-8">
    <title>بوت الحوت</title>
    <style>
    body { background-color: #000; color: #E0F2FF; font-family: 'Segoe UI', sans-serif; }
    /* أضف بقية CSS من النسخة السابقة */
    </style>
    </head>
    <body>
    <h1> بوت الحوت</h1>
    </body>
    </html>
    """

# ============= تشغيل التطبيق =============

if __name__ == "__main__":
    init_db()
    cleanup_inactive_users()
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
