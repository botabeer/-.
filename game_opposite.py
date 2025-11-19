import random
from linebot.models import FlexSendMessage
from utils import normalize_text, create_game_card, create_hint_card, create_answer_card, create_results_card

class OppositeGame:
    def __init__(self):
        self.all_words = [
            {"word": "كبير", "opposite": "صغير"},
            {"word": "طويل", "opposite": "قصير"},
            {"word": "سريع", "opposite": "بطيء"},
            {"word": "حار", "opposite": "بارد"},
            {"word": "قوي", "opposite": "ضعيف"},
            {"word": "غني", "opposite": "فقير"},
            {"word": "سعيد", "opposite": "حزين"},
            {"word": "نظيف", "opposite": "وسخ"},
            {"word": "جديد", "opposite": "قديم"},
            {"word": "صعب", "opposite": "سهل"},
            {"word": "ثقيل", "opposite": "خفيف"},
            {"word": "واسع", "opposite": "ضيق"},
            {"word": "عميق", "opposite": "ضحل"},
            {"word": "شجاع", "opposite": "جبان"},
            {"word": "ذكي", "opposite": "غبي"},
            {"word": "نشيط", "opposite": "كسول"},
            {"word": "جميل", "opposite": "قبيح"},
            {"word": "مظلم", "opposite": "مضيء"},
            {"word": "عالي", "opposite": "منخفض"},
            {"word": "رطب", "opposite": "جاف"}
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
        
        content = [{
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#1a1f3a90",
            "cornerRadius": "20px",
            "paddingAll": "28px",
            "borderWidth": "2px",
            "borderColor": "#00D9FF50",
            "contents": [
                {"type": "text", "text": "ما هو عكس:", "size": "lg", "color": "#8FB9D8", "align": "center"},
                {"type": "text", "text": self.current_word['word'], "size": "xxl", "weight": "bold", "color": "#00D9FF", "align": "center", "margin": "lg"}
            ]
        }]
        
        card = create_game_card("🎯 لعبة الضد", self.question_number, self.total_questions, content)
        return FlexSendMessage(alt_text=f"السؤال {self.question_number} - لعبة الضد", contents=card)

    def get_hint(self):
        if not self.current_word:
            return None
        opposite = self.current_word['opposite']
        hint_text = f"أول حرف: {opposite[0]} " + "_ " * (len(opposite) - 1)
        extra = f"عدد الحروف: {len(opposite)}"
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
            return {'correct': True, 'points': points}
        return None

    def get_final_results(self):
        return create_results_card(self.player_scores)
