# ============================================
# games/game_fast.py - لعبة أسرع
# ============================================

"""
لعبة أسرع
=========
أول من يكتب الكلمة أو الدعاء الصحيح يفوز
لا تدعم التلميح أو إظهار الإجابة
"""

import random
from .base import BaseGame
from rules import POINTS, GAMES_INFO
from utils import validate_answer, normalize_text


class FastTypingGame(BaseGame):
    """لعبة أسرع - اكتب الكلمة بسرعة"""
    
    def __init__(self):
        game_info = GAMES_INFO['اسرع']
        super().__init__(
            name=game_info['name'],
            rounds=game_info['rounds'],
            supports_hint=game_info['supports_hint']
        )
        
        # قائمة الكلمات والأدعية
        self.words_list = [
            # كلمات بسيطة
            "سبحان الله",
            "الحمد لله",
            "لا إله إلا الله",
            "الله أكبر",
            "استغفر الله",
            "بسم الله",
            "ما شاء الله",
            "لا حول ولا قوة إلا بالله",
            
            # أدعية قصيرة
            "اللهم صل على محمد",
            "ربنا آتنا في الدنيا حسنة",
            "اللهم إني أسألك العافية",
            "حسبنا الله ونعم الوكيل",
            
            # كلمات عربية
            "مرحبا",
            "شكرا",
            "السلام عليكم",
            "وعليكم السلام",
            "صباح الخير",
            "مساء الخير",
            "تصبح على خير",
            "كيف حالك",
            "بارك الله فيك",
            "جزاك الله خيرا"
        ]
        
        # قائمة التحديات (كلمات صعبة)
        self.challenges = [
            "الاستقلال",
            "المسؤولية",
            "الديموقراطية",
            "الاستثمار",
            "البرمجية",
            "الخوارزمية",
            "المعلوماتية",
            "الإلكترونية"
        ]
    
    def generate_question(self):
        """
        توليد سؤال جديد
        
        Returns:
            نص السؤال
        """
        # اختيار عشوائي بين كلمة عادية أو تحدي
        if random.random() < 0.7:  # 70% كلمات عادية
            word = random.choice(self.words_list)
            question = f"اكتب: {word}"
        else:  # 30% تحديات
            word = random.choice(self.challenges)
            question = f"تحدي - اكتب بسرعة: {word}"
        
        # حفظ الإجابة الصحيحة
        self.current_answer = word
        
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
        # تطبيع النصوص
        user_answer = normalize_text(answer)
        correct_answer = normalize_text(self.current_answer)
        
        # التحقق من التطابق
        is_correct = user_answer.lower() == correct_answer.lower()
        
        # حساب النقاط
        points_earned = 0
        if is_correct:
            points_earned = POINTS['correct']
            self.update_score(user_id, points_earned)
        
        # الانتقال للسؤال التالي
        game_continues = self.next_question()
        
        result = {
            'correct': is_correct,
            'correct_answer': self.current_answer,
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
        لا تدعم التلميح
        
        Returns:
            None
        """
        return None
    
    def show_answer(self):
        """
        لا تدعم إظهار الإجابة
        
        Returns:
            None
        """
        return None
