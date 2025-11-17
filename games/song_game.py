from linebot.models import TextSendMessage, FlexSendMessage
import random
import re

class SongGame:
    def __init__(self, line_bot_api, use_ai=False, ask_ai=None):
        self.line_bot_api = line_bot_api
        self.use_ai = use_ai
        self.ask_ai = ask_ai
        
        # 🎨 ألوان متناسقة مع صورة الحوت
        self.C = {
            'bg': '#0a0e1a',
            'card': '#111827',
            'card2': '#1f2937',
            'card3': '#374151',
            'text': '#F1F5F9',
            'text2': '#94A3B8',
            'text3': '#64748B',
            'sep': '#374151',
            'cyan': '#00D9FF',      # اللون الأزرق المتوهج من الصورة
            'cyan_glow': '#00E5FF', # توهج أفتح
            'purple': '#8B5CF6',    # الأرجواني من accent
        }
        
        self.current_song = None
        self.scores = {}
        self.answered = False
        self.hints_used = 0
        self.current_question = 1
        self.max_questions = 5
        
        self.songs = [
            {"lyrics": "أنا بلياك إذا أرمش إلك تنزل ألف دمعة", "singer": "ماجد المهندس"},
            {"lyrics": "يا بعدهم كلهم .. يا سراجي بينهم", "singer": "عبدالمجيد عبدالله"},
            {"lyrics": "أنا لحبيبي وحبيبي إلي", "singer": "فيروز"},
            {"lyrics": "قولي أحبك كي تزيد وسامتي", "singer": "كاظم الساهر"},
            {"lyrics": "كيف أبيّن لك شعوري دون ما أحكي", "singer": "عايض"},
            {"lyrics": "أريد الله يسامحني لان أذيت نفسي", "singer": "رحمة رياض"},
            {"lyrics": "جنّنت قلبي بحبٍ يلوي ذراعي", "singer": "ماجد المهندس"},
            {"lyrics": "واسِع خيالك إكتبه آنا بكذبك مُعجبه", "singer": "شمة حمدان"},
            {"lyrics": "خذني من ليلي لليلك", "singer": "عبادي الجوهر"},
            {"lyrics": "أنا عندي قلب واحد", "singer": "حسين الجسمي"},
            {"lyrics": "احس اني لقيتك بس عشان تضيع مني", "singer": "عبدالمجيد عبدالله"},
            {"lyrics": "قال الوداع و مقصده يجرح القلب", "singer": "راشد الماجد"},
            {"lyrics": "يا بنات يا بنات", "singer": "نانسي عجرم"},
            {"lyrics": "احبك موت كلمة مالها تفسير", "singer": "ماجد المهندس"},
            {"lyrics": "خلني مني طمني عليك", "singer": "نوال الكويتية"},
            {"lyrics": "رحت عني ما قويت جيت لك لاتردني", "singer": "عبدالمجيد عبدالله"},
            {"lyrics": "انسى هالعالم ولو هم يزعلون", "singer": "عباس ابراهيم"},
            {"lyrics": "مشاعر تشاور تودع تسافر", "singer": "شيرين"},
            {"lyrics": "جلست والخوف بعينيها تتأمل فنجاني", "singer": "عبد الحليم حافظ"},
            {"lyrics": "اسخر لك غلا وتشوفني مقصر", "singer": "عايض"}
        ]
        random.shuffle(self.songs)
    
    def normalize_text(self, text):
        if not text:
            return ""
        text = text.strip().lower()
        text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
        text = text.replace('ؤ', 'و').replace('ئ', 'ي').replace('ء', '')
        text = text.replace('ة', 'ه').replace('ى', 'ي')
        text = re.sub(r'[\u064B-\u065F]', '', text)
        text = re.sub(r'\s+', '', text)
        return text
    
    def create_3d_box(self, contents, bg_color=None, padding="20px", margin="none"):
        return {
            "type": "box",
            "layout": "vertical",
            "contents": contents,
            "backgroundColor": bg_color or self.C['card2'],
            "cornerRadius": "16px",
            "paddingAll": padding,
            "margin": margin,
            "borderWidth": "1px",
            "borderColor": self.C['sep']
        }
    
    def get_game_card(self, lyrics, question_num):
        bubble = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    # العنوان
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "box", "layout": "vertical", "contents": [],
                             "width": "4px", "backgroundColor": self.C['cyan'],
                             "cornerRadius": "2px"},
                            {"type": "box", "layout": "vertical", "contents": [
                                {"type": "text", "text": "🎵 لعبة الأغنية", "size": "xxl",
                                 "weight": "bold", "color": self.C['cyan']},
                                {"type": "text", "text": f"السؤال {question_num}/{self.max_questions}",
                                 "size": "sm", "color": self.C['text2'], "margin": "sm"}
                            ], "margin": "md"}
                        ]
                    },
                    {"type": "separator", "margin": "xl", "color": self.C['sep']},
                    
                    # كلمات الأغنية
                    self.create_3d_box([
                        {"type": "text", "text": lyrics, "size": "lg",
                         "color": self.C['text'], "align": "center", "wrap": True,
                         "weight": "bold"}
                    ], self.C['card'], "24px", "xl"),
                    
                    {"type": "text", "text": "من المغني؟", "size": "md",
                     "color": self.C['cyan_glow'], "align": "center",
                     "margin": "lg", "weight": "bold"},
                    
                    # شريط التقدم
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "box", "layout": "vertical", "contents": [],
                             "backgroundColor": self.C['cyan'], "height": "6px",
                             "flex": question_num, "cornerRadius": "3px"},
                            {"type": "box", "layout": "vertical", "contents": [],
                             "backgroundColor": self.C['card2'], "height": "6px",
                             "flex": self.max_questions - question_num, "cornerRadius": "3px"},
                        ],
                        "margin": "xl",
                        "spacing": "xs"
                    }
                ],
                "backgroundColor": self.C['bg'],
                "paddingAll": "24px"
            },
            "footer": {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {"type": "button", "action": {"type": "message", "label": "لمح", "text": "لمح"},
                     "style": "secondary", "color": self.C['card2'], "height": "sm"},
                    {"type": "button", "action": {"type": "message", "label": "جاوب", "text": "جاوب"},
                     "style": "secondary", "color": self.C['card2'], "height": "sm"},
                ],
                "spacing": "sm",
                "backgroundColor": self.C['bg'],
                "paddingAll": "16px"
            }
        }
        return bubble
    
    def start_game(self):
        self.current_question = 1
        self.scores = {}
        return self.next_question()
    
    def next_question(self):
        if self.current_question > self.max_questions:
            return None
        
        self.current_song = random.choice(self.songs)
        self.answered = False
        self.hints_used = 0
        
        card = self.get_game_card(
            self.current_song['lyrics'],
            self.current_question
        )
        
        return FlexSendMessage(
            alt_text=f"السؤال {self.current_question}",
            contents=card
        )
    
    def get_hint(self):
        if self.hints_used > 0:
            return {
                'response': TextSendMessage(text="⚠️ تم استخدام التلميح مسبقاً"),
                'correct': False
            }
        
        self.hints_used += 1
        singer_name = self.current_song['singer']
        first_letter = singer_name[0]
        
        hint_card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "box", "layout": "vertical", "contents": [],
                             "width": "4px", "backgroundColor": self.C['cyan'],
                             "cornerRadius": "2px"},
                            {"type": "text", "text": "💡 تلميح", "size": "xxl",
                             "weight": "bold", "color": self.C['cyan'], "margin": "md"}
                        ]
                    },
                    {"type": "separator", "margin": "xl", "color": self.C['sep']},
                    
                    self.create_3d_box([
                        {"type": "text", "text": "يبدأ بحرف", "size": "sm",
                         "color": self.C['text2'], "align": "center"},
                        {"type": "text", "text": first_letter, "size": "xxl",
                         "weight": "bold", "color": self.C['cyan_glow'],
                         "align": "center", "margin": "md"}
                    ], self.C['card'], "20px", "xl"),
                    
                    {"type": "text", "text": "⚠️ استخدام التلميح يقلل النقاط للنصف",
                     "size": "xs", "color": self.C['purple'],
                     "align": "center", "margin": "xl"}
                ],
                "backgroundColor": self.C['bg'],
                "paddingAll": "24px"
            }
        }
        
        return {
            'response': FlexSendMessage(alt_text="تلميح", contents=hint_card),
            'correct': False
        }
    
    def show_answer(self):
        card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "box", "layout": "vertical", "contents": [],
                             "width": "4px", "backgroundColor": self.C['cyan'],
                             "cornerRadius": "2px"},
                            {"type": "text", "text": "📝 الحل", "size": "xxl",
                             "weight": "bold", "color": self.C['cyan'], "margin": "md"}
                        ]
                    },
                    {"type": "separator", "margin": "xl", "color": self.C['sep']},
                    
                    self.create_3d_box([
                        {"type": "text", "text": self.current_song['singer'],
                         "size": "xxl", "color": self.C['cyan_glow'],
                         "weight": "bold", "align": "center", "wrap": True}
                    ], self.C['card'], "24px", "xl")
                ],
                "backgroundColor": self.C['bg'],
                "paddingAll": "24px"
            }
        }
        
        self.current_question += 1
        
        return {
            'response': FlexSendMessage(alt_text="الحل", contents=card),
            'correct': False,
            'next_question': self.current_question <= self.max_questions
        }
    
    def check_answer(self, text, user_id, display_name):
        if self.answered:
            return None
        
        ans = text.strip().lower()
        
        # تلميح
        if ans in ['لمح', 'تلميح', 'hint']:
            return self.get_hint()
        
        # الحل
        if ans in ['جاوب', 'الجواب', 'الحل', 'answer']:
            return self.show_answer()
        
        text_normalized = self.normalize_text(text)
        singer_normalized = self.normalize_text(self.current_song['singer'])
        
        if text_normalized == singer_normalized or singer_normalized in text_normalized:
            self.answered = True
            points = 2 if self.hints_used == 0 else 1
            
            if user_id not in self.scores:
                self.scores[user_id] = {'name': display_name, 'score': 0}
            self.scores[user_id]['score'] += points
            
            success_card = {
                "type": "bubble",
                "size": "mega",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        self.create_3d_box([
                            {"type": "text", "text": "✨", "size": "xxl", "align": "center"},
                            {"type": "text", "text": "إجابة صحيحة!", "size": "xxl",
                             "weight": "bold", "color": self.C['cyan'],
                             "align": "center", "margin": "md"}
                        ], self.C['card2']),
                        
                        {"type": "separator", "margin": "xl", "color": self.C['sep']},
                        
                        self.create_3d_box([
                            {"type": "text", "text": display_name, "size": "xl",
                             "weight": "bold", "color": self.C['text'], "align": "center"},
                            {"type": "text", "text": f"+{points} نقطة",
                             "size": "lg", "color": self.C['cyan_glow'],
                             "align": "center", "margin": "sm"}
                        ], self.C['card'], "24px", "xl")
                    ],
                    "backgroundColor": self.C['bg'],
                    "paddingAll": "24px"
                }
            }
            
            self.current_question += 1
            
            return {
                'response': FlexSendMessage(alt_text="صحيح", contents=success_card),
                'correct': True,
                'points': points,
                'won': True,
                'next_question': self.current_question <= self.max_questions
            }
        
        return None
