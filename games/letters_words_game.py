import random
import re
from linebot.models import TextSendMessage

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
        self.hint_used = False
        self.words_per_question = 3  # 3 كلمات لكل سؤال
        self.current_round_words = {}  # تتبع كلمات كل لاعب

        # مجموعات الحروف (6 أحرف لكل مجموعة)
        self.letter_sets = [
            {"letters": "س م ا ء ن ج", "words": ["سماء", "سما", "نجم", "ماء", "جم", "نام", "سام"]},
            {"letters": "ب ي ت ك م ل", "letters": "ب ي ت ك م ل", "words": ["بيت", "ملك", "كمل", "بتل", "تيك", "يتم", "لبك"]},
            {"letters": "ق ل م د ر س", "words": ["قلم", "درس", "مدر", "سرد", "قدم", "سلم", "رمد"]},
            {"letters": "ش ج ر ة و ر", "words": ["شجر", "جور", "وجر", "شور", "رجو", "جرة", "ورة"]},
            {"letters": "ح ب ر ط ع م", "words": ["حبر", "حرب", "طعم", "عرب", "برع", "حرم", "ربع"]},
            {"letters": "ط ع ا م ش ر", "words": ["طعام", "شرط", "معط", "شرع", "طرش", "عرش", "مطر"]},
            {"letters": "ن ج م س م ا", "words": ["نجم", "سما", "ماس", "جسم", "نام", "جما", "سام"]},
            {"letters": "م ك ت ب ق ل", "words": ["مكتب", "كتب", "قلب", "ملك", "بتل", "تكم", "بقل"]},
            {"letters": "س ر ي ر ب ا", "words": ["سرير", "بيرس", "ريس", "سير", "بار", "رسي", "بري"]},
            {"letters": "ق م ر ل ي ل", "words": ["قمر", "ليل", "مرق", "ملي", "قيل", "ريم", "يمر"]}
        ]

    def normalize_text(self, text):
        """تطبيع النص لقبول جميع أشكال الحروف"""
        if not text:
            return ""
        text = text.strip().lower()
        # إزالة "ال" التعريف
        text = re.sub(r'^ال', '', text)
        # تطبيع الحروف
        text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
        text = text.replace('ؤ', 'و').replace('ئ', 'ي').replace('ء', '')
        text = text.replace('ة', 'ه').replace('ى', 'ي')
        # إزالة التشكيل
        text = re.sub(r'[\u064B-\u065F]', '', text)
        text = re.sub(r'\s+', '', text)
        return text

    def start_game(self):
        """بدء اللعبة"""
        self.current_question = 1
        self.players_scores = {}
        self.current_round_words = {}
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
        self.current_round_words = {}

        letters_str = ' '.join(self.available_letters)
        return TextSendMessage(
            text=f"▪️ لعبة تكوين الكلمات\n\nسؤال {self.current_question} من {self.max_questions}\n\nكوّن {self.words_per_question} كلمات من هذه الحروف:\n\n{letters_str}\n\nاكتب كلمة واحدة في كل رسالة"
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
        # عرض مثال لكلمة صحيحة
        example_word = list(self.valid_words_set)[0] if self.valid_words_set else ""
        hint = f"▪️ تلميح\n\nحاول تكوين كلمات من 2-4 أحرف\nمثال: {example_word}"
        
        return {
            'response': TextSendMessage(text=hint),
            'points': -1,
            'correct': False,
            'won': False,
            'game_over': False
        }

    def show_answer(self):
        """عرض الإجابة والانتقال للسؤال التالي"""
        # عرض بعض الكلمات الصحيحة
        suggestions = list(self.valid_words_set)[:3]
        msg = f"▪️ كلمات صحيحة:\n\n{', '.join(suggestions)}"

        self.current_question += 1
        
        if self.current_question <= self.max_questions:
            # الانتقال للسؤال التالي
            return {
                'response': TextSendMessage(text=msg),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': False,
                'next_question': True
            }
        else:
            # نهاية اللعبة
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

        # ترتيب اللاعبين
        sorted_players = sorted(
            self.players_scores.items(), 
            key=lambda x: x[1]['score'], 
            reverse=True
        )
        
        winner = sorted_players[0]
        all_scores = [(data['name'], data['score']) for name, data in sorted_players]

        # استخدام بطاقة الفائز من app.py
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
        # معالجة أوامر خاصة
        answer_lower = answer.strip().lower()
        
        if answer_lower in ['لمح', 'تلميح', 'hint']:
            return self.get_hint()
        
        if answer_lower in ['جاوب', 'الجواب', 'الحل', 'answer']:
            return self.show_answer()

        # تطبيع الكلمة
        answer_word = self.normalize_text(answer)

        # التحقق من أن الكلمة لم تُستخدم من قبل
        if answer_word in self.used_words:
            return {
                'response': TextSendMessage(text=f"▫️ الكلمة '{answer}' مستخدمة مسبقاً"),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': False
            }

        # التحقق من إمكانية تكوين الكلمة من الحروف المتاحة
        letters_no_spaces = [l for l in self.available_letters]
        if not self.can_form_word(answer_word, letters_no_spaces):
            letters_str = ' '.join(self.available_letters)
            return {
                'response': TextSendMessage(
                    text=f"▫️ لا يمكن تكوين '{answer}' من الحروف المتاحة\n\nالحروف: {letters_str}"
                ),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': False
            }

        # التحقق من أن الكلمة طولها مناسب
        if len(answer_word) < 2:
            return {
                'response': TextSendMessage(text="▫️ الكلمة يجب أن تكون حرفين على الأقل"),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': False
            }

        # التحقق من أن الكلمة صحيحة
        normalized_valid = {self.normalize_text(w) for w in self.valid_words_set}
        if answer_word not in normalized_valid:
            return {
                'response': TextSendMessage(text=f"▫️ '{answer}' ليست كلمة صحيحة"),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': False
            }

        # الكلمة صحيحة - احتساب النقاط
        self.used_words.add(answer_word)
        
        # تتبع عدد كلمات هذا اللاعب في هذه الجولة
        if user_id not in self.current_round_words:
            self.current_round_words[user_id] = 0
        self.current_round_words[user_id] += 1

        # حساب النقاط
        points = 2 if not self.hint_used else 1

        # تحديث النقاط الإجمالية
        if user_id not in self.players_scores:
            self.players_scores[user_id] = {'name': display_name, 'score': 0}
        self.players_scores[user_id]['score'] += points

        # التحقق من اكتمال عدد الكلمات المطلوبة لهذا اللاعب
        if self.current_round_words[user_id] >= self.words_per_question:
            # اللاعب أكمل الكلمات المطلوبة
            msg = f"▪️ أحسنت {display_name}\n\n+{points} نقطة"
            
            self.current_question += 1
            
            if self.current_question <= self.max_questions:
                # الانتقال للسؤال التالي
                return {
                    'response': TextSendMessage(text=msg),
                    'points': points,
                    'correct': True,
                    'won': True,
                    'game_over': False,
                    'next_question': True
                }
            else:
                # نهاية اللعبة
                return self._end_game()
        else:
            # اللاعب لم يكمل بعد
            remaining = self.words_per_question - self.current_round_words[user_id]
            letters_str = ' '.join(self.available_letters)
            msg = f"▪️ صحيح {display_name}\n\n+{points} نقطة\n\nكلمة أخرى ({remaining} متبقية)\n\n{letters_str}"
            
            return {
                'response': TextSendMessage(text=msg),
                'points': points,
                'correct': True,
                'won': False,
                'game_over': False
            }
