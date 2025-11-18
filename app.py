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

# استيراد الإعدادات والألعاب
from config import *
try:
    from games import start_game, check_game_answer, get_hint, show_answer
    GAMES_LOADED = True
except:
    GAMES_LOADED = False
    logging.warning("games.py غير موجود")

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
    """تهيئة قاعدة البيانات"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.executescript(DB_SCHEMA)
    conn.commit()
    conn.close()
    logger.info("تم تهيئة قاعدة البيانات")

def register_user(user_id, name):
    """تسجيل مستخدم جديد"""
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
    """تحديث اسم المستخدم"""
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
    """التحقق من تسجيل المستخدم"""
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
    """تحديث نقاط المستخدم"""
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
    """جلب إحصائيات المستخدم"""
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
    """جلب لوحة الصدارة"""
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
    """حذف المستخدمين غير النشطين"""
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
    """التحقق من حد الطلبات"""
    now = time.time()
    user_requests = rate_limiter[user_id]
    
    # حذف الطلبات القديمة
    user_requests[:] = [t for t in user_requests if now - t < RATE_LIMIT['window']]
    
    # التحقق من الحد
    if len(user_requests) >= RATE_LIMIT['max_requests']:
        return False
    
    user_requests.append(now)
    return True

# ============= Flex Messages =============

# (الوظائف create_welcome_card، create_help_card، create_stats_card، create_leaderboard_card تبقى كما هي)

# ============= معالجة الرسائل =============

@app.route("/callback", methods=['POST'])
def callback():
    """معالجة webhook من LINE"""
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """معالجة الرسائل النصية"""
    user_id = event.source.user_id
    text = event.message.text.strip()
    group_id = getattr(event.source, 'group_id', user_id)
    
    # التحقق من Rate Limit
    if not check_rate_limit(user_id):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=MESSAGES['rate_limited'])
        )
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
    
    # الأوامر: البداية، المساعدة، إحصائيات، الصدارة، الانضمام، الانسحاب، بدء لعبة، إيقاف، لمح، جاوب، الإجابة
    # تبقى جميعها كما هي في النسخة الأصلية

# ============= الصفحة الرئيسية =============

@app.route("/")
def index():
    """الصفحة الرئيسية"""
    return """
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>بوت الحوت</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #000000; /* الخلفية أسود كامل */
                color: #E0F2FF;
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            .container {
                max-width: 600px;
                width: 100%;
            }
            .glass-card {
                background: rgba(15, 36, 64, 0.8);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(0, 217, 255, 0.3);
                border-radius: 25px;
                padding: 40px;
                box-shadow: 0 8px 32px rgba(0, 217, 255, 0.2);
            }
            .logo {
                width: 120px;
                height: 120px;
                margin: 0 auto 20px;
                display: block;
                border-radius: 50%;
                border: 3px solid #00D9FF;
                box-shadow: 0 0 30px rgba(0, 217, 255, 0.5);
            }
            h1 { text-align: center; color: #00D9FF; font-size: 2em; margin-bottom: 10px; text-shadow: 0 0 20px rgba(0,217,255,0.5); }
            .subtitle { text-align: center; color: #7FB3D5; margin-bottom: 30px; }
            .status-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-top: 20px; }
            .stat-box { background: rgba(0,217,255,0.1); border: 1px solid rgba(0,217,255,0.3); border-radius: 15px; padding: 20px; text-align: center; }
            .stat-value { font-size: 2em; font-weight: bold; color: #00D9FF; display: block; margin-bottom: 5px; }
            .stat-label { color: #7FB3D5; font-size: 0.9em; }
            .footer { text-align: center; margin-top: 30px; color: #7FB3D5; font-size: 0.9em; }
            @keyframes pulse { 0%,100%{opacity:1;}50%{opacity:0.5;} }
            .online-indicator { display:inline-block; width:10px; height:10px; background:#00FF00; border-radius:50%; margin-left:5px; animation:pulse 2s infinite; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="glass-card">
                <img src="https://i.imgur.com/qcWILGi.jpeg" alt="بوت الحوت" class="logo">
                <h1> بوت الحوت</h1>
                <p class="subtitle"><span class="online-indicator"></span> البوت يعمل بنجاح</p>
                <div class="status-grid">
                    <div class="stat-box"><span class="stat-value">9</span><span class="stat-label">ألعاب متوفرة</span></div>
                    <div class="stat-box"><span class="stat-value">✓</span><span class="stat-label">جاهز للعمل</span></div>
                    <div class="stat-box"><span class="stat-value">24/7</span><span class="stat-label">متاح دائماً</span></div>
                    <div class="stat-box"><span class="stat-value">♾️</span><span class="stat-label">متعة لا تنتهي</span></div>
                </div>
                <div class="footer"><p>© بوت الحوت 2025 - جميع الحقوق محفوظة</p></div>
            </div>
        </div>
    </body>
    </html>
    """

# ============= تشغيل التطبيق =============

if __name__ == "__main__":
    init_db()
    cleanup_inactive_users()
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
