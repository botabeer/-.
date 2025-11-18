# ============================================
# app.py - الملف الرئيسي
# ============================================
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os, sqlite3, time, random, requests, json
from games import *

app = Flask(__name__)
line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))

# قاعدة البيانات
def init_db():
    conn = sqlite3.connect('whale_bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS players (user_id TEXT PRIMARY KEY, name TEXT, points INTEGER DEFAULT 0, 
                 games_played INTEGER DEFAULT 0, wins INTEGER DEFAULT 0, last_active REAL)''')
    conn.commit()
    conn.close()

def get_player(user_id):
    conn = sqlite3.connect('whale_bot.db')
    c = conn.cursor()
    c.execute('SELECT * FROM players WHERE user_id=?', (user_id,))
    player = c.fetchone()
    conn.close()
    return player

def update_player(user_id, name, points_delta=0):
    conn = sqlite3.connect('whale_bot.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO players (user_id, name, points, last_active) VALUES (?,?,0,?)', 
              (user_id, name, time.time()))
    c.execute('UPDATE players SET name=?, points=points+?, last_active=? WHERE user_id=?', 
              (name, points_delta, time.time(), user_id))
    conn.commit()
    conn.close()

# الألعاب النشطة
active_games = {}

# الألوان
C = {'bg':'#0A0E27', 'card':'#0F2440', 'text':'#E0F2FF', 'text2':'#7FB3D5', 'cyan':'#00D9FF', 
     'glow':'#5EEBFF', 'sep':'#2C5F8D', 'border':'#00D9FF40', 'gradient':'#88AEE0'}

# بطاقة الترحيب
def welcome_card():
    return FlexSendMessage(alt_text="بوت الحوت", contents={
        "type":"bubble", "size":"mega", "body":{
            "type":"box", "layout":"vertical", "backgroundColor":C['bg'], "paddingAll":"0px", "contents":[
                {"type":"box", "layout":"vertical", "backgroundColor":C['gradient'], "paddingTop":"40px", 
                 "paddingBottom":"150px", "contents":[
                    {"type":"box", "layout":"vertical", "cornerRadius":"25px", "backgroundColor":C['bg'], 
                     "paddingAll":"25px", "offsetTop":"70px", "contents":[
                        {"type":"image", "url":"https://i.imgur.com/qcWILGi.jpeg", "size":"120px", "align":"center"},
                        {"type":"text", "text":"بوت الحوت", "weight":"bold", "size":"26px", "align":"center", 
                         "margin":"15px", "color":C['cyan']},
                        {"type":"separator", "color":C['sep'], "margin":"10px"},
                        {"type":"text", "text":"الألعاب المتوفرة", "align":"center", "size":"18px", 
                         "weight":"bold", "color":C['text'], "margin":"15px"},
                        {"type":"box", "layout":"vertical", "cornerRadius":"15px", "backgroundColor":C['card'], 
                         "paddingAll":"20px", "contents":[
                            {"type":"text", "text":"1. أسرع ▫️\n2. لعبة ▫️\n3. سلسلة الكلمات ▫️\n4. أغنية ▫️\n5. ضد ▫️\n6. ترتيب ▫️\n7. تكوين كلمات ▫️\n8. توافق ▫️\n9. Ai ▫️", 
                             "size":"15px", "color":C['text'], "wrap":True}
                        ]},
                        {"type":"text", "text":"محتوى ترفيهي\nسؤال • منشن • اعتراف • تحدي", "align":"center", 
                         "size":"16px", "color":C['text2'], "margin":"25px", "wrap":True},
                        {"type":"box", "layout":"vertical", "spacing":"12px", "contents":[
                            {"type":"button", "style":"primary", "height":"md", "color":C['cyan'], 
                             "action":{"type":"message", "label":"ابدأ", "text":"ابدأ"}},
                            {"type":"button", "style":"secondary", "color":"#F1F1F1", 
                             "action":{"type":"message", "label":"المساعدة", "text":"مساعدة"}},
                            {"type":"button", "style":"secondary", "color":"#F1F1F1", 
                             "action":{"type":"message", "label":"الصدارة", "text":"الصدارة"}}
                        ]}
                    ]}
                ]}
            ]
        }
    })

# بطاقة المساعدة
def help_card():
    return FlexSendMessage(alt_text="المساعدة", contents={
        "type":"bubble", "size":"mega", "body":{
            "type":"box", "layout":"vertical", "backgroundColor":C['bg'], "paddingAll":"0px", "contents":[
                {"type":"box", "layout":"vertical", "backgroundColor":C['gradient'], "paddingTop":"40px", 
                 "paddingBottom":"150px", "contents":[
                    {"type":"box", "layout":"vertical", "cornerRadius":"25px", "backgroundColor":C['bg'], 
                     "paddingAll":"25px", "offsetTop":"70px", "contents":[
                        {"type":"text", "text":"المساعدة", "weight":"bold", "size":"26px", "align":"center", 
                         "margin":"5px", "color":C['cyan']},
                        {"type":"text", "text":"الأوامر المتاحة", "align":"center", "size":"17px", 
                         "color":C['text'], "margin":"10px"},
                        {"type":"separator", "color":C['sep'], "margin":"15px"},
                        {"type":"box", "layout":"vertical", "cornerRadius":"15px", "backgroundColor":C['card'], 
                         "paddingAll":"18px", "contents":[
                            {"type":"text", "text":"• لمح → تلميح ذكي\n• جاوب → الإجابة والانتقال\n• إعادة → إعادة اللعبة\n• إيقاف → إنهاء اللعبة\n• انضم → التسجيل\n• انسحب → الإلغاء\n• نقاطي → عرض النقاط\n• الصدارة → أفضل اللاعبين", 
                             "size":"15px", "color":C['text'], "wrap":True}
                        ]},
                        {"type":"box", "layout":"horizontal", "spacing":"10px", "margin":"20px", "contents":[
                            {"type":"button", "style":"secondary", "height":"sm", "color":"#F1F1F1", 
                             "action":{"type":"message", "label":"نقاطي", "text":"نقاطي"}},
                            {"type":"button", "style":"secondary", "height":"sm", "color":"#F1F1F1", 
                             "action":{"type":"message", "label":"الصدارة", "text":"الصدارة"}}
                        ]},
                        {"type":"text", "text":"© بوت الحوت 2025", "align":"center", "size":"13px", 
                         "color":C['text2'], "margin":"10px"}
                    ]}
                ]}
            ]
        }
    })

# بطاقة الصدارة
def leaderboard_card():
    conn = sqlite3.connect('whale_bot.db')
    c = conn.cursor()
    c.execute('SELECT name, points FROM players ORDER BY points DESC LIMIT 10')
    players = c.fetchall()
    conn.close()
    
    medals = ['🥇', '🥈', '🥉']
    content = []
    for idx, (name, points) in enumerate(players):
        medal = medals[idx] if idx < 3 else f"{idx+1}."
        content.append({"type":"text", "text":f"{medal} {name}: {points} نقطة", 
                       "size":"15px", "color":C['text'], "wrap":True, "margin":"5px" if idx > 0 else "0px"})
    
    return FlexSendMessage(alt_text="الصدارة", contents={
        "type":"bubble", "size":"mega", "body":{
            "type":"box", "layout":"vertical", "backgroundColor":C['bg'], "paddingAll":"0px", "contents":[
                {"type":"box", "layout":"vertical", "backgroundColor":C['gradient'], "paddingTop":"40px", 
                 "paddingBottom":"150px", "contents":[
                    {"type":"box", "layout":"vertical", "cornerRadius":"25px", "backgroundColor":C['bg'], 
                     "paddingAll":"25px", "offsetTop":"70px", "contents":[
                        {"type":"text", "text":"🏆 لوحة الصدارة", "weight":"bold", "size":"26px", 
                         "align":"center", "color":C['cyan']},
                        {"type":"separator", "color":C['sep'], "margin":"15px"},
                        {"type":"box", "layout":"vertical", "cornerRadius":"15px", "backgroundColor":C['card'], 
                         "paddingAll":"18px", "contents":content if content else [
                            {"type":"text", "text":"لا يوجد لاعبين بعد", "size":"15px", 
                             "color":C['text2'], "align":"center"}
                        ]}
                    ]}
                ]}
            ]
        }
    })

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
    user_id = event.source.user_id if hasattr(event.source, 'user_id') else event.source.group_id
    text = event.message.text.strip()
    
    profile = line_bot_api.get_profile(event.source.user_id) if hasattr(event.source, 'user_id') else None
    user_name = profile.display_name if profile else "لاعب"
    
    player = get_player(user_id)
    if not player:
        update_player(user_id, user_name, 0)
    
    # الأوامر
    if text in ['بوت', 'البوت', 'start', 'قائمة']:
        line_bot_api.reply_message(event.reply_token, welcome_card())
    
    elif text in ['مساعدة', 'help', 'ساعدني']:
        line_bot_api.reply_message(event.reply_token, help_card())
    
    elif text in ['الصدارة', 'leaderboard', 'ترتيب']:
        line_bot_api.reply_message(event.reply_token, leaderboard_card())
    
    elif text in ['نقاطي', 'points', 'نقاط']:
        player = get_player(user_id)
        points = player[2] if player else 0
        line_bot_api.reply_message(event.reply_token, 
            TextSendMessage(text=f"نقاطك: {points} ▫️"))
    
    elif text == 'ابدأ':
        games_list = ['fast', 'human', 'chain', 'song', 'opposite', 'order', 'letters']
        game_type = random.choice(games_list)
        game = start_game(game_type)
        active_games[user_id] = game
        line_bot_api.reply_message(event.reply_token, game['card'])
    
    elif text == 'لمح' and user_id in active_games:
        game = active_games[user_id]
        hint = game['hint']()
        update_player(user_id, user_name, -1)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=hint))
    
    elif text == 'جاوب' and user_id in active_games:
        game = active_games[user_id]
        answer = game['show_answer']()
        line_bot_api.reply_message(event.reply_token, answer)
    
    elif text == 'إيقاف' and user_id in active_games:
        del active_games[user_id]
        line_bot_api.reply_message(event.reply_token, 
            TextSendMessage(text="تم إيقاف اللعبة 🔘"))
    
    elif user_id in active_games:
        game = active_games[user_id]
        result = game['check'](text)
        if result['correct']:
            update_player(user_id, user_name, 2)
        if result['next']:
            line_bot_api.reply_message(event.reply_token, result['next'])
        else:
            line_bot_api.reply_message(event.reply_token, 
                TextSendMessage(text=result['msg']))

@app.route("/")
def home():
    return f'''<html><head><meta charset="utf-8"><title>بوت الحوت</title>
    <style>*{{margin:0;padding:0;box-sizing:border-box;font-family:Arial}}
    body{{background:#0A0E27;color:#E0F2FF;min-height:100vh;display:flex;align-items:center;justify-content:center}}
    .container{{text-align:center;padding:40px}}
    h1{{color:#00D9FF;font-size:3em;margin-bottom:20px}}
    .status{{background:#0F2440;padding:30px;border-radius:15px;margin:20px 0}}
    .grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:20px;margin:20px 0}}
    .stat{{background:#0A0E27;padding:20px;border-radius:10px}}
    .num{{font-size:2em;color:#00D9FF;font-weight:bold}}</style></head>
    <body><div class="container"><h1> بوت الحوت</h1>
    <div class="status"><p>☑️ البوت يعمل بنجاح</p></div>
    <div class="grid"><div class="stat"><div class="num">9</div><p>ألعاب</p></div>
    <div class="stat"><div class="num">Active</div><p>الحالة</p></div></div></div></body></html>'''

if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))


# ============================================
# games.py - جميع الألعاب
# ============================================
import random
from linebot.models import FlexSendMessage, TextSendMessage

C = {'bg':'#0A0E27', 'card':'#0F2440', 'text':'#E0F2FF', 'text2':'#7FB3D5', 'cyan':'#00D9FF'}

# بيانات الألعاب
GAMES_DATA = {
    'fast': {
        'name': 'أسرع ⏱️',
        'questions': [
            {'q': 'اكتب: سبحان الله', 'a': 'سبحان الله'},
            {'q': 'اكتب: الحمد لله', 'a': 'الحمد لله'},
            {'q': 'اكتب: الله أكبر', 'a': 'الله أكبر'},
            {'q': 'اكتب: لا إله إلا الله', 'a': 'لا إله إلا الله'},
            {'q': 'اكتب: استغفر الله', 'a': 'استغفر الله'}
        ]
    },
    'song': {
        'name': 'أغنية 🎵',
        'questions': [
            {'q': 'قولي أحبك كي تزيد وسامتي', 'a': 'كاظم الساهر'},
            {'q': 'يا طير يا طاير طير وهات أخبار', 'a': 'عبد المجيد عبد الله'},
            {'q': 'لو كان قلبي معي ما اخترت غيركم', 'a': 'محمد عبده'},
            {'q': 'قلبي معاك ولا بعيد عنك', 'a': 'راشد الماجد'},
            {'q': 'وش جاب لجيته على بالي', 'a': 'عبادي الجوهر'}
        ]
    },
    'opposite': {
        'name': 'ضد ↔️',
        'questions': [
            {'q': 'ما عكس: حار', 'a': 'بارد'},
            {'q': 'ما عكس: سريع', 'a': 'بطيء'},
            {'q': 'ما عكس: كبير', 'a': 'صغير'},
            {'q': 'ما عكس: قوي', 'a': 'ضعيف'},
            {'q': 'ما عكس: جميل', 'a': 'قبيح'}
        ]
    }
}

def create_game_card(game_name, question_text, current, total, show_buttons=True):
    buttons = []
    if show_buttons:
        buttons = [
            {"type":"button", "action":{"type":"message", "label":"لمح", "text":"لمح"}, 
             "style":"secondary", "color":"#FFFFFF", "height":"sm"},
            {"type":"button", "action":{"type":"message", "label":"جاوب", "text":"جاوب"}, 
             "style":"primary", "color":"#FFFFFF", "height":"sm"}
        ]
    
    return FlexSendMessage(alt_text=game_name, contents={
        "type":"bubble", "size":"mega", "direction":"rtl", "body":{
            "type":"box", "layout":"vertical", "spacing":"md", "backgroundColor":C['bg'], 
            "paddingAll":"20px", "contents":[
                {"type":"box", "layout":"vertical", "contents":[
                    {"type":"text", "text":game_name, "weight":"bold", "size":"xl", "color":C['cyan']},
                    {"type":"text", "text":f"السؤال {current}/{total}", "size":"sm", "color":C['text2']}
                ]},
                {"type":"box", "layout":"vertical", "backgroundColor":C['card'], "cornerRadius":"12px", 
                 "paddingAll":"16px", "contents":[
                    {"type":"text", "text":question_text, "wrap":True, "color":C['text'], "size":"md"}
                ]},
                {"type":"box", "layout":"vertical", "height":"3px", "cornerRadius":"2px", 
                 "backgroundColor":C['cyan']},
                {"type":"box", "layout":"horizontal", "spacing":"md", "margin":"lg", 
                 "contents":buttons} if buttons else {"type":"box", "layout":"vertical", "contents":[]}
            ]
        }
    })

def start_game(game_type):
    game_data = GAMES_DATA.get(game_type, GAMES_DATA['fast'])
    current_q = 0
    
    def get_card():
        q = game_data['questions'][current_q]
        return create_game_card(game_data['name'], q['q'], current_q+1, 5, 
                               show_buttons=game_type != 'fast')
    
    def hint():
        q = game_data['questions'][current_q]
        ans = q['a']
        return f"💡 تلميح\nأول حرف: {ans[0]}\nعدد الحروف: {len(ans)}"
    
    def show_answer():
        nonlocal current_q
        q = game_data['questions'][current_q]
        ans = q['a']
        current_q += 1
        if current_q < 5:
            return get_card()
        return TextSendMessage(text=f"☑️ الإجابة: {ans}\n🏁 انتهت اللعبة!")
    
    def check(user_input):
        nonlocal current_q
        q = game_data['questions'][current_q]
        correct = user_input.strip().lower() == q['a'].lower()
        
        if correct:
            current_q += 1
            if current_q < 5:
                return {'correct': True, 'next': get_card(), 'msg': ''}
            return {'correct': True, 'next': TextSendMessage(text=" إجابة صحيحة!\n🏁 انتهت اللعبة!"), 'msg': ''}
        return {'correct': False, 'next': None, 'msg': '❌ إجابة خاطئة، حاول مرة أخرى'}
    
    return {'card': get_card(), 'hint': hint, 'show_answer': show_answer, 'check': check}


# ============================================
# requirements.txt
# ============================================
Flask==2.3.0
line-bot-sdk==3.5.0
requests==2.31.0


# ============================================
# .env (متغيرات البيئة)
# ============================================
LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token_here
LINE_CHANNEL_SECRET=your_channel_secret_here
PORT=5000
