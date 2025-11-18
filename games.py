# games.py - ألعاب بوت الحوت المحسّنة

import random
import re
import time
from config import C, GAME_SETTINGS, POINTS, MESSAGES

# ============= بيانات الألعاب =============

# لعبة أسرع - كلمات وأدعية
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

# لعبة إنسان حيوان نبات بلد
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

# لعبة سلسلة الكلمات
CHAIN_START = ['سيارة', 'قلم', 'كتاب', 'رياضة', 'مدرسة', 'طائرة', 'شمس', 'قمر', 'باب', 'نور']

# لعبة الأغنية
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

# لعبة الأضداد
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

# لعبة الترتيب
ORDER_DATA = [
    {'items': ['يناير', 'مارس', 'فبراير', 'أبريل'], 'answer': ['يناير', 'فبراير', 'مارس', 'أبريل'], 'type': 'الأشهر'},
    {'items': ['الأحد', 'الثلاثاء', 'الاثنين', 'الأربعاء'], 'answer': ['الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء'], 'type': 'الأيام'},
    {'items': ['5', '2', '8', '1'], 'answer': ['1', '2', '5', '8'], 'type': 'الأرقام تصاعدياً'},
    {'items': ['القاهرة', 'الرياض', 'دبي', 'بيروت'], 'answer': ['بيروت', 'دبي', 'الرياض', 'القاهرة'], 'type': 'المدن أبجدياً'},
    {'items': ['طفل', 'شاب', 'رضيع', 'كهل'], 'answer': ['رضيع', 'طفل', 'شاب', 'كهل'], 'type': 'العمر'}
]

# لعبة تكوين الكلمات
BUILD_DATA = [
    {'letters': 'م د ر س ة ت', 'words': ['مدرسة', 'درس', 'مدة']},
    {'letters': 'ك ت ا ب ة ي', 'words': ['كتاب', 'كتابة', 'كاتب']},
    {'letters': 'ط ع ا م ة ت', 'words': ['طعام', 'طعمة', 'معت']},
    {'letters': 'ج م ي ل ة ا', 'words': ['جميلة', 'جمال', 'جمل']},
    {'letters': 'س ي ا ر ة ت', 'words': ['سيارة', 'سير', 'رسا']}
]

# ============= دوال مساعدة =============

def normalize_arabic(text):
    """توحيد الحروف العربية"""
    text = text.strip()
    text = re.sub('[أإآ]', 'ا', text)
    text = re.sub('ى', 'ي', text)
    text = re.sub('ة', 'ه', text)
    return text.lower()

def create_game_card(title, question, current, total, emoji="🎮", show_buttons=True):
    """إنشاء بطاقة اللعبة الموحدة"""
    
    # شريط التقدم
    progress_percent = (current / total) * 100
    
    contents = [
        {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": f"{emoji} {title}",
                    "weight": "bold",
                    "size": "xl",
                    "color": C['cyan'],
                    "align": "center"
                },
                {
                    "type": "text",
                    "text": f"السؤال {current}/{total}",
                    "size": "sm",
                    "color": C['text2'],
                    "align": "center",
                    "margin": "xs"
                }
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
                {
                    "type": "text",
                    "text": question,
                    "wrap": True,
                    "color": C['text'],
                    "size": "md",
                    "align": "center"
                }
            ]
        },
        {
            "type": "box",
            "layout": "vertical",
            "height": "6px",
            "backgroundColor": C['sep'],
            "cornerRadius": "3px",
            "margin": "md",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "width": f"{progress_percent}%",
                    "height": "6px",
                    "backgroundColor": C['cyan'],
                    "cornerRadius": "3px",
                    "contents": []
                }
            ]
        }
    ]
    
    if show_buttons:
        contents.append({
            "type": "box",
            "layout": "horizontal",
            "spacing": "md",
            "margin": "lg",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "message",
                        "label": "💡 لمح",
                        "text": "لمح"
                    },
                    "style": "secondary",
                    "color": "#F1F1F1",
                    "height": "sm"
                },
                {
                    "type": "button",
                    "action": {
                        "type": "message",
                        "label": "📝 جاوب",
                        "text": "جاوب"
                    },
                    "style": "primary",
                    "color": C['cyan'],
                    "height": "sm"
                }
            ]
        })
    
    return {
        "type": "bubble",
        "size": "mega",
        "direction": "rtl",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "backgroundColor": C['bg'],
            "paddingAll": "20px",
            "contents": contents
        }
    }

def create_winner_card(winner_name, winner_points, game_name):
    """إنشاء بطاقة الفائز"""
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": C['bg'],
            "paddingAll": "20px",
            "contents": [
                {
                    "type": "text",
                    "text": "🏆 انتهت اللعبة!",
                    "weight": "bold",
                    "size": "xxl",
                    "color": C['cyan'],
                    "align": "center"
                },
                {
                    "type": "separator",
                    "color": C['sep'],
                    "margin": "15px"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": C['card'],
                    "cornerRadius": "15px",
                    "paddingAll": "20px",
                    "margin": "md",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"🥇 الفائز: {winner_name}",
                            "size": "lg",
                            "color": C['text'],
                            "wrap": True,
                            "align": "center"
                        },
                        {
                            "type": "text",
                            "text": f"⭐ النقاط: {winner_points}",
                            "size": "md",
                            "color": C['text2'],
                            "margin": "md",
                            "align": "center"
                        }
                    ]
                },
                {
                    "type": "button",
                    "style": "primary",
                    "color": C['cyan'],
                    "action": {
                        "type": "message",
                        "label": "🎮 لعب مرة أخرى",
                        "text": game_name
                    },
                    "margin": "xl"
                }
            ]
        }
    }

# ============= الألعاب =============

def start_game(group_id, game_type, user_id, user_name):
    """بدء لعبة جديدة"""
    game_data = {
        'type': game_type,
        'round': 1,
        'players': {user_id: {'name': user_name, 'points': 0}},
        'started_by': user_id,
        'start_time': time.time()
    }
    
    if game_type == 'fast':
        return start_fast_game(game_data)
    elif game_type == 'lbgame':
        return start_lbgame(game_data)
    elif game_type == 'chain':
        return start_chain_game(game_data)
    elif game_type == 'song':
        return start_song_game(game_data)
    elif game_type == 'opposite':
        return start_opposite_game(game_data)
    elif game_type == 'order':
        return start_order_game(game_data)
    elif game_type == 'build':
        return start_build_game(game_data)
    elif game_type == 'compat':
        return start_compat_game(game_data)
    
    return {'message': 'لعبة غير معروفة', 'game_data': game_data}

# ========== 1. لعبة أسرع ==========

def start_fast_game(game_data):
    """لعبة أسرع"""
    item = random.choice(FAST_WORDS)
    game_data['current_q'] = item['q']
    game_data['current_a'] = item['a']
    game_data['question_time'] = time.time()
    
    card = create_game_card(
        "أسرع",
        f"أكمل الجملة:\n\n{item['q']}",
        game_data['round'],
        GAME_SETTINGS['rounds'],
        emoji="⏱️",
        show_buttons=False  # لا تدعم لمح/جاوب
    )
    
    return {
        'message': '⏱️ بدأت لعبة أسرع!',
        'flex': card,
        'game_data': game_data
    }

def check_fast_answer(game, text, user_id, user_name):
    """التحقق من إجابة لعبة أسرع"""
    elapsed = time.time() - game.get('question_time', time.time())
    
    if normalize_arabic(text) == normalize_arabic(game['current_a']):
        # حساب النقاط بناءً على السرعة
        if elapsed < 5:
            points = 5
        elif elapsed < 10:
            points = 4
        elif elapsed < 15:
            points = 3
        else:
            points = 2
        
        if user_id not in game['players']:
            game['players'][user_id] = {'name': user_name, 'points': 0}
        
        game['players'][user_id]['points'] += points
        
        return {'correct': True, 'points': points}
    
    return {'correct': False}

# ========== 2. لعبة إنسان حيوان نبات بلد ==========

def start_lbgame(game_data):
    """لعبة إنسان حيوان نبات بلد"""
    item = random.choice(LBGAME_DATA)
    game_data['current_letter'] = item['letter']
    game_data['current_answers'] = item['answers']
    
    card = create_game_card(
        "لعبة",
        f"أعط أسماء تبدأ بحرف: {item['letter']}\n\nإنسان\nحيوان\nنبات\nبلد",
        game_data['round'],
        GAME_SETTINGS['rounds'],
        emoji="🎮"
    )
    
    return {
        'message': '🎮 بدأت لعبة إنسان حيوان نبات بلد!',
        'flex': card,
        'game_data': game_data
    }

def check_lbgame_answer(game, text, user_id, user_name):
    """التحقق من إجابة لعبة إنسان حيوان نبات بلد"""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if len(lines) != 4:
        return {'correct': False, 'message': 'يجب كتابة 4 إجابات (إنسان، حيوان، نبات، بلد)'}
    
    correct_count = 0
    
    for answer in lines:
        normalized = normalize_arabic(answer)
        if normalized.startswith(normalize_arabic(game['current_letter'])):
            correct_count += 1
    
    if correct_count >= 3:  # 3 إجابات صحيحة على الأقل
        if user_id not in game['players']:
            game['players'][user_id] = {'name': user_name, 'points': 0}
        
        game['players'][user_id]['points'] += POINTS['correct']
        return {'correct': True}
    
    return {'correct': False}

# ========== 3. سلسلة الكلمات ==========

def start_chain_game(game_data):
    """لعبة سلسلة الكلمات"""
    start_word = random.choice(CHAIN_START)
    game_data['current_word'] = start_word
    game_data['last_letter'] = start_word[-1]
    game_data['used_words'] = [start_word]
    
    card = create_game_card(
        "سلسلة الكلمات",
        f"الكلمة الحالية: {start_word}\n\nاكتب كلمة تبدأ بحرف: {start_word[-1]}",
        game_data['round'],
        GAME_SETTINGS['rounds'],
        emoji="🔗"
    )
    
    return {
        'message': '🔗 بدأت لعبة سلسلة الكلمات!',
        'flex': card,
        'game_data': game_data
    }

def check_chain_answer(game, text, user_id, user_name):
    """التحقق من إجابة سلسلة الكلمات"""
    word = text.strip()
    normalized = normalize_arabic(word)
    
    if len(word) < 2:
        return {'correct': False}
    
    if normalized in [normalize_arabic(w) for w in game['used_words']]:
        return {'correct': False, 'message': 'هذه الكلمة مستخدمة بالفعل'}
    
    if normalized[0] == normalize_arabic(game['last_letter']):
        if user_id not in game['players']:
            game['players'][user_id] = {'name': user_name, 'points': 0}
        
        game['players'][user_id]['points'] += POINTS['correct']
        game['current_word'] = word
        game['last_letter'] = word[-1]
        game['used_words'].append(word)
        
        return {'correct': True}
    
    return {'correct': False}

# ========== 4. لعبة الأغنية ==========

def start_song_game(game_data):
    """لعبة الأغنية"""
    song = random.choice(SONGS_DATA)
    game_data['current_lyrics'] = song['lyrics']
    game_data['current_artist'] = song['artist']
    
    card = create_game_card(
        "الأغنية",
        f"{song['lyrics']}\n\nمن المغني؟",
        game_data['round'],
        GAME_SETTINGS['rounds'],
        emoji="🎵"
    )
    
    return {
        'message': '🎵 بدأت لعبة الأغنية!',
        'flex': card,
        'game_data': game_data
    }

def check_song_answer(game, text, user_id, user_name):
    """التحقق من إجابة لعبة الأغنية"""
    if normalize_arabic(text) == normalize_arabic(game['current_artist']):
        if user_id not in game['players']:
            game['players'][user_id] = {'name': user_name, 'points': 0}
        
        game['players'][user_id]['points'] += POINTS['correct']
        return {'correct': True}
    
    return {'correct': False}

# ========== 5. لعبة الأضداد ==========

def start_opposite_game(game_data):
    """لعبة الأضداد"""
    item = random.choice(OPPOSITE_DATA)
    game_data['current_word'] = item['word']
    game_data['current_opposite'] = item['opposite']
    
    card = create_game_card(
        "ضد",
        f"ما هو عكس كلمة:\n\n{item['word']}",
        game_data['round'],
        GAME_SETTINGS['rounds'],
        emoji="⚖️"
    )
    
    return {
        'message': '⚖️ بدأت لعبة الأضداد!',
        'flex': card,
        'game_data': game_data
    }

def check_opposite_answer(game, text, user_id, user_name):
    """التحقق من إجابة لعبة الأضداد"""
    if normalize_arabic(text) == normalize_arabic(game['current_opposite']):
        if user_id not in game['players']:
            game['players'][user_id] = {'name': user_name, 'points': 0}
        
        game['players'][user_id]['points'] += POINTS['correct']
        return {'correct': True}
    
    return {'correct': False}

# ========== 6. لعبة الترتيب ==========

def start_order_game(game_data):
    """لعبة الترتيب"""
    item = random.choice(ORDER_DATA)
    game_data['current_items'] = item['items']
    game_data['correct_order'] = item['answer']
    game_data['order_type'] = item['type']
    
    card = create_game_card(
        "ترتيب",
        f"رتب {item['type']}:\n\n" + '\n'.join(item['items']),
        game_data['round'],
        GAME_SETTINGS['rounds'],
        emoji="📋"
    )
    
    return {
        'message': '📋 بدأت لعبة الترتيب!',
        'flex': card,
        'game_data': game_data
    }

def check_order_answer(game, text, user_id, user_name):
    """التحقق من إجابة لعبة الترتيب"""
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

# ========== 7. لعبة تكوين الكلمات ==========

def start_build_game(game_data):
    """لعبة تكوين الكلمات"""
    item = random.choice(BUILD_DATA)
    game_data['current_letters'] = item['letters']
    game_data['valid_words'] = item['words']
    
    card = create_game_card(
        "تكوين كلمات",
        f"كون 3 كلمات من الحروف:\n\n{item['letters']}\n\nاكتب الكلمات كل واحدة في سطر",
        game_data['round'],
        GAME_SETTINGS['rounds'],
        emoji="🔤"
    )
    
    return {
        'message': '🔤 بدأت لعبة تكوين الكلمات!',
        'flex': card,
        'game_data': game_data
    }

def check_build_answer(game, text, user_id, user_name):
    """التحقق من إجابة لعبة تكوين الكلمات"""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if len(lines) != 3:
        return {'correct': False, 'message': 'يجب كتابة 3 كلمات'}
    
    correct_count = 0
    for word in lines:
        normalized = normalize_arabic(word)
        if any(normalize_arabic(valid) == normalized for valid in game['valid_words']):
            correct_count += 1
    
    if correct_count >= 2:  # كلمتان صحيحتان على الأقل
        if user_id not in game['players']:
            game['players'][user_id] = {'name': user_name, 'points': 0}
        
        game['players'][user_id]['points'] += POINTS['correct']
        return {'correct': True}
    
    return {'correct': False}

# ========== 8. لعبة التوافق ==========

def start_compat_game(game_data):
    """لعبة التوافق"""
    return {
        'message': '💕 لعبة التوافق\n\nاكتب اسمين لحساب نسبة التوافق بينهما\n\nمثال:\nأحمد\nفاطمة',
        'game_data': game_data
    }

def check_compat_answer(game, text, user_id, user_name):
    """التحقق من إجابة لعبة التوافق"""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if len(lines) != 2:
        return {'correct': False, 'message': 'يجب كتابة اسمين'}
    
    # حساب نسبة التوافق بطريقة عشوائية لكن ثابتة لنفس الأسماء
    name1, name2 = sorted(lines)
    seed = sum(ord(c) for c in name1 + name2)
    random.seed(seed)
    compat = random.randint(1, 100)
    
    # رموز القلوب حسب النسبة
    hearts = '❤️' * (compat // 10)
    
    message = f"💕 نسبة التوافق بين {lines[0]} و {lines[1]}:\n\n{hearts} {compat}%"
    
    if user_id not in game['players']:
        game['players'][user_id] = {'name': user_name, 'points': 0}
    
    return {'correct': True, 'message': message, 'end_game': True}

# ============= دوال التحقق الرئيسية =============

def check_game_answer(game, text, user_id, user_name, group_id, active_games):
    """التحقق من الإجابة حسب نوع اللعبة"""
    game_type = game['type']
    
    result = {'correct': False, 'message': None}
    
    if game_type == 'fast':
        result = check_fast_answer(game, text, user_id, user_name)
    elif game_type == 'lbgame':
        result = check_lbgame_answer(game, text, user_id, user_name)
    elif game_type == 'chain':
        result = check_chain_answer(game, text, user_id, user_name)
    elif game_type == 'song':
        result = check_song_answer(game, text, user_id, user_name)
    elif game_type == 'opposite':
        result = check_opposite_answer(game, text, user_id, user_name)
    elif game_type == 'order':
        result = check_order_answer(game, text, user_id, user_name)
    elif game_type == 'build':
        result = check_build_answer(game, text, user_id, user_name)
    elif game_type == 'compat':
        result = check_compat_answer(game, text, user_id, user_name)
    
    # إذا كانت الإجابة صحيحة والجولة لم تنته
    if result['correct']:
        if result.get('end_game'):
            del active_games[group_id]
            return result
        
        game['round'] += 1
        
        # إذا انتهت الجولات
        if game['round'] > GAME_SETTINGS['rounds']:
            # إيجاد الفائز
            winner = max(game['players'].items(), key=lambda x: x[1]['points'])
            winner_id, winner_data = winner
            
            card = create_winner_card(winner_data['name'], winner_data['points'], game_type)
            
            del active_games[group_id]
            
            return {
                'correct': True,
                'message': f"🏆 الفائز: {winner_data['name']} بـ {winner_data['points']} نقطة!",
                'flex': card
            }
        else:
            # السؤال التالي
            next_result = start_game(group_id, game_type, user_id, user_name)
            active_games[group_id] = next_result['game_data']
            
            return {
                'correct': True,
                'message': f"✅ إجابة صحيحة! +{result.get('points', POINTS['correct'])} نقطة",
                'flex': next_result.get('flex')
            }
    
    return result

def get_hint(game):
    """الحصول على تلميح"""
    game_type = game['type']
    
    if game_type == 'fast':
        return None  # لا تدعم التلميحات
    elif game_type == 'lbgame':
        return f"💡 تلميح:\nالحرف: {game['current_letter']}\nمثال أول حرف:\nإنسان: {game['current_answers'][0][0]}_\nحيوان: {game['current_answers'][1][0]}_"
    elif game_type == 'chain':
        return f"💡 تلميح:\nابدأ بحرف: {game['last_letter']}\nعدد الحروف المقترح: 4-6"
    elif game_type == 'song':
        answer = game['current_artist']
        return f"💡 تلميح:\nأول حرف: {answer[0]}\nعدد الحروف: {len(answer)}"
    elif game_type == 'opposite':
        answer = game['current_opposite']
        return f"💡 تلميح:\nأول حرف: {answer[0]}\nعدد الحروف: {len(answer)}"
    elif game_type == 'order':
        return f"💡 تلميح:\nنوع الترتيب: {game['order_type']}\nالعنصر الأول: {game['correct_order'][0]}"
    elif game_type == 'build':
        return f"💡 تلميح:\nالحروف المتاحة: {game['current_letters']}\nمثال كلمة: {game['valid_words'][0][:2]}..."
    elif game_type == 'compat':
        return None  # لا تدعم التلميحات
    
    return None

def show_answer(game, group_id, active_games):
    """عرض الإجابة الصحيحة والانتقال للسؤال التالي"""
    game_type = game['type']
    answer = ""
    
    if game_type == 'fast':
        answer = game['current_a']
    elif game_type == 'lbgame':
        answer = '\n'.join(game['current_answers'])
    elif game_type == 'chain':
        answer = f"أي كلمة تبدأ بـ {game['last_letter']}"
    elif game_type == 'song':
        answer = game['current_artist']
    elif game_type == 'opposite':
        answer = game['current_opposite']
    elif game_type == 'order':
        answer = '\n'.join(game['correct_order'])
    elif game_type == 'build':
        answer = '\n'.join(game['valid_words'])
    elif game_type == 'compat':
        return {'message': 'هذه اللعبة لا تدعم عرض الإجابة'}
    
    # الانتقال للسؤال التالي
    game['round'] += 1
    
    if game['round'] > GAME_SETTINGS['rounds']:
        # إيجاد الفائز
        if game['players']:
            winner = max(game['players'].items(), key=lambda x: x[1]['points'])
            winner_id, winner_data = winner
            
            card = create_winner_card(winner_data['name'], winner_data['points'], game_type)
            
            del active_games[group_id]
            
            return {
                'message': f"📝 الإجابة الصحيحة:\n{answer}\n\n🏆 الفائز: {winner_data['name']} بـ {winner_data['points']} نقطة!",
                'flex': card
            }
        else:
            del active_games[group_id]
            return {'message': f"📝 الإجابة الصحيحة:\n{answer}\n\nانتهت اللعبة!"}
    else:
        # السؤال التالي
        next_result = start_game(group_id, game_type, list(game['players'].keys())[0] if game['players'] else 'system', 'النظام')
        active_games[group_id] = next_result['game_data']
        
        return {
            'message': f"📝 الإجابة الصحيحة:\n{answer}",
            'flex': next_result.get('flex')
        }
