# ============================================
# games/game_opposite.py - لعبة ضد
# ============================================

"""
لعبة ضد
========
إيجاد عكس الكلمة المعطاة
تدعم التلميح وإظهار الإجابة
"""

import random
from .base import BaseGame
from rules import POINTS, GAMES_INFO
from utils import normalize_text


class OppositeGame(BaseGame):
    """لعبة إيجاد عكس الكلمة"""
    
    def __init__(self):
        game_info = GAMES_INFO['ضد']
        super().__init__(
            name=game_info['name'],
            rounds=game_info['rounds'],
            supports_hint=game_info['supports_hint']
        )
        
        # قاعدة بيانات الكلمات وأضدادها
        self.opposites = {
            'كبير': 'صغير',
            'طويل': 'قصير',
            'سريع': 'بطيء',
            'حار': 'بارد',
            'نظيف': 'وسخ',
            'قوي': 'ضعيف',
            'غني': 'فقير',
            'سعيد': 'حزين',
            'جميل': 'قبيح',
            'صعب': 'سهل',
            'ثقيل': 'خفيف',
            'مظلم': 'مضيء',
            'عالي': 'منخفض',
            'واسع': 'ضيق',
            'جديد': 'قديم',
            'نهار': 'ليل',
            'شمس': 'قمر',
            'أبيض': 'أسود',
            'فوق': 'تحت',
            'داخل': 'خارج',
            'قريب': 'بعيد',
            'يمين': 'يسار',
            'أمام': 'خلف',
            'شرق': 'غرب',
            'شمال': 'جنوب',
            'حي': 'ميت',
            'صحيح': 'خاطئ',
            'موجود': 'معدوم',
            'ممكن': 'مستحيل',
            'مفيد': 'ضار',
            'محبوب': 'مكروه',
            'جاف': 'رطب',
            'ناعم': 'خشن',
            'صلب': 'لين',
            'مفتوح': 'مغلق',
            'واضح': 'غامض',
            'بداية': 'نهاية',
            'دخول': 'خروج',
            'صعود': 'هبوط',
            'ربح': 'خسارة',
            'نجاح': 'فشل',
            'صدق': 'كذب',
            'أمانة': 'خيانة',
            'عدل': 'ظلم',
            'سلام': 'حرب',
            'محبة': 'كراهية',
            'شجاعة': 'جبن',
            'كرم': 'بخل',
            'علم': 'جهل',
            'نور': 'ظلام',
            'حياة': 'موت'
        }
        
        self.current_word = None
    
    def generate_question(self):
        """
        توليد سؤال جديد
        
        Returns:
            نص السؤال
        """
        # اختيار كلمة عشوائية
        self.current_word = random.choice(list(self.opposites.keys()))
        
        # حفظ الإجابة (الضد)
        self.current_answer = self.opposites[self.current_word]
        
        # إنشاء السؤال
        question = f'ما هو ضد كلمة: {self.current_word}؟'
        
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
        user_answer = normalize_text(answer).lower()
        correct_answer = normalize_text(self.current_answer).lower()
        
        # التحقق من التطابق
        is_correct = user_answer == correct_answer
        
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
            'original_word': self.current_word,
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
        
        answer = self.current_answer
        
        # تلميح: الحرف الأول وعدد الأحرف
        first_letter = answer[0]
        length = len(answer)
        hint_word = first_letter + ('_' * (length - 1))
        
        hint = f"التلميح: {hint_word} ({length} أحرف)"
        
        return hint
    
    def show_answer(self):
        """
        إظهار الإجابة الصحيحة
        
        Returns:
            الإجابة
        """
        return f'ضد {self.current_word} هو: {self.current_answer}'
