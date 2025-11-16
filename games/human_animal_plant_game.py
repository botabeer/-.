from linebot.models import TextSendMessage
import random
import re

class HumanAnimalPlantGame:
    def __init__(self, line_bot_api, use_ai=False, ask_ai=None):
        self.line_bot_api = line_bot_api
        self.use_ai = use_ai
        self.ask_ai = ask_ai
        self.current_letter = None
        self.answers = {}
        self.scores = {}
        
        self.letters = ['أ','ب','ت','ث','ج','ح','خ','د','ذ','ر','ز','س','ش','ص','ض','ط','ظ','ع','غ','ف','ق','ك','ل','م','ن','ه','و','ي']
    
    def start_game(self):
        self.current_letter = random.choice(self.letters)
        self.answers = {}
        self.scores = {}
        return TextSendMessage(text=f"▪️ لعبة إنسان حيوان نبات بلاد\n\nالحرف: {self.current_letter}")
    
    def check_answer(self, text, user_id, display_name):
        if user_id in self.answers:
            return None
        
        lines = text.strip().split('\n')
        
        if len(lines) >= 4:
            words = [line.strip() for line in lines[:4]]
            valid = sum(1 for w in words if w and w[0] == self.current_letter)
            
            if valid == 4:
                points = valid * 2
                self.answers[user_id] = words
                if user_id not in self.scores:
                    self.scores[user_id] = {'name': display_name, 'score': 0}
                self.scores[user_id]['score'] += points
                
                return {
                    "correct": True,
                    "points": points,
                    "won": True,
                    "game_over": True,
                    "response": TextSendMessage(text=f"▪️ ممتاز {display_name}\nإجابات صحيحة 4/4\n+{points} نقطة")
                }
        
        return None
