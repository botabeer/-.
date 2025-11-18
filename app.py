"""بوت الحوت v3.2 - نسخة مضغوطة ومحسّنة"""
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage, QuickReply, QuickReplyButton, MessageAction
import os, sqlite3, logging, sys, threading, time, re, random
from datetime import datetime, timedelta
from collections import defaultdict, deque, Counter
from queue import Queue

# Logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler('logs/bot.log', encoding='utf-8')])
logger = logging.getLogger("whale-bot")

# الإعدادات
LINE_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_SECRET = os.getenv('LINE_CHANNEL_SECRET')
GEMINI_KEYS = [k for k in [os.getenv(f'GEMINI_API_KEY_{i}', '') for i in range(1,4)] if k]

# CRITICAL: تعريف app لحل مشكلة Gunicorn
app = Flask(__name__)
line_bot_api = LineBotApi(LINE_TOKEN) if LINE_TOKEN else None
handler = WebhookHandler(LINE_SECRET) if LINE_SECRET else None
active_games, registered_players = {}, set()

# ألوان من الصورة فقط (أزرق سماوي ودرجات الداكن)
C = {'bg':'#0A0E27','card':'#0F2440','text':'#E0F2FF','text2':'#7FB3D5','cyan':'#00D9FF','glow':'#5EEBFF','sep':'#2C5F8D','border':'#00D9FF40'}
LOGO = "https://i.imgur.com/qcWILGi.jpeg"

# Rate Limiter
class RateLimiter:
    def __init__(self, max_req=10, window=60):
        self.max_req, self.window, self.requests, self.lock = max_req, window, defaultdict(deque), threading.Lock()
    def is_allowed(self, uid):
        with self.lock:
            now, reqs = time.time(), self.requests[uid]
            while reqs and reqs[0] < now - self.window: reqs.popleft()
            if len(reqs) >= self.max_req: return False
            reqs.append(now)
            return True

rate_limiter = RateLimiter()

# Metrics
class Metrics:
    def __init__(self): self.msgs, self.games, self.start = Counter(), Counter(), datetime.now()
    def log_msg(self, uid): self.msgs[uid] += 1
    def log_game(self, gtype): self.games[gtype] += 1
    def stats(self): return {'uptime':(datetime.now()-self.start).total_seconds(),'total_msgs':sum(self.msgs.values()),'total_games':sum(self.games.values())}

metrics = Metrics()

# DB Pool
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
        finally: self.pool.put(conn)
    def fetchone(self, query, params=()): c = self.execute(query, params); result = c.fetchone(); return dict(result) if result else None
    def fetchall(self, query, params=()): c = self.execute(query, params); return [dict(r) for r in c.fetchall()]

def init_db():
    try:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS players (user_id TEXT PRIMARY KEY, display_name TEXT NOT NULL, total_points INTEGER DEFAULT 0, 
            games_played INTEGER DEFAULT 0, wins INTEGER DEFAULT 0, last_active TEXT DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_points ON players(total_points DESC)')
        conn.commit(); conn.close()
        logger.info("DB جاهز")
        return True
    except Exception as e: logger.error(f"DB: {e}"); return False

init_db()
db = DBPool(DB)

def safe_text(t, max_len=500): return str(t or "").strip()[:max_len].replace('"','').replace("'",'')
def normalize_text(t):
    if not t: return ""
    t = t.strip().lower()
    t = re.sub('[أإآ]','ا',t); t = re.sub('[ؤ]','و',t); t = re.sub('[ئ]','ي',t); t = re.sub('[ءةى]','',t); t = re.sub('[\u064B-\u065F]','',t)
    return re.sub(r'\s+',' ',t).strip()

def get_profile(uid):
    if not line_bot_api: return f"مستخدم{uid[-4:]}"
    try: p = line_bot_api.get_profile(uid); return safe_text(p.display_name,50) if p.display_name else f"مستخدم{uid[-4:]}"
    except: return f"مستخدم{uid[-4:]}"

def update_user(uid, name):
    try: db.execute('INSERT OR REPLACE INTO players (user_id,display_name,last_active) VALUES (?,?,?)', (uid, safe_text(name,100), datetime.now().isoformat()))
    except Exception as e: logger.error(f"تحديث: {e}")

def update_points(uid, name, pts, won=False):
    try:
        r = db.fetchone('SELECT total_points,games_played,wins FROM players WHERE user_id=?', (uid,))
        if r: db.execute('UPDATE players SET total_points=?,games_played=?,wins=?,last_active=?,display_name=? WHERE user_id=?',
            (max(0,r['total_points']+pts), r['games_played']+1, r['wins']+(1 if won else 0), datetime.now().isoformat(), safe_text(name,100), uid))
        else: db.execute('INSERT INTO players VALUES (?,?,?,1,?,?)', (uid, safe_text(name,100), max(0,pts), 1 if won else 0, datetime.now().isoformat()))
    except Exception as e: logger.error(f"نقاط: {e}")

def get_stats(uid): return db.fetchone('SELECT * FROM players WHERE user_id=?', (uid,))
def get_leaderboard(limit=10): return db.fetchall('SELECT display_name,total_points,games_played,wins FROM players WHERE total_points>0 ORDER BY total_points DESC,wins DESC LIMIT ?', (limit,))

def cleanup_inactive():
    try:
        cutoff = (datetime.now()-timedelta(days=45)).isoformat()
        c = db.execute('DELETE FROM players WHERE last_active<?', (cutoff,))
        if c.rowcount: logger.info(f"حذف {c.rowcount} مستخدم")
    except Exception as e: logger.error(f"تنظيف: {e}")

threading.Thread(target=lambda: [time.sleep(21600) or cleanup_inactive() for _ in iter(int,1)], daemon=True).start()

# المحتوى
def load_txt(name):
    try:
        with open(f'{name}.txt','r',encoding='utf-8') as f: return [l.strip() for l in f if l.strip()]
    except: logger.warning(f"{name}.txt غير موجود"); return []

QUESTIONS, CHALLENGES, CONFESSIONS, MENTIONS = load_txt('questions'), load_txt('challenges'), load_txt('confessions'), load_txt('more_questions')
q_idx = c_idx = cf_idx = m_idx = 0

def next_content(items, idx_name):
    global q_idx, c_idx, cf_idx, m_idx
    idx = globals()[idx_name]
    if not items: return "محتوى افتراضي"
    r = items[idx % len(items)]
    globals()[idx_name] += 1
    return r

# Quick Reply - ألعاب + المزيد
def get_qr():
    btns = ["أغنية","لعبة","سلسلة","أسرع","ضد","تكوين","ترتيب","كلمة","لون","المزيد"]
    return QuickReply(items=[QuickReplyButton(action=MessageAction(label=b,text=b)) for b in btns])

# Flex Components
def glass_box(contents, padding="20px"):
    return {"type":"box","layout":"vertical","contents":contents,"backgroundColor":C['card'],"cornerRadius":"16px",
        "paddingAll":padding,"borderWidth":"1px","borderColor":C['border'],"margin":"md"}

def progress_bar(current, total):
    return {"type":"box","layout":"horizontal","contents":[
        {"type":"box","layout":"vertical","contents":[],"backgroundColor":C['cyan'],"height":"6px","flex":current,"cornerRadius":"3px"},
        {"type":"box","layout":"vertical","contents":[],"backgroundColor":C['card'],"height":"6px","flex":max(1,total-current),"cornerRadius":"3px"}
    ],"spacing":"xs","margin":"lg"}

def game_header(title, subtitle):
    return [{"type":"box","layout":"vertical","contents":[{"type":"image","url":LOGO,"size":"60px","aspectMode":"cover"}],
        "width":"60px","height":"60px","cornerRadius":"30px","borderWidth":"2px","borderColor":C['cyan'],"margin":"none"},
        {"type":"text","text":title,"size":"xl","weight":"bold","color":C['cyan'],"align":"center","margin":"md"},
        {"type":"text","text":subtitle,"size":"sm","color":C['text2'],"align":"center","margin":"xs"},
        {"type":"separator","margin":"lg","color":C['sep']}]

def create_button(label, text): return {"type":"button","action":{"type":"message","label":label,"text":text},"style":"secondary","height":"md"}

# Flex Cards
def welcome_card():
    return {"type":"bubble","size":"kilo","body":{"type":"box","layout":"vertical","contents":[
        {"type":"box","layout":"vertical","contents":[{"type":"image","url":LOGO,"size":"100px","aspectMode":"cover"}],
            "width":"100px","height":"100px","cornerRadius":"50px","borderWidth":"2px","borderColor":C['cyan'],"margin":"none"},
        {"type":"text","text":"بوت الحوت","size":"xxl","weight":"bold","color":C['cyan'],"align":"center","margin":"md"},
        {"type":"text","text":"نظام ألعاب تفاعلية","size":"sm","color":C['text2'],"align":"center","margin":"sm"},
        {"type":"separator","margin":"lg","color":C['sep']},
        glass_box([{"type":"text","text":"الألعاب المتوفرة","size":"md","weight":"bold","color":C['text']},
            {"type":"text","text":"أغنية | لعبة | سلسلة | أسرع | ضد\nتكوين | ترتيب | كلمة | لون","size":"xs","color":C['text2'],"wrap":True,"margin":"sm"}]),
        {"type":"text","text":"بوت الحوت © 2025","size":"xxs","color":C['text2'],"align":"center","margin":"lg"}
    ],"backgroundColor":C['bg'],"paddingAll":"24px"},"footer":{"type":"box","layout":"vertical","contents":[
        {"type":"button","action":{"type":"message","label":"ابدأ اللعب","text":"مساعدة"},"style":"primary","color":C['cyan'],"height":"md"},
        {"type":"box","layout":"horizontal","contents":[
            {"type":"button","action":{"type":"message","label":"المزيد","text":"المزيد"},"style":"secondary","height":"sm"},
            {"type":"button","action":{"type":"message","label":"نقاطي","text":"نقاطي"},"style":"secondary","height":"sm"}
        ],"spacing":"sm","margin":"sm"}
    ],"paddingAll":"16px","backgroundColor":C['bg']}}

def help_card():
    return {"type":"bubble","size":"kilo","body":{"type":"box","layout":"vertical","contents":[
        {"type":"box","layout":"vertical","contents":[{"type":"image","url":LOGO,"size":"80px","aspectMode":"cover"}],
            "width":"80px","height":"80px","cornerRadius":"40px","borderWidth":"2px","borderColor":C['cyan'],"margin":"none"},
        {"type":"text","text":"المساعدة","size":"xl","weight":"bold","color":C['cyan'],"align":"center","margin":"md"},
        {"type":"separator","margin":"lg","color":C['sep']},
        glass_box([{"type":"text","text":"أوامر اللعب","size":"md","weight":"bold","color":C['text']},
            {"type":"text","text":"لمح: تلميح (نصف النقاط)\nجاوب: عرض الحل\nإيقاف: إنهاء اللعبة","size":"xs","color":C['text2'],"wrap":True,"margin":"sm"}]),
        glass_box([{"type":"text","text":"إدارة الحساب","size":"md","weight":"bold","color":C['text']},
            {"type":"text","text":"انضم: التسجيل\nانسحب: حذف الحساب\nنقاطي: الإحصائيات","size":"xs","color":C['text2'],"wrap":True,"margin":"sm"}]),
        glass_box([{"type":"text","text":"نظام اللعب","size":"md","weight":"bold","color":C['text']},
            {"type":"text","text":"5 جولات | +2 نقطة | +1 مع تلميح","size":"xs","color":C['text2'],"wrap":True,"margin":"sm"}]),
        {"type":"text","text":"بوت الحوت © 2025","size":"xxs","color":C['text2'],"align":"center","margin":"lg"}
    ],"backgroundColor":C['bg'],"paddingAll":"24px"},"footer":{"type":"box","layout":"vertical","contents":[
        {"type":"box","layout":"horizontal","contents":[
            {"type":"button","action":{"type":"message","label":"انضم","text":"انضم"},"style":"primary","color":C['cyan'],"height":"md","flex":1},
            {"type":"button","action":{"type":"message","label":"إيقاف","text":"إيقاف"},"style":"secondary","height":"md","flex":1}
        ],"spacing":"sm"},
        {"type":"button","action":{"type":"message","label":"انسحب","text":"انسحب"},"style":"secondary","margin":"sm","height":"md"}
    ],"paddingAll":"16px","backgroundColor":C['bg']}}

def more_card():
    return {"type":"bubble","size":"kilo","body":{"type":"box","layout":"vertical","contents":[
        {"type":"box","layout":"vertical","contents":[{"type":"image","url":LOGO,"size":"80px","aspectMode":"cover"}],
            "width":"80px","height":"80px","cornerRadius":"40px","borderWidth":"2px","borderColor":C['cyan'],"margin":"none"},
        {"type":"text","text":"المزيد","size":"xl","weight":"bold","color":C['cyan'],"align":"center","margin":"md"},
        {"type":"separator","margin":"lg","color":C['sep']},
        glass_box([{"type":"text","text":"محتوى ترفيهي","size":"md","weight":"bold","color":C['text']},
            {"type":"text","text":"سؤال | تحدي | اعتراف | منشن","size":"xs","color":C['text2'],"wrap":True,"margin":"sm"}]),
        {"type":"text","text":"بوت الحوت © 2025","size":"xxs","color":C['text2'],"align":"center","margin":"lg"}
    ],"backgroundColor":C['bg'],"paddingAll":"24px"},"footer":{"type":"box","layout":"vertical","contents":[
        {"type":"box","layout":"horizontal","contents":[
            {"type":"button","action":{"type":"message","label":"سؤال","text":"سؤال"},"style":"secondary","height":"md"},
            {"type":"button","action":{"type":"message","label":"تحدي","text":"تحدي"},"style":"secondary","height":"md"}
        ],"spacing":"sm"},
        {"type":"box","layout":"horizontal","contents":[
            {"type":"button","action":{"type":"message","label":"اعتراف","text":"اعتراف"},"style":"secondary","height":"md"},
            {"type":"button","action":{"type":"message","label":"منشن","text":"منشن"},"style":"secondary","height":"md"}
        ],"spacing":"sm","margin":"sm"}
    ],"paddingAll":"16px","backgroundColor":C['bg']}}

def stats_card(uid, name, is_reg):
    stats = get_stats(uid)
    if not stats:
        return {"type":"bubble","size":"kilo","body":{"type":"box","layout":"vertical","contents":[
            {"type":"box","layout":"vertical","contents":[{"type":"image","url":LOGO,"size":"80px","aspectMode":"cover"}],
                "width":"80px","height":"80px","cornerRadius":"40px","borderWidth":"2px","borderColor":C['cyan'],"margin":"none"},
            {"type":"text","text":"إحصائياتك","size":"xl","weight":"bold","color":C['cyan'],"align":"center","margin":"md"},
            {"type":"separator","margin":"lg","color":C['sep']},
            glass_box([{"type":"text","text":name,"size":"lg","color":C['text'],"align":"center"},
                {"type":"text","text":"غير مسجل" if not is_reg else "لم تبدأ","size":"md","color":C['text2'],"align":"center","margin":"md"}]),
            {"type":"text","text":"بوت الحوت © 2025","size":"xxs","color":C['text2'],"align":"center","margin":"lg"}
        ],"backgroundColor":C['bg'],"paddingAll":"24px"},"footer":{"type":"box","layout":"vertical","contents":[
            {"type":"button","action":{"type":"message","label":"انضم الآن","text":"انضم"},"style":"primary","color":C['cyan'],"height":"md"}
        ],"paddingAll":"16px","backgroundColor":C['bg']} if not is_reg else None}
    
    wr = (stats['wins']/stats['games_played']*100) if stats['games_played']>0 else 0
    return {"type":"bubble","size":"kilo","body":{"type":"box","layout":"vertical","contents":[
        {"type":"box","layout":"vertical","contents":[{"type":"image","url":LOGO,"size":"80px","aspectMode":"cover"}],
            "width":"80px","height":"80px","cornerRadius":"40px","borderWidth":"2px","borderColor":C['cyan'],"margin":"none"},
        {"type":"text","text":"إحصائياتك","size":"xl","weight":"bold","color":C['cyan'],"align":"center","margin":"md"},
        {"type":"separator","margin":"lg","color":C['sep']},
        glass_box([{"type":"text","text":name,"size":"lg","color":C['text'],"align":"center"}],"md"),
        glass_box([
            {"type":"box","layout":"horizontal","contents":[
                {"type":"text","text":"النقاط","size":"sm","color":C['text2'],"flex":1},
                {"type":"text","text":str(stats['total_points']),"size":"xxl","weight":"bold","color":C['glow'],"flex":1,"align":"end"}
            ]},
            {"type":"separator","margin":"md","color":C['sep']},
            {"type":"box","layout":"horizontal","contents":[
                {"type":"text","text":"الألعاب","size":"sm","color":C['text2'],"flex":1},
                {"type":"text","text":str(stats['games_played']),"size":"lg","color":C['text'],"flex":1,"align":"end"}
            ],"margin":"md"},
            {"type":"box","layout":"horizontal","contents":[
                {"type":"text","text":"الفوز","size":"sm","color":C['text2'],"flex":1},
                {"type":"text","text":str(stats['wins']),"size":"lg","color":C['text'],"flex":1,"align":"end"}
            ],"margin":"sm"},
            {"type":"box","layout":"horizontal","contents":[
                {"type":"text","text":"المعدل","size":"sm","color":C['text2'],"flex":1},
                {"type":"text","text":f"{wr:.0f}%","size":"lg","color":C['text'],"flex":1,"align":"end"}
            ],"margin":"sm"}
        ]),
        {"type":"text","text":"بوت الحوت © 2025","size":"xxs","color":C['text2'],"align":"center","margin":"lg"}
    ],"backgroundColor":C['bg'],"paddingAll":"24px"}}

def leaderboard_card():
    leaders = get_leaderboard()
    if not leaders:
        return {"type":"bubble","size":"kilo","body":{"type":"box","layout":"vertical","contents":[
            {"type":"box","layout":"vertical","contents":[{"type":"image","url":LOGO,"size":"80px","aspectMode":"cover"}],
                "width":"80px","height":"80px","cornerRadius":"40px","borderWidth":"2px","borderColor":C['cyan'],"margin":"none"},
            {"type":"text","text":"لوحة الصدارة","size":"xl","weight":"bold","color":C['cyan'],"align":"center","margin":"md"},
            {"type":"separator","margin":"lg","color":C['sep']},
            {"type":"text","text":"لا توجد بيانات","size":"md","color":C['text2'],"align":"center","margin":"lg"},
            {"type":"text","text":"بوت الحوت © 2025","size":"xxs","color":C['text2'],"align":"center","margin":"lg"}
        ],"backgroundColor":C['bg'],"paddingAll":"24px"}}
    
    items = []
    for i,l in enumerate(leaders,1):
        rank = ["🥇","🥈","🥉"][i-1] if i<=3 else f"#{i}"
        items.append({"type":"box","layout":"horizontal","contents":[
            {"type":"text","text":rank,"size":"md" if i<=3 else "sm","weight":"bold","flex":0,"color":C['cyan'] if i<=3 else C['text']},
            {"type":"text","text":l['display_name'],"size":"sm","flex":3,"margin":"md","wrap":True,"color":C['cyan'] if i==1 else C['text']},
            {"type":"text","text":str(l['total_points']),"size":"lg" if i==1 else "md","weight":"bold","flex":1,"align":"end","color":C['glow'] if i==1 else C['text2']}
        ],"backgroundColor":C['card'],"cornerRadius":"12px","paddingAll":"14px","margin":"sm" if i>1 else "md",
            "borderWidth":"2px" if i==1 else "1px","borderColor":C['cyan'] if i==1 else C['border']})
    
    return {"type":"bubble","size":"kilo","body":{"type":"box","layout":"vertical","contents":[
        {"type":"box","layout":"vertical","contents":[{"type":"image","url":LOGO,"size":"80px","aspectMode":"cover"}],
            "width":"80px","height":"80px","cornerRadius":"40px","borderWidth":"2px","borderColor":C['cyan'],"margin":"none"},
        {"type":"text","text":"لوحة الصدارة","size":"xl","weight":"bold","color":C['cyan'],"align":"center","margin":"md"},
        {"type":"separator","margin":"lg","color":C['sep']},
        {"type":"box","layout":"vertical","contents":items,"margin":"md"},
        {"type":"text","text":"بوت الحوت © 2025","size":"xxs","color":C['text2'],"align":"center","margin":"lg"}
    ],"backgroundColor":C['bg'],"paddingAll":"24px"}}

# استيراد الألعاب
try:
    from games import start_game, check_game_answer
    GAMES_LOADED = True
except: logger.warning("games.py غير موجود"); GAMES_LOADED = False

# معالج الرسائل
CMDS = ['البداية','ابدأ','start','مساعدة','help','انضم','join','انسحب','خروج','نقاطي','إحصائياتي','الصدارة','المتصدرين',
    'إيقاف','stop','أغنية','لعبة','سلسلة','أسرع','ضد','تكوين','ترتيب','كلمة','لون','سؤال','سوال','تحدي','اعتراف','منشن',
    'لمح','تلميح','جاوب','الحل','الجواب','المزيد']

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        uid, txt = event.source.user_id, safe_text(event.message.text, 500)
        if not txt or not any(c.lower() in txt.lower() for c in CMDS): return
        if not rate_limiter.is_allowed(uid): return
        
        name = get_profile(uid)
        update_user(uid, name)
        metrics.log_msg(uid)
        if uid not in registered_players and get_stats(uid): registered_players.add(uid)
        gid = getattr(event.source, 'group_id', uid)
        
        # أوامر
        if txt in ['البداية','ابدأ','start']: return line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="بوت الحوت", contents=welcome_card(), quick_reply=get_qr()))
        if txt in ['مساعدة','help']: return line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="المساعدة", contents=help_card(), quick_reply=get_qr()))
        if txt in ['المزيد']: return line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="المزيد", contents=more_card(), quick_reply=get_qr()))
        if txt in ['نقاطي','إحصائياتي','احصائياتي']: return line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="إحصائياتك", contents=stats_card(uid, name, uid in registered_players), quick_reply=get_qr()))
        if txt in ['الصدارة','المتصدرين']: return line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="الصدارة", contents=leaderboard_card(), quick_reply=get_qr()))
        if txt in ['إيقاف','stop','ايقاف']: g = active_games.pop(gid, None); return line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"تم إيقاف {g['type']}" if g else "لا توجد لعبة", quick_reply=get_qr()))
        if txt in ['انضم','تسجيل','join']:
            if uid in registered_players: return line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"أنت مسجل يا {name}", quick_reply=get_qr()))
            registered_players.add(uid); logger.info(f"تسجيل: {name}")
            return line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"تم تسجيلك يا {name}\nابدأ اللعب الآن", quick_reply=get_qr()))
        if txt in ['انسحب','خروج']:
            if uid not in registered_players: return line_bot_api.reply_message(event.reply_token, TextSendMessage(text="غير مسجل", quick_reply=get_qr()))
            registered_players.remove(uid); return line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"تم انسحابك", quick_reply=get_qr()))
        if txt in ['سؤال','سوال']: return line_bot_api.reply_message(event.reply_token, TextSendMessage(text=next_content(QUESTIONS,'q_idx'), quick_reply=get_qr()))
        if txt in ['تحدي','challenge']: return line_bot_api.reply_message(event.reply_token, TextSendMessage(text=next_content(CHALLENGES,'c_idx'), quick_reply=get_qr()))
        if txt in ['اعتراف','confession']: return line_bot_api.reply_message(event.reply_token, TextSendMessage(text=next_content(CONFESSIONS,'cf_idx'), quick_reply=get_qr()))
        if txt in ['منشن','mention']: return line_bot_api.reply_message(event.reply_token, TextSendMessage(text=next_content(MENTIONS,'m_idx'), quick_reply=get_qr()))
        
        # ألعاب
        is_reg = uid in registered_players
        if GAMES_LOADED:
            gmap = {'أغنية':'song','لعبة':'game','سلسلة':'chain','أسرع':'fast','ضد':'opposite','تكوين':'build','ترتيب':'order','كلمة':'word','لون':'color'}
            if txt in gmap:
                if not is_reg: return line_bot_api.reply_message(event.reply_token, TextSendMessage(text="سجل أولاً: انضم", quick_reply=get_qr()))
                r = start_game(gmap[txt], gid, active_games, line_bot_api, None)
                if r: metrics.log_game(gmap[txt]); return line_bot_api.reply_message(event.reply_token, r)
            if gid in active_games and is_reg:
                r = check_game_answer(gid, txt, uid, name, active_games, line_bot_api, update_points)
                if r: return line_bot_api.reply_message(event.reply_token, r)
    except Exception as e: logger.error(f"معالجة: {e}", exc_info=True)

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
    <title>بوت الحوت v3.2</title>
    <style>
        *{{margin:0;padding:0;box-sizing:border-box}}
        body{{font-family:'Segoe UI',sans-serif;background:#0A0E27;min-height:100vh;display:flex;align-items:center;justify-content:center;overflow:hidden}}
        .background{{position:fixed;width:100%;height:100%;top:0;left:0;background:radial-gradient(ellipse at center,#0F1629 0%,#0A0E27 100%)}}
        .particles{{position:fixed;width:100%;height:100%;top:0;left:0}}
        .particle{{position:absolute;width:3px;height:3px;background:#00D9FF;border-radius:50%;animation:float 15s infinite ease-in-out;box-shadow:0 0 10px #00D9FF}}
        @keyframes float{{0%,100%{{transform:translateY(0);opacity:0}}10%{{opacity:0.8}}50%{{transform:translateY(-50vh);opacity:1}}90%{{opacity:0.8}}}}
        .container{{position:relative;z-index:10;width:90%;max-width:900px;padding:40px}}
        .main-circle{{position:relative;width:300px;height:300px;margin:0 auto 50px;display:flex;align-items:center;justify-content:center;animation:rotate360 30s linear infinite}}
        @keyframes rotate360{{from{{transform:rotate(0deg)}}to{{transform:rotate(360deg)}}}}
        .outer-ring{{position:absolute;width:100%;height:100%;border:3px solid #00D9FF;border-radius:50%;box-shadow:0 0 30px rgba(0,217,255,0.6),inset 0 0 30px rgba(0,217,255,0.2);animation:pulse-ring 3s ease-in-out infinite}}
        @keyframes pulse-ring{{0%,100%{{transform:scale(1);opacity:0.8}}50%{{transform:scale(1.05);opacity:1}}}}
        .logo-container{{position:relative;width:180px;height:180px;background:linear-gradient(135deg,rgba(15,40,71,0.9) 0%,rgba(10,22,40,0.9) 100%);border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 0 60px rgba(0,217,255,0.5),inset 0 0 50px rgba(0,217,255,0.1);border:2px solid rgba(0,217,255,0.3);backdrop-filter:blur(20px);animation:logo-float 6s ease-in-out infinite}}
        @keyframes logo-float{{0%,100%{{transform:translateY(0px)}}50%{{transform:translateY(-20px)}}}}
        .pisces-logo{{font-size:100px;filter:drop-shadow(0 0 40px rgba(0,217,255,1));animation:logo-glow 3s ease-in-out infinite}}
        @keyframes logo-glow{{0%,100%{{filter:drop-shadow(0 0 40px rgba(0,217,255,1))}}50%{{filter:drop-shadow(0 0 50px rgba(94,235,255,1))}}}}
        .glass-card{{background:linear-gradient(135deg,rgba(15,40,71,0.7) 0%,rgba(10,22,40,0.5) 100%);border-radius:30px;padding:40px;backdrop-filter:blur(30px);border:2px solid rgba(0,217,255,0.3);box-shadow:0 0 60px rgba(0,217,255,0.4);position:relative;overflow:hidden}}
        .title{{font-size:48px;font-weight:900;text-align:center;color:#00D9FF;margin-bottom:15px;text-shadow:0 0 30px rgba(0,217,255,0.8);animation:title-glow 3s ease-in-out infinite}}
        @keyframes title-glow{{0%,100%{{text-shadow:0 0 30px rgba(0,217,255,0.8)}}50%{{text-shadow:0 0 40px rgba(94,235,255,1)}}}}
        .subtitle{{font-size:18px;text-align:center;color:#7FB3D5;margin-bottom:40px;letter-spacing:2px}}
        .status-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin-top:40px}}
        .status-item{{background:linear-gradient(135deg,rgba(15,40,71,0.6) 0%,rgba(10,22,40,0.4) 100%);border-radius:20px;padding:25px;border:1px solid rgba(0,217,255,0.2);backdrop-filter:blur(10px);box-shadow:0 0 30px rgba(0,217,255,0.2);transition:all 0.3s ease}}
        .status-item:hover{{transform:translateY(-5px);border-color:rgba(0,217,255,0.5);box-shadow:0 0 40px rgba(0,217,255,0.4)}}
        .status-label{{font-size:14px;color:#7FB3D5;margin-bottom:10px}}
        .status-value{{font-size:32px;font-weight:900;color:#5EEBFF;text-shadow:0 0 20px rgba(94,235,255,0.6)}}
        .badge{{padding:6px 14px;border-radius:20px;font-size:14px;font-weight:600;display:inline-block;margin-top:10px;background:rgba(0,217,255,0.2);color:#00D9FF;box-shadow:0 0 20px rgba(0,217,255,0.4);border:1px solid rgba(0,217,255,0.3)}}
        .footer{{text-align:center;margin-top:40px;color:#2C5F8D;font-size:14px}}
        .footer a{{color:#00D9FF;text-decoration:none}}
        @media (max-width:768px){{.main-circle{{width:250px;height:250px}}.logo-container{{width:150px;height:150px}}.pisces-logo{{font-size:80px}}.title{{font-size:36px}}.glass-card{{padding:30px 20px}}}}
    </style>
</head>
<body>
    <div class="background"></div>
    <div class="particles" id="particles"></div>
    <div class="container">
        <div class="main-circle">
            <div class="outer-ring"></div>
            <div class="logo-container">
                <div class="pisces-logo">♓</div>
            </div>
        </div>
        <div class="glass-card">
            <h1 class="title">بوت الحوت</h1>
            <p class="subtitle">نظام ألعاب تفاعلية v3.2</p>
            <div class="status-grid">
                <div class="status-item">
                    <div class="status-label">حالة الخادم</div>
                    <div class="status-value">نشط</div>
                    <span class="badge">يعمل</span>
                </div>
                <div class="status-item">
                    <div class="status-label">اللاعبون</div>
                    <div class="status-value">{len(registered_players)}</div>
                </div>
                <div class="status-item">
                    <div class="status-label">الألعاب النشطة</div>
                    <div class="status-value">{len(active_games)}</div>
                </div>
                <div class="status-item">
                    <div class="status-label">الرسائل</div>
                    <div class="status-value">{m['total_msgs']}</div>
                </div>
                <div class="status-item">
                    <div class="status-label">الألعاب</div>
                    <div class="status-value">{m['total_games']}</div>
                </div>
                <div class="status-item">
                    <div class="status-label">وقت التشغيل</div>
                    <div class="status-value">{uptime_hours}س {uptime_mins}د</div>
                </div>
            </div>
            <div class="footer">
                بوت الحوت v3.2 © 2025<br>
                <a href="/health">Health Check</a>
            </div>
        </div>
    </div>
    <script>
        const pc=document.getElementById('particles');
        for(let i=0;i<40;i++){{
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
    return {"status":"healthy","version":"3.2.0","timestamp":datetime.now().isoformat(),"active_games":len(active_games),
        "registered_players":len(registered_players),"games_loaded":GAMES_LOADED,"metrics":{"uptime_seconds":m['uptime'],
        "total_messages":m['total_msgs'],"total_games":m['total_games']}}

@app.route("/callback", methods=['POST'])
def callback():
    if not handler or not line_bot_api: abort(500)
    sig = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, sig)
    except InvalidSignatureError:
        logger.error("توقيع غير صالح")
        abort(400)
    except Exception as e:
        logger.error(f"webhook: {e}")
    return 'OK'

@app.errorhandler(404)
def not_found(e): return {"error":"الصفحة غير موجودة","status":404}, 404

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"خطأ: {e}")
    return {"error":"خطأ داخلي","status":500}, 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"خطأ غير متوقع: {e}", exc_info=True)
    return 'OK', 200

# التشغيل
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print(f"\n{'='*60}")
    print(f"♓ بوت الحوت v3.2 ♓")
    print(f"{'='*60}")
    print(f"المنفذ: {port}")
    print(f"الألعاب: {'متوفرة' if GAMES_LOADED else 'غير متوفرة'}")
    print(f"{'='*60}\n")
    
    try:
        logger.info(f"بدء الخادم على المنفذ {port}")
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("تم إيقاف الخادم")
        cleanup_inactive()
    except Exception as e:
        logger.critical(f"فشل التشغيل: {e}")
        sys.exit(1)
