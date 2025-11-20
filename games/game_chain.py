# ============================================
# games/game_chain.py - لعبة سلسلة الكلمات
# ============================================

"""
لعبة سلسلة الكلمات
==================
كلمة تبدأ بالحرف الأخير من الكلمة السابقة
تدعم التلميح وإظهار الإجابة
"""

import random
from .base import BaseGame
from rules import POINTS, GAMES_INFO
from utils import normalize_text, is_arabic


class ChainWordsGame(BaseGame):
    """لعبة سلسلة الكلمات"""
    
    def __init__(self):
        game_info = GAMES_INFO['سلسلة']
        super().__init__(
            name=game_info['name'],
            rounds=game_info['rounds'],
            supports_hint=game_info['supports_hint']
        )
        
        # قاموس الكلمات حسب الحرف الأول
        self.words_dict = {
            'ا': ['أسد', 'أرنب', 'أحمد', 'أمل', 'إبراهيم', 'إيمان'],
            'ب': ['بحر', 'بدر', 'باب', 'بيت', 'برتقال', 'بطل'],
            'ت': ['تفاح', 'تمر', 'تميم', 'تالا', 'تربية', 'تعليم'],
            'ث': ['ثلج', 'ثمر', 'ثابت', 'ثروة', 'ثقافة'],
            'ج': ['جمل', 'جبل', 'جمال', 'جنة', 'جودة', 'جميل'],
            'ح': ['حصان', 'حب', 'حسن', 'حنان', 'حرية', 'حياة'],
            'خ': ['خروف', 'خيار', 'خالد', 'خديجة', 'خير', 'خلود'],
            'د': ['دب', 'دار', 'داود', 'دانا', 'دواء', 'دين'],
            'ذ': ['ذهب', 'ذئب', 'ذكاء', 'ذكر', 'ذكرى'],
            'ر': ['رمان', 'رمل', 'رامي', 'رنا', 'رحمة', 'رزق'],
            'ز': ['زهرة', 'زيت', 'زياد', 'زينب', 'زمن', 'زكاة'],
            'س': ['سمك', 'سماء', 'سالم', 'سارة', 'سلام', 'سعادة'],
            'ش': ['شمس', 'شجر', 'شادي', 'شذى', 'شكر', 'شهامة'],
            'ص': ['صقر', 'صخر', 'صالح', 'صفاء', 'صبر', 'صدق'],
            'ض': ['ضوء', 'ضفدع', 'ضياء', 'ضحى', 'ضيف'],
            'ط': ['طائر', 'طعام', 'طارق', 'طيبة', 'طموح', 'طاعة'],
            'ظ': ['ظبي', 'ظل', 'ظافر', 'ظريف'],
            'ع': ['عصفور', 'علم', 'عادل', 'عائشة', 'عز', 'علو'],
            'غ': ['غزال', 'غصن', 'غازي', 'غادة', 'غيث', 'غفران'],
            'ف': ['فيل', 'فرح', 'فادي', 'فاطمة', 'فضل', 'فلاح'],
            'ق': ['قط', 'قمر', 'قاسم', 'قمرة', 'قوة', 'قلب'],
            'ك': ['كلب', 'كتاب', 'كريم', 'كوثر', 'كرم', 'كمال'],
            'ل': ['ليث', 'لبن', 'لؤي', 'لينا', 'لطف', 'لقاء'],
            'م': ['ماء', 'محمد', 'مريم', 'مجد', 'محبة', 'منى'],
            'ن': ['نمر', 'نور', 'ناصر', 'نجلاء', 'نجاح', 'نعمة'],
            'ه': ['هدهد', 'هواء', 'هاني', 'هند', 'همة', 'هدوء'],
            'و': ['ورد', 'وطن', 'وليد', 'وفاء', 'ود', 'وعد'],
            'ي': ['يمام', 'ياسر', 'ياسمين', 'يقين', 'يسر', 'يمن']
        }
        
        self.previous_word = None
        self.last_letter = None
        self.possible_answers = []
    
    def generate_question(self):
        """
        توليد سؤال جديد
        
        Returns:
            نص السؤال
        """
        if self.current_round == 1:
            # السؤال الأول: كلمة عشوائية
            letters = list(self.words_dict.keys())
            start_letter = random.choice(letters)
            self.previous_word = random.choice(self.words_dict[start_letter])
        else:
            # الأسئلة التالية: استخدام آخر حرف
            if self.current_answer and isinstance(self.current_answer, list):
                self.previous_word = random.choice(self.current_answer)
        
        # الحصول على آخر حرف
        self.last_letter = self.previous_word[-1]
        
        # إزالة التشكيل والحركات
        clean_letter = normalize_text(self.last_letter)[0] if self.last_letter else 'ا'
        
        # الحصول على الكلمات الممكنة
        self.possible_answers = self.words_dict.get(clean_letter, [])
        
        if not self.possible_answers:
            # إذا لم توجد كلمات، استخدم حرف آخر
            clean_letter = random.choice(list(self.words_dict.keys()))
            self.possible_answers = self.words_dict[clean_letter]
        
        self.current_answer = self.possible_answers
        
        question = f"الكلمة السابقة: {self.previous_word}\nاكتب كلمة تبدأ بحرف: {clean_letter}"
        
        return question
    
    def check_answer(self, user_id, answer):
        """
        التحقق من الإجابة
        
        Args:
            user_id: معرف المستخدم
            answer: إجابة المستخدم
            
        Returns:
            dict مع النتيجة
        """
        user_answer = normalize_text(answer)
        
        # التحقق من أن الإجابة عربية
        if not is_arabic(user_answer):
            is_correct = False
        else:
            # التحقق من أن الكلمة تبدأ بالحرف الصحيح
            first_letter = user_answer[0] if user_answer else ''
            expected_letter = self.last_letter if self.last_letter else ''
            expected_letter = normalize_text(expected_letter)[0] if expected_letter else ''
            
            # قبول الإجابة إذا كانت تبدأ بالحرف الصحيح أو موجودة في القائمة
            is_correct = (first_letter == expected_letter) or \
                         any(user_answer.lower() == normalize_text(word).lower() 
                             for word in self.possible_answers)
        
        # حساب النقاط
        points_earned = 0
        if is_correct:
            points_earned = POINTS['correct']
            self.update_score(user_id, points_earned)
        
        # الانتقال للسؤال التالي
        game_continues = self.next_question()
        
        result = {
            'correct': is_correct,
            'correct_answer': self.possible_answers[0] if self.possible_answers else 'غير متوفر',
            'all_answers': self.possible_answers[:3],  # أول 3 إجابات
            'points_earned': points_earned,
            'total_points': self.get_score(user_id),
            'current_round': self.current_round,
            'total_rounds': self.total_rounds,
            'game_ended': not game_continues,
            'next_question': self.current_question if game_continues else None
        }
        
        return result
    
    def get_hint(self):
        """
        الحصول على تلميح
        
        Returns:
            التلميح
        """
        if not self.possible_answers:
            return "لا يوجد تلميح متاح"
        
        answer = self.possible_answers[0]
        hint_length = max(1, len(answer) // 2)
        
        hint = answer[:hint_length] + ('_' * (len(answer) - hint_length))
        return f"التلميح: {hint}"
    
    def show_answer(self):
        """
        إظهار الإجابة الصحيحة
        
        Returns:
            الإجابة
        """
        if self.possible_answers:
            return f"{self.possible_answers[0]} (أمثلة أخرى: {', '.join(self.possible_answers[1:3])})"
        return "لا توجد إجابة"
