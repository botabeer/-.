import random
import re
import time
from config import C, GAME_SETTINGS, POINTS

# بيانات الألعاب
FAST_WORDS = [
    {'q': 'سبحان الله وبحمده', 'a': 'سبحان الله العظيم'},
    {'q': 'لا إله إلا', 'a': 'الله'},
    {'q': 'استغفر', 'a': 'الله'},
    {'q': 'الحمد', 'a': 'لله'},
    {'q': 'الله', 'a': 'أكبر'},
    {'q': 'بسم الله', 'a': 'الرحمن الرحيم'},
    {'q': 'لا حول ولا قوة إلا', 'a': 'بالله'},
    {'q': 'سبحان', 'a': 'الله'},
    {'q': 'اللهم صل على', 'a': 'محمد'},
    {'q': 'حسبنا الله ونعم', 'a': 'الوكيل'}
]

LBGAME_DATA = [
    {'letter': 'م', 'answers': ['محمد', 'ماعز', 'موز', 'مصر']},
    {'letter': 'ع', 'answers': ['علي', 'عصفور', 'عنب', 'عمان']},
    {'letter': 'س', 'answers': ['سارة', 'سمكة', 'سفرجل', 'سوريا']},
    {'letter': 'ن', 'answers': ['نور', 'نمر', 'نعناع', 'النرويج']},
    {'letter': 'ح', 'answers': ['حسن', 'حمار', 'حمص', 'الحجاز']},
    {'letter': 'ر', 'answers': ['رامي', 'رخم', 'رمان', 'الرياض']},
    {'letter': 'ف', 'answers': ['فاطمة', 'فيل', 'فلفل', 'فرنسا']},
    {'letter': 'ك', 'answers': ['كريم', 'كلب', 'كرز', 'الكويت']},
    {'letter': 'ب', 'answers': ['بدر', 'بقرة', 'بطيخ', 'البحرين']},
    {'letter': 'ص', 'answers': ['صالح', 'صقر', 'صبار', 'الصين']}
]

CHAIN_START = ['سيارة', 'قلم', 'كتاب', 'رياضة', 'مدرسة', 'طائرة', 'شمس', 'قمر']

SONGS_DATA = [
    {'lyrics': 'قولي أحبك كي تزيد وسامتي', 'artist': 'كاظم الساهر'},
    {'lyrics': 'على البال دوم معايا في كل مكان', 'artist': 'عمرو دياب'},
    {'lyrics': 'بحبك يا حياتي وانت عمري وسنيني', 'artist': 'تامر حسني'},
    {'lyrics': 'يا حبيبي يا عيني يا روحي يا غالي', 'artist': 'محمد عبده'},
    {'lyrics': 'انا قلبي دليلي وعيني تشوف', 'artist': 'راشد الماجد'},
    {'lyrics': 'حبك نار وحنيني زاد', 'artist': 'عبدالمجيد عبدالله'},
    {'lyrics': 'يا طير يا طاير يا رايح على بلادي', 'artist': 'وديع الصافي'},
    {'lyrics': 'احلى ما في الدنيا انك تحب', 'artist': 'وائل كفوري'},
    {'lyrics': 'قلبي يا قلبي عشقك يا عيني', 'artist': 'نانسي عجرم'},
    {'lyrics': 'خلاص سلمت وقلبي حبها', 'artist': 'ماجد المهندس'}
]

OPPOSITE_DATA = [
    {'word': 'كبير', 'opposite': 'صغير'},
    {'word': 'طويل', 'opposite': 'قصير'},
    {'word': 'سريع', 'opposite': 'بطيء'},
    {'word': 'حار', 'opposite': 'بارد'},
    {'word': 'نظيف', 'opposite': 'قذر'},
    {'word': 'قوي', 'opposite': 'ضعيف'},
    {'word': 'سهل', 'opposite': 'صعب'},
    {'word': 'جميل', 'opposite': 'قبيح'},
    {'word': 'غني', 'opposite': 'فقير'},
    {'word': 'ذكي', 'opposite': 'غبي'}
]

ORDER_DATA = [
    {'items': ['يناير', 'مارس', 'فبراير', 'أبريل'], 'answer': ['يناير', 'فبراير', 'مارس', 'أبريل'], 'type': 'الأشهر'},
    {'items': ['الأحد', 'الثلاثاء', 'الاثنين', 'الأربعاء'], 'answer': ['الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء'], 'type': 'الأيام'},
    {'items': ['5', '2', '8', '1'], 'answer': ['1', '2', '5', '8'], 'type': 'الأرقام'},
    {'items': ['القاهرة', 'الرياض', 'دبي', 'بيروت'], 'answer': ['بيروت', 'دبي', 'الرياض', 'القاهرة'], 'type': 'المدن'},
    {'items': ['طفل', 'شاب', 'رضيع', 'كهل'], 'answer': ['رضيع', 'طفل', 'شاب', 'كهل'], 'type': 'العمر'}
]

BUILD_DATA = [
    {'letters': 'م د ر س ة ت', 'words': ['مدرسة', 'درس', 'مدة']},
    {'letters': 'ك ت ا ب ة ي', 'words': ['كتاب', 'كتابة', 'كاتب']},
    {'letters': 'ط ع ا م ة ت', 'words': ['طعام', 'طعمة', 'معت']},
    {'letters': 'ج م ي ل ة ا', 'words': ['جميلة', 'جمال', 'جمل']},
    {'letters': 'س ي ا ر ة ت', 'words': ['سيارة', 'سير', 'رسا']}
]

# دوال مساعدة
def normalize_arabic(text):
    text = text.strip()
    text = re.sub('[أإآ]', 'ا', text)
    text = re.sub('ى', 'ي', text)
    text = re.sub('ة', 'ه', text)
    return text.lower()

def create_game_card(title, question, current, total, show_buttons=True):
    contents = [
        {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": title, "weight": "bold", "size": "xl", "color": C['cyan']},
                {"type": "text", "text": f"السؤال {current}/{total}", "size": "sm", "color": C['text2']}
            ]
        },
        {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": C['card'],
            "cornerRadius": "12px",
            "paddingAll": "16px",
            "margin": "md",
            "contents": [
                {"type": "text", "text": question, "wrap": True, "color": C['text'], "size": "md"}
            ]
        }
    ]
    
    if show_buttons:
        contents.extend([
            {
                "type": "box",
                "layout": "vertical",
                "height": "3px",
                "cornerRadius": "2px",
                "backgroundColor": C['cyan'],
                "margin": "md"
            },
            {
                "type": "box",
                "layout": "horizontal",
                "spacing": "sm",
                "margin": "md",
                "contents": [
                    {"type": "button", "action": {"type": "message", "label": "💡 لمح", "text": "لمح"}, "style": "secondary", "color": "#E8F4F8", "height": "sm"},
                    {"type": "button", "action": {"type": "message", "label": "📝 جاوب", "text": "جاوب"}, "style": "primary", "color": C['cyan'], "height": "sm"}
                ]
            }
        ])
    
    return {
        "type": "bubble",
        "size": "mega",
        "direction": "rtl",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "backgroundColor": C['bg'],
            "paddingAll": "20px",
            "contents": contents
        }
    }

def create_winner_card(winner_name, winner_points, game_name):
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": C['bg'],
            "paddingAll": "20px",
            "contents": [
                {"type": "text", "text": "🏆 انتهت اللعبة!", "weight": "bold", "size": "xxl", "color": C['cyan'], "align": "center"},
                {"type": "separator", "color": C['sep'], "margin": "md"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": C['card'],
                    "cornerRadius": "12px",
                    "paddingAll": "18px",
                    "margin": "md",
                    "contents": [
                        {"type": "text", "text": f"🥇 الفائز: {winner_name}", "size": "lg", "color": C['text'], "wrap": True, "align": "center"},
                        {"type": "text", "text": f"⭐ النقاط: {winner_points}", "size": "md", "color": C['text2'], "margin": "sm", "align": "center"}
                    ]
                },
                {
                    "type": "button",
                    "style": "primary",
                    "color": C['cyan'],
                    "action": {"type": "message", "label": "🔄 لعب مرة أخرى", "text": game_name},
                    "margin": "lg"
                }
            ]
        }
    }

# الألعاب
def start_game(group_id, game_type, user_id, user_name):
    game_data = {
        'type': game_type,
        'round': 1,
        'players': {user_id: {'name': user_name, 'points': 0}},
        'started_by': user_id,
        'start_time': time.time()
    }
    
    games_map = {
        'fast': start_fast_game,
        'lbgame': start_lbgame,
        'chain': start_chain_game,
        'song': start_song_game,
        'opposite': start_opposite_game,
        'order': start_order_game,
        'build': start_build_game,
        'compat': start_compat_game
    }
    
    return games_map.get(game_type, lambda x: {'message': 'لعبة غير معروفة', 'game_data': x})(game_data)

def start_fast_game(game_data):
    item = random.choice(FAST_WORDS)
    game_data['current_q'] = item['q']
    game_data['current_a'] = item['a']
    game_data['question_time'] = time.time()
    
    card = create_game_card("⏱️ لعبة أسرع", f"أكمل الجملة:\n{item['q']}", game_data['round'], GAME_SETTINGS['rounds'], show_buttons=False)
    
    return {'message': 'بدأت لعبة أسرع!', 'flex': card, 'game_data': game_data}

def check_fast_answer(game, text, user_id, user_name):
    elapsed = time.time() - game.get('question_time', time.time())
    
    if normalize_arabic(text) == normalize_arabic(game['current_a']):
        points = 5 if elapsed < 5 else (4 if elapsed < 10 else (3 if elapsed < 15 else 2))
        
        if user_id not in game['players']:
            game['players'][user_id] = {'name': user_name, 'points': 0}
        
        game['players'][user_id]['points'] += points
        return {'correct': True, 'points': points}
    
    return {'correct': False}

def start_lbgame(game_data):
    item = random.choice(LBGAME_DATA)
    game_data['current_letter'] = item['letter']
    game_data['current_answers'] = item['answers']
    
    card = create_game_card("🎮 لعبة", f"أعط أسماء تبدأ بحرف: {item['letter']}\n\nإنسان → حيوان → نبات → بلد", game_data['round'], GAME_SETTINGS['rounds'])
    
    return {'message': 'بدأت لعبة إنسان حيوان نبات بلد!', 'flex': card, 'game_data': game_data}

def check_lbgame_answer(game, text, user_id, user_name):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if len(lines) != 4:
        return {'correct': False, 'message': 'يجب كتابة 4 إجابات'}
    
    correct_count = sum(1 for answer in lines if normalize_arabic(answer).startswith(normalize_arabic(game['current_letter'])))
    
    if correct_count >= 3:
        if user_id not in game['players']:
            game['players'][user_id] = {'name': user_name, 'points': 0}
        
        game['players'][user_id]['points'] += POINTS['correct']
        return {'correct': True}
    
    return {'correct': False}

def start_chain_game(game_data):
    start_word = random.choice(CHAIN_START)
    game_data['current_word'] = start_word
    game_data['last_letter'] = start_word[-1]
    game_data['used_words'] = [start_word]
    
    card = create_game_card("🔗 سلسلة الكلمات", f"الكلمة الحالية: {start_word}\n\nاكتب كلمة تبدأ بحرف: {start_word[-1]}", game_data['round'], GAME_SETTINGS['rounds'])
    
    return {'message': 'بدأت لعبة سلسلة الكلمات!', 'flex': card, 'game_data': game_data}

def check_chain_answer(game, text, user_id, user_name):
    word = text.strip()
    normalized = normalize_arabic(word)
    
    if len(word) < 2:
        return {'correct': False}
    
    if normalized in [normalize_arabic(w) for w in game['used_words']]:
        return {'correct': False, 'message': 'كلمة مستخدمة'}
    
    if normalized[0] == normalize_arabic(game['last_letter']):
        if user_id not in game['players']:
            game['players'][user_id] = {'name': user_name, 'points': 0}
        
        game['players'][user_id]['points'] += POINTS['correct']
        game['current_word'] = word
        game['last_letter'] = word[-1]
        game['used_words'].append(word)
        
        return {'correct': True}
    
    return {'correct': False}

def start_song_game(game_data):
    song = random.choice(SONGS_DATA)
    game_data['current_lyrics'] = song['lyrics']
    game_data['current_artist'] = song['artist']
    
    card = create_game_card("🎵 لعبة الأغنية", f"{song['lyrics']}\n\nمن المغني؟", game_data['round'], GAME_SETTINGS['rounds'])
    
    return {'message': 'بدأت لعبة الأغنية!', 'flex': card, 'game_data': game_data}

def check_song_answer(game, text, user_id, user_name):
    if normalize_arabic(text) == normalize_arabic(game['current_artist']):
        if user_id not in game['players']:
            game['players'][user_id] = {'name': user_name, 'points': 0}
        
        game['players'][user_id]['points'] += POINTS['correct']
        return {'correct': True}
    
    return {'correct': False}

def start_opposite_game(game_data):
    item = random.choice(OPPOSITE_DATA)
    game_data['current_word'] = item['word']
    game_data['current_opposite'] = item['opposite']
    
    card = create_game_card("⚖️ لعبة ضد", f"ما هو عكس كلمة:\n{item['word']}", game_data['round'], GAME_SETTINGS['rounds'])
    
    return {'message': 'بدأت لعبة الأضداد!', 'flex': card, 'game_data': game_data}

def check_opposite_answer(game, text, user_id, user_name):
    if normalize_arabic(text) == normalize_arabic(game['current_opposite']):
        if user_id not in game['players']:
            game['players'][user_id] = {'name': user_name, 'points': 0}
        
        game['players'][user_id]['points'] += POINTS['correct']
        return {'correct': True}
    
    return {'correct': False}

def start_order_game(game_data):
    item = random.choice(ORDER_DATA)
    game_data['current_items'] = item['items']
    game_data['correct_order'] = item['answer']
    game_data['order_type'] = item['type']
    
    card = create_game_card("📋 لعبة ترتيب", f"رتب {item['type']}:\n" + '\n'.join(item['items']), game_data['round'], GAME_SETTINGS['rounds'])
    
    return {'message': 'بدأت لعبة الترتيب!', 'flex': card, 'game_data': game_data}

def check_order_answer(game, text, user_id, user_name):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if len(lines) != len(game['correct_order']):
        return {'correct': False}
    
    normalized_answer = [normalize_arabic(line) for line in lines]
    normalized_correct = [normalize_arabic(item) for item in game['correct_order']]
    
    if normalized_answer == normalized_correct:
        if user_id not in game['players']:
            game['players'][user_id] = {'name': user_name, 'points': 0}
        
        game['players'][user_id]['points'] += POINTS['correct']
        return {'correct': True}
    
    return {'correct': False}

def start_build_game(game_data):
    item = random.choice(BUILD_DATA)
    game_data['current_letters'] = item['letters']
    game_data['valid_words'] = item['words']
    
    card = create_game_card("🔤 تكوين كلمات", f"كون 3 كلمات من الحروف:\n{item['letters']}\n\nاكتب الكلمات كل واحدة في سطر", game_data['round'], GAME_SETTINGS['rounds'])
    
    return {'message': 'بدأت لعبة تكوين الكلمات!', 'flex': card, 'game_data': game_data}

def check_build_answer(game, text, user_id, user_name):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if len(lines) != 3:
        return {'correct': False, 'message': 'يجب كتابة 3 كلمات'}
    
    correct_count = sum(1 for word in lines if any(normalize_arabic(valid) == normalize_arabic(word) for valid in game['valid_words']))
    
    if correct_count >= 2:
        if user_id not in game['players']:
            game['players'][user_id] = {'name': user_name, 'points': 0}
        
        game['players'][user_id]['points'] += POINTS['correct']
        return {'correct': True}
    
    return {'correct': False}

def start_compat_game(game_data):
    return {'message': '💕 لعبة التوافق\n\nاكتب اسمين لحساب نسبة التوافق\nمثال:\nأحمد\nفاطمة', 'game_data': game_data}

def check_compat_answer(game, text, user_id, user_name):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if len(lines) != 2:
        return {'correct': False, 'message': 'يجب كتابة اسمين'}
    
    name1, name2 = sorted(lines)
    seed = sum(ord(c) for c in name1 + name2)
    random.seed(seed)
    compat = random.randint(1, 100)
    
    hearts = '❤️' * (compat // 10)
    message = f"💕 نسبة التوافق بين {lines[0]} و {lines[1]}:\n\n{hearts} {compat}%"
    
    return {'correct': True, 'message': message, 'end_game': True}

# دوال التحقق الرئيسية
def check_game_answer(game, text, user_id, user_name, group_id, active_games):
    game_type = game['type']
    
    check_map = {
        'fast': check_fast_answer,
        'lbgame': check_lbgame_answer,
        'chain': check_chain_answer,
        'song': check_song_answer,
        'opposite': check_opposite_answer,
        'order': check_order_answer,
        'build': check_build_answer,
        'compat': check_compat_answer
    }
    
    result = check_map.get(game_type, lambda *args: {'correct': False})(game, text, user_id, user_name)
    
    if result['correct']:
        if result.get('end_game'):
            del active_games[group_id]
            return result
        
        game['round'] += 1
        
        if game['round'] > GAME_SETTINGS['rounds']:
            winner = max(game['players'].items(), key=lambda x: x[1]['points'])
            winner_id, winner_data = winner
            
            card = create_winner_card(winner_data['name'], winner_data['points'], game_type)
            
            del active_games[group_id]
            
            return {'correct': True, 'message': f"🏆 الفائز: {winner_data['name']} بـ {winner_data['points']} نقطة!", 'flex': card}
        else:
            next_result = start_game(group_id, game_type, user_id, user_name)
            active_games[group_id] = next_result['game_data']
            
            return {'correct': True, 'message': f"✅ إجابة صحيحة! +{result.get('points', POINTS['correct'])} نقطة", 'flex': next_result.get('flex')}
    
    return result

def get_hint(game):
    game_type = game['type']
    
    hints = {
        'lbgame': lambda: f"💡 تلميح:\nالحرف: {game['current_letter']}\nمثال أول حرف:\nإنسان: {game['current_answers'][0][0]}_\nحيوان: {game['current_answers'][1][0]}_",
        'chain': lambda: f"💡 تلميح:\nابدأ بحرف: {game['last_letter']}\nعدد الحروف المقترح: 4-6",
        'song': lambda: f"💡 تلميح:\nأول حرف: {game['current_artist'][0]}\nعدد الحروف: {len(game['current_artist'])}",
        'opposite': lambda: f"💡 تلميح:\nأول حرف: {game['current_opposite'][0]}\nعدد الحروف: {len(game['current_opposite'])}",
        'order': lambda: f"💡 تلميح:\nنوع الترتيب: {game['order_type']}\nالعنصر الأول: {game['correct_order'][0]}",
        'build': lambda: f"💡 تلميح:\nالحروف المتاحة: {game['current_letters']}\nمثال كلمة: {game['valid_words'][0][:2]}..."
    }
    
    return hints.get(game_type, lambda: None)()

def show_answer(game, group_id, active_games):
    game_type = game['type']
    
    answers = {
        'fast': lambda: game['current_a'],
        'lbgame': lambda: '\n'.join(game['current_answers']),
        'chain': lambda: f"أي كلمة تبدأ بـ {game['last_letter']}",
        'song': lambda: game['current_artist'],
        'opposite': lambda: game['current_opposite'],
        'order': lambda: '\n'.join(game['correct_order']),
        'build': lambda: '\n'.join(game['valid_words'])
    }
    
    if game_type == 'compat':
        return {'message': 'هذه اللعبة لا تدعم عرض الإجابة'}
    
    answer = answers.get(game_type, lambda: '')()
    
    game['round'] += 1
    
    if game['round'] > GAME_SETTINGS['rounds']:
        if game['players']:
            winner = max(game['players'].items(), key=lambda x: x[1]['points'])
            winner_id, winner_data = winner
            
            card = create_winner_card(winner_data['name'], winner_data['points'], game_type)
            
            del active_games[group_id]
            
            return {'message': f"📝 الإجابة الصحيحة:\n{answer}\n\n🏆 الفائز: {winner_data['name']} بـ {winner_data['points']} نقطة!", 'flex': card}
        else:
            del active_games[group_id]
            return {'message': f"📝 الإجابة الصحيحة:\n{answer}\n\nانتهت اللعبة!"}
    else:
        next_result = start_game(group_id, game_type, list(game['players'].keys())[0] if game['players'] else 'system', 'النظام')
        active_games[group_id] = next_result['game_data']
        
        return {'message': f"📝 الإجابة الصحيحة:\n{answer}", 'flex': next_result.get('flex')}
