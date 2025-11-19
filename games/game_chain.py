import random
from linebot.models import FlexSendMessage
from utils import normalize_text, create_game_card, create_hint_card, create_answer_card, create_results_card

class ChainWordsGame:
    def __init__(self):
        self.words_chain = [
            ["رياض", "ضياء", "ءامل", "لبنان", "نور"],
            ["سلام", "ملك", "كرم", "محمد", "دمشق"],
            ["قمر", "رمان", "نجم", "ماء", "ءيمان"],
            ["بحر", "رمل", "ليمون", "نسيم", "ماجد"],
            ["جبل", "لحم", "مصر", "رياح", "حلب"],
            ["باب", "بطل", "لون", "نهر", "روح"],
            ["كتاب", "برق", "قلب", "بحر", "رمز"],
            ["صباح", "حلم", "ملك", "كوب", "بحر"]
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
            {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#1a1f3a90",
                "cornerRadius": "20px",
                "paddingAll": "28px",
                "borderWidth": "2px",
                "borderColor": "#00D9FF50",
                "contents": [
                    {"type": "text", "text": "الكلمة الحالية:", "size": "lg", "color": "#8FB9D8", "align": "center"},
                    {"type": "text", "text": current_word, "size": "xxl", "weight": "bold", "color": "#00D9FF", "align": "center", "margin": "lg"}
                ]
            },
            {"type": "text", "text": f"⛓️ اكتب كلمة تبدأ بحرف: {current_word[-1]}", "size": "lg", "color": "#E8F4FF", "align": "center", "margin": "lg", "wrap": True}
        ]
        
        card = create_game_card("⛓️ سلسلة الكلمات", self.question_number, self.total_questions, content)
        return FlexSendMessage(alt_text=f"السؤال {self.question_number} - سلسلة الكلمات", contents=card)

    def get_hint(self):
        if self.current_index >= len(self.current_chain) - 1:
            return None
        next_word = self.current_chain[self.current_index + 1]
        hint_text = f"الكلمة: {next_word[0]} " + "_ " * (len(next_word) - 1)
        extra = f"عدد الحروف: {len(next_word)}"
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
            return {'correct': True, 'points': points}
        return None

    def get_final_results(self):
        return create_results_card(self.player_scores)
