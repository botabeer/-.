from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from dotenv import load_dotenv
from database import Database
from style import *
from games import get_game_class
from games.game_ai import AiChat
from rules import GAMES_INFO, COMMANDS
import random

load_dotenv()

app = Flask(__name__)
line_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
db = Database()

active_games = {}
group_players = {}

# قراءة المحتوى الترفيهي من ملفات data/
DATA_DIR = "data"

def load_entertainment_content():
    content_types = ['سؤال', 'تحدي', 'اعتراف', 'منشن']
    content = {}
    for ctype in content_types:
        file_path = os.path.join(DATA_DIR, f"{ctype}s.txt")  # مثال: questions.txt
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content[ctype] = [line.strip() for line in f if line.strip()]
        else:
            content[ctype] = []
    return content

entertainment_content = load_entertainment_content()

@app.route("/")
def home():
    return "Whale Bot is running!"

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
    profile = line_api.get_profile(user_id)
    user_name = profile.display_name

    player = db.get_player(user_id)
    if not player:
        db.create_player(user_id, user_name)
    else:
        db.update_name(user_id, user_name)

    group_id = getattr(event.source, 'group_id', None)
    messages = process_input(user_id, group_id, text, user_name)

    if messages:
        line_api.reply_message(event.reply_token, messages)

def process_input(user_id, group_id, text, user_name):
    text_lower = text.lower()

    if text_lower in COMMANDS['start']:
        return [create_welcome_card()]
    if text_lower in ['العاب', 'الالعاب', 'games']:
        return [create_games_menu()]
    if text_lower in ['ترفيه', 'محتوى', 'entertainment']:
        return [create_entertainment_menu()]
    if text_lower in ['مساعدة', 'help', 'ساعدني']:
        return [create_help_card()]
    if text_lower in COMMANDS['stats']:
        return [create_stats_card(user_id, db)]
    if text_lower in COMMANDS['leaderboard']:
        return [create_leaderboard_card(db)]

    if text in ['سؤال', 'تحدي', 'اعتراف', 'منشن']:
        content_item = random.choice(entertainment_content.get(text, ["لا يوجد محتوى بعد"]))
        return [create_entertainment_content(text, content_item)]

    if group_id:
        if text_lower in ['انضم', 'join']:
            if group_id not in group_players:
                group_players[group_id] = set()
            if user_id in group_players[group_id]:
                return [TextSendMessage(text=f"{user_name} أنت مشترك بالفعل")]
            group_players[group_id].add(user_id)
            count = len(group_players[group_id])
            return [TextSendMessage(text=f"تم الانضمام!\n{user_name} انضم للعبة\nعدد اللاعبين: {count}")]
        if group_id in group_players and user_id not in group_players[group_id]:
            if text_lower not in ['ابدأ', 'مساعدة', 'نقاطي', 'الصدارة', 'العاب', 'ترفيه', 'سؤال', 'تحدي', 'اعتراف', 'منشن']:
                return None

    if text_lower in COMMANDS['stop']:
        if user_id in active_games:
            del active_games[user_id]
            return [TextSendMessage(text="تم إيقاف اللعبة")]
        return None

    # بدء أي لعبة
    for game_key, game_info in GAMES_INFO.items():
        if text in game_info['triggers']:
            if game_key == "ai":
                game = AiChat()
                active_games[user_id] = {
                    'type': game_key,
                    'game': game,
                    'round': 1,
                    'points': 0,
                    'name': user_name
                }
                return [TextSendMessage(text="مرحباً! ابدأ المحادثة مع AI")]
            else:
                return start_game(user_id, game_key, user_name)

    if user_id in active_games:
        return handle_game_input(user_id, text)

    return None

def start_game(user_id, game_key, user_name):
    if user_id in active_games:
        return [TextSendMessage(text="لديك لعبة نشطة، ارسل 'ايقاف' لإنهائها")]

    game_class = get_game_class(game_key)
    if not game_class:
        return [TextSendMessage(text="خطأ في تحميل اللعبة")]

    game = game_class()
    active_games[user_id] = {
        'type': game_key,
        'game': game,
        'round': 1,
        'points': 0,
        'name': user_name
    }

    question = game.generate_question()
    active_games[user_id]['question'] = question

    game_info = GAMES_INFO[game_key]
    return [create_question_card(
        game_info['name'],
        question['text'],
        1,
        game.rounds,
        game.supports_hint
    )]

def handle_game_input(user_id, text):
    session = active_games[user_id]
    game = session['game']
    game_key = session['type']
    text_lower = text.lower()

    if text_lower in COMMANDS['hint'] and game.supports_hint:
        hint = game.get_hint()
        session['points'] -= 1
        return [TextSendMessage(text=f"تلميح: {hint} - خصم نقطة واحدة")]

    if text_lower in COMMANDS['skip']:
        answer = game.show_answer()
        session['round'] += 1
        if session['round'] > game.rounds:
            return end_game(user_id)
        question = game.next_question()
        session['question'] = question
        game_info = GAMES_INFO[game_key]
        return [
            create_result_card(False, f"الإجابة: {answer}", 0),
            create_question_card(
                game_info['name'],
                question['text'],
                session['round'],
                game.rounds,
                game.supports_hint
            )
        ]

    result = game.check_answer(user_id, text)

    if game_key == 'ai':
        if result['correct']:
            session['round'] += 1
            return [TextSendMessage(text=result['message'])]
        return [TextSendMessage(text=result['message'])]

    if game_key == 'compatibility':
        del active_games[user_id]
        return [create_result_card(True, result['message'], 0)]

    if result['correct']:
        session['points'] += result['points']
        session['round'] += 1
        if session['round'] > game.rounds:
            return end_game(user_id)
        question = game.next_question()
        session['question'] = question
        game_info = GAMES_INFO[game_key]
        return [
            create_result_card(True, result['message'], result['points']),
            create_question_card(
                game_info['name'],
                question['text'],
                session['round'],
                game.rounds,
                game.supports_hint
            )
        ]
    else:
        return [create_result_card(False, result['message'], 0)]

def end_game(user_id):
    session = active_games[user_id]
    points = session['points']
    game_key = session['type']
    user_name = session['name']

    won = points > 0
    db.update_points(user_id, points)
    db.update_stats(user_id, won)
    db.save_game_history(user_id, game_key, points, session['round'] - 1, won)
    del active_games[user_id]

    if won:
        message = f"أحسنت {user_name}!\nنقاطك: {points}\nارسل 'ابدأ' للعب مرة أخرى"
    else:
        message = f"انتهت اللعبة {user_name}\nنقاطك: {points}\nحاول مرة أخرى!"

    return [TextSendMessage(text=message)]

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False') == 'True'
    app.run(host='0.0.0.0', port=port, debug=debug)
