"""ملف الألعاب - نسخة كاملة محسّنة"""
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

def btn(label, text): 
    return {"type":"button","action":{"type":"message","label":label,"text":text},"style":"secondary","height":"md"}

def game_over_card(game_name, scores):
    """بطاقة نهاية اللعبة مع النتائج"""
    if not scores:
        contents = [{"type":"text","text":"لم يسجل أحد نقاط","size":"md","color":C['text2'],"align":"center","margin":"lg"}]
    else:
        sorted_scores = sorted(scores.items(), key=lambda x: x[1]['score'], reverse=True)
        contents = []
        for i, (uid, data) in enumerate(sorted_scores[:5], 1):
            rank = ["🥇","🥈","🥉"][i-1] if i<=3 else f"#{i}"
            contents.append({"type":"box","layout":"horizontal","contents":[
                {"type":"text","text":rank,"size":"md","weight":"bold","flex":0,"color":C['cyan'] if i<=3 else C['text']},
                {"type":"text","text":data['name'],"size":"sm","flex":3,"margin":"md","wrap":True,"color":C['text']},
                {"type":"text","text":str(data['score']),"size":"lg","weight":"bold","flex":1,"align":"end","color":C['glow']}
            ],"backgroundColor":C['card'],"cornerRadius":"12px","paddingAll":"12px","margin":"sm" if i>1 else "md",
                "borderWidth":"2px" if i==1 else "1px","borderColor":C['cyan'] if i==1 else C['border']})
    
    return FlexSendMessage(alt_text="انتهت اللعبة",
        contents=create_game_card(game_header("انتهت اللعبة",f"نتائج {game_name}"), 
            [{"type":"box","layout":"vertical","contents":contents,"margin":"md"}]))

# ==================== الألعاب ====================

# 1. لعبة الأغنية
class SongGame:
    def __init__(self):
        self.songs = [
            {"lyrics":"أنا بلياك إذا أرمش إلك تنزل ألف دمعة","singer":"ماجد المهندس"},
            {"lyrics":"يا بعدهم كلهم .. يا سراجي بينهم","singer":"عبدالمجيد عبدالله"},
            {"lyrics":"قولي أحبك كي تزيد وسامتي","singer":"كاظم الساهر"},
            {"lyrics":"كيف أبيّن لك شعوري دون ما أحكي","singer":"عايض"}
        ]
        self.current_song = None
        self.current_q = 0
        self.max_q = 5
        self.scores = {}
        self.hints_used = 0
    
    def start_game(self):
        self.current_q = 1
        self.scores = {}
        return self.next_question()
    
    def next_question(self):
        if self.current_q > self.max_q: 
            return None
        self.current_song = random.choice(self.songs)
        self.hints_used = 0
        return FlexSendMessage(
            alt_text=f"السؤال {self.current_q}",
            contents=create_game_card(
                game_header("لعبة الأغنية",f"السؤال {self.current_q}/{self.max_q}"),
                [
                    glass_box([{"type":"text","text":self.current_song['lyrics'],"size":"lg","color":C['text'],"align":"center","wrap":True,"weight":"bold"}],"24px"),
                    {"type":"text","text":"من المغني؟","size":"md","color":C['glow'],"align":"center","margin":"lg","weight":"bold"},
                    progress_bar(self.current_q, self.max_q)
                ],
                [btn("لمح","لمح"),btn("جاوب","جاوب")]
            )
        )
    
    def check_answer(self, text, user_id, name):
        ans = text.strip().lower()
        
        if ans in ['لمح','تلميح']:
            if self.hints_used > 0:
                return {'response':TextSendMessage(text="تم استخدام التلميح"),'correct':False}
            self.hints_used = 1
            singer = self.current_song['singer']
            hint = singer[0] + " " + "_ " * (len(singer) - 1)
            return {
                'response':FlexSendMessage(alt_text="تلميح",
                    contents=create_game_card(game_header("تلميح","الحرف الأول + عدد الحروف"), [
                        glass_box([{"type":"text","text":hint,"size":"3xl","weight":"bold","color":C['glow'],"align":"center","letterSpacing":"4px"}],"32px")
                    ])
                ),
                'correct':False
            }
        
        if ans in ['جاوب','الجواب','الحل']:
            self.current_q += 1
            return {
                'response':FlexSendMessage(alt_text="الحل",
                    contents=create_game_card(game_header("الحل","الإجابة الصحيحة"), [
                        glass_box([{"type":"text","text":self.current_song['singer'],"size":"xxl","color":C['glow'],"weight":"bold","align":"center","wrap":True}],"28px")
                    ])
                ),
                'correct':False,
                'next_question':self.current_q <= self.max_q
            }
        
        if normalize_text(text) == normalize_text(self.current_song['singer']):
            points = 2 if self.hints_used == 0 else 1
            if user_id not in self.scores:
                self.scores[user_id] = {'name':name,'score':0}
            self.scores[user_id]['score'] += points
            self.current_q += 1
            return {
                'response':FlexSendMessage(alt_text="صحيح",
                    contents=create_game_card(game_header("إجابة صحيحة","أحسنت"), [
                        glass_box([
                            {"type":"text","text":name,"size":"xl","weight":"bold","color":C['text'],"align":"center"},
                            {"type":"text","text":f"+{points} نقطة","size":"xxl","color":C['glow'],"align":"center","margin":"md","weight":"bold"}
                        ],"28px")
                    ])
                ),
                'correct':True,
                'points':points,
                'won':True,
                'next_question':self.current_q <= self.max_q
            }
        
        return None

# 2. لعبة الأضداد
class OppositeGame:
    def __init__(self):
        self.words = [
            {"word":"كبير","opposite":"صغير"},
            {"word":"طويل","opposite":"قصير"},
            {"word":"سريع","opposite":"بطيء"},
            {"word":"ساخن","opposite":"بارد"},
            {"word":"قوي","opposite":"ضعيف"}
        ]
        self.current_word = None
        self.current_q = 0
        self.max_q = 5
        self.scores = {}
        self.hints_used = 0
    
    def start_game(self):
        self.current_q = 1
        self.scores = {}
        return self.next_question()
    
    def next_question(self):
        if self.current_q > self.max_q:
            return None
        self.current_word = random.choice(self.words)
        self.hints_used = 0
        return FlexSendMessage(
            alt_text=f"السؤال {self.current_q}",
            contents=create_game_card(
                game_header("لعبة الأضداد",f"السؤال {self.current_q}/{self.max_q}"),
                [
                    glass_box([
                        {"type":"text","text":"ما هو عكس","size":"sm","color":C['text2'],"align":"center"},
                        {"type":"text","text":self.current_word['word'],"size":"5xl","weight":"bold","color":C['glow'],"align":"center","margin":"md"}
                    ],"32px"),
                    progress_bar(self.current_q, self.max_q)
                ],
                [btn("لمح","لمح"),btn("جاوب","جاوب")]
            )
        )
    
    def check_answer(self, text, user_id, name):
        ans = text.strip().lower()
        
        if ans in ['لمح','تلميح']:
            if self.hints_used > 0:
                return {'response':TextSendMessage(text="تم استخدام التلميح"),'correct':False}
            self.hints_used = 1
            opposite = self.current_word['opposite']
            hint = opposite[0] + " " + "_ " * (len(opposite) - 1)
            return {
                'response':FlexSendMessage(alt_text="تلميح",
                    contents=create_game_card(game_header("تلميح","الحرف الأول + عدد الحروف"), [
                        glass_box([{"type":"text","text":hint,"size":"3xl","weight":"bold","color":C['glow'],"align":"center","letterSpacing":"4px"}],"32px")
                    ])
                ),
                'correct':False
            }
        
        if ans in ['جاوب','الجواب','الحل']:
            self.current_q += 1
            return {
                'response':FlexSendMessage(alt_text="الحل",
                    contents=create_game_card(game_header("الحل","الإجابة الصحيحة"), [
                        glass_box([{"type":"text","text":f"{self.current_word['word']} ↔ {self.current_word['opposite']}",
                            "size":"xl","color":C['glow'],"weight":"bold","align":"center","wrap":True}],"28px")
                    ])
                ),
                'correct':False,
                'next_question':self.current_q <= self.max_q
            }
        
        if normalize_text(text) == normalize_text(self.current_word['opposite']):
            points = 2 if self.hints_used == 0 else 1
            if user_id not in self.scores:
                self.scores[user_id] = {'name':name,'score':0}
            self.scores[user_id]['score'] += points
            self.current_q += 1
            return {
                'response':FlexSendMessage(alt_text="صحيح",
                    contents=create_game_card(game_header("صحيح","إجابة ممتازة"), [
                        glass_box([
                            {"type":"text","text":name,"size":"xl","weight":"bold","color":C['text'],"align":"center"},
                            {"type":"text","text":f"+{points} نقطة","size":"xxl","color":C['glow'],"align":"center","margin":"md","weight":"bold"}
                        ],"28px")
                    ])
                ),
                'correct':True,
                'points':points,
                'next_question':self.current_q <= self.max_q
            }
        
        return None

# 3. لعبة سلسلة الكلمات
class ChainGame:
    def __init__(self):
        self.start_words = ["قلم","كتاب","مدرسة","باب","نافذة"]
        self.current_word = None
        self.used = set()
        self.round = 0
        self.max_rounds = 5
        self.scores = {}
    
    def start_game(self):
        self.current_word = random.choice(self.start_words)
        self.used = {normalize_text(self.current_word)}
        self.round = 1
        self.scores = {}
        return FlexSendMessage(
            alt_text="سلسلة الكلمات",
            contents=create_game_card(
                game_header("سلسلة الكلمات",f"الجولة {self.round}/{self.max_rounds}"),
                [
                    glass_box([
                        {"type":"text","text":"الكلمة السابقة","size":"sm","color":C['text2'],"align":"center"},
                        {"type":"text","text":self.current_word,"size":"xl","weight":"bold","color":C['text'],"align":"center","margin":"sm"}
                    ],"20px"),
                    glass_box([
                        {"type":"text","text":"ابدأ بحرف","size":"sm","color":C['text2'],"align":"center"},
                        {"type":"text","text":self.current_word[-1],"size":"5xl","weight":"bold","color":C['glow'],"align":"center","margin":"md"}
                    ],"32px"),
                    progress_bar(self.round, self.max_rounds)
                ]
            )
        )
    
    def check_answer(self, text, user_id, name):
        text = text.strip()
        last = self.current_word[-1]
        norm_last = 'ه' if last in ['ة','ه'] else last
        norm_ans = normalize_text(text)
        
        if norm_ans in self.used:
            return {'response':TextSendMessage(text="الكلمة مستخدمة"),'correct':False}
        
        first = 'ه' if text[0].lower() in ['ة','ه'] else text[0].lower()
        
        if first == norm_last:
            self.used.add(norm_ans)
            old = self.current_word
            self.current_word = text
            self.round += 1
            points = 2
            
            if user_id not in self.scores:
                self.scores[user_id] = {'name':name,'score':0}
            self.scores[user_id]['score'] += points
            
            if self.round <= self.max_rounds:
                return {
                    'response':FlexSendMessage(alt_text="صحيح",
                        contents=create_game_card(game_header("صحيح","كلمة ممتازة"), [
                            glass_box([
                                {"type":"text","text":name,"size":"xl","weight":"bold","color":C['text'],"align":"center"},
                                {"type":"text","text":f"{old} → {text}","size":"lg","color":C['text2'],"align":"center","margin":"sm"},
                                {"type":"text","text":f"+{points} نقطة","size":"xxl","color":C['glow'],"align":"center","margin":"md","weight":"bold"}
                            ],"28px")
                        ])
                    ),
                    'points':points,
                    'correct':True,
                    'next_question':True
                }
            else:
                return {'points':0,'correct':False,'won':True,'game_over':True}
        
        return {'response':TextSendMessage(text=f"يجب أن تبدأ بحرف: {last}"),'correct':False}

# 4. لعبة تكوين الكلمات
class BuildGame:
    def __init__(self):
        self.letter_sets = [
            {"letters":"ق م ر ي ل ن","words":["قمر","ليل","مرق","ريم","نيل","قرن"]},
            {"letters":"ن ج م س و ر","words":["نجم","نجوم","سور","نور","سمر","رسم"]}
        ]
        self.current_letters = []
        self.valid_words = set()
        self.used = set()
        self.current_q = 1
        self.max_q = 5
        self.words_needed = 3
        self.scores = {}
        self.hints_used = 0

    def start_game(self):
        self.current_q = 1
        self.scores = {}
        return self.next_question()

    def next_question(self):
        if self.current_q > self.max_q:
            return None
        
        letter_set = random.choice(self.letter_sets)
        self.current_letters = letter_set['letters'].split()
        self.valid_words = set(letter_set['words'])
        random.shuffle(self.current_letters)
        self.used = set()
        self.hints_used = 0

        letter_boxes = [
            {
                "type":"box","layout":"vertical",
                "contents":[{"type":"text","text":letter,"size":"xxl","weight":"bold","color":C['glow'],"align":"center"}],
                "backgroundColor":C['card'],"cornerRadius":"16px","width":"55px","height":"60px",
                "justifyContent":"center","borderWidth":"2px","borderColor":C['border']
            } 
            for letter in self.current_letters
        ]
        row1, row2 = letter_boxes[:3], letter_boxes[3:]

        return FlexSendMessage(
            alt_text=f"الجولة {self.current_q}",
            contents=create_game_card(
                game_header("تكوين الكلمات",f"الجولة {self.current_q}/{self.max_q}"),
                [
                    {"type":"box","layout":"vertical","contents":[
                        {"type":"box","layout":"horizontal","contents":row1,"spacing":"sm","justifyContent":"center"},
                        {"type":"box","layout":"horizontal","contents":row2,"spacing":"sm","justifyContent":"center","margin":"sm"}
                    ],"margin":"lg"},
                    glass_box([{"type":"text","text":f"كوّن {self.words_needed} كلمات صحيحة","size":"sm","color":C['text'],"align":"center","wrap":True}],"16px"),
                    progress_bar(self.current_q, self.max_q)
                ],
                [btn("لمح","لمح"),btn("جاوب","جاوب")]
            )
        )

    def check_answer(self, text, user_id, name):
        ans = text.strip().lower()
        
        if ans in ['لمح','تلميح']:
            if self.hints_used > 0:
                return {'response':TextSendMessage(text="تم استخدام التلميح"),'correct':False}
            self.hints_used = 1
            example = random.choice(list(self.valid_words))
            hint = example[0] + " " + "_ " * (len(example) - 1)
            return {
                'response':FlexSendMessage(alt_text="تلميح",
                    contents=create_game_card(game_header("تلميح","الحرف الأول + عدد الحروف"), [
                        glass_box([{"type":"text","text":hint,"size":"3xl","weight":"bold","color":C['glow'],"align":"center","letterSpacing":"6px"}],"28px")
                    ])
                ),
                'correct':False
            }

        if ans in ['جاوب','الحل']:
            suggestions = sorted(self.valid_words, key=len, reverse=True)[:4]
            self.current_q += 1
            return {
                'response':FlexSendMessage(alt_text="الحل",
                    contents=create_game_card(game_header("الحل","بعض الكلمات الصحيحة"), [
                        glass_box([{"type":"text","text":" • ".join(suggestions),"size":"lg","color":C['glow'],"weight":"bold","align":"center","wrap":True}],"24px")
                    ])
                ),
                'correct':False,
                'next_question':self.current_q <= self.max_q
            }

        word = normalize_text(text)
        if word in self.used:
            return {'response':TextSendMessage(text=f"الكلمة '{text}' مستخدمة"),'correct':False}

        letters_copy = self.current_letters.copy()
        can_form = all(c in letters_copy and (letters_copy.remove(c) or True) for c in word)
        if not can_form:
            return {'response':TextSendMessage(text=f"لا يمكن تكوين '{text}'"),'correct':False}
        
        if len(word) < 2:
            return {'response':TextSendMessage(text="حرفين على الأقل"),'correct':False}
        
        if word not in {normalize_text(w) for w in self.valid_words}:
            return {'response':TextSendMessage(text=f"'{text}' ليست صحيحة"),'correct':False}

        self.used.add(word)
        points = 2 if not self.hints_used else 1
        
        if user_id not in self.scores:
            self.scores[user_id] = {'name':name,'score':0,'words':0}
        self.scores[user_id]['score'] += points
        self.scores[user_id]['words'] += 1

        if self.scores[user_id]['words'] >= self.words_needed:
            self.current_q += 1
            return {
                'response':FlexSendMessage(alt_text="أحسنت",
                    contents=create_game_card(game_header("أحسنت","أكملت الجولة"), [
                        glass_box([
                            {"type":"text","text":name,"size":"xl","weight":"bold","color":C['text'],"align":"center"},
                            {"type":"text","text":f"+{points} نقطة","size":"xxl","color":C['glow'],"align":"center","margin":"md","weight":"bold"}
                        ],"28px")
                    ])
                ),
                'correct':True,
                'won_round':True,
                'next_question':self.current_q <= self.max_q
            }

        return {'response':TextSendMessage(text=f"'{text}' صحيحة! +{points}"),'correct':True}

# 5. لعبة ترتيب الحروف
class OrderGame:
    def __init__(self):
        self.words = ["مدرسة","حديقة","كتاب","طائرة","مطعم"]
        self.current_word = None
        self.shuffled = None
        self.current_q = 0
        self.max_q = 5
        self.scores = {}
    
    def start_game(self):
        self.current_q = 1
        self.scores = {}
        return self.next_question()
    
    def next_question(self):
        if self.current_q > self.max_q:
            return None
        
        self.current_word = random.choice(self.words)
        letters = list(self.current_word)
        random.shuffle(letters)
        self.shuffled = ''.join(letters)
        
        return FlexSendMessage(
            alt_text=f"السؤال {self.current_q}",
            contents=create_game_card(
                game_header("ترتيب الحروف",f"السؤال {self.current_q}/{self.max_q}"),
                [
                    glass_box([
                        {"type":"text","text":"رتب الحروف","size":"sm","color":C['text2'],"align":"center"},
                        {"type":"text","text":self.shuffled,"size":"4xl","weight":"bold","color":C['glow'],"align":"center","margin":"md","letterSpacing":"10px"}
                    ],"32px"),
                    progress_bar(self.current_q, self.max_q)
                ]
            )
        )
    
    def check_answer(self, text, user_id, name):
        if normalize_text(text) == normalize_text(self.current_word):
            points = 2
            self.current_q += 1
            if user_id not in self.scores:
                self.scores[user_id] = {'name':name,'score':0}
            self.scores[user_id]['score'] += points
            return {
                'response':FlexSendMessage(alt_text="صحيح",
                    contents=create_game_card(game_header("صحيح","ممتاز"), [
                        glass_box([
                            {"type":"text","text":name,"size":"xl","weight":"bold","color":C['text'],"align":"center"},
                            {"type":"text","text":self.current_word,"size":"3xl","color":C['glow'],"align":"center","margin":"md","weight":"bold"},
                            {"type":"text","text":f"+{points} نقطة","size":"xxl","color":C['cyan'],"align":"center","margin":"md","weight":"bold"}
                        ],"28px")
                    ])
                ),
                'correct':True,
                'points':points,
                'next_question':self.current_q <= self.max_q
            }
        return None

# 6. لعبة أطول كلمة
class WordGame:
    def __init__(self):
        self.categories = ["حيوان","نبات","بلد","طعام"]
        self.current_category = None
        self.current_q = 0
        self.max_q = 5
        self.scores = {}
        self.answers = {}
    
    def start_game(self):
        self.current_q = 1
        self.scores = {}
        self.answers = {}
        return self.next_question()
    
    def next_question(self):
        if self.current_q > self.max_q:
            return None
        
        self.current_category = random.choice(self.categories)
        self.answers = {}
        
        return FlexSendMessage(
            alt_text=f"الجولة {self.current_q}",
            contents=create_game_card(
                game_header("أطول كلمة",f"الجولة {self.current_q}/{self.max_q}"),
                [
                    glass_box([
                        {"type":"text","text":"اكتب أطول كلمة من فئة","size":"sm","color":C['text2'],"align":"center"},
                        {"type":"text","text":self.current_category,"size":"4xl","weight":"bold","color":C['glow'],"align":"center","margin":"md"}
                    ],"32px"),
                    progress_bar(self.current_q, self.max_q)
                ]
            )
        )
    
    def check_answer(self, text, user_id, name):
        if user_id in self.answers:
            return None
        
        word = text.strip()
        if len(word) >= 3:
            self.answers[user_id] = {'name':name,'word':word,'length':len(word)}
            
            if len(self.answers) >= 3:
                winner = max(self.answers.items(), key=lambda x: x[1]['length'])
                points = 3
                self.current_q += 1
                
                if winner[0] not in self.scores:
                    self.scores[winner[0]] = {'name':winner[1]['name'],'score':0}
                self.scores[winner[0]]['score'] += points
                
                return {
                    'response':FlexSendMessage(alt_text="الفائز",
                        contents=create_game_card(game_header("الفائز","أطول كلمة"), [
                            glass_box([
                                {"type":"text","text":winner[1]['name'],"size":"xl","weight":"bold","color":C['text'],"align":"center"},
                                {"type":"text","text":winner[1]['word'],"size":"3xl","color":C['glow'],"align":"center","margin":"md","weight":"bold"},
                                {"type":"text","text":f"{winner[1]['length']} حرف - +{points} نقطة","size":"lg","color":C['cyan'],"align":"center","margin":"md"}
                            ],"28px")
                        ])
                    ),
                    'correct':True,
                    'points':points,
                    'next_question':self.current_q <= self.max_q
                }
            
            return {'response':TextSendMessage(text=f"تم تسجيل: {word} ({len(word)} حرف)"),'correct':True}
        
        return None

# 7. لعبة تخمين اللون
class ColorGame:
    def __init__(self):
        self.colors = [
            {"name":"أحمر","hex":"#EF4444"},
            {"name":"أزرق","hex":"#3B82F6"},
            {"name":"أخضر","hex":"#10B981"},
            {"name":"أصفر","hex":"#F59E0B"},
            {"name":"برتقالي","hex":"#F97316"}
        ]
        self.current_color = None
        self.current_q = 0
        self.max_q = 5
        self.scores = {}
        self.hints_used = 0
    
    def start_game(self):
        self.current_q = 1
        self.scores = {}
        return self.next_question()
    
    def next_question(self):
        if self.current_q > self.max_q:
            return None
        
        self.current_color = random.choice(self.colors)
        self.hints_used = 0
        
        return FlexSendMessage(
            alt_text=f"السؤال {self.current_q}",
            contents=create_game_card(
                game_header("تخمين اللون",f"السؤال {self.current_q}/{self.max_q}"),
                [
                    glass_box([
                        {"type":"text","text":"ما هذا اللون؟","size":"sm","color":C['text2'],"align":"center"},
                        {"type":"box","layout":"vertical","contents":[],"height":"140px","backgroundColor":self.current_color['hex'],
                         "cornerRadius":"20px","margin":"md","borderWidth":"3px","borderColor":"#ffffff30"}
                    ],"32px"),
                    progress_bar(self.current_q, self.max_q)
                ],
                [btn("لمح","لمح")]
            )
        )
    
    def check_answer(self, text, user_id, name):
        ans = text.strip().lower()
        
        if ans in ['لمح','تلميح']:
            if self.hints_used > 0:
                return {'response':TextSendMessage(text="تم استخدام التلميح"),'correct':False}
            self.hints_used = 1
            hint = self.current_color['name'][0] + " " + "_ " * (len(self.current_color['name']) - 1)
            return {
                'response':FlexSendMessage(alt_text="تلميح",
                    contents=create_game_card(game_header("تلميح","الحرف الأول"), [
                        glass_box([{"type":"text","text":hint,"size":"3xl","color":C['glow'],"align":"center","weight":"bold","letterSpacing":"6px"}],"28px")
                    ])
                ),
                'correct':False
            }
        
        if normalize_text(text) == normalize_text(self.current_color['name']):
            points = 2 if self.hints_used == 0 else 1
            self.current_q += 1
            
            if user_id not in self.scores:
                self.scores[user_id] = {'name':name,'score':0}
            self.scores[user_id]['score'] += points
            
            return {
                'response':FlexSendMessage(alt_text="صحيح",
                    contents=create_game_card(game_header("صحيح","ممتاز"), [
                        glass_box([
                            {"type":"text","text":name,"size":"xl","weight":"bold","color":C['text'],"align":"center"},
                            {"type":"text","text":self.current_color['name'],"size":"3xl","color":self.current_color['hex'],"align":"center","margin":"md","weight":"bold"},
                            {"type":"text","text":f"+{points} نقطة","size":"xxl","color":C['glow'],"align":"center","margin":"md","weight":"bold"}
                        ],"28px")
                    ])
                ),
                'correct':True,
                'points':points,
                'next_question':self.current_q <= self.max_q
            }
        
        return None

# 8. لعبة السرعة
class FastGame:
    def __init__(self):
        self.questions = [
            {"q":"كم عدد أيام الأسبوع؟","a":"7"},
            {"q":"ما عاصمة السعودية؟","a":"الرياض"},
            {"q":"كم عدد الألوان في قوس قزح؟","a":"7"},
            {"q":"ما أكبر كوكب؟","a":"المشتري"}
        ]
        self.current_question = None
        self.current_q = 0
        self.max_q = 5
        self.scores = {}
    
    def start_game(self):
        self.current_q = 1
        self.scores = {}
        return self.next_question()
    
    def next_question(self):
        if self.current_q > self.max_q:
            return None
        
        self.current_question = random.choice(self.questions)
        
        return FlexSendMessage(
            alt_text=f"السؤال {self.current_q}",
            contents=create_game_card(
                game_header("لعبة السرعة",f"السؤال {self.current_q}/{self.max_q}"),
                [
                    glass_box([
                        {"type":"text","text":self.current_question['q'],"size":"lg","color":C['text'],"align":"center","wrap":True,"weight":"bold"}
                    ],"24px"),
                    {"type":"text","text":"أسرع إجابة تفوز","size":"sm","color":C['glow'],"align":"center","margin":"md"},
                    progress_bar(self.current_q, self.max_q)
                ]
            )
        )
    
    def check_answer(self, text, user_id, name):
        if normalize_text(text) == normalize_text(self.current_question['a']):
            points = 3
            self.current_q += 1
            
            if user_id not in self.scores:
                self.scores[user_id] = {'name':name,'score':0}
            self.scores[user_id]['score'] += points
            
            return {
                'response':FlexSendMessage(alt_text="صحيح",
                    contents=create_game_card(game_header("إجابة صحيحة","الأسرع"), [
                        glass_box([
                            {"type":"text","text":name,"size":"xl","weight":"bold","color":C['text'],"align":"center"},
                            {"type":"text","text":"🏆","size":"5xl","align":"center","margin":"sm"},
                            {"type":"text","text":f"+{points} نقطة","size":"xxl","color":C['glow'],"align":"center","margin":"md","weight":"bold"}
                        ],"28px")
                    ])
                ),
                'correct':True,
                'points':points,
                'next_question':self.current_q <= self.max_q
            }
        
        return None

# 9. لعبة الألغاز
class GameQuiz:
    def __init__(self):
        self.riddles = [
            {"q":"ما الشيء الذي له أسنان ولا يعض؟","a":"المشط"},
            {"q":"ما الشيء الذي يكتب ولا يقرأ؟","a":"القلم"},
            {"q":"ما الشيء الذي له عين واحدة ولا يرى؟","a":"الإبرة"},
            {"q":"ما الشيء الذي يجري ولا يمشي؟","a":"الماء"}
        ]
        self.current_riddle = None
        self.current_q = 0
        self.max_q = 5
        self.scores = {}
        self.hints_used = 0
    
    def start_game(self):
        self.current_q = 1
        self.scores = {}
        return self.next_question()
    
    def next_question(self):
        if self.current_q > self.max_q:
            return None
        
        self.current_riddle = random.choice(self.riddles)
        self.hints_used = 0
        
        return FlexSendMessage(
            alt_text=f"السؤال {self.current_q}",
            contents=create_game_card(
                game_header("لعبة الألغاز",f"السؤال {self.current_q}/{self.max_q}"),
                [
                    glass_box([
                        {"type":"text","text":"🤔","size":"4xl","align":"center"},
                        {"type":"text","text":self.current_riddle['q'],"size":"lg","color":C['text'],"align":"center","wrap":True,"weight":"bold","margin":"md"}
                    ],"28px"),
                    progress_bar(self.current_q, self.max_q)
                ],
                [btn("لمح","لمح"),btn("جاوب","جاوب")]
            )
        )
    
    def check_answer(self, text, user_id, name):
        ans = text.strip().lower()
        
        if ans in ['لمح','تلميح']:
            if self.hints_used > 0:
                return {'response':TextSendMessage(text="تم استخدام التلميح"),'correct':False}
            self.hints_used = 1
            answer = self.current_riddle['a']
            hint = answer[0] + " " + "_ " * (len(answer) - 1)
            return {
                'response':FlexSendMessage(alt_text="تلميح",
                    contents=create_game_card(game_header("تلميح","الحرف الأول"), [
                        glass_box([{"type":"text","text":hint,"size":"3xl","weight":"bold","color":C['glow'],"align":"center","letterSpacing":"6px"}],"28px")
                    ])
                ),
                'correct':False
            }
        
        if ans in ['جاوب','الجواب','الحل']:
            self.current_q += 1
            return {
                'response':FlexSendMessage(alt_text="الحل",
                    contents=create_game_card(game_header("الحل","الإجابة الصحيحة"), [
                        glass_box([{"type":"text","text":self.current_riddle['a'],"size":"xxl","color":C['glow'],"weight":"bold","align":"center","wrap":True}],"28px")
                    ])
                ),
                'correct':False,
                'next_question':self.current_q <= self.max_q
            }
        
        if normalize_text(text) == normalize_text(self.current_riddle['a']):
            points = 2 if self.hints_used == 0 else 1
            self.current_q += 1
            
            if user_id not in self.scores:
                self.scores[user_id] = {'name':name,'score':0}
            self.scores[user_id]['score'] += points
            
            return {
                'response':FlexSendMessage(alt_text="صحيح",
                    contents=create_game_card(game_header("إجابة صحيحة","عبقري"), [
                        glass_box([
                            {"type":"text","text":name,"size":"xl","weight":"bold","color":C['text'],"align":"center"},
                            {"type":"text","text":f"+{points} نقطة","size":"xxl","color":C['glow'],"align":"center","margin":"md","weight":"bold"}
                        ],"28px")
                    ])
                ),
                'correct':True,
                'points':points,
                'next_question':self.current_q <= self.max_q
            }
        
        return None

# ==================== إدارة الألعاب ====================

# خريطة الألعاب
GAME_CLASSES = {
    'song': SongGame,
    'opposite': OppositeGame,
    'chain': ChainGame,
    'build': BuildGame,
    'order': OrderGame,
    'word': WordGame,
    'color': ColorGame,
    'fast': FastGame,
    'game': GameQuiz
}

GAME_NAMES = {
    'song': 'لعبة الأغنية',
    'opposite': 'لعبة الأضداد',
    'chain': 'سلسلة الكلمات',
    'build': 'تكوين الكلمات',
    'order': 'ترتيب الحروف',
    'word': 'أطول كلمة',
    'color': 'تخمين اللون',
    'fast': 'لعبة السرعة',
    'game': 'لعبة الألغاز'
}

def start_game(game_type, group_id, active_games, line_bot_api, event):
    """بدء لعبة جديدة"""
    if group_id in active_games:
        current_game = active_games[group_id]['type']
        return TextSendMessage(text=f"يوجد لعبة نشطة: {GAME_NAMES.get(current_game, current_game)}\nأوقفها أولاً: إيقاف")
    
    if game_type not in GAME_CLASSES:
        return TextSendMessage(text="لعبة غير معروفة")
    
    game_instance = GAME_CLASSES[game_type]()
    active_games[group_id] = {
        'type': game_type,
        'instance': game_instance
    }
    
    return game_instance.start_game()

def check_game_answer(group_id, text, user_id, name, active_games, line_bot_api, update_points_func):
    """التحقق من إجابة اللاعب"""
    if group_id not in active_games:
        return None
    
    game_data = active_games[group_id]
    game_instance = game_data['instance']
    game_type = game_data['type']
    
    result = game_instance.check_answer(text, user_id, name)
    
    if not result:
        return None
    
    # تحديث النقاط إذا كانت الإجابة صحيحة
    if result.get('correct') and result.get('points'):
        update_points_func(user_id, name, result['points'], result.get('won', False))
    
    # التحقق من نهاية اللعبة
    if result.get('game_over') or (not result.get('next_question') and game_instance.current_q > game_instance.max_q):
        final_scores = game_instance.scores
        
        # تحديث النقاط النهائية للجميع
        for uid, score_data in final_scores.items():
            if uid != user_id:  # تم تحديث النقاط للمستخدم الحالي أعلاه
                update_points_func(uid, score_data['name'], 0, False)
        
        # حذف اللعبة
        del active_games[group_id]
        
        # إرسال بطاقة النتائج النهائية
        if result.get('response'):
            line_bot_api.push_message(group_id, result['response'])
        
        return game_over_card(GAME_NAMES.get(game_type, game_type), final_scores)
    
    # السؤال التالي
    if result.get('next_question'):
        next_q = game_instance.next_question()
        if next_q:
            if result.get('response'):
                line_bot_api.push_message(group_id, result['response'])
            return next_q
        else:
            # انتهت الأسئلة
            final_scores = game_instance.scores
            del active_games[group_id]
            
            if result.get('response'):
                line_bot_api.push_message(group_id, result['response'])
            
            return game_over_card(GAME_NAMES.get(game_type, game_type), final_scores)
    
    return result.get('response')
