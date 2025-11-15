from linebot.models import TextSendMessage
import random, re

class LettersWordsGame:
    def __init__(self, line_bot_api, use_ai=False, ask_ai=None):
        self.line_bot_api = line_bot_api
        self.current_letters = None
        self.valid_words = []
        self.found_words = {}
        self.words_needed = 3
        self.scores = {}
        
        self.challenges = [
            {"letters": "ك ت ا ب ي ه", "words": ["كتاب","كتب","تاب","بيت","بات"]},
            {"letters": "م د ر س ه ل", "words": ["مدرسه","مدرس","درس","سهل","هدم"]},
            {"letters": "ح ب ر ك ه ي", "words": ["حرب","حبر","كبير","حبك","كرب"]},
            {"letters": "ق ل م ع ر ي", "words": ["قلم","عمر","قمر","علم","لعب"]},
            {"letters": "ن و ر س م ي", "words": ["نور","سمر","نمر","سور","مرس"]},
            {"letters": "ش ج ر ق ه ل", "words": ["شجر","قشر","شرق","جرش","قرش"]}
        ]
    
    def normalize(self, text):
        if not text: return ""
        text = text.strip().lower()
        text = text.replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ؤ','و').replace('ئ','ي').replace('ء','').replace('ة','ه').replace('ى','ي')
        return re.sub(r'[\u064B-\u065F]', '', re.sub(r'\s+', '', text))
    
    def start_game(self):
        challenge = random.choice(self.challenges)
        self.current_letters = challenge['letters']
        self.valid_words = [self.normalize(w) for w in challenge['words']]
        self.found_words = {}
        self.scores = {}
        return TextSendMessage(text=f"▪️ لعبة تكوين الكلمات\n\nالحروف:\n{self.current_letters}\n\nكوّن {self.words_needed} كلمات\n\nاكتب كلمة واحدة في كل رسالة\n\nجاوب - عرض حلول")
    
    def check_answer(self, text, user_id, name):
        if text.strip().lower() in ['جاوب', 'الحل', 'الجواب']:
            for c in self.challenges:
                if self.current_letters == c['letters']:
                    return {'correct': False, 'game_over': True, 'response': TextSendMessage(text=f"بعض الحلول:\n\n" + "\n".join(c['words'][:5]))}
        
        word_norm = self.normalize(text)
        
        if user_id in self.found_words and word_norm in self.found_words[user_id]:
            return None
        
        if len(word_norm) < 2 or word_norm not in self.valid_words:
            return None
        
        if user_id not in self.found_words:
            self.found_words[user_id] = []
        self.found_words[user_id].append(word_norm)
        
        if user_id not in self.scores:
            self.scores[user_id] = {'name': name, 'score': 0}
        
        points = 5
        self.scores[user_id]['score'] += points
        words_count = len(self.found_words[user_id])
        
        if words_count >= self.words_needed:
            return {'correct': True, 'points': points, 'won': True, 'game_over': True, 'response': TextSendMessage(text=f"🏆 {name} فاز\n\nالكلمات:\n" + "\n".join(self.found_words[user_id]) + f"\n\nالنقاط: {self.scores[user_id]['score']}")}
        
        return {'correct': True, 'points': points, 'response': TextSendMessage(text=f"✓ {name}\n\nكلمة صحيحة: {text}\n+{points} نقطة\n\nمتبقي: {self.words_needed - words_count} كلمات")}
