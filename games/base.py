# ============================================
# games/base.py - الكلاس الأساسي للألعاب
# ============================================

"""
الكلاس الأساسي للألعاب
======================
جميع الألعاب ترث من هذا الكلاس
"""

from abc import ABC, abstractmethod
from datetime import datetime


class BaseGame(ABC):
    """الكلاس الأساسي لجميع الألعاب"""
    
    def __init__(self, name, rounds=5, supports_hint=True):
        """
        تهيئة اللعبة
        
        Args:
            name: اسم اللعبة
            rounds: عدد الجولات
            supports_hint: هل تدعم التلميح
        """
        self.name = name
        self.total_rounds = rounds
        self.current_round = 0
        self.supports_hint = supports_hint
        self.players_scores = {}
        self.current_question = None
        self.current_answer = None
        self.started_at = datetime.now()
        self.is_active = True
    
    @abstractmethod
    def generate_question(self):
        """
        توليد سؤال جديد
        يجب تنفيذها في كل لعبة
        
        Returns:
            السؤال الجديد
        """
        pass
    
    @abstractmethod
    def check_answer(self, user_id, answer):
        """
        التحقق من الإجابة
        يجب تنفيذها في كل لعبة
        
        Args:
            user_id: معرف المستخدم
            answer: الإجابة
            
        Returns:
            dict مع النتيجة
        """
        pass
    
    def get_current_question(self):
        """
        الحصول على السؤال الحالي أو توليد جديد
        
        Returns:
            السؤال الحالي
        """
        if not self.current_question or self.current_round == 0:
            self.next_question()
        
        return self.current_question
    
    def next_question(self):
        """الانتقال للسؤال التالي"""
        if self.current_round < self.total_rounds:
            self.current_round += 1
            self.current_question = self.generate_question()
            return True
        else:
            self.is_active = False
            return False
    
    def get_hint(self):
        """
        الحصول على تلميح
        يمكن تخصيصها في كل لعبة
        
        Returns:
            التلميح أو None
        """
        if not self.supports_hint or not self.current_answer:
            return None
        
        # تلميح افتراضي: إظهار بعض الأحرف
        answer = str(self.current_answer)
        hint_length = max(1, len(answer) // 3)
        
        hint = answer[:hint_length] + ('_' * (len(answer) - hint_length))
        return hint
    
    def show_answer(self):
        """
        إظهار الإجابة الصحيحة
        
        Returns:
            الإجابة الصحيحة
        """
        return self.current_answer
    
    def add_player(self, user_id):
        """
        إضافة لاعب
        
        Args:
            user_id: معرف المستخدم
        """
        if user_id not in self.players_scores:
            self.players_scores[user_id] = 0
    
    def update_score(self, user_id, points):
        """
        تحديث نقاط اللاعب
        
        Args:
            user_id: معرف المستخدم
            points: النقاط المضافة
        """
        self.add_player(user_id)
        self.players_scores[user_id] += points
    
    def get_score(self, user_id):
        """
        الحصول على نقاط اللاعب
        
        Args:
            user_id: معرف المستخدم
            
        Returns:
            النقاط
        """
        return self.players_scores.get(user_id, 0)
    
    def get_state(self):
        """
        الحصول على حالة اللعبة
        
        Returns:
            dict مع حالة اللعبة
        """
        return {
            'name': self.name,
            'current_round': self.current_round,
            'total_rounds': self.total_rounds,
            'is_active': self.is_active,
            'supports_hint': self.supports_hint,
            'players_count': len(self.players_scores),
            'started_at': self.started_at.isoformat()
        }
    
    def is_game_ended(self):
        """
        التحقق من انتهاء اللعبة
        
        Returns:
            True إذا انتهت اللعبة
        """
        return self.current_round >= self.total_rounds or not self.is_active
    
    def get_winner(self):
        """
        الحصول على الفائز
        
        Returns:
            معرف الفائز أو None
        """
        if not self.players_scores:
            return None
        
        return max(self.players_scores.items(), key=lambda x: x[1])[0]
    
    def reset(self):
        """إعادة تعيين اللعبة"""
        self.current_round = 0
        self.players_scores = {}
        self.current_question = None
        self.current_answer = None
        self.is_active = True
        self.started_at = datetime.now()
