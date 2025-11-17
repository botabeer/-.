from flask import Flask, request, abort, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction, FlexSendMessage
import os, sqlite3, threading, time, random, re, logging, sys, traceback
from datetime import datetime, timedelta
from collections import defaultdict
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

# iOS Style Colors
IOS = {"primary":"#007AFF","secondary":"#5AC8FA","bg":"#F2F2F7","card":"#FFFFFF","elevated":"#F9F9F9","border":"#E5E5EA","text":"#000000","text_dim":"#8E8E93","text_muted":"#C7C7CC","accent":"#34C759"}

# شعار 3D مع توهج
LOGO_3D = "https://i.ibb.co/placeholder-logo.png"  # ضع رابط الشعار هنا

DB_NAME, MAX_MSG, TIMEOUT, MAX_ERR, MAX_CACHE = 'game_scores.db', 30, 15, 50, 1000

USE_AI, ask_gemini = False, None
try:
    import google.generativeai as genai
    keys = [os.getenv(f'GEMINI_API_KEY_{i}','').strip() for i in range(1,4)]
    keys = [k for k in keys if k]
    if keys:
        genai.configure(api_key=keys[0])
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        USE_AI = True
        def ask_gemini(prompt, max_retries=2):
            for attempt in range(max_retries):
                try:
                    if attempt > 0 and attempt < len(keys): genai.configure(api_key=keys[attempt])
                    return model.generate_content(prompt).text.strip()
                except Exception as e:
                    if attempt == max_retries - 1: return None
            return None
        logger.info(f"✅ Gemini: {len(keys)} key(s)")
except: logger.warning("⚠️ Gemini unavailable")

games = {}
game_names = ['SongGame','HumanAnimalPlantGame','ChainWordsGame','FastTypingGame','OppositeGame','LettersWordsGame','DifferencesGame','CompatibilityGame']
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'games'))
for name in game_names:
    try:
        module = __import__(name.lower().replace('game','_game'), fromlist=[name])
        games[name] = getattr(module, name)
        logger.info(f"✅ {name}")
    except Exception as e:
        games[name] = None
        logger.warning(f"⚠️ {name}")

app = Flask(__name__)
TOKEN, SECRET = os.getenv('LINE_CHANNEL_ACCESS_TOKEN','').strip(), os.getenv('LINE_CHANNEL_SECRET','').strip()
if not TOKEN or not SECRET:
    logger.critical("❌ LINE credentials missing!")
    sys.exit(1)
line_bot_api, handler = LineBotApi(TOKEN), WebhookHandler(SECRET)

active_games, registered_players, user_msg_count, user_names, error_log = {}, set(), defaultdict(lambda:{'count':0,'reset_time':datetime.now()}), {}, []
games_lock, players_lock, names_lock, error_lock = threading.RLock(), threading.RLock(), threading.RLock(), threading.RLock()

@contextmanager
def get_db():
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME, check_same_thread=False, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA journal_mode=WAL')
        yield conn
    except Exception as e:
        logger.error(f"DB error: {e}")
        if conn: conn.rollback()
        raise
    finally:
        if conn: conn.close()

def init_db():
    try:
        with get_db() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, display_name TEXT, total_points INT DEFAULT 0, games_played INT DEFAULT 0, wins INT DEFAULT 0, last_played TEXT, registered_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
            conn.execute('''CREATE TABLE IF NOT EXISTS game_history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, game_type TEXT, points INT DEFAULT 0, won INT DEFAULT 0, played_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_points ON users(total_points DESC)')
            conn.commit()
            logger.info("✅ DB ready")
    except Exception as e:
        logger.error(f"❌ DB init failed: {e}")
        raise
init_db()

def update_points(uid, name, pts, won=False, gtype=""):
    try:
        with get_db() as conn:
            u = conn.execute('SELECT * FROM users WHERE user_id=?',(uid,)).fetchone()
            if u:
                conn.execute('UPDATE users SET total_points=total_points+?, games_played=games_played+1, wins=wins+?, last_played=?, display_name=? WHERE user_id=?', (pts, 1 if won else 0, datetime.now().isoformat(), name, uid))
            else:
                conn.execute('INSERT INTO users (user_id, display_name, total_points, games_played, wins, last_played) VALUES (?,?,?,1,?,?)', (uid, name, pts, 1 if won else 0, datetime.now().isoformat()))
            if gtype:
                conn.execute('INSERT INTO game_history (user_id, game_type, points, won) VALUES (?,?,?,?)', (uid, gtype, pts, 1 if won else 0))
            conn.commit()
            return True
    except: return False

def get_stats(uid):
    try:
        with get_db() as conn: return conn.execute('SELECT * FROM users WHERE user_id=?',(uid,)).fetchone()
    except: return None

def get_top(limit=10):
    try:
        with get_db() as conn: return conn.execute('SELECT display_name, total_points, games_played, wins FROM users ORDER BY total_points DESC LIMIT?',(limit,)).fetchall()
    except: return []

def normalize(txt):
    if not txt: return ""
    txt = str(txt).strip().lower()
    txt = txt.replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ؤ','و').replace('ئ','ي').replace('ء','').replace('ة','ه').replace('ى','ي')
    return re.sub(r'\s+','', re.sub(r'[\u064B-\u065F]','', txt))

def check_rate(uid, max_m=MAX_MSG, win=60):
    now, data = datetime.now(), user_msg_count[uid]
    if now - data['reset_time'] > timedelta(seconds=win):
        data['count'], data['reset_time'] = 0, now
    if data['count'] >= max_m: return False
    data['count'] += 1
    return True

def load_file(fname):
    try:
        path = os.path.join('games', fname)
        if os.path.exists(path):
            with open(path,'r',encoding='utf-8') as f: return [line.strip() for line in f if line.strip()]
    except: pass
    return []

QUESTIONS, CHALLENGES, CONFESSIONS, MENTIONS = load_file('questions.txt'), load_file('challenges.txt'), load_file('confessions.txt'), load_file('more_questions.txt')

def log_err(etype, msg, det=None):
    try:
        with error_lock:
            error_log.append({'time': datetime.now().isoformat(), 'type': etype, 'msg': str(msg)[:500]})
            if len(error_log) > MAX_ERR: error_log.pop(0)
    except: pass

def get_name(uid):
    with names_lock:
        if uid in user_names: return user_names[uid]
    try:
        profile = line_bot_api.get_profile(uid)
        name = profile.display_name.strip() if profile.display_name else None
        if name:
            with names_lock: user_names[uid] = name
            return name
    except: pass
    name = f"لاعب_{uid[-4:]}"
    with names_lock: user_names[uid] = name
    return name

def qr():
    return QuickReply(items=[QuickReplyButton(action=MessageAction(label=l,text=t)) for l,t in [("سؤال","سؤال"),("تحدي","تحدي"),("اعتراف","اعتراف"),("منشن","منشن"),("أغنية","أغنية"),("لعبة","لعبة"),("سلسلة","سلسلة"),("أسرع","أسرع"),("ضد","ضد"),("تكوين","تكوين"),("اختلاف","اختلاف"),("توافق","توافق")]])

def card(body, footer=None):
    c = {"type":"bubble","body":{"type":"box","layout":"vertical","contents":body,"backgroundColor":IOS["card"],"paddingAll":"20px"}}
    if footer: c["footer"] = {"type":"box","layout":"horizontal" if len(footer)>1 else "vertical","contents":footer,"backgroundColor":IOS["card"],"paddingAll":"16px","spacing":"sm"}
    return c

def btn(label, text, color=None):
    return {"type":"button","action":{"type":"message","label":label,"text":text},"style":"primary","color":color or IOS["primary"],"height":"sm"}

def welcome_card(name):
    body = [
        {"type":"image","url":LOGO_3D,"size":"full","aspectRatio":"1:1","aspectMode":"cover"},
        {"type":"box","layout":"vertical","contents":[
            {"type":"text","text":"بوت الحوت","size":"xxl","weight":"bold","color":IOS["text"],"align":"center"},
            {"type":"text","text":"3D Experience","size":"sm","color":IOS["text_dim"],"align":"center","margin":"sm"},
            {"type":"separator","margin":"lg","color":IOS["border"]},
            {"type":"text","text":name,"size":"lg","weight":"bold","color":IOS["text"],"align":"center","margin":"lg"}
        ],"paddingAll":"16px","backgroundColor":IOS["elevated"],"cornerRadius":"16px","margin":"lg"}
    ]
    footer = [btn("انضم","انضم"), btn("انسحب","انسحب",IOS["text_dim"]), btn("ابدأ اللعب","أغنية",IOS["accent"])]
    return card(body, footer)

def help_card():
    games_info = [
        ("أغنية","أكمل كلمات الأغنية\nمثال: يا ليل يا عين"),
        ("لعبة","إنسان حيوان نبات بلاد\nالحرف: ر\nاكتب كل كلمة في سطر"),
        ("سلسلة","الكلمة: قلم\nاكتب كلمة تبدأ بـ: م"),
        ("أسرع","اكتب النص بأسرع وقت"),
        ("ضد","ما عكس: جميل\nيدعم لمح وجاوب"),
        ("تكوين","6 حروف كون 3 كلمات\nيدعم لمح وجاوب"),
        ("اختلاف","ابحث عن 5 اختلافات\nللتسلية فقط بدون نقاط"),
        ("توافق","اكتب اسمين بمسافة\nمثال: أحمد سارة")
    ]
    
    carousel = {"type":"carousel","contents":[]}
    
    # بطاقة الأوامر
    cmd_body = [
        {"type":"text","text":"الأوامر","size":"xl","weight":"bold","color":IOS["text"],"align":"center"},
        {"type":"separator","margin":"md","color":IOS["border"]},
        {"type":"text","text":"▫️ انضم - التسجيل\n▫️ انسحب - الخروج\n▫️ نقاطي - إحصائياتك\n▫️ الصدارة - المتصدرون\n▫️ إيقاف - توقف اللعبة","size":"sm","color":IOS["text_dim"],"wrap":True,"margin":"md"}
    ]
    carousel["contents"].append(card(cmd_body))
    
    # بطاقة أثناء اللعب
    play_body = [
        {"type":"text","text":"أثناء اللعب","size":"xl","weight":"bold","color":IOS["text"],"align":"center"},
        {"type":"separator","margin":"md","color":IOS["border"]},
        {"type":"text","text":"▪️ لمح - تلميح\n(يعطي أول حرف + عدد الحروف)\n\n▪️ جاوب - الحل الصحيح\n(ثم ينتقل للسؤال التالي)\n\nكل لعبة 5 جولات","size":"sm","color":IOS["text_dim"],"wrap":True,"margin":"md"}
    ]
    carousel["contents"].append(card(play_body))
    
    # بطاقات الألعاب (كل 2 لعبة في بطاقة)
    for i in range(0, len(games_info), 2):
        game_body = []
        for j in range(2):
            if i+j < len(games_info):
                gname, gdesc = games_info[i+j]
                if game_body:
                    game_body.append({"type":"separator","margin":"md","color":IOS["border"]})
                game_body.extend([
                    {"type":"text","text":gname,"size":"md","weight":"bold","color":IOS["primary"],"margin":"md" if game_body else "none"},
                    {"type":"text","text":gdesc,"size":"xs","color":IOS["text_dim"],"wrap":True,"margin":"xs"}
                ])
        carousel["contents"].append(card(game_body))
    
    return carousel

def stats_card(uid, name):
    stats = get_stats(uid)
    if not stats:
        body = [
            {"type":"text","text":"إحصائياتك","size":"xl","weight":"bold","color":IOS["text"],"align":"center"},
            {"type":"separator","margin":"md","color":IOS["border"]},
            {"type":"text","text":"لم تبدأ بعد","size":"md","color":IOS["text_dim"],"align":"center","margin":"lg"}
        ]
        return card(body, [btn("ابدأ الآن","انضم")])
    
    wr = (stats['wins']/stats['games_played']*100) if stats['games_played']>0 else 0
    body = [
        {"type":"text","text":"إحصائياتك","size":"xl","weight":"bold","color":IOS["text"],"align":"center"},
        {"type":"text","text":name,"size":"sm","color":IOS["text_dim"],"align":"center","margin":"xs"},
        {"type":"separator","margin":"md","color":IOS["border"]},
        {"type":"box","layout":"vertical","contents":[
            {"type":"box","layout":"horizontal","contents":[
                {"type":"text","text":"النقاط","size":"sm","color":IOS["text_dim"],"flex":1},
                {"type":"text","text":str(stats['total_points']),"size":"xxl","weight":"bold","color":IOS["primary"],"flex":1,"align":"end"}
            ]},
            {"type":"separator","margin":"md","color":IOS["border"]},
            {"type":"box","layout":"horizontal","contents":[
                {"type":"text","text":"الألعاب","size":"sm","color":IOS["text_dim"],"flex":1},
                {"type":"text","text":str(stats['games_played']),"size":"md","weight":"bold","color":IOS["text"],"flex":1,"align":"end"}
            ],"margin":"md"},
            {"type":"box","layout":"horizontal","contents":[
                {"type":"text","text":"الفوز","size":"sm","color":IOS["text_dim"],"flex":1},
                {"type":"text","text":str(stats['wins']),"size":"md","weight":"bold","color":IOS["accent"],"flex":1,"align":"end"}
            ],"margin":"xs"},
            {"type":"box","layout":"horizontal","contents":[
                {"type":"text","text":"معدل الفوز","size":"sm","color":IOS["text_dim"],"flex":1},
                {"type":"text","text":f"{wr:.0f}%","size":"md","weight":"bold","color":IOS["secondary"],"flex":1,"align":"end"}
            ],"margin":"xs"}
        ],"backgroundColor":IOS["elevated"],"cornerRadius":"12px","paddingAll":"16px","margin":"md"}
    ]
    return card(body, [btn("الصدارة","الصدارة",IOS["secondary"])])

def top_card():
    leaders = get_top()
    if not leaders:
        body = [
            {"type":"text","text":"🏆 الصدارة","size":"xl","weight":"bold","color":IOS["text"],"align":"center"},
            {"type":"text","text":"لا توجد بيانات","size":"md","color":IOS["text_dim"],"align":"center","margin":"lg"}
        ]
        return card(body)
    
    items = []
    for i, l in enumerate(leaders, 1):
        rank = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"#{i}"
        color = IOS["primary"] if i<=3 else IOS["text_dim"]
        items.append({"type":"box","layout":"horizontal","contents":[
            {"type":"text","text":rank,"size":"md","color":color,"flex":0,"weight":"bold"},
            {"type":"text","text":l['display_name'],"size":"sm","color":color,"flex":3,"margin":"sm","wrap":True},
            {"type":"text","text":str(l['total_points']),"size":"md","color":color,"flex":1,"align":"end","weight":"bold"}
        ],"backgroundColor":IOS["elevated"] if i==1 else IOS["card"],"cornerRadius":"10px","paddingAll":"12px","margin":"xs" if i>1 else "none"})
    
    body = [
        {"type":"text","text":"🏆 الصدارة","size":"xl","weight":"bold","color":IOS["text"],"align":"center"},
        {"type":"separator","margin":"md","color":IOS["border"]},
        {"type":"box","layout":"vertical","contents":items,"margin":"md"}
    ]
    return card(body)

def winner_card(wname, wscore, all_scores):
    items = []
    for i, (name, score) in enumerate(all_scores, 1):
        rt = f"{'🥇' if i==1 else '🥈' if i==2 else '🥉' if i==3 else '#'+str(i)} المركز"
        color = IOS["primary"] if i==1 else IOS["text"] if i<=3 else IOS["text_muted"]
        items.append({"type":"box","layout":"horizontal","contents":[
            {"type":"box","layout":"vertical","contents":[
                {"type":"text","text":rt,"size":"xs","color":IOS["text_dim"]},
                {"type":"text","text":name,"size":"sm","color":color,"weight":"bold","wrap":True}
            ],"flex":3},
            {"type":"text","text":str(score),"size":"xl" if i==1 else "lg","color":color,"weight":"bold","align":"end","flex":1}
        ],"backgroundColor":IOS["elevated"] if i==1 else IOS["card"],"cornerRadius":"10px","paddingAll":"12px","margin":"xs" if i>1 else "none"})
    
    body = [
        {"type":"box","layout":"vertical","contents":[
            {"type":"text","text":"انتهت اللعبة","size":"lg","weight":"bold","color":IOS["text"],"align":"center"}
        ],"backgroundColor":IOS["elevated"],"cornerRadius":"12px","paddingAll":"16px"},
        {"type":"separator","margin":"md","color":IOS["border"]},
        {"type":"box","layout":"vertical","contents":[
            {"type":"text","text":"الفائز","size":"sm","color":IOS["text_dim"],"align":"center"},
            {"type":"text","text":wname,"size":"xl","weight":"bold","color":IOS["primary"],"align":"center","margin":"xs","wrap":True},
            {"type":"text","text":f"{wscore} نقطة","size":"md","weight":"bold","color":IOS["accent"],"align":"center","margin":"xs"}
        ],"margin":"md"},
        {"type":"separator","margin":"md","color":IOS["border"]},
        {"type":"text","text":"النتائج","size":"md","weight":"bold","color":IOS["text"],"margin":"md"},
        {"type":"box","layout":"vertical","contents":items,"margin":"xs"}
    ]
    footer = [btn("لعب مرة أخرى","أغنية"), btn("الصدارة","الصدارة",IOS["secondary"])]
    return card(body, footer)

def game_card(gtype, question, round_num, total_rounds, supports_hint=False):
    body = [
        {"type":"box","layout":"horizontal","contents":[
            {"type":"text","text":gtype,"size":"lg","weight":"bold","color":IOS["text"],"flex":1},
            {"type":"text","text":f"⏱️ {round_num}/{total_rounds}","size":"sm","color":IOS["text_dim"],"flex":0,"align":"end"}
        ]},
        {"type":"separator","margin":"md","color":IOS["border"]},
        {"type":"text","text":question,"size":"md","color":IOS["text"],"wrap":True,"margin":"md"}
    ]
    
    footer = []
    if supports_hint:
        footer.append(btn("لمح","لمح",IOS["secondary"]))
    footer.append(btn("جاوب","جاوب",IOS["accent"]))
    
    return card(body, footer if footer else None)

def start_game(gid, gclass, gtype, uid, event):
    if not gclass:
        try: line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"لعبة {gtype} غير متوفرة", quick_reply=qr()))
        except: pass
        return False
    try:
        with games_lock:
            if gclass.__name__ in ['SongGame','HumanAnimalPlantGame','LettersWordsGame']:
                game = gclass(line_bot_api, use_ai=USE_AI, ask_ai=ask_gemini)
            else:
                game = gclass(line_bot_api)
            with players_lock:
                participants = registered_players.copy()
                participants.add(uid)
            active_games[gid] = {'game':game,'type':gtype,'created':datetime.now(),'participants':participants,'answered':set(),'round':1}
        
        resp = game.start_game()
        
        # تحويل الرد إلى بطاقة لعبة
        supports_hint = gtype in ['أغنية','لعبة','ضد','تكوين']
        q_text = resp.text if isinstance(resp, TextSendMessage) else str(resp)
        game_flex = FlexSendMessage(alt_text=f"لعبة {gtype}", contents=game_card(gtype, q_text, 1, 5, supports_hint), quick_reply=qr())
        
        line_bot_api.reply_message(event.reply_token, game_flex)
        logger.info(f"✅ Started {gtype}")
        return True
    except Exception as e:
        logger.error(f"Start {gtype} failed: {e}")
        log_err('start_game', e)
        return False

@app.route("/", methods=['GET'])
def home():
    gc = sum(1 for g in games.values() if g)
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>بوت الحوت</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:-apple-system,sans-serif;background:{IOS['bg']};min-height:100vh;display:flex;align-items:center;justify-content:center}}.container{{background:{IOS['card']};border-radius:20px;box-shadow:0 2px 20px rgba(0,0,0,0.1);padding:40px;max-width:500px;width:100%}}h1{{text-align:center;color:{IOS['text']};margin-bottom:20px}}.status{{background:{IOS['elevated']};border-radius:12px;padding:20px;margin:20px 0}}.item{{display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid {IOS['border']}}}.item:last-child{{border:none}}.label{{color:{IOS['text_dim']}}}.value{{color:{IOS['primary']};font-weight:600}}.btn{{display:inline-block;padding:10px 20px;background:{IOS['primary']};color:white;text-decoration:none;border-radius:8px;margin:5px}}</style></head><body><div class="container"><h1>بوت الحوت</h1><div class="status"><div class="item"><span class="label">الخادم</span><span class="value">✅ يعمل</span></div><div class="item"><span class="label">Gemini AI</span><span class="value">{'✅ مفعّل' if USE_AI else '⚠️ معطّل'}</span></div><div class="item"><span class="label">اللاعبون</span><span class="value">{len(registered_players)}</span></div><div class="item"><span class="label">ألعاب نشطة</span><span class="value">{len(active_games)}</span></div><div class="item"><span class="label">ألعاب متوفرة</span><span class="value">{gc}/8</span></div></div><div style="text-align:center"><a href="/health" class="btn">الصحة</a><a href="/errors" class="btn">الأخطاء ({len(error_log)})</a></div></div></body></html>"""

@app.route("/health", methods=['GET'])
def health(): return jsonify({"status":"healthy","time":datetime.now().isoformat(),"games":len(active_games),"players":len(registered_players),"ai":USE_AI}), 200

@app.route("/errors", methods=['GET'])
def errors():
    with error_lock: errs = list(reversed(error_log))
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>الأخطاء</title><style>body{{font-family:-apple-system,sans-serif;background:{IOS['bg']};padding:20px}}.container{{max-width:900px;margin:auto;background:{IOS['card']};border-radius:16px;padding:30px}}h1{{color:{IOS['text']}}}. err{{background:{IOS['elevated']};border-left:3px solid {IOS['primary']};padding:12px;margin:10px 0;border-radius:8px}}.time{{color:{IOS['text_dim']};font-size:0.9em}}.btn{{display:inline-block;margin-top:20px;padding:10px 20px;background:{IOS['primary']};color:white;text-decoration:none;border-radius:8px}}</style></head><body><div class="container"><h1>سجل الأخطاء</h1>"""
    if not errs: html += '<p>لا توجد أخطاء</p>'
    else:
        for e in errs: html += f"""<div class="err"><div class="time">{e.get('time','Unknown')}</div><div>{e.get('type','Unknown')}: {e.get('msg','')}</div></div>"""
    html += '<a href="/" class="btn">العودة</a></div></body></html>'
    return html

@app.route("/callback", methods=['POST'])
def callback():
    sig = request.headers.get('X-Line-Signature','')
    if not sig: abort(400)
    body = request.get_data(as_text=True)
    try: handler.handle(body, sig)
    except InvalidSignatureError: logger.error("Invalid signature"); abort(400)
    except Exception as e: logger.error(f"Callback: {e}"); log_err('callback', e)
    return 'OK', 200

@handler.add(MessageEvent, message=TextMessage)
def handle_msg(event):
    uid, txt = None, None
    try:
        uid = event.source.user_id
        txt = (event.message.text or "").strip()
        if not uid or not txt: return
        
        with players_lock:
            if uid not in registered_players: registered_players.add(uid)
        if not check_rate(uid): return
        
        name = get_name(uid)
        gid = getattr(event.source, 'group_id', uid)
        
        # الأوامر
        if txt in ['البداية','ابدأ','start','البوت']:
            line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text=f"مرحباً {name}", contents=welcome_card(name), quick_reply=qr()))
            return
        
        if txt in ['مساعدة','help']:
            line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="المساعدة", contents=help_card(), quick_reply=qr()))
            return
        
        if txt in ['نقاطي','إحصائياتي','احصائياتي']:
            line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="إحصائياتك", contents=stats_card(uid, name), quick_reply=qr()))
            return
        
        if txt in ['الصدارة','المتصدرين']:
            line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="الصدارة", contents=top_card(), quick_reply=qr()))
            return
        
        if txt in ['إيقاف','stop','ايقاف']:
            with games_lock:
                if gid in active_games:
                    gt = active_games[gid]['type']
                    del active_games[gid]
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"تم إيقاف {gt}", quick_reply=qr()))
                else:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="لا توجد لعبة نشطة", quick_reply=qr()))
            return
        
        if txt in ['انضم','تسجيل','join']:
            with players_lock:
                if uid in registered_players:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"أنت مسجل بالفعل يا {name}", quick_reply=qr()))
                else:
                    registered_players.add(uid)
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"مرحباً {name}! تم التسجيل بنجاح", quick_reply=qr()))
            return
        
        if txt in ['انسحب','خروج']:
            with players_lock:
                if uid in registered_players:
                    registered_players.remove(uid)
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"تم الانسحاب يا {name}", quick_reply=qr()))
                else:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="أنت غير مسجل", quick_reply=qr()))
            return
        
        # أوامر نصية
        if txt in ['سؤال','سوال'] and QUESTIONS:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=random.choice(QUESTIONS), quick_reply=qr()))
            return
        if txt in ['تحدي','challenge'] and CHALLENGES:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=random.choice(CHALLENGES), quick_reply=qr()))
            return
        if txt in ['اعتراف','confession'] and CONFESSIONS:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=random.choice(CONFESSIONS), quick_reply=qr()))
            return
        if txt in ['منشن','mention'] and MENTIONS:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=random.choice(MENTIONS), quick_reply=qr()))
            return
        
        # الألعاب
        games_map = {
            'أغنية': (games['SongGame'], 'أغنية'),
            'لعبة': (games['HumanAnimalPlantGame'], 'لعبة'),
            'سلسلة': (games['ChainWordsGame'], 'سلسلة'),
            'أسرع': (games['FastTypingGame'], 'أسرع'),
            'ضد': (games['OppositeGame'], 'ضد'),
            'تكوين': (games['LettersWordsGame'], 'تكوين'),
            'اختلاف': (games['DifferencesGame'], 'اختلاف'),
            'توافق': (games['CompatibilityGame'], 'توافق')
        }
        
        if txt in games_map:
            gclass, gtype = games_map[txt]
            
            # معالجة خاصة للتوافق
            if txt == 'توافق' and gclass:
                with games_lock:
                    with players_lock:
                        participants = registered_players.copy()
                        participants.add(uid)
                    active_games[gid] = {'game':gclass(line_bot_api),'type':'توافق','created':datetime.now(),'participants':participants,'answered':set(),'waiting_names':True}
                
                compat_body = [
                    {"type":"text","text":"لعبة التوافق","size":"lg","weight":"bold","color":IOS["text"],"align":"center"},
                    {"type":"separator","margin":"md","color":IOS["border"]},
                    {"type":"text","text":"اكتب اسمين مفصولين بمسافة\nنص فقط بدون رموز\n\nمثال: أحمد سارة","size":"sm","color":IOS["text_dim"],"wrap":True,"margin":"md"}
                ]
                line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="لعبة التوافق", contents=card(compat_body), quick_reply=qr()))
                return
            
            # معالجة خاصة للاختلافات
            if txt == 'اختلاف' and gclass:
                diff_body = [
                    {"type":"text","text":"لعبة الاختلافات","size":"lg","weight":"bold","color":IOS["text"],"align":"center"},
                    {"type":"separator","margin":"md","color":IOS["border"]},
                    {"type":"text","text":"ابحث عن 5 اختلافات\n\n▫️ للتسلية فقط\n▫️ بدون نقاط\n▫️ لا يحسب في الإحصائيات","size":"sm","color":IOS["text_dim"],"wrap":True,"margin":"md"}
                ]
                line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="لعبة الاختلافات", contents=card(diff_body, [btn("جاوب","جاوب",IOS["accent"])]), quick_reply=qr()))
                
                with games_lock:
                    with players_lock:
                        participants = registered_players.copy()
                        participants.add(uid)
                    active_games[gid] = {'game':gclass(line_bot_api),'type':'اختلاف','created':datetime.now(),'participants':participants,'answered':set()}
                return
            
            if gid in active_games:
                active_games[gid]['last_game'] = txt
            
            start_game(gid, gclass, gtype, uid, event)
            return
        
        # معالجة أوامر اللعب
        if gid in active_games:
            gdata = active_games[gid]
            gtype = gdata['type']
            game = gdata['game']
            
            # معالجة لعبة التوافق
            if gtype == 'توافق' and gdata.get('waiting_names'):
                cleaned = txt.replace('@','').strip()
                if '@' in txt:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="بدون علامة @", quick_reply=qr()))
                    return
                names = cleaned.split()
                if len(names) < 2:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="اكتب اسمين مفصولين بمسافة", quick_reply=qr()))
                    return
                try:
                    result = game.check_answer(f"{names[0]} {names[1]}", uid, name)
                    gdata['waiting_names'] = False
                    with games_lock:
                        if gid in active_games: del active_games[gid]
                    if result and result.get('response'):
                        resp = result['response']
                        if isinstance(resp, TextSendMessage): resp.quick_reply = qr()
                        line_bot_api.reply_message(event.reply_token, resp)
                    return
                except Exception as e:
                    logger.error(f"Compatibility error: {e}")
                    log_err('compatibility', e)
                    return
            
            with players_lock:
                if uid not in registered_players: return
            
            # أمر لمح
            if txt in ['لمح','تلميح','hint']:
                supports_hint = gtype in ['أغنية','لعبة','ضد','تكوين']
                if not supports_hint:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"▫️ لعبة {gtype} لا تدعم التلميحات", quick_reply=qr()))
                    return
                
                try:
                    hint_result = game.get_hint() if hasattr(game, 'get_hint') else None
                    if hint_result:
                        # تنسيق التلميح: الحرف الأول + عدد الحروف
                        hint_text = f"▪️ تلميح:\n\nالحرف الأول: {hint_result[0]}\nعدد الحروف: {len(hint_result)} (_ " * (len(hint_result)-1) + ")"
                        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=hint_text, quick_reply=qr()))
                    else:
                        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="▫️ لا يوجد تلميح متاح", quick_reply=qr()))
                    return
                except:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="▫️ خطأ في التلميح", quick_reply=qr()))
                    return
            
            # أمر جاوب
            if txt in ['جاوب','الحل','الجواب','answer']:
                try:
                    # الحصول على الإجابة الصحيحة
                    correct_ans = game.get_correct_answer() if hasattr(game, 'get_correct_answer') else "غير متوفر"
                    
                    # الانتقال للسؤال التالي
                    current_round = gdata.get('round', 1)
                    if current_round < 5:
                        gdata['round'] = current_round + 1
                        gdata['answered'] = set()
                        next_q = game.next_question()
                        
                        if next_q:
                            supports_hint = gtype in ['أغنية','لعبة','ضد','تكوين']
                            q_text = next_q.text if isinstance(next_q, TextSendMessage) else str(next_q)
                            ans_text = f"▪️ الحل: {correct_ans}\n\n{'─' * 20}\n\nالسؤال التالي:"
                            
                            # إرسال الحل والسؤال التالي
                            line_bot_api.reply_message(event.reply_token, [
                                TextSendMessage(text=ans_text, quick_reply=qr()),
                                FlexSendMessage(alt_text=f"الجولة {current_round + 1}", contents=game_card(gtype, q_text, current_round + 1, 5, supports_hint), quick_reply=qr())
                            ])
                        else:
                            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"▪️ الحل: {correct_ans}", quick_reply=qr()))
                    else:
                        # آخر جولة - إنهاء اللعبة
                        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"▪️ الحل: {correct_ans}\n\nانتهت اللعبة!", quick_reply=qr()))
                        with games_lock:
                            if gid in active_games: del active_games[gid]
                    return
                except Exception as e:
                    logger.error(f"Answer error: {e}")
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="▫️ خطأ في عرض الحل", quick_reply=qr()))
                    return
            
            # معالجة الإجابات العادية
            if uid in gdata.get('answered', set()): return
            
            try:
                result = game.check_answer(txt, uid, name)
                if not result: return
                
                if result.get('correct'):
                    gdata.setdefault('answered', set()).add(uid)
                
                pts = result.get('points', 0)
                if pts > 0 and gtype != 'اختلاف':  # لا نقاط للاختلافات
                    update_points(uid, name, pts, result.get('won', False), gtype)
                
                # الانتقال للسؤال التالي تلقائياً
                if result.get('next_question'):
                    current_round = gdata.get('round', 1)
                    if current_round < 5:
                        gdata['round'] = current_round + 1
                        gdata['answered'] = set()
                        next_q = game.next_question()
                        
                        if next_q:
                            supports_hint = gtype in ['أغنية','لعبة','ضد','تكوين']
                            q_text = next_q.text if isinstance(next_q, TextSendMessage) else str(next_q)
                            
                            line_bot_api.reply_message(event.reply_token, [
                                TextSendMessage(text=result.get('message', 'صحيح!'), quick_reply=qr()),
                                FlexSendMessage(alt_text=f"الجولة {current_round + 1}", contents=game_card(gtype, q_text, current_round + 1, 5, supports_hint), quick_reply=qr())
                            ])
                            return
                
                # انتهاء اللعبة
                if result.get('game_over'):
                    with games_lock:
                        last_game = active_games.get(gid, {}).get('last_game', 'أغنية')
                        if gid in active_games: del active_games[gid]
                    
                    if result.get('winner_card'):
                        wcard = result['winner_card']
                        if 'footer' in wcard:
                            for b in wcard['footer'].get('contents', []):
                                if 'لعب' in b.get('action', {}).get('label', ''):
                                    b['action']['text'] = last_game
                        line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="الفائز", contents=wcard, quick_reply=qr()))
                    else:
                        resp = result.get('response', TextSendMessage(text=result.get('message', '')))
                        if isinstance(resp, TextSendMessage): resp.quick_reply = qr()
                        line_bot_api.reply_message(event.reply_token, resp)
                    return
                
                # رد عادي
                resp = result.get('response', TextSendMessage(text=result.get('message', '')))
                if isinstance(resp, TextSendMessage): resp.quick_reply = qr()
                elif isinstance(resp, list):
                    for r in resp:
                        if isinstance(r, TextSendMessage): r.quick_reply = qr()
                line_bot_api.reply_message(event.reply_token, resp)
                
            except Exception as e:
                logger.error(f"Game answer error: {e}")
                log_err('game_answer', e)
    
    except Exception as e:
        logger.error(f"Handler error: {e}")
        log_err('handle_msg', e)
        try:
            if hasattr(event, 'reply_token') and event.reply_token:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="حدث خطأ مؤقت. حاول مرة أخرى", quick_reply=qr()))
        except: pass

def cleanup():
    while True:
        try:
            time.sleep(300)
            now = datetime.now()
            to_del = []
            with games_lock:
                for gid, data in active_games.items():
                    if now - data.get('created', now) > timedelta(minutes=TIMEOUT):
                        to_del.append(gid)
                for gid in to_del: del active_games[gid]
                if to_del: logger.info(f"Cleaned {len(to_del)} game(s)")
            with names_lock:
                if len(user_names) > MAX_CACHE:
                    user_names.clear()
                    logger.info("Cleared cache")
            with error_lock:
                if len(error_log) > MAX_ERR * 2:
                    error_log[:] = error_log[-MAX_ERR:]
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            log_err('cleanup', e)

threading.Thread(target=cleanup, daemon=True).start()

@app.errorhandler(400)
def bad_req(e): return 'Bad Request', 400
@app.errorhandler(404)
def not_found(e): return 'Not Found', 404
@app.errorhandler(500)
def internal(e): logger.error(f"Internal: {e}"); log_err('internal', e); return 'Internal Server Error', 500
@app.errorhandler(Exception)
def handle_err(e):
    logger.error(f"Unexpected: {e}")
    log_err('unexpected', e)
    if request.path == '/callback': return 'OK', 200
    return 'Internal Server Error', 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    logger.info("=" * 50)
    logger.info("بوت الحوت - 3D Experience")
    logger.info("=" * 50)
    logger.info(f"Port: {port}")
    logger.info(f"AI: {'✅' if USE_AI else '⚠️'}")
    loaded = [n for n, c in games.items() if c]
    logger.info(f"Games: {len(loaded)}/8")
    for n in loaded: logger.info(f"  ✓ {n}")
    logger.info("=" * 50)
    try:
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    except Exception as e:
        logger.error(f"Failed: {e}")
        log_err('app_start', e)
        sys.exit(1)
