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
        
        self.songs = [
            {"lyrics": "أنا بلياك إذا أرمش إلك تنزل ألف دمعة", "singer": "ماجد المهندس"},
            {"lyrics": "يا بعدهم كلهم .. يا سراجي بينهم", "singer": "عبدالمجيد عبدالله"},
            {"lyrics": "أنا لحبيبي وحبيبي إلي", "singer": "فيروز"},
            {"lyrics": "قولي أحبك كي تزيد وسامتي", "singer": "كاظم الساهر"},
            {"lyrics": "كيف أبيّن لك شعوري دون ما أحكي", "singer": "عايض"},
            {"lyrics": "أريد الله يسامحني لان أذيت نفسي", "singer": "رحمة رياض"},
            {"lyrics": "جنّنت قلبي بحبٍ يلوي ذراعي", "singer": "ماجد المهندس"},
            {"lyrics": "واسِع خيالك إكتبه آنا بكذبك مُعجبه", "singer": "شمة حمدان"},
            {"lyrics": "خذني من ليلي لليلك", "singer": "عبادي الجوهر"},
            {"lyrics": "أنا عندي قلب واحد", "singer": "حسين الجسمي"},
            {"lyrics": "احس اني لقيتك بس عشان تضيع مني", "singer": "عبدالمجيد عبدالله"},
            {"lyrics": "قال الوداع و مقصده يجرح القلب", "singer": "راشد الماجد"},
            {"lyrics": "يا بنات يا بنات", "singer": "نانسي عجرم"},
            {"lyrics": "احبك موت كلمة مالها تفسير", "singer": "ماجد المهندس"},
            {"lyrics": "خلني مني طمني عليك", "singer": "نوال الكويتية"},
            {"lyrics": "رحت عني ما قويت جيت لك لاتردني", "singer": "عبدالمجيد عبدالله"},
            {"lyrics": "انسى هالعالم ولو هم يزعلون", "singer": "عباس ابراهيم"},
            {"lyrics": "مشاعر تشاور تودع تسافر", "singer": "شيرين"},
            {"lyrics": "جلست والخوف بعينيها تتأمل فنجاني", "singer": "عبد الحليم حافظ"},
            {"lyrics": "اسخر لك غلا وتشوفني مقصر", "singer": "عايض"}
        ]
        random.shuffle(self.songs)
    
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
        self.current_song = random.choice(self.songs)
        self.answered = False
        return TextSendMessage(text=f"▪️ لعبة الأغنية\n\n{self.current_song['lyrics']}\n\nمن المغني؟")
    
    def check_answer(self, text, user_id, display_name):
        if self.answered:
            return None
        
        text_normalized = self.normalize_text(text)
        singer_normalized = self.normalize_text(self.current_song['singer'])
        
        if text in ['لمح', 'تلميح']:
            singer_name = self.current_song['singer']
            return {
                'correct': False,
                'response': TextSendMessage(text=f"▪️ تلميح\n\nيبدأ بحرف: {singer_name[0]}")
            }
        
        if text in ['جاوب', 'الجواب', 'الحل']:
            self.answered = True
            return {
                'correct': False,
                'game_over': True,
                'response': TextSendMessage(text=f"▪️ الإجابة الصحيحة\n\n{self.current_song['singer']}")
            }
        
        if text_normalized == singer_normalized or singer_normalized in text_normalized:
            self.answered = True
            points = 2
            if user_id not in self.scores:
                self.scores[user_id] = {'name': display_name, 'score': 0}
            self.scores[user_id]['score'] += points
            return {
                'correct': True,
                'points': points,
                'won': True,
                'game_over': True,
                'response': TextSendMessage(text=f"▪️ صحيح {display_name}\n+{points} نقطة")
            }
        
        return None
