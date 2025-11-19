import random
import time
from linebot.models import FlexSendMessage
from utils import normalize_text, create_game_card, create_answer_card, create_results_card, COLORS

class FastGame:
    def __init__(self):
        self.all_words = [
            {"word": "سبحان الله", "type": "ذكر"},
            {"word": "الحمد لله", "type": "ذكر"},
            {"word": "لا إله إلا الله", "type": "ذكر"},
            {"word": "الله أكبر", "type": "ذكر"},
            {"word": "استغفر الله", "type": "ذكر"},
            {"word": "بسم الله", "type": "ذكر"},
            {"word": "لا حول ولا قوة إلا بالله", "type": "ذكر"},
            {"word": "اللهم صل على محمد", "type": "دعاء"},
            {"word": "اللهم اغفر لي", "type": "دعاء"},
            {"word": "اللهم ارحمني", "type": "دعاء"},
            {"word": "اللهم اهدني", "type": "دعاء"},
            {"word": "اللهم ارزقني", "type": "دعاء"},
            {"word": "ربنا آتنا في الدنيا حسنة", "type": "دعاء"},
            {"word": "اللهم إني أسألك الجنة", "type": "دعاء"}
        ]
        self.questions = []
        self.current_word = None
        self.question_number = 0
        self.total_questions = 5
        self.player_scores = {}
        self.start_time = None
        self.time_limit = 30  # 30 ثانية لكل سؤال

    def start_game(self):
        self.questions = random.sample(self.all_words, min(self.total_questions, len(self.all_words)))
        self.question_number = 0
        self.player_scores = {}
        return self.next_question()

    def next_question(self):
        if self.question_number >= self.total_questions:
            return None
        self.current_word = self.questions[self.question_number]
        self.question_number += 1
        self.start_time = time.time()
        
        C = COLORS
        content = [
            {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": C['glass'],
                "cornerRadius": "20px",
                "paddingAll": "28px",
                "borderWidth": "2px",
                "borderColor": C['border'],
                "contents": [
                    {"type": "text", "text": "⏱️ اكتب أسرع:", "size": "lg", "color": C['text2'], "align": "center"},
                    {"type": "text", "text": self.current_word['word'], "size": "xxl", "weight": "bold", "color": C['cyan'], "align": "center", "margin": "lg", "wrap": True},
                    {"type": "text", "text": f"النوع: {self.current_word['type']}", "size": "md", "color": C['text2'], "align": "center", "margin": "md"}
                ]
            },
            {"type": "text", "text": f"⏰ الوقت المتاح: {self.time_limit} ثانية", "size": "sm", "color": C['warning'], "align": "center", "margin": "lg"}
        ]
        
        card = create_game_card("⏱️ لعبة أسرع", self.question_number, self.total_questions, content)
        return FlexSendMessage(alt_text=f"السؤال {self.question_number} - لعبة أسرع", contents=card)

    def get_hint(self):
        # لا يدعم التلميحات
        return None

    def show_answer(self):
        if not self.current_word:
            return None
        return FlexSendMessage(alt_text="الإجابة الصحيحة", contents=create_answer_card(self.current_word['word']))

    def check_answer(self, answer, user_id, display_name):
        if not self.current_word or not self.start_time:
            return None
        
        # حساب الوقت المستغرق
        elapsed_time = time.time() - self.start_time
        
        # التحقق من انتهاء الوقت
        if elapsed_time > self.time_limit:
            return None
        
        # التحقق من صحة الإجابة
        if normalize_text(answer) == normalize_text(self.current_word['word']):
            # حساب النقاط بناءً على السرعة
            if elapsed_time < 5:
                points = 5  # سريع جداً
            elif elapsed_time < 10:
                points = 4
            elif elapsed_time < 15:
                points = 3
            elif elapsed_time < 20:
                points = 2
            else:
                points = 1
            
            if user_id not in self.player_scores:
                self.player_scores[user_id] = {'name': display_name, 'score': 0}
            self.player_scores[user_id]['score'] += points
            
            return {'correct': True, 'points': points, 'time': round(elapsed_time, 2)}
        return None

    def get_final_results(self):
        return create_results_card(self.player_scores)
