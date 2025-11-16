from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
import os, sys, sqlite3, threading, time, random, re, logging
from datetime import datetime, timedelta
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger("bot")

LINE_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'YOUR_TOKEN')
LINE_SECRET = os.getenv('LINE_CHANNEL_SECRET', 'YOUR_SECRET')

line_bot_api = LineBotApi(LINE_TOKEN)
handler = WebhookHandler(LINE_SECRET)

USE_AI = False
ask_gemini = None

try:
    import google.generativeai as genai
    GEMINI_KEYS = [k for k in [os.getenv(f'GEMINI_API_KEY_{i}', '') for i in ['', '1', '2', '3']] if k]
    if GEMINI_KEYS:
        genai.configure(api_key=GEMINI_KEYS[0])
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        USE_AI = True
        logger.info(f"Gemini AI جاهز ({len(GEMINI_KEYS)} مفاتيح)")
        def ask_gemini(prompt, max_retries=2):
            for attempt in range(max_retries):
                try:
                    return model.generate_content(prompt).text.strip()
                except Exception as e:
                    logger.error(f"Gemini خطأ: {e}")
            return None
except:
    pass

GAMES = {}
GAME_CLASSES = {
    'song': ('song_game', 'SongGame'),
    'human_animal': ('human_animal_plant_game', 'HumanAnimalPlantGame'),
    'chain': ('chain_words_game', 'ChainWordsGame'),
    'fast': ('fast_typing_game', 'FastTypingGame'),
    'opposite': ('opposite_game', 'OppositeGame'),
    'letters': ('letters_words_game', 'LettersWordsGame'),
    'differences': ('differences_game', 'DifferencesGame'),
    'compatibility': ('compatibility_game', 'CompatibilityGame'),
    'arrange': ('arrange_game', 'ArrangeGame'),
    'word_game': ('word_game', 'WordGame'),
    'color_game': ('color_game', 'ColorGame')
}

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'games'))

for key, (module_name, class_name) in GAME_CLASSES.items():
    try:
        module = __import__(module_name)
        GAMES[key] = getattr(module, class_name)
        logger.info(f"تم تحميل {class_name}")
    except Exception as e:
        logger.error(f"فشل تحميل {module_name}: {e}")

logger.info(f"تم تحميل {len(GAMES)}/11 ألعاب")

app = Flask(__name__)

DB_NAME = 'game_scores.db'

def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            display_name TEXT,
            total_points INTEGER DEFAULT 0,
            games_played INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            last_active TEXT,
            registered_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS game_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            game_type TEXT,
            points INTEGER,
            won INTEGER,
            played_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_points ON users(total_points DESC)')
        conn.commit()
        conn.close()
        logger.info("قاعدة البيانات جاهزة")
    except Exception as e:
        logger.error(f"فشل إنشاء قاعدة البيانات: {e}")

init_db()

active_games = {}
registered_players = set()
user_names_cache = {}
rate_limit = defaultdict(lambda: {'count': 0, 'reset': datetime.now()})
games_lock = threading.Lock()
players_lock = threading.Lock()

QUESTIONS = []
CHALLENGES = []
CONFESSIONS = []
MENTIONS = []
question_index = {'q': 0, 'ch': 0, 'co': 0, 'm': 0}

def load_text_file(filename):
    try:
        path = os.path.join('games', filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        return []
    except Exception as e:
        logger.error(f"فشل قراءة {filename}: {e}")
        return []

QUESTIONS = load_text_file('questions.txt')
CHALLENGES = load_text_file('challenges.txt')
CONFESSIONS = load_text_file('confessions.txt')
MENTIONS = load_text_file('more_questions.txt')

def normalize_text(text):
    if not text: return ""
    text = text.strip().lower()
    text = text.replace('أ','ا').replace('إ','ا').replace('آ','ا')
    text = text.replace('ؤ','و').replace('ئ','ي').replace('ء','')
    text = text.replace('ة','ه').replace('ى','ي')
    text = re.sub(r'[\u064B-\u065F]', '', text)
    return re.sub(r'\s+', '', text)

def check_rate_limit(user_id, max_msg=30, window=60):
    now = datetime.now()
    data = rate_limit[user_id]
    if now - data['reset'] > timedelta(seconds=window):
        data['count'] = 0
        data['reset'] = now
    if data['count'] >= max_msg:
        return False
    data['count'] += 1
    return True

def get_user_profile_safe(user_id):
    if user_id in user_names_cache:
        return user_names_cache[user_id]
    try:
        profile = line_bot_api.get_profile(user_id)
        name = profile.display_name.strip() if profile.display_name else f"لاعب_{user_id[-4:]}"
        user_names_cache[user_id] = name
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT display_name FROM users WHERE user_id = ?', (user_id,))
        row = c.fetchone()
        if row and row['display_name'] != name:
            c.execute('UPDATE users SET display_name = ?, last_active = ? WHERE user_id = ?', (name, datetime.now().isoformat(), user_id))
            conn.commit()
        elif not row:
            c.execute('INSERT INTO users (user_id, display_name, last_active) VALUES (?, ?, ?)', (user_id, name, datetime.now().isoformat()))
            conn.commit()
        conn.close()
        return name
    except LineBotApiError as e:
        name = f"لاعب_{user_id[-4:]}"
        user_names_cache[user_id] = name
        return name
    except Exception as e:
        logger.error(f"خطأ: {e}")
        return f"لاعب_{user_id[-4:]}"

def update_points(user_id, name, points, won=False, game_type=""):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = c.fetchone()
        if user:
            c.execute('''UPDATE users SET total_points = ?, games_played = ?, wins = ?, 
                         last_active = ?, display_name = ? WHERE user_id = ?''',
                      (user['total_points'] + points, user['games_played'] + 1,
                       user['wins'] + (1 if won else 0), datetime.now().isoformat(), name, user_id))
        else:
            c.execute('''INSERT INTO users (user_id, display_name, total_points, games_played, wins, last_active) 
                         VALUES (?, ?, ?, 1, ?, ?)''',
                      (user_id, name, points, 1 if won else 0, datetime.now().isoformat()))
        if game_type:
            c.execute('INSERT INTO game_history (user_id, game_type, points, won) VALUES (?, ?, ?, ?)',
                      (user_id, game_type, points, 1 if won else 0))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"فشل تحديث النقاط: {e}")
        return False

def get_stats(user_id):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = c.fetchone()
        conn.close()
        return user
    except Exception as e:
        logger.error(f"فشل جلب الإحصائيات: {e}")
        return None

def get_leaderboard(limit=10):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT display_name, total_points, games_played, wins FROM users ORDER BY total_points DESC LIMIT ?', (limit,))
        leaders = c.fetchall()
        conn.close()
        return leaders
    except Exception as e:
        logger.error(f"فشل جلب الصدارة: {e}")
        return []

def get_welcome_card():
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "بوت الحوت", "size": "xxl", "weight": "bold", "color": "#1C1C1E", "align": "center"},
                {"type": "text", "text": "بوت ألعاب تفاعلي للمجموعات", "size": "sm", "color": "#8E8E93", "align": "center", "margin": "md", "wrap": True},
                {"type": "separator", "margin": "xl", "color": "#E5E5EA"},
                {"type": "text", "text": "الألعاب المتوفرة", "size": "md", "weight": "bold", "color": "#1C1C1E", "margin": "xl"},
                {"type": "box", "layout": "vertical", "contents": [
                    {"type": "text", "text": "▪️ أغنية - خمن اسم المغني", "size": "sm", "color": "#3C3C43", "margin": "md", "wrap": True},
                    {"type": "text", "text": "▪️ ضد - اكتب عكس الكلمة", "size": "sm", "color": "#3C3C43", "margin": "sm", "wrap": True},
                    {"type": "text", "text": "▪️ أسرع - اكتب الكلمة بسرعة", "size": "sm", "color": "#3C3C43", "margin": "sm", "wrap": True},
                    {"type": "text", "text": "▪️ سلسلة - كون سلسلة كلمات", "size": "sm", "color": "#3C3C43", "margin": "sm", "wrap": True},
                    {"type": "text", "text": "▪️ لعبة - إنسان حيوان نبات جماد بلد", "size": "sm", "color": "#3C3C43", "margin": "sm", "wrap": True},
                    {"type": "text", "text": "▪️ تكوين - كون كلمات من حروف", "size": "sm", "color": "#3C3C43", "margin": "sm", "wrap": True},
                    {"type": "text", "text": "▪️ ترتيب - رتب الحروف لتكوين كلمة", "size": "sm", "color": "#3C3C43", "margin": "sm", "wrap": True},
                    {"type": "text", "text": "▪️ كلمة - احزر الكلمة المخفية", "size": "sm", "color": "#3C3C43", "margin": "sm", "wrap": True},
                    {"type": "text", "text": "▪️ لون - احزر اللون", "size": "sm", "color": "#3C3C43", "margin": "sm", "wrap": True}
                ], "backgroundColor": "#F2F2F7", "cornerRadius": "12px", "paddingAll": "16px", "margin": "md"},
                {"type": "text", "text": "ألعاب تسلية بدون نقاط", "size": "md", "weight": "bold", "color": "#1C1C1E", "margin": "xl"},
                {"type": "box", "layout": "vertical", "contents": [
                    {"type": "text", "text": "▪️ اختلاف - ابحث عن الاختلافات", "size": "sm", "color": "#3C3C43", "margin": "md", "wrap": True},
                    {"type": "text", "text": "▪️ توافق - نسبة التوافق بين اسمين", "size": "sm", "color": "#3C3C43", "margin": "sm", "wrap": True},
                    {"type": "text", "text": "▪️ سؤال - أسئلة عشوائية", "size": "sm", "color": "#3C3C43", "margin": "sm", "wrap": True},
                    {"type": "text", "text": "▪️ تحدي - تحديات ممتعة", "size": "sm", "color": "#3C3C43", "margin": "sm", "wrap": True},
                    {"type": "text", "text": "▪️ اعتراف - اعترافات", "size": "sm", "color": "#3C3C43", "margin": "sm", "wrap": True},
                    {"type": "text", "text": "▪️ منشن - أسئلة منشن", "size": "sm", "color": "#3C3C43", "margin": "sm", "wrap": True}
                ], "backgroundColor": "#F2F2F7", "cornerRadius": "12px", "paddingAll": "16px", "margin": "md"},
                {"type": "text", "text": "بوت الحوت", "size": "xs", "color": "#C7C7CC", "align": "center", "margin": "xl"}
            ],
            "backgroundColor": "#FFFFFF",
            "paddingAll": "24px"
        }
    }

def get_help_card():
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "مساعدة", "size": "xxl", "weight": "bold", "color": "#1C1C1E", "align": "center"},
                {"type": "separator", "margin": "md", "color": "#E5E5EA"},
                {"type": "text", "text": "الأوامر الأساسية", "size": "md", "weight": "bold", "color": "#1C1C1E", "margin": "xl"},
                {"type": "box", "layout": "vertical", "contents": [
                    {"type": "text", "text": "▪️ انضم - للتسجيل واللعب", "size": "sm", "color": "#3C3C43", "margin": "md"},
                    {"type": "text", "text": "▪️ انسحب - للخروج من البوت", "size": "sm", "color": "#3C3C43", "margin": "sm"},
                    {"type": "text", "text": "▪️ نقاطي - عرض إحصائياتك", "size": "sm", "color": "#3C3C43", "margin": "sm"},
                    {"type": "text", "text": "▪️ الصدارة - أفضل اللاعبين", "size": "sm", "color": "#3C3C43", "margin": "sm"},
                    {"type": "text", "text": "▪️ ايقاف - إيقاف اللعبة الحالية", "size": "sm", "color": "#3C3C43", "margin": "sm"}
                ], "backgroundColor": "#F2F2F7", "cornerRadius": "12px", "paddingAll": "16px", "margin": "md"},
                {"type": "text", "text": "أوامر اللعب", "size": "md", "weight": "bold", "color": "#1C1C1E", "margin": "xl"},
                {"type": "box", "layout": "vertical", "contents": [
                    {"type": "text", "text": "▪️ لمح - احصل على تلميح (-1 نقطة)", "size": "sm", "color": "#3C3C43", "margin": "md"},
                    {"type": "text", "text": "▪️ جاوب - اعرض الإجابة الصحيحة", "size": "sm", "color": "#3C3C43", "margin": "sm"}
                ], "backgroundColor": "#F2F2F7", "cornerRadius": "12px", "paddingAll": "16px", "margin": "md"},
                {"type": "text", "text": "نظام النقاط", "size": "md", "weight": "bold", "color": "#1C1C1E", "margin": "xl"},
                {"type": "box", "layout": "vertical", "contents": [
                    {"type": "text", "text": "إجابة صحيحة: +2 نقطة", "size": "sm", "color": "#3C3C43", "margin": "md"},
                    {"type": "text", "text": "طلب لمح: -1 نقطة", "size": "sm", "color": "#3C3C43", "margin": "sm"},
                    {"type": "text", "text": "طلب جاوب أو تخطي: 0 نقطة", "size": "sm", "color": "#3C3C43", "margin": "sm"}
                ], "backgroundColor": "#F2F2F7", "cornerRadius": "12px", "paddingAll": "16px", "margin": "md"},
                {"type": "text", "text": "بوت الحوت", "size": "xs", "color": "#C7C7CC", "align": "center", "margin": "xl"}
            ],
            "backgroundColor": "#FFFFFF",
            "paddingAll": "24px"
        }
    }

def get_stats_card(user_id, name):
    stats = get_stats(user_id)
    is_reg = user_id in registered_players
    
    if not stats:
        return {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "إحصائياتك", "size": "xxl", "weight": "bold", "color": "#1C1C1E", "align": "center"},
                    {"type": "text", "text": name, "size": "md", "color": "#8E8E93", "align": "center", "margin": "sm"},
                    {"type": "separator", "margin": "xl", "color": "#E5E5EA"},
                    {"type": "box", "layout": "horizontal", "contents": [
                        {"type": "text", "text": "الحالة", "size": "sm", "color": "#8E8E93", "flex": 1},
                        {"type": "text", "text": "مسجل" if is_reg else "غير مسجل", "size": "sm", "color": "#34C759" if is_reg else "#FF3B30", "flex": 1, "align": "end", "weight": "bold"}
                    ], "backgroundColor": "#F2F2F7", "cornerRadius": "12px", "paddingAll": "16px", "margin": "xl"},
                    {"type": "text", "text": "لم تبدأ بعد" if is_reg else "يجب التسجيل أولاً", "size": "md", "color": "#8E8E93", "align": "center", "margin": "xl"}
                ],
                "backgroundColor": "#FFFFFF",
                "paddingAll": "24px"
            }
        }
    
    win_rate = (stats['wins'] / stats['games_played'] * 100) if stats['games_played'] > 0 else 0
    
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "إحصائياتك", "size": "xxl", "weight": "bold", "color": "#1C1C1E", "align": "center"},
                {"type": "text", "text": name, "size": "md", "color": "#8E8E93", "align": "center", "margin": "sm"},
                {"type": "separator", "margin": "xl", "color": "#E5E5EA"},
                {"type": "box", "layout": "vertical", "contents": [
                    {"type": "box", "layout": "horizontal", "contents": [
                        {"type": "text", "text": "النقاط", "size": "sm", "color": "#8E8E93", "flex": 1},
                        {"type": "text", "text": str(stats['total_points']), "size": "xxl", "weight": "bold", "color": "#1C1C1E", "flex": 1, "align": "end"}
                    ]},
                    {"type": "separator", "margin": "md", "color": "#E5E5EA"},
                    {"type": "box", "layout": "horizontal", "contents": [
                        {"type": "text", "text": "الألعاب", "size": "sm", "color": "#8E8E93"},
                        {"type": "text", "text": str(stats['games_played']), "size": "md", "weight": "bold", "color": "#1C1C1E", "align": "end"}
                    ], "margin": "md"},
                    {"type": "box", "layout": "horizontal", "contents": [
                        {"type": "text", "text": "الفوز", "size": "sm", "color": "#8E8E93"},
                        {"type": "text", "text": str(stats['wins']), "size": "md", "weight": "bold", "color": "#1C1C1E", "align": "end"}
                    ], "margin": "sm"},
                    {"type": "box", "layout": "horizontal", "contents": [
                        {"type": "text", "text": "معدل الفوز", "size": "sm", "color": "#8E8E93"},
                        {"type": "text", "text": f"{win_rate:.0f}%", "size": "md", "weight": "bold", "color": "#1C1C1E", "align": "end"}
                    ], "margin": "sm"}
                ], "backgroundColor": "#F2F2F7", "cornerRadius": "12px", "paddingAll": "16px", "margin": "lg"}
            ],
            "backgroundColor": "#FFFFFF",
            "paddingAll": "24px"
        }
    }

def get_leaderboard_card():
    leaders = get_leaderboard()
    if not leaders:
        return {"type": "bubble", "body": {"type": "box", "layout": "vertical", "contents": [
            {"type": "text", "text": "لوحة الصدارة", "size": "xxl", "weight": "bold", "color": "#1C1C1E", "align": "center"},
            {"type": "text", "text": "لا توجد بيانات", "size": "md", "color": "#8E8E93", "align": "center", "margin": "xl"}
        ], "backgroundColor": "#FFFFFF", "paddingAll": "24px"}}
    
    items = []
    for i, leader in enumerate(leaders, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}"
        bg = "#F2F2F7" if i <= 3 else "#FAFAFA"
        
        items.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": emoji, "size": "md", "color": "#1C1C1E", "flex": 0, "weight": "bold"},
                {"type": "text", "text": leader['display_name'], "size": "sm", "color": "#1C1C1E", "flex": 3, "margin": "md", "wrap": True},
                {"type": "text", "text": str(leader['total_points']), "size": "md", "color": "#1C1C1E", "flex": 1, "align": "end", "weight": "bold"}
            ],
            "backgroundColor": bg,
            "cornerRadius": "12px",
            "paddingAll": "16px",
            "margin": "sm" if i > 1 else "none"
        })
    
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "🏆 لوحة الصدارة", "size": "xxl", "weight": "bold", "color": "#1C1C1E", "align": "center"},
                {"type": "separator", "margin": "xl", "color": "#E5E5EA"},
                {"type": "box", "layout": "vertical", "contents": items, "margin": "lg"}
            ],
            "backgroundColor": "#FFFFFF",
            "paddingAll": "24px"
        }
    }

GAME_COMMANDS = ['أغنية', 'لعبة', 'سلسلة', 'أسرع', 'ضد', 'تكوين', 'اختلاف', 'توافق', 'ترتيب', 'كلمة', 'لون']
BOT_COMMANDS = ['البداية', 'البدايه', 'مساعدة', 'مساعده', 'انضم', 'انسحب', 'نقاطي', 'الصدارة', 'الصداره', 'ايقاف', 'إيقاف', 
                'سؤال', 'سوال', 'تحدي', 'اعتراف', 'منشن', 'لمح', 'جاوب', 'الجواب', 'الحل']

def is_bot_command(text):
    text = text.strip()
    return text in BOT_COMMANDS or text in GAME_COMMANDS

@app.route("/", methods=['GET'])
def home():
    games_loaded = len(GAMES)
    return f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><title>بوت الحوت</title>
    <style>
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{font-family:-apple-system,sans-serif;background:#F2F2F7;padding:20px}}
    .container{{background:#fff;border-radius:16px;padding:30px;max-width:600px;margin:0 auto;box-shadow:0 2px 10px rgba(0,0,0,0.05)}}
    h1{{color:#1C1C1E;margin-bottom:20px;text-align:center}}
    .status{{background:#F2F2F7;padding:20px;border-radius:12px;margin:20px 0}}
    .status-item{{display:flex;justify-content:space-between;padding:12px 0;border-bottom:1px solid #E5E5EA}}
    .status-item:last-child{{border:none}}
    .label{{color:#8E8E93}}
    .value{{color:#1C1C1E;font-weight:bold}}
    </style></head><body>
    <div class="container">
        <h1>بوت الحوت</h1>
        <div class="status">
            <div class="status-item"><span class="label">الحالة</span><span class="value">يعمل</span></div>
            <div class="status-item"><span class="label">Gemini AI</span><span class="value">{'مفعّل' if USE_AI else 'معطّل'}</span></div>
            <div class="status-item"><span class="label">اللاعبون</span><span class="value">{len(registered_players)}</span></div>
            <div class="status-item"><span class="label">الألعاب المحملة</span><span class="value">{games_loaded}/11</span></div>
        </div>
    </div></body></html>
    """

@app.route("/health")
def health():
    return {"status": "healthy", "games": len(GAMES)
