import random
import re
from linebot.models import TextSendMessage, FlexSendMessage

class LettersWordsGame:
    def __init__(self, line_bot_api, use_ai=False, ask_ai=None):
        self.line_bot_api = line_bot_api
        self.use_ai = use_ai
        self.ask_ai = ask_ai
        
        self.available_letters = []
        self.used_words = set()
        self.current_question = 1
        self.max_questions = 5
        self.players_scores = {}
        self.players_words = {}  # تتبع عدد كلمات كل لاعب
        self.hint_used = False
        self.words_per_question = 3

        # ✅ مجموعات الحروف المحدثة (تم إصلاح التكرار)
        self.letter_sets = [
            {"letters": "س م ا ء ن ج", "words": ["سماء", "سما", "نجم", "ماء", "جمان", "نام", "سام", "جسم"]},
            {"letters": "ب ي ت ك م ل", "words": ["بيت", "ملك", "كمل", "بتل", "تيك", "يتم", "لبك", "كتب"]},
            {"letters": "ق ل م د ر س", "words": ["قلم", "درس", "مدر", "سرد", "قدم", "سلم", "رمد", "لمس"]},
            {"letters": "ش ج ر ة و ر", "words": ["شجر", "شجرة", "جور", "وجر", "شور", "رجو", "جرة", "ورة"]},
            {"letters": "ح ب ر ط ع م", "words": ["حبر", "حرب", "طعم", "عرب", "برع", "حرم", "ربع", "طرب"]},
            {"letters": "ط ع ا م ش ر", "words": ["طعام", "شرط", "معط", "شرع", "طرش", "عرش", "مطر", "شعر"]},
            {"letters": "ن ج م س م ا", "words": ["نجم", "سما", "ماس", "جسم", "نام", "جما", "سام", "نمس"]},
            {"letters": "م ك ت ب ق ل", "words": ["مكتب", "كتب", "قلب", "ملك", "بتل", "تكم", "بقل", "قبل"]},
            {"letters": "س ر ي ر ب ا", "words": ["سرير", "بيرس", "ريس", "سير", "بار", "رسي", "بري", "سري"]},
            {"letters": "ق م ر ل ي ل", "words": ["قمر", "ليل", "مرق", "ملي", "قيل", "ريم", "يمر", "مير"]}
        ]

    def normalize_text(self, text):
        """تطبيع النص لقبول جميع أشكال الحروف"""
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

    def get_neumorphism_card(self, title, question_num, letters_str, instruction, show_buttons=True):
        """بطاقة Neumorphism Dark الاحترافية"""
        
        # تحويل الحروف إلى مربعات منفصلة
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
                        "color": "#A78BFA",
                        "align": "center"
                    }
                ],
                "backgroundColor": "#1F2937",
                "cornerRadius": "12px",
                "width": "50px",
                "height": "60px",
                "justifyContent": "center",
                "paddingAll": "8px",
                "shadow": {
                    "offsetX": "4px",
                    "offsetY": "4px",
                    "blur": "8px",
                    "color": "#000000"
                }
            })
        
        # تقسيم الحروف إلى صفين إذا كانت أكثر من 3
        if len(letter_boxes) > 3:
            first_row = letter_boxes[:3]
            second_row = letter_boxes[3:]
        else:
            first_row = letter_boxes
            second_row = []
        
        letters_display = {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": first_row,
                    "spacing": "md",
                    "justifyContent": "center"
                }
            ],
            "spacing": "md"
        }
        
        if second_row:
            letters_display["contents"].append({
                "type": "box",
                "layout": "horizontal",
                "contents": second_row,
                "spacing": "md",
                "justifyContent": "center"
            })
        
        # بناء البطاقة
        bubble = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    # Header
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": title,
                                "size": "xl",
                                "weight": "bold",
                                "color": "#F3F4F6",
                                "align": "center"
                            },
                            {
                                "type": "text",
                                "text": f"سؤال {question_num} من {self.max_questions}",
                                "size": "sm",
                                "color": "#9CA3AF",
                                "align": "center",
                                "margin": "sm"
                            }
                        ],
                        "paddingAll": "20px",
                        "backgroundColor": "#111827",
                        "cornerRadius": "16px",
                        "margin": "none",
                        "shadow": {
                            "offsetX": "0px",
                            "offsetY": "4px",
                            "blur": "12px",
                            "color": "#000000"
                        }
                    },
                    # Separator
                    {
                        "type": "separator",
                        "margin": "xl",
                        "color": "#374151"
                    },
                    # Letters Section
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "الحروف المتاحة",
                                "size": "xs",
                                "color": "#6B7280",
                                "align": "center",
                                "weight": "bold"
                            },
                            letters_display
                        ],
                        "margin": "xl",
                        "spacing": "md"
                    },
                    # Instruction Box
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": instruction,
                                "size": "sm",
                                "color": "#D1D5DB",
                                "align": "center",
                                "wrap": True,
                                "weight": "bold"
                            }
                        ],
                        "backgroundColor": "#1F2937",
                        "cornerRadius": "12px",
                        "paddingAll": "16px",
                        "margin": "xl",
                        "shadow": {
                            "offsetX": "inset 2px",
                            "offsetY": "inset 2px",
                            "blur": "4px",
                            "color": "#000000"
                        }
                    },
                    # Progress indicator
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [],
                                "backgroundColor": "#A78BFA",
                                "height": "4px",
                                "flex": question_num,
                                "cornerRadius": "2px"
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [],
                                "backgroundColor": "#374151",
                                "height": "4px",
                                "flex": self.max_questions - question_num,
                                "cornerRadius": "2px"
                            }
                        ],
                        "margin": "xl",
                        "spacing": "sm"
                    }
                ],
                "backgroundColor": "#0F172A",
                "paddingAll": "24px"
            }
        }
        
        # إضافة الأزرار إذا كانت مطلوبة
        if show_buttons:
            bubble["footer"] = {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": "💡 تلميح",
                            "text": "لمح"
                        },
                        "style": "secondary",
                        "height": "sm",
                        "color": "#6366F1"
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": "✓ الحل",
                            "text": "جاوب"
                        },
                        "style": "secondary",
                        "height": "sm",
                        "color": "#8B5CF6"
                    }
                ],
                "spacing": "sm",
                "backgroundColor": "#1E293B",
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

        # اختيار مجموعة حروف عشوائية
        letter_set = random.choice(self.letter_sets)
        self.available_letters = letter_set['letters'].split()
        self.valid_words_set = set(letter_set['words'])
        
        random.shuffle(self.available_letters)
        self.used_words.clear()
        self.hint_used = False
        self.players_words = {}  # إعادة تعيين عدد الكلمات لكل لاعب

        letters_str = ' '.join(self.available_letters)
        
        flex_card = self.get_neumorphism_card(
            title="▪️ لعبة تكوين الكلمات",
            question_num=self.current_question,
            letters_str=letters_str,
            instruction=f"كوّن {self.words_per_question} كلمات من الحروف أعلاه\nأول لاعب يكمل يفوز بالجولة!"
        )
        
        return FlexSendMessage(
            alt_text=f"سؤال {self.current_question} - تكوين كلمات",
            contents=flex_card
        )

    def get_hint(self):
        """الحصول على تلميح"""
        if self.hint_used:
            return {
                'response': TextSendMessage(text="▫️ تم استخدام التلميح مسبقاً"),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': False
            }
        
        self.hint_used = True
        example_word = list(self.valid_words_set)[0] if self.valid_words_set else ""
        
        hint_card = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "💡 تلميح",
                        "size": "xl",
                        "weight": "bold",
                        "color": "#FCD34D",
                        "align": "center"
                    },
                    {
                        "type": "separator",
                        "margin": "lg",
                        "color": "#374151"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "مثال على كلمة صحيحة:",
                                "size": "sm",
                                "color": "#9CA3AF",
                                "margin": "lg"
                            },
                            {
                                "type": "text",
                                "text": example_word,
                                "size": "xxl",
                                "weight": "bold",
                                "color": "#A78BFA",
                                "align": "center",
                                "margin": "md"
                            },
                            {
                                "type": "text",
                                "text": "حاول تكوين كلمات من 2-4 أحرف",
                                "size": "xs",
                                "color": "#6B7280",
                                "wrap": True,
                                "margin": "lg",
                                "align": "center"
                            }
                        ],
                        "backgroundColor": "#1F2937",
                        "cornerRadius": "12px",
                        "paddingAll": "16px"
                    }
                ],
                "backgroundColor": "#0F172A",
                "paddingAll": "20px"
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
        """عرض الإجابة والانتقال للسؤال التالي"""
        suggestions = list(self.valid_words_set)[:4]
        
        answer_card = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "✓ الحل",
                        "size": "xl",
                        "weight": "bold",
                        "color": "#10B981",
                        "align": "center"
                    },
                    {
                        "type": "separator",
                        "margin": "lg",
                        "color": "#374151"
                    },
                    {
                        "type": "text",
                        "text": "بعض الكلمات الصحيحة:",
                        "size": "sm",
                        "color": "#9CA3AF",
                        "margin": "lg"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "، ".join(suggestions),
                                "size": "lg",
                                "weight": "bold",
                                "color": "#A78BFA",
                                "align": "center",
                                "wrap": True
                            }
                        ],
                        "backgroundColor": "#1F2937",
                        "cornerRadius": "12px",
                        "paddingAll": "16px",
                        "margin": "md"
                    }
                ],
                "backgroundColor": "#0F172A",
                "paddingAll": "20px"
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
        """إنهاء اللعبة وعرض النتائج"""
        if not self.players_scores:
            return {
                'response': TextSendMessage(text="▫️ انتهت اللعبة\n\nلم يشارك أحد"),
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
        all_scores = [(data['name'], data['score']) for name, data in sorted_players]

        from app import get_winner_card
        winner_card = get_winner_card(
            winner[1]['name'], 
            winner[1]['score'], 
            all_scores
        )

        return {
            'points': 0,
            'correct': False,
            'won': True,
            'game_over': True,
            'winner_card': winner_card
        }

    def can_form_word(self, word, letters):
        """التحقق من إمكانية تكوين الكلمة من الحروف المتاحة"""
        letters_list = letters.copy()
        word_letters = list(word)
        
        for char in word_letters:
            if char in letters_list:
                letters_list.remove(char)
            else:
                return False
        return True

    def check_answer(self, answer, user_id, display_name):
        """التحقق من إجابة المستخدم"""
        answer_lower = answer.strip().lower()
        
        if answer_lower in ['لمح', 'تلميح', 'hint']:
            return self.get_hint()
        
        if answer_lower in ['جاوب', 'الجواب', 'الحل', 'answer']:
            return self.show_answer()

        answer_word = self.normalize_text(answer)

        # التحقق من أن الكلمة لم تُستخدم
        if answer_word in self.used_words:
            return {
                'response': TextSendMessage(text=f"▫️ الكلمة '{answer}' مستخدمة مسبقاً"),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': False
            }

        # التحقق من إمكانية تكوين الكلمة
        letters_no_spaces = [l for l in self.available_letters]
        if not self.can_form_word(answer_word, letters_no_spaces):
            return {
                'response': TextSendMessage(text=f"▫️ لا يمكن تكوين '{answer}' من الحروف المتاحة"),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': False
            }

        if len(answer_word) < 2:
            return {
                'response': TextSendMessage(text="▫️ الكلمة يجب أن تكون حرفين على الأقل"),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': False
            }

        # التحقق من صحة الكلمة
        normalized_valid = {self.normalize_text(w) for w in self.valid_words_set}
        if answer_word not in normalized_valid:
            return {
                'response': TextSendMessage(text=f"▫️ '{answer}' ليست كلمة صحيحة"),
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

        # التحقق من إكمال اللاعب للكلمات المطلوبة
        if self.players_words[user_id] >= self.words_per_question:
            # اللاعب فاز بالجولة
            success_card = {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "🎉 أحسنت!",
                            "size": "xxl",
                            "weight": "bold",
                            "color": "#10B981",
                            "align": "center"
                        },
                        {
                            "type": "separator",
                            "margin": "lg",
                            "color": "#374151"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": display_name,
                                    "size": "xl",
                                    "weight": "bold",
                                    "color": "#F3F4F6",
                                    "align": "center"
                                },
                                {
                                    "type": "text",
                                    "text": f"+{points} نقطة",
                                    "size": "lg",
                                    "color": "#A78BFA",
                                    "align": "center",
                                    "margin": "sm"
                                }
                            ],
                            "backgroundColor": "#1F2937",
                            "cornerRadius": "12px",
                            "paddingAll": "20px",
                            "margin": "lg"
                        }
                    ],
                    "backgroundColor": "#0F172A",
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
            # اللاعب لم يكمل بعد
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
                            "color": "#10B981",
                            "align": "center"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": display_name,
                                    "size": "md",
                                    "color": "#F3F4F6",
                                    "align": "center"
                                },
                                {
                                    "type": "text",
                                    "text": f"+{points} نقطة",
                                    "size": "sm",
                                    "color": "#A78BFA",
                                    "align": "center",
                                    "margin": "xs"
                                }
                            ],
                            "margin": "md"
                        },
                        {
                            "type": "separator",
                            "margin": "lg",
                            "color": "#374151"
                        },
                        {
                            "type": "text",
                            "text": f"متبقي {remaining} كلمة",
                            "size": "sm",
                            "color": "#9CA3AF",
                            "align": "center",
                            "margin": "lg"
                        }
                    ],
                    "backgroundColor": "#0F172A",
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
