from linebot.models import TextSendMessage, FlexSendMessage
import random
import re

def normalize_text(text):
    if not text:
        return ""
    text = text.strip().lower()
    text = text.replace('أ','ا').replace('إ','ا').replace('آ','ا')
    text = text.replace('ؤ','و').replace('ئ','ي').replace('ء','')
    text = text.replace('ة','ه').replace('ى','ي')
    text = re.sub(r'[\u064B-\u065F]','',text)
    text = re.sub(r'\s+','',text)
    return text

class OppositeGame:
    def __init__(self,line_bot_api):
        self.line_bot_api = line_bot_api
        self.C={'bg':'#0a0e1a','card':'#111827','card2':'#1f2937','text':'#F1F5F9',
                'text2':'#94A3B8','sep':'#374151','cyan':'#00D9FF','cyan_glow':'#00E5FF',
                'purple':'#8B5CF6'}
        self.all_words=[{"word":"كبير","opposite":"صغير"},{"word":"طويل","opposite":"قصير"},{"word":"سريع","opposite":"بطيء"}]
        self.questions=[]
        self.current_word=None
        self.hints_used=0
        self.question_number=0
        self.total_questions=3
        self.player_scores={}

    def create_3d_box(self,contents,bg_color=None,padding="20px",margin="none"):
        return {"type":"box","layout":"vertical","contents":contents,"backgroundColor":bg_color or self.C['card2'],
                "cornerRadius":"16px","paddingAll":padding,"margin":margin,"borderWidth":"1px","borderColor":self.C['sep']}

    def start_game(self):
        self.questions=random.sample(self.all_words,self.total_questions)
        self.question_number=0
        self.player_scores={}
        return self.next_question()

    def next_question(self):
        if self.question_number>=self.total_questions:
            return None
        self.current_word=self.questions[self.question_number]
        self.question_number+=1
        card={"type":"bubble","size":"mega","body":self.create_3d_box([
            {"type":"text","text":f"ما هو عكس {self.current_word['word']}","size":"xl","color":self.C['cyan_glow'],"align":"center"}
        ],self.C['card'])}
        return FlexSendMessage(alt_text=f"السؤال {self.question_number}",contents=card)

    def check_answer(self,answer,user_id,display_name):
        if normalize_text(answer)==normalize_text(self.current_word['opposite']):
            points=2
            if user_id not in self.player_scores:
                self.player_scores[user_id]={'name':display_name,'score':0}
            self.player_scores[user_id]['score']+=points
            return {'response':TextSendMessage(text=f"✅ صحيح! +{points} نقطة"),'points':points,'correct':True}
        return None
