from linebot.models import TextSendMessage, FlexSendMessage
import random
import re
from datetime import datetime

class FastTypingGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.C = {'bg': '#0a0e1a','card':'#111827','card2':'#1f2937','text':'#F1F5F9',
                  'text2':'#94A3B8','sep':'#374151','cyan':'#00D9FF','cyan_glow':'#00E5FF'}
        self.words = ["سرعة","كتابة","برمجة","حاسوب","إنترنت","تطبيق","موقع","شبكة"]
        self.current_word = None
        self.first_correct = None
        self.start_time = None
        self.time_limit = 30
        self.scores = {}

    def normalize_text(self, text):
        if not text:
            return ""
        text = text.strip().lower()
        text = text.replace('أ','ا').replace('إ','ا').replace('آ','ا')
        text = text.replace('ؤ','و').replace('ئ','ي').replace('ء','')
        text = text.replace('ة','ه').replace('ى','ي')
        text = re.sub(r'[\u064B-\u065F]','',text)
        text = re.sub(r'\s+','',text)
        return text

    def create_3d_box(self, contents, bg_color=None, padding="20px", margin="none"):
        return {"type":"box","layout":"vertical","contents":contents,
                "backgroundColor":bg_color or self.C['card2'],"cornerRadius":"16px",
                "paddingAll":padding,"margin":margin,"borderWidth":"1px","borderColor":self.C['sep']}

    def start_game(self):
        self.current_word = random.choice(self.words)
        self.first_correct = None
        self.start_time = datetime.now()
        self.scores = {}
        card = {"type":"bubble","size":"mega","body":{"type":"box","layout":"vertical",
                "contents":[{"type":"text","text":"اكتب هذه الكلمة بأسرع وقت","size":"sm","color":self.C['text2'],
                             "align":"center"},{"type":"text","text":self.current_word,"size":"xxl",
                             "weight":"bold","color":self.C['cyan_glow'],"align":"center","margin":"md"}],
                "backgroundColor":self.C['bg'],"paddingAll":"24px"}}
        return FlexSendMessage(alt_text="الكتابة السريعة", contents=card)

    def check_answer(self,text,user_id,display_name):
        if self.first_correct:
            return None
        if self.normalize_text(text) == self.normalize_text(self.current_word):
            self.first_correct = user_id
            points = 5
            if user_id not in self.scores:
                self.scores[user_id] = {'name':display_name,'score':0}
            self.scores[user_id]['score'] += points
            return {'correct':True,'points':points,'won':True,
                    'response':TextSendMessage(text=f"✅ {display_name} فاز! +{points} نقطة")}
        return None
