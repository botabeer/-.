from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage, QuickReply, QuickReplyButton, MessageAction
import os
import sqlite3
import logging
import random
import time
from collections import defaultdict
from datetime import datetime

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

from config import *

# تحميل الألعاب
GAMES_LOADED = False
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("games", "games.py")
    games = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(games)
    start_game = games.start_game
    check_game_answer = games.check_game_answer
    get_hint = games.get_hint
    show_answer = games.show_answer
    GAMES_LOADED = True
    logger.info("✓ تم تحميل الألعاب")
except Exception as e:
    logger.error(f"✗ خطأ تحميل الألعاب: {e}")

app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

active_games = {}
rate_limiter = defaultdict(list)

# قاعدة البيانات
def init_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.executescript(DB_SCHEMA)
        conn.commit()
        conn.close()
        logger.info("✓ قاعدة البيانات جاهزة")
        return True
    except Exception as e:
        logger.error(f"✗ خطأ قاعدة البيانات: {e}")
        return False

# تهيئة قاعدة البيانات عند تشغيل التطبيق
init_db()

def db_execute(query, params=(), fetch=False):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchall() if fetch else None
        conn.commit()
        conn.close()
        return result
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            logger.warning("⚠ إعادة تهيئة قاعدة البيانات...")
            if init_db():
                return db_execute(query, params, fetch)
        logger.error(f"DB Error: {e}")
        return None
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return None

def register_user(user_id, name):
    return db_execute('INSERT OR REPLACE INTO players (user_id, name, last_active) VALUES (?, ?, CURRENT_TIMESTAMP)', (user_id, name))

def update_user_name(user_id, name):
    db_execute('UPDATE players SET name = ?, last_active = CURRENT_TIMESTAMP WHERE user_id = ?', (name, user_id))

def is_registered(user_id):
    result = db_execute('SELECT user_id FROM players WHERE user_id = ?', (user_id,), fetch=True)
    return result is not None and len(result) > 0

def update_points(user_id, points):
    db_execute('UPDATE players SET points = points + ?, last_active = CURRENT_TIMESTAMP WHERE user_id = ?', (points, user_id))

def get_user_stats(user_id):
    result = db_execute('SELECT name, points, games_played, games_won FROM players WHERE user_id = ?', (user_id,), fetch=True)
    if result and len(result) > 0:
        r = result[0]
        return {'name': r[0], 'points': r[1], 'games_played': r[2], 'games_won': r[3]}
    return None

def get_leaderboard(limit=10):
    result = db_execute('SELECT name, points, games_won FROM players ORDER BY points DESC, games_won DESC LIMIT ?', (limit,), fetch=True)
    return result if result else []

# Rate Limiter
def check_rate_limit(user_id):
    now = time.time()
    user_requests = rate_limiter[user_id]
    user_requests[:] = [t for t in user_requests if now - t < RATE_LIMIT['window']]
    if len(user_requests) >= RATE_LIMIT['max_requests']:
        return False
    user_requests.append(now)
    return True

# Quick Reply
def create_quick_reply():
    items = [
        QuickReplyButton(action=MessageAction(label=label, text=text))
        for label, text in [
            ("⏱️ أسرع", "أسرع"), ("🎮 لعبة", "لعبة"), ("🔗 سلسلة", "سلسلة"),
            ("🎵 أغنية", "أغنية"), ("⚖️ ضد", "ضد"), ("📋 ترتيب", "ترتيب"),
            ("🔤 تكوين", "تكوين"), ("💕 توافق", "توافق"), ("❓ سؤال", "سؤال"), ("🏆 تحدي", "تحدي")
        ]
    ]
    return QuickReply(items=items)

# Flex Messages
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
                                    {"type": "text", "text": f"{i}. {desc}", "size": "sm", "color": C['text'], "wrap": True, "margin": "xs" if i > 1 else "none"}
                                    for i, desc in enumerate([
                                        "⏱️ أسرع - أول من يكتب الكلمة/الدعاء",
                                        "🎮 لعبة - إنسان، حيوان، نبات، بلد",
                                        "🔗 سلسلة - كلمات متصلة",
                                        "🎵 أغنية - تخمين المغني",
                                        "⚖️ ضد - عكس الكلمة",
                                        "📋 ترتيب - ترتيب العناصر",
                                        "🔤 تكوين - 3 كلمات من حروف",
                                        "💕 توافق - نسبة التوافق"
                                    ], 1)
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
                        {"type": "text", "text": cmd, "size": "sm", "color": C['text'], "wrap": True, "margin": "xs" if i > 0 else "none"}
                        for i, cmd in enumerate([
                            "• لمح → تلميح ذكي (-1 نقطة)",
                            "• جاوب → عرض الإجابة والانتقال",
                            "• إيقاف → إنهاء اللعبة فوراً",
                            "• نقاطي → إحصائياتك الشخصية",
                            "• الصدارة → أفضل 10 لاعبين"
                        ])
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

# معالجة الرسائل
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature")
        abort(400)
    except Exception as e:
        logger.error(f"Callback error: {e}")
        abort(500)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
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
            line_bot_api.reply_message(event.reply_token, flex)
            return
        
        # المساعدة
        if any(cmd in text_lower for cmd in CMDS['help']):
            flex = FlexSendMessage(alt_text="المساعدة", contents=create_help_card())
            line_bot_api.reply_message(event.reply_token, flex)
            return
        
        # الإحصائيات
        if any(cmd in text_lower for cmd in CMDS['stats']):
            stats = get_user_stats(user_id)
            if stats:
                flex = FlexSendMessage(alt_text="إحصائياتك", contents=create_stats_card(stats))
                line_bot_api.reply_message(event.reply_token, flex)
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="لم يتم العثور على إحصائيات"))
            return
        
        # الصدارة
        if any(cmd in text_lower for cmd in CMDS['leaderboard']):
            leaderboard = get_leaderboard()
            if leaderboard:
                flex = FlexSendMessage(alt_text="لوحة الصدارة", contents=create_leaderboard_card(leaderboard))
                line_bot_api.reply_message(event.reply_token, flex)
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="لا توجد بيانات للصدارة"))
            return
        
        # بدء لعبة عشوائية
        if text in ['ابدأ', 'start', 'بدء']:
            if group_id in active_games:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MESSAGES['already_playing']))
                return
            
            if GAMES_LOADED:
                game_type = random.choice(GAMES_LIST[:8])
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
        
        # إيقاف اللعبة
        if any(cmd in text_lower for cmd in CMDS['stop']):
            if group_id in active_games:
                del active_games[group_id]
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MESSAGES['game_stopped']))
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MESSAGES['no_active_game']))
            return
        
        # التلميح
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
        
        # جاوب
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
    
    except Exception as e:
        logger.error(f"Handle message error: {e}")
        try:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="حدث خطأ، يرجى المحاولة مرة أخرى"))
        except:
            pass

# الصفحة الرئيسية
@app.route("/")
def index():
    status = "✓ متوفرة" if GAMES_LOADED else "✗ غير متوفرة"
    color = "#00FF88" if GAMES_LOADED else "#FF4444"
    
    # التحقق من قاعدة البيانات
    db_status = "✓ متصلة"
    try:
        result = db_execute('SELECT COUNT(*) FROM players', fetch=True)
        player_count = result[0][0] if result else 0
        db_status = f"✓ متصلة ({player_count} لاعب)"
    except:
        db_status = "✗ غير متصلة"
    
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
                    <div class="stat"><span class="stat-value">✓</span><span class="stat-label">{db_status}</span></div>
                </div>
                <div class="footer"><p>© بوت الحوت 2025 - جميع الحقوق محفوظة</p></div>
            </div>
        </div>
    </body>
    </html>
    """

@app.route("/health")
def health():
    """نقطة فحص صحة التطبيق"""
    try:
        # فحص قاعدة البيانات
        result = db_execute('SELECT COUNT(*) FROM players', fetch=True)
        db_ok = result is not None
        
        return {
            "status": "ok" if db_ok and GAMES_LOADED else "degraded",
            "database": "connected" if db_ok else "disconnected",
            "games": "loaded" if GAMES_LOADED else "not loaded",
            "active_games": len(active_games)
        }, 200
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

# تشغيل التطبيق
if __name__ == "__main__":
    print("="*50)
    print("🐋 بوت الحوت - حالة البدء")
    print("="*50)
    print(f"{'✓' if GAMES_LOADED else '✗'} تحميل الألعاب: {'نجح' if GAMES_LOADED else 'فشل'}")
    print("="*50)
    
    port = int(os.getenv("PORT", 5000))
    print(f"🚀 تشغيل البوت على المنفذ {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
