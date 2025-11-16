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
        self.players_words = {}
        self.hint_used = False
        self.words_per_question = 3

        # ✅ مجموعات حروف منطقية (6 حروف) - كلمات حقيقية فقط
        self.letter_sets = [
            {
                "letters": "ق م ر ي ل ن",
                "words": [
                    "قمر",      # القمر
                    "ليل",      # الليل
                    "مرق",      # مرق الطبخ
                    "ريم",      # اسم / الغزال
                    "نيل",      # نهر النيل
                    "قرن",      # القرن
                    "ملي",      # يملي
                    "مير",      # أمير
                    "قيل",      # قيل وقال
                    "ليم",      # الليم (الليمون)
                    "نمر",      # النمر
                    "مرن",      # مرونة
                ]
            },
            {
                "letters": "ن ج م س و ر",
                "words": [
                    "نجم",      # النجم
                    "نجوم",     # النجوم
                    "سور",      # السور
                    "نور",      # النور
                    "سمر",      # السمر / السهرة
                    "رسم",      # الرسم
                    "جور",      # الظلم
                    "نمر",      # النمر
                    "جرس",      # الجرس
                    "سجن",      # السجن
                    "مرج",      # المرج
                    "رسوم",     # الرسوم
                    "سمور",     # حيوان السمور
                    "نسور",     # النسور
                ]
            },
            {
                "letters": "ب ح ر ي ن ل",
                "words": [
                    "بحر",      # البحر
                    "بحرين",    # دولة البحرين
                    "بحري",     # بحري
                    "حرب",      # الحرب
                    "نحل",      # النحل
                    "نيل",      # نهر النيل
                    "لبن",      # اللبن
                    "حبل",      # الحبل
                    "نبيل",     # اسم نبيل
                    "نبل",      # النبل
                    "ربح",      # الربح
                    "بين",      # بين
                    "حين",      # الحين
                ]
            },
            {
                "letters": "ك ت ب م ل و",
                "words": [
                    "كتب",      # الكتب
                    "كتاب",     # الكتاب (ينقص حرف أ لكن كتب موجود)
                    "مكتب",     # المكتب
                    "ملك",      # الملك
                    "كمل",      # اكتمل
                    "كلم",      # الكلام
                    "بلوت",     # لعبة البلوت
                    "موت",      # الموت
                    "كوم",      # الكومة
                    "ملت",      # ملل
                    "بكت",      # البكاء
                    "تكلم",     # يتكلم
                ]
            },
            {
                "letters": "ش ج ر ة ي ن",
                "words": [
                    "شجر",      # الشجر
                    "شجرة",     # الشجرة
                    "جرة",      # جرة الماء
                    "نشر",      # النشر
                    "شرن",      # الشرنقة (ناقص حرف لكن شرن ممكن)
                    "تين",      # التين
                    "جنة",      # الجنة
                    "جين",      # الجينات
                    "رجة",      # الرجة
                    "شين",      # حرف الشين
                    "شجن",      # الشجن (الحزن)
                    "جشن",      # الجشن (الاحتفال التركي)
                ]
            },
            {
                "letters": "س م ك ن ا ه",
                "words": [
                    "سمك",      # السمك
                    "سكن",      # السكن
                    "سماء",     # السماء (ناقص حرف لكن سما موجود)
                    "سما",      # السماء
                    "ماء",      # الماء
                    "سمان",     # طائر السمان
                    "نام",      # نام
                    "سام",      # سام
                    "هام",      # مهم
                    "سهم",      # السهم
                    "اسم",      # الاسم
                    "امن",      # الأمن
                    "نهم",      # النهم
                    "مهن",      # المهن
                ]
            },
            {
                "letters": "ع ي ن ر ب د",
                "words": [
                    "عين",      # العين
                    "عربي",     # عربي
                    "عرب",      # العرب
                    "برد",      # البرد
                    "عبد",      # عبد
                    "بعد",      # بعد
                    "دين",      # الدين
                    "عيد",      # العيد
                    "برع",      # يبرع
                    "عبر",      # العبور
                    "رعد",      # الرعد
                    "عرين",     # عرين الأسد
                    "بعير",     # البعير
                ]
            },
            {
                "letters": "د ر س م ح ل",
                "words": [
                    "درس",      # الدرس
                    "مدرس",     # المدرس
                    "رسم",      # الرسم
                    "حلم",      # الحلم
                    "سلم",      # السلام
                    "حرم",      # الحرم
                    "حرس",      # الحرس
                    "سحر",      # السحر
                    "حمل",      # الحمل
                    "رحم",      # الرحمة
                    "حسد",      # الحسد
                    "ملح",      # الملح
                    "رمح",      # الرمح
                ]
            },
            {
                "letters": "ط ل ع م و ب",
                "words": [
                    "طلع",      # طلع
                    "علم",      # العلم
                    "طعم",      # الطعم
                    "عمل",      # العمل
                    "طمع",      # الطمع
                    "بطل",      # البطل
                    "طول",      # الطول
                    "علب",      # العلب
                    "موعد",     # الموعد (ناقص د لكن موع ممكن)
                    "معلم",     # المعلم
                    "طبع",      # الطبع
                    "بعل",      # بعل
                ]
            },
            {
                "letters": "ح ب ر ط ي ق",
                "words": [
                    "حبر",      # الحبر
                    "حرب",      # الحرب
                    "طرب",      # الطرب
                    "طريق",     # الطريق
                    "قرب",      # القرب
                    "طيب",      # الطيب
                    "قطر",      # قطر
                    "حرق",      # الحرق
                    "بحر",      # البحر (ناقص لكن ممكن)
                    "قبر",      # القبر
                    "حقب",      # الحقبة
                    "ربح",      # الربح
                ]
            },
            {
                "letters": "ف ك ر ت ي ن",
                "words": [
                    "فكر",      # الفكر
                    "فكري",     # فكري
                    "تفكير",    # التفكير (ناقص حرف لكن فكر موجود)
                    "ركن",      # الركن
                    "تين",      # التين
                    "فني",      # فني
                    "كفر",      # الكفر
                    "نير",      # النير
                    "فرن",      # الفرن
                    "فتن",      # الفتنة
                    "ترف",      # الترف
                    "كفن",      # الكفن
                ]
            },
            {
                "letters": "ص و ر ة ح ب",
                "words": [
                    "صورة",     # الصورة
                    "صور",      # الصور
                    "بحر",      # البحر
                    "حرب",      # الحرب
                    "صبر",      # الصبر
                    "حبر",      # الحبر
                    "وحش",      # الوحش (ناقص ش)
                    "بحة",      # البحة
                    "حصر",      # الحصر
                    "روح",      # الروح
                    "صحة",      # الصحة
                    "حوض",      # الحوض (ناقص ض)
                ]
            },
            {
                "letters": "ج س م ا ل ن",
                "words": [
                    "جسم",      # الجسم
                    "جمال",     # الجمال
                    "سلام",     # السلام
                    "مجلس",     # المجلس
                    "جمل",      # الجمل
                    "سام",      # سام
                    "نام",      # نام
                    "مال",      # المال
                    "جان",      # الجان
                    "لسان",     # اللسان
                    "سلم",      # السلم
                    "ماس",      # الماس
                ]
            },
            {
                "letters": "خ ل ق ا ن ي",
                "words": [
                    "خلق",      # الخلق
                    "خالق",     # الخالق
                    "اخلاق",    # الأخلاق
                    "خال",      # الخال
                    "خيل",      # الخيل
                    "لقي",      # لقي
                    "نقي",      # نقي
                    "خان",      # الخان
                    "نخيل",     # النخيل
                    "قلي",      # القلي
                    "خيال",     # الخيال
                ]
            },
            {
                "letters": "ذ ه ب و ن ي",
                "words": [
                    "ذهب",      # الذهب
                    "ذهبي",     # ذهبي
                    "نبي",      # النبي
                    "بون",      # البون
                    "ذوب",      # الذوبان
                    "وهن",      # الوهن
                    "نهب",      # النهب
                    "ذنب",      # الذنب
                    "بيون",     # البيون (ناقص لكن ممكن)
                    "هون",      # الهون
                ]
            },
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
        
        # تقسيم الحروف إلى صفين (3 × 3)
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
        
        # إضافة الأزرار
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

        letter_set = random.choice(self.letter_sets)
        self.available_letters = letter_set['letters'].split()
        self.valid_words_set = set(letter_set['words'])
        
        random.shuffle(self.available_letters)
        self.used_words.clear()
        self.hint_used = False
        self.players_words = {}

        letters_str = ' '.join(self.available_letters)
        
        flex_card = self.get_neumorphism_card(
            title="▪️ لعبة تكوين الكلمات",
            question_num=self.current_question,
            letters_str=letters_str,
            instruction=f"كوّن {self.words_per_question} كلمات صحيحة من الحروف\nأول لاعب يكمل يفوز!"
        )
        
        return FlexSendMessage(
            alt_text=f"سؤال {self.current_question} - تكوين كلمات",
            contents=flex_card
        )

    def get_hint(self):
        """الحصول على تلميح - يعرض أول حرف وعدد الحروف"""
        if self.hint_used:
            return {
                'response': TextSendMessage(text="▫️ تم استخدام التلميح مسبقاً"),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': False
            }
        
        self.hint_used = True
        # اختيار كلمة عشوائية من الكلمات المتاحة
        example_word = random.choice(list(self.valid_words_set)) if self.valid_words_set else ""
        
        # الحصول على أول حرف
        first_letter = example_word[0] if example_word else ""
        word_length = len(example_word)
        
        # إنشاء نمط الكلمة: أول حرف + _ _ _
        hint_pattern = first_letter + " " + " ".join(["_"] * (word_length - 1))
        
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
                                "text": "أول حرف من الكلمة:",
                                "size": "sm",
                                "color": "#9CA3AF",
                                "margin": "lg",
                                "align": "center"
                            },
                            {
                                "type": "text",
                                "text": hint_pattern,
                                "size": "xxl",
                                "weight": "bold",
                                "color": "#A78BFA",
                                "align": "center",
                                "margin": "md",
                                "spacing": "lg"
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "عدد الحروف:",
                                        "size": "xs",
                                        "color": "#6B7280",
                                        "flex": 0
                                    },
                                    {
                                        "type": "text",
                                        "text": str(word_length),
                                        "size": "sm",
                                        "color": "#10B981",
                                        "weight": "bold",
                                        "flex": 0,
                                        "margin": "md"
                                    }
                                ],
                                "margin": "lg",
                                "justifyContent": "center"
                            }
                        ],
                        "backgroundColor": "#1F2937",
                        "cornerRadius": "12px",
                        "paddingAll": "16px"
                    },
                    {
                        "type": "text",
                        "text": "⚠️ النقاط ستنخفض إلى نصف القيمة",
                        "size": "xxs",
                        "color": "#F59E0B",
                        "align": "center",
                        "margin": "lg"
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
        suggestions = sorted(self.valid_words_set, key=len, reverse=True)[:4]
        
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
                                "text": " ، ".join(suggestions),
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

        if answer_word in self.used_words:
            return {
                'response': TextSendMessage(text=f"▫️ الكلمة '{answer}' مستخدمة مسبقاً"),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': False
            }

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

        # ✅ التحقق من أن الكلمة موجودة في قائمة الكلمات الصحيحة
        normalized_valid = {self.normalize_text(w) for w in self.valid_words_set}
        if answer_word not in normalized_valid:
            return {
                'response': TextSendMessage(text=f"▫️ '{answer}' ليست من الكلمات المطلوبة\n\nحاول كلمة أخرى من نفس الحروف"),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': False
            }
