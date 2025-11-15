from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction, FlexSendMessage
import os
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import time
import random
import logging
import sys

# Logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("game-bot")

# استيراد الإعدادات
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'config'))
from config.settings import LINE_TOKEN, LINE_SECRET, GEMINI_KEYS, GEMINI_MODEL, COLORS, RATE_LIMIT
from config.database import init_db, update_points, get_stats, get_leaderboard
from config.helpers import normalize_text, load_file

# Gemini AI
USE_AI = False
ask_gemini = None

try:
    import google.generativeai as genai
    if GEMINI_KEYS:
        genai.configure(api_key=GEMINI_KEYS[0])
        model = genai.GenerativeModel(GEMINI_MODEL)
        USE_AI = True
        logger.info(f"✅ Gemini AI - {len(GEMINI_KEYS)} مفاتيح")
        
        def ask_gemini(prompt, max_retries=2):
            for attempt in range(max_retries):
                try:
                    response = model.generate_content(prompt)
                    return response.text.strip()
                except Exception as e:
                    logger.error(f"Gemini خطأ: {e}")
                    if attempt < max_retries - 1 and len(GEMINI_KEYS) > 1:
                        genai.configure(api_key=GEMINI_KEYS[(attempt + 1) % len(GEMINI_KEYS)])
            return None
except Exception as e:
    logger.warning(f"⚠️ Gemini غير متوفر: {e}")

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
    logger.info("✅ تم استيراد جميع الألعاب")
except Exception as e:
    logger.error(f"❌ خطأ استيراد: {e}")

app = Flask(__name__)
line_bot_api = LineBotApi(LINE_TOKEN)
handler = WebhookHandler(LINE_SECRET)

# البيانات
active_games = {}
registered_players = set()
user_message_count = defaultdict(lambda: {'count': 0, 'reset_time': datetime.now()})
games_lock = threading.Lock()
players_lock = threading.Lock()

init_db()

# تحميل الملفات
QUESTIONS = load_file('questions.txt')
CHALLENGES = load_file('challenges.txt')
CONFESSIONS = load_file('confessions.txt')
MENTIONS = load_file('more_questions.txt')

def get_profile(user_id):
    try:
        return line_bot_api.get_profile(user_id).display_name
    except:
        return "مستخدم"

def check_rate(user_id):
    now = datetime.now()
    data = user_message_count[user_id]
    if now - data['reset_time'] > timedelta(seconds=RATE_LIMIT['window']):
        data['count'] = 0
        data['reset_time'] = now
    if data['count'] >= RATE_LIMIT['max']:
        return False
    data['count'] += 1
    return True

def get_quick_reply():
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="▪️سؤال", text="سؤال")),
        QuickReplyButton(action=MessageAction(label="▪️تحدي", text="تحدي")),
        QuickReplyButton(action=MessageAction(label="▪️اعتراف", text="اعتراف")),
        QuickReplyButton(action=MessageAction(label="▪️منشن", text="منشن")),
        QuickReplyButton(action=MessageAction(label="▫️أغنية", text="أغنية")),
        QuickReplyButton(action=MessageAction(label="▫️لعبة", text="لعبة")),
        QuickReplyButton(action=MessageAction(label="▫️سلسلة", text="سلسلة")),
        QuickReplyButton(action=MessageAction(label="▫️أسرع", text="أسرع")),
        QuickReplyButton(action=MessageAction(label="▫️ضد", text="ضد")),
        QuickReplyButton(action=MessageAction(label="▫️تكوين", text="تكوين")),
        QuickReplyButton(action=MessageAction(label="▫️اختلاف", text="اختلاف")),
        QuickReplyButton(action=MessageAction(label="▫️توافق", text="توافق"))
    ])

# بطاقات Flex
def get_card(title, body_content, footer_buttons=None):
    c = COLORS
    card = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "box", "layout": "vertical", "contents": [
                    {"type": "text", "text": title, "size": "xl", "weight": "bold", 
                     "color": c['white'], "align": "center"}
                ], "backgroundColor": c['primary'], "cornerRadius": "12px", "paddingAll": "24px"},
                {"type": "separator", "margin": "xl", "color": c['border']},
                *body_content
            ],
            "backgroundColor": c['white'],
            "paddingAll": "24px"
        }
    }
    
    if footer_buttons:
        card["footer"] = {
            "type": "box",
            "layout": "horizontal",
            "contents": footer_buttons,
            "spacing": "sm",
            "backgroundColor": c['light'],
            "paddingAll": "16px"
        }
    
    return card

def get_registration_card(name):
    return get_card("تم التسجيل بنجاح", [
        {"type": "text", "text": name, "size": "lg", "weight": "bold", 
         "color": COLORS['primary'], "align": "center", "margin": "xl"},
        {"type": "separator", "margin": "lg", "color": COLORS['border']},
        {"type": "text", "text": "يمكنك الآن اللعب وجمع النقاط", 
         "size": "sm", "color": COLORS['secondary'], "align": "center", 
         "margin": "lg", "wrap": True}
    ], [
        {"type": "button", "action": {"type": "message", "label": "ابدأ اللعب", "text": "أغنية"},
         "style": "primary", "color": COLORS['primary'], "height": "sm"}
    ])

def get_withdrawal_card(name):
    return get_card("تم الانسحاب", [
        {"type": "text", "text": name, "size": "lg", "weight": "bold", 
         "color": COLORS['secondary'], "align": "center", "margin": "xl"},
        {"type": "separator", "margin": "lg", "color": COLORS['border']},
        {"type": "text", "text": "نتمنى رؤيتك مرة أخرى", 
         "size": "sm", "color": COLORS['secondary'], "align": "center", "margin": "lg"}
    ])

def get_welcome_card(name):
    return get_card("مرحباً بك", [
        {"type": "text", "text": name, "size": "lg", "weight": "bold", 
         "color": COLORS['primary'], "align": "center", "margin": "xl"},
        {"type": "separator", "margin": "lg", "color": COLORS['border']},
        {"type": "text", "text": "استخدم الأزرار أدناه للعب", 
         "size": "sm", "color": COLORS['secondary'], "align": "center", 
         "margin": "lg", "wrap": True}
    ], [
        {"type": "button", "action": {"type": "message", "label": "انضم", "text": "انضم"},
         "style": "primary", "color": COLORS['primary'], "height": "sm"},
        {"type": "button", "action": {"type": "message", "label": "مساعدة", "text": "مساعدة"},
         "style": "secondary", "height": "sm"}
    ])

def get_stats_card(user_id, name):
    stats = get_stats(user_id)
    if not stats:
        return get_card("إحصائياتك", [
            {"type": "text", "text": "لم تبدأ بعد", "size": "md", 
             "color": COLORS['secondary'], "align": "center", "margin": "xl"}
        ], [
            {"type": "button", "action": {"type": "message", "label": "ابدأ الآن", "text": "انضم"},
             "style": "primary", "color": COLORS['primary']}
        ])
    
    win_rate = (stats['wins'] / stats['games_played'] * 100) if stats['games_played'] > 0 else 0
    
    return get_card("إحصائياتك", [
        {"type": "text", "text": name, "size": "md", "color": COLORS['secondary'], 
         "align": "center", "margin": "sm"},
        {"type": "separator", "margin": "xl", "color": COLORS['border']},
        {"type": "box", "layout": "vertical", "contents": [
            {"type": "box", "layout": "horizontal", "contents": [
                {"type": "text", "text": "النقاط", "size": "sm", "color": COLORS['secondary'], "flex": 1},
                {"type": "text", "text": str(stats['total_points']), "size": "xxl", 
                 "weight": "bold", "color": COLORS['primary'], "flex": 1, "align": "end"}
            ]},
            {"type": "separator", "margin": "lg", "color": COLORS['border']},
            {"type": "box", "layout": "horizontal", "contents": [
                {"type": "text", "text": "الألعاب", "size": "sm", "color": COLORS['secondary'], "flex": 1},
                {"type": "text", "text": str(stats['games_played']), "size": "md", 
                 "weight": "bold", "color": COLORS['primary'], "flex": 1, "align": "end"}
            ], "margin": "lg"},
            {"type": "box", "layout": "horizontal", "contents": [
                {"type": "text", "text": "الفوز", "size": "sm", "color": COLORS['secondary'], "flex": 1},
                {"type": "text", "text": str(stats['wins']), "size": "md", 
                 "weight": "bold", "color": COLORS['primary'], "flex": 1, "align": "end"}
            ], "margin": "md"},
            {"type": "box", "layout": "horizontal", "contents": [
                {"type": "text", "text": "معدل الفوز", "size": "sm", "color": COLORS['secondary'], "flex": 1},
                {"type": "text", "text": f"{win_rate:.0f}%", "size": "md", 
                 "weight": "bold", "color": COLORS['primary'], "flex": 1, "align": "end"}
            ], "margin": "md"}
        ], "backgroundColor": COLORS['light'], "cornerRadius": "10px", "paddingAll": "16px", "margin": "xl"}
    ], [
        {"type": "button", "action": {"type": "message", "label": "الصدارة", "text": "الصدارة"},
         "style": "secondary", "height": "sm"}
    ])

def get_leaderboard_card():
    leaders = get_leaderboard()
    if not leaders:
        return get_card("لوحة الصدارة", [
            {"type": "text", "text": "لا توجد بيانات", "size": "md", 
             "color": COLORS['secondary'], "align": "center", "margin": "xl"}
        ])
    
    items = []
    for i, l in enumerate(leaders, 1):
        bg = COLORS['primary'] if i == 1 else COLORS['secondary'] if i == 2 else COLORS['light']
        tc = COLORS['white'] if i <= 2 else COLORS['primary']
        
        items.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": str(i), "size": "sm", "color": tc, "flex": 0, "weight": "bold"},
                {"type": "text", "text": l['display_name'], "size": "sm", "color": tc, 
                 "flex": 3, "margin": "md", "wrap": True},
                {"type": "text", "text": str(l['total_points']), "size": "sm", "color": tc, 
                 "flex": 1, "align": "end", "weight": "bold"}
            ],
            "backgroundColor": bg,
            "cornerRadius": "8px",
            "paddingAll": "12px",
            "margin": "sm" if i > 1 else "md"
        })
    
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "لوحة الصدارة", "size": "xl", "weight": "bold", 
                 "color": COLORS['primary'], "align": "center"},
                {"type": "text", "text": "أفضل اللاعبين", "size": "sm", 
                 "color": COLORS['secondary'], "align": "center", "margin": "sm"},
                {"type": "separator", "margin": "xl", "color": COLORS['border']},
                {"type": "box", "layout": "vertical", "contents": items, "margin": "lg"}
            ],
            "backgroundColor": COLORS['white'],
            "paddingAll": "20px"
        }
    }

def get_winner_card(name, score, all_scores):
    score_items = []
    for i, (n, s) in enumerate(all_scores, 1):
        tc = COLORS['primary'] if i == 1 else COLORS['secondary']
        score_items.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": f"▪️ {i}", "size": "sm", "color": tc, "flex": 0, "weight": "bold"},
                {"type": "text", "text": n, "size": "sm", "color": COLORS['primary'], 
                 "flex": 3, "margin": "md", "wrap": True},
                {"type": "text", "text": f"{s} نقطة", "size": "sm", "color": tc, 
                 "flex": 2, "align": "end", "weight": "bold"}
            ],
            "paddingAll": "8px",
            "margin": "sm" if i > 1 else "none"
        })
    
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "box", "layout": "vertical", "contents": [
                    {"type": "text", "text": "انتهت اللعبة", "size": "xl", "weight": "bold", 
                     "color": COLORS['white'], "align": "center"}
                ], "backgroundColor": COLORS['primary'], "cornerRadius": "12px", "paddingAll": "24px"},
                {"type": "separator", "margin": "xl", "color": COLORS['border']},
                {"type": "box", "layout": "vertical", "contents": [
                    {"type": "text", "text": "الفائز", "size": "sm", 
                     "color": COLORS['secondary'], "align": "center"},
                    {"type": "text", "text": name, "size": "xxl", "weight": "bold", 
                     "color": COLORS['primary'], "align": "center", "margin": "sm", "wrap": True},
                    {"type": "text", "text": f"{score} نقطة", "size": "md", 
                     "color": COLORS['secondary'], "align": "center", "margin": "md"}
                ], "margin": "xl"},
                {"type": "separator", "margin": "xl", "color": COLORS['border']},
                {"type": "text", "text": "النتائج النهائية", "size": "md", "weight": "bold", 
                 "color": COLORS['primary'], "margin": "xl"},
                {"type": "box", "layout": "vertical", "contents": score_items, "margin": "md"}
            ],
            "backgroundColor": COLORS['white'],
            "paddingAll": "24px"
        },
        "footer": {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": "لعب مرة أخرى", "text": "أغنية"},
                 "style": "primary", "color": COLORS['primary'], "height": "sm"},
                {"type": "button", "action": {"type": "message", "label": "الصدارة", "text": "الصدارة"},
                 "style": "secondary", "height": "sm"}
            ],
            "spacing": "sm",
            "backgroundColor": COLORS['light'],
            "paddingAll": "16px"
        }
    }

def start_game(game_id, game_class, game_type, user_id, event):
    if not game_class:
        try:
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text=f"▫️ لعبة {game_type} غير متوفرة", quick_reply=get_quick_reply()))
        except:
            pass
        return False
    
    try:
        with games_lock:
            if game_class in [SongGame, HumanAnimalPlantGame, LettersWordsGame]:
                game = game_class(line_bot_api, use_ai=USE_AI, ask_ai=ask_gemini)
            else:
                game = game_class(line_bot_api)
            
            with players_lock:
                participants = registered_players.copy()
                participants.add(user_id)
            
            active_games[game_id] = {
                'game': game,
                'type': game_type,
                'created_at': datetime.now(),
                'participants': participants,
                'answered_users': set(),
                'last_game': game_type
            }
        
        response = game.start_game()
        if isinstance(response, TextSendMessage):
            response.quick_reply = get_quick_reply()
        elif isinstance(response, list):
            for r in response:
                if isinstance(r, TextSendMessage):
                    r.quick_reply = get_quick_reply()
        
        line_bot_api.reply_message(event.reply_token, response)
        logger.info(f"✅ بدأت {game_type}")
        return True
    except Exception as e:
        logger.error(f"❌ خطأ {game_type}: {e}")
        try:
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text="▫️ خطأ في بدء اللعبة", quick_reply=get_quick_reply()))
        except:
            pass
        return False

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
    
    return f"""<!DOCTYPE html>
<html><head><title>بوت الحُوت</title><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:-apple-system,sans-serif;background:linear-gradient(135deg,#2c2c2c 0%,#1a1a1a 100%);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}.container{{background:#fff;border-radius:16px;box-shadow:0 10px 40px rgba(0,0,0,.3);padding:40px;max-width:500px;width:100%}}h1{{color:#000;font-size:2em;margin-bottom:10px;text-align:center}}.status{{background:#F5F5F5;border-radius:10px;padding:20px;margin:20px 0}}.status-item{{display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #DDD}}.status-item:last-child{{border-bottom:none}}.label{{color:#666}}.value{{color:#000;font-weight:bold}}.games-list{{background:#FAFAFA;border-radius:8px;padding:12px;margin-top:10px;font-size:.85em;color:#666}}.footer{{text-align:center;margin-top:20px;color:#999;font-size:.8em}}</style>
</head><body><div class="container"><h1>بوت الحُوت</h1><div class="status">
<div class="status-item"><span class="label">الخادم</span><span class="value">▪️ يعمل</span></div>
<div class="status-item"><span class="label">Gemini AI</span><span class="value">{'✅ مفعّل' if USE_AI else '⚠️ معطّل'}</span></div>
<div class="status-item"><span class="label">اللاعبون</span><span class="value">▫️ {len(registered_players)}</span></div>
<div class="status-item"><span class="label">ألعاب نشطة</span><span class="value">▫️ {len(active_games)}</span></div>
<div class="status-item"><span class="label">الألعاب</span><span class="value">▪️ {len(games_status)}/8</span></div>
</div><div class="games-list"><strong>جاهز:</strong> {', '.join(games_status) if games_status else 'لا توجد'}</div>
<div class="footer">بوت الحُوت</div></div></body></html>"""

@app.route("/health", methods=['GET'])
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), 
            "games": len(active_games), "players": len(registered_players), "ai": USE_AI}, 200

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        user_id = event.source.user_id
        text = event.message.text.strip()
        
        if not check_rate(user_id):
            try:
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text="▪️ انتظر قليلاً", quick_reply=get_quick_reply()))
            except:
                pass
            return
        
        name = get_profile(user_id)
        game_id = event.source.group_id if hasattr(event.source, 'group_id') else user_id
        
        logger.info(f"📨 {name}: {text}")
        
        # الأوامر
        if text in ['البداية', 'ابدأ', 'start', 'البوت']:
            line_bot_api.reply_message(event.reply_token,
                FlexSendMessage(alt_text=f"مرحباً {name}",
                    contents=get_welcome_card(name), quick_reply=get_quick_reply()))
            return
        
        if text in ['مساعدة', 'help']:
            help_text = "▪️ دليل الاستخدام\n\n▫️ انضم - التسجيل\n▫️ انسحب - إلغاء التسجيل\n▫️ نقاطي - إحصائياتك\n▫️ الصدارة - أفضل اللاعبين\n▫️ إيقاف - إنهاء اللعبة\n\n▫️ لمح - تلميح\n▫️ جاوب - عرض الإجابة"
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text=help_text, quick_reply=get_quick_reply()))
            return
        
        if text in ['نقاطي', 'إحصائياتي', 'احصائياتي']:
            line_bot_api.reply_message(event.reply_token,
                FlexSendMessage(alt_text="إحصائياتك",
                    contents=get_stats_card(user_id, name), quick_reply=get_quick_reply()))
            return
        
        if text in ['الصدارة', 'المتصدرين']:
            line_bot_api.reply_message(event.reply_token,
                FlexSendMessage(alt_text="الصدارة",
                    contents=get_leaderboard_card(), quick_reply=get_quick_reply()))
            return
        
        if text in ['إيقاف', 'stop', 'ايقاف']:
            with games_lock:
                if game_id in active_games:
                    game_type = active_games[game_id]['type']
                    del active_games[game_id]
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text=f"▪️ تم إيقاف {game_type}", quick_reply=get_quick_reply()))
                else:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="▫️ لا توجد لعبة", quick_reply=get_quick_reply()))
            return
        
        if text in ['انضم', 'تسجيل', 'join']:
            with players_lock:
                if user_id in registered_players:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text=f"▪️ أنت مسجل يا {name}", quick_reply=get_quick_reply()))
                else:
                    registered_players.add(user_id)
                    line_bot_api.reply_message(event.reply_token,
                        FlexSendMessage(alt_text="تم التسجيل",
                            contents=get_registration_card(name), quick_reply=get_quick_reply()))
                    logger.info(f"✅ انضم: {name}")
            return
        
        if text in ['انسحب', 'خروج']:
            with players_lock:
                if user_id in registered_players:
                    registered_players.remove(user_id)
                    line_bot_api.reply_message(event.reply_token,
                        FlexSendMessage(alt_text="تم الانسحاب",
                            contents=get_withdrawal_card(name), quick_reply=get_quick_reply()))
                    logger.info(f"❌ انسحب: {name}")
                else:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="▫️ غير مسجل", quick_reply=get_quick_reply()))
            return
        
        # الأوامر النصية
        if text in ['سؤال', 'سوال'] and QUESTIONS:
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text=f"▪️ {random.choice(QUESTIONS)}", quick_reply=get_quick_reply()))
            return
        
        if text in ['تحدي', 'challenge'] and CHALLENGES:
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text=f"▪️ {random.choice(CHALLENGES)}", quick_reply=get_quick_reply()))
            return
        
        if text in ['اعتراف', 'confession'] and CONFESSIONS:
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text=f"▪️ {random.choice(CONFESSIONS)}", quick_reply=get_quick_reply()))
            return
        
        if text in ['منشن', 'mention'] and MENTIONS:
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text=f"▪️ {random.choice(MENTIONS)}", quick_reply=get_quick_reply()))
            return
        
        # بدء الألعاب
        games_map = {
            'أغنية': (SongGame, 'أغنية'),
            'لعبة': (HumanAnimalPlantGame, 'لعبة'),
            'سلسلة': (ChainWordsGame, 'سلسلة'),
            'أسرع': (FastTypingGame, 'أسرع'),
            'ضد': (OppositeGame, 'ضد'),
            'تكوين': (LettersWordsGame, 'تكوين'),
            'اختلاف': (DifferencesGame, 'اختلاف'),
            'توافق': (CompatibilityGame, 'توافق')
        }
        
        if text in games_map:
            game_class, game_type = games_map[text]
            
            if text == 'توافق':
                if not CompatibilityGame:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="▫️ غير متوفرة", quick_reply=get_quick_reply()))
                    return
                
                with games_lock:
                    with players_lock:
                        participants = registered_players.copy()
                        participants.add(user_id)
                    game = CompatibilityGame(line_bot_api)
                    active_games[game_id] = {
                        'game': game,
                        'type': 'توافق',
                        'created_at': datetime.now(),
                        'participants': participants,
                        'answered_users': set(),
                        'last_game': text
                    }
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text="▪️ لعبة التوافق\n\nاكتب اسمين مفصولين بمسافة\nمثال: أحمد فاطمة",
                        quick_reply=get_quick_reply()))
                return
            
            start_game(game_id, game_class, game_type, user_id, event)
            return
        
        # معالجة إجابات الألعاب
        if game_id in active_games:
            game_data = active_games[game_id]
            
            with players_lock:
                is_registered = user_id in registered_players
            
            if not is_registered:
                return
            
            if 'answered_users' in game_data and user_id in game_data['answered_users']:
                return
            
            game = game_data['game']
            game_type = game_data['type']
            
            try:
                result = game.check_answer(text, user_id, name)
                if result:
                    if result.get('correct', False):
                        if 'answered_users' not in game_data:
                            game_data['answered_users'] = set()
                        game_data['answered_users'].add(user_id)
                    
                    points = result.get('points', 0)
                    if points > 0:
                        update_points(user_id, name, points, result.get('won', False), game_type)
                    
                    if result.get('next_question', False):
                        game_data['answered_users'] = set()
                        next_q = game.next_question()
                        if next_q:
                            if isinstance(next_q, TextSendMessage):
                                next_q.quick_reply = get_quick_reply()
                            line_bot_api.reply_message(event.reply_token, next_q)
                        return
                    
                    if result.get('game_over', False):
                        with games_lock:
                            last_game = active_games[game_id].get('last_game', 'أغنية')
                            if game_id in active_games:
                                del active_games[game_id]
                        
                        if result.get('winner_card'):
                            card = result['winner_card']
                            if 'footer' in card and 'contents' in card['footer']:
                                for btn in card['footer']['contents']:
                                    if btn.get('type') == 'button' and 'لعب مرة أخرى' in btn.get('action', {}).get('label', ''):
                                        btn['action']['text'] = last_game
                            
                            line_bot_api.reply_message(event.reply_token,
                                FlexSendMessage(alt_text="الفائز", contents=card, quick_reply=get_quick_reply()))
                        else:
                            response = result.get('response', TextSendMessage(text=result.get('message', '')))
                            if isinstance(response, TextSendMessage):
                                response.quick_reply = get_quick_reply()
                            line_bot_api.reply_message(event.reply_token, response)
                        return
                    
                    response = result.get('response', TextSendMessage(text=result.get('message', '')))
                    if isinstance(response, TextSendMessage):
                        response.quick_reply = get_quick_reply()
                    elif isinstance(response, list):
                        for r in response:
                            if isinstance(r, TextSendMessage):
                                r.quick_reply = get_quick_reply()
                    line_bot_api.reply_message(event.reply_token, response)
                return
            except Exception as e:
                logger.error(f"❌ خطأ إجابة: {e}")
                return
    
    except Exception as e:
        logger.error(f"❌ خطأ معالجة: {e}")

def cleanup_old():
    while True:
        try:
            time.sleep(300)
            now = datetime.now()
            to_delete = []
            with games_lock:
                for gid, gdata in active_games.items():
                    if now - gdata.get('created_at', now) > timedelta(minutes=15):
                        to_delete.append(gid)
                for gid in to_delete:
                    del active_games[gid]
                if to_delete:
                    logger.info(f"🗑️ حذف {len(to_delete)} لعبة قديمة")
        except Exception as e:
            logger.error(f"❌ خطأ تنظيف: {e}")

threading.Thread(target=cleanup_old, daemon=True).start()

@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f"❌ خطأ: {error}", exc_info=True)
    return 'Internal Server Error', 500

@app.errorhandler(404)
def not_found(error):
    return 'Not Found', 404

@app.errorhandler(400)
def bad_request(error):
    return 'Bad Request', 400

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    logger.info("="*50)
    logger.info("🚀 بوت الحُوت")
    logger.info(f"🔌 المنفذ: {port}")
    logger.info(f"🤖 Gemini: {'✅' if USE_AI else '⚠️'}")
    logger.info(f"📊 اللاعبون: {len(registered_players)}")
    logger.info(f"🎮 الألعاب: {len(active_games)}")
    logger.info("="*50)
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
