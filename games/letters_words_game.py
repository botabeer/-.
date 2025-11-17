import random
import re
from linebot.models import TextSendMessage, FlexSendMessage

class LettersWordsGame:
    def __init__(self, line_bot_api, use_ai=False, ask_ai=None):
        self.line_bot_api = line_bot_api
        self.use_ai = use_ai
        self.ask_ai = ask_ai
        
        # ألوان 3D Dark Experience
        self.C = {
            'bg': '#0a0e1a',
            'card': '#111827',
            'card2': '#1f2937',
            'card3': '#374151',
            'text': '#F1F5F9',
            'text2': '#94A3B8',
            'text3': '#64748B',
            'sep': '#374151',
            'gradient1': '#06B6D4',
            'gradient2': '#0EA5E9',
        }
        
        self.available_letters = []
        self.used_words = set()
        self.current_question = 1
        self.max_questions = 5
        self.players_scores = {}
        self.players_words = {}
        self.hint_used = False
        self.words_per_question = 3

        # مجموعات حروف منطقية
        self.letter_sets = [
            {
                "letters": "ق م ر ي ل ن",
                "words": ["قمر", "ليل", "مرق", "ريم", "نيل", "قرن", "ملي", "مير", "قيل", "ليم", "نمر", "مرن"]
            },
            {
                "letters": "ن ج م س و ر",
                "words": ["نجم", "نجوم", "سور", "نور", "سمر", "رسم", "جور", "نمر", "جرس", "سجن", "مرج", "رسوم", "سمور", "نسور"]
            },
            {
                "letters": "ب ح ر ي ن ل",
                "words": ["بحر", "بحرين", "بحري", "حرب", "نحل", "نيل", "لبن", "حبل", "نبيل", "نبل", "ربح", "بين", "حين"]
            },
            {
                "letters": "ك ت ب م ل و",
                "words": ["كتب", "مكتب", "ملك", "كمل", "كلم", "بلوت", "موت", "كوم", "ملت", "بكت", "تكلم"]
            },
            {
                "letters": "ش ج ر ة ي ن",
                "words": ["شجر", "شجرة", "جرة", "نشر", "تين", "جنة", "جين", "رجة", "شين", "شجن", "جشن"]
            },
            {
                "letters": "س م ك ن ا ه",
                "words": ["سمك", "سكن", "سما", "ماء", "سمان", "نام", "سام", "هام", "سهم", "اسم", "امن", "نهم", "مهن"]
            },
            {
                "letters": "ع ي ن ر ب د",
                "words": ["عين", "عربي", "عرب", "برد", "عبد", "بعد", "دين", "عيد", "برع", "عبر", "رعد", "عرين", "بعير"]
            },
            {
                "letters": "د ر س م ح ل",
                "words": ["درس", "مدرس", "رسم", "حلم", "سلم", "حرم", "حرس", "سحر", "حمل", "رحم", "حسد", "ملح", "رمح"]
            },
            {
                "letters": "ط ل ع م و ب",
                "words": ["طلع", "علم", "طعم", "عمل", "طمع", "بطل", "طول", "علب", "معلم", "طبع", "بعل"]
            },
            {
                "letters": "ح ب ر ط ي ق",
                "words": ["حبر", "حرب", "طرب", "طريق", "قرب", "طيب", "قطر", "حرق", "قبر", "حقب", "ربح"]
            }
        ]

    def normalize_text(self, text):
        """تطبيع النص"""
        if not text:
            return ""
        text = text.strip().lower()
        text = re.sub(r'^ال', '', text)
        text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
        text = text.replace('ؤ', 'و').replace('ئ', 'ي').replace('ء', '')
        text = text.replace('ة', 'ه').replace('ى', 'ي')
        text = re.sub(r'[\u064B-\u065F]', '', text)
        text = re.sub(r'\s+', '', text)
        return text

    def create_3d_box(self, contents, bg_color=None, padding="20px", margin="none"):
        """صندوق 3D محسّن"""
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

    def get_game_card(self, title, question_num, letters_str, instruction, show_buttons=True):
        """بطاقة اللعبة بتصميم 3D Dark Experience"""
        
        # تحويل الحروف إلى مربعات 3D
        letter_boxes = []
        letters_list = letters_str.split()
        
        for letter in letters_list:
            letter_boxes.append({
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": letter,
                        "size": "xxl",
                        "weight": "bold",
                        "color": self.C['gradient1'],
                        "align": "center"
                    }
                ],
                "backgroundColor": self.C['card2'],
                "cornerRadius": "16px",
                "width": "55px",
                "height": "65px",
                "justifyContent": "center",
                "borderWidth": "2px",
                "borderColor": self.C['sep']
            })
        
        # تقسيم الحروف إلى صفين
        first_row = letter_boxes[:3]
        second_row = letter_boxes[3:] if len(letter_boxes) > 3 else []
        
        letters_display = {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": first_row,
                    "spacing": "sm",
                    "justifyContent": "center"
                }
            ],
            "spacing": "sm"
        }
        
        if second_row:
            letters_display["contents"].append({
                "type": "box",
                "layout": "horizontal",
                "contents": second_row,
                "spacing": "sm",
                "justifyContent": "center"
            })
        
        # بناء البطاقة
        bubble = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    # Header مع شريط جانبي
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [],
                                "width": "4px",
                                "backgroundColor": self.C['gradient1'],
                                "cornerRadius": "2px"
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": title,
                                        "size": "xxl",
                                        "weight": "bold",
                                        "color": self.C['gradient1']
                                    },
                                    {
                                        "type": "text",
                                        "text": f"الجولة {question_num}/{self.max_questions}",
                                        "size": "sm",
                                        "color": self.C['text2'],
                                        "margin": "sm"
                                    }
                                ],
                                "margin": "md"
                            }
                        ]
                    },
                    
                    {"type": "separator", "margin": "xl", "color": self.C['sep']},
                    
                    # الحروف المتاحة
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "الحروف المتاحة",
                                "size": "sm",
                                "color": self.C['text2'],
                                "weight": "bold",
                                "align": "center"
                            },
                            letters_display
                        ],
                        "margin": "xl",
                        "spacing": "md"
                    },
                    
                    # التعليمات
                    self.create_3d_box([
                        {
                            "type": "text",
                            "text": instruction,
                            "size": "sm",
                            "color": self.C['text'],
                            "align": "center",
                            "wrap": True
                        }
                    ], self.C['card'], "16px", "xl"),
                    
                    # شريط التقدم
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [],
                                "backgroundColor": self.C['gradient1'],
                                "height": "6px",
                                "flex": question_num,
                                "cornerRadius": "3px"
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [],
                                "backgroundColor": self.C['card2'],
                                "height": "6px",
                                "flex": self.max_questions - question_num,
                                "cornerRadius": "3px"
                            }
                        ],
                        "margin": "xl",
                        "spacing": "xs"
                    }
                ],
                "backgroundColor": self.C['bg'],
                "paddingAll": "24px"
            }
        }
        
        # الأزرار
        if show_buttons:
            bubble["footer"] = {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "button",
                        "action": {"type": "message", "label": "لمح", "text": "لمح"},
                        "style": "secondary",
                        "color": self.C['card2'],
                        "height": "sm"
                    },
                    {
                        "type": "button",
                        "action": {"type": "message", "label": "جاوب", "text": "جاوب"},
                        "style": "secondary",
                        "color": self.C['card2'],
                        "height": "sm"
                    }
                ],
                "spacing": "sm",
                "backgroundColor": self.C['bg'],
                "paddingAll": "16px"
            }
        
        return bubble

    def start_game(self):
        """بدء اللعبة"""
        self.current_question = 1
        self.players_scores = {}
        self.players_words = {}
        return self.next_question()

    def next_question(self):
        """السؤال التالي"""
        if self.current_question > self.max_questions:
            return None

        letter_set = random.choice(self.letter_sets)
        self.available_letters = letter_set['letters'].split()
        self.valid_words_set = set(letter_set['words'])
        
        random.shuffle(self.available_letters)
        self.used_words.clear()
        self.hint_used = False
        self.players_words = {}

        letters_str = ' '.join(self.available_letters)
        
        flex_card = self.get_game_card(
            title="تكوين الكلمات",
            question_num=self.current_question,
            letters_str=letters_str,
            instruction=f"كوّن {self.words_per_question} كلمات صحيحة من الحروف\nأول لاعب يكمل يفوز"
        )
        
        return FlexSendMessage(
            alt_text=f"الجولة {self.current_question} - تكوين كلمات",
            contents=flex_card
        )

    def get_hint(self):
        """الحصول على تلميح"""
        if self.hint_used:
            return {
                'response': TextSendMessage(text="تم استخدام التلميح مسبقاً"),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': False
            }
        
        self.hint_used = True
        example_word = random.choice(list(self.valid_words_set)) if self.valid_words_set else ""
        
        first_letter = example_word[0] if example_word else ""
        word_length = len(example_word)
        hint_pattern = first_letter + " " + " ".join(["_"] * (word_length - 1))
        
        hint_card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    # Header
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [],
                                "width": "4px",
                                "backgroundColor": self.C['gradient1'],
                                "cornerRadius": "2px"
                            },
                            {
                                "type": "text",
                                "text": "تلميح",
                                "size": "xxl",
                                "weight": "bold",
                                "color": self.C['gradient1'],
                                "margin": "md"
                            }
                        ]
                    },
                    
                    {"type": "separator", "margin": "xl", "color": self.C['sep']},
                    
                    # نمط الكلمة
                    self.create_3d_box([
                        {
                            "type": "text",
                            "text": "أول حرف من الكلمة",
                            "size": "sm",
                            "color": self.C['text2'],
                            "align": "center"
                        },
                        {
                            "type": "text",
                            "text": hint_pattern,
                            "size": "xxl",
                            "weight": "bold",
                            "color": self.C['gradient1'],
                            "align": "center",
                            "margin": "md"
                        }
                    ], self.C['card'], "20px", "xl"),
                    
                    # عدد الحروف
                    self.create_3d_box([
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "عدد الحروف",
                                    "size": "sm",
                                    "color": self.C['text2'],
                                    "flex": 1
                                },
                                {
                                    "type": "text",
                                    "text": str(word_length),
                                    "size": "xl",
                                    "weight": "bold",
                                    "color": self.C['gradient1'],
                                    "flex": 0
                                }
                            ]
                        }
                    ], self.C['card2'], "16px", "md"),
                    
                    # تحذير
                    {
                        "type": "text",
                        "text": "النقاط ستنخفض إلى نصف القيمة",
                        "size": "xs",
                        "color": self.C['gradient2'],
                        "align": "center",
                        "margin": "xl"
                    }
                ],
                "backgroundColor": self.C['bg'],
                "paddingAll": "24px"
            }
        }
        
        return {
            'response': FlexSendMessage(alt_text="تلميح", contents=hint_card),
            'points': -1,
            'correct': False,
            'won': False,
            'game_over': False
        }

    def show_answer(self):
        """عرض الإجابة"""
        suggestions = sorted(self.valid_words_set, key=len, reverse=True)[:4]
        
        answer_card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    # Header
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [],
                                "width": "4px",
                                "backgroundColor": self.C['gradient1'],
                                "cornerRadius": "2px"
                            },
                            {
                                "type": "text",
                                "text": "الحل",
                                "size": "xxl",
                                "weight": "bold",
                                "color": self.C['gradient1'],
                                "margin": "md"
                            }
                        ]
                    },
                    
                    {"type": "separator", "margin": "xl", "color": self.C['sep']},
                    
                    {
                        "type": "text",
                        "text": "بعض الكلمات الصحيحة",
                        "size": "sm",
                        "color": self.C['text2'],
                        "margin": "xl"
                    },
                    
                    # الكلمات
                    self.create_3d_box([
                        {
                            "type": "text",
                            "text": " • ".join(suggestions),
                            "size": "md",
                            "weight": "bold",
                            "color": self.C['gradient1'],
                            "wrap": True,
                            "align": "center"
                        }
                    ], self.C['card'], "20px", "md")
                ],
                "backgroundColor": self.C['bg'],
                "paddingAll": "24px"
            }
        }

        self.current_question += 1
        
        if self.current_question <= self.max_questions:
            return {
                'response': FlexSendMessage(alt_text="الحل", contents=answer_card),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': False,
                'next_question': True
            }
        else:
            return self._end_game()

    def _end_game(self):
        """إنهاء اللعبة"""
        if not self.players_scores:
            return {
                'response': TextSendMessage(text="انتهت اللعبة - لم يشارك أحد"),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': True
            }

        sorted_players = sorted(
            self.players_scores.items(), 
            key=lambda x: x[1]['score'], 
            reverse=True
        )
        
        winner = sorted_players[0]
        
        # بطاقة الفائز
        score_items = []
        for i, (user_id, data) in enumerate(sorted_players, 1):
            rank = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
            
            score_items.append(
                self.create_3d_box([
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": f"{rank} {data['name']}",
                                "size": "sm",
                                "color": self.C['gradient1'] if i == 1 else self.C['text'],
                                "weight": "bold" if i <= 3 else "regular",
                                "flex": 3
                            },
                            {
                                "type": "text",
                                "text": str(data['score']),
                                "size": "lg" if i == 1 else "md",
                                "weight": "bold",
                                "color": self.C['gradient1'] if i == 1 else self.C['text2'],
                                "align": "end",
                                "flex": 1
                            }
                        ]
                    }
                ], self.C['card2'] if i == 1 else self.C['card3'], "16px", "sm")
            )
        
        winner_card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    self.create_3d_box([
                        {
                            "type": "text",
                            "text": "✨",
                            "size": "xxl",
                            "align": "center"
                        },
                        {
                            "type": "text",
                            "text": "انتهت اللعبة",
                            "size": "xl",
                            "weight": "bold",
                            "color": self.C['gradient1'],
                            "align": "center",
                            "margin": "md"
                        }
                    ], self.C['card2']),
                    
                    {"type": "separator", "margin": "xl", "color": self.C['sep']},
                    
                    # الفائز
                    self.create_3d_box([
                        {
                            "type": "text",
                            "text": "الفائز",
                            "size": "sm",
                            "color": self.C['text2'],
                            "align": "center"
                        },
                        {
                            "type": "text",
                            "text": winner[1]['name'],
                            "size": "xxl",
                            "weight": "bold",
                            "color": self.C['gradient1'],
                            "align": "center",
                            "margin": "sm"
                        },
                        {
                            "type": "text",
                            "text": f"{winner[1]['score']} نقطة",
                            "size": "lg",
                            "weight": "bold",
                            "color": self.C['gradient2'],
                            "align": "center",
                            "margin": "md"
                        }
                    ], self.C['card'], "24px", "xl"),
                    
                    {"type": "separator", "margin": "xl", "color": self.C['sep']},
                    
                    # النتائج النهائية
                    {
                        "type": "text",
                        "text": "النتائج النهائية",
                        "size": "lg",
                        "weight": "bold",
                        "color": self.C['text'],
                        "margin": "xl",
                        "align": "center"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": score_items,
                        "margin": "md"
                    }
                ],
                "backgroundColor": self.C['bg'],
                "paddingAll": "24px"
            },
            "footer": {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "button",
                        "action": {"type": "message", "label": "لعب مرة أخرى", "text": "تكوين"},
                        "style": "primary",
                        "color": self.C['gradient1'],
                        "height": "sm"
                    },
                    {
                        "type": "button",
                        "action": {"type": "message", "label": "الصدارة", "text": "الصدارة"},
                        "style": "secondary",
                        "color": self.C['card2'],
                        "height": "sm"
                    }
                ],
                "spacing": "sm",
                "backgroundColor": self.C['bg'],
                "paddingAll": "16px"
            }
        }

        return {
            'response': FlexSendMessage(alt_text="الفائز", contents=winner_card),
            'points': 0,
            'correct': False,
            'won': True,
            'game_over': True,
            'winner_card': winner_card
        }

    def can_form_word(self, word, letters):
        """التحقق من إمكانية تكوين الكلمة"""
        letters_list = letters.copy()
        for char in list(word):
            if char in letters_list:
                letters_list.remove(char)
            else:
                return False
        return True

    def check_answer(self, answer, user_id, display_name):
        """التحقق من الإجابة"""
        answer_lower = answer.strip().lower()
        
        if answer_lower in ['لمح', 'تلميح', 'hint']:
            return self.get_hint()
        
        if answer_lower in ['جاوب', 'الجواب', 'الحل', 'answer']:
            return self.show_answer()

        answer_word = self.normalize_text(answer)

        if answer_word in self.used_words:
            return {
                'response': TextSendMessage(text=f"الكلمة '{answer}' مستخدمة مسبقاً"),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': False
            }

        letters_no_spaces = [l for l in self.available_letters]
        if not self.can_form_word(answer_word, letters_no_spaces):
            return {
                'response': TextSendMessage(text=f"لا يمكن تكوين '{answer}' من الحروف المتاحة"),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': False
            }

        if len(answer_word) < 2:
            return {
                'response': TextSendMessage(text="الكلمة يجب أن تكون حرفين على الأقل"),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': False
            }

        normalized_valid = {self.normalize_text(w) for w in self.valid_words_set}
        if answer_word not in normalized_valid:
            return {
                'response': TextSendMessage(text=f"'{answer}' ليست من الكلمات المطلوبة\n\nحاول كلمة أخرى"),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': False
            }

        # الكلمة صحيحة
        self.used_words.add(answer_word)
        
        if user_id not in self.players_words:
            self.players_words[user_id] = 0
        self.players_words[user_id] += 1

        points = 2 if not self.hint_used else 1

        if user_id not in self.players_scores:
            self.players_scores[user_id] = {'name': display_name, 'score': 0}
        self.players_scores[user_id]['score'] += points

        # التحقق من اكتمال الكلمات
        if self.players_words[user_id] >= self.words_per_question:
            # فاز بالجولة
            success_card = {
                "type": "bubble",
                "size": "mega",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        self.create_3d_box([
                            {
                                "type": "text",
                                "text": "✨",
                                "size": "xxl",
                                "align": "center"
                            },
                            {
                                "type": "text",
                                "text": "أحسنت",
                                "size": "xxl",
                                "weight": "bold",
                                "color": self.C['gradient1'],
                                "align": "center",
                                "margin": "md"
                            }
                        ], self.C['card2']),
                        
                        {"type": "separator", "margin": "xl", "color": self.C['sep']},
                        
                        self.create_3d_box([
                            {
                                "type": "text",
                                "text": display_name,
                                "size": "xl",
                                "weight": "bold",
                                "color": self.C['text'],
                                "align": "center"
                            },
                            {
                                "type": "text",
                                "text": f"+{points} نقطة",
                                "size": "lg",
                                "color": self.C['gradient1'],
                                "align": "center",
                                "margin": "sm"
                            }
                        ], self.C['card'], "24px", "xl")
                    ],
                    "backgroundColor": self.C['bg'],
                    "paddingAll": "24px"
                }
            }
            
            self.current_question += 1
            
            if self.current_question <= self.max_questions:
                return {
                    'response': FlexSendMessage(alt_text="أحسنت", contents=success_card),
                    'points': points,
                    'correct': True,
                    'won': True,
                    'game_over': False,
                    'next_question': True
                }
            else:
                return self._end_game()
        else:
            # لم يكمل بعد
            remaining = self.words_per_question - self.players_words[user_id]
            
            progress_card = {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "✓ صحيح",
                            "size": "xl",
                            "weight": "bold",
                            "color": self.C['gradient1'],
                            "align": "center"
                        },
                        
                        {"type": "separator", "margin": "md", "color": self.C['sep']},
                        
                        self.create_3d_box([
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": display_name,
                                        "size": "sm",
                                        "color": self.C['text'],
                                        "flex": 2
                                    },
                                    {
                                        "type": "text",
                                        "text": f"+{points}",
                                        "size": "md",
                                        "weight": "bold",
                                        "color": self.C['gradient1'],
                                        "align": "end",
                                        "flex": 1
                                    }
                                ]
                            }
                        ], self.C['card2'], "12px", "md"),
                        
                        {"type": "separator", "margin": "lg", "color": self.C['sep']},
                        
                        {
                            "type": "text",
                            "text": f"متبقي {remaining} كلمة",
                            "size": "sm",
                            "color": self.C['text2'],
                            "align": "center",
                            "margin": "md"
                        }
                    ],
                    "backgroundColor": self.C['bg'],
                    "paddingAll": "20px"
                }
            }
            
            return {
                'response': FlexSendMessage(alt_text="صحيح", contents=progress_card),
                'points': points,
                'correct': True,
                'won': False,
                'game_over': False
            }
