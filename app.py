from flask import Flask, request, abort, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage
import os, sys, logging
from datetime import datetime
from functools import wraps
from collections import defaultdict
from threading import Lock

# استيراد المكونات الأساسية
from config import config
from database import db_manager
from cache import names_cache, stats_cache, leaderboard_cache
from managers import UserManager, GameManager, cleanup_manager
from ui import (
    get_welcome_card, get_help_card, get_stats_card,
    get_leaderboard_card, get_registration_card, get_withdrawal_card,
    get_quick_reply
)
from utils import safe_text, get_profile_safe, check_rate, load_file
from handlers import handle_text_message

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler('bot.log', encoding='utf-8')]
)
logger = logging.getLogger("whale-bot")

print("\n" + "═"*65)
print("بوت الحوت - نظام ألعاب تفاعلية على LINE")
print("═"*65)
print("النسخة: 2.1.0 (محسّنة)")
print("© 2025 بوت الحوت")
print("═"*65 + "\n")

# التحقق من الإعدادات
if not config.validate():
    logger.critical("إعدادات غير صحيحة")
    sys.exit(1)

# تهيئة قاعدة البيانات
if not db_manager.init_database():
    logger.critical("فشل تهيئة قاعدة البيانات")
    sys.exit(1)

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
    logger.info("تم استيراد جميع الألعاب")
except Exception as e:
    logger.error(f"خطأ استيراد الألعاب: {e}")

# Flask و LINE Bot
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['JSON_SORT_KEYS'] = False

line_bot_api = LineBotApi(config.line_token) if config.line_token else None
handler = WebhookHandler(config.line_secret) if config.line_secret else None

if not line_bot_api or not handler:
    logger.critical("فشل تهيئة LINE Bot API")
    sys.exit(1)
logger.info("LINE Bot API جاهز")

# البيانات المشتركة
active_games = {}
registered_players = set()
user_message_count = defaultdict(lambda: {'count': 0, 'reset_time': datetime.now()})

games_lock = Lock()
players_lock = Lock()

QUESTIONS = load_file('questions.txt')
CHALLENGES = load_file('challenges.txt')
CONFESSIONS = load_file('confessions.txt')
MENTIONS = load_file('more_questions.txt')

logger.info(f"محتوى التحميل: {len(QUESTIONS)} سؤال، {len(CHALLENGES)} تحدي، {len(CONFESSIONS)} اعتراف، {len(MENTIONS)} منشن")

# Decorators
def require_admin_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-Admin-Token', '')
        if token != config.admin_token:
            abort(403)
        return f(*args, **kwargs)
    return decorated

def verify_line_signature(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        signature = request.headers.get('X-Line-Signature', '')
        body = request.get_data(as_text=True)
        try:
            handler.parser.parse(body, signature)
        except InvalidSignatureError:
            abort(400)
        return f(*args, **kwargs)
    return decorated

# Routes
@app.route("/", methods=['GET'])
def home():
    games_status = [g for g, cls in [
        ('أغنية', SongGame), ('لعبة', HumanAnimalPlantGame), ('سلسلة', ChainWordsGame),
        ('أسرع', FastTypingGame), ('ضد', OppositeGame), ('تكوين', LettersWordsGame),
        ('اختلاف', DifferencesGame), ('توافق', CompatibilityGame)
    ] if cls]
    from ai import USE_AI
    return f"<h1>بوت الحوت</h1><p>الألعاب المتوفرة: {len(games_status)}/8</p>"

@app.route("/health", methods=['GET'])
def health():
    from ai import USE_AI
    try:
        db_status = "connected" if db_manager.get_connection() else "disconnected"
    except:
        db_status = "error"
    return jsonify({
        "status": "healthy",
        "version": "2.1.0",
        "active_games": len(active_games),
        "registered_players": len(registered_players),
        "cached_names": len(names_cache.cache),
        "ai_enabled": USE_AI,
        "database": db_status
    })

@app.route("/reload_content", methods=['POST'])
@require_admin_token
def reload_content():
    global QUESTIONS, CHALLENGES, CONFESSIONS, MENTIONS
    try:
        QUESTIONS = load_file('questions.txt')
        CHALLENGES = load_file('challenges.txt')
        CONFESSIONS = load_file('confessions.txt')
        MENTIONS = load_file('more_questions.txt')
        return jsonify({"status": "reloaded"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/callback", methods=['POST'])
@verify_line_signature
def callback():
    body = request.get_data(as_text=True)
    signature = request.headers.get('X-Line-Signature', '')
    try:
        handler.handle(body, signature)
    except Exception as e:
        logger.error(f"خطأ في webhook: {e}")
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    handle_text_message(
        event, line_bot_api, active_games, registered_players, user_message_count,
        games_lock, players_lock, QUESTIONS, CHALLENGES, CONFESSIONS, MENTIONS,
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

# معالج الأخطاء
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

# التشغيل
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    cleanup_manager.start(active_games, games_lock)
    try:
        logger.info(f"بدء الخادم على المنفذ {port}")
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("تم إيقاف الخادم بواسطة المستخدم")
        cleanup_manager.stop()
        db_manager.close_connection()
    except Exception as e:
        logger.critical(f"فشل تشغيل الخادم: {e}")
        sys.exit(1)
