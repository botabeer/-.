import random
from linebot.models import FlexSendMessage
from utils import normalize_text, create_game_card, create_hint_card, create_answer_card, create_results_card

class LBGame:
    def __init__(self):
        self.all_questions = [
            {
                "letter": "م",
                "answers": {
                    "human": "محمد",
                    "animal": "ماعز",
                    "plant": "موز",
                    "country": "مصر"
                }
            },
            {
                "letter": "ع",
                "answers": {
                    "human": "علي",
                    "animal": "عصفور",
                    "plant": "عنب",
                    "country": "عمان"
                }
            },
            {
                "letter": "ح",
                "answers": {
                    "human": "حسن",
                    "animal": "حمار",
                    "plant": "حمص",
                    "country": "الحجاز"
                }
            },
            {
                "letter": "س",
                "answers": {
                    "human": "سالم",
                    "animal": "سمكة",
                    "plant": "سبانخ",
                    "country": "سوريا"
                }
            },
            {
                "letter": "ر",
                "answers": {
                    "human": "رامي",
                    "animal": "راكون",
                    "plant": "رمان",
                    "country": "روسيا"
                }
            },
            {
                "letter": "ن",
                "answers": {
                    "human": "نورا",
                    "animal": "نمر",
                    "plant": "نعناع",
                    "country": "النرويج"
                }
            },
            {
                "letter": "ب",
                "answers": {
                    "human": "باسم",
                    "animal": "بقرة",
                    "plant": "بطاطس",
                    "country": "البحرين"
                }
            }
        ]
        self.questions = []
        self.current_question = None
        self.hints_used = 0
        self.question_number = 0
        self.total_questions = 5
        self.player_scores = {}
        self.current_step = 0  # 0: human, 1: animal, 2: plant, 3: country
        self.user_answers = {}

    def start_game(self):
        self.questions = random.sample(self.all_questions, min(self.total_questions, len(self.all_questions)))
        self.question_number = 0
        self.player_scores = {}
        self.hints_used = 0
        self.current_step = 0
        self.user_answers = {}
        return self.next_question()

    def next_question(self):
        if self.question_number >= self.total_questions:
            return None
        
        # إذا انتقلنا لسؤال جديد
        if self.current_step == 0:
            self.current_question = self.questions[self.question_number]
            self.question_number += 1
            self.hints_used = 0
            self.user_answers = {}
        
        # تحديد نوع السؤال الحالي
        steps = ["إنسان", "حيوان", "نبات", "بلد"]
        current_type = steps[self.current_step]
        
        content = [
            {"type": "text", "text": f"🎮 لعبة: إنسان، حيوان، نبات، بلد", "size": "lg", "color": "#E8F4FF", "align": "center", "wrap": True},
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
                    {"type": "text", "text": f"الحرف: {self.current_question['letter']}", "size": "xxl", "weight": "bold", "color": "#00D9FF", "align": "center"},
                    {"type": "text", "text": f"المطلوب: {current_type}", "size": "lg", "color": "#8FB9D8", "align": "center", "margin": "md"}
                ]
            },
            {"type": "text", "text": f"اكتب {current_type} يبدأ بحرف {self.current_question['letter']}", "size": "sm", "color": "#E8F4FF", "align": "center", "margin": "lg", "wrap": True}
        ]
        
        card = create_game_card(f"🎮 لعبة - {current_type}", self.question_number, self.total_questions, content)
        return FlexSendMessage(alt_text=f"السؤال {self.question_number} - لعبة", contents=card)

    def get_hint(self):
        if not self.current_question:
            return None
        
        steps_keys = ["human", "animal", "plant", "country"]
        answer = self.current_question['answers'][steps_keys[self.current_step]]
        hint_text = f"الكلمة: {answer[0]} " + "_ " * (len(answer) - 1)
        extra = f"عدد الحروف: {len(answer)}"
        self.hints_used += 1
        return FlexSendMessage(alt_text="تلميح", contents=create_hint_card(hint_text, extra))

    def show_answer(self):
        if not self.current_question:
            return None
        steps_keys = ["human", "animal", "plant", "country"]
        answer = self.current_question['answers'][steps_keys[self.current_step]]
        return FlexSendMessage(alt_text="الإجابة الصحيحة", contents=create_answer_card(answer))

    def check_answer(self, answer, user_id, display_name):
        if not self.current_question:
            return None
        
        steps_keys = ["human", "animal", "plant", "country"]
        correct_answer = self.current_question['answers'][steps_keys[self.current_step]]
        
        if normalize_text(answer) == normalize_text(correct_answer):
            # الإجابة صحيحة للخطوة الحالية
            self.user_answers[steps_keys[self.current_step]] = answer
            self.current_step += 1
            
            # إذا انتهت جميع الخطوات
            if self.current_step >= 4:
                points = 2 if self.hints_used == 0 else 1
                if user_id not in self.player_scores:
                    self.player_scores[user_id] = {'name': display_name, 'score': 0}
                self.player_scores[user_id]['score'] += points
                self.current_step = 0
                return {'correct': True, 'points': points, 'complete': True}
            else:
                # الانتقال للخطوة التالية
                return {'correct': True, 'points': 0, 'complete': False}
        return None

    def get_final_results(self):
        return create_results_card(self.player_scores)
