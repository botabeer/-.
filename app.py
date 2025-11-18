# app.py - بوت الحوت المحسن

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage, QuickReply, QuickReplyButton, MessageAction
import os
import sqlite3
import logging
from datetime import datetime, timedelta
import random
import time
from collections import defaultdict

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

from config import *

# تحميل الألعاب
GAMES_LOADED = False
GAMES_SOURCE = None

try:
    import importlib.util
    current_dir = os.path.dirname(os.path.abspath(__file__))
    games_file = os.path.join(current_dir, 'games.py')
    
    if os.path.exists(games_file):
        spec = importlib.util.spec_from_file_location("games_module", games_file)
        games_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(games_module)
        start_game = games_module.start_game
        check_game_answer = games_module.check_game_answer
        get_hint = games_module.get_hint
        show_answer = games_module.show_answer
        GAMES_LOADED = True
        GAMES_SOURCE = "games.py"
        logger.info("✓ تم تحميل الألعاب بنجاح")
    else:
        raise FileNotFoundError("games.py غير موجود")
except Exception as e:
    logger.error(f"✗ فشل تحميل الألعاب: {e}")
    GAMES_LOADED = False

app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

active_games = {}
rate_limiter = defaultdict(list)

# ============= قاعدة البيانات =============

def init_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.executescript(DB_SCHEMA)
        conn.commit()
        conn.close()
        logger.info("✓ تم تهيئة قاعدة البيانات")
    except Exception as e:
        logger.error(f"✗ خطأ في قاعدة البيانات: {e}")

def register_user(user_id, name):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO players (user_id, name, last_active) VALUES (?, ?, CURRENT_TIMESTAMP)', (user_id, name))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def update_user_name(user_id, name):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('UPDATE players SET name = ?, last_active = CURRENT_TIMESTAMP WHERE user_id = ?', (name, user_id))
        conn.commit()
        conn.close()
    except:
        pass

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
        cursor.execute('UPDATE players SET points = points + ?, last_active = CURRENT_TIMESTAMP WHERE user_id = ?', (points, user_id))
        conn.commit()
        conn.close()
    except:
        pass

def get_user_stats(user_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT name, points, games_played, games_won FROM players WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return {'name': result[0], 'points': result[1], 'games_played': result[2], 'games_won': result[3]}
        return None
    except:
        return None

def get_leaderboard(limit=10):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT name, points, games_won FROM players ORDER BY points DESC, games_won DESC LIMIT ?', (limit,))
        results = cursor.fetchall()
        conn.close()
        return results
    except:
        return []

# ============= Rate Limiter =============

def check_rate_limit(user_id):
    now = time.time()
    user_requests = rate_limiter[user_id]
    user_requests[:] = [t for t in user_requests if now - t < RATE_LIMIT['window']]
    if len(user_requests) >= RATE_LIMIT['max_requests']:
        return False
    user_requests.append(now)
    return True

# ============= Quick Reply =============

def create_quick_reply():
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="أسرع", text="أسرع")),
        QuickReplyButton(action=MessageAction(label="لعبة", text="لعبة")),
        QuickReplyButton(action=MessageAction(label="سلسلة", text="سلسلة")),
        QuickReplyButton(action=MessageAction(label="أغنية", text="أغنية")),
        QuickReplyButton(action=MessageAction(label="ضد", text="ضد")),
        QuickReplyButton(action=MessageAction(label="ترتيب", text="ترتيب")),
        QuickReplyButton(action=MessageAction(label="تكوين", text="تكوين")),
        QuickReplyButton(action=MessageAction(label="توافق", text="توافق")),
        QuickReplyButton(action=MessageAction(label="سؤال", text="سؤال")),
        QuickReplyButton(action=MessageAction(label="تحدي", text="تحدي"))
    ])

# ============= Flex Messages =============

def create_welcome_card():
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
                    "contents": [{
                        "type": "box",
                        "layout": "vertical",
                        "cornerRadius": "25px",
                        "backgroundColor": C['bg'],
                        "paddingAll": "25px",
                        "offsetTop": "70px",
                        "contents": [
                            {"type": "image", "url": LOGO_URL, "size": "120px", "align": "center"},
                            {"type": "text", "text": "بوت الحوت", "weight": "bold", "size": "xxl", "align": "center", "margin": "md", "color": C['cyan']},
                            {"type": "separator", "color": C['sep'], "margin": "md"},
                            {"type": "text", "text": "الألعاب المتوفرة", "align": "center", "size": "lg", "weight": "bold", "color": C['text'], "margin": "md"},
                            {
                                "type": "box",
                                "layout": "vertical",
                                "cornerRadius": "15px",
                                "backgroundColor": C['card'],
                                "paddingAll": "18px",
                                "margin": "md",
                                "contents": [
                                    {"type": "text", "text": "⏱️ أسرع - أول من يكتب الكلمة/الدعاء الصحيح", "size": "sm", "color": C['text'], "wrap": True},
                                    {"type": "text", "text": "🎮 لعبة - إنسان، حيوان، نبات، بلد", "size": "sm", "color": C['text'], "wrap": True, "margin": "sm"},
                                    {"type": "text", "text": "🔗 سلسلة - كلمات متصلة", "size": "sm", "color": C['text'], "wrap": True, "margin": "sm"},
                                    {"type": "text", "text": "🎵 أغنية - تخمين المغني", "size": "sm", "color": C['text'], "wrap": True, "margin": "sm"},
                                    {"type": "text", "text": "⚖️ ضد - عكس الكلمة", "size": "sm", "color": C['text'], "wrap": True, "margin": "sm"},
                                    {"type": "text", "text": "📋 ترتيب - ترتيب العناصر", "size": "sm", "color": C['text'], "wrap": True, "margin": "sm"},
                                    {"type": "text", "text": "🔤 تكوين - تكوين 3 كلمات", "size": "sm", "color": C['text'], "wrap": True, "margin": "sm"},
                                    {"type": "text", "text": "💕 توافق - نسبة التوافق", "size": "sm", "color": C['text'], "wrap": True, "margin": "sm"}
                                ]
                            },
                            {"type": "text", "text": "محتوى ترفيهي\nسؤال • تحدي • اعتراف • منشن", "align": "center", "size": "sm", "color": C['text2'], "margin": "lg", "wrap": True},
                            {
                                "type": "box",
                                "layout": "vertical",
                                "spacing": "sm",
                                "margin": "lg",
                                "contents": [
                                    {"type": "button", "style": "primary", "color": C['cyan'], "action": {"type": "message", "label": "🎮 ابدأ", "text": "ابدأ"}},
                                    {"type": "button", "style": "secondary", "color": "#E8F4F8", "action": {"type": "message", "label": "📊 نقاطي", "text": "نقاطي"}},
                                    {"type": "button", "style": "secondary", "color": "#E8F4F8", "action": {"type": "message", "label": "🏆 الصدارة", "text": "الصدارة"}}
                                ]
                            }
                        ]
                    }]
                }
            ]
        }
    }

def create_help_card():
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": C['bg'],
            "paddingAll": "20px",
            "contents": [
                {"type": "text", "text": "💡 المساعدة", "weight": "bold", "size": "xl", "color": C['cyan'], "align": "center"},
                {"type": "separator", "color": C['sep'], "margin": "md"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": C['card'],
                    "cornerRadius": "12px",
                    "paddingAll": "16px",
                    "margin": "md",
                    "contents": [
                        {"type": "text", "text": "• لمح → تلميح ذكي (-1 نقطة)", "size": "sm", "color": C['text'], "wrap": True},
                        {"type": "text", "text": "• جاوب → عرض الجواب والانتقال", "size": "sm", "color": C['text'], "wrap": True, "margin": "xs"},
                        {"type": "text", "text": "• إيقاف → إنهاء اللعبة فوراً", "size": "sm", "color": C['text'], "wrap": True, "margin": "xs"},
                        {"type": "text", "text": "• نقاطي → إحصائياتك الشخصية", "size": "sm", "color": C['text'], "wrap": True, "margin": "xs"},
                        {"type": "text", "text": "• الصدارة → أفضل 10 لاعبين", "size": "sm", "color": C['text'], "wrap": True, "margin": "xs"}
                    ]
                },
                {"type": "text", "text": "© بوت الحوت 2025", "align": "center", "size": "xs", "color": C['text2'], "margin": "lg"}
            ]
        }
    }

def create_stats_card(stats):
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
                {"type": "separator", "color": C['sep'], "margin": "md"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": C['card'],
                    "cornerRadius": "12px",
                    "paddingAll": "18px",
                    "margin": "md",
                    "contents": [
                        {"type": "text", "text": f"👤 {stats['name']}", "size": "lg", "color": C['text'], "weight": "bold", "wrap": True},
                        {"type": "text", "text": f"⭐ النقاط: {stats['points']}", "size": "md", "color": C['text'], "margin": "md"},
                        {"type": "text", "text": f"🎮 الألعاب: {stats['games_played']}", "size": "md", "color": C['text'], "margin": "sm"},
                        {"type": "text", "text": f"🏆 الانتصارات: {stats['games_won']}", "size": "md", "color": C['text'], "margin": "sm"}
                    ]
                }
            ]
        }
    }

def create_leaderboard_card(leaderboard):
    contents = [
        {"type": "text", "text": "🏆 لوحة الصدارة", "weight": "bold", "size": "xl", "color": C['cyan'], "align": "center"},
        {"type": "separator", "color": C['sep'], "margin": "md"}
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
                {"type": "text", "text": f"{emoji} {name}", "size": "sm", "color": C['text'], "flex": 3, "wrap": True},
                {"type": "text", "text": f"{points} نقطة", "size": "xs", "color": C['text2'], "align": "end", "flex": 2}
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
    
    # أوامر البداية
    if any(cmd in text_lower for cmd in CMDS['start'] + ['بوت', 'whale', 'مرحبا', 'السلام']):
        flex = FlexSendMessage(alt_text="بوت الحوت", contents=create_welcome_card())
        line_bot_api.reply_message(event.reply_token, flex, quick_reply=create_quick_reply())
        return
    
    # المساعدة
    if any(cmd in text_lower for cmd in CMDS['help']):
        flex = FlexSendMessage(alt_text="المساعدة", contents=create_help_card())
        line_bot_api.reply_message(event.reply_token, flex, quick_reply=create_quick_reply())
        return
    
    # الإحصائيات
    if any(cmd in text_lower for cmd in CMDS['stats']):
        stats = get_user_stats(user_id)
        if stats:
            flex = FlexSendMessage(alt_text="إحصائياتك", contents=create_stats_card(stats))
            line_bot_api.reply_message(event.reply_token, flex, quick_reply=create_quick_reply())
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="لم يتم العثور على إحصائيات", quick_reply=create_quick_reply()))
        return
    
    # الصدارة
    if any(cmd in text_lower for cmd in CMDS['leaderboard']):
        leaderboard = get_leaderboard()
        if leaderboard:
            flex = FlexSendMessage(alt_text="لوحة الصدارة", contents=create_leaderboard_card(leaderboard))
            line_bot_api.reply_message(event.reply_token, flex, quick_reply=create_quick_reply())
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="لا توجد بيانات للصدارة", quick_reply=create_quick_reply()))
        return
    
    # بدء لعبة عشوائية
    if text in ['ابدأ', 'start', 'بدء']:
        if group_id in active_games:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MESSAGES['already_playing'], quick_reply=create_quick_reply()))
            return
        
        if GAMES_LOADED:
            game_type = random.choice(GAMES_LIST[:8])
            result = start_game(group_id, game_type, user_id, user_name)
            active_games[group_id] = result['game_data']
            
            if result.get('flex'):
                flex = FlexSendMessage(alt_text=result['message'], contents=result['flex'])
                line_bot_api.reply_message(event.reply_token, flex, quick_reply=create_quick_reply())
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result['message'], quick_reply=create_quick_reply()))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="الألعاب غير متوفرة حالياً", quick_reply=create_quick_reply()))
        return
    
    # إيقاف اللعبة
    if any(cmd in text_lower for cmd in CMDS['stop']):
        if group_id in active_games:
            del active_games[group_id]
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MESSAGES['game_stopped'], quick_reply=create_quick_reply()))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MESSAGES['no_active_game'], quick_reply=create_quick_reply()))
        return
    
    # التلميح
    if any(cmd in text_lower for cmd in CMDS['hint']):
        if group_id in active_games and GAMES_LOADED:
            game = active_games[group_id]
            hint_text = get_hint(game)
            if hint_text:
                update_points(user_id, POINTS['hint'])
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=hint_text, quick_reply=create_quick_reply()))
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="التلميح غير متوفر لهذه اللعبة", quick_reply=create_quick_reply()))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MESSAGES['no_active_game'], quick_reply=create_quick_reply()))
        return
    
    # جاوب
    if any(cmd in text_lower for cmd in CMDS['answer']):
        if group_id in active_games and GAMES_LOADED:
            game = active_games[group_id]
            answer_result = show_answer(game, group_id, active_games)
            
            if answer_result.get('flex'):
                flex = FlexSendMessage(alt_text=answer_result['message'], contents=answer_result['flex'])
                line_bot_api.reply_message(event.reply_token, flex, quick_reply=create_quick_reply())
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=answer_result['message'], quick_reply=create_quick_reply()))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MESSAGES['no_active_game'], quick_reply=create_quick_reply()))
        return
    
    # التحقق من الإجابة
    if group_id in active_games and GAMES_LOADED:
        game = active_games[group_id]
        result = check_game_answer(game, text, user_id, user_name, group_id, active_games)
        
        if result['correct']:
            update_points(user_id, POINTS['correct'])
        
        if result.get('flex'):
            flex = FlexSendMessage(alt_text=result['message'], contents=result['flex'])
            line_bot_api.reply_message(event.reply_token, flex, quick_reply=create_quick_reply())
        elif result.get('message'):
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result['message'], quick_reply=create_quick_reply()))

# ============= الصفحة الرئيسية =============

@app.route("/")
def index():
    status = "✓ متوفرة" if GAMES_LOADED else "✗ غير متوفرة"
    color = "#00FF88" if GAMES_LOADED else "#FF4444"
    
    return f"""
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>بوت الحوت</title>
        <style>
            *{{margin:0;padding:0;box-sizing:border-box}}
            body{{font-family:'Segoe UI',Tahoma,sans-serif;background:linear-gradient(135deg,#0A0E27 0%,#1a1f3a 100%);color:#E0F2FF;min-height:100vh;display:flex;justify-content:center;align-items:center;padding:20px}}
            .container{{max-width:600px;width:100%}}
            .card{{background:rgba(15,36,64,0.8);backdrop-filter:blur(10px);border:1px solid rgba(0,217,255,0.3);border-radius:20px;padding:30px;box-shadow:0 8px 32px rgba(0,217,255,0.2)}}
            .logo{{width:100px;height:100px;margin:0 auto 15px;display:block;border-radius:50%;border:3px solid #00D9FF;box-shadow:0 0 20px rgba(0,217,255,0.5)}}
            h1{{text-align:center;color:#00D9FF;font-size:2em;margin-bottom:10px;text-shadow:0 0 15px rgba(0,217,255,0.5)}}
            .subtitle{{text-align:center;color:#7FB3D5;margin-bottom:20px;font-size:0.9em}}
            .grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-top:15px}}
            .stat{{background:rgba(0,217,255,0.1);border:1px solid rgba(0,217,255,0.3);border-radius:12px;padding:15px;text-align:center}}
            .stat-value{{font-size:1.5em;font-weight:bold;color:#00D9FF;display:block;margin-bottom:5px}}
            .stat-label{{color:#7FB3D5;font-size:0.85em}}
            .footer{{text-align:center;margin-top:20px;color:#7FB3D5;font-size:0.85em}}
            @keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:0.5}}}}
            .indicator{{display:inline-block;width:8px;height:8px;background:{color};border-radius:50%;margin-left:5px;animation:pulse 2s infinite}}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <img src="{LOGO_URL}" alt="بوت الحوت" class="logo">
                <h1>بوت الحوت</h1>
                <p class="subtitle"><span class="indicator"></span>البوت يعمل بنجاح</p>
                <div class="grid">
                    <div class="stat"><span class="stat-value">8</span><span class="stat-label">ألعاب متوفرة</span></div>
                    <div class="stat"><span class="stat-value"><span class="indicator"></span></span><span class="stat-label">{status}</span></div>
                    <div class="stat"><span class="stat-value">24/7</span><span class="stat-label">متاح دائماً</span></div>
                    <div class="stat"><span class="stat-value">✓</span><span class="stat-label">جاهز للعمل</span></div>
                </div>
                <div class="footer"><p>© بوت الحوت 2025 - جميع الحقوق محفوظة</p></div>
            </div>
        </div>
    </body>
    </html>
    """

# ============= تشغيل التطبيق =============

if __name__ == "__main__":
    print("="*50)
    print("🐋 بوت الحوت - حالة البدء")
    print("="*50)
    if GAMES_LOADED:
        print(f"✓ تم تحميل الألعاب: {GAMES_SOURCE}")
    else:
        print("✗ تحذير: لم يتم تحميل الألعاب")
    print("="*50)
    
    init_db()
    port = int(os.getenv("PORT", 5000))
    print(f"🚀 تشغيل البوت على المنفذ {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
