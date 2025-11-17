"""بوت الحوت v3.1 - نظام ألعاب تفاعلية محسّن"""
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage, QuickReply, QuickReplyButton, MessageAction
import os, sqlite3, logging, sys, threading, time, re
from datetime import datetime, timedelta
from collections import defaultdict, deque, Counter
from functools import lru_cache
from queue import Queue

# إعداد Logging محسّن
os.makedirs('logs', exist_ok=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s',
                   handlers=[logging.StreamHandler(sys.stdout),
                           logging.handlers.RotatingFileHandler('logs/bot.log', maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')])
logger = logging.getLogger("whale-bot")

print("\n" + "═"*60 + "\nبوت الحوت v3.1 - محسّن\n" + "═"*60 + "\n")

# الإعدادات
LINE_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_SECRET = os.getenv('LINE_CHANNEL_SECRET')
GEMINI_KEYS = [k for k in [os.getenv(f'GEMINI_API_KEY_{i}', '') for i in range(1,4)] if k]

app = Flask(__name__)
line_bot_api = LineBotApi(LINE_TOKEN) if LINE_TOKEN else None
handler = WebhookHandler(LINE_SECRET) if LINE_SECRET else None

# بيانات مشتركة
active_games = {}
registered_players = set()

# Rate Limiter محسّن
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
    
    def log_msg(self, uid): self.msgs[uid] += 1
    def log_game(self, gtype): self.games[gtype] += 1
    def stats(self): 
        return {'uptime': (datetime.now()-self.start).total_seconds(), 
                'total_msgs': sum(self.msgs.values()), 
                'total_games': sum(self.games.values())}

metrics = Metrics()

# Gemini AI محسّن
USE_AI, model = False, None
try:
    import google.generativeai as genai
    if GEMINI_KEYS:
        genai.configure(api_key=GEMINI_KEYS[0])
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        USE_AI = True
        logger.info(f"Gemini جاهز ({len(GEMINI_KEYS)} مفاتيح)")
except Exception as e:
    logger.warning(f"Gemini معطّل: {e}")

class GeminiClient:
    def __init__(self, keys):
        self.keys, self.idx, self.lock = keys, 0, threading.Lock()
    
    def ask(self, prompt):
        if not USE_AI or not self.keys: return None
        for _ in range(len(self.keys)):
            try:
                r = model.generate_content(prompt)
                if r and r.text: return r.text.strip()[:1000]
            except Exception as e:
                logger.error(f"Gemini خطأ: {e}")
                with self.lock:
                    self.idx = (self.idx + 1) % len(self.keys)
                    genai.configure(api_key=self.keys[self.idx])
        return None

gemini = GeminiClient(GEMINI_KEYS) if GEMINI_KEYS else None

# قاعدة بيانات محسّنة
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
        return dict(c.fetchone()) if c.rowcount else None
    
    def fetchall(self, query, params=()):
        c = self.execute(query, params)
        return [dict(r) for r in c.fetchall()]

def init_db():
    try:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS players (
            user_id TEXT PRIMARY KEY, display_name TEXT NOT NULL,
            total_points INTEGER DEFAULT 0, games_played INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0, last_active TEXT DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_points ON players(total_points DESC)')
        conn.commit()
        conn.close()
        logger.info("قاعدة البيانات جاهزة")
        return True
    except Exception as e:
        logger.error(f"DB خطأ: {e}")
        return False

init_db()
db = DBPool(DB)

# دوال مساعدة محسّنة
def safe_text(t, max_len=500):
    return str(t or "").strip()[:max_len].replace('"','').replace("'",'')

@lru_cache(maxsize=1000)
def normalize_text(t):
    if not t: return ""
    t = t.strip().lower()
    t = re.sub('[أإآ]','ا',t); t = re.sub('[ؤ]','و',t); t = re.sub('[ئ]','ي',t)
    t = re.sub('[ءةى]','',t); t = re.sub('[\u064B-\u065F]','',t)
    return re.sub(r'\s+',' ',t).strip()

def get_profile(uid):
    if not line_bot_api: return f"مستخدم{uid[-4:]}"
    try:
        p = line_bot_api.get_profile(uid)
        return safe_text(p.display_name,50) if p.display_name else f"مستخدم{uid[-4:]}"
    except: return f"مستخدم{uid[-4:]}"

# إدارة المستخدمين
def update_user(uid, name):
    try:
        db.execute('INSERT OR REPLACE INTO players (user_id,display_name,last_active) VALUES (?,?,?)',
                  (uid, safe_text(name,100), datetime.now().isoformat()))
    except Exception as e: logger.error(f"تحديث خطأ: {e}")

def update_points(uid, name, pts, won=False):
    try:
        r = db.fetchone('SELECT total_points,games_played,wins FROM players WHERE user_id=?', (uid,))
        if r:
            db.execute('UPDATE players SET total_points=?,games_played=?,wins=?,last_active=?,display_name=? WHERE user_id=?',
                      (max(0,r['total_points']+pts), r['games_played']+1, r['wins']+(1 if won else 0),
                       datetime.now().isoformat(), safe_text(name,100), uid))
        else:
            db.execute('INSERT INTO players VALUES (?,?,?,1,?,?)',
                      (uid, safe_text(name,100), max(0,pts), 1 if won else 0, datetime.now().isoformat()))
    except Exception as e: logger.error(f"نقاط خطأ: {e}")

def get_stats(uid):
    return db.fetchone('SELECT * FROM players WHERE user_id=?', (uid,))

def get_leaderboard(limit=10):
    return db.fetchall('SELECT display_name,total_points,games_played,wins FROM players WHERE total_points>0 ORDER BY total_points DESC,wins DESC LIMIT ?', (limit,))

def cleanup_inactive():
    try:
        cutoff = (datetime.now()-timedelta(days=45)).isoformat()
        c = db.execute('DELETE FROM players WHERE last_active<?', (cutoff,))
        if c.rowcount: logger.info(f"حذف {c.rowcount} مستخدم غير نشط")
    except Exception as e: logger.error(f"تنظيف خطأ: {e}")

threading.Thread(target=lambda: [time.sleep(21600) or cleanup_inactive() for _ in iter(int,1)], daemon=True).start()

# المحتوى
def load_txt(name):
    try:
        with open(f'{name}.txt','r',encoding='utf-8') as f:
            return [l.strip() for l in f if l.strip()]
    except FileNotFoundError:
        logger.warning(f"{name}.txt غير موجود")
        return []

QUESTIONS, CHALLENGES, CONFESSIONS, MENTIONS = [load_txt(x) for x in ['questions','challenges','confessions','mentions']]
q_idx = c_idx = cf_idx = m_idx = 0

def next_content(items, idx_name):
    global q_idx, c_idx, cf_idx, m_idx
    idx = globals()[idx_name]
    if not items: return "محتوى افتراضي"
    r = items[idx % len(items)]
    globals()[idx_name] += 1
    return r

# Quick Reply
def get_qr():
    btns = ["أغنية","لعبة","سلسلة","أسرع","ضد","تكوين","ترتيب","كلمة","لون","سؤال","تحدي","اعتراف","منشن"]
    return QuickReply(items=[QuickReplyButton(action=MessageAction(label=f"▫️ {b}",text=b)) for b in btns])

# Flex Cards مضغوطة
C = {'bg':'#0F172A','card':'#1E293B','text':'#F1F5F9','text2':'#94A3B8','sep':'#334155','btn':'#06B6D4'}

def create_card(title, body_contents, footer_btns=None):
    return {"type":"bubble","size":"kilo",
            "body":{"type":"box","layout":"vertical","contents":[
                {"type":"text","text":title,"size":"xl","weight":"bold","color":C['text'],"align":"center"},
                {"type":"separator","margin":"lg","color":C['sep']}] + body_contents,
                "paddingAll":"24px","backgroundColor":C['bg']},
            "footer":{"type":"box","layout":"vertical",
                     "contents":[{"type":"button","action":{"type":"message","label":b[0],"text":b[1]},
                                 "style":"primary" if i==0 else "secondary","color":C['btn'] if i==0 else None,
                                 "margin":"sm" if i>0 else None} for i,b in enumerate(footer_btns)],
                     "paddingAll":"16px","backgroundColor":C['bg']} if footer_btns else None}

def welcome_card():
    games = "▫️ أغنية: خمن المغني\n▫️ لعبة: إنسان حيوان نبات\n▫️ سلسلة: كلمة بآخر حرف\n▫️ أسرع: أسرع إجابة\n▫️ ضد: عكس الكلمة\n▫️ تكوين | ترتيب | كلمة | لون"
    fun = "▫️ سؤال | تحدي | اعتراف | منشن"
    return create_card("بوت الحوت", [
        {"type":"box","layout":"vertical","contents":[
            {"type":"box","layout":"horizontal","contents":[
                {"type":"box","layout":"vertical","contents":[
                    {"type":"text","text":"♓","size":"4xl","color":C['btn'],"align":"center","weight":"bold"}
                ],"width":"80px","height":"80px","backgroundColor":C['card'],"cornerRadius":"40px",
                "justifyContent":"center","alignItems":"center","offsetTop":"0px"}
            ],"justifyContent":"center","alignItems":"center"},
            {"type":"text","text":"نظام ألعاب تفاعلية","size":"sm","color":C['text2'],"align":"center","margin":"md"}
        ],"margin":"lg"},
        {"type":"box","layout":"vertical","contents":[
            {"type":"text","text":"الألعاب","size":"md","weight":"bold","color":C['text']},
            {"type":"text","text":games,"size":"xs","color":C['text2'],"wrap":True,"margin":"md"}
        ],"backgroundColor":C['card'],"cornerRadius":"12px","paddingAll":"16px","margin":"lg"},
        {"type":"box","layout":"vertical","contents":[
            {"type":"text","text":"التسلية (بدون نقاط)","size":"md","weight":"bold","color":C['text']},
            {"type":"text","text":fun,"size":"xs","color":C['text2'],"wrap":True,"margin":"md"}
        ],"backgroundColor":C['card'],"cornerRadius":"12px","paddingAll":"16px","margin":"md"}
    ], [("المساعدة","مساعدة"),("نقاطي","نقاطي"),("الصدارة","الصدارة")])

def help_card():
    return create_card("المساعدة", [
        {"type":"box","layout":"vertical","contents":[
            {"type":"text","text":"أوامر اللعب","size":"md","weight":"bold","color":C['text']},
            {"type":"text","text":"▫️ لمح: تلميح (-1)\n▫️ جاوب: عرض الحل\n▫️ إيقاف: إنهاء","size":"xs","color":C['text2'],"wrap":True,"margin":"md"}
        ],"backgroundColor":C['card'],"cornerRadius":"12px","paddingAll":"16px","margin":"lg"},
        {"type":"box","layout":"vertical","contents":[
            {"type":"text","text":"الإحصائيات","size":"md","weight":"bold","color":C['text']},
            {"type":"text","text":"▫️ نقاطي | الصدارة","size":"xs","color":C['text2'],"wrap":True,"margin":"md"}
        ],"backgroundColor":C['card'],"cornerRadius":"12px","paddingAll":"16px","margin":"md"}
    ], [("انضم","انضم"),("نقاطي","نقاطي")])

def stats_card(uid, name, is_reg):
    stats = get_stats(uid)
    if not stats:
        return create_card("إحصائياتك", [
            {"type":"text","text":name,"size":"md","color":C['text'],"align":"center","margin":"lg"},
            {"type":"text","text":"مسجل" if is_reg else "غير مسجل","size":"xs","color":"#34C759" if is_reg else C['text2'],"align":"center","margin":"sm"},
            {"type":"text","text":"لم تبدأ بعد" if is_reg else "سجل أولاً","size":"md","color":C['text2'],"align":"center","margin":"lg"}
        ], [("انضم","انضم")] if not is_reg else None)
    
    wr = (stats['wins']/stats['games_played']*100) if stats['games_played']>0 else 0
    return create_card("إحصائياتك", [
        {"type":"text","text":name,"size":"md","color":C['text'],"align":"center","margin":"lg"},
        {"type":"box","layout":"vertical","contents":[
            {"type":"box","layout":"horizontal","contents":[
                {"type":"text","text":"النقاط","size":"sm","color":C['text2'],"flex":1},
                {"type":"text","text":str(stats['total_points']),"size":"xxl","weight":"bold","color":C['btn'],"flex":1,"align":"end"}
            ]},
            {"type":"separator","margin":"lg","color":C['sep']},
            {"type":"box","layout":"horizontal","contents":[
                {"type":"text","text":"الألعاب","size":"sm","color":C['text2'],"flex":1},
                {"type":"text","text":str(stats['games_played']),"size":"md","color":C['text'],"flex":1,"align":"end"}
            ],"margin":"lg"},
            {"type":"box","layout":"horizontal","contents":[
                {"type":"text","text":"الفوز","size":"sm","color":C['text2'],"flex":1},
                {"type":"text","text":str(stats['wins']),"size":"md","color":C['text'],"flex":1,"align":"end"}
            ],"margin":"md"},
            {"type":"box","layout":"horizontal","contents":[
                {"type":"text","text":"معدل الفوز","size":"sm","color":C['text2'],"flex":1},
                {"type":"text","text":f"{wr:.0f}%","size":"md","color":C['text'],"flex":1,"align":"end"}
            ],"margin":"md"}
        ],"backgroundColor":C['card'],"cornerRadius":"12px","paddingAll":"16px","margin":"lg"}
    ], [("الصدارة","الصدارة")])

def leaderboard_card():
    leaders = get_leaderboard()
    if not leaders:
        return create_card("لوحة الصدارة", [{"type":"text","text":"لا توجد بيانات","size":"md","color":C['text2'],"align":"center","margin":"lg"}])
    
    items = []
    for i,l in enumerate(leaders,1):
        rank = ["🥇","🥈","🥉"][i-1] if i<=3 else str(i)
        items.append({"type":"box","layout":"horizontal","contents":[
            {"type":"text","text":rank,"size":"sm","weight":"bold","flex":0,"color":C['text']},
            {"type":"text","text":l['display_name'],"size":"sm","flex":3,"margin":"md","wrap":True,"color":C['text']},
            {"type":"text","text":str(l['total_points']),"size":"sm","weight":"bold","flex":1,"align":"end","color":C['btn']}
        ],"backgroundColor":C['card'],"cornerRadius":"12px","paddingAll":"12px","margin":"sm" if i>1 else "md"})
    
    return create_card("لوحة الصدارة", [
        {"type":"text","text":"أفضل اللاعبين","size":"sm","color":C['text2'],"align":"center","margin":"md"},
        {"type":"box","layout":"vertical","contents":items,"margin":"lg"}
    ])

# استيراد الألعاب
try:
    from games import start_game, check_game_answer
    GAMES_LOADED = True
except ImportError:
    logger.warning("games.py غير موجود")
    GAMES_LOADED = False

# معالج الرسائل
CMDS = ['البداية','ابدأ','start','مساعدة','help','انضم','join','انسحب','خروج',
        'نقاطي','إحصائياتي','الصدارة','المتصدرين','إيقاف','stop',
        'أغنية','لعبة','سلسلة','أسرع','ضد','تكوين','ترتيب','كلمة','لون',
        'سؤال','سوال','تحدي','اعتراف','منشن','اختلاف','توافق',
        'لمح','تلميح','جاوب','الحل','الجواب']

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        uid, txt = event.source.user_id, safe_text(event.message.text,500)
        if not txt or not any(c.lower() in txt.lower() for c in CMDS): return
        if not rate_limiter.is_allowed(uid): return
        
        name = get_profile(uid)
        update_user(uid, name)
        metrics.log_msg(uid)
        
        if uid not in registered_players and get_stats(uid):
            registered_players.add(uid)
        
        gid = getattr(event.source,'group_id',uid)
        
        # أوامر أساسية
        if txt in ['البداية','ابدأ','start']:
            return line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="بوت الحوت",contents=welcome_card(),quick_reply=get_qr()))
        if txt in ['مساعدة','help']:
            return line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="المساعدة",contents=help_card(),quick_reply=get_qr()))
        if txt in ['نقاطي','إحصائياتي','احصائياتي']:
            return line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="إحصائياتك",contents=stats_card(uid,name,uid in registered_players),quick_reply=get_qr()))
        if txt in ['الصدارة','المتصدرين']:
            return line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="الصدارة",contents=leaderboard_card(),quick_reply=get_qr()))
        if txt in ['إيقاف','stop','ايقاف']:
            g = active_games.pop(gid,None)
            return line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"⏹️ تم إيقاف {g['type']}" if g else "لا توجد لعبة",quick_reply=get_qr()))
        if txt in ['انضم','تسجيل','join']:
            if uid in registered_players:
                return line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"أنت مسجل يا {name}",quick_reply=get_qr()))
            registered_players.add(uid)
            logger.info(f"تسجيل: {name}")
            return line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"✅ تم تسجيلك يا {name}",quick_reply=get_qr()))
        if txt in ['انسحب','خروج']:
            if uid not in registered_players:
                return line_bot_api.reply_message(event.reply_token, TextSendMessage(text="غير مسجل",quick_reply=get_qr()))
            registered_players.remove(uid)
            return line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"👋 تم انسحابك",quick_reply=get_qr()))
        
        # محتوى نصي
        if txt in ['سؤال','سوال']:
            return line_bot_api.reply_message(event.reply_token, TextSendMessage(text=next_content(QUESTIONS,'q_idx'),quick_reply=get_qr()))
        if txt in ['تحدي','challenge']:
            return line_bot_api.reply_message(event.reply_token, TextSendMessage(text=next_content(CHALLENGES,'c_idx'),quick_reply=get_qr()))
        if txt in ['اعتراف','confession']:
            return line_bot_api.reply_message(event.reply_token, TextSendMessage(text=next_content(CONFESSIONS,'cf_idx'),quick_reply=get_qr()))
        if txt in ['منشن','mention']:
            return line_bot_api.reply_message(event.reply_token, TextSendMessage(text=next_content(MENTIONS,'m_idx'),quick_reply=get_qr()))
        
        # ألعاب
        is_reg = uid in registered_players
        if GAMES_LOADED:
            gmap = {'أغنية':'song','لعبة':'game','سلسلة':'chain','أسرع':'fast','ضد':'opposite','تكوين':'build','ترتيب':'order','كلمة':'word','لون':'color','اختلاف':'diff','توافق':'compat'}
            if txt in gmap:
                if not is_reg:
                    return line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠️ سجل أولاً: انضم",quick_reply=get_qr()))
                r = start_game(gmap[txt],gid,active_games,line_bot_api,gemini.ask if gemini else None)
                if r: 
                    metrics.log_game(gmap[txt])
                    return line_bot_api.reply_message(event.reply_token,r)
            
            if gid in active_games and is_reg:
                r = check_game_answer(gid,txt,uid,name,active_games,line_bot_api,update_points)
                if r: return line_bot_api.reply_message(event.reply_token,r)
    
    except Exception as e:
        logger.error(f"معالجة خطأ: {e}", exc_info=True)

# Routes
@app.route("/", methods=['GET'])
def home():
    m = metrics.stats()
    return f"""<!DOCTYPE html>
<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>بوت الحوت</title><style>*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,sans-serif;background:#0F172A;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}
.container{{background:#1E293B;border-radius:24px;box-shadow:0 20px 60px rgba(6,182,212,0.3);padding:40px;max-width:600px;width:100%;border:2px solid rgba(6,182,212,0.2)}}
h1{{color:#06B6D4;font-size:2.5em;margin-bottom:8px;text-align:center;font-weight:700;text-shadow:0 0 30px rgba(6,182,212,0.5)}}
.logo{{font-size:4em;text-align:center;margin-bottom:10px;filter:drop-shadow(0 0 20px rgba(6,182,212,0.8))}}
.subtitle{{color:#94A3B8;font-size:1em;text-align:center;margin-bottom:30px}}
.status{{background:#0F172A;border-radius:16px;padding:24px;margin:20px 0;border:1px solid #334155}}
.item{{display:flex;justify-content:space-between;padding:16px 0;border-bottom:1px solid #334155}}
.item:last-child{{border:none}}.label{{color:#94A3B8;font-size:0.95em}}.value{{color:#F1F5F9;font-weight:700;font-size:1.1em}}
.badge{{padding:6px 14px;border-radius:20px;font-size:0.85em;font-weight:600}}
.success{{background:rgba(6,182,212,0.2);color:#06B6D4;box-shadow:0 0 15px rgba(6,182,212,0.3)}}
.footer{{text-align:center;margin-top:30px;color:#64748B;font-size:0.85em}}
</style></head><body><div class="container"><div class="logo">♓</div>
<h1>بوت الحوت</h1><div class="subtitle">نظام ألعاب تفاعلية محسّن</div>
<div class="status"><div class="item"><span class="label">حالة الخادم</span><span class="badge success">يعمل</span></div>
<div class="item"><span class="label">الذكاء الاصطناعي</span><span class="badge success">{'مفعّل' if USE_AI else 'معطّل'}</span></div>
<div class="item"><span class="label">اللاعبون</span><span class="value">{len(registered_players)}</span></div>
<div class="item"><span class="label">الألعاب النشطة</span><span class="value">{len(active_games)}</span></div>
<div class="item"><span class="label">إجمالي الرسائل</span><span class="value">{m['total_msgs']}</span></div>
<div class="item"><span class="label">وقت التشغيل</span><span class="value">{int(m['uptime']/3600)}ساعة</span></div>
</div><div class="footer">بوت الحوت v3.1 © 2025</div></div></body></html>"""

@app.route("/health", methods=['GET'])
def health():
    m = metrics.stats()
    return {"status":"healthy","version":"3.1.0","timestamp":datetime.now().isoformat(),
            "active_games":len(active_games),"registered_players":len(registered_players),
            "ai_enabled":USE_AI,"metrics":m}

@app.route("/callback", methods=['POST'])
def callback():
    if not handler or not line_bot_api: abort(500)
    sig, body = request.headers.get('X-Line-Signature',''), request.get_data(as_text=True)
    try:
        handler.handle(body, sig)
    except InvalidSignatureError:
        logger.error("توقيع غير صالح")
        abort(400)
    except Exception as e:
        logger.error(f"webhook خطأ: {e}")
    return 'OK'

@app.errorhandler(404)
def not_found(e): return {"error":"غير موجود"}, 404

@app.errorhandler(500)
def internal_error(e): 
    logger.error(f"خطأ: {e}")
    return {"error":"خطأ داخلي"}, 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"خطأ غير متوقع: {e}", exc_info=True)
    return 'OK', 200

# التشغيل
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print(f"\n{'='*60}\nبوت الحوت جاهز\nالمنفذ: {port}\nالذكاء الاصطناعي: {'مفعّل' if USE_AI else 'معطّل'}\n{'='*60}\n")
    try:
        logger.info(f"بدء الخادم على المنفذ {port}")
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("تم إيقاف الخادم")
        cleanup_inactive()
    except Exception as e:
        logger.critical(f"فشل التشغيل: {e}")
        sys.exit(1)
