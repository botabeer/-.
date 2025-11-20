# ============================================
# app.py - الملف الرئيسي لبوت الحوت
# ============================================

"""
بوت الحوت - LINE Bot
====================
بوت تفاعلي للألعاب والمحتوى الترفيهي
"""

import os
import sys
import logging
from datetime import datetime
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    FlexSendMessage, QuickReply, QuickReplyButton,
    MessageAction
)

# استيراد الوحدات المخصصة
from config import *
from rules import POINTS, GAME_SETTINGS, GAMES_INFO, COMMANDS, SYSTEM_MESSAGES, GAME_RULES
from style import (
    COLORS, create_welcome_card, create_game_question_card,
    create_result_card, create_leaderboard_card, create_stats_card
)
from games import (
    start_game, get_active_game, stop_game, check_game_answer,
    get_hint, show_answer, get_game_state, GAME_CLASSES
)
from utils import (
    random_choice_from_file, validate_answer, sanitize_input,
    is_valid_user_id, parse_command, normalize_text
)
from init_db import init_database, verify_database

# إعداد السجل
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)
logger = logging.getLogger(__name__)

# إنشاء تطبيق Flask
app = Flask(__name__)

# إعداد LINE Bot API
try:
    line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
    handler = WebhookHandler(LINE_CHANNEL_SECRET)
    logger.info("LINE Bot API initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize LINE Bot API: {e}")
    sys.exit(1)

# تهيئة قاعدة البيانات
try:
    if not verify_database(DATABASE_PATH):
        logger.info("Initializing database...")
        init_database(DATABASE_PATH)
    logger.info("Database ready")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")
    sys.exit(1)


# ============================================
# دوال قاعدة البيانات
# ============================================

import sqlite3

def get_db_connection():
    """الحصول على اتصال بقاعدة البيانات"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_or_create_player(user_id, name):
    """الحصول على أو إنشاء لاعب"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # التحقق من وجود اللاعب
        cursor.execute('SELECT * FROM players WHERE user_id = ?', (user_id,))
        player = cursor.fetchone()
        
        if not player:
            # إنشاء لاعب جديد
            cursor.execute('''
                INSERT INTO players (user_id, name)
                VALUES (?, ?)
            ''', (user_id, name))
            conn.commit()
            logger.info(f"New player created: {name} ({user_id})")
        else:
            # تحديث آخر نشاط
            cursor.execute('''
                UPDATE players 
                SET last_active = CURRENT_TIMESTAMP 
                WHERE user_id = ?
            ''', (user_id,))
            conn.commit()
        
        # الحصول على بيانات اللاعب
        cursor.execute('SELECT * FROM players WHERE user_id = ?', (user_id,))
        return dict(cursor.fetchone())
        
    except Exception as e:
        logger.error(f"Database error in get_or_create_player: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def update_player_points(user_id, points_change):
    """تحديث نقاط اللاعب"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE players 
            SET points = points + ? 
            WHERE user_id = ?
        ''', (points_change, user_id))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating points: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def update_game_stats(user_id, won=False):
    """تحديث إحصائيات الألعاب"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if won:
            cursor.execute('''
                UPDATE players 
                SET games_played = games_played + 1,
                    games_won = games_won + 1
                WHERE user_id = ?
            ''', (user_id,))
        else:
            cursor.execute('''
                UPDATE players 
                SET games_played = games_played + 1
                WHERE user_id = ?
            ''', (user_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating game stats: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def get_leaderboard(limit=10):
    """الحصول على قائمة المتصدرين"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT name, points, 
                   ROW_NUMBER() OVER (ORDER BY points DESC) as rank
            FROM players 
            WHERE points > 0
            ORDER BY points DESC 
            LIMIT ?
        ''', (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        return []
    finally:
        conn.close()


def get_player_stats(user_id):
    """الحصول على إحصائيات اللاعب"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT name, points, games_played, games_won 
            FROM players 
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        return dict(result) if result else None
    except Exception as e:
        logger.error(f"Error getting player stats: {e}")
        return None
    finally:
        conn.close()


# ============================================
# معالجات الأوامر
# ============================================

def handle_start_command(user_id, user_name):
    """معالجة أمر البدء"""
    # التأكد من تسجيل المستخدم
    player = get_or_create_player(user_id, user_name)
    
    # إنشاء رسالة الترحيب
    welcome_flex = FlexSendMessage(
        alt_text="مرحباً بك في بوت الحوت",
        contents=create_welcome_card()
    )
    
    # إنشاء Quick Reply للألعاب
    quick_reply_items = []
    for game_key, game_info in GAMES_INFO.items():
        quick_reply_items.append(
            QuickReplyButton(
                action=MessageAction(
                    label=game_info['name'],
                    text=game_key
                )
            )
        )
    
    quick_reply = QuickReply(items=quick_reply_items[:13])  # حد أقصى 13 عنصر
    
    # رسالة نصية مع Quick Reply
    text_message = TextSendMessage(
        text="اختر لعبة من القائمة:",
        quick_reply=quick_reply
    )
    
    return [welcome_flex, text_message]


def handle_stats_command(user_id):
    """معالجة أمر الإحصائيات"""
    stats = get_player_stats(user_id)
    
    if not stats:
        return [TextSendMessage(text=SYSTEM_MESSAGES['not_registered'])]
    
    stats_flex = FlexSendMessage(
        alt_text="إحصائياتك",
        contents=create_stats_card(
            stats['name'],
            stats['points'],
            stats['games_played'],
            stats['games_won']
        )
    )
    
    return [stats_flex]


def handle_leaderboard_command():
    """معالجة أمر المتصدرين"""
    players = get_leaderboard(10)
    
    if not players:
        return [TextSendMessage(text="لا يوجد لاعبون في القائمة بعد")]
    
    # تحويل البيانات للفورمات المطلوب
    leaderboard_data = [
        (p['name'], p['points'], p['rank']) 
        for p in players
    ]
    
    leaderboard_flex = FlexSendMessage(
        alt_text="قائمة المتصدرين",
        contents=create_leaderboard_card(leaderboard_data)
    )
    
    return [leaderboard_flex]


def handle_help_command():
    """معالجة أمر المساعدة"""
    help_text = f"""مرحباً بك في بوت الحوت

الألعاب المتاحة:
{chr(10).join([f'- {info["name"]}: {info["description"]}' for info in GAMES_INFO.values()])}

{GAME_RULES}

للبدء، اختر لعبة من القائمة أو اكتب اسمها."""
    
    return [TextSendMessage(text=help_text)]


def handle_game_start(user_id, game_key):
    """بدء لعبة جديدة"""
    # التحقق من وجود اللعبة
    if game_key not in GAMES_INFO:
        return [TextSendMessage(text="لعبة غير موجودة")]
    
    game_info = GAMES_INFO[game_key]
    game_class_name = AVAILABLE_GAMES.get(game_key)
    
    if not game_class_name:
        return [TextSendMessage(text="اللعبة غير متاحة حالياً")]
    
    # التحقق من وجود لعبة نشطة
    if get_active_game(user_id):
        return [TextSendMessage(text="يوجد لعبة نشطة بالفعل. استخدم 'إيقاف' لإنهائها أولاً.")]
    
    # بدء اللعبة
    game = start_game(game_class_name, user_id)
    
    if not game:
        return [TextSendMessage(text="فشل بدء اللعبة")]
    
    # الحصول على السؤال الأول
    try:
        question = game.get_current_question()
        
        if not question:
            return [TextSendMessage(text="فشل تحميل السؤال")]
        
        # إنشاء كارد السؤال
        question_flex = FlexSendMessage(
            alt_text=f"{game_info['name']} - السؤال 1",
            contents=create_game_question_card(
                game_info['name'],
                question,
                1,
                game_info['rounds'],
                game_info['supports_hint']
            )
        )
        
        return [question_flex]
        
    except Exception as e:
        logger.error(f"Error starting game: {e}")
        stop_game(user_id)
        return [TextSendMessage(text="حدث خطأ في بدء اللعبة")]


def handle_game_answer(user_id, user_name, answer):
    """معالجة إجابة اللعبة"""
    game = get_active_game(user_id)
    
    if not game:
        return [TextSendMessage(text=SYSTEM_MESSAGES['no_active_game'])]
    
    # التحقق من الإجابة
    result = check_game_answer(user_id, user_id, answer)
    
    if not result:
        return [TextSendMessage(text="فشل التحقق من الإجابة")]
    
    messages = []
    
    # رسالة النتيجة
    if result.get('correct'):
        points_change = POINTS['correct']
        update_player_points(user_id, points_change)
        
        result_flex = FlexSendMessage(
            alt_text="إجابة صحيحة",
            contents=create_result_card(
                "إجابة صحيحة",
                f"أحسنت يا {user_name}",
                points_change,
                True
            )
        )
        messages.append(result_flex)
    else:
        result_message = TextSendMessage(
            text=f"إجابة خاطئة. الإجابة الصحيحة: {result.get('correct_answer', 'غير متوفرة')}"
        )
        messages.append(result_message)
    
    # التحقق من انتهاء اللعبة
    if result.get('game_ended'):
        total_points = result.get('total_points', 0)
        update_game_stats(user_id, won=(total_points > 0))
        
        final_message = TextSendMessage(
            text=f"انتهت اللعبة!\nمجموع نقاطك: {total_points}"
        )
        messages.append(final_message)
        
        # Quick Reply للعب مرة أخرى
        replay_message = TextSendMessage(
            text="هل تريد اللعب مرة أخرى؟",
            quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="نعم", text="إعادة")),
                QuickReplyButton(action=MessageAction(label="لا", text="نقاطي"))
            ])
        )
        messages.append(replay_message)
    else:
        # السؤال التالي
        try:
            next_question = game.get_current_question()
            current_round = result.get('current_round', 1)
            total_rounds = result.get('total_rounds', 5)
            
            question_flex = FlexSendMessage(
                alt_text=f"السؤال {current_round}",
                contents=create_game_question_card(
                    game.name,
                    next_question,
                    current_round,
                    total_rounds,
                    hasattr(game, 'get_hint')
                )
            )
            messages.append(question_flex)
        except Exception as e:
            logger.error(f"Error getting next question: {e}")
    
    return messages


def handle_hint_command(user_id):
    """معالجة أمر التلميح"""
    game = get_active_game(user_id)
    
    if not game:
        return [TextSendMessage(text=SYSTEM_MESSAGES['no_active_game'])]
    
    hint = get_hint(user_id)
    
    if not hint:
        return [TextSendMessage(text="التلميح غير متوفر لهذه اللعبة")]
    
    # خصم نقطة
    update_player_points(user_id, POINTS['hint'])
    
    hint_message = TextSendMessage(text=f"تلميح: {hint}\n(تم خصم نقطة واحدة)")
    
    return [hint_message]


def handle_show_answer_command(user_id):
    """معالجة أمر إظهار الإجابة"""
    game = get_active_game(user_id)
    
    if not game:
        return [TextSendMessage(text=SYSTEM_MESSAGES['no_active_game'])]
    
    answer = show_answer(user_id)
    
    if not answer:
        return [TextSendMessage(text="فشل عرض الإجابة")]
    
    answer_message = TextSendMessage(text=f"الإجابة الصحيحة: {answer}")
    
    # السؤال التالي
    try:
        next_question = game.get_current_question()
        
        if next_question:
            current_state = get_game_state(user_id)
            
            question_flex = FlexSendMessage(
                alt_text="السؤال التالي",
                contents=create_game_question_card(
                    game.name,
                    next_question,
                    current_state.get('current_round', 1),
                    current_state.get('total_rounds', 5),
                    hasattr(game, 'get_hint')
                )
            )
            return [answer_message, question_flex]
        else:
            # انتهت اللعبة
            stop_game(user_id)
            return [answer_message, TextSendMessage(text="انتهت اللعبة!")]
    except Exception as e:
        logger.error(f"Error in show answer: {e}")
        return [answer_message]


def handle_stop_command(user_id):
    """معالجة أمر الإيقاف"""
    if stop_game(user_id):
        return [TextSendMessage(text=SYSTEM_MESSAGES['game_stopped'])]
    else:
        return [TextSendMessage(text=SYSTEM_MESSAGES['no_active_game'])]


def handle_entertainment_command(command):
    """معالجة أوامر المحتوى الترفيهي"""
    file_path = ENTERTAINMENT_COMMANDS.get(command)
    
    if not file_path:
        return [TextSendMessage(text="محتوى غير موجود")]
    
    content = random_choice_from_file(file_path)
    
    if not content:
        return [TextSendMessage(text="فشل تحميل المحتوى")]
    
    return [TextSendMessage(text=content)]


# ============================================
# معالجات LINE
# ============================================

@app.route("/callback", methods=['POST'])
def callback():
    """نقطة استقبال رسائل LINE"""
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature")
        abort(400)
    except Exception as e:
        logger.error(f"Error in callback: {e}")
    
    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """معالجة الرسائل النصية"""
    user_id = event.source.user_id
    message_text = event.message.text.strip()
    
    # تنظيف المدخلات
    message_text = sanitize_input(message_text)
    
    # الحصول على اسم المستخدم
    try:
        profile = line_bot_api.get_profile(user_id)
        user_name = profile.display_name
    except LineBotApiError:
        user_name = "مستخدم"
    
    logger.info(f"Message from {user_name} ({user_id}): {message_text}")
    
    # تحديد نوع الأمر
    messages = []
    
    # أوامر البدء
    if any(cmd in message_text for cmd in COMMANDS['start']):
        messages = handle_start_command(user_id, user_name)
    
    # أوامر المساعدة
    elif any(cmd in message_text for cmd in COMMANDS['help']):
        messages = handle_help_command()
    
    # أوامر الإحصائيات
    elif any(cmd in message_text for cmd in COMMANDS['stats']):
        messages = handle_stats_command(user_id)
    
    # أوامر المتصدرين
    elif any(cmd in message_text for cmd in COMMANDS['leaderboard']):
        messages = handle_leaderboard_command()
    
    # أوامر الإيقاف
    elif any(cmd in message_text for cmd in COMMANDS['stop']):
        messages = handle_stop_command(user_id)
    
    # أوامر التلميح
    elif any(cmd in message_text for cmd in COMMANDS['hint']):
        messages = handle_hint_command(user_id)
    
    # أوامر الإجابة
    elif any(cmd in message_text for cmd in COMMANDS['answer']):
        messages = handle_show_answer_command(user_id)
    
    # بدء لعبة جديدة
    elif message_text in AVAILABLE_GAMES:
        messages = handle_game_start(user_id, message_text)
    
    # محتوى ترفيهي
    elif message_text in ENTERTAINMENT_COMMANDS:
        messages = handle_entertainment_command(message_text)
    
    # إجابة على سؤال في لعبة نشطة
    elif get_active_game(user_id):
        messages = handle_game_answer(user_id, user_name, message_text)
    
    # أمر غير معروف
    else:
        messages = [TextSendMessage(text=SYSTEM_MESSAGES['invalid_command'])]
    
    # إرسال الرسائل
    try:
        if messages:
            line_bot_api.reply_message(event.reply_token, messages)
    except LineBotApiError as e:
        logger.error(f"Error sending message: {e}")


# ============================================
# نقاط النهاية الإضافية
# ============================================

@app.route("/", methods=['GET'])
def home():
    """الصفحة الرئيسية"""
    return """
    <html>
        <head>
            <title>بوت الحوت</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background: #0A0E27;
                    color: #E0F2FF;
                    text-align: center;
                    padding: 50px;
                }
                h1 { color: #00D9FF; }
            </style>
        </head>
        <body>
            <h1>🐋 بوت الحوت</h1>
            <p>البوت يعمل بنجاح</p>
            <p>أضف البوت على LINE لبدء اللعب</p>
        </body>
    </html>
    """


@app.route("/health", methods=['GET'])
def health():
    """فحص صحة الخادم"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": verify_database(DATABASE_PATH)
    }


# ============================================
# تشغيل التطبيق
# ============================================

if __name__ == "__main__":
    logger.info(f"Starting Whale Bot on port {PORT}")
    app.run(host=HOST, port=PORT, debug=DEBUG)
