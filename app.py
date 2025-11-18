"""بوت الحوت v3.3 - نسخة محسّنة مع ترتيب الأزرار الجديد"""
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage, QuickReply, QuickReplyButton, MessageAction
import os, sqlite3, logging, sys, threading, time, re, random
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from queue import Queue

# إعدادات اللوج
os.makedirs('logs', exist_ok=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler('logs/bot.log', encoding='utf-8')])
logger = logging.getLogger("whale-bot")

# توكنات
LINE_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_SECRET = os.getenv('LINE_CHANNEL_SECRET')

app = Flask(__name__)
line_bot_api = LineBotApi(LINE_TOKEN) if LINE_TOKEN else None
handler = WebhookHandler(LINE_SECRET) if LINE_SECRET else None
active_games, registered_players = {}, set()

# ألوان
C = {'bg':'#0A0E27','card':'#0F2440','text':'#E0F2FF','text2':'#7FB3D5','cyan':'#00D9FF','glow':'#5EEBFF','sep':'#2C5F8D','border':'#00D9FF40'}

# معدل الرسائل
class RateLimiter:
    def __init__(self,max_req=10,window=60):
        self.max_req,self.window,self.requests,self.lock=max_req,window,defaultdict(lambda: []),threading.Lock()
    def is_allowed(self,uid):
        with self.lock:
            now,reqs=time.time(),self.requests[uid]
            reqs=[r for r in reqs if r>now-self.window]
            if len(reqs)>=self.max_req: return False
            reqs.append(now); self.requests[uid]=reqs; return True

rate_limiter = RateLimiter()

# إحصاءات
class Metrics:
    def __init__(self): self.msgs,self.games,self.start=Counter(),Counter(),datetime.now()
    def log_msg(self,uid): self.msgs[uid]+=1
    def log_game(self,gtype): self.games[gtype]+=1
    def stats(self): return {'uptime':(datetime.now()-self.start).total_seconds(),'total_msgs':sum(self.msgs.values()),'total_games':sum(self.games.values())}

metrics = Metrics()

# قاعدة البيانات
DB='whale_bot.db'
class DBPool:
    def __init__(self,db,size=5):
        self.pool=Queue(maxsize=size)
        for _ in range(size):
            conn=sqlite3.connect(db,check_same_thread=False)
            conn.row_factory=sqlite3.Row
            self.pool.put(conn)
    def execute(self,query,params=()):
        conn=self.pool.get()
        try: c=conn.cursor(); c.execute(query,params); conn.commit(); return c
        finally: self.pool.put(conn)
    def fetchone(self,query,params=()): c=self.execute(query,params); r=c.fetchone(); return dict(r) if r else None
    def fetchall(self,query,params=()): c=self.execute(query,params); return [dict(r) for r in c.fetchall()]

def init_db():
    try:
        conn=sqlite3.connect(DB); c=conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS players (user_id TEXT PRIMARY KEY, display_name TEXT NOT NULL, total_points INTEGER DEFAULT 0, 
            games_played INTEGER DEFAULT 0, wins INTEGER DEFAULT 0, last_active TEXT DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_points ON players(total_points DESC)')
        conn.commit(); conn.close(); return True
    except Exception as e: logger.error(f"DB: {e}"); return False

init_db()
db=DBPool(DB)

# دوال مساعدة
def safe_text(t,max_len=500): return str(t or "").strip()[:max_len].replace('"','').replace("'",'')
def normalize_text(t):
    if not t: return ""
    t=t.strip().lower()
    t=re.sub('[أإآ]','ا',t); t=re.sub('[ؤ]','و',t); t=re.sub('[ئ]','ي',t); t=re.sub('[ءةى]','',t)
    t=re.sub('[\u064B-\u065F]','',t)
    return re.sub(r'\s+',' ',t).strip()

def get_profile(uid):
    if not line_bot_api: return f"مستخدم{uid[-4:]}"
    try: p=line_bot_api.get_profile(uid); return safe_text(p.display_name,50) if p.display_name else f"مستخدم{uid[-4:]}"
    except: return f"مستخدم{uid[-4:]}"

def update_user(uid,name):
    try: db.execute('INSERT OR REPLACE INTO players (user_id,display_name,last_active) VALUES (?,?,?)',(uid,safe_text(name,100),datetime.now().isoformat()))
    except Exception as e: logger.error(f"تحديث: {e}")

def update_points(uid,name,pts,won=False):
    try:
        r=db.fetchone('SELECT total_points,games_played,wins FROM players WHERE user_id=?',(uid,))
        if r: db.execute('UPDATE players SET total_points=?,games_played=?,wins=?,last_active=?,display_name=? WHERE user_id=?',
            (max(0,r['total_points']+pts), r['games_played']+1, r['wins']+(1 if won else 0), datetime.now().isoformat(), safe_text(name,100), uid))
        else: db.execute('INSERT INTO players VALUES (?,?,?,1,?,?)',(uid,safe_text(name,100),max(0,pts),1 if won else 0,datetime.now().isoformat()))
    except Exception as e: logger.error(f"نقاط: {e}")

def get_stats(uid): return db.fetchone('SELECT * FROM players WHERE user_id=?',(uid,))
def get_leaderboard(limit=10): return db.fetchall('SELECT display_name,total_points,games_played,wins FROM players WHERE total_points>0 ORDER BY total_points DESC,wins DESC LIMIT ?',(limit,))

def cleanup_inactive():
    try:
        cutoff=(datetime.now()-timedelta(days=45)).isoformat()
        c=db.execute('DELETE FROM players WHERE last_active<?',(cutoff,))
        if c.rowcount: logger.info(f"حذف {c.rowcount} مستخدم")
    except Exception as e: logger.error(f"تنظيف: {e}")

threading.Thread(target=lambda:[time.sleep(21600) or cleanup_inactive() for _ in iter(int,1)],daemon=True).start()

# تحميل المحتوى
def load_txt(name):
    try:
        with open(f'{name}.txt','r',encoding='utf-8') as f: return [l.strip() for l in f if l.strip()]
    except: logger.warning(f"{name}.txt غير موجود"); return []

QUESTIONS, CHALLENGES, CONFESSIONS, MENTIONS = load_txt('questions'), load_txt('challenges'), load_txt('confessions'), load_txt('more_questions')
q_idx=c_idx=cf_idx=m_idx=0

def next_content(items,idx_name):
    global q_idx,c_idx,cf_idx,m_idx
    idx=globals()[idx_name]
    if not items: return "محتوى افتراضي"
    r=items[idx % len(items)]
    globals()[idx_name]+=1
    return r

# أزرار ثابتة حسب ترتيبك
def get_qr():
    btns=["أسرع","لعبة","سلسلة","أغنية","ضد","ترتيب","تكوين","توافق","Ai","سؤال","منشن","اعتراف","تحدي"]
    return QuickReply(items=[QuickReplyButton(action=MessageAction(label=b,text=b)) for b in btns])

# دوال كروت (تم الحفاظ على الكروت الأصلية مع الترتيب الجديد)
def glass_box(contents,padding="20px"):
    return {"type":"box","layout":"vertical","contents":contents,"backgroundColor":C['card'],
            "cornerRadius":"16px","paddingAll":padding,"borderWidth":"1px","borderColor":C['border'],"margin":"md"}

# هنا تضع كل دوال الكروت welcome_card(), help_card(), more_card(), stats_card(), leaderboard_card()
# كما هي في الكود الأصلي مع حذف أي size غير مسموح، فقط لضغط الكود لنركز على البنية الأساسية

# تحميل الألعاب
try:
    from games import start_game, check_game_answer
    GAMES_LOADED=True
except: logger.warning("games.py غير موجود"); GAMES_LOADED=False

CMDS=['البداية','ابدأ','start','مساعدة','help','انضم','join','انسحب','إيقاف','stop'] + get_qr().items

# معالجات الرسائل
@handler.add(MessageEvent,message=TextMessage)
def handle_message(event):
    try:
        uid,txt=event.source.user_id,safe_text(event.message.text,500)
        if not txt or not any(c.lower() in txt.lower() for c in CMDS): return
        if not rate_limiter.is_allowed(uid): return

        name=get_profile(uid)
        update_user(uid,name)
        metrics.log_msg(uid)
        if uid not in registered_players and get_stats(uid): registered_players.add(uid)
        gid=getattr(event.source,'group_id',uid)

        is_reg=uid in registered_players

        # أوامر أساسية
        if txt in ['البداية','ابدأ','start']: return line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="بوت الحوت", contents=welcome_card(), quick_reply=get_qr()))
        if txt in ['مساعدة','help']: return line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="المساعدة", contents=help_card(), quick_reply=get_qr()))
        if txt in ['المزيد']: return line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="المزيد", contents=more_card(), quick_reply=get_qr()))
        if txt in ['نقاطي','إحصائياتي','احصائياتي']: return line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="إحصائياتك", contents=stats_card(uid,name,is_reg), quick_reply=get_qr()))
        if txt in ['الصدارة','المتصدرين']: return line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="الصدارة", contents=leaderboard_card(), quick_reply=get_qr()))
        if txt in ['إيقاف','stop','انسحب']: g=active_games.pop(gid,None); return line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"تم إيقاف {g['type']}" if g else "تم إيقاف اللعبة", quick_reply=get_qr()))
        if txt in ['انضم','تسجيل','join']:
            if uid in registered_players: return line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"أنت مسجل يا {name}", quick_reply=get_qr()))
            registered_players.add(uid); logger.info(f"تسجيل: {name}")
            return line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"تم تسجيلك يا {name}\nابدأ اللعب الآن", quick_reply=get_qr()))

        # الألعاب
        if GAMES_LOADED and is_reg:
            gmap={'أغنية':'song','لعبة':'game','سلسلة':'chain','أسرع':'fast','ضد':'opposite','تكوين':'build','ترتيب':'order','توافق':'compat','Ai':'ai'}
            if txt in gmap:
                r=start_game(gmap[txt],gid,active_games,line_bot_api,None)
                if r: metrics.log_game(gmap[txt]); return line_bot_api.reply_message(event.reply_token,r)
            if gid in active_games:
                r=check_game_answer(gid,txt,uid,name,active_games,line_bot_api,update_points)
                if r: return line_bot_api.reply_message(event.reply_token,r)
    except Exception as e: logger.error(f"معالجة: {e}",exc_info=True)

# باقي الـ routes و health و callback تبقى كما هي في الكود الأصلي
# وكذلك HTML و CSS للصفحة الرئيسية

if __name__=="__main__":
    port=int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0',port=port,debug=False,threaded=True,use_reloader=False)
