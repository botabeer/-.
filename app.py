"""
Bot Mesh v24.0 - النسخة المبسطة
Created by: Abeer Aldosari © 2025
"""

import os
import sqlite3
import threading
import time
import random
from datetime import datetime, timedelta
from collections import defaultdict
from flask import Flask, request, abort, jsonify
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, 
    ReplyMessageRequest, TextMessage, FlexMessage, FlexContainer
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# إعدادات البوت
# ============================================================================

BOT_NAME = "Bot Mesh"
BOT_VERSION = "24.0 SIMPLE"
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN:
    raise ValueError("Missing LINE credentials in .env file")

# ============================================================================
# قاعدة البيانات المبسطة
# ============================================================================

class SimpleDB:
    def __init__(self, db_path='botmesh.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.Lock()
        self._init_tables()
    
    def _init_tables(self):
        with self.lock:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS users(
                    user_id TEXT PRIMARY KEY,
                    name TEXT,
                    points INTEGER DEFAULT 0,
                    is_registered INTEGER DEFAULT 1
                )
            ''')
            self.conn.commit()
    
    def get_user(self, user_id):
        with self.lock:
            row = self.conn.execute('SELECT * FROM users WHERE user_id=?', (user_id,)).fetchone()
            return dict(row) if row else None
    
    def create_user(self, user_id, name):
        with self.lock:
            self.conn.execute('INSERT OR IGNORE INTO users(user_id, name, points) VALUES(?,?,0)', (user_id, name))
            self.conn.commit()
    
    def add_points(self, user_id, points):
        with self.lock:
            self.conn.execute('UPDATE users SET points=points+? WHERE user_id=?', (points, user_id))
            self.conn.commit()
    
    def get_leaderboard(self, limit=10):
        with self.lock:
            rows = self.conn.execute('SELECT name, points FROM users WHERE points>0 ORDER BY points DESC LIMIT ?', (limit,)).fetchall()
            return [(r['name'], r['points']) for r in rows]

db = SimpleDB()

# ============================================================================
# تطبيق Flask
# ============================================================================

app = Flask(__name__)
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

active_games = {}
user_rate = defaultdict(list)

# ============================================================================
# واجهات المستخدم (UI)
# ============================================================================

def build_home(username, points):
    """الصفحة الرئيسية"""
    return FlexMessage(
        alt_text="البداية",
        contents=FlexContainer.from_dict({
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": f"مرحباً {username}", "size": "xl", "weight": "bold", "color": "#007AFF"},
                    {"type": "text", "text": f"النقاط: {points}", "size": "md", "margin": "md"},
                    {"type": "separator", "margin": "lg"},
                    {"type": "button", "action": {"type": "message", "label": "🎮 الألعاب", "text": "ألعاب"}, "style": "primary", "margin": "lg"},
                    {"type": "button", "action": {"type": "message", "label": "🏆 الصدارة", "text": "صدارة"}, "style": "secondary", "margin": "sm"}
                ],
                "paddingAll": "20px"
            }
        })
    )

def build_games_menu():
    """قائمة الألعاب"""
    games = ["ذكاء", "رياضيات", "لون", "ترتيب", "خمن", "ضد"]
    buttons = [{"type": "button", "action": {"type": "message", "label": g, "text": g}, "style": "primary", "margin": "sm"} for g in games]
    
    return FlexMessage(
        alt_text="الألعاب",
        contents=FlexContainer.from_dict({
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "🎮 الألعاب", "size": "xl", "weight": "bold", "color": "#007AFF"},
                    {"type": "separator", "margin": "lg"},
                    *buttons,
                    {"type": "separator", "margin": "lg"},
                    {"type": "button", "action": {"type": "message", "label": "🏠 رجوع", "text": "بداية"}, "margin": "md"}
                ],
                "paddingAll": "20px"
            }
        })
    )

def build_leaderboard(top_users):
    """لوحة الصدارة"""
    user_list = []
    medals = ["🥇", "🥈", "🥉"]
    
    for i, (name, points) in enumerate(top_users, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        user_list.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": medal, "size": "sm", "flex": 0},
                {"type": "text", "text": name[:15], "size": "sm", "flex": 1, "margin": "md"},
                {"type": "text", "text": str(points), "size": "sm", "flex": 0, "align": "end", "weight": "bold"}
            ],
            "margin": "md"
        })
    
    return FlexMessage(
        alt_text="الصدارة",
        contents=FlexContainer.from_dict({
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "🏆 لوحة الصدارة", "size": "xl", "weight": "bold", "color": "#007AFF"},
                    {"type": "separator", "margin": "lg"},
                    *user_list,
                    {"type": "separator", "margin": "lg"},
                    {"type": "button", "action": {"type": "message", "label": "🏠 رجوع", "text": "بداية"}, "margin": "md"}
                ],
                "paddingAll": "20px"
            }
        })
    )

def build_question(game_name, question_text, current, total):
    """نافذة السؤال"""
    return FlexMessage(
        alt_text=game_name,
        contents=FlexContainer.from_dict({
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": game_name, "size": "xl", "weight": "bold", "color": "#007AFF"},
                    {"type": "text", "text": f"السؤال {current}/{total}", "size": "sm", "color": "#666", "margin": "sm"},
                    {"type": "separator", "margin": "lg"},
                    {"type": "text", "text": question_text, "size": "lg", "weight": "bold", "wrap": True, "margin": "lg", "align": "center"},
                    {"type": "separator", "margin": "lg"},
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "spacing": "sm",
                        "margin": "lg",
                        "contents": [
                            {"type": "button", "action": {"type": "message", "label": "لمح", "text": "لمح"}, "style": "secondary", "flex": 1},
                            {"type": "button", "action": {"type": "message", "label": "جاوب", "text": "جاوب"}, "style": "secondary", "flex": 1}
                        ]
                    }
                ],
                "paddingAll": "20px"
            }
        })
    )

# ============================================================================
# معالج الرسائل
# ============================================================================

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@app.route("/", methods=['GET'])
def home():
    return f"<h1>{BOT_NAME} v{BOT_VERSION}</h1><p>Bot is running ✅</p>"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()
    
    with ApiClient(configuration) as api_client:
        line_api = MessagingApi(api_client)
        
        # الحصول على اسم المستخدم
        try:
            profile = line_api.get_profile(user_id)
            username = profile.display_name or "مستخدم"
        except:
            username = "مستخدم"
        
        # إنشاء أو جلب المستخدم
        user = db.get_user(user_id)
        if not user:
            db.create_user(user_id, username)
            user = db.get_user(user_id)
        
        reply_message = None
        game_id = user_id
        
        # معالجة الأوامر
        if text in ["بداية", "home", "start"]:
            reply_message = build_home(username, user['points'])
        
        elif text in ["ألعاب", "games"]:
            reply_message = build_games_menu()
        
        elif text in ["صدارة", "leaderboard"]:
            top = db.get_leaderboard(10)
            reply_message = build_leaderboard(top)
        
        elif text == "إيقاف":
            if game_id in active_games:
                del active_games[game_id]
                reply_message = TextMessage(text="⏹️ تم إيقاف اللعبة")
        
        # بدء لعبة
        elif text in ["ذكاء", "رياضيات", "لون", "ترتيب", "خمن", "ضد"]:
            from games import get_game
            GameClass = get_game(text)
            if GameClass:
                game = GameClass(line_api)
                active_games[game_id] = game
                reply_message = game.start_game()
        
        # الإجابة على اللعبة
        elif game_id in active_games:
            game = active_games[game_id]
            result = game.check_answer(text, user_id, username)
            
            if result:
                if result.get('points', 0) > 0:
                    db.add_points(user_id, 1)
                
                if result.get('game_over'):
                    del active_games[game_id]
                    points = result.get('points', 0)
                    reply_message = TextMessage(text=f"🎉 انتهت اللعبة!\nحصلت على {points} نقطة")
                elif result.get('response'):
                    reply_message = result['response']
        
        # إرسال الرد
        if reply_message:
            line_api.reply_message(
                ReplyMessageRequest(reply_token=event.reply_token, messages=[reply_message])
            )

# ============================================================================
# تشغيل التطبيق
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    print(f"🚀 {BOT_NAME} v{BOT_VERSION} - Running on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
