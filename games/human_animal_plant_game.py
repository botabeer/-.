# ============================================
# human_animal_plant_game.py - لعبة إنسان حيوان نبات
# ============================================

from linebot.models import TextSendMessage
import random
import re

class HumanAnimalPlantGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.current_letter = None
        self.answers = {}
        self.scores = {}
        self.letters = ['أ', 'ب', 'ت', 'ث', 'ج', 'ح', 'خ', 'د', 'ذ', 'ر', 'ز', 'س', 'ش', 'ص', 'ض', 'ط', 'ظ', 'ع', 'غ', 'ف', 'ق', 'ك', 'ل', 'م', 'ن', 'ه', 'و', 'ي']
    
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
        self.current_letter = random.choice(self.letters)
        self.answers = {}
        self.scores = {}
        return TextSendMessage(
            text=f"▪️ لعبة إنسان حيوان نبات بلاد\n\n▫️ الحرف: {self.current_letter}\n\n▫️ اكتب إجاباتك (كلمة في كل سطر)\n▪️ مثال:\n{self.current_letter}هد\n{self.current_letter}يهان\n{self.current_letter}مام\n{self.current_letter}رورة"
        )
    
    def check_answer(self, text, user_id, display_name):
        if user_id in self.answers:
            return None
        
        text = text.strip()
        lines = text.split('\n')
        
        if len(lines) >= 4 and ':' not in text:
            words = [line.strip() for line in lines if line.strip()]
            if len(words) >= 4:
                valid_count = sum(1 for word in words[:4] if word and word[0] == self.current_letter)
                if valid_count >= 4:
                    points = valid_count * 3
                    self.answers[user_id] = words[:4]
                    if user_id not in self.scores:
                        self.scores[user_id] = {'name': display_name, 'score': 0}
                    self.scores[user_id]['score'] += points
                    return {'correct': True, 'points': points, 'won': valid_count == 4, 'game_over': True, 'response': TextSendMessage(text=f"▪️ {display_name}\n▫️ إجابات صحيحة: {valid_count}/4\n▫️ +{points} نقطة")}
        
        user_answers = {}
        categories = ['إنسان', 'حيوان', 'نبات', 'بلاد']
        categories_en = ['human', 'animal', 'plant', 'country']
        for line in lines:
            for i, cat in enumerate(categories):
                if cat in line or categories_en[i] in line.lower():
                    parts = line.split(':')
                    if len(parts) == 2:
                        answer_word = parts[1].strip()
                        if answer_word and answer_word[0] == self.current_letter:
                            user_answers[categories_en[i]] = answer_word
        
        if len(user_answers) >= 4:
            points = len(user_answers) * 3
            self.answers[user_id] = user_answers
            if user_id not in self.scores:
                self.scores[user_id] = {'name': display_name, 'score': 0}
            self.scores[user_id]['score'] += points
            return {'correct': True, 'points': points, 'won': len(user_answers) == 4, 'game_over': True, 'response': TextSendMessage(text=f"▪️ {display_name}\n▫️ إجابات صحيحة: {len(user_answers)}/4\n▫️ +{points} نقطة")}
        
        return None
