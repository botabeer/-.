from linebot.models import TextSendMessage
import random
import re

class SongGame:
    def __init__(self, line_bot_api, use_ai=False, ask_ai=None):
        self.line_bot_api = line_bot_api
        self.use_ai = use_ai
        self.ask_ai = ask_ai
        self.current_song = None
        self.scores = {}
        self.answered = False

        self.all_songs = [
            {"lyrics": "رجعت لي أيام الماضي معاك", "singer": "أم كلثوم"},
            {"lyrics": "جلست والخوف بعينيها تتأمل فنجاني", "singer": "عبد الحليم حافظ"},
            {"lyrics": "تملي معاك ولو حتى بعيد عني", "singer": "عمرو دياب"},
            {"lyrics": "يا بنات يا بنات", "singer": "نانسي عجرم"},
            {"lyrics": "قولي أحبك كي تزيد وسامتي", "singer": "كاظم الساهر"},
            {"lyrics": "أنا لحبيبي وحبيبي إلي", "singer": "فيروز"},
            {"lyrics": "حبيبي يا كل الحياة اوعدني تبقى معايا", "singer": "تامر حسني"},
            {"lyrics": "قلبي بيسألني عنك دخلك طمني وينك", "singer": "وائل كفوري"},
            {"lyrics": "كيف أبيّن لك شعوري دون ما أحكي", "singer": "عايض"},
            {"lyrics": "اسخر لك غلا وتشوفني مقصر", "singer": "عايض"},
            {"lyrics": "رحت عني ما قويت جيت لك لاتردني", "singer": "عبدالمجيد عبدالله"},
            {"lyrics": "خذني من ليلي لليلك", "singer": "عبادي الجوهر"},
            {"lyrics": "تدري كثر ماني من البعد مخنوق", "singer": "راشد الماجد"},
            {"lyrics": "انسى هالعالم ولو هم يزعلون", "singer": "عباس ابراهيم"},
            {"lyrics": "أنا عندي قلب واحد", "singer": "حسين الجسمي"},
            {"lyrics": "منوتي ليتك معي", "singer": "محمد عبده"},
            {"lyrics": "خلنا مني طمني عليك", "singer": "نوال الكويتية"},
            {"lyrics": "أحبك ليه أنا مدري", "singer": "عبدالمجيد عبدالله"},
            {"lyrics": "أمر الله أقوى أحبك والعقل واعي", "singer": "ماجد المهندس"},
            {"lyrics": "الحب يتعب من يدله والله في حبه بلاني", "singer": "راشد الماجد"}
        ]

        random.shuffle(self.all_songs)

    def normalize_text(self, text):
        if not text:
            return ""
        text = text.strip().lower()
        text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
        text = text.replace('ؤ', 'و').replace('ئ', 'ي').replace('ء', '')
        text = text.replace('ة', 'ه').replace('ى', 'ي')
        text = re.sub(r'[\u064B-\u065F]', '', text)
        text = re.sub(r'\s+', '', text)
        return text

    def start_game(self):
        self.current_song = random.choice(self.all_songs)
        self.answered = False
        return TextSendMessage(text=f"🎵 لعبة الأغنية\n\nأغنية:\n{self.current_song['lyrics']}\n\nمن المغني؟")

    def check_answer(self, text, user_id, display_name):
        if self.answered:
            return None

        text_normalized = self.normalize_text(text)
        singer_normalized = self.normalize_text(self.current_song['singer'])

        if text in ['لمح', 'تلميح']:
            singer = self.current_song['singer']
            words = singer.split()
            word_count = "كلمة واحدة" if len(words) == 1 else "كلمتين"
            first_letter = singer[0]
            char_count = len(singer.replace(' ', ''))
            
            hint = f"تلميح:\n• يبدأ بحرف: {first_letter}\n• عدد الحروف: {char_count}\n• الاسم مكون من: {word_count}"
            return {'correct': False, 'response': TextSendMessage(text=hint)}
        
        if text in ['جاوب', 'الجواب', 'الحل']:
            self.answered = True
            return {
                'correct': False,
                'game_over': True,
                'response': TextSendMessage(
                    text=f"الإجابة الصحيحة:\n{self.current_song['singer']}\n\nأغنية:\n{self.current_song['lyrics']}"
                )
            }
        
        if text_normalized == singer_normalized or singer_normalized in text_normalized:
            self.answered = True
            points = 10
            if user_id not in self.scores:
                self.scores[user_id] = {'name': display_name, 'score': 0}
            self.scores[user_id]['score'] += points
            return {
                'correct': True,
                'points': points,
                'won': True,
                'game_over': True,
                'response': TextSendMessage(
                    text=f"✓ إجابة صحيحة يا {display_name}\n+{points} نقطة\n\nالمغني: {self.current_song['singer']}\nأغنية: {self.current_song['lyrics']}"
                )
            }
        return None
