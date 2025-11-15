from linebot.models import TextSendMessage
import random, re

class HumanAnimalPlantGame:
    def __init__(self, line_bot_api, use_ai=False, ask_ai=None):
        self.line_bot_api = line_bot_api
        self.current_letter = None
        self.answers = {}
        self.scores = {}
        self.letters = ['أ','ب','ت','ج','ح','خ','د','ر','ز','س','ش','ص','ع','ف','ق','ك','ل','م','ن','ه','و','ي']
    
    def normalize(self, text):
        if not text: return ""
        text = text.strip().lower()
        text = text.replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ؤ','و').replace('ئ','ي').replace('ء','').replace('ة','ه').replace('ى','ي')
        return re.sub(r'[\u064B-\u065F]', '', re.sub(r'\s+', '', text))
    
    def start_game(self):
        self.current_letter = random.choice(self.letters)
        self.answers = {}
        self.scores = {}
        return TextSendMessage(text=f"▫️ لعبة إنسان حيوان نبات بلاد\n\nالحرف: {self.current_letter}\n\nاكتب إجاباتك\nكل كلمة في سطر منفصل\n\nمثال:\nأحمد\nأسد\nأرز\nالأردن")
    
    def check_answer(self, text, user_id, name):
        if user_id in self.answers:
            return None
        
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        if len(lines) >= 4:
            valid = sum(1 for w in lines[:4] if w and w[0] == self.current_letter)
            if valid >= 4:
                points = valid * 3
                self.answers[user_id] = lines[:4]
                if user_id not in self.scores:
                    self.scores[user_id] = {'name': name, 'score': 0}
                self.scores[user_id]['score'] += points
                return {'correct': True, 'points': points, 'won': valid == 4, 'game_over': True, 'response': TextSendMessage(text=f"✓ {name}\n\nإجابات صحيحة: {valid}/4\n+{points} نقطة")}
        
        return None
