# ============================================
# letters_words_game.py - لعبة تكوين الكلمات
# ============================================

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
            {"letters": "ق ل م ع ر ب", "words": ["قلم", "عمر", "رقم", "قلب", "لعب", "عرب", "عمل"]},
            {"letters": "ك ت ا ب ل م", "words": ["كتاب", "كتب", "كلم", "ملك", "تلك", "بلك"]},
            {"letters": "م د ر س ه ل", "words": ["مدرسه", "درس", "مدر", "سرد", "سهل", "درسه"]},
            {"letters": "ش ج ر ه ق ف", "words": ["شجره", "جرش", "شجر", "قشر", "فجر", "شرف"]},
            {"letters": "ح د ي ق ه ل", "words": ["حديقه", "حديق", "دقيق", "حقل", "قلد", "حيد"]},
            {"letters": "ب ي ت ك ر م", "words": ["بيت", "كبير", "ترك", "كرم", "تبي", "ريم"]},
            {"letters": "ن و ر س م ا", "words": ["نور", "سمر", "مان", "نار", "سور", "مرس"]},
            {"letters": "ف ل ج ر ب ح", "words": ["فجر", "حرب", "فلج", "جرح", "حفل", "برج"]},
            {"letters": "س ل ا م و ن", "words": ["سلام", "سلم", "سما", "لوم", "ماس", "سوم"]}
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
    
    def verify_word_with_ai(self, word):
        if not self.use_ai or not self.ask_ai:
            return True
        try:
            prompt = f"هل '{word}' كلمة عربية صحيحة؟ أجب بنعم أو لا فقط"
            response = self.ask_ai(prompt)
            return response and 'نعم' in response
        except:
            return True
    
    def start_game(self):
        challenge = random.choice(self.challenges)
        self.current_letters = challenge['letters']
        self.valid_words = [self.normalize_text(w) for w in challenge['words']]
        self.found_words = {}
        self.scores = {}
        
        return TextSendMessage(
            text=f"▪️ لعبة تكوين الكلمات\n\n▫️ الحروف:\n{self.current_letters}\n\n▫️ كوّن {self.words_needed} كلمات\n▫️ اكتب كلمة في كل رسالة\n\n▪️ مثال: قلم\n▪️ جاوب - عرض حلول"
        )
    
    def check_answer(self, text, user_id, display_name):
        text = text.strip()
        
        if text in ['جاوب', 'الحل', 'الجواب']:
            sample_words = []
            for challenge in self.challenges:
                if self.current_letters == challenge['letters']:
                    sample_words = challenge['words'][:5]
                    break
            
            return {
                'correct': False,
                'game_over': True,
                'response': TextSendMessage(
                    text=f"▪️ بعض الحلول:\n\n▫️ {', '.join(sample_words)}"
                )
            }
        
        word_normalized = self.normalize_text(text)
        
        if user_id in self.found_words and word_normalized in self.found_words[user_id]:
            return None
        
        if len(word_normalized) < 2:
            return None
        
        if not self.can_form_word(word_normalized, self.current_letters):
            return None
        
        is_valid = word_normalized in self.valid_words
        
        if not is_valid and self.use_ai:
            is_valid = self.verify_word_with_ai(text)
        
        if not is_valid:
            return None
        
        if user_id not in self.found_words:
            self.found_words[user_id] = []
        self.found_words[user_id].append(word_normalized)
        
        if user_id not in self.scores:
            self.scores[user_id] = {'name': display_name, 'score': 0}
        
        points = 5
        self.scores[user_id]['score'] += points
        
        words_count = len(self.found_words[user_id])
        
        if words_count >= self.words_needed:
            return {
                'correct': True,
                'points': points,
                'won': True,
                'game_over': True,
                'response': TextSendMessage(
                    text=f"▪️ {display_name} فاز\n\n▫️ الكلمات: {', '.join(self.found_words[user_id])}\n▫️ النقاط: {self.scores[user_id]['score']}"
                )
            }
        
        return {
            'correct': True,
            'points': points,
            'response': TextSendMessage(
                text=f"▪️ {display_name}\n\n▫️ كلمة صحيحة: {text}\n▫️ +{points} نقطة\n▫️ متبقي: {self.words_needed - words_count}"
            )
        }
