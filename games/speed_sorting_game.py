from linebot.models import TextSendMessage, FlexSendMessage
import random, re

def normalize(t):
    if not t: return ""
    t = t.strip().lower().replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ؤ','و').replace('ئ','ي').replace('ء','').replace('ة','ه').replace('ى','ي')
    return re.sub(r'[\u064B-\u065F\s]+','',t)

class SpeedSortingGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.C = {'bg':'#0a0e1a','card':'#111827','card2':'#1f2937','card3':'#374151',
                  'text':'#F1F5F9','text2':'#94A3B8','sep':'#374151','cyan':'#00D9FF',
                  'cyan_glow':'#00E5FF','purple':'#8B5CF6'}
        
        self.sets = [
            {"items":["نملة","فأر","قطة","كلب","أسد","فيل"],"type":"size","q":"من الاصغر للاكبر","count":4},
            {"items":["عصفور","ارنب","خروف","حصان","جمل","حوت"],"type":"size","q":"من الاصغر للاكبر","count":4},
            {"items":["قطر","الكويت","الاردن","السعودية","مصر"],"type":"population","q":"من الاقل سكانا للاكثر","count":4},
            {"items":["البحرين","عمان","الامارات","سوريا","المغرب"],"type":"population","q":"من الاقل سكانا للاكثر","count":4},
            {"items":["5","12","23","45","67","89","120"],"type":"number","q":"من الاصغر للاكبر","count":5},
            {"items":["3","8","15","28","44","71","95"],"type":"number","q":"من الاصغر للاكبر","count":5},
            {"items":["احمد","باسم","جمال","داود","زياد","سامي"],"type":"alpha","q":"حسب الابجدية","count":4},
            {"items":["ريم","سارة","فاطمة","ليلى","مريم","نور"],"type":"alpha","q":"حسب الابجدية","count":4},
            {"items":["منزل","عمارة","برج خليفة","جبل افرست"],"type":"height","q":"من الاقصر للاطول","count":4},
            {"items":["سلحفاة","انسان","حصان","فهد","صقر","صاروخ"],"type":"speed","q":"من الابطأ للاسرع","count":4},
            {"items":["رضيع","طفل","شاب","كهل"],"type":"age","q":"من الاصغر للاكبر","count":4},
            {"items":["الفجر","الضحى","الظهر","العصر","المغرب","العشاء"],"type":"time","q":"حسب الترتيب الزمني","count":5}
        ]
        
        self.current = None
        self.correct_order = []
        self.answered = False
        self.q_num = 1
        self.max_q = 5
        self.scores = {}

    def box(self, c, bg=None, pad="20px", mar="none"):
        return {"type":"box","layout":"vertical","contents":c,"backgroundColor":bg or self.C['card2'],
                "cornerRadius":"16px","paddingAll":pad,"margin":mar,"borderWidth":"1px","borderColor":self.C['sep']}

    def card(self, items_str, question, q_num):
        items_boxes = [{"type":"box","layout":"vertical","contents":[
            {"type":"text","text":item,"size":"lg","weight":"bold","color":self.C['cyan'],"align":"center"}
        ],"backgroundColor":self.C['card2'],"cornerRadius":"12px","height":"50px","justifyContent":"center",
          "borderWidth":"1px","borderColor":self.C['sep'],"margin":"xs"} for item in items_str.split(" - ")]
        
        return {"type":"bubble","size":"mega","body":{"type":"box","layout":"vertical","contents":[
            {"type":"box","layout":"horizontal","contents":[
                {"type":"box","layout":"vertical","contents":[],"width":"4px","backgroundColor":self.C['cyan'],"cornerRadius":"2px"},
                {"type":"box","layout":"vertical","contents":[
                    {"type":"text","text":"ترتيب السرعة","size":"xxl","weight":"bold","color":self.C['cyan']},
                    {"type":"text","text":f"الجولة {q_num} من {self.max_q}","size":"sm","color":self.C['text2'],"margin":"sm"}
                ],"margin":"md"}
            ]},
            {"type":"separator","margin":"xl","color":self.C['sep']},
            self.box([{"type":"text","text":question,"size":"md","color":self.C['text2'],"align":"center","weight":"bold"}],
                     self.C['card'],"16px","lg"),
            {"type":"box","layout":"vertical","contents":items_boxes,"margin":"md","spacing":"xs"},
            self.box([{"type":"text","text":"اكتب العناصر بنفس الترتيب\nافصل بـ (-) او (-) او مسافة","size":"xs",
                      "color":self.C['text2'],"align":"center","wrap":True}],self.C['card3'],"12px","md"),
            {"type":"box","layout":"horizontal","contents":[
                {"type":"box","layout":"vertical","contents":[],"backgroundColor":self.C['cyan'],"height":"6px",
                 "flex":q_num,"cornerRadius":"3px"},
                {"type":"box","layout":"vertical","contents":[],"backgroundColor":self.C['card2'],"height":"6px",
                 "flex":self.max_q - q_num,"cornerRadius":"3px"}
            ],"margin":"xl","spacing":"xs"}
        ],"backgroundColor":self.C['bg'],"paddingAll":"24px"},"footer":{"type":"box","layout":"horizontal",
        "contents":[{"type":"button","action":{"type":"message","label":"تلميح","text":"لمح"},"style":"secondary",
                     "color":self.C['card2'],"height":"sm"},
                    {"type":"button","action":{"type":"message","label":"الحل","text":"جاوب"},"style":"secondary",
                     "color":self.C['card2'],"height":"sm"}],
        "spacing":"sm","backgroundColor":self.C['bg'],"paddingAll":"16px"}}

    def start_game(self):
        self.q_num = 1
        self.scores = {}
        return self.next_question()

    def next_question(self):
        if self.q_num > self.max_q: return None
        
        data = random.choice(self.sets)
        selected = random.sample(data["items"], data["count"])
        
        if data["type"] == "number":
            self.correct_order = sorted(selected, key=lambda x: int(x))
        elif data["type"] == "alpha":
            self.correct_order = sorted(selected)
        else:
            order_map = {item: i for i, item in enumerate(data["items"])}
            self.correct_order = sorted(selected, key=lambda x: order_map[x])
        
        shuffled = self.correct_order.copy()
        while shuffled == self.correct_order:
            random.shuffle(shuffled)
        
        self.current = data
        self.answered = False
        
        return FlexSendMessage(alt_text=f"الجولة {self.q_num}",
                              contents=self.card(" - ".join(shuffled), data["q"], self.q_num))

    def hint(self):
        if not self.current: return None
        first_two = " - ".join(self.correct_order[:2])
        return {'response': FlexSendMessage(alt_text="تلميح",
                contents={"type":"bubble","size":"mega","body":{"type":"box","layout":"vertical","contents":[
                    {"type":"box","layout":"horizontal","contents":[
                        {"type":"box","layout":"vertical","contents":[],"width":"4px","backgroundColor":self.C['cyan'],"cornerRadius":"2px"},
                        {"type":"text","text":"تلميح","size":"xxl","weight":"bold","color":self.C['cyan'],"margin":"md"}
                    ]},
                    {"type":"separator","margin":"xl","color":self.C['sep']},
                    self.box([{"type":"text","text":"اول عنصرين","size":"sm","color":self.C['text2'],"align":"center"},
                              {"type":"text","text":first_two,"size":"lg","weight":"bold","color":self.C['cyan_glow'],
                               "align":"center","margin":"md","wrap":True}],self.C['card'],"20px","xl"),
                    {"type":"text","text":"استخدام التلميح يقلل النقاط للنصف","size":"xs",
                     "color":self.C['purple'],"align":"center","margin":"xl"}
                ],"backgroundColor":self.C['bg'],"paddingAll":"24px"}}), 'points':-1, 'correct':False}

    def show_answer(self):
        answer_str = " - ".join(self.correct_order)
        card = {"type":"bubble","size":"mega","body":{"type":"box","layout":"vertical","contents":[
            {"type":"box","layout":"horizontal","contents":[
                {"type":"box","layout":"vertical","contents":[],"width":"4px","backgroundColor":self.C['cyan'],"cornerRadius":"2px"},
                {"type":"text","text":"الحل","size":"xxl","weight":"bold","color":self.C['cyan'],"margin":"md"}
            ]},
            {"type":"separator","margin":"xl","color":self.C['sep']},
            self.box([{"type":"text","text":answer_str,"size":"lg","color":self.C['cyan_glow'],
                       "weight":"bold","align":"center","wrap":True}],self.C['card'],"20px","xl")
        ],"backgroundColor":self.C['bg'],"paddingAll":"24px"}}
        
        self.q_num += 1
        return {'response': FlexSendMessage(alt_text="الحل", contents=card), 'correct':False,
                'next_question': self.q_num <= self.max_q}

    def check_answer(self, text, user_id, display_name):
        if self.answered or not self.current: return None
        
        ans = text.strip().lower()
        if ans in ['لمح','تلميح','hint']: return self.hint()
        if ans in ['جاوب','الجواب','الحل','answer']: return self.show_answer()
        
        answer_list = [normalize(x) for x in re.split(r'[-\s]+', text) if x.strip()]
        correct_norm = [normalize(x) for x in self.correct_order]
        
        if answer_list == correct_norm:
            self.answered = True
            points = 3
            
            if user_id not in self.scores:
                self.scores[user_id] = {'name': display_name, 'score': 0}
            self.scores[user_id]['score'] += points
            
            success = {"type":"bubble","size":"mega","body":{"type":"box","layout":"vertical","contents":[
                self.box([{"type":"text","text":"ترتيب صحيح","size":"xxl","weight":"bold",
                           "color":self.C['cyan'],"align":"center"}],self.C['card2']),
                {"type":"separator","margin":"xl","color":self.C['sep']},
                self.box([{"type":"text","text":display_name,"size":"xl","weight":"bold","color":self.C['text'],"align":"center"},
                          {"type":"text","text":f"{points} نقطة","size":"lg","color":self.C['cyan_glow'],
                           "align":"center","margin":"sm"}],self.C['card'],"24px","xl")
            ],"backgroundColor":self.C['bg'],"paddingAll":"24px"}}
            
            self.q_num += 1
            
            if self.q_num <= self.max_q:
                return {'response': FlexSendMessage(alt_text="صحيح", contents=success),
                        'correct':True, 'points':points, 'won':True, 'next_question':True}
            else:
                return self._end_game()
        
        return {'response': TextSendMessage(text="ترتيب خاطئ - حاول مرة اخرى"), 'correct':False}

    def _end_game(self):
        if not self.scores:
            return {'response': TextSendMessage(text="انتهت اللعبة - لم يشارك احد"), 'game_over':True}
        
        sorted_p = sorted(self.scores.items(), key=lambda x: x[1]['score'], reverse=True)
        winner = sorted_p[0][1]
        
        score_items = []
        for i, (uid, data) in enumerate(sorted_p, 1):
            rank = "المركز الاول" if i==1 else "المركز الثاني" if i==2 else "المركز الثالث" if i==3 else f"المركز {i}"
            score_items.append(self.box([{"type":"box","layout":"horizontal","contents":[
                {"type":"text","text":f"{rank} - {data['name']}","size":"sm",
                 "color":self.C['cyan'] if i==1 else self.C['text'],"weight":"bold" if i<=3 else "regular","flex":3},
                {"type":"text","text":str(data['score']),"size":"lg" if i==1 else "md","weight":"bold",
                 "color":self.C['cyan'] if i==1 else self.C['text2'],"align":"end","flex":1}
            ]}], self.C['card2'] if i==1 else self.C['card3'], "16px", "sm"))
        
        winner_card = {"type":"bubble","size":"mega","body":{"type":"box","layout":"vertical","contents":[
            self.box([{"type":"text","text":"انتهت اللعبة","size":"xl","weight":"bold",
                       "color":self.C['cyan'],"align":"center"}],self.C['card2']),
            {"type":"separator","margin":"xl","color":self.C['sep']},
            self.box([{"type":"text","text":"الفائز","size":"sm","color":self.C['text2'],"align":"center"},
                      {"type":"text","text":winner['name'],"size":"xxl","weight":"bold",
                       "color":self.C['cyan'],"align":"center","margin":"sm"},
                      {"type":"text","text":f"{winner['score']} نقطة","size":"lg","weight":"bold",
                       "color":self.C['cyan_glow'],"align":"center","margin":"md"}],self.C['card'],"24px","xl"),
            {"type":"separator","margin":"xl","color":self.C['sep']},
            {"type":"text","text":"النتائج النهائية","size":"lg","weight":"bold",
             "color":self.C['text'],"align":"center","margin":"xl"},
            {"type":"box","layout":"vertical","contents":score_items,"margin":"md"}
        ],"backgroundColor":self.C['bg'],"paddingAll":"24px"},"footer":{"type":"box","layout":"horizontal",
        "contents":[{"type":"button","action":{"type":"message","label":"لعب مرة اخرى","text":"ترتيب"},
                     "style":"primary","color":self.C['cyan']},
                    {"type":"button","action":{"type":"message","label":"الصدارة","text":"الصدارة"},
                     "style":"secondary","color":self.C['card2']}],
        "spacing":"sm","backgroundColor":self.C['bg'],"paddingAll":"16px"}}
        
        return {'response': FlexSendMessage(alt_text="الفائز", contents=winner_card),
                'won':True, 'game_over':True}
