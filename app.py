"""
Whale Bot
=========
Main application file
"""

import logging
import time
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
)

from config import *
from database import db
from style import welcome_card, question_card, result_card, stats_card, ranks_card, hint_card
from utils import (
    read_random_line, parse_game_line, sanitize_input, 
    check_similarity, create_hint, ensure_directory, ensure_file
)

# Setup logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# LINE Bot API
try:
    line_api = LineBotApi(LINE_ACCESS_TOKEN)
    handler = WebhookHandler(LINE_SECRET)
    logger.info("LINE Bot initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize LINE Bot: {e}")
    exit(1)

# Game sessions
active_games = {}

# Ensure directories exist
ensure_directory(DATA_DIR)
ensure_directory(GAMES_DIR)

# Routes
@app.route("/", methods=['GET'])
def home():
    """Home page"""
    return f"""
    <html>
    <head>
        <title>Whale Bot</title>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: linear-gradient(135deg, #000000 0%, #1A1A1A 100%);
                color: #FFFFFF;
                text-align: center;
                padding: 50px;
                margin: 0;
            }}
            h1 {{ color: #4DD0E1; margin-bottom: 20px; }}
            p {{ color: #9E9E9E; font-size: 1.1em; }}
            .status {{ color: #26C6DA; font-weight: bold; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <h1>Whale Bot</h1>
        <p>LINE Bot is running</p>
        <div class="status">Version {VERSION}</div>
        <div class="status">{DEVELOPER}</div>
    </body>
    </html>
    """

@app.route("/callback", methods=['POST'])
def callback():
    """LINE webhook callback"""
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature")
        abort(400)
    except Exception as e:
        logger.error(f"Callback error: {e}")
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """Handle incoming messages"""
    user_id = event.source.user_id
    text = sanitize_input(event.message.text, MAX_INPUT)
    
    # Get user profile
    try:
        profile = line_api.get_profile(user_id)
        name = profile.display_name
    except:
        name = "مستخدم"
    
    logger.info(f"User: {name} ({user_id}), Message: {text}")
    
    # Get or create player
    player = db.get_player(user_id)
    if not player:
        player = db.create_player(user_id, name)
    else:
        db.update_name(user_id, name)
    
    # Route commands
    messages = []
    
    # Check for commands
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
    
    elif any(cmd in text for cmd in CMD['skip']):
        messages = handle_skip(user_id)
    
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
        logger.error(f"Failed to send message: {e}")

# Command handlers

def handle_start():
    """Handle start command"""
    return [FlexSendMessage(alt_text="مرحباً", contents=welcome_card())]

def handle_stats(user_id):
    """Handle stats command"""
    player = db.get_player(user_id)
    if not player:
        return [TextSendMessage(text=MSG['error'])]
    
    return [FlexSendMessage(
        alt_text="احصائياتك",
        contents=stats_card(
            player['name'],
            player['points'],
            player['games_played'],
            player['games_won']
        )
    )]

def handle_ranks():
    """Handle ranks command"""
    players = db.get_leaderboard(LEADERBOARD_SIZE)
    if not players:
        return [TextSendMessage(text=MSG['no_players'])]
    
    return [FlexSendMessage(
        alt_text="المتصدرون",
        contents=ranks_card(players)
    )]

def handle_stop(user_id):
    """Handle stop command"""
    if user_id in active_games:
        game = active_games[user_id]
        db.save_game_history(
            user_id, 
            game['type'], 
            game['points'], 
            game['round'] - 1, 
            False
        )
        del active_games[user_id]
        return [TextSendMessage(text=MSG['stopped'])]
    return [TextSendMessage(text=MSG['no_game'])]

def handle_hint(user_id):
    """Handle hint command"""
    if user_id not in active_games:
        return [TextSendMessage(text=MSG['no_game'])]
    
    game = active_games[user_id]
    game_info = GAMES.get(game['type'])
    
    if not game_info or not game_info.get('hint'):
        return [TextSendMessage(text="التلميح غير متاح في هذه اللعبة")]
    
    if game.get('hint_used'):
        return [TextSendMessage(text="تم استخدام التلميح مسبقاً")]
    
    answer = game.get('answer', '')
    if not answer:
        return [TextSendMessage(text=MSG['error'])]
    
    hint_text = create_hint(answer)
    game['hint_used'] = True
    game['points'] += POINTS['hint']
    db.update_points(user_id, POINTS['hint'])
    
    return [FlexSendMessage(
        alt_text="تلميح",
        contents=hint_card(hint_text)
    )]

def handle_skip(user_id):
    """Handle skip command"""
    if user_id not in active_games:
        return [TextSendMessage(text=MSG['no_game'])]
    
    game = active_games[user_id]
    game_info = GAMES.get(game['type'])
    
    if not game_info or not game_info.get('skip'):
        return [TextSendMessage(text="التخطي غير متاح في هذه اللعبة")]
    
    return handle_next_round(user_id, skip=True)

def handle_game_start(user_id, game_key):
    """Start a new game"""
    if user_id in active_games:
        return [TextSendMessage(text=MSG['game_active'])]
    
    game_info = GAMES.get(game_key)
    if not game_info:
        return [TextSendMessage(text=MSG['error'])]
    
    # Initialize game session
    active_games[user_id] = {
        'type': game_key,
        'round': 1,
        'points': 0,
        'start_time': time.time(),
        'hint_used': False
    }
    
    return load_question(user_id)

def load_question(user_id):
    """Load next question"""
    if user_id not in active_games:
        return [TextSendMessage(text=MSG['no_game'])]
    
    game = active_games[user_id]
    game_info = GAMES.get(game['type'])
    
    if not game_info:
        return [TextSendMessage(text=MSG['error'])]
    
    # Read question from file
    filepath = f"{GAMES_DIR}/{game_info['file']}"
    ensure_file(filepath, "سؤال تجريبي|جواب\n")
    
    line = read_random_line(filepath)
    if not line:
        return [TextSendMessage(text="لا توجد أسئلة متاحة")]
    
    question, answer = parse_game_line(line)
    if not question or not answer:
        return [TextSendMessage(text=MSG['error'])]
    
    # Store in session
    game['question'] = question
    game['answer'] = answer
    game['hint_used'] = False
    game['round_start'] = time.time()
    
    return [FlexSendMessage(
        alt_text=game_info['name'],
        contents=question_card(
            game_info['name'],
            question,
            game['round'],
            ROUNDS
        )
    )]

def handle_game_answer(user_id, name, answer):
    """Handle game answer"""
    if user_id not in active_games:
        return [TextSendMessage(text=MSG['no_game'])]
    
    game = active_games[user_id]
    correct_answer = game.get('answer', '')
    
    if not correct_answer:
        return [TextSendMessage(text=MSG['error'])]
    
    # Check answer
    is_correct = check_similarity(answer, correct_answer)
    
    if is_correct:
        # Calculate points
        points = POINTS['correct']
        game['points'] += points
        db.update_points(user_id, points)
        
        messages = [FlexSendMessage(
            alt_text="صحيح",
            contents=result_card(
                MSG['correct'],
                f"أحسنت {name}",
                points,
                True
            )
        )]
        
        # Next round or end game
        game['round'] += 1
        if game['round'] > ROUNDS:
            # Game ended
            db.update_stats(user_id, won=True)
            db.save_game_history(
                user_id,
                game['type'],
                game['points'],
                ROUNDS,
                True
            )
            del active_games[user_id]
            messages.append(TextSendMessage(
                text=f"{MSG['game_end']}\nمجموع نقاطك: {game['points']}"
            ))
        else:
            # Next question
            messages.extend(load_question(user_id))
        
        return messages
    else:
        return [FlexSendMessage(
            alt_text="خطأ",
            contents=result_card(
                MSG['wrong'],
                "حاول مرة أخرى",
                None,
                False
            )
        )]

def handle_next_round(user_id, skip=False):
    """Move to next round"""
    if user_id not in active_games:
        return [TextSendMessage(text=MSG['no_game'])]
    
    game = active_games[user_id]
    
    if skip:
        messages = [TextSendMessage(text=f"الإجابة الصحيحة: {game.get('answer', '')}")]
    else:
        messages = []
    
    game['round'] += 1
    if game['round'] > ROUNDS:
        # Game ended
        db.update_stats(user_id, won=False)
        db.save_game_history(
            user_id,
            game['type'],
            game['points'],
            game['round'] - 1,
            False
        )
        del active_games[user_id]
        messages.append(TextSendMessage(
            text=f"{MSG['game_end']}\nمجموع نقاطك: {game['points']}"
        ))
    else:
        messages.extend(load_question(user_id))
    
    return messages

def handle_content(content_type):
    """Handle content requests"""
    filename = CONTENT.get(content_type)
    if not filename:
        return [TextSendMessage(text=MSG['error'])]
    
    filepath = f"{DATA_DIR}/{filename}"
    ensure_file(filepath, f"{content_type} تجريبي\n")
    
    line = read_random_line(filepath)
    return [TextSendMessage(text=line or MSG['error'])]

# Run app
if __name__ == "__main__":
    logger.info(f"Starting Whale Bot v{VERSION} on port {PORT}")
    app.run(host=HOST, port=PORT, debug=DEBUG)
