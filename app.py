"""
Whale Bot
=========
Main application file
"""

import logging
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
)

from config import *
from database import db
from style import welcome_card, question_card, result_card, stats_card, ranks_card
from utils import read_random_line

# Setup logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# LINE Bot API
try:
    line_api = LineBotApi(LINE_ACCESS_TOKEN)
    handler = WebhookHandler(LINE_SECRET)
    logger.info("LINE Bot initialized")
except Exception as e:
    logger.error(f"Failed to initialize: {e}")
    exit(1)

# Game sessions
active_games = {}

# Routes
@app.route("/", methods=['GET'])
def home():
    return """
    <html>
    <head>
        <title>Whale Bot</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #0F172A;
                color: #F1F5F9;
                text-align: center;
                padding: 50px;
            }
            h1 { color: #3B82F6; }
        </style>
    </head>
    <body>
        <h1>Whale Bot</h1>
        <p>Bot is running</p>
    </body>
    </html>
    """

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    except Exception as e:
        logger.error(f"Callback error: {e}")
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()[:MAX_INPUT]
    
    try:
        profile = line_api.get_profile(user_id)
        name = profile.display_name
    except:
        name = "مستخدم"
    
    logger.info(f"{name}: {text}")
    
    # Get or create player
    player = db.get_player(user_id)
    if not player:
        player = db.create_player(user_id, name)
    
    # Route commands
    messages = []
    
    if any(cmd in text for cmd in CMD['start']):
        messages = handle_start()
    
    elif any(cmd in text for cmd in CMD['stats']):
        messages = handle_stats(user_id)
    
    elif any(cmd in text for cmd in CMD['ranks']):
        messages = handle_ranks()
    
    elif any(cmd in text for cmd in CMD['stop']):
        messages = handle_stop(user_id)
    
    elif any(cmd in text for cmd in CMD['hint']):
        messages = handle_hint(user_id)
    
    elif any(cmd in text for cmd in CMD['answer']):
        messages = handle_answer(user_id)
    
    elif text in GAMES:
        messages = handle_game_start(user_id, text)
    
    elif text in CONTENT:
        messages = handle_content(text)
    
    elif user_id in active_games:
        messages = handle_game_answer(user_id, name, text)
    
    else:
        messages = [TextSendMessage(text=MSG['invalid'])]
    
    # Send reply
    try:
        if messages:
            line_api.reply_message(event.reply_token, messages)
    except LineBotApiError as e:
        logger.error(f"Send error: {e}")

# Command handlers
def handle_start():
    return [FlexSendMessage(alt_text="مرحباً", contents=welcome_card())]

def handle_stats(user_id):
    player = db.get_player(user_id)
    if not player:
        return [TextSendMessage(text=MSG['error'])]
    
    return [FlexSendMessage(
        alt_text="إحصائياتك",
        contents=stats_card(
            player['name'],
            player['points'],
            player['games_played'],
            player['games_won']
        )
    )]

def handle_ranks():
    players = db.get_leaderboard()
    if not players:
        return [TextSendMessage(text="لا يوجد لاعبون")]
    
    return [FlexSendMessage(
        alt_text="المتصدرون",
        contents=ranks_card(players)
    )]

def handle_stop(user_id):
    if user_id in active_games:
        del active_games[user_id]
        return [TextSendMessage(text=MSG['stopped'])]
    return [TextSendMessage(text=MSG['no_game'])]

def handle_hint(user_id):
    # Implement hint logic based on game type
    return [TextSendMessage(text="التلميح غير متوفر")]

def handle_answer(user_id):
    # Implement answer reveal logic
    return [TextSendMessage(text="الجواب غير متوفر")]

def handle_game_start(user_id, game_key):
    if user_id in active_games:
        return [TextSendMessage(text=MSG['game_active'])]
    
    # Initialize game session
    active_games[user_id] = {
        'type': game_key,
        'round': 1,
        'points': 0
    }
    
    game_name = GAMES[game_key]['name']
    question = "سؤال تجريبي"  # Replace with actual game logic
    
    return [FlexSendMessage(
        alt_text=f"{game_name}",
        contents=question_card(game_name, question, 1, ROUNDS)
    )]

def handle_game_answer(user_id, name, answer):
    if user_id not in active_games:
        return [TextSendMessage(text=MSG['no_game'])]
    
    game = active_games[user_id]
    
    # Check answer (implement actual logic)
    is_correct = True  # Placeholder
    
    if is_correct:
        db.update_points(user_id, POINTS['correct'])
        game['points'] += POINTS['correct']
        game['round'] += 1
        
        messages = [FlexSendMessage(
            alt_text="صحيح",
            contents=result_card(
                "إجابة صحيحة",
                f"أحسنت {name}",
                POINTS['correct'],
                True
            )
        )]
        
        if game['round'] > ROUNDS:
            db.update_stats(user_id, won=True)
            del active_games[user_id]
            messages.append(TextSendMessage(
                text=f"انتهت اللعبة\nمجموع نقاطك: {game['points']}"
            ))
        else:
            # Next question
            question = "السؤال التالي"  # Placeholder
            messages.append(FlexSendMessage(
                alt_text="السؤال التالي",
                contents=question_card(
                    GAMES[game['type']]['name'],
                    question,
                    game['round'],
                    ROUNDS
                )
            ))
        
        return messages
    else:
        return [FlexSendMessage(
            alt_text="خطأ",
            contents=result_card(
                "إجابة خاطئة",
                "حاول مرة أخرى",
                None,
                False
            )
        )]

def handle_content(content_type):
    file_map = {
        'سؤال': 'questions.txt',
        'منشن': 'mentions.txt',
        'تحدي': 'challenges.txt',
        'اعتراف': 'confessions.txt'
    }
    
    filename = file_map.get(content_type)
    if not filename:
        return [TextSendMessage(text=MSG['error'])]
    
    line = read_random_line(f"{DATA_DIR}/{filename}")
    return [TextSendMessage(text=line or MSG['error'])]

# Run app
if __name__ == "__main__":
    logger.info(f"Starting bot on port {PORT}")
    app.run(host=HOST, port=PORT, debug=DEBUG)
