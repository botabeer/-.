import random
from linebot.models import TextSendMessage, FlexSendMessage
from utils import normalize_text, create_game_card, create_hint_card, create_answer_card, create_results_card, COLORS

class SongGame:
    def __init__(self):
        self.all_songs = [
            {"lyrics": "قولي أحبك كي تزيد وسامتي", "singer": "كاظم الساهر"},
            {"lyrics": "يا طيور الطايرة فوق الحدود", "singer": "عبد المجيد عبدالله"},
            {"lyrics": "أنا لو عشقت حبيبي بجنون", "singer": "نجوى كرم"},
            {"lyrics": "حبيبي يا نور العين", "singer": "عمرو دياب"},
            {"lyrics": "على مودك يا بعد عمري", "singer": "محمد عبده"},
            {"lyrics": "تعبت من الصبر والانتظار", "singer": "راشد الماجد"},
            {"lyrics": "يا حبيبي كل اللي ودك فيه", "singer": "أصالة"},
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
            {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": COLORS['glass'],
                "cornerRadius": "20px",
                "paddingAll": "28px",
                "borderWidth": "2px",
                "borderColor": COLORS['border'],
                "contents": [
                    {"type": "text", "text": "كلمات الأغنية:", "size": "lg", "color": COLORS['text2'], "align": "center"},
                    {"type": "text", "text": self.current_song['lyrics'], "size": "xl", "weight": "bold", "color": COLORS['cyan'], "align": "center", "margin": "lg", "wrap": True}
                ]
            },
            {"type": "text", "text": "من المغني؟", "size": "lg", "color": COLORS['text'], "align": "center", "margin": "lg"}
        ]
        
        card = create_game_card("لعبة الأغنية", self.question_number, self.total_questions, content)
        return FlexSendMessage(alt_text=f"السؤال {self.question_number} - لعبة الأغنية", contents=card)

    def get_hint(self):
        if not self.current_song:
            return None
        singer = self.current_song['singer']
        hint_text = f"أول حرف: {singer[0]} " + "_ " * (len(singer) - 1)
        extra = f"عدد الحروف: {len(singer)}"
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
            return {'response': TextSendMessage(text=f"إجابة صحيحة +{points} نقطة"), 'points': points, 'correct': True}
        return None

    def get_final_results(self):
        return create_results_card(self.player_scores)
