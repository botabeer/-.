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

COSMIC = {"primary":"#00D4FF","secondary":"#0099FF","accent":"#004D66","bg":"#0A0E27","card":"#111827","elevated":"#1F2937","border":"#00D4FF","text":"#FFFFFF","text_dim":"#8B9DC3","text_muted":"#56607C","glow":"#00D4FF","dark":"#0A0E1A"}

PISCES_LOGO = "https://i.ibb.co/KVqg9wY/pisces-logo-3d.png"

DB_NAME,MAX_MESSAGES_PER_MINUTE,GAME_TIMEOUT_MINUTES,MAX_ERROR_LOG_SIZE,MAX_CACHE_SIZE='game_scores.db',30,15,50,1000
QUESTIONS_PER_GAME = 5

USE_AI,ask_gemini=False,None
try:
    import google.generativeai as genai
    api_keys=[os.getenv(f'GEMINI_API_KEY_{i}','').strip() for i in range(1,4)]
    api_keys=[k for k in api_keys if k]
    if api_keys:
        genai.configure(api_key=api_keys[0])
        model=genai.GenerativeModel('gemini-2.0-flash-exp')
        USE_AI=True
        def ask_gemini(prompt,max_retries=2):
            for attempt in range(max_retries):
                try:
                    if attempt>0 and attempt<len(api_keys):genai.configure(api_key=api_keys[attempt])
                    return model.generate_content(prompt).text.strip()
                except Exception as e:
                    logger.warning(f"Gemini attempt {attempt+1} failed: {e}")
                    if attempt==max_retries-1:return None
            return None
        logger.info(f"Gemini AI: {len(api_keys)} key(s)")
except Exception as e:logger.warning(f"Gemini AI unavailable: {e}")

games={}
game_names=['SongGame','HumanAnimalPlantGame','ChainWordsGame','FastTypingGame','OppositeGame','LettersWordsGame','CompatibilityGame','SpeedSortingGame']
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'games'))
for name in game_names:
    try:
        module=__import__(name.lower().replace('game','_game'),fromlist=[name])
        games[name]=getattr(module,name)
        logger.info(f"Loaded {name}")
    except Exception as e:
        games[name]=None
        logger.warning(f"{name}: {e}")

app=Flask(__name__)
TOKEN,SECRET=os.getenv('LINE_CHANNEL_ACCESS_TOKEN','').strip(),os.getenv('LINE_CHANNEL_SECRET','').strip()
if not TOKEN or not SECRET:
    logger.critical("LINE credentials missing")
    sys.exit(1)
line_bot_api,handler=LineBotApi(TOKEN),WebhookHandler(SECRET)

active_games,registered_players,user_message_count,user_names_cache,error_log={},set(),defaultdict(lambda:{'count':0,'reset_time':datetime.now()}),{},[]
games_lock,players_lock,names_cache_lock,error_log_lock=threading.RLock(),threading.RLock(),threading.RLock(),threading.RLock()

@contextmanager
def get_db():
    conn=None
    try:
        conn=sqlite3.connect(DB_NAME,check_same_thread=False,timeout=10.0)
        conn.row_factory=sqlite3.Row
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA synchronous=NORMAL')
        yield conn
    except Exception as e:
        logger.error(f"DB error: {e}")
        if conn:conn.rollback()
        raise
    finally:
        if conn:conn.close()

def init_db():
    try:
        with get_db() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY,display_name TEXT NOT NULL,total_points INTEGER DEFAULT 0,games_played INTEGER DEFAULT 0,wins INTEGER DEFAULT 0,last_played TEXT,registered_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
            conn.execute('''CREATE TABLE IF NOT EXISTS game_history (id INTEGER PRIMARY KEY AUTOINCREMENT,user_id TEXT NOT NULL,game_type TEXT NOT NULL,points INTEGER DEFAULT 0,won INTEGER DEFAULT 0,played_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY (user_id) REFERENCES users(user_id))''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_points ON users(total_points DESC)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_history_user ON game_history(user_id)')
            conn.commit()
            logger.info("DB ready")
    except Exception as e:
        logger.error(f"DB init failed: {e}")
        raise
init_db()

def update_user_points(user_id,name,points,won=False,game_type=""):
    try:
        with get_db() as conn:
            user=conn.execute('SELECT * FROM users WHERE user_id=?',(user_id,)).fetchone()
            if user:
                conn.execute('UPDATE users SET total_points=total_points+?,games_played=games_played+1,wins=wins+?,last_played=?,display_name=? WHERE user_id=?',(points,1 if won else 0,datetime.now().isoformat(),name,user_id))
            else:
                conn.execute('INSERT INTO users (user_id,display_name,total_points,games_played,wins,last_played) VALUES (?,?,?,1,?,?)',(user_id,name,points,1 if won else 0,datetime.now().isoformat()))
            if game_type:
                conn.execute('INSERT INTO game_history (user_id,game_type,points,won) VALUES (?,?,?,?)',(user_id,game_type,points,1 if won else 0))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Update points failed: {e}")
        return False

def get_user_stats(user_id):
    try:
        with get_db() as conn:return conn.execute('SELECT * FROM users WHERE user_id=?',(user_id,)).fetchone()
    except:return None

def get_leaderboard(limit=10):
    try:
        with get_db() as conn:return conn.execute('SELECT display_name,total_points,games_played,wins FROM users ORDER BY total_points DESC LIMIT?',(limit,)).fetchall()
    except:return[]

def normalize_text(text):
    if not text:return ""
    text=str(text).strip().lower()
    text=text.replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ؤ','و').replace('ئ','ي').replace('ء','').replace('ة','ه').replace('ى','ي')
    return re.sub(r'\s+','',re.sub(r'[\u064B-\u065F]','',text))

def check_rate_limit(user_id,max_msg=MAX_MESSAGES_PER_MINUTE,window=60):
    now,data=datetime.now(),user_message_count[user_id]
    if now-data['reset_time']>timedelta(seconds=window):
        data['count'],data['reset_time']=0,now
    if data['count']>=max_msg:return False
    data['count']+=1
    return True

def load_text_file(filename):
    try:
        path=os.path.join('games',filename)
        if os.path.exists(path):
            with open(path,'r',encoding='utf-8') as f:return[line.strip()for line in f if line.strip()]
    except Exception as e:logger.error(f"Load {filename} failed: {e}")
    return[]

QUESTIONS,CHALLENGES,CONFESSIONS,MENTION_QUESTIONS=load_text_file('questions.txt'),load_text_file('challenges.txt'),load_text_file('confessions.txt'),load_text_file('more_questions.txt')

def log_error(err_type,message,details=None):
    try:
        with error_log_lock:
            error_log.append({'timestamp':datetime.now().isoformat(),'type':err_type,'message':str(message)[:500],'details':details or{},'traceback':traceback.format_exc()[:1000]})
            if len(error_log)>MAX_ERROR_LOG_SIZE:error_log.pop(0)
    except:pass

def get_user_profile_safe(user_id):
    with names_cache_lock:
        if user_id in user_names_cache:return user_names_cache[user_id]
    try:
        profile=line_bot_api.get_profile(user_id)
        name=profile.display_name.strip()if profile.display_name else None
        if name:
            with names_cache_lock:user_names_cache[user_id]=name
            try:
                with get_db()as conn:
                    conn.execute('UPDATE users SET display_name=? WHERE user_id=?',(name,user_id))
                    conn.commit()
            except:pass
            return name
    except LineBotApiError as e:
        if e.status_code==404:logger.debug(f"Profile not found: {user_id[-4:]}")
    except Exception as e:logger.error(f"Profile error: {e}")
    name=f"لاعب_{user_id[-4:]}"
    with names_cache_lock:user_names_cache[user_id]=name
    return name

def get_quick_reply():
    return QuickReply(items=[QuickReplyButton(action=MessageAction(label=l,text=t))for l,t in[("سؤال","سؤال"),("تحدي","تحدي"),("اعتراف","اعتراف"),("منشن","منشن"),("أغنية","أغنية"),("لعبة","لعبة"),("أسرع","أسرع"),("ترتيب","ترتيب"),("تكوين","تكوين"),("ضد","ضد"),("توافق","توافق"),("سلسلة","سلسلة"),("لمح","لمح"),("جاوب","جاوب")]])

def create_card(body_contents,footer_buttons=None):
    card={"type":"bubble","body":{"type":"box","layout":"vertical","contents":body_contents,"backgroundColor":COSMIC["card"],"paddingAll":"24px","spacing":"md"}}
    if footer_buttons:card["footer"]={"type":"box","layout":"horizontal"if len(footer_buttons)>1 else"vertical","contents":footer_buttons,"backgroundColor":COSMIC["dark"],"paddingAll":"16px","spacing":"sm"}
    return card

def make_button(label,text,color=None):
    return{"type":"button","action":{"type":"message","label":label,"text":text},"style":"primary","color":color or COSMIC["primary"],"height":"sm"}

def get_welcome_card(name):
    games_list=[
        {"icon":"🎵","name":"أغنية","desc":"خمن الأغنية"},
        {"icon":"🎮","name":"لعبة","desc":"إنسان حيوان نبات"},
        {"icon":"⛓️","name":"سلسلة","desc":"ربط الكلمات"},
        {"icon":"⚡","name":"أسرع","desc":"اكتب بسرعة"},
        {"icon":"↔️","name":"ضد","desc":"الكلمة المعاكسة"},
        {"icon":"🔤","name":"تكوين","desc":"كون كلمة"},
        {"icon":"💕","name":"توافق","desc":"نسبة التوافق"},
        {"icon":"🔢","name":"ترتيب","desc":"رتب العناصر"}
    ]
    game_items=[]
    for g in games_list:
        game_items.append({"type":"box","layout":"horizontal","contents":[
            {"type":"text","text":g['icon'],"size":"lg","flex":0},
            {"type":"text","text":g['name'],"size":"sm","color":COSMIC["text"],"weight":"bold","flex":1,"margin":"md"},
            {"type":"text","text":g['desc'],"size":"xs","color":COSMIC["text_muted"],"flex":2,"align":"end"}
        ],"margin":"sm"if game_items else"none"})
    
    body=[
        {"type":"box","layout":"vertical","contents":[
            {"type":"image","url":PISCES_LOGO,"size":"full","aspectRatio":"1:1","aspectMode":"cover"}
        ],"width":"200px","height":"200px","cornerRadius":"100px"},
        {"type":"text","text":"بوت الحوت","size":"xxl","weight":"bold","color":COSMIC["primary"],"align":"center","margin":"lg"},
        {"type":"text","text":"3D Gaming Experience","size":"xs","color":COSMIC["text_dim"],"align":"center","margin":"xs"},
        {"type":"separator","margin":"lg","color":COSMIC["border"]},
        {"type":"text","text":f"مرحباً {name}","size":"md","color":COSMIC["text"],"align":"center","margin":"md","weight":"bold"},
        {"type":"box","layout":"vertical","contents":game_items,"backgroundColor":COSMIC["elevated"],"cornerRadius":"12px","paddingAll":"14px","margin":"md"},
        {"type":"separator","margin":"md","color":COSMIC["border"]},
        {"type":"text","text":"بوت الحوت © 2025","size":"xxs","color":COSMIC["text_muted"],"align":"center","margin":"sm"}
    ]
    footer=[
        make_button("انضم","انضم",COSMIC["primary"]),
        make_button("انسحب","انسحب",COSMIC["accent"]),
        make_button("ابدأ","ابدأ",COSMIC["glow"])
    ]
    return create_card(body,footer)

def get_help_card():
    body=[
        {"type":"box","layout":"vertical","contents":[
            {"type":"image","url":PISCES_LOGO,"size":"full","aspectRatio":"1:1","aspectMode":"cover"}
        ],"width":"120px","height":"120px","cornerRadius":"60px"},
        {"type":"text","text":"دليل الاستخدام","size":"xl","weight":"bold","color":COSMIC["primary"],"align":"center","margin":"md"},
        {"type":"separator","margin":"lg","color":COSMIC["border"]},
        {"type":"box","layout":"vertical","contents":[
            {"type":"text","text":"الأوامر الأساسية","size":"md","weight":"bold","color":COSMIC["primary"]},
            {"type":"text","text":"انضم - للانضمام\nانسحب - للخروج\nنقاطي - إحصائياتك\nالصدارة - أفضل اللاعبين\nإيقاف - إنهاء اللعبة","size":"xs","color":COSMIC["text_dim"],"wrap":True,"margin":"sm"}
        ],"backgroundColor":COSMIC["elevated"],"cornerRadius":"12px","paddingAll":"14px","margin":"md"},
        {"type":"box","layout":"vertical","contents":[
            {"type":"text","text":"أثناء اللعب","size":"md","weight":"bold","color":COSMIC["primary"]},
            {"type":"text","text":"اكتب جوابك مباشرة\nلمح - تلميح\nجاوب - عرض الإجابة","size":"xs","color":COSMIC["text_dim"],"wrap":True,"margin":"sm"}
        ],"backgroundColor":COSMIC["elevated"],"cornerRadius":"12px","paddingAll":"14px","margin":"sm"},
        {"type":"separator","margin":"md","color":COSMIC["border"]},
        {"type":"text","text":"بوت الحوت © 2025","size":"xxs","color":COSMIC["text_muted"],"align":"center","margin":"sm"}
    ]
    footer=[
        make_button("إيقاف","إيقاف",COSMIC["accent"]),
        make_button("نقاطي","نقاطي",COSMIC["primary"]),
        make_button("الصدارة","الصدارة",COSMIC["glow"])
    ]
    return create_card(body,footer)

def get_stats_card(user_id,name):
    stats=get_user_stats(user_id)
    if not stats:
        body=[
            {"type":"box","layout":"vertical","contents":[
                {"type":"image","url":PISCES_LOGO,"size":"full","aspectRatio":"1:1","aspectMode":"cover"}
            ],"width":"120px","height":"120px","cornerRadius":"60px"},
            {"type":"text","text":"إحصائياتك","size":"xl","weight":"bold","color":COSMIC["primary"],"align":"center","margin":"md"},
            {"type":"separator","margin":"lg","color":COSMIC["border"]},
            {"type":"text","text":"لم تبدأ اللعب بعد","size":"sm","color":COSMIC["text_dim"],"align":"center","margin":"lg"}
        ]
        return create_card(body,[make_button("ابدأ الآن","ابدأ",COSMIC["primary"])])
    win_rate=(stats['wins']/stats['games_played']*100)if stats['games_played']>0 else 0
    body=[
        {"type":"box","layout":"vertical","contents":[
            {"type":"image","url":PISCES_LOGO,"size":"full","aspectRatio":"1:1","aspectMode":"cover"}
        ],"width":"100px","height":"100px","cornerRadius":"50px"},
        {"type":"text","text":"إحصائياتك","size":"lg","weight":"bold","color":COSMIC["primary"],"align":"center","margin":"sm"},
        {"type":"text","text":name,"size":"xs","color":COSMIC["text_dim"],"align":"center","margin":"xs"},
        {"type":"separator","margin":"md","color":COSMIC["border"]},
        {"type":"box","layout":"vertical","contents":[
            {"type":"box","layout":"horizontal","contents":[
                {"type":"text","text":"النقاط","size":"sm","color":COSMIC["text_muted"],"flex":1},
                {"type":"text","text":str(stats['total_points']),"size":"xl","weight":"bold","color":COSMIC["glow"],"flex":1,"align":"end"}
            ]},
            {"type":"separator","margin":"sm","color":COSMIC["border"]},
            {"type":"box","layout":"horizontal","contents":[
                {"type":"text","text":"الألعاب","size":"xs","color":COSMIC["text_muted"],"flex":1},
                {"type":"text","text":str(stats['games_played']),"size":"md","weight":"bold","color":COSMIC["text"],"flex":1,"align":"end"}
            ],"margin":"sm"},
            {"type":"box","layout":"horizontal","contents":[
                {"type":"text","text":"الفوز","size":"xs","color":COSMIC["text_muted"],"flex":1},
                {"type":"text","text":str(stats['wins']),"size":"md","weight":"bold","color":COSMIC["primary"],"flex":1,"align":"end"}
            ],"margin":"xs"},
            {"type":"box","layout":"horizontal","contents":[
                {"type":"text","text":"معدل الفوز","size":"xs","color":COSMIC["text_muted"],"flex":1},
                {"type":"text","text":f"{win_rate:.0f}%","size":"md","weight":"bold","color":COSMIC["secondary"],"flex":1,"align":"end"}
            ],"margin":"xs"}
        ],"backgroundColor":COSMIC["elevated"],"cornerRadius":"12px","paddingAll":"12px","margin":"md"},
        {"type":"separator","margin":"md","color":COSMIC["border"]},
        {"type":"text","text":"بوت الحوت © 2025","size":"xxs","color":COSMIC["text_muted"],"align":"center","margin":"xs"}
    ]
    return create_card(body,[make_button("الصدارة","الصدارة",COSMIC["glow"])])

def get_leaderboard_card():
    leaders=get_leaderboard()
    if not leaders:
        body=[
            {"type":"box","layout":"vertical","contents":[
                {"type":"image","url":PISCES_LOGO,"size":"full","aspectRatio":"1:1","aspectMode":"cover"}
            ],"width":"120px","height":"120px","cornerRadius":"60px"},
            {"type":"text","text":"لوحة الصدارة","size":"xl","weight":"bold","color":COSMIC["primary"],"align":"center","margin":"md"},
            {"type":"text","text":"لا توجد بيانات","size":"sm","color":COSMIC["text_dim"],"align":"center","margin":"lg"}
        ]
        return create_card(body)
    items=[]
    for i,leader in enumerate(leaders,1):
        rank=f"[{i}]"
        color=COSMIC["glow"]if i==1 else COSMIC["primary"]if i==2 else COSMIC["secondary"]if i==3 else COSMIC["text_muted"]
        items.append({"type":"box","layout":"horizontal","contents":[
            {"type":"text","text":rank,"size":"md","color":color,"flex":0,"weight":"bold"},
            {"type":"text","text":leader['display_name'],"size":"xs","color":color,"flex":3,"margin":"sm","wrap":True,"weight":"bold"if i<=3 else"regular"},
            {"type":"text","text":str(leader['total_points']),"size":"md"if i<=3 else"sm","color":color,"flex":1,"align":"end","weight":"bold"}
        ],"backgroundColor":COSMIC["elevated"]if i<=3 else COSMIC["card"],"cornerRadius":"10px","paddingAll":"10px","margin":"xs"if i>1 else"none","borderColor":COSMIC["border"]if i==1 else"transparent","borderWidth":"1px"})
    body=[
        {"type":"box","layout":"vertical","contents":[
            {"type":"image","url":PISCES_LOGO,"size":"full","aspectRatio":"1:1","aspectMode":"cover"}
        ],"width":"100px","height":"100px","cornerRadius":"50px"},
        {"type":"text","text":"لوحة الصدارة","size":"lg","weight":"bold","color":COSMIC["primary"],"align":"center","margin":"sm"},
        {"type":"text","text":"أفضل اللاعبين","size":"xxs","color":COSMIC["text_dim"],"align":"center","margin":"xs"},
        {"type":"separator","margin":"md","color":COSMIC["border"]},
        {"type":"box","layout":"vertical","contents":items,"margin":"sm"},
        {"type":"separator","margin":"md","color":COSMIC["border"]},
        {"type":"text","text":"بوت الحوت © 2025","size":"xxs","color":COSMIC["text_muted"],"align":"center","margin":"xs"}
    ]
    return create_card(body)

def get_game_question_card(game_type,question_num,question_text,supports_hint=True):
    body=[
        {"type":"text","text":game_type,"size":"md","weight":"bold","color":COSMIC["glow"],"align":"center"},
        {"type":"text","text":f"السؤال {question_num} من {QUESTIONS_PER_GAME}","size":"xs","color":COSMIC["text_dim"],"align":"center","margin":"xs"},
        {"type":"separator","margin":"sm","color":COSMIC["border"]},
        {"type":"box","layout":"vertical","contents":[
            {"type":"text","text":question_text,"size":"sm","color":COSMIC["text"],"wrap":True,"weight":"bold"}
        ],"backgroundColor":COSMIC["elevated"],"cornerRadius":"10px","paddingAll":"12px","margin":"md"}
    ]
    if supports_hint:
        body.append({"type":"text","text":"استخدم: لمح أو جاوب","size":"xxs","color":COSMIC["text_muted"],"align":"center","margin":"sm"})
        footer=[make_button("لمح","لمح",COSMIC["secondary"]),make_button("جاوب","جاوب",COSMIC["accent"])]
    else:
        body.append({"type":"text","text":"هذه اللعبة لا تدعم لمح","size":"xxs","color":COSMIC["text_muted"],"align":"center","margin":"sm"})
        footer=[make_button("جاوب","جاوب",COSMIC["accent"])]
    return create_card(body,footer)

def get_winner_card(winner_name,winner_score,all_scores,game_type):
    score_items=[]
    for i,(name,score)in enumerate(all_scores,1):
        rank=f"[{i}]"
        color=COSMIC["glow"]if i==1 else COSMIC["primary"]if i==2 else COSMIC["secondary"]if i==3 else COSMIC["text_muted"]
        score_items.append({"type":"box","layout":"horizontal","contents":[
            {"type":"box","layout":"vertical","contents":[
                {"type":"text","text":rank,"size":"xs","color":color,"weight":"bold"},
                {"type":"text","text":name,"size":"xs","color":color,"wrap":True}
            ],"flex":3},
            {"type":"text","text":f"{score} نقطة","size":"sm"if i==1 else"xs","color":color,"weight":"bold","align":"end","flex":2}
        ],"backgroundColor":COSMIC["elevated"]if i==1 else COSMIC["card"],"cornerRadius":"8px","paddingAll":"8px","margin":"xs"if i>1 else"none","borderColor":COSMIC["border"]if i==1 else"transparent","borderWidth":"1px"})
    
    body=[
        {"type":"box","layout":"vertical","contents":[
            {"type":"image","url":PISCES_LOGO,"size":"full","aspectRatio":"1:1","aspectMode":"cover"}
        ],"width":"120px","height":"120px","cornerRadius":"60px"},
        {"type":"text","text":"انتهت اللعبة","size":"md","weight":"bold","color":COSMIC["text_dim"],"align":"center","margin":"sm"},
        {"type":"text","text":game_type,"size":"xs","color":COSMIC["text_muted"],"align":"center","margin":"xs"},
        {"type":"separator","margin":"md","color":COSMIC["border"]},
        {"type":"box","layout":"vertical","contents":[
            {"type":"text","text":"الفائز","size":"xs","color":COSMIC["text_muted"],"align":"center"},
            {"type":"text","text":winner_name,"size":"lg","weight":"bold","color":COSMIC["glow"],"align":"center","margin":"xs","wrap":True},
            {"type":"text","text":f"{winner_score} نقطة","size":"sm","weight":"bold","color":COSMIC["primary"],"align":"center","margin":"xs"}
        ],"backgroundColor":COSMIC["elevated"],"cornerRadius":"10px","paddingAll":"10px","margin":"sm"},
        {"type":"separator","margin":"sm","color":COSMIC["border"]},
        {"type":"text","text":"النتائج","size":"xs","weight":"bold","color":COSMIC["text"],"margin":"sm"},
        {"type":"box","layout":"vertical","contents":score_items,"margin":"xs"},
        {"type":"separator","margin":"sm","color":COSMIC["border"]},
        {"type":"text","text":"بوت الحوت © 2025","size":"xxs","color":COSMIC["text_muted"],"align":"center","margin":"xs"}
    ]
    footer=[
        make_button("إعادة اللعبة",game_type,COSMIC["glow"]),
        make_button("الصدارة","الصدارة",COSMIC["secondary"])
    ]
    return create_card(body,footer)

def start_game(game_id,game_class,game_type,user_id,event):
    if not game_class:
        try:line_bot_api.reply_message(event.reply_token,TextSendMessage(text=f"لعبة {game_type} غير متوفرة",quick_reply=get_quick_reply()))
        except:pass
        return False
    try:
        with games_lock:
            if game_class.__name__ in['SongGame','HumanAnimalPlantGame','LettersWordsGame']:
                game=game_class(line_bot_api,use_ai=USE_AI,ask_ai=ask_gemini)
            else:
                game=game_class(line_bot_api)
            with players_lock:
                participants=registered_players.copy()
                participants.add(user_id)
            active_games[game_id]={'game':game,'type':game_type,'created_at':datetime.now(),'participants':participants,'answered_users':set(),'question_num':1,'scores':defaultdict(int)}
        response=game.start_game()
        question_text=""
        supports_hint=game_class.__name__ in['SongGame','OppositeGame']
        if isinstance(response,TextSendMessage):
            question_text=response.text
        elif isinstance(response,list):
            question_text=response[0].text if response else"ابدأ اللعبة"
        flex_card=get_game_question_card(game_type,1,question_text,supports_hint)
        line_bot_api.reply_message(event.reply_token,FlexSendMessage(alt_text=f"{game_type} - السؤال 1",contents=flex_card,quick_reply=get_quick_reply()))
        logger.info(f"Started {game_type}")
        return True
    except Exception as e:
        logger.error(f"Start {game_type} failed: {e}")
        log_error('start_game',e,{'game_type':game_type,'user_id':user_id[-4:]})
        return False

@app.route("/",methods=['GET'])
def home():
    games_count=sum(1 for g in games.values()if g)
    return f"""<!DOCTYPE html><html dir="rtl"><head><title>بوت الحوت</title><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:-apple-system,sans-serif;background:linear-gradient(135deg,{COSMIC['bg']},{COSMIC['card']});min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}.container{{background:{COSMIC['card']};border:2px solid {COSMIC['border']};border-radius:20px;box-shadow:0 0 60px rgba(0,212,255,0.4);padding:40px;max-width:600px;width:100%}}h1{{text-align:center;font-size:2.5em;margin-bottom:10px;background:linear-gradient(135deg,{COSMIC['primary']},{COSMIC['secondary']});-webkit-background-clip:text;-webkit-text-fill-color:transparent}}.subtitle{{text-align:center;color:{COSMIC['text_dim']};margin-bottom:30px}}.status{{background:{COSMIC['elevated']};border-radius:15px;padding:20px;margin:20px 0}}.status-item{{display:flex;justify-content:space-between;padding:12px 0;border-bottom:1px solid {COSMIC['border']}}}.status-item:last-child{{border-bottom:none}}.label{{color:{COSMIC['text_muted']}}}.value{{color:{COSMIC['primary']};font-weight:bold}}.btn{{display:inline-block;padding:12px 24px;background:{COSMIC['primary']};color:{COSMIC['dark']};text-decoration:none;border-radius:10px;margin:5px;font-weight:600}}.footer{{text-align:center;margin-top:30px;color:{COSMIC['text_muted']};font-size:0.9em}}</style></head><body><div class="container"><h1>بوت الحوت</h1><p class="subtitle">3D Gaming Experience</p><div class="status"><div class="status-item"><span class="label">الخادم</span><span class="value">يعمل</span></div><div class="status-item"><span class="label">Gemini AI</span><span class="value">{'مفعل'if USE_AI else'معطل'}</span></div><div class="status-item"><span class="label">اللاعبون</span><span class="value">{len(registered_players)}</span></div><div class="status-item"><span class="label">ألعاب نشطة</span><span class="value">{len(active_games)}</span></div><div class="status-item"><span class="label">ألعاب متوفرة</span><span class="value">{games_count}/8</span></div></div><div style="text-align:center;margin-top:25px"><a href="/health" class="btn">الصحة</a><a href="/errors" class="btn">الأخطاء({len(error_log)})</a></div><div class="footer">بوت الحوت © 2025</div></div></body></html>"""

@app.route("/health",methods=['GET'])
def health_check():
    return jsonify({"status":"healthy","timestamp":datetime.now().isoformat(),"active_games":len(active_games),"registered_players":len(registered_players),"ai_enabled":USE_AI,"errors":len(error_log)}),200

@app.route("/errors",methods=['GET'])
def view_errors():
    with error_log_lock:errors=list(reversed(error_log))
    html=f"""<!DOCTYPE html><html dir="rtl"><head><title>سجل الأخطاء</title><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{{font-family:-apple-system,sans-serif;background:{COSMIC['bg']};color:{COSMIC['text']};padding:20px}}.container{{max-width:1200px;margin:0 auto;background:{COSMIC['card']};border-radius:20px;padding:30px;border:2px solid {COSMIC['border']}}}h1{{color:{COSMIC['primary']};margin-bottom:20px}}.error-item{{background:{COSMIC['elevated']};border-left:4px solid {COSMIC['glow']};padding:15px;margin:15px 0;border-radius:8px}}.error-header{{display:flex;justify-content:space-between;margin-bottom:10px}}.error-type{{font-weight:bold;color:{COSMIC['glow']}}}.error-time{{color:{COSMIC['text_muted']};font-size:0.9em}}.error-message{{color:{COSMIC['text_dim']};margin:10px 0;font-family:monospace;font-size:0.9em}}.no-errors{{text-align:center;padding:40px;color:{COSMIC['glow']}}}.btn{{display:inline-block;margin-top:20px;padding:10px 20px;background:{COSMIC['primary']};color:{COSMIC['dark']};text-decoration:none;border-radius:8px}}</style></head><body><div class="container"><h1>سجل الأخطاء</h1>"""
    if not errors:html+='<div class="no-errors">لا توجد أخطاء</div>'
    else:
        for err in errors:html+=f"""<div class="error-item"><div class="error-header"><span class="error-type">{err.get('type','Unknown')}</span><span class="error-time">{err.get('timestamp','Unknown')}</span></div><div class="error-message">{err.get('message','No message')}</div></div>"""
    html+='<a href="/" class="btn">العودة</a></div></body></html>'
    return html

@app.route("/callback",methods=['POST'])
def callback():
    signature=request.headers.get('X-Line-Signature','')
    if not signature:abort(400)
    body=request.get_data(as_text=True)
    try:handler.handle(body,signature)
    except InvalidSignatureError:logger.error("Invalid signature");abort(400)
    except Exception as e:logger.error(f"Callback error: {e}");log_error('callback',e)
    return'OK',200

@handler.add(MessageEvent,message=TextMessage)
def handle_message(event):
    user_id,text=None,None
    try:
        user_id=event.source.user_id
        text=(event.message.text or"").strip()
        if not user_id or not text:return
        with players_lock:
            if user_id not in registered_players:registered_players.add(user_id)
        if not check_rate_limit(user_id):return
        display_name=get_user_profile_safe(user_id)
        game_id=getattr(event.source,'group_id',user_id)
        logger.info(f"Message from {display_name}: {text[:50]}")
        
        if text in['البداية','ابدأ','start','البوت']:
            line_bot_api.reply_message(event.reply_token,FlexSendMessage(alt_text=f"مرحباً {display_name}",contents=get_welcome_card(display_name),quick_reply=get_quick_reply()))
            return
        if text in['مساعدة','help']:
            line_bot_api.reply_message(event.reply_token,FlexSendMessage(alt_text="المساعدة",contents=get_help_card(),quick_reply=get_quick_reply()))
            return
        if text in['نقاطي','إحصائياتي','احصائياتي']:
            line_bot_api.reply_message(event.reply_token,FlexSendMessage(alt_text="إحصائياتك",contents=get_stats_card(user_id,display_name),quick_reply=get_quick_reply()))
            return
        if text in['الصدارة','المتصدرين']:
            line_bot_api.reply_message(event.reply_token,FlexSendMessage(alt_text="الصدارة",contents=get_leaderboard_card(),quick_reply=get_quick_reply()))
            return
        if text in['إيقاف','stop','ايقاف']:
            with games_lock:
                if game_id in active_games:
                    game_type=active_games[game_id]['type']
                    del active_games[game_id]
                    line_bot_api.reply_message(event.reply_token,TextSendMessage(text=f"تم إيقاف {game_type}",quick_reply=get_quick_reply()))
                else:line_bot_api.reply_message(event.reply_token,TextSendMessage(text="لا توجد لعبة نشطة",quick_reply=get_quick_reply()))
            return
        if text in['انضم','تسجيل','join']:
            with players_lock:
                if user_id in registered_players:line_bot_api.reply_message(event.reply_token,TextSendMessage(text=f"أنت مسجل بالفعل يا {display_name}",quick_reply=get_quick_reply()))
                else:registered_players.add(user_id);line_bot_api.reply_message(event.reply_token,TextSendMessage(text=f"مرحباً {display_name} تم التسجيل بنجاح",quick_reply=get_quick_reply()))
            return
        if text in['انسحب','خروج']:
            with players_lock:
                if user_id in registered_players:registered_players.remove(user_id);line_bot_api.reply_message(event.reply_token,TextSendMessage(text=f"تم الانسحاب يا {display_name}",quick_reply=get_quick_reply()))
                else:line_bot_api.reply_message(event.reply_token,TextSendMessage(text="أنت غير مسجل",quick_reply=get_quick_reply()))
            return
        
        if text in['سؤال','سوال']and QUESTIONS:line_bot_api.reply_message(event.reply_token,TextSendMessage(text=random.choice(QUESTIONS),quick_reply=get_quick_reply()));return
        if text in['تحدي','challenge']and CHALLENGES:line_bot_api.reply_message(event.reply_token,TextSendMessage(text=random.choice(CHALLENGES),quick_reply=get_quick_reply()));return
        if text in['اعتراف','confession']and CONFESSIONS:line_bot_api.reply_message(event.reply_token,TextSendMessage(text=random.choice(CONFESSIONS),quick_reply=get_quick_reply()));return
        if text in['منشن','mention']and MENTION_QUESTIONS:line_bot_api.reply_message(event.reply_token,TextSendMessage(text=random.choice(MENTION_QUESTIONS),quick_reply=get_quick_reply()));return
        
        games_map={'أغنية':(games['SongGame'],'أغنية'),'لعبة':(games['HumanAnimalPlantGame'],'لعبة'),'سلسلة':(games['ChainWordsGame'],'سلسلة'),'أسرع':(games['FastTypingGame'],'أسرع'),'ضد':(games['OppositeGame'],'ضد'),'تكوين':(games['LettersWordsGame'],'تكوين'),'توافق':(games['CompatibilityGame'],'توافق'),'ترتيب':(games['SpeedSortingGame'],'ترتيب')}
        
        if text=='ابدأ':
            available_games=[k for k,v in games_map.items()if v[0]and k!='توافق']
            if available_games:
                random_game=random.choice(available_games)
                game_class,game_type=games_map[random_game]
                if game_id in active_games:active_games[game_id]['last_game']=random_game
                start_game(game_id,game_class,game_type,user_id,event)
            return
        
        if text in games_map:
            game_class,game_type=games_map[text]
            if text=='توافق'and game_class:
                with games_lock:
                    with players_lock:
                        participants=registered_players.copy()
                        participants.add(user_id)
                    active_games[game_id]={'game':game_class(line_bot_api),'type':'توافق','created_at':datetime.now(),'participants':participants,'answered_users':set(),'last_game':text,'waiting_for_names':True}
                line_bot_api.reply_message(event.reply_token,TextSendMessage(text="لعبة التوافق\n\nاكتب اسمين مفصولين بمسافة\nنص فقط\n\nمثال: ميش عبير",quick_reply=get_quick_reply()))
                return
            if game_id in active_games:active_games[game_id]['last_game']=text
            start_game(game_id,game_class,game_type,user_id,event)
            return
        
        if game_id in active_games:
            game_data=active_games[game_id]
            if game_data.get('type')=='توافق'and game_data.get('waiting_for_names'):
                cleaned=text.replace('@','').strip()
                if'@'in text:line_bot_api.reply_message(event.reply_token,TextSendMessage(text="بدون علامة @",quick_reply=get_quick_reply()));return
                names=cleaned.split()
                if len(names)<2:line_bot_api.reply_message(event.reply_token,TextSendMessage(text="اكتب اسمين مفصولين بمسافة",quick_reply=get_quick_reply()));return
                try:
                    result=game_data['game'].check_answer(f"{names[0]} {names[1]}",user_id,display_name)
                    game_data['waiting_for_names']=False
                    with games_lock:
                        if game_id in active_games:del active_games[game_id]
                    if result and result.get('response'):
                        response=result['response']
                        if isinstance(response,TextSendMessage):response.quick_reply=get_quick_reply()
                        line_bot_api.reply_message(event.reply_token,response)
                    return
                except Exception as e:logger.error(f"Compatibility error: {e}");log_error('compatibility_game',e,{'user_id':user_id[-4:]});return
            
            game=game_data['game']
            game_type=game_data['type']
            supports_hint=game.__class__.__name__ in['SongGame','OppositeGame']
            
            if text in['لمح','تلميح','hint']:
                if supports_hint and hasattr(game,'get_hint'):
                    try:
                        hint=game.get_hint()
                        line_bot_api.reply_message(event.reply_token,TextSendMessage(text=hint,quick_reply=get_quick_reply()))
                    except:
                        line_bot_api.reply_message(event.reply_token,TextSendMessage(text="لا يوجد تلميح متاح",quick_reply=get_quick_reply()))
                else:
                    line_bot_api.reply_message(event.reply_token,TextSendMessage(text="هذه اللعبة لا تدعم لمح",quick_reply=get_quick_reply()))
                return
            
            if text in['جاوب','الجواب','answer']:
                if hasattr(game,'reveal_answer'):
                    try:
                        answer=game.reveal_answer()
                        question_num=game_data.get('question_num',1)
                        if question_num<QUESTIONS_PER_GAME:
                            game_data['question_num']=question_num+1
                            game_data['answered_users']=set()
                            next_q=game.next_question()
                            if next_q:
                                q_text=next_q.text if isinstance(next_q,TextSendMessage)else str(next_q)
                                flex_card=get_game_question_card(game_type,question_num+1,q_text,supports_hint)
                                line_bot_api.reply_message(event.reply_token,[
                                    TextSendMessage(text=f"الإجابة: {answer}"),
                                    FlexSendMessage(alt_text=f"{game_type} - السؤال {question_num+1}",contents=flex_card,quick_reply=get_quick_reply())
                                ])
                        else:
                            scores=game_data.get('scores',{})
                            if scores:
                                sorted_scores=sorted(scores.items(),key=lambda x:x[1],reverse=True)
                                winner_id,winner_score=sorted_scores[0]
                                winner_name=get_user_profile_safe(winner_id)
                                all_scores=[(get_user_profile_safe(uid),score)for uid,score in sorted_scores]
                                for uid,score in scores.items():
                                    update_user_points(uid,get_user_profile_safe(uid),score,uid==winner_id,game_type)
                                card=get_winner_card(winner_name,winner_score,all_scores,game_type)
                                with games_lock:
                                    if game_id in active_games:del active_games[game_id]
                                line_bot_api.reply_message(event.reply_token,[
                                    TextSendMessage(text=f"الإجابة: {answer}"),
                                    FlexSendMessage(alt_text="الفائز",contents=card,quick_reply=get_quick_reply())
                                ])
                            else:
                                with games_lock:
                                    if game_id in active_games:del active_games[game_id]
                                line_bot_api.reply_message(event.reply_token,TextSendMessage(text=f"الإجابة: {answer}\nانتهت اللعبة",quick_reply=get_quick_reply()))
                    except:
                        line_bot_api.reply_message(event.reply_token,TextSendMessage(text="لا يمكن عرض الإجابة",quick_reply=get_quick_reply()))
                else:
                    line_bot_api.reply_message(event.reply_token,TextSendMessage(text="هذه اللعبة لا تدعم عرض الإجابة",quick_reply=get_quick_reply()))
                return
            
            with players_lock:
                if user_id not in registered_players:return
            if user_id in game_data.get('answered_users',set()):return
            try:
                result=game.check_answer(text,user_id,display_name)
                if not result:return
                if result.get('correct'):
                    game_data.setdefault('answered_users',set()).add(user_id)
                    game_data.setdefault('scores',defaultdict(int))[user_id]+=result.get('points',0)
                points=result.get('points',0)
                question_num=game_data.get('question_num',1)
                if result.get('correct')and question_num<QUESTIONS_PER_GAME:
                    game_data['question_num']=question_num+1
                    game_data['answered_users']=set()
                    next_q=game.next_question()
                    if next_q:
                        q_text=next_q.text if isinstance(next_q,TextSendMessage)else str(next_q)
                        flex_card=get_game_question_card(game_type,question_num+1,q_text,supports_hint)
                        line_bot_api.reply_message(event.reply_token,[
                            TextSendMessage(text=f"صحيح! +{points} نقطة"),
                            FlexSendMessage(alt_text=f"{game_type} - السؤال {question_num+1}",contents=flex_card,quick_reply=get_quick_reply())
                        ])
                    return
                if result.get('correct')and question_num>=QUESTIONS_PER_GAME:
                    scores=game_data.get('scores',{})
                    if scores:
                        sorted_scores=sorted(scores.items(),key=lambda x:x[1],reverse=True)
                        winner_id,winner_score=sorted_scores[0]
                        winner_name=get_user_profile_safe(winner_id)
                        all_scores=[(get_user_profile_safe(uid),score)for uid,score in sorted_scores]
                        for uid,score in scores.items():
                            update_user_points(uid,get_user_profile_safe(uid),score,uid==winner_id,game_type)
                        card=get_winner_card(winner_name,winner_score,all_scores,game_type)
                        with games_lock:
                            if game_id in active_games:del active_games[game_id]
                        line_bot_api.reply_message(event.reply_token,[
                            TextSendMessage(text=f"صحيح! +{points} نقطة"),
                            FlexSendMessage(alt_text="الفائز",contents=card,quick_reply=get_quick_reply())
                        ])
                    else:
                        with games_lock:
                            if game_id in active_games:del active_games[game_id]
                        line_bot_api.reply_message(event.reply_token,TextSendMessage(text="انتهت اللعبة",quick_reply=get_quick_reply()))
                    return
                response=result.get('response',TextSendMessage(text=result.get('message','')))
                if isinstance(response,TextSendMessage):response.quick_reply=get_quick_reply()
                line_bot_api.reply_message(event.reply_token,response)
            except Exception as e:
                logger.error(f"Game answer error: {e}")
                log_error('game_answer',e,{'user_id':user_id[-4:],'game_type':game_type})
    except Exception as e:
        logger.error(f"Handler error: {e}")
        log_error('handle_message',e,{'user_id':user_id[-4:]if user_id else'Unknown','text':text[:100]if text else'Unknown'})
        try:
            if hasattr(event,'reply_token')and event.reply_token:line_bot_api.reply_message(event.reply_token,TextSendMessage(text="حدث خطأ مؤقت. حاول مرة أخرى",quick_reply=get_quick_reply()))
        except:pass

def cleanup_old_games():
    while True:
        try:
            time.sleep(300)
            now=datetime.now()
            to_delete=[]
            with games_lock:
                for gid,data in active_games.items():
                    if now-data.get('created_at',now)>timedelta(minutes=GAME_TIMEOUT_MINUTES):to_delete.append(gid)
                for gid in to_delete:del active_games[gid]
                if to_delete:logger.info(f"Cleaned {len(to_delete)} old game(s)")
            with names_cache_lock:
                if len(user_names_cache)>MAX_CACHE_SIZE:user_names_cache.clear();logger.info("Cleared names cache")
            with error_log_lock:
                if len(error_log)>MAX_ERROR_LOG_SIZE*2:error_log[:]=error_log[-MAX_ERROR_LOG_SIZE:];logger.info("Cleaned error log")
        except Exception as e:logger.error(f"Cleanup error: {e}");log_error('cleanup',e)

cleanup_thread=threading.Thread(target=cleanup_old_games,daemon=True)
cleanup_thread.start()

@app.errorhandler(400)
def bad_request(error):return'Bad Request',400
@app.errorhandler(404)
def not_found(error):return'Not Found',404
@app.errorhandler(500)
def internal_error(error):logger.error(f"Internal error: {error}");log_error('internal_error',error);return'Internal Server Error',500
@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f"Unexpected error: {error}")
    log_error('unexpected_error',error)
    if request.path=='/callback':return'OK',200
    return'Internal Server Error',500

if __name__=="__main__":
    port=int(os.environ.get('PORT',5000))
    logger.info("="*60)
    logger.info("بوت الحوت - 3D Gaming Experience")
    logger.info("="*60)
    logger.info(f"Port: {port}")
    logger.info(f"AI: {'Enabled'if USE_AI else'Disabled'}")
    logger.info(f"Players: {len(registered_players)}")
    logger.info(f"Active Games: {len(active_games)}")
    loaded=[name for name,cls in games.items()if cls]
    logger.info(f"Games Available ({len(loaded)}/8):")
    for name in loaded:logger.info(f"  - {name}")
    if len(loaded)<len(games):
        missing=[name for name,cls in games.items()if not cls]
        logger.warning(f"Games Unavailable ({len(missing)}):")
        for name in missing:logger.warning(f"  - {name}")
    logger.info("="*60)
    try:app.run(host='0.0.0.0',port=port,debug=False,threaded=True)
    except Exception as e:logger.error(f"Failed to start: {e}");log_error('app_start',e);sys.exit(1)
