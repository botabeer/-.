from linebot.models import TextSendMessage, FlexSendMessage
import random, re

def normalize_text(text):
    if not text:return ""
    text=text.strip().lower()
    text=text.replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ؤ','و').replace('ئ','ي').replace('ء','').replace('ة','ه').replace('ى','ي')
    return re.sub(r'\s+','',re.sub(r'[\u064B-\u065F]','',text))

class OppositeGame:
    def __init__(self,line_bot_api):
        self.line_bot_api=line_bot_api
        self.C={'bg':'#0A0F1A','card':'#0F1823','card2':'#1A2332','text':'#E0F7FF','text2':'#7DD3FC','sep':'#00D9FF','cyan':'#00D9FF','glow':'#00E5FF','dark':'#030712'}
        self.all_words=[
            {"word":"كبير","opposite":"صغير","hint":"حجم"},
            {"word":"سريع","opposite":"بطيء","hint":"سرعة"},
            {"word":"ساخن","opposite":"بارد","hint":"حرارة"},
            {"word":"قوي","opposite":"ضعيف","hint":"قوة"},
            {"word":"جميل","opposite":"قبيح","hint":"شكل"},
            {"word":"غني","opposite":"فقير","hint":"مال"},
            {"word":"نظيف","opposite":"وسخ","hint":"نظافة"},
            {"word":"سعيد","opposite":"حزين","hint":"شعور"},
            {"word":"صعب","opposite":"سهل","hint":"مستوى"},
            {"word":"ثقيل","opposite":"خفيف","hint":"وزن"},
            {"word":"قديم","opposite":"جديد","hint":"عمر"},
            {"word":"واسع","opposite":"ضيق","hint":"مساحة"},
            {"word":"مظلم","opposite":"مضيء","hint":"إضاءة"},
            {"word":"عالي","opposite":"منخفض","hint":"ارتفاع"}
        ]
        self.questions,self.current_word,self.hints_used,self.question_number,self.total_questions,self.player_scores=[],None,0,0,5,{}

    def start_game(self):
        self.questions=random.sample(self.all_words,self.total_questions)
        self.question_number,self.player_scores,self.hints_used=0,{},0
        return self.next_question()

    def next_question(self):
        if self.question_number>=self.total_questions:return None
        self.current_word=self.questions[self.question_number]
        self.question_number+=1
        self.hints_used=0
        return TextSendMessage(text=f"ما هو عكس: {self.current_word['word']}")

    def get_hint(self):
        if not self.current_word:return"لا يوجد سؤال نشط"
        self.hints_used=1
        answer=self.current_word['opposite']
        hint_word=self.current_word.get('hint','')
        blanks=' '.join(['_']*len(answer))
        return f"التلميح: {hint_word}\nالحرف الأول: {answer[0]}\nعدد الحروف: {blanks}"

    def reveal_answer(self):
        return self.current_word['opposite']if self.current_word else"لا يوجد سؤال"

    def check_answer(self,answer,user_id,display_name):
        if not self.current_word:return None
        if normalize_text(answer)==normalize_text(self.current_word['opposite']):
            points=3 if self.hints_used==0 else 2
            if user_id not in self.player_scores:self.player_scores[user_id]={'name':display_name,'score':0}
            self.player_scores[user_id]['score']+=points
            return{'response':TextSendMessage(text=f"صحيح! +{points} نقطة"),'points':points,'correct':True,'next_question':self.question_number<self.total_questions}
        return None
