# app.py
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
import os
import sqlite3
import logging
from datetime import datetime, timedelta
import random
import time
from collections import defaultdict

from config import *
try:
    from games import GameManager
    game_manager = GameManager()
    GAMES_LOADED = True
except ImportError as e:
    GAMES_LOADED = False
    game_manager = None

app = Flask(__name__)
logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)
logger = logging.getLogger(__name__)

line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

active_games = {}
rate_limiter = defaultdict(list)

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.executescript(DB_SCHEMA)
    conn.commit()
    conn.close()

def register_user(user_id, name):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO players (user_id, name, last_active) VALUES (?, ?, CURRENT_TIMESTAMP)', (user_id, name))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def update_user_name(user_id, name):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('UPDATE players SET name = ?, last_active = CURRENT_TIMESTAMP WHERE user_id = ?', (name, user_id))
        conn.commit()
        conn.close()
    except:
        pass

def is_registered(user_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM players WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except:
        return False

def update_points(user_id, points):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('UPDATE players SET points = points + ?, last_active = CURRENT_TIMESTAMP WHERE user_id = ?', (points, user_id))
        conn.commit()
        conn.close()
    except:
        pass

def update_game_stats(user_id, won=False):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        if won:
            cursor.execute('UPDATE players SET games_played = games_played + 1, games_won = games_won + 1, last_active = CURRENT_TIMESTAMP WHERE user_id = ?', (user_id,))
        else:
            cursor.execute('UPDATE players SET games_played = games_played + 1, last_active = CURRENT_TIMESTAMP WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
    except:
        pass

def get_user_stats(user_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT name, points, games_played, games_won FROM players WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return {'name': result[0], 'points': result[1], 'games_played': result[2], 'games_won': result[3]}
        return None
    except:
        return None

def get_leaderboard(limit=10):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT name, points, games_won FROM players ORDER BY points DESC, games_won DESC LIMIT ?', (limit,))
        results = cursor.fetchall()
        conn.close()
        return results
    except:
        return []

def cleanup_inactive_users():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cutoff = datetime.now() - timedelta(days=GAME_SETTINGS.get('inactive_days', 90))
        cursor.execute('DELETE FROM players WHERE last_active < ?', (cutoff,))
        conn.commit()
        conn.close()
    except:
        pass

def check_rate_limit(user_id):
    now = time.time()
    user_requests = rate_limiter[user_id]
    user_requests[:] = [t for t in user_requests if now - t < RATE_LIMIT['window']]
    if len(user_requests) >= RATE_LIMIT['max_requests']:
        return False
    user_requests.append(now)
    return True

def create_welcome_card():
    return {"type":"bubble","size":"mega","body":{"type":"box","layout":"vertical","backgroundColor":C['bg'],"paddingAll":"0px","contents":[{"type":"box","layout":"vertical","backgroundColor":C['topbg'],"paddingTop":"40px","paddingBottom":"150px","contents":[{"type":"box","layout":"vertical","cornerRadius":"25px","backgroundColor":C['bg'],"paddingAll":"25px","offsetTop":"70px","contents":[{"type":"image","url":LOGO_URL,"size":"120px","align":"center"},{"type":"text","text":"بوت الحوت","weight":"bold","size":"26px","align":"center","margin":"15px","color":C['cyan']},{"type":"separator","color":C['sep'],"margin":"10px"},{"type":"text","text":"الألعاب المتوفرة","align":"center","size":"18px","weight":"bold","color":C['text'],"margin":"15px"},{"type":"box","layout":"vertical","cornerRadius":"15px","backgroundColor":C['card'],"paddingAll":"20px","contents":[{"type":"text","text":"1. أسرع - أول من يكتب الإجابة الصحيحة","size":"15px","color":C['text'],"wrap":True},{"type":"text","text":"2. لعبة - إنسان، حيوان، نبات، بلد","size":"15px","color":C['text'],"wrap":True,"margin":"10px"},{"type":"text","text":"3. سلسلة - سلسلة الكلمات المترابطة","size":"15px","color":C['text'],"wrap":True,"margin":"10px"},{"type":"text","text":"4. أغنية - خمن المغني من كلمات الأغنية","size":"15px","color":C['text'],"wrap":True,"margin":"10px"},{"type":"text","text":"5. ضد - اعكس الكلمة المعطاة","size":"15px","color":C['text'],"wrap":True,"margin":"10px"},{"type":"text","text":"6. ترتيب - رتب العناصر حسب المطلوب","size":"15px","color":C['text'],"wrap":True,"margin":"10px"},{"type":"text","text":"7. تكوين - كوّن 3 كلمات من الحروف","size":"15px","color":C['text'],"wrap":True,"margin":"10px"},{"type":"text","text":"8. توافق - احسب نسبة التوافق","size":"15px","color":C['text'],"wrap":True,"margin":"10px"},{"type":"text","text":"9. Ai - محادثة ذكية مع الذكاء الاصطناعي","size":"15px","color":C['text'],"wrap":True,"margin":"10px"}]},{"type":"text","text":"محتوى ترفيهي\nسؤال • منشن • اعتراف • تحدي","align":"center","size":"16px","color":C['text2'],"margin":"25px","wrap":True},{"type":"box","layout":"vertical","spacing":"12px","contents":[{"type":"button","style":"primary","height":"md","color":C['cyan'],"action":{"type":"message","label":"ابدأ لعبة عشوائية","text":"ابدأ"}},{"type":"button","style":"secondary","color":"#F1F1F1","action":{"type":"message","label":"المساعدة","text":"مساعدة"}},{"type":"button","style":"secondary","color":"#F1F1F1","action":{"type":"message","label":"إحصائياتي","text":"نقاطي"}},{"type":"button","style":"secondary","color":"#F1F1F1","action":{"type":"message","label":"الصدارة","text":"الصدارة"}}]}]}]}]}}

def create_help_card():
    return {"type":"bubble","size":"mega","body":{"type":"box","layout":"vertical","backgroundColor":C['bg'],"paddingAll":"0px","contents":[{"type":"box","layout":"vertical","backgroundColor":C['topbg'],"paddingTop":"40px","paddingBottom":"150px","contents":[{"type":"box","layout":"vertical","cornerRadius":"25px","backgroundColor":C['bg'],"paddingAll":"25px","offsetTop":"70px","contents":[{"type":"text","text":"المساعدة","weight":"bold","size":"26px","align":"center","margin":"5px","color":C['cyan']},{"type":"text","text":"الأوامر المتاحة","align":"center","size":"17px","color":C['text'],"margin":"10px"},{"type":"separator","color":C['sep'],"margin":"15px"},{"type":"box","layout":"vertical","cornerRadius":"15px","backgroundColor":C['card'],"paddingAll":"18px","contents":[{"type":"text","text":"أوامر اللعب:","weight":"bold","size":"16px","color":C['cyan'],"margin":"none"},{"type":"text","text":"• ابدأ → بدء لعبة عشوائية","size":"15px","color":C['text'],"wrap":True,"margin":"md"},{"type":"text","text":"• لمح → الحصول على تلميح","size":"15px","color":C['text'],"wrap":True,"margin":"sm"},{"type":"text","text":"• جاوب → إظهار الإجابة الصحيحة","size":"15px","color":C['text'],"wrap":True,"margin":"sm"},{"type":"text","text":"• إيقاف → إنهاء اللعبة الحالية","size":"15px","color":C['text'],"wrap":True,"margin":"sm"},{"type":"separator","color":C['sep'],"margin":"md"},{"type":"text","text":"أوامر الإحصائيات:","weight":"bold","size":"16px","color":C['cyan'],"margin":"md"},{"type":"text","text":"• نقاطي → عرض نقاطك وإحصائياتك","size":"15px","color":C['text'],"wrap":True,"margin":"md"},{"type":"text","text":"• الصدارة → لوحة أفضل اللاعبين","size":"15px","color":C['text'],"wrap":True,"margin":"sm"}]},{"type":"box","layout":"horizontal","spacing":"10px","margin":"20px","contents":[{"type":"button","style":"primary","height":"sm","color":C['cyan'],"action":{"type":"message","label":"ابدأ","text":"ابدأ"}},{"type":"button","style":"secondary","height":"sm","color":"#F1F1F1","action":{"type":"message","label":"الصدارة","text":"الصدارة"}}]},{"type":"text","text":"© بوت الحوت 2025","align":"center","size":"13px","color":C['text2'],"margin":"10px"}]}]}]}}

def create_stats_card(stats):
    win_rate = (stats['games_won'] / stats['games_played'] * 100) if stats['games_played'] > 0 else 0
    return {"type":"bubble","size":"mega","body":{"type":"box","layout":"vertical","backgroundColor":C['bg'],"paddingAll":"20px","contents":[{"type":"text","text":"إحصائياتك","weight":"bold","size":"xl","color":C['cyan'],"align":"center"},{"type":"separator","color":C['sep'],"margin":"15px"},{"type":"box","layout":"vertical","backgroundColor":C['card'],"cornerRadius":"15px","paddingAll":"20px","margin":"md","contents":[{"type":"text","text":f"{stats['name']}","size":"lg","color":C['text'],"wrap":True,"weight":"bold"},{"type":"separator","color":C['sep'],"margin":"md"},{"type":"text","text":f"النقاط: {stats['points']}","size":"md","color":C['text'],"margin":"md"},{"type":"text","text":f"الألعاب المُلعَبة: {stats['games_played']}","size":"md","color":C['text'],"margin":"sm"},{"type":"text","text":f"الانتصارات: {stats['games_won']}","size":"md","color":C['text'],"margin":"sm"},{"type":"text","text":f"نسبة الفوز: {win_rate:.1f}%","size":"md","color":C['cyan'],"margin":"sm"}]},{"type":"box","layout":"horizontal","spacing":"10px","margin":"lg","contents":[{"type":"button","style":"primary","color":C['cyan'],"action":{"type":"message","label":"ابدأ لعبة","text":"ابدأ"}},{"type":"button","style":"secondary","color":"#F1F1F1","action":{"type":"message","label":"الصدارة","text":"الصدارة"}}]}]}}

def create_leaderboard_card(leaderboard):
    contents = [{"type":"text","text":"لوحة الصدارة","weight":"bold","size":"xl","color":C['cyan'],"align":"center"},{"type":"separator","color":C['sep'],"margin":"15px"}]
    for i, (name, points, wins) in enumerate(leaderboard[:10], 1):
        emoji = RANK_EMOJIS.get(i, f"{i}.")
        contents.append({"type":"box","layout":"horizontal","backgroundColor":C['card'],"cornerRadius":"10px","paddingAll":"12px","margin":"sm","contents":[{"type":"text","text":f"{emoji} {name}","size":"md","color":C['text'],"flex":3,"wrap":True},{"type":"text","text":f"{points}","size":"sm","color":C['text2'],"align":"end","flex":2}]})
    return {"type":"bubble","size":"mega","body":{"type":"box","layout":"vertical","backgroundColor":C['bg'],"paddingAll":"20px","contents":contents}}

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()
    group_id = getattr(event.source, 'group_id', user_id)
    
    if not check_rate_limit(user_id):
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MESSAGES['rate_limited']))
        return
    
    try:
        profile = line_bot_api.get_profile(user_id)
        user_name = profile.display_name
    except:
        user_name = "مستخدم"
    
    if not is_registered(user_id):
        register_user(user_id, user_name)
    else:
        update_user_name(user_id, user_name)
    
    text_lower = text.lower()
    
    if any(cmd in text_lower for cmd in CMDS['start'] + ['بوت', 'whale', 'مرحبا', 'السلام', 'هاي']):
        flex = FlexSendMessage(alt_text="بوت الحوت", contents=create_welcome_card())
        line_bot_api.reply_message(event.reply_token, flex)
        return
    
    if any(cmd in text_lower for cmd in CMDS['help']):
        flex = FlexSendMessage(alt_text="المساعدة", contents=create_help_card())
        line_bot_api.reply_message(event.reply_token, flex)
        return
    
    if any(cmd in text_lower for cmd in CMDS['stats']):
        stats = get_user_stats(user_id)
        if stats:
            flex = FlexSendMessage(alt_text="إحصائياتك", contents=create_stats_card(stats))
            line_bot_api.reply_message(event.reply_token, flex)
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="لم يتم العثور على إحصائيات"))
        return
    
    if any(cmd in text_lower for cmd in CMDS['leaderboard']):
        leaderboard = get_leaderboard()
        if leaderboard:
            flex = FlexSendMessage(alt_text="لوحة الصدارة", contents=create_leaderboard_card(leaderboard))
            line_bot_api.reply_message(event.reply_token, flex)
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="لا توجد بيانات للصدارة"))
        return
    
    if text in ['ابدأ', 'start', 'بدء', 'العب']:
        if group_id in active_games:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MESSAGES['already_playing']))
            return
        if not GAMES_LOADED or not game_manager:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="الألعاب غير متوفرة حالياً"))
            return
        try:
            result = game_manager.start_random_game(group_id, user_id, user_name)
            if result and result.get('success'):
                active_games[group_id] = result.get('game_data', {})
                if result.get('flex'):
                    flex = FlexSendMessage(alt_text=result.get('message', 'لعبة جديدة'), contents=result['flex'])
                    line_bot_api.reply_message(event.reply_token, flex)
                else:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result.get('message', 'بدأت اللعبة!')))
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="حدث خطأ في بدء اللعبة"))
        except:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="حدث خطأ في بدء اللعبة"))
        return
    
    if any(cmd in text_lower for cmd in CMDS['stop']):
        if group_id in active_games:
            del active_games[group_id]
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MESSAGES['game_stopped']))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MESSAGES['no_active_game']))
        return
    
    if any(cmd in text_lower for cmd in CMDS['hint']):
        if group_id not in active_games:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MESSAGES['no_active_game']))
            return
        if not GAMES_LOADED or not game_manager:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="الألعاب غير متوفرة"))
            return
        try:
            game = active_games[group_id]
            hint_text = game_manager.get_hint(game)
            if hint_text:
                update_points(user_id, POINTS['hint'])
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=hint_text))
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="التلميح غير متوفر لهذه اللعبة"))
        except:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="حدث خطأ في الحصول على التلميح"))
        return
    
    if any(cmd in text_lower for cmd in CMDS['answer']):
        if group_id not in active_games:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=MESSAGES['no_active_game']))
            return
        if not GAMES_LOADED or not game_manager:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="الألعاب غير متوفرة"))
            return
        try:
            game = active_games[group_id]
            answer_result = game_manager.show_answer(game, group_id, active_games)
            if answer_result:
                if answer_result.get('flex'):
                    flex = FlexSendMessage(alt_text=answer_result.get('message', 'الإجابة'), contents=answer_result['flex'])
                    line_bot_api.reply_message(event.reply_token, flex)
                else:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=answer_result.get('message', 'تم عرض الإجابة')))
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="حدث خطأ في عرض الإجابة"))
        except:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="حدث خطأ في عرض الإجابة"))
        return
    
    if group_id in active_games and GAMES_LOADED and game_manager:
        try:
            game = active_games[group_id]
            result = game_manager.check_answer(game, text, user_id, user_name, group_id, active_games)
            if result:
                if result.get('correct'):
                    points = result.get('points', POINTS['correct'])
                    update_points(user_id, points)
                    update_game_stats(user_id, won=True)
                if result.get('flex'):
                    flex = FlexSendMessage(alt_text=result.get('message', 'نتيجة'), contents=result['flex'])
                    line_bot_api.reply_message(event.reply_token, flex)
                elif result.get('message'):
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result['message']))
        except:
            pass

@app.route("/")
def index():
    games_status = "متوفرة" if GAMES_LOADED else "غير متوفرة"
    games_count = len(GAMES_LIST) if GAMES_LOADED else 0
    return f"""<!DOCTYPE html><html dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>بوت الحوت</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:linear-gradient(135deg,#0A0E27 0%,#1a1f3a 100%);color:#E0F2FF;min-height:100vh;display:flex;justify-content:center;align-items:center;padding:20px}}.container{{max-width:600px;width:100%}}.glass-card{{background:rgba(15,36,64,0.8);backdrop-filter:blur(10px);border:1px solid rgba(0,217,255,0.3);border-radius:25px;padding:40px;box-shadow:0 8px 32px rgba(0,217,255,0.2)}}.logo{{width:120px;height:120px;margin:0 auto 20px;display:block;border-radius:50%;border:3px solid #00D9FF;box-shadow:0 0 30px rgba(0,217,255,0.5)}}h1{{text-align:center;color:#00D9FF;font-size:2em;margin-bottom:10px;text-shadow:0 0 20px rgba(0,217,255,0.5)}}.subtitle{{text-align:center;color:#7FB3D5;margin-bottom:30px}}.status-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:15px;margin-top:20px}}.stat-box{{background:rgba(0,217,255,0.1);border:1px solid rgba(0,217,255,0.3);border-radius:15px;padding:20px;text-align:center}}.stat-value{{font-size:2em;font-weight:bold;color:#00D9FF;display:block;margin-bottom:5px}}.stat-label{{color:#7FB3D5;font-size:0.9em}}.footer{{text-align:center;margin-top:30px;color:#7FB3D5;font-size:0.9em}}@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:0.5}}}}.online-indicator{{display:inline-block;width:10px;height:10px;background:#00FF00;border-radius:50%;margin-left:5px;animation:pulse 2s infinite}}.status-badge{{display:inline-block;padding:5px 15px;border-radius:20px;font-size:0.9em;margin:10px 0}}.status-active{{background:rgba(0,255,0,0.2);color:#00FF00;border:1px solid #00FF00}}.status-inactive{{background:rgba(255,0,0,0.2);color:#FF0000;border:1px solid #FF0000}}</style></head><body><div class="container"><div class="glass-card"><img src="{LOGO_URL}" alt="بوت الحوت" class="logo"><h1>بوت الحوت</h1><p class="subtitle"><span class="online-indicator"></span>البوت يعمل بنجاح</p><div style="text-align:center;"><span class="status-badge {'status-active' if GAMES_LOADED else 'status-inactive'}">الألعاب: {games_status}</span></div><div class="status-grid"><div class="stat-box"><span class="stat-value">{games_count}</span><span class="stat-label">ألعاب متوفرة</span></div><div class="stat-box"><span class="stat-value">{'✓' if GAMES_LOADED else '✗'}</span><span class="stat-label">حالة الألعاب</span></div><div class="stat-box"><span class="stat-value">24/7</span><span class="stat-label">متاح دائماً</span></div><div class="stat-box"><span class="stat-value">∞</span><span class="stat-label">متعة لا تنتهي</span></div></div><div class="footer"><p>© بوت الحوت 2025</p><p style="margin-top:10px;font-size:0.8em;">Active Games: {len(active_games)}</p></div></div></div></body></html>"""

@app.route("/health")
def health():
    return {"status":"healthy","games_loaded":GAMES_LOADED,"active_games":len(active_games),"timestamp":datetime.now().isoformat()}

if __name__ == "__main__":
    init_db()
    cleanup_inactive_users()
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
