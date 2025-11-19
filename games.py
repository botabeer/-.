from linebot.models import TextSendMessage, FlexSendMessage
import random
import re

def normalize_text(text):
    """تطبيع النص العربي للمقارنة"""
    if not text:
        return ""
    text = text.strip().lower()
    text = text.replace('أ','ا').replace('إ','ا').replace('آ','ا')
    text = text.replace('ؤ','و').replace('ئ','ي').replace('ء','')
    text = text.replace('ة','ه').replace('ى','ي')
    text = re.sub(r'[\u064B-\u065F]','',text)
    text = re.sub(r'\s+','',text)
    return text

# ============= نظام الألوان الموحد =============
COLORS = {
    'bg': '#000000',        # خلفية سوداء نقية
    'topbg': '#88AEE0',     # خلفية علوية زرقاء
    'card': '#0F2440',      # خلفية الكروت
    'card2': '#0A1628',     # كرت ثانوي
    'text': '#E0F2FF',      # نص رئيسي
    'text2': '#7FB3D5',     # نص ثانوي
    'cyan': '#00D9FF',      # أزرق سماوي
    'glow': '#5EEBFF',      # توهج
    'sep': '#2C5F8D',       # فواصل
    'border': '#00D9FF40',  # حدود شفافة
    'glass': '#0F244080'    # تأثير زجاجي
}

LOGO_URL = 'https://i.imgur.com/qcWILGi.jpeg'

# ============= 1. لعبة الضد (OppositeGame) =============
class OppositeGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.C = COLORS
        self.all_words = [
            {"word":"كبير","opposite":"صغير"},
            {"word":"طويل","opposite":"قصير"},
            {"word":"سريع","opposite":"بطيء"},
            {"word":"حار","opposite":"بارد"},
            {"word":"قوي","opposite":"ضعيف"},
            {"word":"غني","opposite":"فقير"},
            {"word":"سعيد","opposite":"حزين"},
            {"word":"نظيف","opposite":"وسخ"},
            {"word":"جديد","opposite":"قديم"},
            {"word":"صعب","opposite":"سهل"},
            {"word":"ثقيل","opposite":"خفيف"},
            {"word":"واسع","opposite":"ضيق"},
            {"word":"عميق","opposite":"ضحل"},
            {"word":"شجاع","opposite":"جبان"},
            {"word":"ذكي","opposite":"غبي"}
        ]
        self.questions = []
        self.current_word = None
        self.hints_used = 0
        self.question_number = 0
        self.total_questions = 5
        self.player_scores = {}

    def start_game(self):
        self.questions = random.sample(self.all_words, min(self.total_questions, len(self.all_words)))
        self.question_number = 0
        self.player_scores = {}
        self.hints_used = 0
        return self.next_question()

    def next_question(self):
        if self.question_number >= self.total_questions:
            return None
        self.current_word = self.questions[self.question_number]
        self.question_number += 1
        self.hints_used = 0
        
        card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": self.C['bg'],
                "paddingAll": "0px",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "backgroundColor": self.C['topbg'],
                        "paddingTop": "35px",
                        "paddingBottom": "140px",
                        "contents": [{
                            "type": "box",
                            "layout": "vertical",
                            "cornerRadius": "25px",
                            "backgroundColor": self.C['bg'],
                            "paddingAll": "0px",
                            "offsetTop": "55px",
                            "borderWidth": "2px",
                            "borderColor": self.C['border'],
                            "contents": [
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "paddingAll": "24px",
                                    "paddingBottom": "20px",
                                    "backgroundColor": self.C['card'],
                                    "cornerRadius": "25px 25px 0px 0px",
                                    "contents": [
                                        {"type": "text", "text": "🎯 لعبة الضد", "weight": "bold", "size": "xl", "align": "center", "color": self.C['glow']},
                                        {"type": "text", "text": f"السؤال {self.question_number} من {self.total_questions}", "size": "sm", "align": "center", "color": self.C['text2'], "margin": "sm"}
                                    ]
                                },
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "height": "6px",
                                    "backgroundColor": self.C['sep'],
                                    "contents": [{
                                        "type": "box",
                                        "layout": "vertical",
                                        "backgroundColor": self.C['cyan'],
                                        "width": f"{(self.question_number/self.total_questions)*100}%",
                                        "height": "6px"
                                    }]
                                },
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "paddingAll": "24px",
                                    "spacing": "lg",
                                    "contents": [
                                        {
                                            "type": "box",
                                            "layout": "vertical",
                                            "backgroundColor": self.C['glass'],
                                            "cornerRadius": "18px",
                                            "paddingAll": "22px",
                                            "borderWidth": "1px",
                                            "borderColor": self.C['border'],
                                            "contents": [
                                                {"type": "text", "text": "ما هو عكس:", "size": "md", "color": self.C['text2'], "align": "center"},
                                                {"type": "text", "text": self.current_word['word'], "size": "xxl", "weight": "bold", "color": self.C['cyan'], "align": "center", "margin": "md"}
                                            ]
                                        },
                                        {"type": "separator", "color": self.C['sep'], "margin": "lg"},
                                        {
                                            "type": "box",
                                            "layout": "horizontal",
                                            "spacing": "md",
                                            "margin": "lg",
                                            "contents": [
                                                {"type": "button", "action": {"type": "message", "label": "💡 لمح", "text": "لمح"}, "style": "secondary", "color": "#FFFFFF", "height": "md"},
                                                {"type": "button", "action": {"type": "message", "label": "📝 جاوب", "text": "جاوب"}, "style": "primary", "color": self.C['cyan'], "height": "md"}
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }]
                    }
                ]
            }
        }
        return FlexSendMessage(alt_text=f"السؤال {self.question_number} - لعبة الضد", contents=card)

    def get_hint(self):
        if not self.current_word:
            return None
        opposite = self.current_word['opposite']
        first_letter = opposite[0]
        word_length = len(opposite)
        hint_text = f"{first_letter} " + "_ " * (word_length - 1)
        self.hints_used += 1
        
        card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": self.C['card'],
                "cornerRadius": "20px",
                "paddingAll": "24px",
                "borderWidth": "2px",
                "borderColor": self.C['border'],
                "contents": [
                    {"type": "text", "text": "💡 تلميح", "weight": "bold", "size": "xl", "color": self.C['glow'], "align": "center"},
                    {"type": "separator", "color": self.C['sep'], "margin": "md"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "backgroundColor": self.C['glass'],
                        "cornerRadius": "15px",
                        "paddingAll": "18px",
                        "margin": "lg",
                        "contents": [
                            {"type": "text", "text": f"أول حرف: {hint_text}", "size": "lg", "color": self.C['text'], "align": "center", "wrap": True},
                            {"type": "text", "text": f"عدد الحروف: {word_length}", "size": "md", "color": self.C['text2'], "align": "center", "margin": "md"}
                        ]
                    },
                    {"type": "text", "text": "⚠️ النقاط ستنخفض إلى نصف القيمة", "size": "sm", "color": "#FFB800", "align": "center", "margin": "lg", "wrap": True}
                ]
            }
        }
        return FlexSendMessage(alt_text="تلميح", contents=card)

    def show_answer(self):
        if not self.current_word:
            return None
        card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": self.C['card'],
                "cornerRadius": "20px",
                "paddingAll": "24px",
                "borderWidth": "2px",
                "borderColor": self.C['border'],
                "contents": [
                    {"type": "text", "text": "📝 الإجابة الصحيحة", "weight": "bold", "size": "xl", "color": self.C['glow'], "align": "center"},
                    {"type": "separator", "color": self.C['sep'], "margin": "md"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "backgroundColor": self.C['glass'],
                        "cornerRadius": "15px",
                        "paddingAll": "20px",
                        "margin": "lg",
                        "contents": [
                            {"type": "text", "text": self.current_word['opposite'], "size": "xxl", "weight": "bold", "color": self.C['cyan'], "align": "center"}
                        ]
                    }
                ]
            }
        }
        return FlexSendMessage(alt_text="الإجابة الصحيحة", contents=card)

    def check_answer(self, answer, user_id, display_name):
        if not self.current_word:
            return None
        if normalize_text(answer) == normalize_text(self.current_word['opposite']):
            points = 2 if self.hints_used == 0 else 1
            if user_id not in self.player_scores:
                self.player_scores[user_id] = {'name': display_name, 'score': 0}
            self.player_scores[user_id]['score'] += points
            return {'response': TextSendMessage(text=f"✅ إجابة صحيحة! +{points} نقطة"), 'points': points, 'correct': True}
        return None

    def get_final_results(self):
        if not self.player_scores:
            return TextSendMessage(text="⚠️ لم يشارك أحد في اللعبة")
        sorted_players = sorted(self.player_scores.items(), key=lambda x: x[1]['score'], reverse=True)
        winners_content = []
        rank_emojis = {1: "🥇", 2: "🥈", 3: "🥉"}
        
        for idx, (user_id, data) in enumerate(sorted_players[:5], 1):
            emoji = rank_emojis.get(idx, f"{idx}️⃣")
            winners_content.append({
                "type": "box",
                "layout": "horizontal",
                "backgroundColor": self.C['glass'],
                "cornerRadius": "12px",
                "paddingAll": "14px",
                "margin": "sm" if idx > 1 else "none",
                "contents": [
                    {"type": "text", "text": emoji, "size": "xl", "flex": 0},
                    {"type": "text", "text": data['name'], "size": "md", "color": self.C['text'], "flex": 3, "margin": "md"},
                    {"type": "text", "text": f"{data['score']} 🏆", "size": "md", "color": self.C['cyan'], "align": "end", "flex": 1}
                ]
            })
        
        card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": self.C['bg'],
                "paddingAll": "0px",
                "contents": [{
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": self.C['topbg'],
                    "paddingTop": "35px",
                    "paddingBottom": "140px",
                    "contents": [{
                        "type": "box",
                        "layout": "vertical",
                        "cornerRadius": "25px",
                        "backgroundColor": self.C['bg'],
                        "paddingAll": "0px",
                        "offsetTop": "55px",
                        "borderWidth": "2px",
                        "borderColor": self.C['border'],
                        "contents": [
                            {
                                "type": "box",
                                "layout": "vertical",
                                "paddingAll": "24px",
                                "paddingBottom": "20px",
                                "backgroundColor": self.C['card'],
                                "cornerRadius": "25px 25px 0px 0px",
                                "contents": [
                                    {"type": "text", "text": "🔤 تكوين كلمات", "weight": "bold", "size": "xl", "align": "center", "color": self.C['glow']},
                                    {"type": "text", "text": f"السؤال {self.question_number} من {self.total_questions}", "size": "sm", "align": "center", "color": self.C['text2'], "margin": "sm"}
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "height": "6px",
                                "backgroundColor": self.C['sep'],
                                "contents": [{
                                    "type": "box",
                                    "layout": "vertical",
                                    "backgroundColor": self.C['cyan'],
                                    "width": f"{(self.question_number/self.total_questions)*100}%",
                                    "height": "6px"
                                }]
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "paddingAll": "24px",
                                "spacing": "lg",
                                "contents": [
                                    {"type": "text", "text": "كوّن 3 كلمات من الحروف التالية:", "size": "md", "color": self.C['text'], "align": "center", "wrap": True},
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "backgroundColor": self.C['glass'],
                                        "cornerRadius": "18px",
                                        "paddingAll": "22px",
                                        "margin": "md",
                                        "borderWidth": "1px",
                                        "borderColor": self.C['border'],
                                        "contents": [
                                            {"type": "text", "text": self.current_question['letters'], "size": "xxl", "weight": "bold", "color": self.C['cyan'], "align": "center", "wrap": True, "letterSpacing": "8px"}
                                        ]
                                    },
                                    {"type": "text", "text": "أكتب 3 كلمات كل واحدة في سطر", "size": "sm", "color": self.C['text2'], "align": "center", "margin": "md", "wrap": True},
                                    {"type": "separator", "color": self.C['sep'], "margin": "lg"},
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "spacing": "md",
                                        "margin": "lg",
                                        "contents": [
                                            {"type": "button", "action": {"type": "message", "label": "💡 لمح", "text": "لمح"}, "style": "secondary", "color": "#FFFFFF", "height": "md"},
                                            {"type": "button", "action": {"type": "message", "label": "📝 جاوب", "text": "جاوب"}, "style": "primary", "color": self.C['cyan'], "height": "md"}
                                        ]
                                    }
                                ]
                            }
                        ]
                    }]
                }]
            }
        }
        return FlexSendMessage(alt_text=f"السؤال {self.question_number} - تكوين كلمات", contents=card)

    def get_hint(self):
        if not self.current_question:
            return None
        first_word = self.current_question['words'][0]
        first_letter = first_word[0]
        word_length = len(first_word)
        hint_text = f"{first_letter} " + "_ " * (word_length - 1)
        self.hints_used += 1
        
        card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": self.C['card'],
                "cornerRadius": "20px",
                "paddingAll": "24px",
                "borderWidth": "2px",
                "borderColor": self.C['border'],
                "contents": [
                    {"type": "text", "text": "💡 تلميح", "weight": "bold", "size": "xl", "color": self.C['glow'], "align": "center"},
                    {"type": "separator", "color": self.C['sep'], "margin": "md"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "backgroundColor": self.C['glass'],
                        "cornerRadius": "15px",
                        "paddingAll": "18px",
                        "margin": "lg",
                        "contents": [
                            {"type": "text", "text": f"الكلمة الأولى: {hint_text}", "size": "lg", "color": self.C['text'], "align": "center", "wrap": True},
                            {"type": "text", "text": f"عدد الحروف: {word_length}", "size": "md", "color": self.C['text2'], "align": "center", "margin": "md"}
                        ]
                    },
                    {"type": "text", "text": "⚠️ النقاط ستنخفض إلى نصف القيمة", "size": "sm", "color": "#FFB800", "align": "center", "margin": "lg", "wrap": True}
                ]
            }
        }
        return FlexSendMessage(alt_text="تلميح", contents=card)

    def show_answer(self):
        if not self.current_question:
            return None
        words = "\n".join(self.current_question['words'])
        card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": self.C['card'],
                "cornerRadius": "20px",
                "paddingAll": "24px",
                "borderWidth": "2px",
                "borderColor": self.C['border'],
                "contents": [
                    {"type": "text", "text": "📝 الإجابة الصحيحة", "weight": "bold", "size": "xl", "color": self.C['glow'], "align": "center"},
                    {"type": "separator", "color": self.C['sep'], "margin": "md"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "backgroundColor": self.C['glass'],
                        "cornerRadius": "15px",
                        "paddingAll": "20px",
                        "margin": "lg",
                        "contents": [
                            {"type": "text", "text": words, "size": "xl", "weight": "bold", "color": self.C['cyan'], "align": "center", "wrap": True}
                        ]
                    }
                ]
            }
        }
        return FlexSendMessage(alt_text="الإجابة الصحيحة", contents=card)

    def check_answer(self, answer, user_id, display_name):
        if not self.current_question:
            return None
        user_words = [normalize_text(word.strip()) for word in answer.split('\n') if word.strip()]
        correct_words = [normalize_text(word) for word in self.current_question['words']]
        
        if len(user_words) >= 3 and all(word in correct_words for word in user_words[:3]):
            points = 2 if self.hints_used == 0 else 1
            if user_id not in self.player_scores:
                self.player_scores[user_id] = {'name': display_name, 'score': 0}
            self.player_scores[user_id]['score'] += points
            return {'response': TextSendMessage(text=f"✅ إجابة صحيحة! +{points} نقطة"), 'points': points, 'correct': True}
        return None

    def get_final_results(self):
        if not self.player_scores:
            return TextSendMessage(text="⚠️ لم يشارك أحد في اللعبة")
        sorted_players = sorted(self.player_scores.items(), key=lambda x: x[1]['score'], reverse=True)
        winners_content = []
        rank_emojis = {1: "🥇", 2: "🥈", 3: "🥉"}
        
        for idx, (user_id, data) in enumerate(sorted_players[:5], 1):
            emoji = rank_emojis.get(idx, f"{idx}️⃣")
            winners_content.append({
                "type": "box",
                "layout": "horizontal",
                "backgroundColor": self.C['glass'],
                "cornerRadius": "12px",
                "paddingAll": "14px",
                "margin": "sm" if idx > 1 else "none",
                "contents": [
                    {"type": "text", "text": emoji, "size": "xl", "flex": 0},
                    {"type": "text", "text": data['name'], "size": "md", "color": self.C['text'], "flex": 3, "margin": "md"},
                    {"type": "text", "text": f"{data['score']} 🏆", "size": "md", "color": self.C['cyan'], "align": "end", "flex": 1}
                ]
            })
        
        card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": self.C['bg'],
                "paddingAll": "0px",
                "contents": [{
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": self.C['topbg'],
                    "paddingTop": "35px",
                    "paddingBottom": "140px",
                    "contents": [{
                        "type": "box",
                        "layout": "vertical",
                        "cornerRadius": "25px",
                        "backgroundColor": self.C['bg'],
                        "paddingAll": "28px",
                        "offsetTop": "55px",
                        "borderWidth": "2px",
                        "borderColor": self.C['border'],
                        "contents": [
                            {"type": "text", "text": "🎉 انتهت اللعبة!", "weight": "bold", "size": "xxl", "align": "center", "color": self.C['glow']},
                            {"type": "separator", "color": self.C['sep'], "margin": "lg"},
                            {"type": "text", "text": "🏆 لوحة الصدارة", "size": "lg", "align": "center", "color": self.C['text'], "margin": "lg"},
                            {"type": "box", "layout": "vertical", "margin": "lg", "contents": winners_content},
                            {"type": "button", "action": {"type": "message", "label": "🔄 لعب مرة أخرى", "text": "إعادة"}, "style": "primary", "color": self.C['cyan'], "height": "md", "margin": "xl"}
                        ]
                    }]
                }]
            }
        }
        return FlexSendMessage(alt_text="النتائج النهائية", contents=card)


# ============= 6. لعبة إنسان حيوان نبات بلد (HumanAnimalPlantGame) =============
class HumanAnimalPlantGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.C = COLORS
        self.all_questions = [
            {"letter": "م", "answers": {"human": "محمد", "animal": "ماعز", "plant": "موز", "country": "مصر"}},
            {"letter": "ع", "answers": {"human": "علي", "animal": "عصفور", "plant": "عنب", "country": "عمان"}},
            {"letter": "س", "answers": {"human": "سعيد", "animal": "سمكة", "plant": "سفرجل", "country": "سوريا"}},
            {"letter": "ر", "answers": {"human": "راشد", "animal": "رمة", "plant": "رمان", "country": "روسيا"}},
            {"letter": "ن", "answers": {"human": "نورة", "animal": "نمر", "plant": "نعناع", "country": "نيجيريا"}}
        ]
        self.questions = []
        self.current_question = None
        self.hints_used = 0
        self.question_number = 0
        self.total_questions = 5
        self.player_scores = {}

    def start_game(self):
        self.questions = random.sample(self.all_questions, min(self.total_questions, len(self.all_questions)))
        self.question_number = 0
        self.player_scores = {}
        self.hints_used = 0
        return self.next_question()

    def next_question(self):
        if self.question_number >= self.total_questions:
            return None
        self.current_question = self.questions[self.question_number]
        self.question_number += 1
        self.hints_used = 0
        
        card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": self.C['bg'],
                "paddingAll": "0px",
                "contents": [{
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": self.C['topbg'],
                    "paddingTop": "35px",
                    "paddingBottom": "140px",
                    "contents": [{
                        "type": "box",
                        "layout": "vertical",
                        "cornerRadius": "25px",
                        "backgroundColor": self.C['bg'],
                        "paddingAll": "0px",
                        "offsetTop": "55px",
                        "borderWidth": "2px",
                        "borderColor": self.C['border'],
                        "contents": [
                            {
                                "type": "box",
                                "layout": "vertical",
                                "paddingAll": "24px",
                                "paddingBottom": "20px",
                                "backgroundColor": self.C['card'],
                                "cornerRadius": "25px 25px 0px 0px",
                                "contents": [
                                    {"type": "text", "text": "🎲 إنسان حيوان نبات بلد", "weight": "bold", "size": "lg", "align": "center", "color": self.C['glow']},
                                    {"type": "text", "text": f"السؤال {self.question_number} من {self.total_questions}", "size": "sm", "align": "center", "color": self.C['text2'], "margin": "sm"}
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "height": "6px",
                                "backgroundColor": self.C['sep'],
                                "contents": [{
                                    "type": "box",
                                    "layout": "vertical",
                                    "backgroundColor": self.C['cyan'],
                                    "width": f"{(self.question_number/self.total_questions)*100}%",
                                    "height": "6px"
                                }]
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "paddingAll": "24px",
                                "spacing": "lg",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "backgroundColor": self.C['glass'],
                                        "cornerRadius": "18px",
                                        "paddingAll": "22px",
                                        "borderWidth": "1px",
                                        "borderColor": self.C['border'],
                                        "contents": [
                                            {"type": "text", "text": "الحرف:", "size": "md", "color": self.C['text2'], "align": "center"},
                                            {"type": "text", "text": self.current_question['letter'], "size": "3xl", "weight": "bold", "color": self.C['cyan'], "align": "center", "margin": "md"}
                                        ]
                                    },
                                    {"type": "text", "text": "أكتب بالترتيب:\nإنسان\nحيوان\nنبات\nبلد", "size": "md", "color": self.C['text'], "align": "center", "margin": "md", "wrap": True},
                                    {"type": "separator", "color": self.C['sep'], "margin": "lg"},
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "spacing": "md",
                                        "margin": "lg",
                                        "contents": [
                                            {"type": "button", "action": {"type": "message", "label": "💡 لمح", "text": "لمح"}, "style": "secondary", "color": "#FFFFFF", "height": "md"},
                                            {"type": "button", "action": {"type": "message", "label": "📝 جاوب", "text": "جاوب"}, "style": "primary", "color": self.C['cyan'], "height": "md"}
                                        ]
                                    }
                                ]
                            }
                        ]
                    }]
                }]
            }
        }
        return FlexSendMessage(alt_text=f"السؤال {self.question_number} - إنسان حيوان نبات بلد", contents=card)

    def get_hint(self):
        if not self.current_question:
            return None
        human = self.current_question['answers']['human']
        first_letter = human[0]
        word_length = len(human)
        hint_text = f"{first_letter} " + "_ " * (word_length - 1)
        self.hints_used += 1
        
        card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": self.C['card'],
                "cornerRadius": "20px",
                "paddingAll": "24px",
                "borderWidth": "2px",
                "borderColor": self.C['border'],
                "contents": [
                    {"type": "text", "text": "💡 تلميح", "weight": "bold", "size": "xl", "color": self.C['glow'], "align": "center"},
                    {"type": "separator", "color": self.C['sep'], "margin": "md"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "backgroundColor": self.C['glass'],
                        "cornerRadius": "15px",
                        "paddingAll": "18px",
                        "margin": "lg",
                        "contents": [
                            {"type": "text", "text": f"إنسان: {hint_text}", "size": "lg", "color": self.C['text'], "align": "center", "wrap": True},
                            {"type": "text", "text": f"عدد الحروف: {word_length}", "size": "md", "color": self.C['text2'], "align": "center", "margin": "md"}
                        ]
                    },
                    {"type": "text", "text": "⚠️ النقاط ستنخفض إلى نصف القيمة", "size": "sm", "color": "#FFB800", "align": "center", "margin": "lg", "wrap": True}
                ]
            }
        }
        return FlexSendMessage(alt_text="تلميح", contents=card)

    def show_answer(self):
        if not self.current_question:
            return None
        answers = self.current_question['answers']
        answer_text = f"إنسان: {answers['human']}\nحيوان: {answers['animal']}\nنبات: {answers['plant']}\nبلد: {answers['country']}"
        
        card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": self.C['card'],
                "cornerRadius": "20px",
                "paddingAll": "24px",
                "borderWidth": "2px",
                "borderColor": self.C['border'],
                "contents": [
                    {"type": "text", "text": "📝 الإجابة الصحيحة", "weight": "bold", "size": "xl", "color": self.C['glow'], "align": "center"},
                    {"type": "separator", "color": self.C['sep'], "margin": "md"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "backgroundColor": self.C['glass'],
                        "cornerRadius": "15px",
                        "paddingAll": "20px",
                        "margin": "lg",
                        "contents": [
                            {"type": "text", "text": answer_text, "size": "lg", "weight": "bold", "color": self.C['cyan'], "align": "center", "wrap": True}
                        ]
                    }
                ]
            }
        }
        return FlexSendMessage(alt_text="الإجابة الصحيحة", contents=card)

    def check_answer(self, answer, user_id, display_name):
        if not self.current_question:
            return None
        user_answers = [normalize_text(line.strip()) for line in answer.split('\n') if line.strip()]
        correct_answers = [
            normalize_text(self.current_question['answers']['human']),
            normalize_text(self.current_question['answers']['animal']),
            normalize_text(self.current_question['answers']['plant']),
            normalize_text(self.current_question['answers']['country'])
        ]
        
        if len(user_answers) >= 4 and user_answers[:4] == correct_answers:
            points = 2 if self.hints_used == 0 else 1
            if user_id not in self.player_scores:
                self.player_scores[user_id] = {'name': display_name, 'score': 0}
            self.player_scores[user_id]['score'] += points
            return {'response': TextSendMessage(text=f"✅ إجابة صحيحة! +{points} نقطة"), 'points': points, 'correct': True}
        return None

    def get_final_results(self):
        if not self.player_scores:
            return TextSendMessage(text="⚠️ لم يشارك أحد في اللعبة")
        sorted_players = sorted(self.player_scores.items(), key=lambda x: x[1]['score'], reverse=True)
        winners_content = []
        rank_emojis = {1: "🥇", 2: "🥈", 3: "🥉"}
        
        for idx, (user_id, data) in enumerate(sorted_players[:5], 1):
            emoji = rank_emojis.get(idx, f"{idx}️⃣")
            winners_content.append({
                "type": "box",
                "layout": "horizontal",
                "backgroundColor": self.C['glass'],
                "cornerRadius": "12px",
                "paddingAll": "14px",
                "margin": "sm" if idx > 1 else "none",
                "contents": [
                    {"type": "text", "text": emoji, "size": "xl", "flex": 0},
                    {"type": "text", "text": data['name'], "size": "md", "color": self.C['text'], "flex": 3, "margin": "md"},
                    {"type": "text", "text": f"{data['score']} 🏆", "size": "md", "color": self.C['cyan'], "align": "end", "flex": 1}
                ]
            })
        
        card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": self.C['bg'],
                "paddingAll": "0px",
                "contents": [{
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": self.C['topbg'],
                    "paddingTop": "35px",
                    "paddingBottom": "140px",
                    "contents": [{
                        "type": "box",
                        "layout": "vertical",
                        "cornerRadius": "25px",
                        "backgroundColor": self.C['bg'],
                        "paddingAll": "28px",
                        "offsetTop": "55px",
                        "borderWidth": "2px",
                        "borderColor": self.C['border'],
                        "contents": [
                            {"type": "text", "text": "🎉 انتهت اللعبة!", "weight": "bold", "size": "xxl", "align": "center", "color": self.C['glow']},
                            {"type": "separator", "color": self.C['sep'], "margin": "lg"},
                            {"type": "text", "text": "🏆 لوحة الصدارة", "size": "lg", "align": "center", "color": self.C['text'], "margin": "lg"},
                            {"type": "box", "layout": "vertical", "margin": "lg", "contents": winners_content},
                            {"type": "button", "action": {"type": "message", "label": "🔄 لعب مرة أخرى", "text": "إعادة"}, "style": "primary", "color": self.C['cyan'], "height": "md", "margin": "xl"}
                        ]
                    }]
                }]
            }
        }
        return FlexSendMessage(alt_text="النتائج النهائية", contents=card)


# ============= دوال مساعدة لـ app.py =============
def start_game(game_type, line_bot_api):
    """تشغيل لعبة حسب النوع"""
    games_map = {
        'opposite': OppositeGame,
        'song': SongGame,
        'chain': ChainWordsGame,
        'order': OrderGame,
        'build': LettersWordsGame,
        'lbgame': HumanAnimalPlantGame
    }
    
    if game_type in games_map:
        game = games_map[game_type](line_bot_api)
        return game.start_game(), game
    return None, None


def check_game_answer(game, answer, user_id, display_name):
    """التحقق من الإجابة"""
    if game:
        return game.check_answer(answer, user_id, display_name)
    return Nonepx",
                    "paddingBottom": "140px",
                    "contents": [{
                        "type": "box",
                        "layout": "vertical",
                        "cornerRadius": "25px",
                        "backgroundColor": self.C['bg'],
                        "paddingAll": "28px",
                        "offsetTop": "55px",
                        "borderWidth": "2px",
                        "borderColor": self.C['border'],
                        "contents": [
                            {"type": "text", "text": "🎉 انتهت اللعبة!", "weight": "bold", "size": "xxl", "align": "center", "color": self.C['glow']},
                            {"type": "separator", "color": self.C['sep'], "margin": "lg"},
                            {"type": "text", "text": "🏆 لوحة الصدارة", "size": "lg", "align": "center", "color": self.C['text'], "margin": "lg"},
                            {"type": "box", "layout": "vertical", "margin": "lg", "contents": winners_content},
                            {"type": "button", "action": {"type": "message", "label": "🔄 لعب مرة أخرى", "text": "إعادة"}, "style": "primary", "color": self.C['cyan'], "height": "md", "margin": "xl"}
                        ]
                    }]
                }]
            }
        }
        return FlexSendMessage(alt_text="النتائج النهائية", contents=card)


# ============= 2. لعبة الأغنية (SongGame) =============
class SongGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.C = COLORS
        self.all_songs = [
            {"lyrics": "قولي أحبك كي تزيد وسامتي", "singer": "كاظم الساهر"},
            {"lyrics": "يا طيور الطايرة فوق الحدود", "singer": "عبد المجيد عبدالله"},
            {"lyrics": "أنا لو عشقت حبيبي بجنون", "singer": "نجوى كرم"},
            {"lyrics": "حبيبي يا نور العين", "singer": "عمرو دياب"},
            {"lyrics": "على مودك يا بعد عمري", "singer": "محمد عبده"},
            {"lyrics": "تعبت من الصبر والانتظار", "singer": "راشد الماجد"},
            {"lyrics": "يا حبيبي كل اللي ودّك فيه", "singer": "أصالة"},
            {"lyrics": "كل عام وانت حبيبي", "singer": "وائل كفوري"},
            {"lyrics": "ما بلاش تبعد عني", "singer": "إليسا"},
            {"lyrics": "يا قمر يا قمر يا قمر", "singer": "نانسي عجرم"}
        ]
        self.questions = []
        self.current_song = None
        self.hints_used = 0
        self.question_number = 0
        self.total_questions = 5
        self.player_scores = {}

    def start_game(self):
        self.questions = random.sample(self.all_songs, min(self.total_questions, len(self.all_songs)))
        self.question_number = 0
        self.player_scores = {}
        self.hints_used = 0
        return self.next_question()

    def next_question(self):
        if self.question_number >= self.total_questions:
            return None
        self.current_song = self.questions[self.question_number]
        self.question_number += 1
        self.hints_used = 0
        
        card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": self.C['bg'],
                "paddingAll": "0px",
                "contents": [{
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": self.C['topbg'],
                    "paddingTop": "35px",
                    "paddingBottom": "140px",
                    "contents": [{
                        "type": "box",
                        "layout": "vertical",
                        "cornerRadius": "25px",
                        "backgroundColor": self.C['bg'],
                        "paddingAll": "0px",
                        "offsetTop": "55px",
                        "borderWidth": "2px",
                        "borderColor": self.C['border'],
                        "contents": [
                            {
                                "type": "box",
                                "layout": "vertical",
                                "paddingAll": "24px",
                                "paddingBottom": "20px",
                                "backgroundColor": self.C['card'],
                                "cornerRadius": "25px 25px 0px 0px",
                                "contents": [
                                    {"type": "text", "text": "🎵 لعبة الأغنية", "weight": "bold", "size": "xl", "align": "center", "color": self.C['glow']},
                                    {"type": "text", "text": f"السؤال {self.question_number} من {self.total_questions}", "size": "sm", "align": "center", "color": self.C['text2'], "margin": "sm"}
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "height": "6px",
                                "backgroundColor": self.C['sep'],
                                "contents": [{
                                    "type": "box",
                                    "layout": "vertical",
                                    "backgroundColor": self.C['cyan'],
                                    "width": f"{(self.question_number/self.total_questions)*100}%",
                                    "height": "6px"
                                }]
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "paddingAll": "24px",
                                "spacing": "lg",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "backgroundColor": self.C['glass'],
                                        "cornerRadius": "18px",
                                        "paddingAll": "22px",
                                        "borderWidth": "1px",
                                        "borderColor": self.C['border'],
                                        "contents": [
                                            {"type": "text", "text": "🎤 كلمات الأغنية:", "size": "md", "color": self.C['text2'], "align": "center"},
                                            {"type": "text", "text": self.current_song['lyrics'], "size": "lg", "weight": "bold", "color": self.C['cyan'], "align": "center", "margin": "md", "wrap": True}
                                        ]
                                    },
                                    {"type": "text", "text": "من المغني؟", "size": "md", "color": self.C['text'], "align": "center", "margin": "md"},
                                    {"type": "separator", "color": self.C['sep'], "margin": "lg"},
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "spacing": "md",
                                        "margin": "lg",
                                        "contents": [
                                            {"type": "button", "action": {"type": "message", "label": "💡 لمح", "text": "لمح"}, "style": "secondary", "color": "#FFFFFF", "height": "md"},
                                            {"type": "button", "action": {"type": "message", "label": "📝 جاوب", "text": "جاوب"}, "style": "primary", "color": self.C['cyan'], "height": "md"}
                                        ]
                                    }
                                ]
                            }
                        ]
                    }]
                }]
            }
        }
        return FlexSendMessage(alt_text=f"السؤال {self.question_number} - لعبة الأغنية", contents=card)

    def get_hint(self):
        if not self.current_song:
            return None
        singer = self.current_song['singer']
        first_letter = singer[0]
        word_length = len(singer)
        hint_text = f"{first_letter} " + "_ " * (word_length - 1)
        self.hints_used += 1
        
        card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": self.C['card'],
                "cornerRadius": "20px",
                "paddingAll": "24px",
                "borderWidth": "2px",
                "borderColor": self.C['border'],
                "contents": [
                    {"type": "text", "text": "💡 تلميح", "weight": "bold", "size": "xl", "color": self.C['glow'], "align": "center"},
                    {"type": "separator", "color": self.C['sep'], "margin": "md"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "backgroundColor": self.C['glass'],
                        "cornerRadius": "15px",
                        "paddingAll": "18px",
                        "margin": "lg",
                        "contents": [
                            {"type": "text", "text": f"أول حرف: {hint_text}", "size": "lg", "color": self.C['text'], "align": "center", "wrap": True},
                            {"type": "text", "text": f"عدد الحروف: {word_length}", "size": "md", "color": self.C['text2'], "align": "center", "margin": "md"}
                        ]
                    },
                    {"type": "text", "text": "⚠️ النقاط ستنخفض إلى نصف القيمة", "size": "sm", "color": "#FFB800", "align": "center", "margin": "lg", "wrap": True}
                ]
            }
        }
        return FlexSendMessage(alt_text="تلميح", contents=card)

    def show_answer(self):
        if not self.current_song:
            return None
        card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": self.C['card'],
                "cornerRadius": "20px",
                "paddingAll": "24px",
                "borderWidth": "2px",
                "borderColor": self.C['border'],
                "contents": [
                    {"type": "text", "text": "📝 الإجابة الصحيحة", "weight": "bold", "size": "xl", "color": self.C['glow'], "align": "center"},
                    {"type": "separator", "color": self.C['sep'], "margin": "md"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "backgroundColor": self.C['glass'],
                        "cornerRadius": "15px",
                        "paddingAll": "20px",
                        "margin": "lg",
                        "contents": [
                            {"type": "text", "text": self.current_song['singer'], "size": "xxl", "weight": "bold", "color": self.C['cyan'], "align": "center"}
                        ]
                    }
                ]
            }
        }
        return FlexSendMessage(alt_text="الإجابة الصحيحة", contents=card)

    def check_answer(self, answer, user_id, display_name):
        if not self.current_song:
            return None
        if normalize_text(answer) == normalize_text(self.current_song['singer']):
            points = 2 if self.hints_used == 0 else 1
            if user_id not in self.player_scores:
                self.player_scores[user_id] = {'name': display_name, 'score': 0}
            self.player_scores[user_id]['score'] += points
            return {'response': TextSendMessage(text=f"✅ إجابة صحيحة! +{points} نقطة"), 'points': points, 'correct': True}
        return None

    def get_final_results(self):
        if not self.player_scores:
            return TextSendMessage(text="⚠️ لم يشارك أحد في اللعبة")
        sorted_players = sorted(self.player_scores.items(), key=lambda x: x[1]['score'], reverse=True)
        winners_content = []
        rank_emojis = {1: "🥇", 2: "🥈", 3: "🥉"}
        
        for idx, (user_id, data) in enumerate(sorted_players[:5], 1):
            emoji = rank_emojis.get(idx, f"{idx}️⃣")
            winners_content.append({
                "type": "box",
                "layout": "horizontal",
                "backgroundColor": self.C['glass'],
                "cornerRadius": "12px",
                "paddingAll": "14px",
                "margin": "sm" if idx > 1 else "none",
                "contents": [
                    {"type": "text", "text": emoji, "size": "xl", "flex": 0},
                    {"type": "text", "text": data['name'], "size": "md", "color": self.C['text'], "flex": 3, "margin": "md"},
                    {"type": "text", "text": f"{data['score']} 🏆", "size": "md", "color": self.C['cyan'], "align": "end", "flex": 1}
                ]
            })
        
        card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": self.C['bg'],
                "paddingAll": "0px",
                "contents": [{
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": self.C['topbg'],
                    "paddingTop": "35px",
                    "paddingBottom": "140px",
                    "contents": [{
                        "type": "box",
                        "layout": "vertical",
                        "cornerRadius": "25px",
                        "backgroundColor": self.C['bg'],
                        "paddingAll": "28px",
                        "offsetTop": "55px",
                        "borderWidth": "2px",
                        "borderColor": self.C['border'],
                        "contents": [
                            {"type": "text", "text": "🎉 انتهت اللعبة!", "weight": "bold", "size": "xxl", "align": "center", "color": self.C['glow']},
                            {"type": "separator", "color": self.C['sep'], "margin": "lg"},
                            {"type": "text", "text": "🏆 لوحة الصدارة", "size": "lg", "align": "center", "color": self.C['text'], "margin": "lg"},
                            {"type": "box", "layout": "vertical", "margin": "lg", "contents": winners_content},
                            {"type": "button", "action": {"type": "message", "label": "🔄 لعب مرة أخرى", "text": "إعادة"}, "style": "primary", "color": self.C['cyan'], "height": "md", "margin": "xl"}
                        ]
                    }]
                }]
            }
        }
        return FlexSendMessage(alt_text="النتائج النهائية", contents=card)


# ============= 3. لعبة سلسلة الكلمات (ChainWordsGame) =============
class ChainWordsGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.C = COLORS
        self.words_chain = [
            ["رياض", "ضياء", "ءامل", "لبنان", "نور"],
            ["سلام", "ملك", "كرم", "محمد", "دمشق"],
            ["قمر", "رمان", "نجم", "ماء", "ءيمان"],
            ["بحر", "رمل", "ليمون", "نسيم", "ماجد"],
            ["جبل", "لحم", "مصر", "رياح", "حلب"]
        ]
        self.current_chain = []
        self.current_index = 0
        self.hints_used = 0
        self.question_number = 0
        self.total_questions = 5
        self.player_scores = {}

    def start_game(self):
        self.current_chain = random.choice(self.words_chain)
        self.current_index = 0
        self.question_number = 0
        self.player_scores = {}
        self.hints_used = 0
        return self.next_question()

    def next_question(self):
        if self.question_number >= self.total_questions or self.current_index >= len(self.current_chain) - 1:
            return None
        self.question_number += 1
        self.hints_used = 0
        current_word = self.current_chain[self.current_index]
        
        card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": self.C['bg'],
                "paddingAll": "0px",
                "contents": [{
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": self.C['topbg'],
                    "paddingTop": "35px",
                    "paddingBottom": "140px",
                    "contents": [{
                        "type": "box",
                        "layout": "vertical",
                        "cornerRadius": "25px",
                        "backgroundColor": self.C['bg'],
                        "paddingAll": "0px",
                        "offsetTop": "55px",
                        "borderWidth": "2px",
                        "borderColor": self.C['border'],
                        "contents": [
                            {
                                "type": "box",
                                "layout": "vertical",
                                "paddingAll": "24px",
                                "paddingBottom": "20px",
                                "backgroundColor": self.C['card'],
                                "cornerRadius": "25px 25px 0px 0px",
                                "contents": [
                                    {"type": "text", "text": "⛓️ سلسلة الكلمات", "weight": "bold", "size": "xl", "align": "center", "color": self.C['glow']},
                                    {"type": "text", "text": f"السؤال {self.question_number} من {self.total_questions}", "size": "sm", "align": "center", "color": self.C['text2'], "margin": "sm"}
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "height": "6px",
                                "backgroundColor": self.C['sep'],
                                "contents": [{
                                    "type": "box",
                                    "layout": "vertical",
                                    "backgroundColor": self.C['cyan'],
                                    "width": f"{(self.question_number/self.total_questions)*100}%",
                                    "height": "6px"
                                }]
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "paddingAll": "24px",
                                "spacing": "lg",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "backgroundColor": self.C['glass'],
                                        "cornerRadius": "18px",
                                        "paddingAll": "22px",
                                        "borderWidth": "1px",
                                        "borderColor": self.C['border'],
                                        "contents": [
                                            {"type": "text", "text": "الكلمة الحالية:", "size": "md", "color": self.C['text2'], "align": "center"},
                                            {"type": "text", "text": current_word, "size": "xxl", "weight": "bold", "color": self.C['cyan'], "align": "center", "margin": "md"}
                                        ]
                                    },
                                    {"type": "text", "text": f"أكتب كلمة تبدأ بحرف: {current_word[-1]}", "size": "md", "color": self.C['text'], "align": "center", "margin": "md", "wrap": True},
                                    {"type": "separator", "color": self.C['sep'], "margin": "lg"},
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "spacing": "md",
                                        "margin": "lg",
                                        "contents": [
                                            {"type": "button", "action": {"type": "message", "label": "💡 لمح", "text": "لمح"}, "style": "secondary", "color": "#FFFFFF", "height": "md"},
                                            {"type": "button", "action": {"type": "message", "label": "📝 جاوب", "text": "جاوب"}, "style": "primary", "color": self.C['cyan'], "height": "md"}
                                        ]
                                    }
                                ]
                            }
                        ]
                    }]
                }]
            }
        }
        return FlexSendMessage(alt_text=f"السؤال {self.question_number} - سلسلة الكلمات", contents=card)

    def get_hint(self):
        if self.current_index >= len(self.current_chain) - 1:
            return None
        next_word = self.current_chain[self.current_index + 1]
        first_letter = next_word[0]
        word_length = len(next_word)
        hint_text = f"{first_letter} " + "_ " * (word_length - 1)
        self.hints_used += 1
        
        card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": self.C['card'],
                "cornerRadius": "20px",
                "paddingAll": "24px",
                "borderWidth": "2px",
                "borderColor": self.C['border'],
                "contents": [
                    {"type": "text", "text": "💡 تلميح", "weight": "bold", "size": "xl", "color": self.C['glow'], "align": "center"},
                    {"type": "separator", "color": self.C['sep'], "margin": "md"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "backgroundColor": self.C['glass'],
                        "cornerRadius": "15px",
                        "paddingAll": "18px",
                        "margin": "lg",
                        "contents": [
                            {"type": "text", "text": f"الكلمة: {hint_text}", "size": "lg", "color": self.C['text'], "align": "center", "wrap": True},
                            {"type": "text", "text": f"عدد الحروف: {word_length}", "size": "md", "color": self.C['text2'], "align": "center", "margin": "md"}
                        ]
                    },
                    {"type": "text", "text": "⚠️ النقاط ستنخفض إلى نصف القيمة", "size": "sm", "color": "#FFB800", "align": "center", "margin": "lg", "wrap": True}
                ]
            }
        }
        return FlexSendMessage(alt_text="تلميح", contents=card)

    def show_answer(self):
        if self.current_index >= len(self.current_chain) - 1:
            return None
        next_word = self.current_chain[self.current_index + 1]
        card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": self.C['card'],
                "cornerRadius": "20px",
                "paddingAll": "24px",
                "borderWidth": "2px",
                "borderColor": self.C['border'],
                "contents": [
                    {"type": "text", "text": "📝 الإجابة الصحيحة", "weight": "bold", "size": "xl", "color": self.C['glow'], "align": "center"},
                    {"type": "separator", "color": self.C['sep'], "margin": "md"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "backgroundColor": self.C['glass'],
                        "cornerRadius": "15px",
                        "paddingAll": "20px",
                        "margin": "lg",
                        "contents": [
                            {"type": "text", "text": next_word, "size": "xxl", "weight": "bold", "color": self.C['cyan'], "align": "center"}
                        ]
                    }
                ]
            }
        }
        return FlexSendMessage(alt_text="الإجابة الصحيحة", contents=card)

    def check_answer(self, answer, user_id, display_name):
        if self.current_index >= len(self.current_chain) - 1:
            return None
        next_word = self.current_chain[self.current_index + 1]
        if normalize_text(answer) == normalize_text(next_word):
            points = 2 if self.hints_used == 0 else 1
            if user_id not in self.player_scores:
                self.player_scores[user_id] = {'name': display_name, 'score': 0}
            self.player_scores[user_id]['score'] += points
            self.current_index += 1
            return {'response': TextSendMessage(text=f"✅ إجابة صحيحة! +{points} نقطة"), 'points': points, 'correct': True}
        return None

    def get_final_results(self):
        if not self.player_scores:
            return TextSendMessage(text="⚠️ لم يشارك أحد في اللعبة")
        sorted_players = sorted(self.player_scores.items(), key=lambda x: x[1]['score'], reverse=True)
        winners_content = []
        rank_emojis = {1: "🥇", 2: "🥈", 3: "🥉"}
        
        for idx, (user_id, data) in enumerate(sorted_players[:5], 1):
            emoji = rank_emojis.get(idx, f"{idx}️⃣")
            winners_content.append({
                "type": "box",
                "layout": "horizontal",
                "backgroundColor": self.C['glass'],
                "cornerRadius": "12px",
                "paddingAll": "14px",
                "margin": "sm" if idx > 1 else "none",
                "contents": [
                    {"type": "text", "text": emoji, "size": "xl", "flex": 0},
                    {"type": "text", "text": data['name'], "size": "md", "color": self.C['text'], "flex": 3, "margin": "md"},
                    {"type": "text", "text": f"{data['score']} 🏆", "size": "md", "color": self.C['cyan'], "align": "end", "flex": 1}
                ]
            })
        
        card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": self.C['bg'],
                "paddingAll": "0px",
                "contents": [{
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": self.C['topbg'],
                    "paddingTop": "35px",
                    "paddingBottom": "140px",
                    "contents": [{
                        "type": "box",
                        "layout": "vertical",
                        "cornerRadius": "25px",
                        "backgroundColor": self.C['bg'],
                        "paddingAll": "28px",
                        "offsetTop": "55px",
                        "borderWidth": "2px",
                        "borderColor": self.C['border'],
                        "contents": [
                            {"type": "text", "text": "🎉 انتهت اللعبة!", "weight": "bold", "size": "xxl", "align": "center", "color": self.C['glow']},
                            {"type": "separator", "color": self.C['sep'], "margin": "lg"},
                            {"type": "text", "text": "🏆 لوحة الصدارة", "size": "lg", "align": "center", "color": self.C['text'], "margin": "lg"},
                            {"type": "box", "layout": "vertical", "margin": "lg", "contents": winners_content},
                            {"type": "button", "action": {"type": "message", "label": "🔄 لعب مرة أخرى", "text": "إعادة"}, "style": "primary", "color": self.C['cyan'], "height": "md", "margin": "xl"}
                        ]
                    }]
                }]
            }
        }
        return FlexSendMessage(alt_text="النتائج النهائية", contents=card)


# ============= 4. لعبة الترتيب (OrderGame) =============
class OrderGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.C = COLORS
        self.all_questions = [
            {"items": ["ثانية", "دقيقة", "ساعة", "يوم"], "order": ["ثانية", "دقيقة", "ساعة", "يوم"], "type": "من الأصغر للأكبر"},
            {"items": ["كيلو", "جرام", "ملي", "طن"], "order": ["ملي", "جرام", "كيلو", "طن"], "type": "من الأصغر للأكبر"},
            {"items": ["قرن", "عام", "شهر", "أسبوع"], "order": ["أسبوع", "شهر", "عام", "قرن"], "type": "من الأصغر للأكبر"},
            {"items": ["محيط", "بحر", "نهر", "جدول"], "order": ["جدول", "نهر", "بحر", "محيط"], "type": "من الأصغر للأكبر"},
            {"items": ["جبل", "هضبة", "تل", "سهل"], "order": ["سهل", "تل", "هضبة", "جبل"], "type": "من الأصغر للأكبر"}
        ]
        self.questions = []
        self.current_question = None
        self.hints_used = 0
        self.question_number = 0
        self.total_questions = 5
        self.player_scores = {}

    def start_game(self):
        self.questions = random.sample(self.all_questions, min(self.total_questions, len(self.all_questions)))
        self.question_number = 0
        self.player_scores = {}
        self.hints_used = 0
        return self.next_question()

    def next_question(self):
        if self.question_number >= self.total_questions:
            return None
        self.current_question = self.questions[self.question_number]
        self.question_number += 1
        self.hints_used = 0
        shuffled_items = random.sample(self.current_question['items'], len(self.current_question['items']))
        
        card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": self.C['bg'],
                "paddingAll": "0px",
                "contents": [{
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": self.C['topbg'],
                    "paddingTop": "35px",
                    "paddingBottom": "140px",
                    "contents": [{
                        "type": "box",
                        "layout": "vertical",
                        "cornerRadius": "25px",
                        "backgroundColor": self.C['bg'],
                        "paddingAll": "0px",
                        "offsetTop": "55px",
                        "borderWidth": "2px",
                        "borderColor": self.C['border'],
                        "contents": [
                            {
                                "type": "box",
                                "layout": "vertical",
                                "paddingAll": "24px",
                                "paddingBottom": "20px",
                                "backgroundColor": self.C['card'],
                                "cornerRadius": "25px 25px 0px 0px",
                                "contents": [
                                    {"type": "text", "text": "📊 لعبة الترتيب", "weight": "bold", "size": "xl", "align": "center", "color": self.C['glow']},
                                    {"type": "text", "text": f"السؤال {self.question_number} من {self.total_questions}", "size": "sm", "align": "center", "color": self.C['text2'], "margin": "sm"}
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "height": "6px",
                                "backgroundColor": self.C['sep'],
                                "contents": [{
                                    "type": "box",
                                    "layout": "vertical",
                                    "backgroundColor": self.C['cyan'],
                                    "width": f"{(self.question_number/self.total_questions)*100}%",
                                    "height": "6px"
                                }]
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "paddingAll": "24px",
                                "spacing": "lg",
                                "contents": [
                                    {"type": "text", "text": f"رتب العناصر {self.current_question['type']}", "size": "md", "color": self.C['text'], "align": "center", "wrap": True},
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "backgroundColor": self.C['glass'],
                                        "cornerRadius": "18px",
                                        "paddingAll": "22px",
                                        "margin": "md",
                                        "borderWidth": "1px",
                                        "borderColor": self.C['border'],
                                        "contents": [
                                            {"type": "text", "text": " • ".join(shuffled_items), "size": "lg", "weight": "bold", "color": self.C['cyan'], "align": "center", "wrap": True}
                                        ]
                                    },
                                    {"type": "text", "text": "أكتب الترتيب الصحيح مفصولاً بفواصل", "size": "sm", "color": self.C['text2'], "align": "center", "margin": "md", "wrap": True},
                                    {"type": "separator", "color": self.C['sep'], "margin": "lg"},
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "spacing": "md",
                                        "margin": "lg",
                                        "contents": [
                                            {"type": "button", "action": {"type": "message", "label": "💡 لمح", "text": "لمح"}, "style": "secondary", "color": "#FFFFFF", "height": "md"},
                                            {"type": "button", "action": {"type": "message", "label": "📝 جاوب", "text": "جاوب"}, "style": "primary", "color": self.C['cyan'], "height": "md"}
                                        ]
                                    }
                                ]
                            }
                        ]
                    }]
                }]
            }
        }
        return FlexSendMessage(alt_text=f"السؤال {self.question_number} - لعبة الترتيب", contents=card)

    def get_hint(self):
        if not self.current_question:
            return None
        first_two = self.current_question['order'][:2]
        self.hints_used += 1
        
        card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": self.C['card'],
                "cornerRadius": "20px",
                "paddingAll": "24px",
                "borderWidth": "2px",
                "borderColor": self.C['border'],
                "contents": [
                    {"type": "text", "text": "💡 تلميح", "weight": "bold", "size": "xl", "color": self.C['glow'], "align": "center"},
                    {"type": "separator", "color": self.C['sep'], "margin": "md"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "backgroundColor": self.C['glass'],
                        "cornerRadius": "15px",
                        "paddingAll": "18px",
                        "margin": "lg",
                        "contents": [
                            {"type": "text", "text": f"أول عنصرين: {first_two[0]}، {first_two[1]}", "size": "lg", "color": self.C['text'], "align": "center", "wrap": True}
                        ]
                    },
                    {"type": "text", "text": "⚠️ النقاط ستنخفض إلى نصف القيمة", "size": "sm", "color": "#FFB800", "align": "center", "margin": "lg", "wrap": True}
                ]
            }
        }
        return FlexSendMessage(alt_text="تلميح", contents=card)

    def show_answer(self):
        if not self.current_question:
            return None
        answer = "، ".join(self.current_question['order'])
        card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": self.C['card'],
                "cornerRadius": "20px",
                "paddingAll": "24px",
                "borderWidth": "2px",
                "borderColor": self.C['border'],
                "contents": [
                    {"type": "text", "text": "📝 الإجابة الصحيحة", "weight": "bold", "size": "xl", "color": self.C['glow'], "align": "center"},
                    {"type": "separator", "color": self.C['sep'], "margin": "md"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "backgroundColor": self.C['glass'],
                        "cornerRadius": "15px",
                        "paddingAll": "20px",
                        "margin": "lg",
                        "contents": [
                            {"type": "text", "text": answer, "size": "lg", "weight": "bold", "color": self.C['cyan'], "align": "center", "wrap": True}
                        ]
                    }
                ]
            }
        }
        return FlexSendMessage(alt_text="الإجابة الصحيحة", contents=card)

    def check_answer(self, answer, user_id, display_name):
        if not self.current_question:
            return None
        user_order = [normalize_text(item.strip()) for item in answer.replace('،', ',').split(',')]
        correct_order = [normalize_text(item) for item in self.current_question['order']]
        
        if user_order == correct_order:
            points = 2 if self.hints_used == 0 else 1
            if user_id not in self.player_scores:
                self.player_scores[user_id] = {'name': display_name, 'score': 0}
            self.player_scores[user_id]['score'] += points
            return {'response': TextSendMessage(text=f"✅ إجابة صحيحة! +{points} نقطة"), 'points': points, 'correct': True}
        return None

    def get_final_results(self):
        if not self.player_scores:
            return TextSendMessage(text="⚠️ لم يشارك أحد في اللعبة")
        sorted_players = sorted(self.player_scores.items(), key=lambda x: x[1]['score'], reverse=True)
        winners_content = []
        rank_emojis = {1: "🥇", 2: "🥈", 3: "🥉"}
        
        for idx, (user_id, data) in enumerate(sorted_players[:5], 1):
            emoji = rank_emojis.get(idx, f"{idx}️⃣")
            winners_content.append({
                "type": "box",
                "layout": "horizontal",
                "backgroundColor": self.C['glass'],
                "cornerRadius": "12px",
                "paddingAll": "14px",
                "margin": "sm" if idx > 1 else "none",
                "contents": [
                    {"type": "text", "text": emoji, "size": "xl", "flex": 0},
                    {"type": "text", "text": data['name'], "size": "md", "color": self.C['text'], "flex": 3, "margin": "md"},
                    {"type": "text", "text": f"{data['score']} 🏆", "size": "md", "color": self.C['cyan'], "align": "end", "flex": 1}
                ]
            })
        
        card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": self.C['bg'],
                "paddingAll": "0px",
                "contents": [{
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": self.C['topbg'],
                    "paddingTop": "35px",
                    "paddingBottom": "140px",
                    "contents": [{
                        "type": "box",
                        "layout": "vertical",
                        "cornerRadius": "25px",
                        "backgroundColor": self.C['bg'],
                        "paddingAll": "28px",
                        "offsetTop": "55px",
                        "borderWidth": "2px",
                        "borderColor": self.C['border'],
                        "contents": [
                            {"type": "text", "text": "🎉 انتهت اللعبة!", "weight": "bold", "size": "xxl", "align": "center", "color": self.C['glow']},
                            {"type": "separator", "color": self.C['sep'], "margin": "lg"},
                            {"type": "text", "text": "🏆 لوحة الصدارة", "size": "lg", "align": "center", "color": self.C['text'], "margin": "lg"},
                            {"type": "box", "layout": "vertical", "margin": "lg", "contents": winners_content},
                            {"type": "button", "action": {"type": "message", "label": "🔄 لعب مرة أخرى", "text": "إعادة"}, "style": "primary", "color": self.C['cyan'], "height": "md", "margin": "xl"}
                        ]
                    }]
                }]
            }
        }
        return FlexSendMessage(alt_text="النتائج النهائية", contents=card)


# ============= 5. لعبة تكوين الكلمات (LettersWordsGame) =============
class LettersWordsGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.C = COLORS
        self.all_questions = [
            {"letters": "م ح م د ل ي", "words": ["محمد", "ليمون", "محمل"]},
            {"letters": "ر ي ا ض س م", "words": ["رياض", "مريض", "رماد"]},
            {"letters": "ك ت ا ب ر م", "words": ["كتاب", "مكتب", "بركة"]},
            {"letters": "ق ل م ر س ي", "words": ["قلم", "رسم", "قمر"]},
            {"letters": "ش م س ر ق ي", "words": ["شمس", "شرق", "قمر"]}
        ]
        self.questions = []
        self.current_question = None
        self.hints_used = 0
        self.question_number = 0
        self.total_questions = 5
        self.player_scores = {}

    def start_game(self):
        self.questions = random.sample(self.all_questions, min(self.total_questions, len(self.all_questions)))
        self.question_number = 0
        self.player_scores = {}
        self.hints_used = 0
        return self.next_question()

    def next_question(self):
        if self.question_number >= self.total_questions:
            return None
        self.current_question = self.questions[self.question_number]
        self.question_number += 1
        self.hints_used = 0
        
        card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": self.C['bg'],
                "paddingAll": "0px",
                "contents": [{
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": self.C['topbg'],
                    "paddingTop": "35
