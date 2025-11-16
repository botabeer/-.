from flask import Flask, request, abort, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
import os
import sys
import logging
from datetime import datetime
from functools import wraps
from collections import defaultdict
from threading import Lock

# إضافة مجلد src للمسار للتأكد من استدعاء الحزم
sys.path.insert(0, os.path.dirname(__file__))

# استيراد المكونات
from config import config
from database import db_manager
from cache import names_cache, stats_cache, leaderboard_cache

# استدعاء managers بشكل صحيح
from managers.user_manager import UserManager
from managers.game_manager import GameManager
from managers.cleanup_manager import cleanup_manager

from ui import (
    get_welcome_card, get_help_card, get_stats_card, 
    get_leaderboard_card, get_registration_card, get_withdrawal_card,
    get_quick_reply
)
from utils import safe_text, get_profile_safe, check_rate, load_file
from handlers.message_handler import handle_text_message

# ═══════════════════════════════════════════════════════════════
# إعدادات النظام
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger("whale-bot")

# ═══════════════════════════════════════════════════════════════
# التحقق من الإعدادات
if not config.validate():
    logger.critical("فشل في تحميل الإعدادات الأساسية")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════
# تهيئة قاعدة البيانات
if not db_manager.init_database():
    logger.critical("فشل في تهيئة قاعدة البيانات")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════
# استيراد الألعاب
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'games'))

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
    logger.info("✅ تم استيراد جميع الألعاب بنجاح")
except ImportError as e:
    logger.error(f"❌ خطأ في استيراد الألعاب: {e}")
except Exception as e:
    logger.error(f"❌ خطأ غير متوقع في استيراد الألعاب: {e}")

# ═══════════════════════════════════════════════════════════════
# Flask و LINE Bot
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['JSON_SORT_KEYS'] = False

line_bot_api = LineBotApi(config.line_token) if config.line_token else None
handler = WebhookHandler(config.line_secret) if config.line_secret else None

if not line_bot_api or not handler:
    logger.critical("فشل في تهيئة LINE Bot API")
    sys.exit(1)

logger.info("✅ LINE Bot API جاهز")

# ═══════════════════════════════════════════════════════════════
# البيانات المشتركة
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

logger.info(f"📄 المحتوى: {len(QUESTIONS)} سؤال، {len(CHALLENGES)} تحدي، {len(CONFESSIONS)} اعتراف، {len(MENTIONS)} منشن")

# ═══════════════════════════════════════════════════════════════
# Decorators
def require_admin_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('X-Admin-Token', '')
        if not token or token != config.admin_token:
            logger.warning("⚠️ محاولة وصول غير مصرح بها للـ Admin API")
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def verify_line_signature(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not handler:
            abort(500)
        signature = request.headers.get('X-Line-Signature', '')
        body = request.get_data(as_text=True)
        try:
            handler.parser.parse(body, signature)
        except InvalidSignatureError:
            logger.error("❌ توقيع LINE غير صالح")
            abort(400)
        return f(*args, **kwargs)
    return decorated_function

# ═══════════════════════════════════════════════════════════════
# Routes
@app.route("/", methods=['GET'])
def home():
    games_status = []
    if SongGame: games_status.append("أغنية")
    if HumanAnimalPlantGame: games_status.append("لعبة")
    if ChainWordsGame: games_status.append("سلسلة")
    if FastTypingGame: games_status.append("أسرع")
    if OppositeGame: games_status.append("ضد")
    if LettersWordsGame: games_status.append("تكوين")
    if DifferencesGame: games_status.append("اختلاف")
    if CompatibilityGame: games_status.append("توافق")
    
    from ai import USE_AI
    
    return f"بوت الحوت: الألعاب المتاحة: {', '.join(games_status)} - الذكاء الاصطناعي: {'مفعل' if USE_AI else 'معطل'}"

@app.route("/health", methods=['GET'])
def health():
    try:
        db_status = "connected" if db_manager.get_connection() else "disconnected"
    except:
        db_status = "error"
    from ai import USE_AI
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

@app.route("/callback", methods=['POST'])
@verify_line_signature
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    except Exception as e:
        logger.error(f"خطأ في معالجة webhook: {e}")
    return 'OK'

# ═══════════════════════════════════════════════════════════════
# معالجة الرسائل
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
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
# التشغيل
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    cleanup_manager.start(active_games, games_lock)
    logger.info(f"بوت الحوت جاهز على المنفذ {port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True, use_reloader=False)
