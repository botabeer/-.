"""ملف الألعاب - تصميم ثري دي زجاجي متوهج"""
from linebot.models import TextSendMessage, FlexSendMessage, ImageSendMessage
import random, re, hashlib

# ألوان موحدة مع التصميم الثري دي
C = {
    'bg':'#0A1628',           # خلفية داكنة
    'card':'#0F2847',         # بطاقة زجاجية
    'card2':'#1A3A5C',        # بطاقة ثانوية
    'text':'#E0F2FF',         # نص أبيض مزرق
    'text2':'#7FB3D5',        # نص ثانوي
    'sep':'#2C5F8D',          # فاصل
    'cyan':'#00D9FF',         # أزرق سماوي
    'cyan_glow':'#5EEBFF',    # سماوي متوهج
    'purple':'#8B7FFF',       # بنفسجي
    'success':'#00E5A0',      # أخضر نجاح
    'border':'#00D9FF40'      # حدود شفافة متوهجة
}

PISCES_LOGO = "♓"

def normalize_text(t):
    """تطبيع النص العربي"""
    if not t: return ""
    t = t.strip().lower()
    t = re.sub('[أإآ]','ا',t)
    t = re.sub('[ؤ]','و',t)
    t = re.sub('[ئ]','ي',t)
    t = re.sub('[ءةى]','',t)
    t = re.sub('[\u064B-\u065F]','',t)
    return re.sub(r'\s+',' ',t).strip()

def glass_box(contents, padding="20px", margin="md"):
    """صندوق زجاجي ثري دي مع حدود متوهجة"""
    return {
        "type":"box",
        "layout":"vertical",
        "contents":contents,
        "backgroundColor":C['card'],
        "cornerRadius":"20px",
        "paddingAll":padding,
        "margin":margin,
        "borderWidth":"2px",
        "borderColor":C['border']
    }

def glow_text(text, size="xl", color=None):
    """نص متوهج"""
    return {
        "type":"text",
        "text":text,
        "size":size,
        "weight":"bold",
        "color":color or C['cyan_glow'],
        "align":"center"
    }

def progress_bar(current, total):
    """شريط تقدم ثري دي متوهج"""
    return {
        "type":"box",
        "layout":"horizontal",
        "contents":[
            {
                "type":"box",
                "layout":"vertical",
                "contents":[],
                "backgroundColor":C['cyan'],
                "height":"8px",
                "flex":current,
                "cornerRadius":"4px"
            },
            {
                "type":"box",
                "layout":"vertical",
                "contents":[],
                "backgroundColor":C['card2'],
                "height":"8px",
                "flex":max(1, total-current),
                "cornerRadius":"4px"
            }
        ],
        "spacing":"xs",
        "margin":"xl"
    }

def game_header(icon, title, subtitle):
    """هيدر موحد للألعاب - ثري دي زجاجي"""
    return [
        # أيقونة الشعار
        glass_box([
            {"type":"text","text":icon,"size":"4xl","align":"center","color":C['cyan_glow']}
        ],"16px","none"),
        # العنوان
        {"type":"text","text":title,"size":"xxl","weight":"bold","color":C['cyan'],"align":"center","margin":"md"},
        # العنوان الفرعي
        {"type":"text","text":subtitle,"size":"sm","color":C['text2'],"align":"center","margin":"sm"},
        # فاصل
        {"type":"separator","margin":"lg","color":C['sep']}
    ]

def create_button(label, text, is_primary=False):
    """زر موحد مع التصميم الثري دي"""
    btn = {
        "type":"button",
        "action":{"type":"message","label":label,"text":text},
        "style":"primary" if is_primary else "secondary",
        "height":"md"
    }
    if is_primary:
        btn["color"] = C['cyan']
    return btn

# ===============================================
# 1. لعبة الأغنية 🎵
# ===============================================
class SongGame:
    def __init__(self):
        self.songs = [
            {"lyrics":"أنا بلياك إذا أرمش إلك تنزل ألف دمعة","singer":"ماجد المهندس"},
            {"lyrics":"يا بعدهم كلهم .. يا سراجي بينهم","singer":"عبدالمجيد عبدالله"},
            {"lyrics":"قولي أحبك كي تزيد وسامتي","singer":"كاظم الساهر"},
            {"lyrics":"كيف أبيّن لك شعوري دون ما أحكي","singer":"عايض"},
            {"lyrics":"أريد الله يسامحني لان أذيت نفسي","singer":"رحمة رياض"},
            {"lyrics":"مشتاق ولهان ودموعي سايلة","singer":"راشد الماجد"},
            {"lyrics":"حبيبي يا نور العين يا ساكن خيالي","singer":"عمرو دياب"}
        ]
        self.current_song, self.current_q, self.max_q = None, 0, 5
        self.scores, self.hints_used = {}, 0
    
    def start_game(self):
        self.current_q, self.scores = 1, {}
        return self.next_question()
    
    def next_question(self):
        if self.current_q > self.max_q: return None
        self.current_song = random.choice(self.songs)
        self.hints_used = 0
        
        return FlexSendMessage(
            alt_text=f"السؤال {self.current_q}",
            contents={
                "type":"bubble","size":"mega",
                "body":{
                    "type":"box","layout":"vertical",
                    "contents":game_header("🎵","لعبة الأغنية",f"السؤال {self.current_q}/{self.max_q}") + [
                        glass_box([
                            {"type":"text","text":self.current_song['lyrics'],"size":"lg",
                             "color":C['text'],"align":"center","wrap":True,"weight":"bold"}
                        ],"24px"),
                        {"type":"text","text":"من المغني؟","size":"md","color":C['cyan_glow'],
                         "align":"center","margin":"lg","weight":"bold"},
                        progress_bar(self.current_q, self.max_q)
                    ],
                    "backgroundColor":C['bg'],"paddingAll":"24px"
                },
                "footer":{
                    "type":"box","layout":"horizontal",
                    "contents":[
                        create_button("💡 لمح","لمح"),
                        create_button("📝 جاوب","جاوب")
                    ],
                    "spacing":"sm","backgroundColor":C['bg'],"paddingAll":"16px"
                }
            }
        )
    
    def check_answer(self, text, user_id, name):
        ans = text.strip().lower()
        
        if ans in ['لمح','تلميح','hint']:
            if self.hints_used > 0:
                return {'response':TextSendMessage(text="⚠️ تم استخدام التلميح"),'correct':False}
            self.hints_used = 1
            
            # التلميح: الحرف الأول + عدد الحروف
            singer = self.current_song['singer']
            first = singer[0]
            hint_pattern = first + " " + "_ " * (len(singer) - 1)
            
            return {
                'response':FlexSendMessage(
                    alt_text="تلميح",
                    contents={
                        "type":"bubble","size":"mega",
                        "body":{
                            "type":"box","layout":"vertical",
                            "contents":game_header("💡","تلميح","الحرف الأول + عدد الحروف") + [
                                glass_box([
                                    {"type":"text","text":hint_pattern,"size":"3xl","weight":"bold",
                                     "color":C['cyan_glow'],"align":"center","letterSpacing":"4px"}
                                ],"32px"),
                                {"type":"text","text":"⚠️ استخدام التلميح يقلل النقاط للنصف",
                                 "size":"xs","color":C['purple'],"align":"center","margin":"lg"}
                            ],
                            "backgroundColor":C['bg'],"paddingAll":"24px"
                        }
                    }
                ),
                'correct':False
            }
        
        if ans in ['جاوب','الجواب','الحل','answer']:
            self.current_q += 1
            return {
                'response':FlexSendMessage(
                    alt_text="الحل",
                    contents={
                        "type":"bubble","size":"mega",
                        "body":{
                            "type":"box","layout":"vertical",
                            "contents":game_header("📝","الحل","الإجابة الصحيحة") + [
                                glass_box([
                                    {"type":"text","text":self.current_song['singer'],"size":"xxl",
                                     "color":C['cyan_glow'],"weight":"bold","align":"center","wrap":True}
                                ],"28px")
                            ],
                            "backgroundColor":C['bg'],"paddingAll":"24px"
                        }
                    }
                ),
                'correct':False,
                'next_question':self.current_q<=self.max_q
            }
        
        if normalize_text(text) == normalize_text(self.current_song['singer']):
            points = 2 if self.hints_used == 0 else 1
            if user_id not in self.scores:
                self.scores[user_id] = {'name':name,'score':0}
            self.scores[user_id]['score'] += points
            self.current_q += 1
            
            return {
                'response':FlexSendMessage(
                    alt_text="صحيح",
                    contents={
                        "type":"bubble","size":"mega",
                        "body":{
                            "type":"box","layout":"vertical",
                            "contents":game_header("✨","إجابة صحيحة!","أحسنت") + [
                                glass_box([
                                    {"type":"text","text":name,"size":"xl","weight":"bold",
                                     "color":C['text'],"align":"center"},
                                    {"type":"text","text":f"+{points} نقطة","size":"xxl",
                                     "color":C['cyan_glow'],"align":"center","margin":"md","weight":"bold"}
                                ],"28px")
                            ],
                            "backgroundColor":C['bg'],"paddingAll":"24px"
                        }
                    }
                ),
                'correct':True,
                'points':points,
                'won':True,
                'next_question':self.current_q<=self.max_q
            }
        
        return None

# ===============================================
# 2. لعبة الأضداد 🔄 (مع تلميحات)
# ===============================================
class OppositeGame:
    def __init__(self):
        self.words = [
            {"word":"كبير","opposite":"صغير"},
            {"word":"طويل","opposite":"قصير"},
            {"word":"سريع","opposite":"بطيء"},
            {"word":"ساخن","opposite":"بارد"},
            {"word":"قوي","opposite":"ضعيف"},
            {"word":"غني","opposite":"فقير"},
            {"word":"نظيف","opposite":"وسخ"},
            {"word":"جميل","opposite":"قبيح"}
        ]
        self.current_word, self.current_q, self.max_q = None, 0, 5
        self.scores, self.hints_used = {}, 0
    
    def start_game(self):
        self.current_q, self.scores = 1, {}
        return self.next_question()
    
    def next_question(self):
        if self.current_q > self.max_q: return None
        self.current_word = random.choice(self.words)
        self.hints_used = 0
        
        return FlexSendMessage(
            alt_text=f"السؤال {self.current_q}",
            contents={
                "type":"bubble","size":"mega",
                "body":{
                    "type":"box","layout":"vertical",
                    "contents":game_header("🔄","لعبة الأضداد",f"السؤال {self.current_q}/{self.max_q}") + [
                        glass_box([
                            {"type":"text","text":"ما هو عكس","size":"sm","color":C['text2'],"align":"center"},
                            {"type":"text","text":self.current_word['word'],"size":"5xl","weight":"bold",
                             "color":C['cyan_glow'],"align":"center","margin":"md"}
                        ],"32px"),
                        progress_bar(self.current_q, self.max_q)
                    ],
                    "backgroundColor":C['bg'],"paddingAll":"24px"
                },
                "footer":{
                    "type":"box","layout":"horizontal",
                    "contents":[
                        create_button("💡 لمح","لمح"),
                        create_button("📝 جاوب","جاوب")
                    ],
                    "spacing":"sm","backgroundColor":C['bg'],"paddingAll":"16px"
                }
            }
        )
    
    def check_answer(self, text, user_id, name):
        ans = text.strip().lower()
        
        if ans in ['لمح','تلميح','hint']:
            if self.hints_used > 0:
                return {'response':TextSendMessage(text="⚠️ تم استخدام التلميح"),'correct':False}
            self.hints_used = 1
            
            # التلميح: الحرف الأول + عدد الحروف
            opposite = self.current_word['opposite']
            first = opposite[0]
            hint_pattern = first + " " + "_ " * (len(opposite) - 1)
            
            return {
                'response':FlexSendMessage(
                    alt_text="تلميح",
                    contents={
                        "type":"bubble","size":"mega",
                        "body":{
                            "type":"box","layout":"vertical",
                            "contents":game_header("💡","تلميح","الحرف الأول + عدد الحروف") + [
                                glass_box([
                                    {"type":"text","text":hint_pattern,"size":"3xl","weight":"bold",
                                     "color":C['cyan_glow'],"align":"center","letterSpacing":"4px"}
                                ],"32px"),
                                {"type":"text","text":"⚠️ استخدام التلميح يقلل النقاط للنصف",
                                 "size":"xs","color":C['purple'],"align":"center","margin":"lg"}
                            ],
                            "backgroundColor":C['bg'],"paddingAll":"24px"
                        }
                    }
                ),
                'correct':False
            }
        
        if ans in ['جاوب','الجواب','الحل','answer']:
            self.current_q += 1
            return {
                'response':FlexSendMessage(
                    alt_text="الحل",
                    contents={
                        "type":"bubble","size":"mega",
                        "body":{
                            "type":"box","layout":"vertical",
                            "contents":game_header("📝","الحل","الإجابة الصحيحة") + [
                                glass_box([
                                    {"type":"text","text":f"{self.current_word['word']} ↔ {self.current_word['opposite']}",
                                     "size":"xl","color":C['cyan_glow'],"weight":"bold","align":"center","wrap":True}
                                ],"28px")
                            ],
                            "backgroundColor":C['bg'],"paddingAll":"24px"
                        }
                    }
                ),
                'correct':False,
                'next_question':self.current_q<=self.max_q
            }
        
        if normalize_text(text) == normalize_text(self.current_word['opposite']):
            points = 2 if self.hints_used == 0 else 1
            if user_id not in self.scores:
                self.scores[user_id] = {'name':name,'score':0}
            self.scores[user_id]['score'] += points
            self.current_q += 1
            
            return {
                'response':FlexSendMessage(
                    alt_text="صحيح",
                    contents={
                        "type":"bubble","size":"mega",
                        "body":{
                            "type":"box","layout":"vertical",
                            "contents":game_header("✅","صحيح!","إجابة ممتازة") + [
                                glass_box([
                                    {"type":"text","text":name,"size":"xl","weight":"bold",
                                     "color":C['text'],"align":"center"},
                                    {"type":"text","text":f"{self.current_word['word']} ↔ {self.current_word['opposite']}",
                                     "size":"lg","color":C['text2'],"align":"center","margin":"sm"},
                                    {"type":"text","text":f"+{points} نقطة","size":"xxl",
                                     "color":C['cyan_glow'],"align":"center","margin":"md","weight":"bold"}
                                ],"28px")
                            ],
                            "backgroundColor":C['bg'],"paddingAll":"24px"
                        }
                    }
                ),
                'correct':True,
                'points':points,
                'next_question':self.current_q<=self.max_q
            }
        
        return None

# ===============================================
# 3. لعبة السلسلة 🔗
# ===============================================
class ChainGame:
    def __init__(self):
        self.start_words = ["قلم","كتاب","مدرسة","باب","نافذة","طاولة","كرسي","حديقة","شجرة","زهرة"]
        self.current_word, self.used, self.round, self.max_rounds = None, set(), 0, 5
        self.scores = {}
    
    def start_game(self):
        self.current_word = random.choice(self.start_words)
        self.used = {normalize_text(self.current_word)}
        self.round, self.scores = 1, {}
        
        return FlexSendMessage(
            alt_text="سلسلة الكلمات",
            contents={
                "type":"bubble","size":"mega",
                "body":{
                    "type":"box","layout":"vertical",
                    "contents":game_header("🔗","سلسلة الكلمات",f"الجولة {self.round}/{self.max_rounds}") + [
                        glass_box([
                            {"type":"text","text":"الكلمة السابقة","size":"sm","color":C['text2'],"align":"center"},
                            {"type":"text","text":self.current_word,"size":"xl","weight":"bold",
                             "color":C['text'],"align":"center","margin":"sm"}
                        ],"20px"),
                        glass_box([
                            {"type":"text","text":"ابدأ بحرف","size":"sm","color":C['text2'],"align":"center"},
                            {"type":"text","text":self.current_word[-1],"size":"5xl","weight":"bold",
                             "color":C['cyan_glow'],"align":"center","margin":"md"}
                        ],"32px"),
                        progress_bar(self.round, self.max_rounds)
                    ],
                    "backgroundColor":C['bg'],"paddingAll":"24px"
                }
            }
        )
    
    def check_answer(self, text, user_id, name):
        text = text.strip()
        last = self.current_word[-1]
        norm_last = 'ه' if last in ['ة','ه'] else last
        norm_ans = normalize_text(text)
        
        if norm_ans in self.used:
            return {'response':TextSendMessage(text="⚠️ الكلمة مستخدمة"),'correct':False}
        
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
                    'response':FlexSendMessage(
                        alt_text="صحيح",
                        contents={
                            "type":"bubble","size":"mega",
                            "body":{
                                "type":"box","layout":"vertical",
                                "contents":game_header("✨","صحيح!","كلمة ممتازة") + [
                                    glass_box([
                                        {"type":"text","text":name,"size":"xl","weight":"bold",
                                         "color":C['text'],"align":"center"},
                                        {"type":"text","text":f"{old} → {text}","size":"lg",
                                         "color":C['text2'],"align":"center","margin":"sm"},
                                        {"type":"text","text":f"+{points} نقطة","size":"xxl",
                                         "color":C['cyan_glow'],"align":"center","margin":"md","weight":"bold"}
                                    ],"28px")
                                ],
                                "backgroundColor":C['bg'],"paddingAll":"24px"
                            }
                        }
                    ),
                    'points':points,
                    'correct':True,
                    'next_question':True
                }
            else:
                return {'points':0,'correct':False,'won':True,'game_over':True}
        else:
            return {'response':TextSendMessage(text=f"⚠️ يجب أن تبدأ بحرف: {last}"),'correct':False}

# ===============================================
# 4. لعبة تكوين الكلمات 🔤
# ===============================================
class BuildGame:
    def __init__(self):
        self.letter_sets = [
            {"letters":"ق م ر ي ل ن","words":["قمر","ليل","مرق","ريم","نيل","قرن","ملي","مير","قيل","ليم","نمر","مرن"]},
            {"letters":"ن ج م س و ر","words":["نجم","نجوم","سور","نور","سمر","رسم","جور","نمر","جرس","سجن","مرج","رسوم"]},
            {"letters":"ب ح ر ي ن ل","words":["بحر","بحرين","بحري","حرب","نحل","نيل","لبن","حبل","نبيل","نبل","ربح","بين"]}
        ]
        self.current_letters, self.valid_words, self.used = [], set(), set()
        self.current_q, self.max_q, self.words_needed = 1, 5, 3
        self.scores, self.hints_used = {}, 0
    
    def start_game(self):
        self.current_q, self.scores = 1, {}
        return self.next_question()
    
    def next_question(self):
        if self.current_q > self.max_q: return None
        
        letter_set = random.choice(self.letter_sets)
        self.current_letters = letter_set['letters'].split()
        self.valid_words = set(letter_set['words'])
        random.shuffle(self.current_letters)
        self.used, self.hints_used = set(), 0
        
        # إنشاء صناديق الحروف
        letter_boxes = []
        for letter in self.current_letters:
            letter_boxes.append({
                "type":"box","layout":"vertical",
                "contents":[
                    {"type":"text","text":letter,"size":"xxl","weight":"bold",
                     "color":C['cyan_glow'],"align":"center"}
                ],
                "backgroundColor":C['card2'],
                "cornerRadius":"16px",
                "width":"55px",
                "height":"60px",
                "justifyContent":"center",
                "borderWidth":"2px",
                "borderColor":C['border']
            })
        
        row1 = letter_boxes[:3]
        row2 = letter_boxes[3:]
        
        return FlexSendMessage(
            alt_text=f"الجولة {self.current_q}",
            contents={
                "type":"bubble","size":"mega",
                "body":{
                    "type":"box","layout":"vertical",
                    "contents":game_header("🔤","تكوين الكلمات",f"الجولة {self.current_q}/{self.max_q}") + [
                        {"type":"box","layout":"vertical","contents":[
                            {"type":"box","layout":"horizontal","contents":row1,"spacing":"sm","justifyContent":"center"},
                            {"type":"box","layout":"horizontal","contents":row2,"spacing":"sm","justifyContent":"center","margin":"sm"}
                        ],"margin":"lg"},
                        glass_box([
                            {"type":"text","text":f"كوّن {self.words_needed} كلمات صحيحة من الحروف",
                             "size":"sm","color":C['text'],"align":"center","wrap":True}
                        ],"16px"),
                        progress_bar(self.current_q, self.max_q)
                    ],
                    "backgroundColor":C['bg'],"paddingAll":"24px"
                },
                "footer":{
                    "type":"box","layout":"horizontal",
                    "contents":[
                        create_button("💡 لمح","لمح"),
                        create_button("📝 جاوب","جاوب")
                    ],
                    "spacing":"sm","backgroundColor":C['bg'],"paddingAll":"16px"
                }
            }
        )
    
    def check_answer(self, text, user_id, name):
        ans = text.strip().lower()
        
        if ans in ['لمح','تلميح','hint']:
            if self.hints_used > 0:
                return {'response':TextSendMessage(text="⚠️ تم استخدام التلميح"),'correct':False}
            self.hints_used = 1
            example = random.choice(list(self.valid_words))
            first = example[0]
            hint_pattern = first + " " + "_ " * (len(example) - 1)
            
            return {
                'response':FlexSendMessage(
                    alt_text="تلميح",
                    contents={
                        "type":"bubble","size":"mega",
                        "body":{
                            "type":"box","layout":"vertical",
                            "contents":game_header("💡","تلميح","الحرف الأول + عدد الحروف") + [
                                glass_box([
                                    {"type":"text","text":hint_pattern,"size":"3xl","weight":"bold",
                                     "color":C['cyan_glow'],"align":"center","letterSpacing":"6px"}
                                ],"28px"),
                                {"type":"text","text":"⚠️ التلميح يقلل النقاط للنصف",
                                 "size":"xs","color":C['purple'],"align":"center","margin":"lg"}
                            ],
                            "backgroundColor":C['bg'],"paddingAll":"24px"
                        }
                    }
                ),
                'correct':False
            }
        
        if ans in ['جاوب','الحل']:
            suggestions = sorted(self.valid_words, key=len, reverse=True)[:4]
            self.current_q += 1
            return {
                'response':FlexSendMessage(
                    alt_text="الحل",
                    contents={
                        "type":"bubble","size":"mega",
                        "body":{
                            "type":"box","layout":"vertical",
                            "contents":game_header("📝","الحل","بعض الكلمات الصحيحة") + [
                                glass_box([
                                    {"type":"text","text":" • ".join(suggestions),"size":"lg",
                                     "color":C['cyan_glow'],"weight":"bold","align":"center","wrap":True}
                                ],"24px")
                            ],
                            "backgroundColor":C['bg'],"paddingAll":"24px"
                        }
                    }
                ),
                'correct':False,
                'next_question':self.current_q<=self.max_q
            }
        
        word = normalize_text(text)
        
        if word in self.used:
            return {'response':TextSendMessage(text=f"⚠️ الكلمة '{text}' مستخدمة"),'correct':False}
        
        letters_copy = self.current_letters.copy()
        can_form = True
        for c in word:
            if c in letters_copy:
                letters_copy.remove(c)
            else:
                can_form = False
                break
        
        if not can_form:
            return {'response':TextSendMessage(text=f"⚠️ لا يمكن تكوين '{text}' من الحروف"),'correct':False}
        
        if len(word) < 2:
            return {'response':TextSendMessage(text="⚠️ الكلمة يجب أن تكون حرفين على الأقل"),'correct':False}
        
        normalized_valid = {normalize_text(w) for w in self.valid_words}
        if word not in normalized_valid:
            return {'response':TextSendMessage(text=f"⚠️ '{text}' ليست كلمة صحيحة"),'correct':False}
        
        self.used.add(word)
        points = 2 if not self.hints_used else 1
        
        if user_id not in self.scores:
            self.scores[user_id] = {'name':name,'score':0,'words':0}
        self.scores[user_id]['score'] += points
        self.scores[user_id]['words'] += 1
        
        if self.scores[user_id]['words'] >= self.words_needed:
            self.current_q += 1
            return {
                'response':FlexSendMessage(
                    alt_text="أحسنت",
                    contents={
                        "type":"bubble","size":"mega",
                        "body":{
                            "type":"box","layout":"vertical",
                            "contents":game_header("✨","أحسنت!","أكملت الجولة") + [
                                glass_box([
                                    {"type":"text","text":name,"size":"xl","weight":"bold",
                                     "color":C['text'],"align":"center"},
                                    {"type":"text","text":f"+{points} نقطة","size":"xxl",
                                     "color":C['cyan_glow'],"align":"center","margin":"md","weight":"bold"}
                                ],"28px")
                            ],
                            "backgroundColor":C['bg'],"paddingAll":"24px"
                        }
                    }
                ),
                'correct':True,
                'won_round':True,
                'next_question':self.current_q<=self.max_q
            }
        
        return {'response':TextSendMessage(text=f"✅ '{text}' صحيحة! +{points} نقطة"),'correct':True}

# ===============================================
# 5. لعبة ترتيب الحروف 🔀
# ===============================================
class OrderGame:
    def __init__(self):
        self.words = ["مدرسة","حديقة","كتاب","طائرة","مستشفى","جامعة","سيارة","منزل","مطعم","فندق","مكتبة","صيدلية"]
        self.current_word, self.shuffled = None, None
        self.current_q, self.max_q = 0, 5
        self.scores = {}
    
    def start_game(self):
        self.current_q, self.scores = 1, {}
        return self.next_question()
    
    def next_question(self):
        if self.current_q > self.max_q: return None
        
        self.current_word = random.choice(self.words)
        letters = list(self.current_word)
        random.shuffle(letters)
        self.shuffled = ''.join(letters)
        
        return FlexSendMessage(
            alt_text=f"السؤال {self.current_q}",
            contents={
                "type":"bubble","size":"mega",
                "body":{
                    "type":"box","layout":"vertical",
                    "contents":game_header("🔀","ترتيب الحروف",f"السؤال {self.current_q}/{self.max_q}") + [
                        glass_box([
                            {"type":"text","text":"رتب الحروف","size":"sm","color":C['text2'],"align":"center"},
                            {"type":"text","text":self.shuffled,"size":"4xl","weight":"bold",
                             "color":C['cyan_glow'],"align":"center","margin":"md","letterSpacing":"10px"}
                        ],"32px"),
                        progress_bar(self.current_q, self.max_q)
                    ],
                    "backgroundColor":C['bg'],"paddingAll":"24px"
                }
            }
        )
    
    def check_answer(self, text, user_id, name):
        if normalize_text(text) == normalize_text(self.current_word):
            points = 2
            if user_id not in self.scores:
                self.scores[user_id] = {'name':name,'score':0}
            self.scores[user_id]['score'] += points
            self.current_q += 1
            
            return {
                'response':FlexSendMessage(
                    alt_text="صحيح",
                    contents={
                        "type":"bubble","size":"mega",
                        "body":{
                            "type":"box","layout":"vertical",
                            "contents":game_header("✅","صحيح!","إجابة ممتازة") + [
                                glass_box([
                                    {"type":"text","text":name,"size":"xl","weight":"bold",
                                     "color":C['text'],"align":"center"},
                                    {"type":"text","text":self.current_word,"size":"3xl",
                                     "color":C['cyan_glow'],"align":"center","margin":"md","weight":"bold"},
                                    {"type":"text","text":f"+{points} نقطة","size":"xxl",
                                     "color":C['success'],"align":"center","margin":"md","weight":"bold"}
                                ],"28px")
                            ],
                            "backgroundColor":C['bg'],"paddingAll":"24px"
                        }
                    }
                ),
                'correct':True,
                'points':points,
                'next_question':self.current_q<=self.max_q
            }
        
        return None

# ===============================================
# 6. لعبة أطول كلمة 📝
# ===============================================
class WordGame:
    def __init__(self):
        self.categories = ["حيوان","نبات","بلد","مدينة","طعام","لون","مهنة","رياضة"]
        self.current_category = None
        self.current_q, self.max_q = 0, 5
        self.scores, self.answers = {}, {}
    
    def start_game(self):
        self.current_q, self.scores, self.answers = 1, {}, {}
        return self.next_question()
    
    def next_question(self):
        if self.current_q > self.max_q: return None
        
        self.current_category = random.choice(self.categories)
        self.answers = {}
        
        return FlexSendMessage(
            alt_text=f"الجولة {self.current_q}",
            contents={
                "type":"bubble","size":"mega",
                "body":{
                    "type":"box","layout":"vertical",
                    "contents":game_header("📝","أطول كلمة",f"الجولة {self.current_q}/{self.max_q}") + [
                        glass_box([
                            {"type":"text","text":"اكتب أطول كلمة من فئة","size":"sm",
                             "color":C['text2'],"align":"center"},
                            {"type":"text","text":self.current_category,"size":"4xl","weight":"bold",
                             "color":C['cyan_glow'],"align":"center","margin":"md"}
                        ],"32px"),
                        glass_box([
                            {"type":"text","text":"⏱ 30 ثانية","size":"xs","color":C['purple'],"align":"center"}
                        ],"12px"),
                        progress_bar(self.current_q, self.max_q)
                    ],
                    "backgroundColor":C['bg'],"paddingAll":"24px"
                }
            }
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
                
                if winner[0] not in self.scores:
                    self.scores[winner[0]] = {'name':winner[1]['name'],'score':0}
                self.scores[winner[0]]['score'] += points
                self.current_q += 1
                
                return {
                    'response':FlexSendMessage(
                        alt_text="الفائز",
                        contents={
                            "type":"bubble","size":"mega",
                            "body":{
                                "type":"box","layout":"vertical",
                                "contents":game_header("🏆","الفائز!","أطول كلمة") + [
                                    glass_box([
                                        {"type":"text","text":winner[1]['name'],"size":"xl",
                                         "weight":"bold","color":C['text'],"align":"center"},
                                        {"type":"text","text":winner[1]['word'],"size":"3xl",
                                         "color":C['cyan_glow'],"align":"center","margin":"md","weight":"bold"},
                                        {"type":"text","text":f"{winner[1]['length']} حرف - +{points} نقطة",
                                         "size":"lg","color":C['success'],"align":"center","margin":"md"}
                                    ],"28px")
                                ],
                                "backgroundColor":C['bg'],"paddingAll":"24px"
                            }
                        }
                    ),
                    'correct':True,
                    'points':points,
                    'next_question':self.current_q<=self.max_q
                }
            
            return {'response':TextSendMessage(text=f"✅ تم تسجيل: {word} ({len(word)} حرف)"),'correct':True}
        
        return None

# ===============================================
# 7. لعبة تخمين اللون 🎨
# ===============================================
class ColorGame:
    def __init__(self):
        self.colors = [
            {"name":"أحمر","hex":"#EF4444","hint":"لون الدم"},
            {"name":"أزرق","hex":"#3B82F6","hint":"لون السماء"},
            {"name":"أخضر","hex":"#10B981","hint":"لون الأشجار"},
            {"name":"أصفر","hex":"#F59E0B","hint":"لون الشمس"},
            {"name":"برتقالي","hex":"#F97316","hint":"لون البرتقال"},
            {"name":"بنفسجي","hex":"#8B5CF6","hint":"لون العنب"},
            {"name":"وردي","hex":"#EC4899","hint":"لون الورد"},
            {"name":"بني","hex":"#92400E","hint":"لون الخشب"}
        ]
        self.current_color = None
        self.current_q, self.max_q = 0, 5
        self.scores, self.hints_used = {}, 0
    
    def start_game(self):
        self.current_q, self.scores = 1, {}
        return self.next_question()
    
    def next_question(self):
        if self.current_q > self.max_q: return None
        
        self.current_color = random.choice(self.colors)
        self.hints_used = 0
        
        return FlexSendMessage(
            alt_text=f"السؤال {self.current_q}",
            contents={
                "type":"bubble","size":"mega",
                "body":{
                    "type":"box","layout":"vertical",
                    "contents":game_header("🎨","تخمين اللون",f"السؤال {self.current_q}/{self.max_q}") + [
                        glass_box([
                            {"type":"text","text":"ما هذا اللون؟","size":"sm",
                             "color":C['text2'],"align":"center"},
                            {"type":"box","layout":"vertical","contents":[],"height":"140px",
                             "backgroundColor":self.current_color['hex'],"cornerRadius":"20px",
                             "margin":"md","borderWidth":"3px","borderColor":"#ffffff30"}
                        ],"32px"),
                        progress_bar(self.current_q, self.max_q)
                    ],
                    "backgroundColor":C['bg'],"paddingAll":"24px"
                },
                "footer":{
                    "type":"box","layout":"horizontal",
                    "contents":[create_button("💡 لمح","لمح")],
                    "backgroundColor":C['bg'],"paddingAll":"16px"
                }
            }
        )
    
    def check_answer(self, text, user_id, name):
        ans = text.strip().lower()
        
        if ans in ['لمح','تلميح','hint']:
            if self.hints_used > 0:
                return {'response':TextSendMessage(text="⚠️ تم استخدام التلميح"),'correct':False}
            self.hints_used = 1
            
            # التلميح: الحرف الأول + عدد الحروف
            color_name = self.current_color['name']
            first = color_name[0]
            hint_pattern = first + " " + "_ " * (len(color_name) - 1)
            
            return {
                'response':FlexSendMessage(
                    alt_text="تلميح",
                    contents={
                        "type":"bubble","size":"mega",
                        "body":{
                            "type":"box","layout":"vertical",
                            "contents":game_header("💡","تلميح","الحرف الأول + عدد الحروف") + [
                                glass_box([
                                    {"type":"text","text":hint_pattern,"size":"3xl",
                                     "color":C['cyan_glow'],"align":"center","wrap":True,"weight":"bold","letterSpacing":"6px"}
                                ],"28px"),
                                {"type":"text","text":"⚠️ التلميح يقلل النقاط للنصف",
                                 "size":"xs","color":C['purple'],"align":"center","margin":"lg"}
                            ],
                            "backgroundColor":C['bg'],"paddingAll":"24px"
                        }
                    }
                ),
                'correct':False
            }
        
        if normalize_text(text) == normalize_text(self.current_color['name']):
            points = 2 if self.hints_used == 0 else 1
            if user_id not in self.scores:
                self.scores[user_id] = {'name':name,'score':0}
            self.scores[user_id]['score'] += points
            self.current_q += 1
            
            return {
                'response':FlexSendMessage(
                    alt_text="صحيح",
                    contents={
                        "type":"bubble","size":"mega",
                        "body":{
                            "type":"box","layout":"vertical",
                            "contents":game_header("✅","صحيح!","إجابة ممتازة") + [
                                glass_box([
                                    {"type":"text","text":name,"size":"xl","weight":"bold",
                                     "color":C['text'],"align":"center"},
                                    {"type":"text","text":self.current_color['name'],"size":"3xl",
                                     "color":self.current_color['hex'],"align":"center","margin":"md","weight":"bold"},
                                    {"type":"text","text":f"+{points} نقطة","size":"xxl",
                                     "color":C['cyan_glow'],"align":"center","margin":"md","weight":"bold"}
                                ],"28px")
                            ],
                            "backgroundColor":C['bg'],"paddingAll":"24px"
                        }
                    }
                ),
                'correct':True,
                'points':points,
                'next_question':self.current_q<=self.max_q
            }
        
        return None

# ===============================================
# 8. لعبة إنسان حيوان نبات 🎯 (مع تلميحات)
# ===============================================
class HumanAnimalGame:
    def __init__(self):
        self.letters = ['أ','ب','ت','ث','ج','ح','خ','د','ذ','ر','ز','س','ش','ص','ض','ط','ظ','ع','غ','ف','ق','ك','ل','م','ن','ه','و','ي']
        self.current_letter = None
        self.answers = {}
        self.hints_used = 0
        self.current_q, self.max_q = 0, 5
        self.scores = {}
    
    def start_game(self):
        self.current_q, self.scores = 1, {}
        return self.next_question()
    
    def next_question(self):
        if self.current_q > self.max_q: return None
        
        self.current_letter = random.choice(self.letters)
        self.answers = {}
        self.hints_used = 0
        
        return FlexSendMessage(
            alt_text=f"الجولة {self.current_q}",
            contents={
                "type":"bubble","size":"mega",
                "body":{
                    "type":"box","layout":"vertical",
                    "contents":game_header("🎯","إنسان حيوان نبات بلاد",f"الجولة {self.current_q}/{self.max_q}") + [
                        glass_box([
                            {"type":"text","text":"الحرف","size":"sm","color":C['text2'],"align":"center"},
                            {"type":"text","text":self.current_letter,"size":"6xl","weight":"bold",
                             "color":C['cyan_glow'],"align":"center","margin":"md"}
                        ],"40px"),
                        glass_box([
                            {"type":"text","text":"اكتب 4 كلمات تبدأ بالحرف\nكل كلمة في سطر:\n▫️ إنسان\n▫️ حيوان\n▫️ نبات\n▫️ بلاد",
                             "size":"xs","color":C['text'],"align":"center","wrap":True}
                        ],"16px"),
                        progress_bar(self.current_q, self.max_q)
                    ],
                    "backgroundColor":C['bg'],"paddingAll":"24px"
                },
                "footer":{
                    "type":"box","layout":"horizontal",
                    "contents":[
                        create_button("💡 لمح","لمح"),
                        create_button("📝 جاوب","جاوب")
                    ],
                    "spacing":"sm","backgroundColor":C['bg'],"paddingAll":"16px"
                }
            }
        )
    
    def check_answer(self, text, user_id, name):
        ans = text.strip().lower()
        
        if ans in ['لمح','تلميح','hint']:
            if self.hints_used > 0:
                return {'response':TextSendMessage(text="⚠️ تم استخدام التلميح"),'correct':False}
            self.hints_used = 1
            
            # أمثلة للتلميح
            examples = {
                'أ': 'أحمد - أسد - أرز - الأردن',
                'ب': 'باسم - بقرة - بصل - بغداد',
                'ت': 'تامر - تمساح - تفاح - تونس',
                'ج': 'جمال - جمل - جزر - الجزائر',
                'ح': 'حسن - حمار - حمص - حلب',
                'خ': 'خالد - خروف - خيار - الخرطوم',
                'د': 'داود - دب - دراق - دمشق',
                'ر': 'راشد - رمح - رمان - الرياض',
                'ز': 'زيد - زرافة - زيتون - الزرقاء',
                'س': 'سالم - سمكة - سبانخ - سوريا',
                'ش': 'شادي - شاة - شمام - شيكاغو',
                'ص': 'صالح - صقر - صبار - صنعاء',
                'ع': 'عمر - عصفور - عنب - عمان',
                'ف': 'فهد - فيل - فول - فرنسا',
                'ق': 'قاسم - قط - قرنبيط - قطر',
                'ك': 'كريم - كلب - كوسا - الكويت',
                'ل': 'ليث - ليث - ليمون - لبنان',
                'م': 'محمد - ماعز - موز - مصر',
                'ن': 'ناصر - نمر - نعناع - نيويورك',
                'ه': 'هاني - هر - هليون - هولندا',
                'و': 'وليد - وحيد القرن - ورد - واشنطن',
                'ي': 'ياسر - يمامة - يقطين - اليمن'
            }
            
            hint_text = examples.get(self.current_letter, "أمثلة غير متوفرة")
            
            return {
                'response':FlexSendMessage(
                    alt_text="تلميح",
                    contents={
                        "type":"bubble","size":"mega",
                        "body":{
                            "type":"box","layout":"vertical",
                            "contents":game_header("💡","تلميح","أمثلة للحل") + [
                                glass_box([
                                    {"type":"text","text":hint_text,"size":"md",
                                     "color":C['cyan_glow'],"align":"center","wrap":True,"weight":"bold"}
                                ],"24px"),
                                {"type":"text","text":"⚠️ التلميح يقلل النقاط للنصف",
                                 "size":"xs","color":C['purple'],"align":"center","margin":"lg"}
                            ],
                            "backgroundColor":C['bg'],"paddingAll":"24px"
                        }
                    }
                ),
                'correct':False
            }
        
        if ans in ['جاوب','الحل','answer']:
            self.current_q += 1
            return {
                'response':TextSendMessage(text=f"تم تخطي السؤال. جولة جديدة!"),
                'correct':False,
                'next_question':self.current_q<=self.max_q
            }
        
        if user_id in self.answers:
            return None
        
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        if len(lines) >= 4:
            valid = sum(1 for word in lines[:4] if word and word[0] == self.current_letter)
            
            if valid >= 4:
                points_per_word = 1 if self.hints_used == 0 else 0.5
                points = int(valid * points_per_word * 2)
                self.answers[user_id] = lines[:4]
                
                if user_id not in self.scores:
                    self.scores[user_id] = {'name':name,'score':0}
                self.scores[user_id]['score'] += points
                
                self.current_q += 1
                
                return {
                    'response':FlexSendMessage(
                        alt_text="صحيح",
                        contents={
                            "type":"bubble","size":"mega",
                            "body":{
                                "type":"box","layout":"vertical",
                                "contents":game_header("✅","أحسنت!","إجابات صحيحة") + [
                                    glass_box([
                                        {"type":"text","text":name,"size":"xl","weight":"bold",
                                         "color":C['text'],"align":"center"},
                                        {"type":"text","text":f"إجابات صحيحة: {valid}/4","size":"lg",
                                         "color":C['text2'],"align":"center","margin":"sm"},
                                        {"type":"text","text":f"+{points} نقطة","size":"xxl",
                                         "color":C['cyan_glow'],"align":"center","margin":"md","weight":"bold"}
                                    ],"28px")
                                ],
                                "backgroundColor":C['bg'],"paddingAll":"24px"
                            }
                        }
                    ),
                    'correct':True,
                    'points':points,
                    'won':valid==4,
                    'next_question':self.current_q<=self.max_q
                }
        
        return None

# ===============================================
# 9. لعبة أسرع إجابة ⚡
# ===============================================
class FastGame:
    def __init__(self):
        self.questions = [
            {"q":"ما عاصمة السعودية؟","a":"الرياض"},
            {"q":"كم عدد أيام الأسبوع؟","a":"سبعة"},
            {"q":"ما أكبر كوكب؟","a":"المشتري"},
            {"q":"كم ساعة في اليوم؟","a":"أربعة وعشرون"},
            {"q":"ما لون السماء؟","a":"أزرق"},
            {"q":"كم عدد أشهر السنة؟","a":"اثني عشر"},
            {"q":"ما أصغر قارة؟","a":"أستراليا"}
        ]
        self.current_question = None
        self.answered = False
    
    def start_game(self):
        self.current_question = random.choice(self.questions)
        self.answered = False
        
        return FlexSendMessage(
            alt_text="أسرع إجابة",
            contents={
                "type":"bubble","size":"mega",
                "body":{
                    "type":"box","layout":"vertical",
                    "contents":game_header("⚡","أسرع إجابة","أول من يجيب يفوز") + [
                        glass_box([
                            {"type":"text","text":self.current_question['q'],"size":"xxl",
                             "color":C['text'],"align":"center","wrap":True,"weight":"bold"}
                        ],"32px"),
                        glass_box([
                            {"type":"text","text":"⏱ السرعة مهمة!","size":"sm",
                             "color":C['purple'],"align":"center","weight":"bold"}
                        ],"16px")
                    ],
                    "backgroundColor":C['bg'],"paddingAll":"24px"
                }
            }
        )
    
    def check_answer(self, text, user_id, name):
        if self.answered:
            return None
        
        if normalize_text(text) == normalize_text(self.current_question['a']):
            self.answered = True
            points = 5
            
            return {
                'response':FlexSendMessage(
                    alt_text="فاز",
                    contents={
                        "type":"bubble","size":"mega",
                        "body":{
                            "type":"box","layout":"vertical",
                            "contents":game_header("🏆","فاز!","أسرع إجابة") + [
                                glass_box([
                                    {"type":"text","text":name,"size":"3xl","weight":"bold",
                                     "color":C['cyan_glow'],"align":"center"},
                                    {"type":"text","text":"⚡ كنت الأسرع!","size":"lg",
                                     "color":C['text2'],"align":"center","margin":"md"},
                                    {"type":"text","text":f"+{points} نقطة","size":"3xl",
                                     "color":C['success'],"align":"center","margin":"lg","weight":"bold"}
                                ],"32px")
                            ],
                            "backgroundColor":C['bg'],"paddingAll":"24px"
                        }
                    }
                ),
                'correct':True,
                'points':points,
                'won':True,
                'game_over':True
            }
        
        return None

# ===============================================
# 10. لعبة الاختلافات 🔍
# ===============================================
class DifferencesGame:
    def __init__(self):
        self.image_pairs = [
            {"original":"https://via.placeholder.com/400x300/0A1628/00D9FF?text=Find+5+Differences",
             "solution":"https://via.placeholder.com/400x300/0A1628/5EEBFF?text=Solution",
             "differences":5}
        ]
        self.current_pair = None
        self.showed_solution = False
    
    def start_game(self):
        self.current_pair = random.choice(self.image_pairs)
        self.showed_solution = False
        
        return [
            FlexSendMessage(
                alt_text="لعبة الاختلافات",
                contents={
                    "type":"bubble","size":"mega",
                    "body":{
                        "type":"box","layout":"vertical",
                        "contents":game_header("🔍","لعبة الاختلافات",f"ابحث عن {self.current_pair['differences']} اختلافات") + [
                            glass_box([
                                {"type":"text","text":"📝 اكتب 'جاوب' لعرض الحل","size":"sm",
                                 "color":C['text'],"align":"center","wrap":True}
                            ],"16px")
                        ],
                        "backgroundColor":C['bg'],"paddingAll":"24px"
                    }
                }
            ),
            ImageSendMessage(
                original_content_url=self.current_pair['original'],
                preview_image_url=self.current_pair['original']
            )
        ]
    
    def check_answer(self, text, user_id, name):
        ans = text.strip().lower()
        
        if ans in ['جاوب','الحل','solution']:
            self.showed_solution = True
            return {
                'response':[
                    TextSendMessage(text="📝 الحل:"),
                    ImageSendMessage(
                        original_content_url=self.current_pair['solution'],
                        preview_image_url=self.current_pair['solution']
                    )
                ],
                'points':0,
                'correct':False,
                'game_over':True
            }
        
        return None

# ===============================================
# 11. لعبة التوافق 💕
# ===============================================
class CompatibilityGame:
    def __init__(self):
        self.waiting = True
    
    def start_game(self):
        self.waiting = True
        return FlexSendMessage(
            alt_text="التوافق",
            contents={
                "type":"bubble","size":"mega",
                "body":{
                    "type":"box","layout":"vertical",
                    "contents":game_header("💕","لعبة التوافق","نسبة التوافق بين اسمين") + [
                        glass_box([
                            {"type":"text","text":"اكتب اسمين مفصولين بمسافة","size":"md",
                             "color":C['text'],"align":"center","wrap":True},
                            {"type":"text","text":"مثال: أحمد سارة","size":"sm",
                             "color":C['text2'],"align":"center","margin":"md"}
                        ],"24px")
                    ],
                    "backgroundColor":C['bg'],"paddingAll":"24px"
                }
            }
        )
    
    def calculate_compatibility(self, name1, name2):
        n1, n2 = normalize_text(name1), normalize_text(name2)
        if n1 > n2: n1, n2 = n2, n1
        combined = n1 + n2
        hash_val = int(hashlib.md5(combined.encode('utf-8')).hexdigest(), 16)
        return 50 + (hash_val % 51)
    
    def check_answer(self, text, user_id, name):
        if not self.waiting:
            return None
        
        parts = text.strip().split()
        
        if len(parts) < 2:
            return {'response':TextSendMessage(text="⚠️ اكتب اسمين مفصولين بمسافة"),'correct':False}
        
        name1, name2 = parts[0], ' '.join(parts[1:])
        compatibility = self.calculate_compatibility(name1, name2)
        
        if compatibility >= 90: msg = "توافق مثالي 💯"
        elif compatibility >= 75: msg = "توافق ممتاز ✨"
        elif compatibility >= 60: msg = "توافق جيد 👍"
        else: msg = "توافق متوسط 🤷"
        
        self.waiting = False
        return {
            'response':FlexSendMessage(
                alt_text="التوافق",
                contents={
                    "type":"bubble","size":"mega",
                    "body":{
                        "type":"box","layout":"vertical",
                        "contents":game_header("💕","نتيجة التوافق",msg) + [
                            glass_box([
                                {"type":"text","text":f"{name1} 💕 {name2}","size":"lg",
                                 "color":C['text'],"align":"center","wrap":True,"weight":"bold"}
                            ],"20px"),
                            glass_box([
                                {"type":"text","text":f"{compatibility}%","size":"6xl",
                                 "color":C['cyan_glow'],"align":"center","weight":"bold"}
                            ],"40px")
                        ],
                        "backgroundColor":C['bg'],"paddingAll":"24px"
                    }
                }
            ),
            'correct':True,
            'points':5,
            'won':True,
            'game_over':True
        }

# ===============================================
# إدارة الألعاب
# ===============================================
GAMES = {
    'song': SongGame,
    'opposite': OppositeGame,
    'chain': ChainGame,
    'build': BuildGame,
    'order': OrderGame,
    'word': WordGame,
    'color': ColorGame,
    'game': HumanAnimalGame,
    'fast': FastGame,
    'diff': DifferencesGame,
    'compat': CompatibilityGame
}

def start_game(game_type, game_id, active_games, line_bot_api, ask_ai=None):
    """بدء لعبة جديدة"""
    if game_id in active_games:
        return TextSendMessage(text="⚠️ لعبة نشطة! اكتب: إيقاف")
    
    if game_type not in GAMES:
        return TextSendMessage(text="⚠️ لعبة غير موجودة")
    
    game = GAMES[game_type]()
    active_games[game_id] = {'type':game_type,'game':game}
    return game.start_game()

def check_game_answer(game_id, text, user_id, name, active_games, line_bot_api, update_points_fn):
    """فحص إجابة اللاعب"""
    if game_id not in active_games:
        return None
    
    game_data = active_games[game_id]
    game = game_data['game']
    
    result = game.check_answer(text, user_id, name)
    
    if not result:
        return None
    
    # تحديث النقاط
    if result.get('points', 0) > 0:
        update_points_fn(user_id, name, result['points'], result.get('won', False))
    
    # سؤال تالي
    if result.get('next_question'):
        next_q = game.next_question()
        if next_q:
            return [result['response'], next_q]
    
    # نهاية اللعبة
    if result.get('game_over'):
        del active_games[game_id]
    
    return result['response']
