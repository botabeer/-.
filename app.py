from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
import os, sys, sqlite3, threading, time, random, re, logging
from datetime import datetime, timedelta
from collections import defaultdict

# ═══════════════════════════════════════════════════
# إعداد Logging مع نظام التشخيص
# ═══════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("game-bot")

class DiagnosticSystem:
    """نظام تشخيص المشاكل"""
    def __init__(self):
        self.issues = []
        self.warnings = []
    
    def add_issue(self, category, message, severity="ERROR"):
        issue = {"category": category, "message": message, "severity": severity, "time": datetime.now().isoformat()}
        self.issues.append(issue)
        if severity == "ERROR":
            logger.error(f"🔴 {category}: {message}")
        else:
            logger.warning(f"🟡 {category}: {message}")
    
    def get_report(self):
        return {"issues": self.issues[-20:], "warnings": self.warnings[-20:]}

diagnostic = DiagnosticSystem()

# ═══════════════════════════════════════════════════
# إعداد LINE Bot
# ═══════════════════════════════════════════════════
LINE_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'YOUR_TOKEN')
LINE_SECRET = os.getenv('LINE_CHANNEL_SECRET', 'YOUR_SECRET')

if LINE_TOKEN == 'YOUR_TOKEN':
    diagnostic.add_issue("CONFIG", "LINE_CHANNEL_ACCESS_TOKEN غير محدد", "ERROR")
if LINE_SECRET == 'YOUR_SECRET':
    diagnostic.add_issue("CONFIG", "LINE_CHANNEL_SECRET غير محدد", "ERROR")

line_bot_api = LineBotApi(LINE_TOKEN)
handler = WebhookHandler(LINE_SECRET)

# ═══════════════════════════════════════════════════
# إعداد Gemini AI (اختياري)
# ═══════════════════════════════════════════════════
USE_AI = False
ask_gemini = None

try:
    import google.generativeai as genai
    GEMINI_KEYS = [k for k in [os.getenv(f'GEMINI_API_KEY_{i}', '') for i in ['', '1', '2', '3']] if k]
    
    if GEMINI_KEYS:
        genai.configure(api_key=GEMINI_KEYS[0])
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        USE_AI = True
        logger.info(f"✅ Gemini AI جاهز ({len(GEMINI_KEYS)} مفاتيح)")
        
        def ask_gemini(prompt, max_retries=2):
            for attempt in range(max_retries):
                try:
                    return model.generate_content(prompt).text.strip()
                except Exception as e:
                    logger.error(f"Gemini خطأ: {e}")
            return None
    else:
        diagnostic.add_issue("AI", "Gemini API Keys غير متوفرة", "WARNING")
except ImportError:
    diagnostic.add_issue("AI", "مكتبة google-generativeai غير مثبتة", "WARNING")
except Exception as e:
    diagnostic.add_issue("AI", f"خطأ في تهيئة Gemini: {e}", "WARNING")

# ═══════════════════════════════════════════════════
# استيراد الألعاب مع نظام التشخيص
# ═══════════════════════════════════════════════════
GAMES = {}
GAME_CLASSES = {
    'song': ('song_game', 'SongGame'),
    'human_animal': ('human_animal_plant_game', 'HumanAnimalPlantGame'),
    'chain': ('chain_words_game', 'ChainWordsGame'),
    'fast': ('fast_typing_game', 'FastTypingGame'),
    'opposite': ('opposite_game', 'OppositeGame'),
    'letters': ('letters_words_game', 'LettersWordsGame'),
    'differences': ('differences_game', 'DifferencesGame'),
    'compatibility': ('compatibility_game', 'CompatibilityGame')
}

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'games'))

for key, (module_name, class_name) in GAME_CLASSES.items():
    try:
        module = __import__(module_name)
        GAMES[key] = getattr(module, class_name)
        logger.info(f"✅ تم تحميل {class_name}")
    except ImportError as e:
        diagnostic.add_issue("GAMES", f"فشل استيراد {module_name}: ملف غير موجود", "ERROR")
    except AttributeError as e:
        diagnostic.add_issue("GAMES", f"فشل استيراد {class_name} من {module_name}: الكلاس غير موجود", "ERROR")
    except Exception as e:
        diagnostic.add_issue("GAMES", f"خطأ في {module_name}: {e}", "ERROR")

logger.info(f"📦 تم تحميل {len(GAMES)}/8 ألعاب")

# ═══════════════════════════════════════════════════
# إعداد Flask
# ═══════════════════════════════════════════════════
app = Flask(__name__)

# ═══════════════════════════════════════════════════
# قاعدة البيانات
# ═══════════════════════════════════════════════════
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
            last_played TEXT,
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
        logger.info("✅ قاعدة البيانات جاهزة")
    except Exception as e:
        diagnostic.add_issue("DATABASE", f"فشل إنشاء قاعدة البيانات: {e}", "ERROR")

init_db()

# ═══════════════════════════════════════════════════
# المتغيرات العامة
# ═══════════════════════════════════════════════════
active_games = {}
registered_players = set()
user_names_cache = {}
rate_limit = defaultdict(lambda: {'count': 0, 'reset': datetime.now()})

games_lock = threading.Lock()
players_lock = threading.Lock()

# ═══════════════════════════════════════════════════
# دوال مساعدة
# ═══════════════════════════════════════════════════
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
            c.execute('UPDATE users SET display_name = ? WHERE user_id = ?', (name, user_id))
            conn.commit()
        elif not row:
            c.execute('INSERT INTO users (user_id, display_name) VALUES (?, ?)', (user_id, name))
            conn.commit()
        conn.close()
        return name
    
    except LineBotApiError as e:
        name = f"لاعب_{user_id[-4:]}"
        user_names_cache[user_id] = name
        if e.status_code == 404:
            diagnostic.add_issue("USER", f"ملف المستخدم {user_id[-4:]} غير موجود (404)", "WARNING")
        else:
            diagnostic.add_issue("USER", f"LINE API خطأ {e.status_code}: {e.message}", "WARNING")
        return name
    
    except Exception as e:
        diagnostic.add_issue("USER", f"خطأ غير متوقع: {e}", "ERROR")
        return f"لاعب_{user_id[-4:]}"

def update_points(user_id, name, points, won=False, game_type=""):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = c.fetchone()
        
        if user:
            c.execute('''UPDATE users SET total_points = ?, games_played = ?, wins = ?, 
                         last_played = ?, display_name = ? WHERE user_id = ?''',
                      (user['total_points'] + points, user['games_played'] + 1,
                       user['wins'] + (1 if won else 0), datetime.now().isoformat(), name, user_id))
        else:
            c.execute('''INSERT INTO users (user_id, display_name, total_points, games_played, wins, last_played) 
                         VALUES (?, ?, ?, 1, ?, ?)''',
                      (user_id, name, points, 1 if won else 0, datetime.now().isoformat()))
        
        if game_type:
            c.execute('INSERT INTO game_history (user_id, game_type, points, won) VALUES (?, ?, ?, ?)',
                      (user_id, game_type, points, 1 if won else 0))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        diagnostic.add_issue("DATABASE", f"فشل تحديث النقاط: {e}", "ERROR")
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
        diagnostic.add_issue("DATABASE", f"فشل جلب الإحصائيات: {e}", "ERROR")
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
        diagnostic.add_issue("DATABASE", f"فشل جلب الصدارة: {e}", "ERROR")
        return []

def load_text_file(filename):
    try:
        path = os.path.join('games', filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        diagnostic.add_issue("FILES", f"ملف {filename} غير موجود", "WARNING")
        return []
    except Exception as e:
        diagnostic.add_issue("FILES", f"فشل قراءة {filename}: {e}", "ERROR")
        return []

QUESTIONS = load_text_file('questions.txt')
CHALLENGES = load_text_file('challenges.txt')
CONFESSIONS = load_text_file('confessions.txt')
MENTIONS = load_text_file('more_questions.txt')

# ═══════════════════════════════════════════════════
# بطاقات Flex محسّنة (iOS Style)
# ═══════════════════════════════════════════════════
def get_welcome_card(name):
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "بوت الحفوت", "size": "xl", "weight": "bold", "color": "#1C1C1E", "align": "center"},
                {"type": "text", "text": f"مرحباً {name}", "size": "md", "color": "#8E8E93", "align": "center", "margin": "md"},
                {"type": "separator", "margin": "xl", "color": "#F2F2F7"},
                {"type": "text", "text": "استخدم الأزرار أدناه للعب", "size": "sm", "color": "#8E8E93", "align": "center", "margin": "xl", "wrap": True}
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
                    {"type": "text", "text": "إحصائياتك", "size": "xl", "weight": "bold", "color": "#1C1C1E", "align": "center"},
                    {"type": "text", "text": name, "size": "md", "color": "#8E8E93", "align": "center", "margin": "sm"},
                    {"type": "separator", "margin": "xl", "color": "#F2F2F7"},
                    {"type": "box", "layout": "horizontal", "contents": [
                        {"type": "text", "text": "الحالة:", "size": "sm", "color": "#8E8E93", "flex": 1},
                        {"type": "text", "text": "مسجل ✓" if is_reg else "غير مسجل", "size": "sm", "color": "#1C1C1E", "flex": 1, "align": "end", "weight": "bold"}
                    ], "backgroundColor": "#F2F2F7", "cornerRadius": "8px", "paddingAll": "12px", "margin": "xl"},
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
                {"type": "text", "text": "إحصائياتك", "size": "xl", "weight": "bold", "color": "#1C1C1E", "align": "center"},
                {"type": "text", "text": name, "size": "md", "color": "#8E8E93", "align": "center", "margin": "sm"},
                {"type": "separator", "margin": "xl", "color": "#F2F2F7"},
                {"type": "box", "layout": "vertical", "contents": [
                    {"type": "box", "layout": "horizontal", "contents": [
                        {"type": "text", "text": "النقاط", "size": "sm", "color": "#8E8E93", "flex": 1},
                        {"type": "text", "text": str(stats['total_points']), "size": "xxl", "weight": "bold", "color": "#1C1C1E", "flex": 1, "align": "end"}
                    ]},
                    {"type": "separator", "margin": "md", "color": "#F2F2F7"},
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
            {"type": "text", "text": "لوحة الصدارة", "size": "xl", "weight": "bold", "color": "#1C1C1E", "align": "center"},
            {"type": "text", "text": "لا توجد بيانات", "size": "md", "color": "#8E8E93", "align": "center", "margin": "xl"}
        ], "backgroundColor": "#FFFFFF", "paddingAll": "24px"}}
    
    items = []
    for i, leader in enumerate(leaders, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}"
        bg = "#F2F2F7" if i == 1 else "#FAFAFA"
        
        items.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": emoji, "size": "md", "color": "#1C1C1E", "flex": 0, "weight": "bold"},
                {"type": "text", "text": leader['display_name'], "size": "sm", "color": "#1C1C1E", "flex": 3, "margin": "md", "wrap": True},
                {"type": "text", "text": str(leader['total_points']), "size": "md", "color": "#1C1C1E", "flex": 1, "align": "end", "weight": "bold"}
            ],
            "backgroundColor": bg,
            "cornerRadius": "8px",
            "paddingAll": "12px",
            "margin": "sm" if i > 1 else "none"
        })
    
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "لوحة الصدارة", "size": "xl", "weight": "bold", "color": "#1C1C1E", "align": "center"},
                {"type": "separator", "margin": "xl", "color": "#F2F2F7"},
                {"type": "box", "layout": "vertical", "contents": items, "margin": "lg"}
            ],
            "backgroundColor": "#FFFFFF",
            "paddingAll": "24px"
        }
    }

# ═══════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════
@app.route("/", methods=['GET'])
def home():
    report = diagnostic.get_report()
    games_loaded = len(GAMES)
    
    issues_html = ""
    for issue in report['issues']:
        color = "red" if issue['severity'] == "ERROR" else "orange"
        issues_html += f'<div style="color:{color};margin:5px 0">▫️ [{issue["category"]}] {issue["message"]}</div>'
    
    return f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><title>بوت الحفوت</title>
    <style>
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{font-family:-apple-system,sans-serif;background:#f5f5f5;padding:20px}}
    .container{{background:#fff;border-radius:12px;padding:30px;max-width:600px;margin:0 auto;box-shadow:0 2px 10px rgba(0,0,0,0.1)}}
    h1{{color:#333;margin-bottom:20px}}
    .status{{background:#f9f9f9;padding:15px;border-radius:8px;margin:10px 0}}
    .status-item{{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #eee}}
    .status-item:last-child{{border:none}}
    .label{{color:#888}}
    .value{{color:#333;font-weight:bold}}
    .issues{{background:#fff8f8;border-left:4px solid #ff4444;padding:15px;margin-top:20px;border-radius:4px}}
    .btn{{display:inline-block;padding:10px 20px;background:#666;color:#fff;text-decoration:none;border-radius:6px;margin:5px}}
    .btn:hover{{background:#555}}
    </style></head><body>
    <div class="container">
        <h1>بوت الحفوت</h1>
        <div class="status">
            <div class="status-item"><span class="label">الحالة</span><span class="value">يعمل</span></div>
            <div class="status-item"><span class="label">Gemini AI</span><span class="value">{'مفعّل' if USE_AI else 'معطّل'}</span></div>
            <div class="status-item"><span class="label">اللاعبون</span><span class="value">{len(registered_players)}</span></div>
            <div class="status-item"><span class="status-item"><span class="label">الألعاب المحملة</span><span class="value">{games_loaded}/8</span></div>
            <div class="status-item"><span class="label">الأخطاء</span><span class="value" style="color:{'red' if len(report['issues']) > 0 else 'green'}">{len(report['issues'])}</span></div>
        </div>
        {'<div class="issues"><strong>🔍 التشخيص:</strong>' + issues_html + '</div>' if report['issues'] else '<div style="color:green;margin-top:20px">✅ لا توجد مشاكل</div>'}
        <div style="text-align:center;margin-top:20px">
            <a href="/health" class="btn">الصحة</a>
            <a href="/diagnostic" class="btn">التشخيص الكامل</a>
        </div>
    </div></body></html>
    """

@app.route("/health")
def health():
    return {
        "status": "healthy",
        "games": len(GAMES),
        "players": len(registered_players),
        "ai": USE_AI,
        "issues": len(diagnostic.get_report()['issues'])
    }, 200

@app.route("/diagnostic")
def diagnostic_page():
    report = diagnostic.get_report()
    return {"diagnostic": report, "games_loaded": list(GAMES.keys())}, 200

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    if not signature:
        abort(400)
    
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        diagnostic.add_issue("WEBHOOK", "توقيع غير صالح", "ERROR")
        abort(400)
    except Exception as e:
        diagnostic.add_issue("WEBHOOK", f"خطأ: {e}", "ERROR")
    
    return 'OK', 200

# ═══════════════════════════════════════════════════
# Message Handler
# ═══════════════════════════════════════════════════
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        user_id = event.source.user_id
        text = event.message.text.strip()
        
        if not check_rate_limit(user_id):
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="انتظر قليلاً"))
            return
        
        name = get_user_profile_safe(user_id)
        game_id = getattr(event.source, 'group_id', user_id)
        
        # الأوامر الأساسية
        if text in ['البداية', 'ابدأ', 'start']:
            line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="مرحباً", contents=get_welcome_card(name)))
            return
        
        if text in ['انضم', 'join']:
            with players_lock:
                if user_id in registered_players:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"أنت مسجل بالفعل يا {name}"))
                else:
                    registered_players.add(user_id)
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"✓ تم تسجيلك يا {name}"))
            return
        
        if text in ['انسحب', 'خروج']:
            with players_lock:
                if user_id in registered_players:
                    registered_players.remove(user_id)
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"تم انسحابك يا {name}"))
                else:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="أنت غير مسجل"))
            return
        
        if text in ['نقاطي', 'احصائياتي']:
            line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="إحصائياتك", contents=get_stats_card(user_id, name)))
            return
        
        if text in ['الصدارة', 'المتصدرين']:
            line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="الصدارة", contents=get_leaderboard_card()))
            return
        
        if text in ['إيقاف', 'stop']:
            with games_lock:
                if game_id in active_games:
                    del active_games[game_id]
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="تم إيقاف اللعبة"))
                else:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="لا توجد لعبة نشطة"))
            return
        
        # الأسئلة والتحديات
        if text in ['سؤال', 'سوال']:
            if QUESTIONS:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=random.choice(QUESTIONS)))
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ملف الأسئلة غير متوفر"))
            return
        
        if text in ['تحدي', 'challenge']:
            if CHALLENGES:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=random.choice(CHALLENGES)))
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ملف التحديات غير متوفر"))
            return
        
        if text in ['اعتراف', 'confession']:
            if CONFESSIONS:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=random.choice(CONFESSIONS)))
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ملف الاعترافات غير متوفر"))
            return
        
        if text in ['منشن', 'mention']:
            if MENTIONS:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=random.choice(MENTIONS)))
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ملف المنشن غير متوفر"))
            return
        
        # التحقق من التسجيل قبل اللعب
        if user_id not in registered_players:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="يجب التسجيل أولاً\nاكتب: انضم"))
            return
        
        # بدء الألعاب
        game_map = {
            'أغنية': ('song', 'أغنية'),
            'لعبة': ('human_animal', 'لعبة'),
            'سلسلة': ('chain', 'سلسلة'),
            'أسرع': ('fast', 'أسرع'),
            'ضد': ('opposite', 'ضد'),
            'تكوين': ('letters', 'تكوين'),
            'اختلاف': ('differences', 'اختلاف'),
            'توافق': ('compatibility', 'توافق')
        }
        
        if text in game_map:
            game_key, game_name = game_map[text]
            
            if game_key not in GAMES:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"لعبة {game_name} غير متوفرة"))
                diagnostic.add_issue("GAME", f"محاولة تشغيل لعبة {game_name} غير محملة", "WARNING")
                return
            
            # لعبة التوافق لها معالجة خاصة
            if game_key == 'compatibility':
                with games_lock:
                    game = GAMES[game_key](line_bot_api)
                    active_games[game_id] = {
                        'game': game,
                        'type': game_name,
                        'created_at': datetime.now(),
                        'waiting_for_names': True
                    }
                line_bot_api.reply_message(event.reply_token, TextSendMessage(
                    text="▪️ لعبة التوافق\n\nاكتب اسمين مفصولين بمسافة\nنص فقط بدون رموز\n\nمثال: محمد فاطمة"
                ))
                return
            
            # الألعاب الأخرى
            try:
                with games_lock:
                    if game_key in ['song', 'human_animal', 'letters']:
                        game = GAMES[game_key](line_bot_api, use_ai=USE_AI, ask_ai=ask_gemini)
                    else:
                        game = GAMES[game_key](line_bot_api)
                    
                    active_games[game_id] = {
                        'game': game,
                        'type': game_name,
                        'created_at': datetime.now(),
                        'answered_users': set(),
                        'last_game': text
                    }
                
                response = game.start_game()
                line_bot_api.reply_message(event.reply_token, response)
                logger.info(f"✅ بدأت لعبة {game_name} للمستخدم {name}")
            
            except Exception as e:
                diagnostic.add_issue("GAME", f"فشل بدء لعبة {game_name}: {e}", "ERROR")
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="حدث خطأ في بدء اللعبة"))
            
            return
        
        # معالجة إجابات اللعبة
        if game_id in active_games:
            game_data = active_games[game_id]
            game = game_data['game']
            game_type = game_data['type']
            
            # لعبة التوافق
            if game_data.get('waiting_for_names'):
                cleaned = text.replace('@', '').strip()
                names = cleaned.split()
                
                if len(names) < 2:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(
                        text="يجب كتابة اسمين مفصولين بمسافة\nمثال: محمد فاطمة"
                    ))
                    return
                
                try:
                    result = game.check_answer(f"{names[0]} {names[1]}", user_id, name)
                    
                    with games_lock:
                        game_data['waiting_for_names'] = False
                        if game_id in active_games:
                            del active_games[game_id]
                    
                    if result and result.get('response'):
                        line_bot_api.reply_message(event.reply_token, result['response'])
                
                except Exception as e:
                    diagnostic.add_issue("GAME", f"خطأ في لعبة التوافق: {e}", "ERROR")
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="حدث خطأ. حاول مرة أخرى"))
                
                return
            
            # منع تكرار الإجابة
            if 'answered_users' in game_data and user_id in game_data['answered_users']:
                return
            
            # التحقق من الإجابة
            try:
                result = game.check_answer(text, user_id, name)
                
                if result:
                    # تحديث النقاط
                    if result.get('correct'):
                        if 'answered_users' not in game_data:
                            game_data['answered_users'] = set()
                        game_data['answered_users'].add(user_id)
                    
                    points = result.get('points', 0)
                    if points > 0:
                        update_points(user_id, name, points, result.get('won', False), game_type)
                    
                    # السؤال التالي
                    if result.get('next_question'):
                        with games_lock:
                            game_data['answered_users'] = set()
                        next_q = game.next_question()
                        if next_q:
                            line_bot_api.reply_message(event.reply_token, next_q)
                        return
                    
                    # نهاية اللعبة
                    if result.get('game_over'):
                        with games_lock:
                            if game_id in active_games:
                                del active_games[game_id]
                        
                        if result.get('winner_card'):
                            line_bot_api.reply_message(event.reply_token, FlexSendMessage(
                                alt_text="الفائز", contents=result['winner_card']
                            ))
                        else:
                            line_bot_api.reply_message(event.reply_token, result.get('response'))
                        return
                    
                    # إرسال الرد
                    line_bot_api.reply_message(event.reply_token, result.get('response'))
            
            except Exception as e:
                diagnostic.add_issue("GAME", f"خطأ في معالجة الإجابة: {e}", "ERROR")
    
    except Exception as e:
        diagnostic.add_issue("HANDLER", f"خطأ في handle_message: {e}", "ERROR")
        try:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="حدث خطأ مؤقت"))
        except:
            pass

# ═══════════════════════════════════════════════════
# تنظيف الألعاب القديمة
# ═══════════════════════════════════════════════════
def cleanup_old_games():
    while True:
        try:
            time.sleep(300)
            now = datetime.now()
            to_delete = []
            
            with games_lock:
                for gid, data in active_games.items():
                    if now - data.get('created_at', now) > timedelta(minutes=15):
                        to_delete.append(gid)
                
                for gid in to_delete:
                    del active_games[gid]
                
                if to_delete:
                    logger.info(f"🗑️ حذف {len(to_delete)} لعبة قديمة")
            
            # تنظيف الذاكرة
            if len(user_names_cache) > 1000:
                user_names_cache.clear()
                logger.info("🧹 تنظيف ذاكرة الأسماء")
        
        except Exception as e:
            diagnostic.add_issue("CLEANUP", f"خطأ في التنظيف: {e}", "WARNING")

cleanup_thread = threading.Thread(target=cleanup_old_games, daemon=True)
cleanup_thread.start()

# ═══════════════════════════════════════════════════
# تشغيل التطبيق
# ═══════════════════════════════════════════════════
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    
    logger.info("="*60)
    logger.info("🚀 بوت الحفوت - بدء التشغيل")
    logger.info(f"📡 المنفذ: {port}")
    logger.info(f"🤖 Gemini AI: {'مفعّل' if USE_AI else 'معطّل'}")
    logger.info(f"🎮 الألعاب المحملة: {len(GAMES)}/8")
    logger.info(f"📋 الألعاب: {', '.join(GAMES.keys())}")
    logger.info(f"⚠️  الأخطاء: {len(diagnostic.get_report()['issues'])}")
    logger.info("="*60)
    
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
