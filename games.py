from linebot.models import TextSendMessage, FlexSendMessage
import random
import re

def normalize_text(text):
    if not text:
        return ""
    text = text.strip().lower()
    text = text.replace('أ','ا').replace('إ','ا').replace('آ','ا')
    text = text.replace('ؤ','و').replace('ئ','ي').replace('ء','')
    text = text.replace('ة','ه').replace('ى','ي')
    text = re.sub(r'[\u064B-\u065F]','',text)
    text = re.sub(r'\s+','',text)
    return text

COLORS = {
    'bg': '#0A0E27',
    'topbg': '#667eea',
    'card': '#1a1f3a',
    'text': '#E8F4FF',
    'text2': '#8FB9D8',
    'cyan': '#00D9FF',
    'glow': '#5EEBFF',
    'sep': '#2C5F8D',
    'border': '#00D9FF50',
    'glass': '#1a1f3a90',
    'success': '#00FF88',
    'warning': '#FFB800'
}

LOGO_URL = 'https://i.imgur.com/qcWILGi.jpeg'

def create_game_card(game_name, question_num, total, content_items):
    C = COLORS
    progress = (question_num/total)*100
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": C['bg'],
            "paddingAll": "0px",
            "contents": [{
                "type": "box",
                "layout": "vertical",
                "backgroundColor": C['topbg'],
                "paddingTop": "40px",
                "paddingBottom": "150px",
                "contents": [{
                    "type": "box",
                    "layout": "vertical",
                    "cornerRadius": "30px",
                    "backgroundColor": C['bg'],
                    "paddingAll": "0px",
                    "offsetTop": "60px",
                    "borderWidth": "2px",
                    "borderColor": C['border'],
                    "contents": [
                        {"type": "box", "layout": "vertical", "paddingAll": "30px", "paddingBottom": "25px", "backgroundColor": C['card'], "cornerRadius": "30px 30px 0px 0px", "contents": [
                            {"type": "text", "text": f"✨ {game_name}", "weight": "bold", "size": "xxl", "align": "center", "color": C['glow']},
                            {"type": "text", "text": f"السؤال {question_num} من {total}", "size": "md", "align": "center", "color": C['text2'], "margin": "md"}
                        ]},
                        {"type": "box", "layout": "vertical", "height": "8px", "backgroundColor": C['sep'], "contents": [
                            {"type": "box", "layout": "vertical", "backgroundColor": C['cyan'], "width": f"{progress}%", "height": "8px"}
                        ]},
                        {"type": "box", "layout": "vertical", "paddingAll": "30px", "spacing": "xl", "contents": content_items + [
                            {"type": "separator", "color": C['sep'], "margin": "xl"},
                            {"type": "box", "layout": "horizontal", "spacing": "md", "margin": "xl", "contents": [
                                {"type": "button", "action": {"type": "message", "label": "💡 لمح", "text": "لمح"}, "style": "secondary", "color": "#FFFFFF", "height": "md"},
                                {"type": "button", "action": {"type": "message", "label": "✓ جاوب", "text": "جاوب"}, "style": "primary", "color": C['cyan'], "height": "md"}
                            ]}
                        ]}
                    ]
                }]
            }]
        }
    }

def create_hint_card(hint_text, extra_info=None):
    C = COLORS
    contents = [{"type": "text", "text": hint_text, "size": "xl", "color": C['text'], "align": "center", "wrap": True, "weight": "bold"}]
    if extra_info:
        contents.append({"type": "text", "text": extra_info, "size": "md", "color": C['text2'], "align": "center", "margin": "md"})
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": C['card'],
            "cornerRadius": "25px",
            "paddingAll": "30px",
            "borderWidth": "2px",
            "borderColor": C['border'],
            "contents": [
                {"type": "text", "text": "💡 تلميح", "weight": "bold", "size": "xxl", "color": C['glow'], "align": "center"},
                {"type": "separator", "color": C['sep'], "margin": "lg"},
                {"type": "box", "layout": "vertical", "backgroundColor": C['glass'], "cornerRadius": "20px", "paddingAll": "25px", "margin": "xl", "borderWidth": "1px", "borderColor": C['border'], "contents": contents},
                {"type": "text", "text": "⚠️ النقاط ستنخفض إلى نصف القيمة", "size": "sm", "color": C['warning'], "align": "center", "margin": "xl", "wrap": True}
            ]
        }
    }

def create_answer_card(answer_text):
    C = COLORS
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": C['card'],
            "cornerRadius": "25px",
            "paddingAll": "30px",
            "borderWidth": "2px",
            "borderColor": C['border'],
            "contents": [
                {"type": "text", "text": "✓ الإجابة الصحيحة", "weight": "bold", "size": "xxl", "color": C['glow'], "align": "center"},
                {"type": "separator", "color": C['sep'], "margin": "lg"},
                {"type": "box", "layout": "vertical", "backgroundColor": C['glass'], "cornerRadius": "20px", "paddingAll": "25px", "margin": "xl", "borderWidth": "2px", "borderColor": C['cyan'], "contents": [
                    {"type": "text", "text": answer_text, "size": "xxl", "weight": "bold", "color": C['cyan'], "align": "center", "wrap": True}
                ]}
            ]
        }
    }

def create_results_card(player_scores):
    C = COLORS
    if not player_scores:
        return TextSendMessage(text="لم يشارك أحد في اللعبة")
    sorted_players = sorted(player_scores.items(), key=lambda x: x[1]['score'], reverse=True)
    winners_content = []
    rank_emojis = {1: "🥇", 2: "🥈", 3: "🥉"}
    for idx, (user_id, data) in enumerate(sorted_players[:5], 1):
        emoji = rank_emojis.get(idx, f"{idx}️⃣")
        winners_content.append({
            "type": "box",
            "layout": "horizontal",
            "backgroundColor": C['glass'],
            "cornerRadius": "15px",
            "paddingAll": "18px",
            "margin": "md" if idx > 1 else "none",
            "borderWidth": "2px" if idx <= 3 else "1px",
            "borderColor": C['cyan'] if idx <= 3 else C['border'],
            "contents": [
                {"type": "text", "text": emoji, "size": "xxl", "flex": 0},
                {"type": "text", "text": data['name'], "size": "lg", "color": C['text'], "flex": 3, "margin": "md", "weight": "bold" if idx <= 3 else "regular"},
                {"type": "text", "text": f"{data['score']} ⭐", "size": "lg", "color": C['cyan'], "align": "end", "flex": 1, "weight": "bold"}
            ]
        })
    return FlexSendMessage(alt_text="النتائج النهائية", contents={
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": C['bg'],
            "paddingAll": "0px",
            "contents": [{
                "type": "box",
                "layout": "vertical",
                "backgroundColor": C['topbg'],
                "paddingTop": "40px",
                "paddingBottom": "150px",
                "contents": [{
                    "type": "box",
                    "layout": "vertical",
                    "cornerRadius": "30px",
                    "backgroundColor": C['bg'],
                    "paddingAll": "35px",
                    "offsetTop": "60px",
                    "borderWidth": "2px",
                    "borderColor": C['border'],
                    "contents": [
                        {"type": "text", "text": "🏆 انتهت اللعبة!", "weight": "bold", "size": "xxl", "align": "center", "color": C['glow']},
                        {"type": "separator", "color": C['sep'], "margin": "xl"},
                        {"type": "text", "text": "✨ لوحة الصدارة", "size": "xl", "align": "center", "color": C['text'], "margin": "xl", "weight": "bold"},
                        {"type": "box", "layout": "vertical", "margin": "xl", "contents": winners_content},
                        {"type": "button", "action": {"type": "message", "label": "🔄 لعب مرة أخرى", "text": "إعادة"}, "style": "primary", "color": C['cyan'], "height": "md", "margin": "xxl"}
                    ]
                }]
            }]
        }
    })

class OppositeGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.all_words = [
            {"word":"كبير","opposite":"صغير"},{"word":"طويل","opposite":"قصير"},{"word":"سريع","opposite":"بطيء"},
            {"word":"حار","opposite":"بارد"},{"word":"قوي","opposite":"ضعيف"},{"word":"غني","opposite":"فقير"},
            {"word":"سعيد","opposite":"حزين"},{"word":"نظيف","opposite":"وسخ"},{"word":"جديد","opposite":"قديم"},
            {"word":"صعب","opposite":"سهل"},{"word":"ثقيل","opposite":"خفيف"},{"word":"واسع","opposite":"ضيق"},
            {"word":"عميق","opposite":"ضحل"},{"word":"شجاع","opposite":"جبان"},{"word":"ذكي","opposite":"غبي"}
        ]
        self.questions = []
        self.current_word = None
        self.hints_used = 0
        self.question_number = 0
        self.total_questions = 5
        self.player_scores = {}

    def start_game(self):
        self.questions = random.sample(self.all_words, min(self.total_questions, len(self.all_words)))
        self.question_number = 0
        self.player_scores = {}
        self.hints_used = 0
        return self.next_question()

    def next_question(self):
        if self.question_number >= self.total_questions:
            return None
        self.current_word = self.questions[self.question_number]
        self.question_number += 1
        self.hints_used = 0
        content = [{"type": "box", "layout": "vertical", "backgroundColor": COLORS['glass'], "cornerRadius": "20px", "paddingAll": "28px", "borderWidth": "2px", "borderColor": COLORS['border'], "contents": [
            {"type": "text", "text": "🔄 ما هو عكس:", "size": "lg", "color": COLORS['text2'], "align": "center"},
            {"type": "text", "text": self.current_word['word'], "size": "xxl", "weight": "bold", "color": COLORS['cyan'], "align": "center", "margin": "lg"}
        ]}]
        card = create_game_card("لعبة الضد", self.question_number, self.total_questions, content)
        return FlexSendMessage(alt_text=f"السؤال {self.question_number} - لعبة الضد", contents=card)

    def get_hint(self):
        if not self.current_word:
            return None
        opposite = self.current_word['opposite']
        hint_text = f"أول حرف: {opposite[0]} " + "_ " * (len(opposite) - 1)
        extra = f"📏 عدد الحروف: {len(opposite)}"
        self.hints_used += 1
        return FlexSendMessage(alt_text="تلميح", contents=create_hint_card(hint_text, extra))

    def show_answer(self):
        if not self.current_word:
            return None
        return FlexSendMessage(alt_text="الإجابة الصحيحة", contents=create_answer_card(self.current_word['opposite']))

    def check_answer(self, answer, user_id, display_name):
        if not self.current_word:
            return None
        if normalize_text(answer) == normalize_text(self.current_word['opposite']):
            points = 2 if self.hints_used == 0 else 1
            if user_id not in self.player_scores:
                self.player_scores[user_id] = {'name': display_name, 'score': 0}
            self.player_scores[user_id]['score'] += points
            return {'response': TextSendMessage(text=f"✅ إجابة صحيحة! +{points} نقطة"), 'points': points, 'correct': True}
        return None

    def get_final_results(self):
        return create_results_card(self.player_scores)

class SongGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.all_songs = [
            {"lyrics": "قولي أحبك كي تزيد وسامتي", "singer": "كاظم الساهر"},
            {"lyrics": "يا طيور الطايرة فوق الحدود", "singer": "عبد المجيد عبدالله"},
            {"lyrics": "أنا لو عشقت حبيبي بجنون", "singer": "نجوى كرم"},
            {"lyrics": "حبيبي يا نور العين", "singer": "عمرو دياب"},
            {"lyrics": "على مودك يا بعد عمري", "singer": "محمد عبده"},
            {"lyrics": "تعبت من الصبر والانتظار", "singer": "راشد الماجد"},
            {"lyrics": "يا حبيبي كل اللي ودّك فيه", "singer": "أصالة"},
            {"lyrics": "كل عام وانت حبيبي", "singer": "وائل كفوري"},
            {"lyrics": "ما بلاش تبعد عني", "singer": "إليسا"},
            {"lyrics": "يا قمر يا قمر يا قمر", "singer": "نانسي عجرم"}
        ]
        self.questions = []
        self.current_song = None
        self.hints_used = 0
        self.question_number = 0
        self.total_questions = 5
        self.player_scores = {}

    def start_game(self):
        self.questions = random.sample(self.all_songs, min(self.total_questions, len(self.all_songs)))
        self.question_number = 0
        self.player_scores = {}
        self.hints_used = 0
        return self.next_question()

    def next_question(self):
        if self.question_number >= self.total_questions:
            return None
        self.current_song = self.questions[self.question_number]
        self.question_number += 1
        self.hints_used = 0
        content = [
            {"type": "box", "layout": "vertical", "backgroundColor": COLORS['glass'], "cornerRadius": "20px", "paddingAll": "28px", "borderWidth": "2px", "borderColor": COLORS['border'], "contents": [
                {"type": "text", "text": "🎵 كلمات الأغنية:", "size": "lg", "color": COLORS['text2'], "align": "center"},
                {"type": "text", "text": self.current_song['lyrics'], "size": "xl", "weight": "bold", "color": COLORS['cyan'], "align": "center", "margin": "lg", "wrap": True}
            ]},
            {"type": "text", "text": "🎤 من المغني؟", "size": "lg", "color": COLORS['text'], "align": "center", "margin": "lg"}
        ]
        card = create_game_card("لعبة الأغنية", self.question_number, self.total_questions, content)
        return FlexSendMessage(alt_text=f"السؤال {self.question_number} - لعبة الأغنية", contents=card)

    def get_hint(self):
        if not self.current_song:
            return None
        singer = self.current_song['singer']
        hint_text = f"أول حرف: {singer[0]} " + "_ " * (len(singer) - 1)
        extra = f"📏 عدد الحروف: {len(singer)}"
        self.hints_used += 1
        return FlexSendMessage(alt_text="تلميح", contents=create_hint_card(hint_text, extra))

    def show_answer(self):
        if not self.current_song:
            return None
        return FlexSendMessage(alt_text="الإجابة الصحيحة", contents=create_answer_card(self.current_song['singer']))

    def check_answer(self, answer, user_id, display_name):
        if not self.current_song:
            return None
        if normalize_text(answer) == normalize_text(self.current_song['singer']):
            points = 2 if self.hints_used == 0 else 1
            if user_id not in self.player_scores:
                self.player_scores[user_id] = {'name': display_name, 'score': 0}
            self.player_scores[user_id]['score'] += points
            return {'response': TextSendMessage(text=f"✅ إجابة صحيحة! +{points} نقطة"), 'points': points, 'correct': True}
        return None

    def get_final_results(self):
        return create_results_card(self.player_scores)

class ChainWordsGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.words_chain = [
            ["رياض", "ضياء", "ءامل", "لبنان", "نور"],
            ["سلام", "ملك", "كرم", "محمد", "دمشق"],
            ["قمر", "رمان", "نجم", "ماء", "ءيمان"],
            ["بحر", "رمل", "ليمون", "نسيم", "ماجد"],
            ["جبل", "لحم", "مصر", "رياح", "حلب"]
        ]
        self.current_chain = []
        self.current_index = 0
        self.hints_used = 0
        self.question_number = 0
        self.total_questions = 5
        self.player_scores = {}

    def start_game(self):
        self.current_chain = random.choice(self.words_chain)
        self.current_index = 0
        self.question_number = 0
        self.player_scores = {}
        self.hints_used = 0
        return self.next_question()

    def next_question(self):
        if self.question_number >= self.total_questions or self.current_index >= len(self.current_chain) - 1:
            return None
        self.question_number += 1
        self.hints_used = 0
        current_word = self.current_chain[self.current_index]
        content = [
            {"type": "box", "layout": "vertical", "backgroundColor": COLORS['glass'], "cornerRadius": "20px", "paddingAll": "28px", "borderWidth": "2px", "borderColor": COLORS['border'], "contents": [
                {"type": "text", "text": "🔗 الكلمة الحالية:", "size": "lg", "color": COLORS['text2'], "align": "center"},
                {"type": "text", "text": current_word, "size": "xxl", "weight": "bold", "color": COLORS['cyan'], "align": "center", "margin": "lg"}
            ]},
            {"type": "text", "text": f"✏️ أكتب كلمة تبدأ بحرف: {current_word[-1]}", "size": "lg", "color": COLORS['text'], "align": "center", "margin": "lg", "wrap": True}
        ]
        card = create_game_card("سلسلة الكلمات", self.question_number, self.total_questions, content)
        return FlexSendMessage(alt_text=f"السؤال {self.question_number} - سلسلة الكلمات", contents=card)

    def get_hint(self):
        if self.current_index >= len(self.current_chain) - 1:
            return None
        next_word = self.current_chain[self.current_index + 1]
        hint_text = f"الكلمة: {next_word[0]} " + "_ " * (len(next_word) - 1)
        extra = f"📏 عدد الحروف: {len(next_word)}"
        self.hints_used += 1
        return FlexSendMessage(alt_text="تلميح", contents=create_hint_card(hint_text, extra))

    def show_answer(self):
        if self.current_index >= len(self.current_chain) - 1:
            return None
        return FlexSendMessage(alt_text="الإجابة الصحيحة", contents=create_answer_card(self.current_chain[self.current_index + 1]))

    def check_answer(self, answer, user_id, display_name):
        if self.current_index >= len(self.current_chain) - 1:
            return None
        next_word = self.current_chain[self.current_index + 1]
        if normalize_text(answer) == normalize_text(next_word):
            points = 2 if self.hints_used == 0 else 1
            if user_id not in self.player_scores:
                self.player_scores[user_id] = {'name': display_name, 'score': 0}
            self.player_scores[user_id]['score'] += points
            self.current_index += 1
            return {'response': TextSendMessage(text=f"✅ إجابة صحيحة! +{points} نقطة"), 'points': points, 'correct': True}
        return None

    def get_final_results(self):
        return create_results_card(self.player_scores)

class OrderGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.all_questions = [
            {"items": ["ثانية", "دقيقة", "ساعة", "يوم"], "order": ["ثانية", "دقيقة", "ساعة", "يوم"], "type": "من الأصغر للأكبر"},
            {"items": ["كيلو", "جرام", "ملي", "طن"], "order": ["ملي", "جرام", "كيلو", "طن"], "type": "من الأصغر للأكبر"},
            {"items": ["قرن", "عام", "شهر", "أسبوع"], "order": ["أسبوع", "شهر", "عام", "قرن"], "type": "من الأصغر للأكبر"},
            {"items": ["محيط", "بحر", "نهر", "جدول"], "order": ["جدول", "نهر", "بحر", "محيط"], "type": "من الأصغر للأكبر"},
            {"items": ["جبل", "هضبة", "تل", "سهل"], "order": ["سهل", "تل", "هضبة", "جبل"], "type": "من الأصغر للأكبر"}
        ]
        self.questions = []
        self.current_question = None
        self.hints_used = 0
        self.question_number = 0
        self.total_questions = 5
        self.player_scores = {}

    def start_game(self):
        self.questions = random.sample(self.all_questions, min(self.total_questions, len(self.all_questions)))
        self.question_number = 0
        self.player_scores = {}
        self.hints_used = 0
        return self.next_question()

    def next_question(self):
        if self.question_number >= self.total_questions:
            return None
        self.current_question = self.questions[self.question_number]
        self.question_number += 1
        self.hints_used = 0
        shuffled = random.sample(self.current_question['items'], len(self.current_question['items']))
        content = [
            {"type": "text", "text": f"📊 رتب العناصر {self.current_question['type']}", "size": "lg", "color": COLORS['text'], "align": "center", "wrap": True},
            {"type": "box", "layout": "vertical", "backgroundColor": COLORS['glass'], "cornerRadius": "20px", "paddingAll": "28px", "margin": "lg", "borderWidth": "2px", "borderColor": COLORS['border'], "contents": [
                {"type": "text", "text": " • ".join(shuffled), "size": "xl", "weight": "bold", "color": COLORS['cyan'], "align": "center", "wrap": True}
            ]},
            {"type": "text", "text": "✏️ أكتب الترتيب مفصولاً بفواصل", "size": "sm", "color": COLORS['text2'], "align": "center", "margin": "lg", "wrap": True}
        ]
        card = create_game_card("لعبة الترتيب", self.question_number, self.total_questions, content)
        return FlexSendMessage(alt_text=f"السؤال {self.question_number} - لعبة الترتيب", contents=card)

    def get_hint(self):
        if not self.current_question:
            return None
        first_two = self.current_question['order'][:2]
        hint_text = f"أول عنصرين: {first_two[0]}، {first_two[1]}"
        self.hints_used += 1
        return FlexSendMessage(alt_text="تلميح", contents=create_hint_card(hint_text))

    def show_answer(self):
        if not self.current_question:
            return None
        answer = "، ".join(self.current_question['order'])
        return FlexSendMessage(alt_text="الإجابة الصحيحة", contents=create_answer_card(answer))

    def check_answer(self, answer, user_id, display_name):
        if not self.current_question:
            return None
        user_order = [normalize_text(item.strip()) for item in answer.replace('،', ',').split(',')]
        correct_order = [normalize_text(item) for item in self.current_question['order']]
        if user_order == correct_order:
            points = 2 if self.hints_used == 0 else 1
            if user_id not in self.player_scores:
                self.player_scores[user_id] = {'name': display_name, 'score': 0}
            self.player_scores[user_id]['score'] += points
            return {'response': TextSendMessage(text=f"✅ إجابة صحيحة! +{points} نقطة"), 'points': points, 'correct': True}
        return None

    def get_final_results(self):
        return create_results_card(self.player_scores)
