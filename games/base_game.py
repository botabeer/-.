"""
Base Game Class
"""

import re
from abc import ABC, abstractmethod

def normalize_text(text):
    """تطبيع النص العربي"""
    if not text:
        return ""
    text = re.sub(r'[\u0617-\u061A\u064B-\u0652]', '', text)
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    text = text.replace('ة', 'ه').replace('ى', 'ي')
    return text.strip().lower()

class BaseGame(ABC):
    """الكلاس الأساسي لجميع الألعاب"""
    
    def __init__(self, name, rounds=5, supports_hint=True, supports_skip=True):
        self.name = name
        self.rounds = rounds
        self.supports_hint = supports_hint
        self.supports_skip = supports_skip
        self.current_round = 0
        self.current_question = None
        self.current_answer = None
        self.hint_used = False
        self.total_points = 0
    
    @abstractmethod
    def generate_question(self):
        """توليد سؤال جديد - يجب تنفيذها في كل لعبة"""
        pass
    
    @abstractmethod
    def check_user_answer(self, answer):
        """فحص إجابة المستخدم - يرجع (correct, points, message)"""
        pass
    
    def start_game(self):
        """بدء اللعبة"""
        self.current_round = 1
        self.total_points = 0
        return self.generate_question()
    
    def get_hint(self):
        """الحصول على تلميح"""
        if not self.supports_hint:
            return -1, "❌ التلميح غير متاح في هذه اللعبة"
        
        if self.hint_used:
            return -1, "⚠️ لقد استخدمت التلميح بالفعل"
        
        self.hint_used = True
        
        if isinstance(self.current_answer, str):
            reveal_count = max(1, int(len(self.current_answer) * 0.3))
            hint = f"💡 يبدأ بـ: {self.current_answer[:reveal_count]}..."
        else:
            hint = "💡 لا يوجد تلميح متاح"
        
        return -1, hint
    
    def skip_question(self):
        """تخطي السؤال"""
        if not self.supports_skip:
            return 0, "❌ التخطي غير متاح في هذه اللعبة"
        
        answer = str(self.current_answer)
        return 0, f"⏭️ الإجابة الصحيحة: {answer}"
    
    def next_round(self):
        """الانتقال للجولة التالية"""
        if self.is_finished():
            return None
        
        self.current_round += 1
        self.hint_used = False
        return self.generate_question()
    
    def is_finished(self):
        """هل انتهت اللعبة؟"""
        return self.current_round >= self.rounds
    
    def add_points(self, points):
        """إضافة نقاط"""
        self.total_points += points
        return self.total_points
    
    def get_game_state(self):
        """الحصول على حالة اللعبة"""
        return {
            'name': self.name,
            'current_round': self.current_round,
            'total_rounds': self.rounds,
            'total_points': self.total_points,
            'is_finished': self.is_finished()
        }
