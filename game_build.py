import random
from linebot.models import FlexSendMessage
from utils import normalize_text, create_game_card, create_hint_card, create_answer_card, create_results_card

class BuildGame:
    def __init__(self):
        self.all_questions = [
            {
                "letters": ["م", "ح", "م", "د", "ل", "ح"],
                "words": ["محمد", "لحم", "حمد"]
            },
            {
                "letters": ["س", "ا", "ل", "م", "ع", "ل"],
                "words": ["سالم", "علم", "عسل"]
            },
            {
                "letters": ["ن", "و", "ر", "ق", "م", "ر"],
                "words": ["نور", "قمر", "رمق"]
            },
            {
                "letters": ["ب", "ح", "ر", "ح", "ب", "ر"],
                "words": ["بحر", "حرب", "برح"]
            },
            {
                "letters": ["ك", "ت", "ا", "ب", "ت", "ك"],
                "words": ["كتاب", "باتك", "تكب"]
            },
            {
                "letters": ["ج", "ب", "ل", "ب", "ل", "ج"],
                "words": ["جبل", "بلج", "جلب"]
            },
            {
                "letters": ["ش", "م", "س", "م", "س", "ش"],
                "words": ["شمس", "مسش", "شسم"]
            }
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
        
        letters_display = " - ".join(self.current_question['letters'])
        
        content = [
            {"type": "text", "text": "🔤 كون 3 كلمات من الحروف التالية:", "size": "lg", "color": "#E8F4FF", "align": "center", "wrap": True},
            {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#1a1f3a90",
                "cornerRadius": "20px",
                "paddingAll": "28px",
                "margin": "lg",
                "borderWidth": "2px",
                "borderColor": "#00D9FF50",
                "contents": [
                    {"type": "text", "text": letters_display, "size": "xxl", "weight": "bold", "color": "#00D9FF", "align": "center", "wrap": True}
                ]
            },
            {"type": "text", "text": "اكتب الكلمات الثلاث (كل كلمة في سطر منفصل)", "size": "sm", "color": "#8FB9D8", "align": "center", "margin": "lg", "wrap": True}
        ]
        
        card = create_game_card("🔤 تكوين كلمات", self.question_number, self.total_questions, content)
        return FlexSendMessage(alt_text=f"السؤال {self.question_number} - تكوين كلمات", contents=card)

    def get_hint(self):
        if not self.current_question:
            return None
        first_word = self.current_question['words'][0]
        hint_text = f"الكلمة الأولى: {first_word[0]} " + "_ " * (len(first_word) - 1)
        extra = f"عدد حروفها: {len(first_word)}"
        self.hints_used += 1
        return FlexSendMessage(alt_text="تلميح", contents=create_hint_card(hint_text, extra))

    def show_answer(self):
        if not self.current_question:
            return None
        answer = "\n".join(self.current_question['words'])
        return FlexSendMessage(alt_text="الإجابة الصحيحة", contents=create_answer_card(answer))

    def check_answer(self, answer, user_id, display_name):
        if not self.current_question:
            return None
        
        # تقسيم الإجابة إلى كلمات
        user_words = [normalize_text(word.strip()) for word in answer.split('\n') if word.strip()]
        correct_words = [normalize_text(word) for word in self.current_question['words']]
        
        # التحقق من أن جميع الكلمات صحيحة
        if len(user_words) == 3 and set(user_words) == set(correct_words):
            points = 2 if self.hints_used == 0 else 1
            if user_id not in self.player_scores:
                self.player_scores[user_id] = {'name': display_name, 'score': 0}
            self.player_scores[user_id]['score'] += points
            return {'correct': True, 'points': points}
        return None

    def get_final_results(self):
        return create_results_card(self.player_scores)
