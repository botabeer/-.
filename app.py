"""بوت الحوت v3.2 - نسخة نهائية محسّنة مع تصميم ثري دي زجاجي"""
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage, QuickReply, QuickReplyButton, MessageAction
import os, sqlite3, logging, sys, threading, time, re
from datetime import datetime, timedelta
from collections import defaultdict, deque, Counter
from functools import lru_cache
from queue import Queue

# إعداد Logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.handlers.RotatingFileHandler('logs/bot.log', maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
    ]
)
logger = logging.getLogger("whale-bot")

print("\n" + "═"*60 + "\n♓ بوت الحوت v3.2 - تصميم ثري دي زجاجي ♓\n" + "═"*60 + "\n")

# الإعدادات
LINE_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_SECRET = os.getenv('LINE_CHANNEL_SECRET')
GEMINI_KEYS = [k for k in [os.getenv(f'GEMINI_API_KEY_{i}', '') for i in range(1,4)] if k]

app = Flask(__name__)
line_bot_api = LineBotApi(LINE_TOKEN) if LINE_TOKEN else None
handler = WebhookHandler(LINE_SECRET) if LINE_SECRET else None

active_games, registered_players = {}, set()

# ألوان موحدة - ثري دي زجاجي
C = {
    'bg':'#0A1628',           # خلفية داكنة
    'card':'#0F2847',         # بطاقة زجاجية
    'card2':'#1A3A5C',        # بطاقة ثانوية
    'text':'#E0F2FF',         # نص أبيض مزرق
    'text2':'#7FB3D5',        # نص ثانوي
    'sep':'#2C5F8D',          # فاصل
    'cyan':'#00D9FF',         # أزرق سماوي
    'cyan_glow':'#5EEBFF',    # سماوي متوهج
    'purple':'#8B7FFF',       # بنفسجي
    'success':'#00E5A0',      # أخضر نجاح
    'border':'#00D9FF40'      # حدود شفافة
}

# شعار الحوت (Pisces)
PISCES_LOGO = "♓"

# Rate Limiter
class RateLimiter:
    def __init__(self, max_req=10, window=60):
        self.max_req, self.window = max_req, window
        self.requests = defaultdict(deque)
        self.lock = threading.Lock()
    
    def is_allowed(self, uid):
        with self.lock:
            now, reqs = time.time(), self.requests[uid]
            while reqs and reqs[0] < now - self.window:
                reqs.popleft()
            if len(reqs) >= self.max_req:
                return False
            reqs.append(now)
            return True

rate_limiter = RateLimiter()

# Metrics
class Metrics:
    def __init__(self):
        self.msgs = Counter()
        self.games = Counter()
        self.start = datetime.now()
    
    def log_msg(self, uid): 
        self.msgs[uid] += 1
    
    def log_game(self, gtype): 
        self.games[gtype] += 1
    
    def stats(self): 
        return {
            'uptime': (datetime.now()-self.start).total_seconds(), 
            'total_msgs': sum(self.msgs.values()), 
            'total_games': sum(self.games.values())
        }

metrics = Metrics()

# Gemini AI
USE_AI, model = False, None
try:
    import google.generativeai as genai
    if GEMINI_KEYS:
        genai.configure(api_key=GEMINI_KEYS[0])
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        USE_AI = True
        logger.info(f"✅ Gemini جاهز ({len(GEMINI_KEYS)} مفاتيح)")
except Exception as e:
    logger.warning(f"⚠️ Gemini معطّل: {e}")

class GeminiClient:
    def __init__(self, keys):
        self.keys, self.idx, self.lock = keys, 0, threading.Lock()
    
    def ask(self, prompt):
        if not USE_AI or not self.keys: 
            return None
        for _ in range(len(self.keys)):
            try:
                r = model.generate_content(prompt)
                if r and r.text: 
                    return r.text.strip()[:1000]
            except Exception as e:
                logger.error(f"Gemini: {e}")
                with self.lock:
                    self.idx = (self.idx + 1) % len(self.keys)
                    genai.configure(api_key=self.keys[self.idx])
        return None

gemini = GeminiClient(GEMINI_KEYS) if GEMINI_KEYS else None

# قاعدة بيانات
DB = 'whale_bot.db'

class DBPool:
    def __init__(self, db, size=5):
        self.pool = Queue(maxsize=size)
        for _ in range(size):
            conn = sqlite3.connect(db, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            self.pool.put(conn)
    
    def execute(self, query, params=()):
        conn = self.pool.get()
        try:
            c = conn.cursor()
            c.execute(query, params)
            conn.commit()
            return c
        finally:
            self.pool.put(conn)
    
    def fetchone(self, query, params=()):
        c = self.execute(query, params)
        result = c.fetchone()
        return dict(result) if result else None
    
    def fetchall(self, query, params=()):
        c = self.execute(query, params)
        return [dict(r) for r in c.fetchall()]

def init_db():
    try:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS players (
            user_id TEXT PRIMARY KEY, 
            display_name TEXT NOT NULL,
            total_points INTEGER DEFAULT 0, 
            games_played INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0, 
            last_active TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_points ON players(total_points DESC)')
        conn.commit()
        conn.close()
        logger.info("✅ قاعدة البيانات جاهزة")
        return True
    except Exception as e:
        logger.error(f"❌ DB: {e}")
        return False

init_db()
db = DBPool(DB)

# دوال مساعدة
def safe_text(t, max_len=500):
    return str(t or "").strip()[:max_len].replace('"','').replace("'",'')

@lru_cache(maxsize=1000)
def normalize_text(t):
    if not t: return ""
    t = t.strip().lower()
    t = re.sub('[أإآ]','ا',t)
    t = re.sub('[ؤ]','و',t)
    t = re.sub('[ئ]','ي',t)
    t = re.sub('[ءةى]','',t)
    t = re.sub('[\u064B-\u065F]','',t)
    return re.sub(r'\s+',' ',t).strip()

def get_profile(uid):
    if not line_bot_api: 
        return f"مستخدم{uid[-4:]}"
    try:
        p = line_bot_api.get_profile(uid)
        return safe_text(p.display_name,50) if p.display_name else f"مستخدم{uid[-4:]}"
    except:
        return f"مستخدم{uid[-4:]}"

# إدارة المستخدمين
def update_user(uid, name):
    try:
        db.execute(
            'INSERT OR REPLACE INTO players (user_id,display_name,last_active) VALUES (?,?,?)',
            (uid, safe_text(name,100), datetime.now().isoformat())
        )
    except Exception as e: 
        logger.error(f"تحديث: {e}")

def update_points(uid, name, pts, won=False):
    try:
        r = db.fetchone('SELECT total_points,games_played,wins FROM players WHERE user_id=?', (uid,))
        if r:
            db.execute(
                'UPDATE players SET total_points=?,games_played=?,wins=?,last_active=?,display_name=? WHERE user_id=?',
                (max(0,r['total_points']+pts), r['games_played']+1, r['wins']+(1 if won else 0),
                 datetime.now().isoformat(), safe_text(name,100), uid)
            )
        else:
            db.execute(
                'INSERT INTO players VALUES (?,?,?,1,?,?)',
                (uid, safe_text(name,100), max(0,pts), 1 if won else 0, datetime.now().isoformat())
            )
    except Exception as e: 
        logger.error(f"نقاط: {e}")

def get_stats(uid):
    return db.fetchone('SELECT * FROM players WHERE user_id=?', (uid,))

def get_leaderboard(limit=10):
    return db.fetchall(
        'SELECT display_name,total_points,games_played,wins FROM players WHERE total_points>0 ORDER BY total_points DESC,wins DESC LIMIT ?', 
        (limit,)
    )

def cleanup_inactive():
    try:
        cutoff = (datetime.now()-timedelta(days=45)).isoformat()
        c = db.execute('DELETE FROM players WHERE last_active<?', (cutoff,))
        if c.rowcount: 
            logger.info(f"🧹 حذف {c.rowcount} مستخدم غير نشط")
    except Exception as e: 
        logger.error(f"تنظيف: {e}")

threading.Thread(
    target=lambda: [time.sleep(21600) or cleanup_inactive() for _ in iter(int,1)], 
    daemon=True
).start()

# المحتوى
def load_txt(name):
    try:
        with open(f'{name}.txt','r',encoding='utf-8') as f:
            return [l.strip() for l in f if l.strip()]
    except FileNotFoundError:
        logger.warning(f"⚠️ {name}.txt غير موجود")
        return []

QUESTIONS = load_txt('questions')
CHALLENGES = load_txt('challenges')
CONFESSIONS = load_txt('confessions')
MENTIONS = load_txt('more_questions')

q_idx = c_idx = cf_idx = m_idx = 0

def next_content(items, idx_name):
    global q_idx, c_idx, cf_idx, m_idx
    idx = globals()[idx_name]
    if not items: 
        return "محتوى افتراضي"
    r = items[idx % len(items)]
    globals()[idx_name] += 1
    return r

# Quick Reply
def get_qr():
    btns = ["أغنية","لعبة","سلسلة","أسرع","ضد","تكوين","ترتيب","كلمة","لون","سؤال","تحدي","اعتراف","منشن"]
    return QuickReply(items=[QuickReplyButton(action=MessageAction(label=f"▫️ {b}",text=b)) for b in btns])

# مكونات Flex محسّنة - ثري دي زجاجي
def create_glass_box(contents, padding="20px", margin="md"):
    """صندوق زجاجي ثري دي"""
    return {
        "type":"box",
        "layout":"vertical",
        "contents":contents,
        "backgroundColor":C['card'],
        "cornerRadius":"20px",
        "paddingAll":padding,
        "margin":margin,
        "borderWidth":"2px",
        "borderColor":C['border'],
        "offsetTop":"0px",
        "offsetStart":"0px"
    }

def create_glow_text(text, size="xl", color=None):
    """نص متوهج"""
    return {
        "type":"text",
        "text":text,
        "size":size,
        "weight":"bold",
        "color":color or C['cyan_glow'],
        "align":"center"
    }

def create_progress_bar(current, total):
    """شريط تقدم ثري دي"""
    return {
        "type":"box",
        "layout":"horizontal",
        "contents":[
            {
                "type":"box",
                "layout":"vertical",
                "contents":[],
                "backgroundColor":C['cyan'],
                "height":"8px",
                "flex":current,
                "cornerRadius":"4px"
            },
            {
                "type":"box",
                "layout":"vertical",
                "contents":[],
                "backgroundColor":C['card2'],
                "height":"8px",
                "flex":max(1, total-current),
                "cornerRadius":"4px"
            }
        ],
        "spacing":"xs",
        "margin":"xl"
    }

def game_header(icon, title, subtitle):
    """هيدر موحد للألعاب - ثري دي"""
    return [
        create_glass_box([
            {"type":"text","text":icon,"size":"4xl","align":"center","color":C['cyan_glow']}
        ],"16px","none"),
        {"type":"text","text":title,"size":"xxl","weight":"bold","color":C['cyan'],"align":"center","margin":"md"},
        {"type":"text","text":subtitle,"size":"sm","color":C['text2'],"align":"center","margin":"sm"},
        {"type":"separator","margin":"lg","color":C['sep']}
    ]

# Flex Cards محسّنة
def welcome_card():
    return {
        "type":"bubble",
        "size":"kilo",
        "body":{
            "type":"box",
            "layout":"vertical",
            "contents":[
                create_glass_box([
                    {"type":"text","text":PISCES_LOGO,"size":"5xl","color":C['cyan_glow'],"align":"center","weight":"bold"}
                ],"20px","none"),
                {"type":"text","text":"بوت الحوت","size":"xxl","weight":"bold","color":C['cyan'],"align":"center","margin":"md"},
                {"type":"text","text":"نظام ألعاب تفاعلية ثري دي","size":"sm","color":C['text2'],"align":"center","margin":"sm"},
                {"type":"separator","margin":"lg","color":C['sep']},
                create_glass_box([
                    {"type":"text","text":"🎮 الألعاب","size":"md","weight":"bold","color":C['text']},
                    {"type":"text","text":"أغنية | لعبة | سلسلة | أسرع\nضد | تكوين | ترتيب | كلمة | لون",
                     "size":"xs","color":C['text2'],"wrap":True,"margin":"sm"}
                ]),
                create_glass_box([
                    {"type":"text","text":"🎯 التسلية","size":"md","weight":"bold","color":C['text']},
                    {"type":"text","text":"سؤال | تحدي | اعتراف | منشن | اختلاف | توافق",
                     "size":"xs","color":C['text2'],"wrap":True,"margin":"sm"}
                ])
            ],
            "backgroundColor":C['bg'],
            "paddingAll":"24px"
        },
        "footer":{
            "type":"box",
            "layout":"vertical",
            "contents":[
                {
                    "type":"button",
                    "action":{"type":"message","label":"🎮 ابدأ اللعب","text":"مساعدة"},
                    "style":"primary",
                    "color":C['cyan'],
                    "height":"md"
                },
                {
                    "type":"box",
                    "layout":"horizontal",
                    "contents":[
                        {"type":"button","action":{"type":"message","label":"📊 نقاطي","text":"نقاطي"},"style":"secondary","height":"sm"},
                        {"type":"button","action":{"type":"message","label":"🏆 الصدارة","text":"الصدارة"},"style":"secondary","height":"sm"}
                    ],
                    "spacing":"sm",
                    "margin":"sm"
                }
            ],
            "paddingAll":"16px",
            "backgroundColor":C['bg']
        }
    }

def help_card():
    return {
        "type":"bubble",
        "size":"kilo",
        "body":{
            "type":"box",
            "layout":"vertical",
            "contents":[
                {"type":"text","text":"📖 المساعدة","size":"xl","weight":"bold","color":C['cyan'],"align":"center"},
                {"type":"separator","margin":"lg","color":C['sep']},
                create_glass_box([
                    {"type":"text","text":"🎮 أوامر اللعب","size":"md","weight":"bold","color":C['text']},
                    {"type":"text","text":"▫️ لمح: تلميح (-1 نقطة)\n▫️ جاوب: عرض الحل\n▫️ إيقاف: إنهاء اللعبة",
                     "size":"xs","color":C['text2'],"wrap":True,"margin":"sm"}
                ]),
                create_glass_box([
                    {"type":"text","text":"📊 الإحصائيات","size":"md","weight":"bold","color":C['text']},
                    {"type":"text","text":"▫️ نقاطي: عرض نقاطك\n▫️ الصدارة: أفضل اللاعبين",
                     "size":"xs","color":C['text2'],"wrap":True,"margin":"sm"}
                ])
            ],
            "backgroundColor":C['bg'],
            "paddingAll":"24px"
        }
    }

def stats_card(uid, name, is_reg):
    stats = get_stats(uid)
    
    if not stats:
        card = {
            "type":"bubble",
            "size":"kilo",
            "body":{
                "type":"box",
                "layout":"vertical",
                "contents":[
                    {"type":"text","text":"📊 إحصائياتك","size":"xl","weight":"bold","color":C['cyan'],"align":"center"},
                    {"type":"separator","margin":"lg","color":C['sep']},
                    create_glass_box([
                        {"type":"text","text":name,"size":"lg","color":C['text'],"align":"center"},
                        {"type":"text","text":"مسجل ✓" if is_reg else "غير مسجل","size":"sm",
                         "color":C['success'] if is_reg else C['text2'],"align":"center","margin":"sm"},
                        {"type":"text","text":"لم تبدأ بعد" if is_reg else "سجل للبدء","size":"md",
                         "color":C['text2'],"align":"center","margin":"md"}
                    ])
                ],
                "backgroundColor":C['bg'],
                "paddingAll":"24px"
            }
        }
        
        if not is_reg:
            card["footer"] = {
                "type":"box",
                "layout":"vertical",
                "contents":[{"type":"button","action":{"type":"message","label":"✅ انضم","text":"انضم"},"style":"primary","color":C['success']}],
                "paddingAll":"16px",
                "backgroundColor":C['bg']
            }
        return card
    
    wr = (stats['wins']/stats['games_played']*100) if stats['games_played']>0 else 0
    return {
        "type":"bubble",
        "size":"kilo",
        "body":{
            "type":"box",
            "layout":"vertical",
            "contents":[
                {"type":"text","text":"📊 إحصائياتك","size":"xl","weight":"bold","color":C['cyan'],"align":"center"},
                {"type":"separator","margin":"lg","color":C['sep']},
                create_glass_box([
                    {"type":"text","text":name,"size":"lg","color":C['text'],"align":"center"},
                    {"type":"text","text":"مسجل ✓","size":"sm","color":C['success'],"align":"center","margin":"sm"}
                ],"md"),
                create_glass_box([
                    {"type":"box","layout":"horizontal","contents":[
                        {"type":"text","text":"💎 النقاط","size":"sm","color":C['text2'],"flex":1},
                        {"type":"text","text":str(stats['total_points']),"size":"xxl","weight":"bold","color":C['cyan_glow'],"flex":1,"align":"end"}
                    ]},
                    {"type":"separator","margin":"md","color":C['sep']},
                    {"type":"box","layout":"horizontal","contents":[
                        {"type":"text","text":"🎮 الألعاب","size":"sm","color":C['text2'],"flex":1},
                        {"type":"text","text":str(stats['games_played']),"size":"lg","color":C['text'],"flex":1,"align":"end"}
                    ],"margin":"md"},
                    {"type":"box","layout":"horizontal","contents":[
                        {"type":"text","text":"🏆 الفوز","size":"sm","color":C['text2'],"flex":1},
                        {"type":"text","text":str(stats['wins']),"size":"lg","color":C['text'],"flex":1,"align":"end"}
                    ],"margin":"sm"},
                    {"type":"box","layout":"horizontal","contents":[
                        {"type":"text","text":"📈 المعدل","size":"sm","color":C['text2'],"flex":1},
                        {"type":"text","text":f"{wr:.0f}%","size":"lg","color":C['text'],"flex":1,"align":"end"}
                    ],"margin":"sm"}
                ])
            ],
            "backgroundColor":C['bg'],
            "paddingAll":"24px"
        }
    }

def leaderboard_card():
    leaders = get_leaderboard()
    if not leaders:
        return {
            "type":"bubble",
            "size":"kilo",
            "body":{
                "type":"box",
                "layout":"vertical",
                "contents":[
                    {"type":"text","text":"🏆 لوحة الصدارة","size":"xl","weight":"bold","color":C['cyan'],"align":"center"},
                    {"type":"separator","margin":"lg","color":C['sep']},
                    {"type":"text","text":"لا توجد بيانات","size":"md","color":C['text2'],"align":"center","margin":"lg"}
                ],
                "backgroundColor":C['bg'],
                "paddingAll":"24px"
            }
        }
    
    items = []
    for i,l in enumerate(leaders,1):
        rank = ["🥇","🥈","🥉"][i-1] if i<=3 else f"#{i}"
        items.append({
            "type":"box",
            "layout":"horizontal",
            "contents":[
                {"type":"text","text":rank,"size":"md" if i<=3 else "sm","weight":"bold","flex":0,"color":C['cyan'] if i<=3 else C['text']},
                {"type":"text","text":l['display_name'],"size":"sm","flex":3,"margin":"md","wrap":True,"color":C['cyan'] if i==1 else C['text']},
                {"type":"text","text":str(l['total_points']),"size":"lg" if i==1 else "md","weight":"bold","flex":1,"align":"end","color":C['cyan_glow'] if i==1 else C['text2']}
            ],
            "backgroundColor":C['card'] if i<=3 else C['card2'],
            "cornerRadius":"12px",
            "paddingAll":"14px",
            "margin":"sm" if i>1 else "md",
            "borderWidth":"2px" if i==1 else "1px",
            "borderColor":C['cyan'] if i==1 else C['border']
        })
    
    return {
        "type":"bubble",
        "size":"kilo",
        "body":{
            "type":"box",
            "layout":"vertical",
            "contents":[
                {"type":"text","text":"🏆 لوحة الصدارة","size":"xl","weight":"bold","color":C['cyan'],"align":"center"},
                {"type":"separator","margin":"lg","color":C['sep']},
                {"type":"text","text":"أفضل اللاعبين","size":"sm","color":C['text2'],"align":"center","margin":"md"},
                {"type":"box","layout":"vertical","contents":items,"margin":"md"}
            ],
            "backgroundColor":C['bg'],
            "paddingAll":"24px"
        }
    }

# استيراد الألعاب
try:
    from games import start_game, check_game_answer
    GAMES_LOADED = True
    logger.info("✅ ملف الألعاب محمل")
except ImportError:
    logger.warning("⚠️ games.py غير موجود")
    GAMES_LOADED = False

# معالج الرسائل
CMDS = [
    'البداية','ابدأ','start','مساعدة','help','انضم','join','انسحب','خروج',
    'نقاطي','إحصائياتي','الصدارة','المتصدرين','إيقاف','stop',
    'أغنية','لعبة','سلسلة','أسرع','ضد','تكوين','ترتيب','كلمة','لون',
    'سؤال','سوال','تحدي','اعتراف','منشن','اختلاف','توافق',
    'لمح','تلميح','جاوب','الحل','الجواب'
]

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        uid = event.source.user_id
        txt = safe_text(event.message.text, 500)
        
        if not txt or not any(c.lower() in txt.lower() for c in CMDS):
            return
        
        if not rate_limiter.is_allowed(uid):
            return
        
        name = get_profile(uid)
        update_user(uid, name)
        metrics.log_msg(uid)
        
        if uid not in registered_players and get_stats(uid):
            registered_players.add(uid)
        
        gid = getattr(event.source, 'group_id', uid)
        
        # أوامر أساسية
        if txt in ['البداية','ابدأ','start']:
            return line_bot_api.reply_message(
                event.reply_token, 
                FlexSendMessage(alt_text="بوت الحوت", contents=welcome_card(), quick_reply=get_qr())
            )
        
        if txt in ['مساعدة','help']:
            return line_bot_api.reply_message(
                event.reply_token, 
                FlexSendMessage(alt_text="المساعدة", contents=help_card(), quick_reply=get_qr())
            )
        
        if txt in ['نقاطي','إحصائياتي','احصائياتي']:
            return line_bot_api.reply_message(
                event.reply_token, 
                FlexSendMessage(
                    alt_text="إحصائياتك", 
                    contents=stats_card(uid, name, uid in registered_players), 
                    quick_reply=get_qr()
                )
            )
        
        if txt in ['الصدارة','المتصدرين']:
            return line_bot_api.reply_message(
                event.reply_token, 
                FlexSendMessage(alt_text="الصدارة", contents=leaderboard_card(), quick_reply=get_qr())
            )
        
        if txt in ['إيقاف','stop','ايقاف']:
            g = active_games.pop(gid, None)
            return line_bot_api.reply_message(
                event.reply_token, 
                TextSendMessage(text=f"⏹️ تم إيقاف {g['type']}" if g else "لا توجد لعبة", quick_reply=get_qr())
            )
        
        if txt in ['انضم','تسجيل','join']:
            if uid in registered_players:
                return line_bot_api.reply_message(
                    event.reply_token, 
                    TextSendMessage(text=f"✓ أنت مسجل يا {name}", quick_reply=get_qr())
                )
            registered_players.add(uid)
            logger.info(f"✅ تسجيل: {name}")
            return line_bot_api.reply_message(
                event.reply_token, 
                TextSendMessage(text=f"✅ تم تسجيلك يا {name}\nابدأ اللعب الآن!", quick_reply=get_qr())
            )
        
        if txt in ['انسحب','خروج']:
            if uid not in registered_players:
                return line_bot_api.reply_message(
                    event.reply_token, 
                    TextSendMessage(text="غير مسجل", quick_reply=get_qr())
                )
            registered_players.remove(uid)
            return line_bot_api.reply_message(
                event.reply_token, 
                TextSendMessage(text=f"👋 تم انسحابك", quick_reply=get_qr())
            )
        
        # محتوى نصي
        if txt in ['سؤال','سوال']:
            return line_bot_api.reply_message(
                event.reply_token, 
                TextSendMessage(text=next_content(QUESTIONS,'q_idx'), quick_reply=get_qr())
            )
        
        if txt in ['تحدي','challenge']:
            return line_bot_api.reply_message(
                event.reply_token, 
                TextSendMessage(text=next_content(CHALLENGES,'c_idx'), quick_reply=get_qr())
            )
        
        if txt in ['اعتراف','confession']:
            return line_bot_api.reply_message(
                event.reply_token, 
                TextSendMessage(text=next_content(CONFESSIONS,'cf_idx'), quick_reply=get_qr())
            )
        
        if txt in ['منشن','mention']:
            return line_bot_api.reply_message(
                event.reply_token, 
                TextSendMessage(text=next_content(MENTIONS,'m_idx'), quick_reply=get_qr())
            )
        
        # ألعاب
        is_reg = uid in registered_players
        if GAMES_LOADED:
            gmap = {
                'أغنية':'song',
                'لعبة':'game',
                'سلسلة':'chain',
                'أسرع':'fast',
                'ضد':'opposite',
                'تكوين':'build',
                'ترتيب':'order',
                'كلمة':'word',
                'لون':'color',
                'اختلاف':'diff',
                'توافق':'compat'
            }
            
            if txt in gmap:
                if not is_reg:
                    return line_bot_api.reply_message(
                        event.reply_token, 
                        TextSendMessage(text="⚠️ سجل أولاً: انضم", quick_reply=get_qr())
                    )
                
                r = start_game(gmap[txt], gid, active_games, line_bot_api, gemini.ask if gemini else None)
                if r:
                    metrics.log_game(gmap[txt])
                    return line_bot_api.reply_message(event.reply_token, r)
            
            if gid in active_games and is_reg:
                r = check_game_answer(gid, txt, uid, name, active_games, line_bot_api, update_points)
                if r:
                    return line_bot_api.reply_message(event.reply_token, r)
    
    except Exception as e:
        logger.error(f"❌ معالجة: {e}", exc_info=True)

# Routes
@app.route("/", methods=['GET'])
def home():
    m = metrics.stats()
    uptime_hours = int(m['uptime']/3600)
    uptime_mins = int((m['uptime']%3600)/60)
    
    return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>♓ بوت الحوت - تصميم ثري دي</title>
    <style>
        * {{margin:0;padding:0;box-sizing:border-box}}
        body {{
            font-family:'Segoe UI',Tahoma,sans-serif;
            background:#0A0E27;
            min-height:100vh;
            display:flex;
            align-items:center;
            justify-content:center;
            overflow:hidden;
            position:relative
        }}
        .background {{
            position:fixed;
            width:100%;
            height:100%;
            top:0;
            left:0;
            background:radial-gradient(ellipse at center,#0F1629 0%,#0A0E27 100%)
        }}
        .particles {{position:fixed;width:100%;height:100%;top:0;left:0}}
        .particle {{
            position:absolute;
            width:3px;
            height:3px;
            background:#00D9FF;
            border-radius:50%;
            animation:float 15s infinite ease-in-out;
            box-shadow:0 0 10px #00D9FF,0 0 20px #00D9FF
        }}
        @keyframes float {{
            0%,100%{{transform:translateY(0) translateX(0) scale(1);opacity:0}}
            10%{{opacity:0.8}}
            50%{{transform:translateY(-50vh) translateX(30px) scale(1.5);opacity:1}}
            90%{{opacity:0.8}}
        }}
        .container {{
            position:relative;
            z-index:10;
            width:90%;
            max-width:900px;
            padding:40px
        }}
        .main-circle {{
            position:relative;
            width:350px;
            height:350px;
            margin:0 auto 50px;
            display:flex;
            align-items:center;
            justify-content:center;
            animation:rotate360 30s linear infinite
        }}
        @keyframes rotate360 {{from{{transform:rotate(0deg)}}to{{transform:rotate(360deg)}}}}
        .outer-ring {{
            position:absolute;
            width:100%;
            height:100%;
            border:3px solid #00D9FF;
            border-radius:50%;
            box-shadow:0 0 30px rgba(0,217,255,0.6),0 0 60px rgba(0,217,255,0.4),inset 0 0 30px rgba(0,217,255,0.2);
            animation:pulse-ring 3s ease-in-out infinite
        }}
        @keyframes pulse-ring {{
            0%,100%{{transform:scale(1);opacity:0.8}}
            50%{{transform:scale(1.05);opacity:1}}
        }}
        .circle-particles {{
            position:absolute;
            width:120%;
            height:120%;
            animation:rotate360 20s linear infinite reverse
        }}
        .circle-particle {{
            position:absolute;
            width:8px;
            height:8px;
            background:#5EEBFF;
            border-radius:50%;
            box-shadow:0 0 15px #5EEBFF,0 0 30px #00D9FF;
            animation:particle-pulse 2s ease-in-out infinite
        }}
        @keyframes particle-pulse {{
            0%,100%{{transform:scale(1);opacity:0.6}}
            50%{{transform:scale(1.5);opacity:1}}
        }}
        .circle-particle:nth-child(1){{top:0;left:50%;margin-left:-4px;animation-delay:0s}}
        .circle-particle:nth-child(2){{top:15%;right:15%;animation-delay:0.25s}}
        .circle-particle:nth-child(3){{top:50%;right:0;margin-top:-4px;animation-delay:0.5s}}
        .circle-particle:nth-child(4){{bottom:15%;right:15%;animation-delay:0.75s}}
        .circle-particle:nth-child(5){{bottom:0;left:50%;margin-left:-4px;animation-delay:1s}}
        .circle-particle:nth-child(6){{bottom:15%;left:15%;animation-delay:1.25s}}
        .circle-particle:nth-child(7){{top:50%;left:0;margin-top:-4px;animation-delay:1.5s}}
        .circle-particle:nth-child(8){{top:15%;left:15%;animation-delay:1.75s}}
        .logo-container {{
            position:relative;
            width:200px;
            height:200px;
            background:linear-gradient(135deg,rgba(15,40,71,0.9) 0%,rgba(10,22,40,0.9) 100%);
            border-radius:50%;
            display:flex;
            align-items:center;
            justify-content:center;
            box-shadow:0 0 60px rgba(0,217,255,0.5),0 0 100px rgba(94,235,255,0.3),inset 0 0 50px rgba(0,217,255,0.1);
            border:2px solid rgba(0,217,255,0.3);
            backdrop-filter:blur(20px);
            animation:logo-float 6s ease-in-out infinite
        }}
        @keyframes logo-float {{
            0%,100%{{transform:translateY(0px) rotate(0deg)}}
            50%{{transform:translateY(-20px) rotate(5deg)}}
        }}
        .logo-container::before {{
            content:'';
            position:absolute;
            width:100%;
            height:100%;
            border-radius:50%;
            background:radial-gradient(circle at 30% 30%,rgba(94,235,255,0.4),transparent 60%);
            animation:shine 4s ease-in-out infinite
        }}
        @keyframes shine {{
            0%,100%{{opacity:0.3}}
            50%{{opacity:0.8}}
        }}
        .pisces-logo {{
            font-size:100px;
            filter:drop-shadow(0 0 40px rgba(0,217,255,1)) drop-shadow(0 0 60px rgba(94,235,255,0.8)) drop-shadow(0 0 80px rgba(0,217,255,0.6));
            animation:logo-glow 3s ease-in-out infinite
        }}
        @keyframes logo-glow {{
            0%,100%{{filter:drop-shadow(0 0 40px rgba(0,217,255,1)) drop-shadow(0 0 60px rgba(94,235,255,0.8))}}
            50%{{filter:drop-shadow(0 0 50px rgba(0,217,255,1)) drop-shadow(0 0 80px rgba(94,235,255,1)) drop-shadow(0 0 100px rgba(0,217,255,0.8))}}
        }}
        .glass-card {{
            background:linear-gradient(135deg,rgba(15,40,71,0.7) 0%,rgba(10,22,40,0.5) 100%);
            border-radius:30px;
            padding:40px;
            backdrop-filter:blur(30px);
            border:2px solid rgba(0,217,255,0.3);
            box-shadow:0 0 60px rgba(0,217,255,0.4),0 20px 80px rgba(0,0,0,0.6),inset 0 0 30px rgba(0,217,255,0.1);
            position:relative;
            overflow:hidden;
            animation:card-appear 1s ease-out
        }}
        @keyframes card-appear {{
            from{{opacity:0;transform:translateY(30px)}}
            to{{opacity:1;transform:translateY(0)}}
        }}
        .glass-card::before {{
            content:'';
            position:absolute;
            top:-50%;
            left:-50%;
            width:200%;
            height:200%;
            background:linear-gradient(45deg,transparent 30%,rgba(94,235,255,0.1) 50%,transparent 70%);
            animation:shine-sweep 5s ease-in-out infinite
        }}
        @keyframes shine-sweep {{
            0%{{transform:translateX(-100%) translateY(-100%) rotate(45deg)}}
            100%{{transform:translateX(100%) translateY(100%) rotate(45deg)}}
        }}
        .title {{
            font-size:48px;
            font-weight:900;
            text-align:center;
            color:#00D9FF;
            margin-bottom:15px;
            text-shadow:0 0 30px rgba(0,217,255,0.8),0 0 50px rgba(94,235,255,0.6),0 0 70px rgba(0,217,255,0.4);
            animation:title-glow 3s ease-in-out infinite
        }}
        @keyframes title-glow {{
            0%,100%{{text-shadow:0 0 30px rgba(0,217,255,0.8),0 0 50px rgba(94,235,255,0.6)}}
            50%{{text-shadow:0 0 40px rgba(0,217,255,1),0 0 70px rgba(94,235,255,0.8),0 0 100px rgba(0,217,255,0.6)}}
        }}
        .subtitle {{
            font-size:18px;
            text-align:center;
            color:#7FB3D5;
            margin-bottom:40px;
            letter-spacing:2px
        }}
        .status-grid {{
            display:grid;
            grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
            gap:20px;
            margin-top:40px
        }}
        .status-item {{
            background:linear-gradient(135deg,rgba(15,40,71,0.6) 0%,rgba(10,22,40,0.4) 100%);
            border-radius:20px;
            padding:25px;
            border:1px solid rgba(0,217,255,0.2);
            backdrop-filter:blur(10px);
            box-shadow:0 0 30px rgba(0,217,255,0.2),inset 0 0 20px rgba(0,217,255,0.05);
            transition:all 0.3s ease
        }}
        .status-item:hover {{
            transform:translateY(-5px);
            border-color:rgba(0,217,255,0.5);
            box-shadow:0 0 40px rgba(0,217,255,0.4),0 10px 30px rgba(0,217,255,0.3)
        }}
        .status-label {{
            font-size:14px;
            color:#7FB3D5;
            margin-bottom:10px;
            display:flex;
            align-items:center;
            gap:8px
        }}
        .status-value {{
            font-size:32px;
            font-weight:900;
            color:#5EEBFF;
            text-shadow:0 0 20px rgba(94,235,255,0.6)
        }}
        .badge {{
            padding:6px 14px;
            border-radius:20px;
            font-size:14px;
            font-weight:600;
            display:inline-block;
            margin-top:10px
        }}
        .success {{
            background:rgba(0,229,160,0.2);
            color:#00E5A0;
            box-shadow:0 0 20px rgba(0,229,160,0.4);
            border:1px solid rgba(0,229,160,0.3)
        }}
        .warning {{
            background:rgba(139,127,255,0.2);
            color:#8B7FFF;
            box-shadow:0 0 20px rgba(139,127,255,0.4);
            border:1px solid rgba(139,127,255,0.3)
        }}
        .footer {{
            text-align:center;
            margin-top:40px;
            color:#2C5F8D;
            font-size:14px
        }}
        .footer a {{
            color:#00D9FF;
            text-decoration:none;
            transition:color 0.3s
        }}
        .footer a:hover {{color:#5EEBFF}}
        @media (max-width:768px) {{
            .main-circle {{width:280px;height:280px}}
            .logo-container {{width:160px;height:160px}}
            .pisces-logo {{font-size:80px}}
            .title {{font-size:36px}}
            .glass-card {{padding:30px 20px}}
        }}
    </style>
</head>
<body>
    <div class="background"></div>
    <div class="particles" id="particles"></div>
    <div class="container">
        <div class="main-circle">
            <div class="outer-ring"></div>
            <div class="circle-particles">
                <div class="circle-particle"></div>
                <div class="circle-particle"></div>
                <div class="circle-particle"></div>
                <div class="circle-particle"></div>
                <div class="circle-particle"></div>
                <div class="circle-particle"></div>
                <div class="circle-particle"></div>
                <div class="circle-particle"></div>
            </div>
            <div class="logo-container">
                <div class="pisces-logo">{PISCES_LOGO}</div>
            </div>
        </div>
        <div class="glass-card">
            <h1 class="title">بوت الحوت</h1>
            <p class="subtitle">نظام ألعاب تفاعلية ثري دي v3.2</p>
            <div class="status-grid">
                <div class="status-item">
                    <div class="status-label">⚡ حالة الخادم</div>
                    <div class="status-value">نشط</div>
                    <span class="badge success">يعمل</span>
                </div>
                <div class="status-item">
                    <div class="status-label">🤖 الذكاء الاصطناعي</div>
                    <div class="status-value">{'مفعّل' if USE_AI else 'معطّل'}</div>
                    <span class="badge {'success' if USE_AI else 'warning'}">{'AI ✓' if USE_AI else 'AI ✗'}</span>
                </div>
                <div class="status-item">
                    <div class="status-label">👥 اللاعبون المسجلون</div>
                    <div class="status-value">{len(registered_players)}</div>
                </div>
                <div class="status-item">
                    <div class="status-label">🎮 الألعاب النشطة</div>
                    <div class="status-value">{len(active_games)}</div>
                </div>
                <div class="status-item">
                    <div class="status-label">💬 إجمالي الرسائل</div>
                    <div class="status-value">{m['total_msgs']}</div>
                </div>
                <div class="status-item">
                    <div class="status-label">📊 إجمالي الألعاب</div>
                    <div class="status-value">{m['total_games']}</div>
                </div>
                <div class="status-item">
                    <div class="status-label">⏱ وقت التشغيل</div>
                    <div class="status-value">{uptime_hours}س {uptime_mins}د</div>
                </div>
            </div>
            <div class="footer">
                بوت الحوت v3.2 © 2025 | تصميم ثري دي زجاجي<br>
                <a href="/health">Health Check</a>
            </div>
        </div>
    </div>
    <script>
        const pc=document.getElementById('particles');
        for(let i=0;i<50;i++){{
            const p=document.createElement('div');
            p.className='particle';
            p.style.left=Math.random()*100+'%';
            p.style.animationDelay=Math.random()*15+'s';
            p.style.animationDuration=(15+Math.random()*10)+'s';
            pc.appendChild(p);
        }}
    </script>
</body>
</html>"""

@app.route("/health", methods=['GET'])
def health():
    m = metrics.stats()
    return {{
        "status": "healthy",
        "version": "3.2.0",
        "design": "3D Glass Morphism",
        "timestamp": datetime.now().isoformat(),
        "active_games": len(active_games),
        "registered_players": len(registered_players),
        "ai_enabled": USE_AI,
        "games_loaded": GAMES_LOADED,
        "metrics": {{
            "uptime_seconds": m['uptime'],
            "total_messages": m['total_msgs'],
            "total_games": m['total_games']
        }},
        "colors": C,
        "logo": PISCES_LOGO
    }}

@app.route("/callback", methods=['POST'])
def callback():
    if not handler or not line_bot_api:
        abort(500)
    
    sig = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, sig)
    except InvalidSignatureError:
        logger.error("❌ توقيع غير صالح")
        abort(400)
    except Exception as e:
        logger.error(f"❌ webhook: {{e}}")
    
    return 'OK'

@app.errorhandler(404)
def not_found(e):
    return {{"error": "الصفحة غير موجودة", "status": 404}}, 404

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"❌ خطأ: {{e}}")
    return {{"error": "خطأ داخلي في الخادم", "status": 500}}, 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"❌ خطأ غير متوقع: {{e}}", exc_info=True)
    return 'OK', 200

# التشغيل
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print(f"\n{{'='*60}}")
    print(f"{{PISCES_LOGO}} بوت الحوت v3.2 - تصميم ثري دي زجاجي {{PISCES_LOGO}}")
    print(f"{{'='*60}}")
    print(f"🌐 المنفذ: {{port}}")
    print(f"🤖 الذكاء الاصطناعي: {{'مفعّل ✓' if USE_AI else 'معطّل ✗'}}")
    print(f"🎮 الألعاب: {{'متوفرة ✓' if GAMES_LOADED else 'غير متوفرة ✗'}}")
    print(f"🎨 التصميم: ثري دي زجاجي متوهج")
    print(f"{{'='*60}}\n")
    
    try:
        logger.info(f"🚀 بدء الخادم على المنفذ {{port}}")
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("⏹️ تم إيقاف الخادم بواسطة المستخدم")
        cleanup_inactive()
    except Exception as e:
        logger.critical(f"❌ فشل التشغيل: {{e}}")
        sys.exit(1)
