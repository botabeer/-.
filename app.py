"""
═══════════════════════════════════════════════════════════════
▪️ بوت الحوت - نظام ألعاب تفاعلية على LINE
═══════════════════════════════════════════════════════════════
النسخة: 2.1.0
التطوير: فريق بوت الحوت
الحقوق: © 2025 بوت الحوت - جميع الحقوق محفوظة
═══════════════════════════════════════════════════════════════
"""

from flask import Flask, request, abort, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
import os
import sys
import logging
from datetime import datetime
from functools import wraps

# استيراد المكونات
from config import config
from database import db_manager
from cache import names_cache, stats_cache, leaderboard_cache
from user_manager import UserManager
from game_manager import GameManager
from cards import (
    get_welcome_card, get_help_card, get_stats_card, 
    get_leaderboard_card, get_registration_card, get_withdrawal_card,
    get_quick_reply
)
from utils import safe_text, get_profile_safe, check_rate, load_file
from cleanup import cleanup_manager

# ═══════════════════════════════════════════════════════════════
# إعدادات النظام
# ═══════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger("whale-bot")

# طباعة معلومات الحقوق
print("\n" + "═"*65)
print("▪️ بوت الحوت - نظام ألعاب تفاعلية على LINE")
print("═"*65)
print("النسخة: 2.1.0 (محسّنة)")
print("© 2025 بوت الحوت - جميع الحقوق محفوظة")
print("═"*65 + "\n")

# ═══════════════════════════════════════════════════════════════
# التحقق من الإعدادات
# ═══════════════════════════════════════════════════════════════
if not config.validate():
    logger.critical("فشل في تحميل الإعدادات الأساسية")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════
# تهيئة قاعدة البيانات
# ═══════════════════════════════════════════════════════════════
if not db_manager.init_database():
    logger.critical("فشل في تهيئة قاعدة البيانات")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════
# استيراد الألعاب
# ═══════════════════════════════════════════════════════════════
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'games'))

# استيراد الألعاب
SongGame = HumanAnimalPlantGame = ChainWordsGame = FastTypingGame = None
OppositeGame = LettersWordsGame = DifferencesGame = CompatibilityGame = None

try:
    from song_game import SongGame
    from human_animal_plant_game import HumanAnimalPlantGame
    from chain_words_game import ChainWordsGame
    from fast_typing_game import FastTypingGame
    from opposite_game import OppositeGame
    from letters_words_game import LettersWordsGame
    from differences_game import DifferencesGame
    from compatibility_game import CompatibilityGame
    logger.info("تم استيراد جميع الألعاب بنجاح")
except ImportError as e:
    logger.error(f"خطأ في استيراد الألعاب: {e}")

# ═══════════════════════════════════════════════════════════════
# Flask و LINE Bot
# ═══════════════════════════════════════════════════════════════
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['JSON_SORT_KEYS'] = False

line_bot_api = LineBotApi(config.line_token) if config.line_token else None
handler = WebhookHandler(config.line_secret) if config.line_secret else None

# البيانات المشتركة
from collections import defaultdict
from threading import Lock

active_games = {}
registered_players = set()
user_message_count = defaultdict(lambda: {'count': 0, 'reset_time': datetime.now()})

games_lock = Lock()
players_lock = Lock()

# تحميل المحتوى
QUESTIONS = load_file('questions.txt')
CHALLENGES = load_file('challenges.txt')
CONFESSIONS = load_file('confessions.txt')
MENTIONS = load_file('more_questions.txt')

# ═══════════════════════════════════════════════════════════════
# Decorators
# ═══════════════════════════════════════════════════════════════
def require_admin_token(f):
    """تتطلب توكن المسؤول"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('X-Admin-Token', '')
        if not token or token != config.admin_token:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def verify_line_signature(f):
    """التحقق من توقيع LINE"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not handler:
            abort(500)
        
        signature = request.headers.get('X-Line-Signature', '')
        body = request.get_data(as_text=True)
        
        try:
            handler.parser.parse(body, signature)
        except InvalidSignatureError:
            logger.error("توقيع غير صالح")
            abort(400)
        
        return f(*args, **kwargs)
    return decorated_function

# ═══════════════════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════════════════
@app.route("/", methods=['GET'])
def home():
    """الصفحة الرئيسية"""
    games_status = []
    if SongGame: games_status.append("أغنية")
    if HumanAnimalPlantGame: games_status.append("لعبة")
    if ChainWordsGame: games_status.append("سلسلة")
    if FastTypingGame: games_status.append("أسرع")
    if OppositeGame: games_status.append("ضد")
    if LettersWordsGame: games_status.append("تكوين")
    if DifferencesGame: games_status.append("اختلاف")
    if CompatibilityGame: games_status.append("توافق")
    
    from gemini_ai import USE_AI
    
    return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>بوت الحوت</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .container {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 24px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
            max-width: 600px;
            width: 100%;
            animation: fadeIn 0.6s ease;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        h1 {{
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 8px;
            text-align: center;
            font-weight: 700;
        }}
        .subtitle {{
            color: #64748b;
            font-size: 1em;
            text-align: center;
            margin-bottom: 30px;
        }}
        .status {{
            background: #f8fafc;
            border-radius: 16px;
            padding: 24px;
            margin: 20px 0;
        }}
        .status-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 0;
            border-bottom: 1px solid #e2e8f0;
        }}
        .status-item:last-child {{
            border-bottom: none;
        }}
        .label {{
            color: #64748b;
            font-size: 0.95em;
            font-weight: 500;
        }}
        .value {{
            color: #1e293b;
            font-weight: 700;
            font-size: 1.1em;
        }}
        .badge {{
            display: inline-block;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        .badge.success {{
            background: #dcfce7;
            color: #16a34a;
        }}
        .badge.warning {{
            background: #fef3c7;
            color: #d97706;
        }}
        .games-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 12px;
            margin-top: 20px;
        }}
        .game-card {{
            background: white;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            padding: 16px;
            text-align: center;
            color: #667eea;
            font-weight: 600;
            font-size: 0.9em;
            transition: all 0.3s ease;
        }}
        .game-card:hover {{
            transform: translateY(-4px);
            border-color: #667eea;
            box-shadow: 0 8px 24px rgba(102, 126, 234, 0.2);
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #94a3b8;
            font-size: 0.85em;
        }}
        .pulse {{
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.7; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🐋 بوت الحوت</h1>
        <div class="subtitle">نظام ألعاب تفاعلية متقدم</div>
        
        <div class="status">
            <div class="status-item">
                <span class="label">حالة الخادم</span>
                <span class="badge success pulse">يعمل</span>
            </div>
            <div class="status-item">
                <span class="label">الذكاء الاصطناعي</span>
                <span class="badge {'success' if USE_AI else 'warning'}">{'مفعّل' if USE_AI else 'معطّل'}</span>
            </div>
            <div class="status-item">
                <span class="label">اللاعبون المسجلون</span>
                <span class="value">{len(registered_players)}</span>
            </div>
            <div class="status-item">
                <span class="label">الألعاب النشطة</span>
                <span class="value">{len(active_games)}</span>
            </div>
            <div class="status-item">
                <span class="label">الألعاب المتوفرة</span>
                <span class="value">{len(games_status)}/8</span>
            </div>
        </div>
        
        <div class="games-grid">
            {''.join([f'<div class="game-card">▪️ {game}</div>' for game in games_status])}
        </div>
        
        <div class="footer">
            بوت الحوت © 2025 | النسخة 2.1.0
        </div>
    </div>
</body>
</html>"""

@app.route("/health", methods=['GET'])
def health():
    """فحص صحة الخادم"""
    try:
        db_status = "connected" if db_manager.get_connection() else "disconnected"
    except:
        db_status = "error"
    
    from gemini_ai import USE_AI
    
    return jsonify({
        "status": "healthy",
        "version": "2.1.0",
        "timestamp": datetime.now().isoformat(),
        "active_games": len(active_games),
        "registered_players": len(registered_players),
        "cached_names": len(names_cache.cache),
        "ai_enabled": USE_AI,
        "database": db_status
    }), 200

@app.route("/reload_content", methods=['POST'])
@require_admin_token
def reload_content():
    """إعادة تحميل المحتوى"""
    global QUESTIONS, CHALLENGES, CONFESSIONS, MENTIONS
    
    try:
        QUESTIONS = load_file('questions.txt')
        CHALLENGES = load_file('challenges.txt')
        CONFESSIONS = load_file('confessions.txt')
        MENTIONS = load_file('more_questions.txt')
        
        return jsonify({
            "status": "reloaded",
            "counts": {
                "questions": len(QUESTIONS),
                "challenges": len(CHALLENGES),
                "confessions": len(CONFESSIONS),
                "mentions": len(MENTIONS)
            }
        }), 200
    except Exception as e:
        logger.error(f"خطأ في إعادة التحميل: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/stats", methods=['GET'])
def get_system_stats():
    """إحصائيات النظام"""
    try:
        total_users = db_manager.execute_query('SELECT COUNT(*) as count FROM players')[0]['count']
        total_games_played = db_manager.execute_query('SELECT SUM(games_played) as total FROM players')[0]['total'] or 0
        
        return jsonify({
            "total_users": total_users,
            "total_games_played": total_games_played,
            "active_games": len(active_games),
            "registered_players": len(registered_players),
            "cache_sizes": {
                "names": len(names_cache.cache),
                "stats": len(stats_cache.cache),
                "leaderboard": len(leaderboard_cache.cache)
            }
        }), 200
    except Exception as e:
        logger.error(f"خطأ في جلب الإحصائيات: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/callback", methods=['POST'])
@verify_line_signature
def callback():
    """معالجة طلبات LINE"""
    if not handler or not line_bot_api:
        logger.error("LINE Bot غير مهيأ بشكل صحيح")
        abort(500)
    
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("توقيع غير صالح")
        abort(400)
    except Exception as e:
        logger.error(f"خطأ في معالجة webhook: {e}")
    
    return 'OK'

# ═══════════════════════════════════════════════════════════════
# معالج الرسائل
# ═══════════════════════════════════════════════════════════════
from message_handler import handle_text_message

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """معالجة الرسائل الواردة"""
    try:
        # استدعاء المعالج الرئيسي
        handle_text_message(
            event=event,
            line_bot_api=line_bot_api,
            active_games=active_games,
            registered_players=registered_players,
            user_message_count=user_message_count,
            games_lock=games_lock,
            players_lock=players_lock,
            QUESTIONS=QUESTIONS,
            CHALLENGES=CHALLENGES,
            CONFESSIONS=CONFESSIONS,
            MENTIONS=MENTIONS,
            games_map={
                'أغنية': (SongGame, 'أغنية'),
                'لعبة': (HumanAnimalPlantGame, 'لعبة'),
                'سلسلة': (ChainWordsGame, 'سلسلة'),
                'أسرع': (FastTypingGame, 'أسرع'),
                'ضد': (OppositeGame, 'ضد'),
                'تكوين': (LettersWordsGame, 'تكوين'),
                'اختلاف': (DifferencesGame, 'اختلاف'),
                'توافق': (CompatibilityGame, 'توافق')
            }
        )
    except Exception as e:
        logger.error(f"خطأ في معالجة الرسالة: {e}", exc_info=True)

# ═══════════════════════════════════════════════════════════════
# معالج الأخطاء
# ═══════════════════════════════════════════════════════════════
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "الصفحة غير موجودة"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"خطأ داخلي في الخادم: {error}")
    return jsonify({"error": "خطأ داخلي في الخادم"}), 500

@app.errorhandler(Exception)
def handle_exception(error):
    logger.error(f"خطأ غير متوقع: {error}", exc_info=True)
    return 'OK', 200

# ═══════════════════════════════════════════════════════════════
# التشغيل
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    
    # بدء التنظيف التلقائي
    cleanup_manager.start()
    
    # طباعة معلومات البدء
    print("\n" + "="*60)
    print("بوت الحوت جاهز للعمل")
    print(f"المنفذ: {port}")
    print(f"الألعاب المتوفرة: {sum([1 for g in [SongGame, HumanAnimalPlantGame, ChainWordsGame, FastTypingGame, OppositeGame, LettersWordsGame, DifferencesGame, CompatibilityGame] if g])}/8")
    print("="*60 + "\n")
    
    try:
        logger.info(f"بدء الخادم على المنفذ {port}")
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            threaded=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        logger.info("تم إيقاف الخادم بواسطة المستخدم")
        cleanup_manager.stop()
        db_manager.close_connection()
    except Exception as e:
        logger.critical(f"فشل في تشغيل الخادم: {e}")
        sys.exit(1)
