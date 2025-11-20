from abc import ABC, abstractmethod

class BaseGame(ABC):
    def __init__(self, name, rounds=5, supports_hint=True, supports_skip=True):
        self.name = name
        self.rounds = rounds
        self.supports_hint = supports_hint
        self.supports_skip = supports_skip
        self.current_round = 1
        self.current_question = None
        self.current_answer = None
        self.hint_used = False
    
    @abstractmethod
    def generate_question(self):
        pass
    
    @abstractmethod
    def check_answer(self, user_id, answer):
        pass
    
    def get_hint(self):
        if not self.supports_hint:
            return "التلميح غير متاح في هذه اللعبة"
        
        if self.hint_used:
            return "لقد استخدمت التلميح بالفعل لهذا السؤال"
        
        self.hint_used = True
        return self._generate_hint()
    
    def _generate_hint(self):
        if not self.current_answer:
            return "لا يوجد تلميح متاح"
        
        hint_length = max(1, len(self.current_answer) // 3)
        return f"الحل يبدأ بـ: {self.current_answer[:hint_length]}..."
    
    def show_answer(self):
        return self.current_answer if self.current_answer else "لا توجد اجابة"
    
    def next_question(self):
        self.current_round += 1
        self.hint_used = False
        return self.generate_question()
    
    def get_state(self):
        return {
            'name': self.name,
            'round': self.current_round,
            'total_rounds': self.rounds,
            'question': self.current_question,
            'answer': self.current_answer,
            'hint_used': self.hint_used
        }
    
    def reset(self):
        self.current_round = 1
        self.current_question = None
        self.current_answer = None
        self.hint_used = False
