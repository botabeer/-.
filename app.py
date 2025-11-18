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

def create_welcome_card():
    """إنشاء بطاقة الترحيب"""
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": C['bg'],
            "paddingAll": "0px",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": C['topbg'],
                    "paddingTop": "40px",
                    "paddingBottom": "150px",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "cornerRadius": "25px",
                            "backgroundColor": C['bg'],
                            "paddingAll": "25px",
                            "offsetTop": "70px",
                            "contents": [
                                {
                                    "type": "image",
                                    "url": LOGO_URL,
                                    "size": "120px",
                                    "align": "center"
                                },
                                {
                                    "type": "text",
                                    "text": "بوت الحوت",
                                    "weight": "bold",
                                    "size": "26px",
                                    "align": "center",
                                    "margin": "15px",
                                    "color": C['cyan']
                                },
                                {
                                    "type": "separator",
                                    "color": C['sep'],
                                    "margin": "10px"
                                },
                                {
                                    "type": "text",
                                    "text": "الألعاب المتوفرة",
                                    "align": "center",
                                    "size": "18px",
                                    "weight": "bold",
                                    "color": C['text'],
                                    "margin": "15px"
                                },
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "cornerRadius": "15px",
                                    "backgroundColor": C['card'],
                                    "paddingAll": "20px",
                                    "contents": [
                                        {"type": "text", "text": "1. أسرع\n- أول من يكتب الكلمة أو الدعاء الصحيح يفوز", "size": "15px", "color": C['text'], "wrap": True},
                                        {"type": "text", "text": "2. لعبة\n- إنسان، حيوان، نبات، بلد\n- الإجابات بالترتيب:\nإنسان → حيوان → نبات → بلد", "size": "15px", "color": C['text'], "wrap": True, "margin": "10px"},
                                        {"type": "text", "text": "3. سلسلة الكلمات\n- كلمة تبدأ بالحرف الأخير من السابقة", "size": "15px", "color": C['text'], "wrap": True, "margin": "10px"},
                                        {"type": "text", "text": "4. أغنية\n- تخمين المغني من كلمات الأغنية", "size": "15px", "color": C['text'], "wrap": True, "margin": "10px"},
                                        {"type": "text", "text": "5. ضد\n- اعكس الكلمة المعطاة", "size": "15px", "color": C['text'], "wrap": True, "margin": "10px"},
                                        {"type": "text", "text": "6. ترتيب\n- ترتيب العناصر حسب المطلوب", "size": "15px", "color": C['text'], "wrap": True, "margin": "10px"},
                                        {"type": "text", "text": "7. تكوين كلمات\n- تكوين 3 كلمات من 6 حروف\n- طريقة الإجابة:\nجواب1\nجواب2\nجواب3", "size": "15px", "color": C['text'], "wrap": True, "margin": "10px"},
                                        {"type": "text", "text": "8. توافق\n- حساب نسبة التوافق بين اسمين", "size": "15px", "color": C['text'], "wrap": True, "margin": "10px"},
                                        {"type": "text", "text": "9. Ai (AiChat)\n- محادثة ذكية قصيرة", "size": "15px", "color": C['text'], "wrap": True, "margin": "10px"}
                                    ]
                                },
                                {
                                    "type": "text",
                                    "text": "محتوى ترفيهي\nسؤال • منشن • اعتراف • تحدي",
                                    "align": "center",
                                    "size": "16px",
                                    "color": C['text2'],
                                    "margin": "25px",
                                    "wrap": True
                                },
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "spacing": "12px",
                                    "contents": [
                                        {"type": "button", "style": "primary", "height": "md", "color": C['cyan'], "action": {"type": "message", "label": "ابدأ", "text": "ابدأ"}},
                                        {"type": "button", "style": "secondary", "color": "#F1F1F1", "action": {"type": "message", "label": "انضم", "text": "انضم"}},
                                        {"type": "button", "style": "secondary", "color": "#F1F1F1", "action": {"type": "message", "label": "انسحب", "text": "انسحب"}},
                                        {"type": "button", "style": "secondary", "color": "#F1F1F1", "action": {"type": "message", "label": "إيقاف", "text": "إيقاف"}}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    }

def create_help_card():
    """إنشاء بطاقة المساعدة"""
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": C['bg'],
            "paddingAll": "0px",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": C['topbg'],
                    "paddingTop": "40px",
                    "paddingBottom": "150px",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "cornerRadius": "25px",
                            "backgroundColor": C['bg'],
                            "paddingAll": "25px",
                            "offsetTop": "70px",
                            "contents": [
                                {"type": "text", "text": "المساعدة", "weight": "bold", "size": "26px", "align": "center", "margin": "5px", "color": C['cyan']},
                                {"type": "text", "text": "الأوامر المتاحة", "align": "center", "size": "17px", "color": C['text'], "margin": "10px"},
                                {"type": "separator", "color": C['sep'], "margin": "15px"},
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "cornerRadius": "15px",
                                    "backgroundColor": C['card'],
                                    "paddingAll": "18px",
                                    "contents": [
                                        {"type": "text", "text": "• لمح → تلميح ذكي للسؤال", "size": "15px", "color": C['text'], "wrap": True},
                                        {"type": "text", "text": "• جاوب → يعرض الإجابة الصحيحة ثم ينتقل للسؤال التالي", "size": "15px", "color": C['text'], "wrap": True, "margin": "5px"},
                                        {"type": "text", "text": "• إعادة → يعيد تشغيل اللعبة الحالية", "size": "15px", "color": C['text'], "wrap": True, "margin": "5px"},
                                        {"type": "text", "text": "• إيقاف → ينهي اللعبة الجارية فورًا", "size": "15px", "color": C['text'], "wrap": True, "margin": "5px"},
                                        {"type": "text", "text": "• انضم → يسجل اللاعب في الجولة", "size": "15px", "color": C['text'], "wrap": True, "margin": "5px"},
                                        {"type": "text", "text": "• انسحب → يلغي تسجيل اللاعب", "size": "15px", "color": C['text'], "wrap": True, "margin": "5px"},
                                        {"type": "text", "text": "• نقاطي → عرض نقاطك الحالية", "size": "15px", "color": C['text'], "wrap": True, "margin": "5px"},
                                        {"type": "text", "text": "• الصدارة → عرض أفضل اللاعبين", "size": "15px", "color": C['text'], "wrap": True, "margin": "5px"}
                                    ]
                                },
                                {
                                    "type": "box",
                                    "layout": "horizontal",
                                    "spacing": "10px",
                                    "margin": "20px",
                                    "contents": [
                                        {"type": "button", "style": "secondary", "height": "sm", "color": "#F1F1F1", "action": {"type": "message", "label": "نقاطي", "text": "نقاطي"}},
                                        {"type": "button", "style": "secondary", "height": "sm", "color": "#F1F1F1", "action": {"type": "message", "label": "الصدارة", "text": "الصدارة"}}
                                    ]
                                },
                                {"type": "text", "text": "© بوت الحوت 2025", "align": "center", "size": "13px", "color": C['text2'], "margin": "10px"}
                            ]
                        }
                    ]
                }
            ]
        }
    }

def create_stats_card(stats):
    """إنشاء بطاقة الإحصائيات"""
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": C['bg'],
            "paddingAll": "20px",
            "contents": [
                {"type": "text", "text": "📊 إحصائياتك", "weight": "bold", "size": "xl", "color": C['cyan'], "align": "center"},
                {"type": "separator", "color": C['sep'], "margin": "15px"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": C['card'],
                    "cornerRadius": "15px",
                    "paddingAll": "20px",
                    "margin": "md",
                    "contents": [
                        {"type": "text", "text": f"👤 {stats['name']}", "size": "lg", "color": C['text'], "wrap": True},
                        {"type": "text", "text": f"⭐ النقاط: {stats['points']}", "size": "md", "color": C['text'], "margin": "md"},
                        {"type": "text", "text": f"🎮 الألعاب: {stats['games_played']}", "size": "md", "color": C['text'], "margin": "sm"},
                        {"type": "text", "text": f"🏆 الانتصارات: {stats['games_won']}", "size": "md", "color": C['text'], "margin": "sm"}
                    ]
                }
            ]
        }
    }

def create_leaderboard_card(leaderboard):
    """إنشاء بطاقة الصدارة"""
    contents = [
        {"type": "text", "text": "🏆 لوحة الصدارة", "weight": "bold", "size": "xl", "color": C['cyan'], "align": "center"},
        {"type": "separator", "color": C['sep'], "margin": "15px"}
    ]
    
    for i, (name, points, wins) in enumerate(leaderboard[:10], 1):
        emoji = RANK_EMOJIS.get(i, f"{i}.")
        contents.append({
            "type": "box",
            "layout": "horizontal",
            "backgroundColor": C['card'],
            "cornerRadius": "10px",
            "paddingAll": "12px",
            "margin": "sm",
            "contents": [
                {"type": "text", "text": f"{emoji} {name}", "size": "md", "color": C['text'], "flex": 3, "wrap": True},
                {"type": "text", "text": f"{points} نقطة", "size": "sm", "color": C['text2'], "align": "end", "flex": 2}
            ]
        })
    
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": C['bg'],
            "paddingAll": "20px",
            "contents": contents
        }
    }

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
    
    # الحصول على group_id
    group_id = getattr(event.source, 'group_id', user_id)
    
    # التحقق من Rate Limit
    if not check_rate_limit(user_id):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=MESSAGES['rate_limited'])
        )
        return
    
    # جلب اسم المستخدم
    try:
        profile = line_bot_api.get_profile(user_id)
        user_name = profile.display_name
    except:
        user_name = "مستخدم"
    
    # تسجيل/تحديث المستخدم تلقائياً
    if not is_registered(user_id):
        register_user(user_id, user_name)
    else:
        update_user_name(user_id, user_name)
    
    # معالجة الأوامر
    text_lower = text.lower()
    
    # أمر البداية/الترحيب
    if any(cmd in text_lower for cmd in CMDS['start'] + ['بوت', 'whale', 'مرحبا', 'السلام']):
        flex = FlexSendMessage(alt_text="بوت الحوت", contents=create_welcome_card())
        line_bot_api.reply_message(event.reply_token, flex)
        return
    
    # أمر المساعدة
    if any(cmd in text_lower for cmd in CMDS['help']):
        flex = FlexSendMessage(alt_text="المساعدة", contents=create_help_card())
        line_bot_api.reply_message(event.reply_token, flex)
        return
    
    # أمر الإحصائيات
    if any(cmd in text_lower for cmd in CMDS['stats']):
        stats = get_user_stats(user_id)
        if stats:
            flex = FlexSendMessage(alt_text="إحصائياتك", contents=create_stats_card(stats))
            line_bot_api.reply_message(event.reply_token, flex)
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="لم يتم العثور على إحصائيات"))
        return
    
    # أمر الصدارة
    if any(cmd in text_lower for cmd in CMDS['leaderboard']):
        leaderboard = get_leaderboard()
        if leaderboard:
            flex = FlexSendMessage(alt_text="لوحة الصدارة", contents=create_leaderboard_card(leaderboard))
            line_bot_api.reply_message(event.reply_token, flex)
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="لا توجد بيانات للصدارة"))
        return
    
    # أمر الانضمام
    if any(cmd in text_lower for cmd in CMDS['join']):
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MESSAGES['joined']))
        return
    
    # أمر الانسحاب
    if any(cmd in text_lower for cmd in CMDS['leave']):
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MESSAGES['left']))
        return
    
    # أمر بدء لعبة عشوائية
    if text in ['ابدأ', 'start', 'بدء']:
        if group_id in active_games:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MESSAGES['already_playing']))
            return
        
        if GAMES_LOADED:
            game_type = random.choice(GAMES_LIST[:7])  # اختيار لعبة عشوائية (بدون ai)
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
    
    # أمر إيقاف اللعبة
    if any(cmd in text_lower for cmd in CMDS['stop']):
        if group_id in active_games:
            del active_games[group_id]
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MESSAGES['game_stopped']))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MESSAGES['no_active_game']))
        return
    
    # أمر التلميح
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
    
    # أمر جاوب
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
    
    # التحقق من الإجابة
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
                background: linear-gradient(135deg, #0A0E27 0%, #1a1f3a 100%);
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
            h1 {
                text-align: center;
                color: #00D9FF;
                font-size: 2em;
                margin-bottom: 10px;
                text-shadow: 0 0 20px rgba(0, 217, 255, 0.5);
            }
            .subtitle {
                text-align: center;
                color: #7FB3D5;
                margin-bottom: 30px;
            }
            .status-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
                margin-top: 20px;
            }
            .stat-box {
                background: rgba(0, 217, 255, 0.1);
                border: 1px solid rgba(0, 217, 255, 0.3);
                border-radius: 15px;
                padding: 20px;
                text-align: center;
            }
            .stat-value {
                font-size: 2em;
                font-weight: bold;
                color: #00D9FF;
                display: block;
                margin-bottom: 5px;
            }
            .stat-label {
                color: #7FB3D5;
                font-size: 0.9em;
            }
            .footer {
                text-align: center;
                margin-top: 30px;
                color: #7FB3D5;
                font-size: 0.9em;
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            .online-indicator {
                display: inline-block;
                width: 10px;
                height: 10px;
                background: #00FF00;
                border-radius: 50%;
                margin-left: 5px;
                animation: pulse 2s infinite;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="glass-card">
                <img src="https://i.imgur.com/qcWILGi.jpeg" alt="بوت الحوت" class="logo">
                <h1>♓ بوت الحوت</h1>
                <p class="subtitle">
                    <span class="online-indicator"></span>
                    البوت يعمل بنجاح
                </p>
                <div class="status-grid">
                    <div class="stat-box">
                        <span class="stat-value">9</span>
                        <span class="stat-label">ألعاب متوفرة</span>
                    </div>
                    <div class="stat-box">
                        <span class="stat-value">✓</span>
                        <span class="stat-label">جاهز للعمل</span>
                    </div>
                    <div class="stat-box">
                        <span class="stat-value">24/7</span>
                        <span class="stat-label">متاح دائماً</span>
                    </div>
                    <div class="stat-box">
                        <span class="stat-value">♾️</span>
                        <span class="stat-label">متعة لا تنتهي</span>
                    </div>
                </div>
                <div class="footer">
                    <p>© بوت الحوت 2025 - جميع الحقوق محفوظة</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

# ============= تشغيل التطبيق =============

if __name__ == "__main__":
    # تهيئة قاعدة البيانات
    init_db()
    
    # تنظيف المستخدمين غير النشطين
    cleanup_inactive_users()
    
    # تشغيل Flask
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
