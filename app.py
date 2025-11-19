from flask import Flask, request, abort, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
import os
import sqlite3
import logging
import random
import time
from collections import defaultdict
from datetime import datetime, timedelta
from contextlib import contextmanager

# إعداد Logging المحسّن
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('whale_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════
# الإعدادات الافتراضية (تُحمّل دائماً أولاً)
# ══════════════════════════════════════════════════════════════
DB_NAME = 'whale_bot.db'
C = {
    'bg': '#0A0E27',
    'topbg': '#88AEE0',
    'card': '#0F2440',
    'cyan': '#00D9FF',
    'text': '#E0F2FF',
    'text2': '#7FB3D5',
    'sep': '#1F3A53'
}
POINTS = {'correct': 2, 'hint': -1}
RATE_LIMIT = {'max_requests': 20, 'window': 60}
CMDS = {
    'start': ['ابدأ', 'start', 'بدء', 'هاي'],
    'help': ['مساعدة', 'help'],
    'stats': ['نقاطي', 'احصائياتي'],
    'leaderboard': ['الصدارة', 'المتصدرين'],
    'stop': ['إيقاف', 'stop', 'ايقاف'],
    'hint': ['لمح', 'تلميح'],
    'answer': ['جاوب', 'الجواب'],
    'join': ['انضم', 'join'],
    'leave': ['انسحب', 'leave'],
    'replay': ['إعادة', 'اعادة']
}
RANK_EMOJIS = {1: '🥇', 2: '🥈', 3: '🥉', 4: '4️⃣', 5: '5️⃣', 6: '6️⃣', 7: '7️⃣', 8: '8️⃣', 9: '9️⃣', 10: '🔟'}

# محاولة استيراد الإعدادات من config.py (اختياري)
try:
    from config import *
    logger.info("✓ تم تحميل config.py وتحديث الإعدادات")
except ImportError:
    logger.info("ℹ️ ملف config.py غير موجود - استخدام الإعدادات الافتراضية")
except Exception as e:
    logger.warning(f"⚠️ خطأ في تحميل config.py: {e} - استخدام الإعدادات الافتراضية")

# رابط اللوجو الجديد
LOGO_URL = "https://i.imgur.com/qcWILGi.jpeg"

# تحميل الألعاب
GAMES_LOADED = False
try:
    from games import start_game, check_game_answer, get_hint, show_answer
    GAMES_LOADED = True
    logger.info("✓ تم تحميل games.py بنجاح")
except Exception as e:
    logger.error(f"✗ خطأ في تحميل games.py: {e}")

app = Flask(__name__)

# التحقق من المتغيرات البيئية
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    logger.error("⚠️ متغيرات LINE غير موجودة!")
    raise ValueError("LINE credentials required")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# المتغيرات العامة
active_games = {}
rate_limiter = defaultdict(list)

# قاعدة البيانات
DB_SCHEMA = '''
CREATE TABLE IF NOT EXISTS players (
    user_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    points INTEGER DEFAULT 0,
    games_played INTEGER DEFAULT 0,
    games_won INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_points ON players(points DESC);
CREATE INDEX IF NOT EXISTS idx_games_won ON players(games_won DESC);
CREATE INDEX IF NOT EXISTS idx_last_active ON players(last_active DESC);
'''

@contextmanager
def get_db_connection():
    """Context manager لإدارة اتصال قاعدة البيانات"""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        conn.row_factory = sqlite3.Row
        yield conn
        conn.commit()
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"خطأ في قاعدة البيانات: {e}")
        raise
    finally:
        if conn:
            conn.close()

def init_db():
    """تهيئة قاعدة البيانات"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript(DB_SCHEMA)
            logger.info("✓ قاعدة البيانات جاهزة")
        return True
    except Exception as e:
        logger.error(f"✗ خطأ في تهيئة قاعدة البيانات: {e}")
        return False

# تهيئة قاعدة البيانات عند بدء التطبيق
init_db()

def db_execute(query, params=(), fetch=False):
    """تنفيذ استعلام SQL مع معالجة الأخطاء"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
            return True
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            logger.warning("⚠ إعادة تهيئة قاعدة البيانات...")
            if init_db():
                return db_execute(query, params, fetch)
        logger.error(f"خطأ في التنفيذ: {e}")
        return None if fetch else False
    except Exception as e:
        logger.error(f"خطأ في قاعدة البيانات: {e}")
        return None if fetch else False

# دوال إدارة المستخدمين
def register_user(user_id, name):
    """تسجيل مستخدم جديد أو تحديثه"""
    return db_execute(
        'INSERT OR REPLACE INTO players (user_id, name, last_active) VALUES (?, ?, CURRENT_TIMESTAMP)',
        (user_id, name)
    )

def update_user_activity(user_id, name):
    """تحديث آخر نشاط للمستخدم"""
    db_execute(
        'UPDATE players SET name = ?, last_active = CURRENT_TIMESTAMP WHERE user_id = ?',
        (name, user_id)
    )

def is_registered(user_id):
    """التحقق من تسجيل المستخدم"""
    result = db_execute('SELECT user_id FROM players WHERE user_id = ?', (user_id,), fetch=True)
    return result is not None and len(result) > 0

def update_points(user_id, points):
    """تحديث نقاط المستخدم"""
    if points != 0:
        db_execute(
            'UPDATE players SET points = points + ?, last_active = CURRENT_TIMESTAMP WHERE user_id = ?',
            (points, user_id)
        )

def update_game_stats(user_id, won=False):
    """تحديث إحصائيات الألعاب"""
    if won:
        db_execute(
            'UPDATE players SET games_played = games_played + 1, games_won = games_won + 1, last_active = CURRENT_TIMESTAMP WHERE user_id = ?',
            (user_id,)
        )
    else:
        db_execute(
            'UPDATE players SET games_played = games_played + 1, last_active = CURRENT_TIMESTAMP WHERE user_id = ?',
            (user_id,)
        )

def get_user_stats(user_id):
    """الحصول على إحصائيات المستخدم"""
    result = db_execute(
        'SELECT name, points, games_played, games_won FROM players WHERE user_id = ?',
        (user_id,), fetch=True
    )
    if result and len(result) > 0:
        row = result[0]
        return {
            'name': row[0],
            'points': row[1],
            'games_played': row[2],
            'games_won': row[3]
        }
    return None

def get_leaderboard(limit=10):
    """الحصول على لوحة الصدارة"""
    result = db_execute(
        'SELECT name, points, games_won FROM players ORDER BY points DESC, games_won DESC LIMIT ?',
        (limit,), fetch=True
    )
    return result if result else []

def clean_inactive_users():
    """حذف المستخدمين غير النشطين (45+ يوم)"""
    try:
        cutoff_date = datetime.now() - timedelta(days=45)
        db_execute(
            'DELETE FROM players WHERE last_active < ?',
            (cutoff_date.isoformat(),)
        )
        logger.info("✓ تم تنظيف المستخدمين غير النشطين")
    except Exception as e:
        logger.error(f"خطأ في التنظيف: {e}")

# Rate Limiter
def check_rate_limit(user_id):
    """فحص حد الطلبات للمستخدم"""
    now = time.time()
    user_requests = rate_limiter[user_id]
    user_requests[:] = [t for t in user_requests if now - t < RATE_LIMIT['window']]
    
    if len(user_requests) >= RATE_LIMIT['max_requests']:
        return False
    
    user_requests.append(now)
    return True

# دوال Flex Messages
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
                                    "size": "xxl",
                                    "align": "center",
                                    "margin": "md",
                                    "color": C['cyan']
                                },
                                {
                                    "type": "separator",
                                    "color": C['sep'],
                                    "margin": "md"
                                },
                                {
                                    "type": "text",
                                    "text": "الألعاب المتوفرة",
                                    "align": "center",
                                    "size": "lg",
                                    "weight": "bold",
                                    "color": C['text'],
                                    "margin": "md"
                                },
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "cornerRadius": "15px",
                                    "backgroundColor": C['card'],
                                    "paddingAll": "20px",
                                    "margin": "md",
                                    "contents": [
                                        {"type": "text", "text": "1. أسرع\n- أول من يكتب الكلمة أو الدعاء الصحيح يفوز", "size": "sm", "color": C['text'], "wrap": True},
                                        {"type": "text", "text": "2. لعبة\n- إنسان، حيوان، نبات، بلد", "size": "sm", "color": C['text'], "wrap": True, "margin": "md"},
                                        {"type": "text", "text": "3. سلسلة الكلمات\n- كلمة تبدأ بالحرف الأخير من السابقة", "size": "sm", "color": C['text'], "wrap": True, "margin": "md"},
                                        {"type": "text", "text": "4. أغنية\n- تخمين المغني من كلمات الأغنية", "size": "sm", "color": C['text'], "wrap": True, "margin": "md"},
                                        {"type": "text", "text": "5. ضد\n- اعكس الكلمة المعطاة", "size": "sm", "color": C['text'], "wrap": True, "margin": "md"},
                                        {"type": "text", "text": "6. ترتيب\n- ترتيب العناصر حسب المطلوب", "size": "sm", "color": C['text'], "wrap": True, "margin": "md"},
                                        {"type": "text", "text": "7. تكوين كلمات\n- تكوين 3 كلمات من 6 حروف", "size": "sm", "color": C['text'], "wrap": True, "margin": "md"},
                                        {"type": "text", "text": "8. توافق\n- حساب نسبة التوافق بين اسمين", "size": "sm", "color": C['text'], "wrap": True, "margin": "md"},
                                        {"type": "text", "text": "9. Ai (AiChat)\n- محادثة ذكية قصيرة", "size": "sm", "color": C['text'], "wrap": True, "margin": "md"}
                                    ]
                                },
                                {
                                    "type": "text",
                                    "text": "محتوى ترفيهي\nسؤال • منشن • اعتراف • تحدي",
                                    "align": "center",
                                    "size": "md",
                                    "color": C['text2'],
                                    "margin": "lg",
                                    "wrap": True
                                },
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "spacing": "sm",
                                    "margin": "lg",
                                    "contents": [
                                        {"type": "button", "style": "primary", "color": C['cyan'], "action": {"type": "message", "label": "ابدأ", "text": "ابدأ"}},
                                        {"type": "button", "style": "secondary", "color": "#F1F1F1", "action": {"type": "message", "label": "نقاطي", "text": "نقاطي"}},
                                        {"type": "button", "style": "secondary", "color": "#F1F1F1", "action": {"type": "message", "label": "الصدارة", "text": "الصدارة"}}
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
                                {"type": "text", "text": "المساعدة", "weight": "bold", "size": "xxl", "align": "center", "color": C['cyan']},
                                {"type": "text", "text": "الأوامر المتاحة", "align": "center", "size": "md", "color": C['text'], "margin": "md"},
                                {"type": "separator", "color": C['sep'], "margin": "md"},
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "cornerRadius": "15px",
                                    "backgroundColor": C['card'],
                                    "paddingAll": "18px",
                                    "margin": "md",
                                    "contents": [
                                        {"type": "text", "text": "• لمح → تلميح ذكي للسؤال", "size": "sm", "color": C['text'], "wrap": True},
                                        {"type": "text", "text": "• جاوب → يعرض الإجابة ثم ينتقل للسؤال التالي", "size": "sm", "color": C['text'], "wrap": True, "margin": "xs"},
                                        {"type": "text", "text": "• إعادة → يعيد تشغيل اللعبة الحالية", "size": "sm", "color": C['text'], "wrap": True, "margin": "xs"},
                                        {"type": "text", "text": "• إيقاف → ينهي اللعبة الجارية فوراً", "size": "sm", "color": C['text'], "wrap": True, "margin": "xs"},
                                        {"type": "text", "text": "• انضم → يسجل اللاعب في الجولة", "size": "sm", "color": C['text'], "wrap": True, "margin": "xs"},
                                        {"type": "text", "text": "• انسحب → يلغي تسجيل اللاعب", "size": "sm", "color": C['text'], "wrap": True, "margin": "xs"},
                                        {"type": "text", "text": "• نقاطي → عرض نقاطك الحالية", "size": "sm", "color": C['text'], "wrap": True, "margin": "xs"},
                                        {"type": "text", "text": "• الصدارة → عرض أفضل اللاعبين", "size": "sm", "color": C['text'], "wrap": True, "margin": "xs"}
                                    ]
                                },
                                {
                                    "type": "box",
                                    "layout": "horizontal",
                                    "spacing": "sm",
                                    "margin": "lg",
                                    "contents": [
                                        {"type": "button", "style": "secondary", "color": "#F1F1F1", "action": {"type": "message", "label": "نقاطي", "text": "نقاطي"}},
                                        {"type": "button", "style": "secondary", "color": "#F1F1F1", "action": {"type": "message", "label": "الصدارة", "text": "الصدارة"}}
                                    ]
                                },
                                {"type": "text", "text": "© بوت الحوت 2025", "align": "center", "size": "xs", "color": C['text2'], "margin": "md"}
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
    """إنشاء بطاقة لوحة الصدارة"""
    contents = [
        {"type": "text", "text": "🏆 لوحة الصدارة", "weight": "bold", "size": "xl", "color": C['cyan'], "align": "center"},
        {"type": "separator", "color": C['sep'], "margin": "md"}
    ]
    
    for i, row in enumerate(leaderboard[:10], 1):
        emoji = RANK_EMOJIS.get(i, f"{i}.")
        name, points, wins = row[0], row[1], row[2]
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

# معالج Webhook
@app.route("/callback", methods=['POST'])
def callback():
    """معالج webhook من LINE"""
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
        return 'OK', 200
    except InvalidSignatureError:
        logger.error("توقيع غير صحيح")
        abort(400)
    except Exception as e:
        logger.error(f"خطأ في callback: {e}", exc_info=True)
        abort(500)

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """معالج الرسائل النصية"""
    try:
        user_id = event.source.user_id
        text = event.message.text.strip()
        group_id = getattr(event.source, 'group_id', user_id)
        
        # فحص Rate Limit
        if not check_rate_limit(user_id):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="⏳ الرجاء الانتظار قليلاً\nلقد وصلت للحد الأقصى من الطلبات")
            )
            return
        
        # الحصول على معلومات المستخدم
        try:
            profile = line_bot_api.get_profile(user_id)
            user_name = profile.display_name
        except Exception as e:
            logger.warning(f"لم يتم الحصول على الملف الشخصي: {e}")
            user_name = "مستخدم"
        
        # التسجيل التلقائي أو التحديث
        if not is_registered(user_id):
            register_user(user_id, user_name)
            logger.info(f"تم تسجيل مستخدم جديد: {user_name} ({user_id})")
        else:
            update_user_activity(user_id, user_name)
        
        text_lower = text.lower()
        
        # أوامر البداية والترحيب
        if any(cmd in text_lower for cmd in CMDS.get('start', ['ابدأ']) + ['بوت', 'whale', 'مرحبا', 'السلام', 'هلا']):
            flex = FlexSendMessage(alt_text="بوت الحوت", contents=create_welcome_card())
            line_bot_api.reply_message(event.reply_token, flex)
            return
        
        # المساعدة
        if any(cmd in text_lower for cmd in CMDS.get('help', ['مساعدة'])):
            flex = FlexSendMessage(alt_text="المساعدة", contents=create_help_card())
            line_bot_api.reply_message(event.reply_token, flex)
            return
        
        # الإحصائيات
        if any(cmd in text_lower for cmd in CMDS.get('stats', ['نقاطي'])):
            stats = get_user_stats(user_id)
            if stats:
                flex = FlexSendMessage(alt_text="إحصائياتك", contents=create_stats_card(stats))
                line_bot_api.reply_message(event.reply_token, flex)
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="❌ لم يتم العثور على إحصائيات\nاكتب 'ابدأ' لبدء اللعب")
                )
            return
        
        # الصدارة
        if any(cmd in text_lower for cmd in CMDS.get('leaderboard', ['الصدارة'])):
            leaderboard = get_leaderboard()
            if leaderboard:
                flex = FlexSendMessage(alt_text="لوحة الصدارة", contents=create_leaderboard_card(leaderboard))
                line_bot_api.reply_message(event.reply_token, flex)
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="❌ لا توجد بيانات للصدارة حتى الآن")
                )
            return
        
        # إيقاف اللعبة
        if any(cmd in text_lower for cmd in CMDS.get('stop', ['إيقاف'])):
            if group_id in active_games:
                del active_games[group_id]
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="🛑 تم إيقاف اللعبة\nاكتب 'ابدأ' لبدء لعبة جديدة")
                )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="❌ لا توجد لعبة نشطة حالياً")
                )
            return
        
        # بدء لعبة عشوائية
        if text in ['ابدأ', 'start', 'بدء']:
            if group_id in active_games:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="⚠️ يوجد لعبة نشطة حالياً!\nأكمل اللعبة أو اكتب 'إيقاف' لإنهائها")
                )
                return
            
            if GAMES_LOADED:
                # اختيار لعبة عشوائية من الألعاب الأساسية (أول 8)
                game_types = ['اسرع', 'لعبة', 'سلسلة', 'اغنية', 'ضد', 'ترتيب', 'تكوين', 'توافق']
                game_type = random.choice(game_types)
                
                result = start_game(group_id, game_type, user_id, user_name)
                active_games[group_id] = result['game_data']
                
                if result.get('flex'):
                    flex = FlexSendMessage(alt_text=result['message'], contents=result['flex'])
                    line_bot_api.reply_message(event.reply_token, flex)
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=result['message'])
                    )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="❌ الألعاب غير متوفرة حالياً\nيرجى المحاولة لاحقاً")
                )
            return
        
        # إعادة اللعبة
        if any(cmd in text_lower for cmd in CMDS.get('replay', ['إعادة', 'اعادة'])):
            if group_id in active_games and GAMES_LOADED:
                game = active_games[group_id]
                game_type = game.get('type', 'اسرع')
                
                # إعادة تشغيل نفس اللعبة
                result = start_game(group_id, game_type, user_id, user_name)
                active_games[group_id] = result['game_data']
                
                if result.get('flex'):
                    flex = FlexSendMessage(alt_text=result['message'], contents=result['flex'])
                    line_bot_api.reply_message(event.reply_token, flex)
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=result['message'])
                    )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="❌ لا توجد لعبة لإعادتها\nاكتب 'ابدأ' لبدء لعبة جديدة")
                )
            return
        
        # التلميح
        if any(cmd in text_lower for cmd in CMDS.get('hint', ['لمح'])):
            if group_id in active_games and GAMES_LOADED:
                game = active_games[group_id]
                hint_text = get_hint(game)
                
                if hint_text:
                    # خصم نقطة عند طلب التلميح
                    update_points(user_id, POINTS['hint'])
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=hint_text)
                    )
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="❌ التلميح غير متوفر لهذه اللعبة")
                    )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="❌ لا توجد لعبة نشطة حالياً\nاكتب 'ابدأ' لبدء لعبة جديدة")
                )
            return
        
        # عرض الإجابة والانتقال
        if any(cmd in text_lower for cmd in CMDS.get('answer', ['جاوب'])):
            if group_id in active_games and GAMES_LOADED:
                game = active_games[group_id]
                answer_result = show_answer(game, group_id, active_games)
                
                if answer_result.get('flex'):
                    flex = FlexSendMessage(alt_text=answer_result['message'], contents=answer_result['flex'])
                    line_bot_api.reply_message(event.reply_token, flex)
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=answer_result['message'])
                    )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="❌ لا توجد لعبة نشطة حالياً")
                )
            return
        
        # الانضمام للعبة
        if any(cmd in text_lower for cmd in CMDS.get('join', ['انضم'])):
            if group_id in active_games:
                game = active_games[group_id]
                if 'players' not in game:
                    game['players'] = []
                
                if user_id not in game['players']:
                    game['players'].append(user_id)
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=f"✅ تم تسجيلك في اللعبة يا {user_name}!\nعدد اللاعبين: {len(game['players'])}")
                    )
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=f"⚠️ أنت مسجل بالفعل يا {user_name}")
                    )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="❌ لا توجد لعبة نشطة للانضمام إليها\nاكتب 'ابدأ' لبدء لعبة جديدة")
                )
            return
        
        # الانسحاب من اللعبة
        if any(cmd in text_lower for cmd in CMDS.get('leave', ['انسحب'])):
            if group_id in active_games:
                game = active_games[group_id]
                if 'players' in game and user_id in game['players']:
                    game['players'].remove(user_id)
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=f"👋 تم انسحابك من اللعبة يا {user_name}")
                    )
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="⚠️ أنت لست مسجلاً في اللعبة")
                    )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="❌ لا توجد لعبة نشطة حالياً")
                )
            return
        
        # التحقق من الإجابة
        if group_id in active_games and GAMES_LOADED:
            game = active_games[group_id]
            result = check_game_answer(game, text, user_id, user_name, group_id, active_games)
            
            # تحديث النقاط والإحصائيات إذا كانت الإجابة صحيحة
            if result.get('correct'):
                update_points(user_id, POINTS['correct'])
                
                # إذا انتهت اللعبة، تحديث إحصائيات الفوز
                if result.get('game_over'):
                    update_game_stats(user_id, won=True)
            
            # إرسال الرد
            if result.get('flex'):
                flex = FlexSendMessage(alt_text=result.get('message', 'رد من اللعبة'), contents=result['flex'])
                line_bot_api.reply_message(event.reply_token, flex)
            elif result.get('message'):
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=result['message'])
                )
    
    except Exception as e:
        logger.error(f"خطأ في معالجة الرسالة: {e}", exc_info=True)
        try:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌ حدث خطأ، يرجى المحاولة مرة أخرى")
            )
        except Exception as reply_error:
            logger.error(f"فشل إرسال رسالة الخطأ: {reply_error}")

# الصفحة الرئيسية
@app.route("/")
def index():
    """الصفحة الرئيسية لعرض حالة البوت"""
    status_games = "✓ متوفرة" if GAMES_LOADED else "✗ غير متوفرة"
    color_games = "#00FF88" if GAMES_LOADED else "#FF4444"
    
    # التحقق من قاعدة البيانات
    db_status = "✓ متصلة"
    player_count = 0
    total_games = 0
    try:
        result = db_execute('SELECT COUNT(*) FROM players', fetch=True)
        if result:
            player_count = result[0][0]
        
        result2 = db_execute('SELECT SUM(games_played) FROM players', fetch=True)
        if result2 and result2[0][0]:
            total_games = result2[0][0]
        
        db_status = f"✓ متصلة ({player_count} لاعب)"
    except:
        db_status = "✗ غير متصلة"
    
    return f"""
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>بوت الحوت - LINE Bot</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
                background: linear-gradient(135deg, #0A0E27 0%, #1a1f3a 100%);
                color: #E0F2FF;
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }}
            .container {{
                max-width: 700px;
                width: 100%;
            }}
            .card {{
                background: rgba(15, 36, 64, 0.9);
                backdrop-filter: blur(10px);
                border: 2px solid rgba(0, 217, 255, 0.3);
                border-radius: 25px;
                padding: 40px;
                box-shadow: 0 10px 40px rgba(0, 217, 255, 0.2);
            }}
            .logo {{
                width: 120px;
                height: 120px;
                margin: 0 auto 20px;
                display: block;
                border-radius: 50%;
                border: 3px solid #00D9FF;
                box-shadow: 0 0 30px rgba(0, 217, 255, 0.6);
            }}
            h1 {{
                text-align: center;
                color: #00D9FF;
                font-size: 2.5em;
                margin-bottom: 10px;
                text-shadow: 0 0 20px rgba(0, 217, 255, 0.5);
            }}
            .subtitle {{
                text-align: center;
                color: #7FB3D5;
                margin-bottom: 30px;
                font-size: 1.1em;
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
                margin-top: 25px;
            }}
            .stat {{
                background: rgba(0, 217, 255, 0.15);
                border: 1px solid rgba(0, 217, 255, 0.3);
                border-radius: 15px;
                padding: 20px;
                text-align: center;
                transition: transform 0.3s ease;
            }}
            .stat:hover {{
                transform: translateY(-5px);
                box-shadow: 0 5px 20px rgba(0, 217, 255, 0.3);
            }}
            .stat-value {{
                font-size: 2em;
                font-weight: bold;
                color: #00D9FF;
                display: block;
                margin-bottom: 8px;
            }}
            .stat-label {{
                color: #7FB3D5;
                font-size: 0.9em;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                color: #7FB3D5;
                font-size: 0.9em;
            }}
            @keyframes pulse {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.5; }}
            }}
            .indicator {{
                display: inline-block;
                width: 10px;
                height: 10px;
                background: {color_games};
                border-radius: 50%;
                margin-left: 8px;
                animation: pulse 2s infinite;
            }}
            .features {{
                background: rgba(0, 217, 255, 0.1);
                border-radius: 15px;
                padding: 20px;
                margin-top: 25px;
            }}
            .features h3 {{
                color: #00D9FF;
                margin-bottom: 15px;
                text-align: center;
            }}
            .features ul {{
                list-style: none;
                padding: 0;
            }}
            .features li {{
                color: #E0F2FF;
                padding: 8px 0;
                border-bottom: 1px solid rgba(0, 217, 255, 0.2);
            }}
            .features li:last-child {{
                border-bottom: none;
            }}
            .features li::before {{
                content: "✓ ";
                color: #00D9FF;
                font-weight: bold;
                margin-left: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <img src="{LOGO_URL}" alt="بوت الحوت" class="logo">
                <h1>بوت الحوت</h1>
                <p class="subtitle">
                    <span class="indicator"></span>
                    البوت يعمل بنجاح
                </p>
                
                <div class="grid">
                    <div class="stat">
                        <span class="stat-value">9</span>
                        <span class="stat-label">ألعاب متوفرة</span>
                    </div>
                    <div class="stat">
                        <span class="stat-value">{player_count}</span>
                        <span class="stat-label">لاعب مسجل</span>
                    </div>
                    <div class="stat">
                        <span class="stat-value">{total_games}</span>
                        <span class="stat-label">لعبة منتهية</span>
                    </div>
                    <div class="stat">
                        <span class="stat-value">{len(active_games)}</span>
                        <span class="stat-label">لعبة نشطة</span>
                    </div>
                </div>
                
                <div class="features">
                    <h3>المميزات</h3>
                    <ul>
                        <li>8 ألعاب تفاعلية مثيرة</li>
                        <li>نظام نقاط وتصنيفات</li>
                        <li>محادثة AI ذكية</li>
                        <li>محتوى ترفيهي متنوع</li>
                        <li>واجهات Flex Messages جميلة</li>
                        <li>تسجيل تلقائي للاعبين</li>
                    </ul>
                </div>
                
                <div class="grid" style="margin-top: 20px;">
                    <div class="stat">
                        <span class="stat-value"><span class="indicator"></span></span>
                        <span class="stat-label">{status_games}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-value">✓</span>
                        <span class="stat-label">{db_status}</span>
                    </div>
                </div>
                
                <div class="footer">
                    <p>© بوت الحوت 2025 - جميع الحقوق محفوظة</p>
                    <p style="margin-top: 10px; font-size: 0.8em;">
                        Powered by LINE Bot SDK & Flask
                    </p>
                </div>
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
        
        player_count = result[0][0] if db_ok and result else 0
        
        status = {
            "status": "healthy" if db_ok and GAMES_LOADED else "degraded",
            "timestamp": datetime.now().isoformat(),
            "database": {
                "status": "connected" if db_ok else "disconnected",
                "players": player_count
            },
            "games": {
                "status": "loaded" if GAMES_LOADED else "not_loaded",
                "active_sessions": len(active_games)
            },
            "system": {
                "rate_limiter_active_users": len(rate_limiter)
            }
        }
        
        return jsonify(status), 200 if status["status"] == "healthy" else 503
    except Exception as e:
        logger.error(f"فشل فحص الصحة: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/stats")
def stats():
    """إحصائيات عامة عن البوت"""
    try:
        player_count = db_execute('SELECT COUNT(*) FROM players', fetch=True)
        total_games = db_execute('SELECT SUM(games_played) FROM players', fetch=True)
        total_wins = db_execute('SELECT SUM(games_won) FROM players', fetch=True)
        
        return jsonify({
            "total_players": player_count[0][0] if player_count else 0,
            "total_games_played": total_games[0][0] if total_games and total_games[0][0] else 0,
            "total_wins": total_wins[0][0] if total_wins and total_wins[0][0] else 0,
            "active_games": len(active_games),
            "games_loaded": GAMES_LOADED,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"خطأ في الإحصائيات: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/clean", methods=['POST'])
def clean_users():
    """تنظيف المستخدمين غير النشطين (يدوي)"""
    try:
        clean_inactive_users()
        return jsonify({"message": "تم تنظيف المستخدمين غير النشطين"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# معالجة الأخطاء
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"خطأ داخلي في الخادم: {error}")
    return jsonify({"error": "Internal server error"}), 500

# تشغيل التطبيق
if __name__ == "__main__":
    print("=" * 60)
    print("🐋 بوت الحوت - LINE Bot")
    print("=" * 60)
    print(f"{'✓' if GAMES_LOADED else '✗'} الألعاب: {'محملة' if GAMES_LOADED else 'غير محملة'}")
    print(f"✓ قاعدة البيانات: جاهزة")
    print(f"✓ Webhook: جاهز")
    print("=" * 60)
    
    port = int(os.getenv("PORT", 5000))
    print(f"🚀 البوت يعمل على المنفذ {port}")
    print(f"🌐 الصفحة الرئيسية: http://localhost:{port}")
    print(f"❤️ فحص الصحة: http://localhost:{port}/health")
    print(f"📊 الإحصائيات: http://localhost:{port}/stats")
    print("=" * 60)
    print("⚠️ ملاحظة: البوت يرد فقط على المستخدمين المسجلين")
    print("=" * 60)
    
    app.run(host="0.0.0.0", port=port)
