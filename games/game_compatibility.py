# ============================================
# games/game_compatibility.py - لعبة التوافق
# ============================================

"""
لعبة التوافق
============
حساب نسبة التوافق بين اسمين
لعبة ترفيهية بدون تلميح أو إظهار إجابة
جولة واحدة فقط
"""

import random
from .base import BaseGame
from rules import POINTS, GAMES_INFO
from utils import normalize_text


class CompatibilityGame(BaseGame):
    """لعبة حساب التوافق بين الأسماء"""
    
    def __init__(self):
        game_info = GAMES_INFO['توافق']
        super().__init__(
            name=game_info['name'],
            rounds=game_info['rounds'],  # جولة واحدة فقط
            supports_hint=game_info['supports_hint']  # False
        )
        
        self.name1 = None
        self.name2 = None
        self.compatibility_percentage = 0
        self.waiting_for_names = True
    
    def generate_question(self):
        """
        توليد سؤال جديد
        
        Returns:
            نص السؤال
        """
        question = "أدخل اسمين لحساب نسبة التوافق بينهما\nمثال: محمد, فاطمة"
        
        return question
    
    def calculate_compatibility(self, name1, name2):
        """
        حساب نسبة التوافق (خوارزمية ترفيهية)
        
        Args:
            name1: الاسم الأول
            name2: الاسم الثاني
            
        Returns:
            نسبة التوافق (0-100)
        """
        # تنظيف الأسماء
        name1 = normalize_text(name1).lower()
        name2 = normalize_text(name2).lower()
        
        # خوارزمية بسيطة: حساب الأحرف المشتركة
        common_letters = set(name1) & set(name2)
        all_letters = set(name1) | set(name2)
        
        if not all_letters:
            base_percentage = 50
        else:
            base_percentage = (len(common_letters) / len(all_letters)) * 100
        
        # إضافة عامل عشوائي للتنويع (+/- 20)
        random_factor = random.randint(-20, 20)
        
        # حساب النسبة النهائية
        percentage = int(base_percentage + random_factor)
        
        # التأكد من أن النسبة بين 1 و 100
        percentage = max(1, min(100, percentage))
        
        return percentage
    
    def get_compatibility_message(self, percentage):
        """
        الحصول على رسالة حسب نسبة التوافق
        
        Args:
            percentage: نسبة التوافق
            
        Returns:
            الرسالة المناسبة
        """
        if percentage >= 90:
            return "توافق ممتاز! تكاد تكونان متطابقين"
        elif percentage >= 75:
            return "توافق عالي جداً! علاقة رائعة"
        elif percentage >= 60:
            return "توافق جيد! يمكن بناء علاقة قوية"
        elif percentage >= 45:
            return "توافق متوسط. يحتاج إلى بعض التفاهم"
        elif percentage >= 30:
            return "توافق منخفض. قد تواجهان بعض التحديات"
        else:
            return "توافق ضعيف. شخصيات مختلفة جداً"
    
    def check_answer(self, user_id, answer):
        """
        التحقق من الإجابة (معالجة الأسماء)
        
        Args:
            user_id: معرف المستخدم
            answer: الأسماء المدخلة
            
        Returns:
            dict مع النتيجة
        """
        # تقسيم الأسماء
        names = [name.strip() for name in answer.split(',')]
        
        if len(names) < 2:
            return {
                'correct': False,
                'error': 'يرجى إدخال اسمين مفصولين بفاصلة',
                'game_ended': False
            }
        
        self.name1 = names[0]
        self.name2 = names[1]
        
        # حساب نسبة التوافق
        self.compatibility_percentage = self.calculate_compatibility(
            self.name1, self.name2
        )
        
        # الحصول على الرسالة
        message = self.get_compatibility_message(self.compatibility_percentage)
        
        # تحديث النتيجة
        self.update_score(user_id, POINTS['skip'])  # نقاط صفر لأنها لعبة ترفيهية
        
        # إنهاء اللعبة (جولة واحدة فقط)
        self.is_active = False
        
        result = {
            'correct': True,
            'name1': self.name1,
            'name2': self.name2,
            'compatibility_percentage': self.compatibility_percentage,
            'message': message,
            'points_earned': 0,
            'total_points': self.get_score(user_id),
            'current_round': 1,
            'total_rounds': 1,
            'game_ended': True,
            'next_question': None
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
