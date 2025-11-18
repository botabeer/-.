from linebot.models import TextSendMessage, FlexSendMessage
import random, re

def normalize_text(t):
    if not t: return ""
    t = t.strip().lower()
    t = re.sub('[أإآ]','ا',t)
    t = re.sub('[ؤ]','و',t)
    t = re.sub('[ئ]','ي',t)
    t = re.sub('[ءةى]','',t)
    t = re.sub('[\u064B-\u065F]','',t)
    return re.sub(r'\s+',' ',t).strip()

C = {'bg':'#0A0E27','card':'#0F2440','text':'#E0F2FF','text2':'#7FB3D5',
     'cyan':'#00D9FF','glow':'#5EEBFF','sep':'#2C5F8D','border':'#00D9FF40'}

def glass_box(contents, pad="20px"):
    return {"type":"box","layout":"vertical","contents":contents,
            "backgroundColor":C['card'],"cornerRadius":"16px",
            "paddingAll":pad,"borderWidth":"1px","borderColor":C['border']}

def game_header(title, sub):
    return [
        {"type":"text","text":"♓","size":"6xl","color":C['glow'],"align":"center"},
        {"type":"text","text":title,"size":"xl","weight":"bold","color":C['cyan'],"align":"center"},
        {"type":"text","text":sub,"size":"sm","color":C['text2'],"align":"center"},
        {"type":"separator","margin":"lg","color":C['sep']}
    ]

def create_game_card(header, body, footer=None):
    card = {"type":"bubble","size":"mega",
        "body":{"type":"box","layout":"vertical","backgroundColor":C['bg'],
                "paddingAll":"24px","contents":header+body}}
    if footer:
        card["footer"] = {"type":"box","layout":"horizontal","contents":footer,
                          "backgroundColor":C['bg']}
    return card

def btn(label, text):
    return {"type":"button","style":"secondary","height":"md",
            "action":{"type":"message","label":label,"text":text}}

def progress_bar(cur, total):
    return {
        "type":"box","layout":"horizontal","margin":"lg",
        "contents":[
            {"type":"box","flex":cur,"height":"6px",
             "backgroundColor":C['cyan'],"cornerRadius":"3px"},
            {"type":"box","flex":(total-cur),"height":"6px",
             "backgroundColor":C['card'],"cornerRadius":"3px"}
        ]
    }

class SongGame:
    def __init__(self):
        self.songs = [
            {"lyrics":"أنا بلياك إذا أرمش إلك تنزل ألف دمعة","singer":"ماجد المهندس"},
            {"lyrics":"يا بعدهم كلهم .. يا سراجي بينهم","singer":"عبدالمجيد عبدالله"},
            {"lyrics":"قولي أحبك كي تزيد وسامتي","singer":"كاظم الساهر"},
            {"lyrics":"كيف أبيّن لك شعوري دون ما أحكي","singer":"عايض"}
        ]
        self.current_song=None
        self.current_q=0
        self.max_q=5
        self.scores={}
        self.hints_used=0

    def start_game(self):
        self.current_q=1
        self.scores={}
        return self.next_question()

    def next_question(self):
        if self.current_q>self.max_q: return None
        self.current_song=random.choice(self.songs)
        self.hints_used=0

        return FlexSendMessage(
            alt_text="لعبة الأغنية",
            contents=create_game_card(
                game_header("لعبة الأغنية", f"السؤال {self.current_q}/{self.max_q}"),
                [
                    glass_box([{
                        "type":"text","text":self.current_song["lyrics"],
                        "size":"lg","color":C["text"],"align":"center","wrap":True
                    }], "24px"),
                    {"type":"text","text":"من المغني؟","size":"md",
                     "color":C["glow"],"align":"center","margin":"lg"},
                    progress_bar(self.current_q, self.max_q)
                ],
                [btn("لمح","لمح"), btn("جاوب","جاوب")]
            )
        )

    def check_answer(self, text, user_id, name):
        ans = text.strip().lower()

        # تلميح
        if ans in ["لمح","تلميح"]:
            if self.hints_used:
                return {"response":TextSendMessage(text="استخدمت التلميح مسبقًا"),"correct":False}

            self.hints_used=1
            singer=self.current_song["singer"]
            hint = singer[0] + " " + "_ " * (len(singer)-1)

            return {
                "response":FlexSendMessage(
                    alt_text="تلميح",
                    contents=create_game_card(
                        game_header("تلميح","الحرف الأول"),
                        [glass_box([{
                            "type":"text","text":hint,"size":"3xl",
                            "color":C["glow"],"align":"center"
                        }],"32px")]
                    )
                ),
                "correct":False
            }

        # كشف الجواب
        if ans in ["جاوب","الجواب","الحل"]:
            self.current_q += 1
            return {
                "response":FlexSendMessage(
                    alt_text="الحل",
                    contents=create_game_card(
                        game_header("الحل","المغني"),
                        [glass_box([{
                            "type":"text","text":self.current_song["singer"],
                            "size":"xl","color":C["glow"],
                            "align":"center","weight":"bold"
                        }],"32px")]
                    )
                ),
                "correct":False,
                "next_question":self.current_q <= self.max_q
            }

        # إجابة صحيحة
        if normalize_text(text)==normalize_text(self.current_song["singer"]):
            points = 2 if not self.hints_used else 1

            if user_id not in self.scores:
                self.scores[user_id]={"name":name,"score":0}

            self.scores[user_id]["score"] += points
            self.current_q += 1

            return {
                "response":FlexSendMessage(
                    alt_text="صحيح",
                    contents=create_game_card(
                        game_header("صحيح","إجابة ممتازة"),
                        [glass_box([
                            {"type":"text","text":name,"size":"xl","align":"center","color":C["text"]},
                            {"type":"text","text":f"+{points} نقطة","size":"xxl",
                             "color":C["glow"],"align":"center","margin":"md"}
                        ],"28px")]
                    )
                ),
                "correct":True,
                "points":points,
                "next_question":self.current_q <= self.max_q
            }

        return None
