import random
from linebot.models import TextSendMessage, FlexSendMessage
from utils import normalize_text, create_game_card, create_hint_card, create_answer_card, create_results_card, COLORS

class OrderGame:
    def __init__(self):
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
            {"type": "text", "text": f"رتب العناصر {self.current_question['type']}", "size": "lg", "color": COLORS['text'], "align": "center", "wrap": True},
            {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": COLORS['glass'],
                "cornerRadius": "20px",
                "paddingAll": "28px",
                "margin": "lg",
                "borderWidth": "2px",
                "borderColor": COLORS['border'],
                "contents": [
                    {"type": "text", "text": " - ".join(shuffled), "size": "xl", "weight": "bold", "color": COLORS['cyan'], "align": "center", "wrap": True}
                ]
            },
            {"type": "text", "text": "أكتب الترتيب مفصولا بفواصل", "size": "sm", "color": COLORS['text2'], "align": "center", "margin": "lg", "wrap": True}
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
            return {'response': TextSendMessage(text=f"إجابة صحيحة +{points} نقطة"), 'points': points, 'correct': True}
        return None

    def get_final_results(self):
        return create_results_card(self.player_scores)
