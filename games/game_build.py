# ============================================
# games/game_build.py - لعبة تكوين الكلمات
# ============================================

"""
لعبة تكوين الكلمات
==================
تكوين 3 كلمات من 6 حروف معطاة
تدعم التلميح وإظهار الإجابة
"""

import random
from .base import BaseGame
from rules import POINTS, GAMES_INFO
from utils import normalize_text


class LettersWordsGame(BaseGame):
    """لعبة تكوين كلمات من حروف"""
    
    def __init__(self):
        game_info = GAMES_INFO['تكوين']
        super().__init__(
            name=game_info['name'],
            rounds=game_info['rounds'],
            supports_hint=game_info['supports_hint']
        )
        
        # قاعدة بيانات التحديات
        self.challenges = [
            {
                'letters': 'ب ر م ح د ل',
                'words': ['برد', 'حمل', 'مدح']
            },
            {
                'letters': 'س ر ف ح ن م',
                'words': ['سحر', 'فرح', 'نصر']
            },
            {
                'letters': 'ج ل م ر س ن',
                'words': ['جمل', 'رسم', 'نجم']
            },
            {
                'letters': 'ك ت ب ل م ي',
                'words': ['كتب', 'ليل', 'يمل']
            },
            {
                'letters': 'ق ل ب ح ر ن',
                'words': ['قلب', 'بحر', 'نحل']
            },
            {
                'letters': 'ع ل م س ي ر',
                'words': ['علم', 'سير', 'يسر']
            },
            {
                'letters': 'ن و ر ح ب م',
                'words': ['نور', 'حب', 'رمح']
            },
            {
                'letters': 'ص خ ر د ق ل',
                'words': ['صخر', 'قدر', 'خلد']
            },
            {
                'letters': 'ط ر ح ل ب س',
                'words': ['طرح', 'لبس', 'حرب']
            },
            {
                'letters': 'ف ج ر س ل م',
                'words': ['فجر', 'سلم', 'رجل']
            },
            {
                'letters': 'ش م س ر ق ن',
                'words': ['شمس', 'رقص', 'نشر']
            },
            {
                'letters': 'ذ ه ب ر ك م',
                'words': ['ذهب', 'ركب', 'مذهب']
            },
            {
                'letters': 'غ ي ر ب د ل',
                'words': ['غير', 'بدل', 'لغة']
            },
            {
                'letters': 'ظ ل م ن ف ر',
                'words': ['ظلم', 'نفر', 'رمل']
            },
            {
                'letters': 'ث و ب ر م ن',
                'words': ['ثوب', 'رمن', 'بنت']
            }
        ]
        
        self.current_challenge = None
        self.expected_words_count = 3
        self.found_words = []
    
    def generate_question(self):
        """
        توليد سؤال جديد
        
        Returns:
            نص السؤال
        """
        # اختيار تحدي عشوائي
        self.current_challenge = random.choice(self.challenges)
        self.found_words = []
        
        # حفظ الكلمات المطلوبة
        self.current_answer = self.current_challenge['words']
        
        # إنشاء السؤال
        question = f"كون {self.expected_words_count} كلمات من الحروف التالية:\n"
        question += self.current_challenge['letters']
        question += "\n\nأجب بالكلمات مفصولة بفواصل"
        
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
        # تنظيف وتقسيم إجابة المستخدم
        user_words = [normalize_text(word.strip()).lower() 
                      for word in answer.split(',') if word.strip()]
        
        # تنظيف الكلمات المطلوبة
        required_words = [normalize_text(word).lower() 
                         for word in self.current_answer]
        
        # حساب عدد الكلمات الصحيحة
        correct_count = 0
        for word in user_words:
            if word in required_words and word not in self.found_words:
                self.found_words.append(word)
                correct_count += 1
        
        # التحقق من الإجابة الكاملة
        is_correct = len(self.found_words) >= self.expected_words_count
        
        # حساب النقاط
        points_earned = 0
        if is_correct:
            points_earned = POINTS['correct']
            self.update_score(user_id, points_earned)
        
        # الانتقال للسؤال التالي
        game_continues = self.next_question()
        
        result = {
            'correct': is_correct,
            'correct_answer': ', '.join(self.current_answer),
            'found_words': ', '.join(self.found_words) if self.found_words else 'لا يوجد',
            'correct_count': len(self.found_words),
            'required_count': self.expected_words_count,
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
        if not self.current_answer:
            return "لا يوجد تلميح متاح"
        
        # تلميح: إظهار أول كلمة بشكل جزئي
        first_word = self.current_answer[0]
        hint_length = max(1, len(first_word) // 2)
        hint_word = first_word[:hint_length] + ('_' * (len(first_word) - hint_length))
        
        hint = f"التلميح: إحدى الكلمات تبدأ بـ: {hint_word}"
        
        return hint
    
    def show_answer(self):
        """
        إظهار الإجابة الصحيحة
        
        Returns:
            الإجابة
        """
        return f'الكلمات المطلوبة: {", ".join(self.current_answer)}'
