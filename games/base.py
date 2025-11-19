"""
Base Game Class - الفئة الأساسية لجميع الألعاب
توفر الوظائف المشتركة بين جميع الألعاب
"""

from abc import ABC, abstractmethod
from utils import create_game_card, create_hint_card, create_answer_card, create_results_card


class BaseGame(ABC):
    """الفئة الأساسية لجميع الألعاب"""
    
    def __init__(self, game_name, total_rounds=5):
        """
        تهيئة اللعبة الأساسية
        
        Args:
            game_name: اسم اللعبة
            total_rounds: عدد الجولات (افتراضي 5)
        """
        self.game_name = game_name
        self.total_rounds = total_rounds
        self.current_round = 0
        self.player_scores = {}
        self.questions = []
        self.current_question = None
        self.hint_used = False
    
    @abstractmethod
    def generate_questions(self):
        """توليد الأسئلة - يجب تنفيذه في كل لعبة"""
        pass
    
    @abstractmethod
    def check_answer(self, text, user_id, user_name):
        """فحص الإجابة - يجب تنفيذه في كل لعبة"""
        pass
    
    def start_game(self):
        """بدء اللعبة وإنشاء الأسئلة"""
        self.generate_questions()
        self.current_round = 0
        self.hint_used = False
        return self.next_question()
    
    def next_question(self):
        """الانتقال للسؤال التالي"""
        if self.current_round >= self.total_rounds:
            return None
        
        self.current_round += 1
        self.hint_used = False
        
        if self.current_round <= len(self.questions):
            self.current_question = self.questions[self.current_round - 1]
            return self._create_question_card()
        
        return None
    
    @abstractmethod
    def _create_question_card(self):
        """إنشاء بطاقة السؤال - يجب تنفيذه في كل لعبة"""
        pass
    
    def get_hint(self):
        """الحصول على تلميح - اختياري"""
        return None
    
    def show_answer(self):
        """عرض الإجابة الصحيحة"""
        if not self.current_question:
            return None
        
        answer = self.current_question.get('answer', 'غير متوفر')
        return create_answer_card(answer)
    
    def add_score(self, user_id, user_name, points):
        """إضافة نقاط للاعب"""
        if user_id not in self.player_scores:
            self.player_scores[user_id] = {
                'name': user_name,
                'score': 0
            }
        
        self.player_scores[user_id]['score'] += points
    
    def get_final_results(self):
        """الحصول على النتائج النهائية"""
        return create_results_card(self.player_scores)
    
    def is_game_over(self):
        """التحقق من انتهاء اللعبة"""
        return self.current_round >= self.total_rounds
