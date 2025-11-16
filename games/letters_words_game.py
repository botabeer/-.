from linebot.models import TextSendMessage
import random
import re

class LettersWordsGame:
    def __init__(self, line_bot_api, use_ai=False, ask_ai=None):
        self.line_bot_api = line_bot_api
        self.use_ai = use_ai
        self.ask_ai = ask_ai
        self.current_letters = None
        self.valid_words = []
        self.found_words = {}
        self.words_needed = 3
        self.scores = {}
        
        self.challenges = [
            {"letters": "ق ل م ب ر و", "words": ["قلم", "برق", "مرو", "قلب", "لعب"]},
            {"letters": "ك ت ا ب ر ل", "words": ["كتاب", "تلب", "بكر", "كلم", "ملك"]},
            {"letters": "م د ر س ه ل", "words": ["مدرس", "درس", "سهل", "مدر", "هلم"]},
            {"letters": "ش ج ر ف ق ه", "words": ["شجر", "فجر", "قهر", "جرش", "شرف"]},
            {"letters": "ح د ي ق ه ل", "words": ["حديق", "حقل", "قلد", "دقيق", "حديقه"]}
        ]
    
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
    
    def can_form_word(self, word, letters):
        letters_list = list(letters.replace(' ', ''))
        word_letters = list(word)
        for char in word_letters:
            if char in letters_list:
                letters_list.remove(char)
            else:
                return False
        return True
    
    def start_game(self):
        challenge = random.choice(self.challenges)
        self.current_letters = challenge['letters']
        self.valid_words = [self.normalize_text(w) for w in challenge.get('words', [])]
        self.found_words = {}
        self.scores = {}
        return TextSendMessage(text=f"▪️ لعبة تكوين الكلمات\n\nالحروف: {self.current_letters}\n\nكوّن {self.words_needed} كلمات من هذه الحروف\n\nاكتب كلمة واحدة في كل رسالة")
    
    def check_answer(self, text, user_id, display_name):
        text = text.strip()
        if text in ['جاوب', 'الحل']:
            return {
                'correct': False,
                'game_over': True,
                'response': TextSendMessage(text=f"▪️ بعض الكلمات الصحيحة:\n\n{', '.join(self.valid_words[:5])}")
            }
        
        word_normalized = self.normalize_text(text)
        
        if user_id in self.found_words and word_normalized in self.found_words[user_id]:
            return None
        
        if not self.can_form_word(word_normalized, self.current_letters):
            return None
        
        is_valid = word_normalized in self.valid_words
        
        if not is_valid:
            return None
        
        if user_id not in self.found_words:
            self.found_words[user_id] = []
        self.found_words[user_id].append(word_normalized)
        
        points = 2
        if user_id not in self.scores:
            self.scores[user_id] = {'name': display_name, 'score': 0}
        self.scores[user_id]['score'] += points
        
        finished = len(self.found_words[user_id]) >= self.words_needed
        
        return {
            'correct': True,
            'points': points,
            'won': finished,
            'game_over': finished,
            'response': TextSendMessage(text=f"▪️ {display_name}\n\n+{points} نقطة\n\nالكلمة: {text}")
        }
