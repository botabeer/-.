import random
import re
import time
from linebot.models import TextSendMessage, FlexSendMessage

# ============= الإعدادات والثوابت =============
COLORS = {
    'bg': '#000000',
    'topbg': '#88AEE0',
    'card': '#0F2440',
    'card2': '#0A1628',
    'text': '#E0F2FF',
    'text2': '#7FB3D5',
    'cyan': '#00D9FF',
    'glow': '#5EEBFF',
    'sep': '#2C5F8D',
    'border': '#00D9FF40',
    'glass': '#0F244080'
}

GAME_SETTINGS = {
    'rounds': 5,
    'timeout': 30
}

POINTS = {
    'correct': 3,
    'hint': 1
}

LOGO_URL = 'https://i.imgur.com/qcWILGi.jpeg'

# ============= دوال التطبيع =============
def normalize_arabic(text):
    """تطبيع النص العربي للمقارنة"""
    if not text:
        return ""
    text = text.strip().lower()
    text = re.sub('[أإآ]', 'ا', text)
    text = re.sub('ى', 'ي', text)
    text = re.sub('ة', 'ه', text)
    text = re.sub('ؤ', 'و', text)
    text = re.sub('ئ', 'ي', text)
    text = re.sub('ء', '', text)
    text = re.sub(r'[\u064B-\u065F]', '', text)
    text = re.sub(r'\s+', '', text)
    return text

# ============= بيانات الألعاب =============
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
    {'letter': 'م', 'answers': {'human': 'محمد', 'animal': 'ماعز', 'plant': 'موز', 'country': 'مصر'}},
    {'letter': 'ع', 'answers': {'human': 'علي', 'animal': 'عصفور', 'plant': 'عنب', 'country': 'عمان'}},
    {'letter': 'س', 'answers': {'human': 'سارة', 'animal': 'سمكة', 'plant': 'سفرجل', 'country': 'سوريا'}},
    {'letter': 'ن', 'answers': {'human': 'نور', 'animal': 'نمر', 'plant': 'نعناع', 'country': 'النرويج'}},
    {'letter': 'ح', 'answers': {'human': 'حسن', 'animal': 'حمار', 'plant': 'حمص', 'country': 'الحجاز'}},
    {'letter': 'ر', 'answers': {'human': 'رامي', 'animal': 'رخم', 'plant': 'رمان', 'country': 'الرياض'}},
    {'letter': 'ف', 'answers': {'human': 'فاطمة', 'animal': 'فيل', 'plant': 'فلفل', 'country': 'فرنسا'}},
    {'letter': 'ك', 'answers': {'human': 'كريم', 'animal': 'كلب', 'plant': 'كرز', 'country': 'الكويت'}},
    {'letter': 'ب', 'answers': {'human': 'بدر', 'animal': 'بقرة', 'plant': 'بطيخ', 'country': 'البحرين'}},
    {'letter': 'ص', 'answers': {'human': 'صالح', 'animal': 'صقر', 'plant': 'صبار', 'country': 'الصين'}}
]

CHAIN_WORDS = [
    ['رياض', 'ضياء', 'ءامل', 'لبنان', 'نور'],
    ['سلام', 'ملك', 'كرم', 'محمد', 'دمشق'],
    ['قمر', 'رمان', 'نجم', 'ماء', 'ءيمان'],
    ['بحر', 'رمل', 'ليمون', 'نسيم', 'ماجد'],
    ['جبل', 'لحم', 'مصر', 'رياح', 'حلب']
]

SONGS_DATA = [
    {'lyrics': 'قولي أحبك كي تزيد وسامتي', 'singer': 'كاظم الساهر'},
    {'lyrics': 'على البال دوم معايا في كل مكان', 'singer': 'عمرو دياب'},
    {'lyrics': 'بحبك يا حياتي وانت عمري وسنيني', 'singer': 'تامر حسني'},
    {'lyrics': 'يا حبيبي يا عيني يا روحي يا غالي', 'singer': 'محمد عبده'},
    {'lyrics': 'انا قلبي دليلي وعيني تشوف', 'singer': 'راشد الماجد'},
    {'lyrics': 'حبك نار وحنيني زاد', 'singer': 'عبدالمجيد عبدالله'},
    {'lyrics': 'يا طير يا طاير يا رايح على بلادي', 'singer': 'وديع الصافي'},
    {'lyrics': 'احلى ما في الدنيا انك تحب', 'singer': 'وائل كفوري'},
    {'lyrics': 'قلبي يا قلبي عشقك يا عيني', 'singer': 'نانسي عجرم'},
    {'lyrics': 'خلاص سلمت وقلبي حبها', 'singer': 'ماجد المهندس'}
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
    {'items': ['ثانية', 'دقيقة', 'ساعة', 'يوم'], 'order': ['ثانية', 'دقيقة', 'ساعة', 'يوم'], 'type': 'من الأصغر للأكبر'},
    {'items': ['كيلو', 'جرام', 'ملي', 'طن'], 'order': ['ملي', 'جرام', 'كيلو', 'طن'], 'type': 'من الأصغر للأكبر'},
    {'items': ['قرن', 'عام', 'شهر', 'أسبوع'], 'order': ['أسبوع', 'شهر', 'عام', 'قرن'], 'type': 'من الأصغر للأكبر'},
    {'items': ['محيط', 'بحر', 'نهر', 'جدول'], 'order': ['جدول', 'نهر', 'بحر', 'محيط'], 'type': 'من الأصغر للأكبر'},
    {'items': ['جبل', 'هضبة', 'تل', 'سهل'], 'order': ['سهل', 'تل', 'هضبة', 'جبل'], 'type': 'من الأصغر للأكبر'}
]

BUILD_DATA = [
    {'letters': 'م ح م د ل ي', 'words': ['محمد', 'ليمون', 'محمل']},
    {'letters': 'ر ي ا ض س م', 'words': ['رياض', 'مريض', 'رماد']},
    {'letters': 'ك ت ا ب ر م', 'words': ['كتاب', 'مكتب', 'بركة']},
    {'letters': 'ق ل م ر س ي', 'words': ['قلم', 'رسم', 'قمر']},
    {'letters': 'ش م س ر ق ي', 'words': ['شمس', 'شرق', 'قمر']}
]

# ============= دوال إنشاء البطاقات =============
def create_game_card(title, question, current, total, emoji="🎮"):
    """إنشاء بطاقة لعبة موحدة"""
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": COLORS['bg'],
            "paddingAll": "0px",
            "contents": [{
                "type": "box",
                "layout": "vertical",
                "backgroundColor": COLORS['topbg'],
                "paddingTop": "35px",
                "paddingBottom": "140px",
                "contents": [{
                    "type": "box",
                    "layout": "vertical",
                    "cornerRadius": "25px",
                    "backgroundColor": COLORS['bg'],
                    "paddingAll": "0px",
                    "offsetTop": "55px",
                    "borderWidth": "2px",
                    "borderColor": COLORS['border'],
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "paddingAll": "24px",
                            "paddingBottom": "20px",
                            "backgroundColor": COLORS['card'],
                            "cornerRadius": "25px 25px 0px 0px",
                            "contents": [
                                {"type": "text", "text": f"{emoji} {title}", "weight": "bold", "size": "xl", "align": "center", "color": COLORS['glow']},
                                {"type": "text", "text": f"السؤال {current} من {total}", "size": "sm", "align": "center", "color": COLORS['text2'], "margin": "sm"}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "height": "6px",
                            "backgroundColor": COLORS['sep'],
                            "contents": [{
                                "type": "box",
                                "layout": "vertical",
                                "backgroundColor": COLORS['cyan'],
                                "width": f"{(current/total)*100}%",
                                "height": "6px"
                            }]
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "paddingAll": "24px",
                            "spacing": "lg",
                            "contents": [
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "backgroundColor": COLORS['glass'],
                                    "cornerRadius": "18px",
                                    "paddingAll": "22px",
                                    "borderWidth": "1px",
                                    "borderColor": COLORS['border'],
                                    "contents": [
                                        {"type": "text", "text": question, "size": "lg", "color": COLORS['text'], "align": "center", "wrap": True}
                                    ]
                                },
                                {"type": "separator", "color": COLORS['sep'], "margin": "lg"},
                                {
                                    "type": "box",
                                    "layout": "horizontal",
                                    "spacing": "md",
                                    "margin": "lg",
                                    "contents": [
                                        {"type": "button", "action": {"type": "message", "label": "💡 لمح", "text": "لمح"}, "style": "secondary", "color": "#FFFFFF", "height": "md"},
                                        {"type": "button", "action": {"type": "message", "label": "📝 جاوب", "text": "جاوب"}, "style": "primary", "color": COLORS['cyan'], "height": "md"}
                                    ]
                                }
                            ]
                        }
                    ]
                }]
            }]
        }
    }

def create_results_card(player_scores, game_name):
    """إنشاء بطاقة النتائج النهائية"""
    if not player_scores:
        return TextSendMessage(text="⚠️ لم يشارك أحد في اللعبة")
    
    sorted_players = sorted(player_scores.items(), key=lambda x: x[1]['score'], reverse=True)
    rank_emojis = {1: "🥇", 2: "🥈", 3: "🥉"}
    
    winners_content = []
    for idx, (user_id, data) in enumerate(sorted_players[:5], 1):
        emoji = rank_emojis.get(idx, f"{idx}️⃣")
        winners_content.append({
            "type": "box",
            "layout": "horizontal",
            "backgroundColor": COLORS['glass'],
            "cornerRadius": "12px",
            "paddingAll": "14px",
            "margin": "sm" if idx > 1 else "none",
            "contents": [
                {"type": "text", "text": emoji, "size": "xl", "flex": 0},
                {"type": "text", "text": data['name'], "size": "md", "color": COLORS['text'], "flex": 3, "margin": "md"},
                {"type": "text", "text": f"{data['score']} 🏆", "size": "md", "color": COLORS['cyan'], "align": "end", "flex": 1}
            ]
        })
    
    card = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": COLORS['bg'],
            "paddingAll": "0px",
            "contents": [{
                "type": "box",
                "layout": "vertical",
                "backgroundColor": COLORS['topbg'],
                "paddingTop": "35px",
                "paddingBottom": "140px",
                "contents": [{
                    "type": "box",
                    "layout": "vertical",
                    "cornerRadius": "25px",
                    "backgroundColor": COLORS['bg'],
                    "paddingAll": "28px",
                    "offsetTop": "55px",
                    "borderWidth": "2px",
                    "borderColor": COLORS['border'],
                    "contents": [
                        {"type": "text", "text": "🎉 انتهت اللعبة!", "weight": "bold", "size": "xxl", "align": "center", "color": COLORS['glow']},
                        {"type": "separator", "color": COLORS['sep'], "margin": "lg"},
                        {"type": "text", "text": "🏆 لوحة الصدارة", "size": "lg", "align": "center", "color": COLORS['text'], "margin": "lg"},
                        {"type": "box", "layout": "vertical", "margin": "lg", "contents": winners_content},
                        {"type": "button", "action": {"type": "message", "label": "🔄 لعب مرة أخرى", "text": game_name}, "style": "primary", "color": COLORS['cyan'], "height": "md", "margin": "xl"}
                    ]
                }]
            }]
        }
    }
    return FlexSendMessage(alt_text="النتائج النهائية", contents=card)

# ============= الفئة الأساسية للألعاب =============
class BaseGame:
    """الفئة الأساسية لجميع الألعاب"""
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.C = COLORS
        self.questions = []
        self.current_question = None
        self.hints_used = 0
        self.question_number = 0
        self.total_questions = 5
        self.player_scores = {}
        self.game_name = "اللعبة"
        self.game_emoji = "🎮"

    def start_game(self):
        """بدء اللعبة"""
        self.question_number = 0
        self.player_scores = {}
        self.hints_used = 0
        return self.next_question()

    def next_question(self):
        """السؤال التالي - يجب تنفيذها في الفئات المشتقة"""
        raise NotImplementedError

    def get_hint(self):
        """الحصول على تلميح - يجب تنفيذها في الفئات المشتقة"""
        raise NotImplementedError

    def show_answer(self):
        """عرض الإجابة الصحيحة - يجب تنفيذها في الفئات المشتقة"""
        raise NotImplementedError

    def check_answer(self, answer, user_id, display_name):
        """التحقق من الإجابة - يجب تنفيذها في الفئات المشتقة"""
        raise NotImplementedError

    def get_final_results(self):
        """الحصول على النتائج النهائية"""
        return create_results_card(self.player_scores, self.game_name)

    def add_points(self, user_id, display_name, points):
        """إضافة نقاط للاعب"""
        if user_id not in self.player_scores:
            self.player_scores[user_id] = {'name': display_name, 'score': 0}
        self.player_scores[user_id]['score'] += points

# ============= 1. لعبة الضد =============
class OppositeGame(BaseGame):
    def __init__(self, line_bot_api):
        super().__init__(line_bot_api)
        self.game_name = "الضد"
        self.game_emoji = "🎯"
        self.all_questions = OPPOSITE_DATA

    def start_game(self):
        self.questions = random.sample(self.all_questions, min(self.total_questions, len(self.all_questions)))
        return super().start_game()

    def next_question(self):
        if self.question_number >= self.total_questions:
            return None
        self.current_question = self.questions[self.question_number]
        self.question_number += 1
        self.hints_used = 0
        
        question_text = f"ما هو عكس:\n{self.current_question['word']}"
        card = create_game_card(self.game_name, question_text, self.question_number, self.total_questions, self.game_emoji)
        return FlexSendMessage(alt_text=f"السؤال {self.question_number} - {self.game_name}", contents=card)

    def get_hint(self):
        if not self.current_question:
            return None
        opposite = self.current_question['opposite']
        hint_text = f"{opposite[0]} " + "_ " * (len(opposite) - 1)
        self.hints_used += 1
        return TextSendMessage(text=f"💡 تلميح:\n{hint_text}\nعدد الحروف: {len(opposite)}")

    def show_answer(self):
        if not self.current_question:
            return None
        return TextSendMessage(text=f"📝 الإجابة الصحيحة:\n{self.current_question['opposite']}")

    def check_answer(self, answer, user_id, display_name):
        if not self.current_question:
            return None
        if normalize_arabic(answer) == normalize_arabic(self.current_question['opposite']):
            points = 2 if self.hints_used == 0 else 1
            self.add_points(user_id, display_name, points)
            return {'response': TextSendMessage(text=f"✅ إجابة صحيحة! +{points} نقطة"), 'correct': True}
        return None

# ============= 2. لعبة الأغنية =============
class SongGame(BaseGame):
    def __init__(self, line_bot_api):
        super().__init__(line_bot_api)
        self.game_name = "الأغنية"
        self.game_emoji = "🎵"
        self.all_questions = SONGS_DATA

    def start_game(self):
        self.questions = random.sample(self.all_questions, min(self.total_questions, len(self.all_questions)))
        return super().start_game()

    def next_question(self):
        if self.question_number >= self.total_questions:
            return None
        self.current_question = self.questions[self.question_number]
        self.question_number += 1
        self.hints_used = 0
        
        question_text = f"🎤 {self.current_question['lyrics']}\n\nمن المغني؟"
        card = create_game_card(self.game_name, question_text, self.question_number, self.total_questions, self.game_emoji)
        return FlexSendMessage(alt_text=f"السؤال {self.question_number} - {self.game_name}", contents=card)

    def get_hint(self):
        if not self.current_question:
            return None
        singer = self.current_question['singer']
        hint_text = f"{singer[0]} " + "_ " * (len(singer) - 1)
        self.hints_used += 1
        return TextSendMessage(text=f"💡 تلميح:\n{hint_text}\nعدد الحروف: {len(singer)}")

    def show_answer(self):
        if not self.current_question:
            return None
        return TextSendMessage(text=f"📝 الإجابة الصحيحة:\n{self.current_question['singer']}")

    def check_answer(self, answer, user_id, display_name):
        if not self.current_question:
            return None
        if normalize_arabic(answer) == normalize_arabic(self.current_question['singer']):
            points = 2 if self.hints_used == 0 else 1
            self.add_points(user_id, display_name, points)
            return {'response': TextSendMessage(text=f"✅ إجابة صحيحة! +{points} نقطة"), 'correct': True}
        return None

# ============= 3. لعبة سلسلة الكلمات =============
class ChainWordsGame(BaseGame):
    def __init__(self, line_bot_api):
        super().__init__(line_bot_api)
        self.game_name = "سلسلة الكلمات"
        self.game_emoji = "⛓️"
        self.current_chain = []
        self.current_index = 0

    def start_game(self):
        self.current_chain = random.choice(CHAIN_WORDS)
        self.current_index = 0
        return super().start_game()

    def next_question(self):
        if self.question_number >= self.total_questions or self.current_index >= len(self.current_chain) - 1:
            return None
        self.question_number += 1
        self.hints_used = 0
        current_word = self.current_chain[self.current_index]
        
        question_text = f"الكلمة الحالية:\n{current_word}\n\nأكتب كلمة تبدأ بحرف: {current_word[-1]}"
        card = create_game_card(self.game_name, question_text, self.question_number, self.total_questions, self.game_emoji)
        return FlexSendMessage(alt_text=f"السؤال {self.question_number} - {self.game_name}", contents=card)

    def get_hint(self):
        if self.current_index >= len(self.current_chain) - 1:
            return None
        next_word = self.current_chain[self.current_index + 1]
        hint_text = f"{next_word[0]} " + "_ " * (len(next_word) - 1)
        self.hints_used += 1
        return TextSendMessage(text=f"💡 تلميح:\n{hint_text}\nعدد الحروف: {len(next_word)}")

    def show_answer(self):
        if self.current_index >= len(self.current_chain) - 1:
            return None
        return TextSendMessage(text=f"📝 الإجابة الصحيحة:\n{self.current_chain[self.current_index + 1]}")

    def check_answer(self, answer, user_id, display_name):
        if self.current_index >= len(self.current_chain) - 1:
            return None
        next_word = self.current_chain[self.current_index + 1]
        if normalize_arabic(answer) == normalize_arabic(next_word):
            points = 2 if self.hints_used == 0 else 1
            self.add_points(user_id, display_name, points)
            self.current_index += 1
            return {'response': TextSendMessage(text=f"✅ إجابة صحيحة! +{points} نقطة"), 'correct': True}
        return None

# ============= 4. لعبة الترتيب =============
class OrderGame(BaseGame):
    def __init__(self, line_bot_api):
        super().__init__(line_bot_api)
        self.game_name = "الترتيب"
        self.game_emoji = "📊"
        self.all_questions = ORDER_DATA

    def start_game(self):
        self.questions = random.sample(self.all_questions, min(self.total_questions, len(self.all_questions)))
        return super().start_game()

    def next_question(self):
        if self.question_number >= self.total_questions:
            return None
        self.current_question = self.questions[self.question_number]
        self.question_number += 1
        self.hints_used = 0
        
        shuffled = random.sample(self.current_question['items'], len(self.current_question['items']))
        question_text = f"رتب {self.current_question['type']}:\n" + " • ".join(shuffled)
        card = create_game_card(self.game_name, question_text, self.question_number, self.total_questions, self.game_emoji)
        return FlexSendMessage(alt_text=f"السؤال {self.question_number} - {self.game_name}", contents=card)

    def get_hint(self):
        if not self.current_question:
            return None
        first_two = self.current_question['order'][:2]
        self.hints_used += 1
        return TextSendMessage(text=f"💡 تلميح:\nأول عنصرين: {first_two[0]}، {first_two[1]}")

    def show_answer(self):
        if not self.current_question:
            return None
        answer = "، ".join(self.current_question['order'])
        return TextSendMessage(text=f"📝 الإجابة الصحيحة:\n{answer}")

    def check_answer(self, answer, user_id, display_name):
        if not self.current_question:
            return None
        user_order = [normalize_arabic(item.strip()) for item in answer.replace('،', ',').split(',')]
        correct_order = [normalize_arabic(item) for item in self.current_question['order']]
        
        if user_order == correct_order:
            points = 2 if self.hints_used == 0 else 1
            self.add_points(user_id, display_name, points)
            return {'response': TextSendMessage(text=f"✅ إجابة صحيحة! +{points} نقطة"), 'correct': True}
        return None

# ============= 5. لعبة تكوين الكلمات =============
class LettersWordsGame(BaseGame):
    def __init__(self, line_bot_api):
        super().__init__(line_bot_api)
        self.game_name = "تكوين الكلمات"
        self.game_emoji = "🔤"
        self.all_questions = BUILD_DATA

    def start_game(self):
        self.questions = random.sample(self.all_questions, min(self.total_questions, len(self.all_questions)))
        return super().start_game()

    def next_question(self):
        if self.question_number >= self.total_questions:
            return None
        self.current_question = self.questions[self.question_number]
        self.question_number += 1
        self.hints_used = 0
        
        question_text = f"كوّن 3 كلمات من الحروف:\n{self.current_question['letters']}\n\nأكتب الكلمات كل واحدة في سطر"
        card = create_game_card(self.game_name, question_text, self.question_number, self.total_questions, self.game_emoji)
        return FlexSendMessage(alt_text=f"السؤال {self.question_number} - {self.game_name}", contents=card)

    def get_hint(self):
        if not self.current_question:
            return None
        first_word = self.current_question['words'][0]
        hint_text = f"{first_word[0]} " + "_ " * (len(first_word) - 1)
        self.hints_used += 1
        return TextSendMessage(text=f"💡 تلميح:\nالكلمة الأولى: {hint_text}\nعدد الحروف: {len(first_word)}")

    def show_answer(self):
        if not self.current_question:
            return None
        words = "\n".join(self.current_question['words'])
        return TextSendMessage(text=f"📝 الإجابة الصحيحة:\n{words}")

    def check_answer(self, answer, user_id, display_name):
        if not self.current_question:
            return None
        user_words = [normalize_arabic(word.strip()) for word in answer.split('\n') if word.strip()]
        correct_words = [normalize_arabic(word) for word in self.current_question['words']]
        
        if len(user_words) >= 3 and all(word in correct_words for word in user_words[:3]):
            points = 2 if self.hints_used == 0 else 1
            self.add_points(user_id, display_name, points)
            return {'response': TextSendMessage(text=f"✅ إجابة صحيحة! +{points} نقطة"), 'correct': True}
        return None

# ============= 6. لعبة إنسان حيوان نبات بلد =============
class HumanAnimalPlantGame(BaseGame):
    def __init__(self, line_bot_api):
        super().__init__(line_bot_api)
        self.game_name = "إنسان حيوان نبات بلد"
        self.game_emoji = "🎲"
        self.all_questions = LBGAME_DATA

    def start_game(self):
        self.questions = random.sample(self.all_questions, min(self.total_questions, len(self.all_questions)))
        return super().start_game()

    def next_question(self):
        if self.question_number >= self.total_questions:
            return None
        self.current_question = self.questions[self.question_number]
        self.question_number += 1
        self.hints_used = 0
        
        question_text = f"الحرف: {self.current_question['letter']}\n\nأكتب بالترتيب:\nإنسان\nحيوان\nنبات\nبلد"
        card = create_game_card(self.game_name, question_text, self.question_number, self.total_questions, self.game_emoji)
        return FlexSendMessage(alt_text=f"السؤال {self.question_number} - {self.game_name}", contents=card)

    def get_hint(self):
        if not self.current_question:
            return None
        human = self.current_question['answers']['human']
        hint_text = f"{human[0]} " + "_ " * (len(human) - 1)
        self.hints_used += 1
        return TextSendMessage(text=f"💡 تلميح:\nإنسان: {hint_text}\nعدد الحروف: {len(human)}")

    def show_answer(self):
        if not self.current_question:
            return None
        answers = self.current_question['answers']
        answer_text = f"إنسان: {answers['human']}\nحيوان: {answers['animal']}\nنبات: {answers['plant']}\nبلد: {answers['country']}"
        return TextSendMessage(text=f"📝 الإجابة الصحيحة:\n{answer_text}")

    def check_answer(self, answer, user_id, display_name):
        if not self.current_question:
            return None
        user_answers = [normalize_arabic(line.strip()) for line in answer.split('\n') if line.strip()]
        correct_answers = [
            normalize_arabic(self.current_question['answers']['human']),
            normalize_arabic(self.current_question['answers']['animal']),
            normalize_arabic(self.current_question['answers']['plant']),
            normalize_arabic(self.current_question['answers']['country'])
        ]
        
        if len(user_answers) >= 4 and user_answers[:4] == correct_answers:
            points = 2 if self.hints_used == 0 else 1
            self.add_points(user_id, display_name, points)
            return {'response': TextSendMessage(text=f"✅ إجابة صحيحة! +{points} نقطة"), 'correct': True}
        return None

# ============= 7. لعبة أسرع =============
class FastGame(BaseGame):
    def __init__(self, line_bot_api):
        super().__init__(line_bot_api)
        self.game_name = "أسرع"
        self.game_emoji = "⏱️"
        self.all_questions = FAST_WORDS
        self.question_time = 0

    def start_game(self):
        self.questions = random.sample(self.all_questions, min(self.total_questions, len(self.all_questions)))
        return super().start_game()

    def next_question(self):
        if self.question_number >= self.total_questions:
            return None
        self.current_question = self.questions[self.question_number]
        self.question_number += 1
        self.hints_used = 0
        self.question_time = time.time()
        
        question_text = f"أكمل الجملة:\n{self.current_question['q']}"
        card = create_game_card(self.game_name, question_text, self.question_number, self.total_questions, self.game_emoji)
        return FlexSendMessage(alt_text=f"السؤال {self.question_number} - {self.game_name}", contents=card)

    def get_hint(self):
        if not self.current_question:
            return None
        answer = self.current_question['a']
        hint_text = f"{answer[0]} " + "_ " * (len(answer) - 1)
        self.hints_used += 1
        return TextSendMessage(text=f"💡 تلميح:\n{hint_text}")

    def show_answer(self):
        if not self.current_question:
            return None
        return TextSendMessage(text=f"📝 الإجابة الصحيحة:\n{self.current_question['a']}")

    def check_answer(self, answer, user_id, display_name):
        if not self.current_question:
            return None
        if normalize_arabic(answer) == normalize_arabic(self.current_question['a']):
            elapsed = time.time() - self.question_time
            points = 5 if elapsed < 5 else (4 if elapsed < 10 else (3 if elapsed < 15 else 2))
            if self.hints_used > 0:
                points = max(1, points // 2)
            self.add_points(user_id, display_name, points)
            return {'response': TextSendMessage(text=f"✅ إجابة صحيحة! +{points} نقطة"), 'correct': True}
        return None

# ============= 8. لعبة التوافق =============
class CompatGame(BaseGame):
    def __init__(self, line_bot_api):
        super().__init__(line_bot_api)
        self.game_name = "التوافق"
        self.game_emoji = "💕"
        self.total_questions = 1

    def start_game(self):
        msg = TextSendMessage(text="💕 لعبة التوافق\n\nاكتب اسمين لحساب نسبة التوافق\nمثال:\nأحمد\nفاطمة")
        return msg

    def next_question(self):
        return None

    def get_hint(self):
        return TextSendMessage(text="💡 اكتب اسمين فقط، كل اسم في سطر")

    def show_answer(self):
        return TextSendMessage(text="📝 لا توجد إجابة صحيحة لهذه اللعبة")

    def check_answer(self, answer, user_id, display_name):
        lines = [line.strip() for line in answer.split('\n') if line.strip()]
        
        if len(lines) != 2:
            return None
        
        name1, name2 = sorted(lines)
        seed = sum(ord(c) for c in name1 + name2)
        random.seed(seed)
        compat = random.randint(1, 100)
        
        hearts = '❤️' * (compat // 10)
        message = f"💕 نسبة التوافق بين {lines[0]} و {lines[1]}:\n\n{hearts} {compat}%"
        
        return {'response': TextSendMessage(text=message), 'correct': True, 'end_game': True}

# ============= دوال المساعدة الرئيسية =============
def start_game(game_type, line_bot_api):
    """بدء لعبة حسب النوع"""
    games_map = {
        'opposite': OppositeGame,
        'song': SongGame,
        'chain': ChainWordsGame,
        'order': OrderGame,
        'build': LettersWordsGame,
        'lbgame': HumanAnimalPlantGame,
        'fast': FastGame,
        'compat': CompatGame
    }
    
    if game_type in games_map:
        game = games_map[game_type](line_bot_api)
        first_msg = game.start_game()
        return first_msg, game
    return None, None

def check_game_answer(game, answer, user_id, display_name):
    """التحقق من الإجابة"""
    if game:
        result = game.check_answer(answer, user_id, display_name)
        if result and result.get('correct'):
            if result.get('end_game'):
                return result
            next_q = game.next_question()
            if next_q:
                return {'response': result['response'], 'next': next_q, 'correct': True}
            else:
                return {'response': result['response'], 'final': game.get_final_results(), 'correct': True}
        return result
    return None

def get_game_hint(game):
    """الحصول على تلميح"""
    if game:
        return game.get_hint()
    return None

def show_game_answer(game):
    """عرض الإجابة الصحيحة"""
    if game:
        answer_msg = game.show_answer()
        next_q = game.next_question()
        if next_q:
            return {'answer': answer_msg, 'next': next_q}
        else:
            return {'answer': answer_msg, 'final': game.get_final_results()}
    return None

# ============= دوال التوافق مع الكود القديم =============
def create_game_card_old(title, question, current, total, show_buttons=True):
    """للتوافق مع الكود القديم"""
    return create_game_card(title, question, current, total)

def normalize_text(text):
    """للتوافق مع الكود القديم"""
    return normalize_arabic(text)
