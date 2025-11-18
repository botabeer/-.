# song_game.py
from linebot.models import TextSendMessage, FlexSendMessage
import random, re

# ألوان موحدة
C = {'bg':'#0A0E27','card':'#0F2440','text':'#E0F2FF','text2':'#7FB3D5','cyan':'#00D9FF','glow':'#5EEBFF','sep':'#2C5F8D','border':'#00D9FF40'}

def normalize_text(t):
    if not t: return ""
    t = t.strip().lower()
    t = re.sub('[أإآ]','ا',t); t = re.sub('[ؤ]','و',t); t = re.sub('[ئ]','ي',t); t = re.sub('[ءةى]','',t); t = re.sub('[\u064B-\u065F]','',t)
    return re.sub(r'\s+',' ',t).strip()

def glass_box(contents, padding="20px"):
    return {"type":"box","layout":"vertical","contents":contents,"backgroundColor":C['card'],"cornerRadius":"16px",
        "paddingAll":padding,"borderWidth":"1px","borderColor":C['border'],"margin":"md"}

def progress_bar(current, total):
    return {"type":"box","layout":"horizontal","contents":[
        {"type":"box","layout":"vertical","contents":[],"backgroundColor":C['cyan'],"height":"6px","flex":current,"cornerRadius":"3px"},
        {"type":"box","layout":"vertical","contents":[],"backgroundColor":C['card'],"height":"6px","flex":max(1,total-current),"cornerRadius":"3px"}
    ],"spacing":"xs","margin":"lg"}

def game_header(title, subtitle):
    return [{"type":"text","text":"♓","size":"6xl","color":C['glow'],"align":"center","margin":"none"},
        {"type":"text","text":title,"size":"xl","weight":"bold","color":C['cyan'],"align":"center","margin":"md"},
        {"type":"text","text":subtitle,"size":"sm","color":C['text2'],"align":"center","margin":"xs"},
        {"type":"separator","margin":"lg","color":C['sep']}]

def create_game_card(header, body_contents, footer_buttons=None):
    card = {"type":"bubble","size":"mega","body":{"type":"box","layout":"vertical",
        "contents":header + body_contents,"backgroundColor":C['bg'],"paddingAll":"24px"}}
    if footer_buttons:
        card["footer"] = {"type":"box","layout":"horizontal","contents":footer_buttons,
            "spacing":"sm","backgroundColor":C['bg'],"paddingAll":"16px"}
    return card

def btn(label, text): return {"type":"button","action":{"type":"message","label":label,"text":text},"style":"secondary","height":"md"}

class SongGame:
    def __init__(self):
        self.songs = [
            {"lyrics":"أنا بلياك إذا أرمش إلك تنزل ألف دمعة","singer":"ماجد المهندس"},
            {"lyrics":"يا بعدهم كلهم .. يا سراجي بينهم","singer":"عبدالمجيد عبدالله"},
            {"lyrics":"قولي أحبك كي تزيد وسامتي","singer":"كاظم الساهر"},
            {"lyrics":"كيف أبيّن لك شعوري دون ما أحكي","singer":"عايض"}
        ]
        self.current_song, self.current_q, self.max_q, self.scores, self.hints_used = None, 0, 5, {}, 0
    
    def start_game(self):
        self.current_q, self.scores = 1, {}
        return self.next_question()
    
    def next_question(self):
        if self.current_q > self.max_q: return None
        self.current_song = random.choice(self.songs)
        self.hints_used = 0
        return FlexSendMessage(alt_text=f"السؤال {self.current_q}",
            contents=create_game_card(game_header("لعبة الأغنية",f"السؤال {self.current_q}/{self.max_q}"), [
            glass_box([{"type":"text","text":self.current_song['lyrics'],"size":"lg","color":C['text'],"align":"center","wrap":True,"weight":"bold"}],"24px"),
            {"type":"text","text":"من المغني؟","size":"md","color":C['glow'],"align":"center","margin":"lg","weight":"bold"},
            progress_bar(self.current_q, self.max_q)],[btn("لمح","لمح"),btn("جاوب","جاوب")]))
    
    def check_answer(self, text, user_id, name):
        ans = text.strip().lower()
        if ans in ['لمح','تلميح']:
            if self.hints_used > 0: return {'response':TextSendMessage(text="تم استخدام التلميح"),'correct':False}
            self.hints_used = 1
            singer = self.current_song['singer']
            hint = singer[0] + " " + "_ " * (len(singer) - 1)
            return {'response':FlexSendMessage(alt_text="تلميح",
                contents=create_game_card(game_header("تلميح","الحرف الأول + عدد الحروف"), [
                glass_box([{"type":"text","text":hint,"size":"3xl","weight":"bold","color":C['glow'],"align":"center","letterSpacing":"4px"}],"32px"),
                {"type":"text","text":"استخدام التلميح يقلل النقاط للنصف","size":"xs","color":C['text2'],"align":"center","margin":"lg"}])),'correct':False}
        if ans in ['جاوب','الجواب','الحل']:
            self.current_q += 1
            return {'response':FlexSendMessage(alt_text="الحل",
                contents=create_game_card(game_header("الحل","الإجابة الصحيحة"), [
                glass_box([{"type":"text","text":self.current_song['singer'],"size":"xxl","color":C['glow'],"weight":"bold","align":"center","wrap":True}],"28px")])),'correct':False,'next_question':self.current_q<=self.max_q}
        if normalize_text(text) == normalize_text(self.current_song['singer']):
            points = 2 if self.hints_used == 0 else 1
            if user_id not in self.scores: self.scores[user_id] = {'name':name,'score':0}
            self.scores[user_id]['score'] += points
            self.current_q += 1
            return {'response':FlexSendMessage(alt_text="صحيح",
                contents=create_game_card(game_header("إجابة صحيحة","أحسنت"), [
                glass_box([{"type":"text","text":name,"size":"xl","weight":"bold","color":C['text'],"align":"center"},
                {"type":"text","text":f"+{points} نقطة","size":"xxl","color":C['glow'],"align":"center","margin":"md","weight":"bold"}],"28px")])),'correct':True,'points':points,'won':True,'next_question':self.current_q<=self.max_q}
        return None
