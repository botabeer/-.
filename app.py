from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from dotenv import load_dotenv
from database import Database
from style import create_welcome_card, create_question_card, create_result_card, create_stats_card, create_leaderboard_card
from games import get_game_class
from rules import GAMES_INFO, COMMANDS
import utils
from gemini_service import GeminiService

load_dotenv()

app = Flask(__name__)
line_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
db = Database()
gemini = GeminiService()

active_games = {}

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
    
    messages = process_input(user_id, text)
    line_api.reply_message(event.reply_token, messages)

def process_input(user_id, text):
    text_lower = text.lower()
    
    if text_lower in COMMANDS['start']:
        return [create_welcome_card()]
    
    if text_lower in COMMANDS['stats']:
        return [create_stats_card(user_id, db)]
    
    if text_lower in COMMANDS['leaderboard']:
        return [create_leaderboard_card(db)]
    
    if text_lower in COMMANDS['stop']:
        if user_id in active_games:
            del active_games[user_id]
            return [TextSendMessage(text="تم ايقاف اللعبة")]
        return [TextSendMessage(text="لا توجد لعبة نشطة")]
    
    for game_key, game_info in GAMES_INFO.items():
        if text in game_info['triggers']:
            return start_game(user_id, game_key)
    
    if user_id in active_games:
        return handle_game_input(user_id, text)
    
    if text_lower == 'ai' or text_lower == 'محادثة':
        return start_game(user_id, 'ai')
    
    return [TextSendMessage(text="ارسل 'ابدا' لعرض القائمة")]

def start_game(user_id, game_key):
    if user_id in active_games:
        return [TextSendMessage(text="لديك لعبة نشطة، ارسل 'ايقاف' لانهائها")]
    
    game_info = GAMES_INFO[game_key]
    game_class = get_game_class(game_key)
    
    if not game_class:
        return [TextSendMessage(text="خطأ في تحميل اللعبة")]
    
    game = game_class()
    active_games[user_id] = {
        'type': game_key,
        'game': game,
        'round': 1,
        'points': 0
    }
    
    if game_key == 'ai':
        return [TextSendMessage(text="مرحبا! انا مساعدك الذكي. اسالني عن اي شيء (حد اقصى 5 رسائل)")]
    
    if game_key == 'compatibility':
        return [TextSendMessage(text="اكتب اسمين مفصولين بمسافة لحساب التوافق")]
    
    question = game.generate_question()
    active_games[user_id]['question'] = question
    
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
        return [TextSendMessage(text=f"تلميح: {hint}\nخصم نقطة واحدة")]
    
    if text_lower in COMMANDS['skip']:
        answer = game.show_answer()
        session['round'] += 1
        
        if session['round'] > game.rounds:
            return end_game(user_id)
        
        question = game.next_question()
        session['question'] = question
        
        game_info = GAMES_INFO[game_key]
        return [
            create_result_card(False, f"الاجابة: {answer}", 0),
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
            if session['round'] > 5:
                del active_games[user_id]
                return [TextSendMessage(text=result['message'] + "\n\nانتهت المحادثة (حد اقصى 5 رسائل)")]
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
    
    won = points > 0
    
    db.update_points(user_id, points)
    db.update_stats(user_id, won)
    db.save_game_history(user_id, game_key, points, session['round'] - 1, won)
    
    del active_games[user_id]
    
    message = f"انتهت اللعبة!\nنقاطك: {points}\n\nارسل 'ابدا' للعب مرة اخرى"
    return [TextSendMessage(text=message)]

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False') == 'True'
    app.run(host='0.0.0.0', port=port, debug=debug)
