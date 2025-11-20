from games.base import BaseGame
import utils
import random

class ChainGame(BaseGame):
    def __init__(self):
        super().__init__('سلسلة', rounds=5, supports_hint=True, supports_skip=True)
        self.words = [
            'محمد', 'دار', 'رمان', 'نور', 'رياض', 'ضياء', 'ءامن', 'نجم',
            'مدرسة', 'هدى', 'يوم', 'مساء', 'ءاسف', 'فرح', 'حب', 'بحر',
            'رسالة', 'هلال', 'لون', 'نجاح', 'حديقة', 'همة', 'هواء', 'ءامال',
            'ليل', 'لؤلؤ', 'ؤفاء', 'ءاخر', 'رحمة', 'هناء', 'ءافكار', 'رحلة'
        ]
        self.used_words = set()
    
    def generate_question(self):
        available_words = [w for w in self.words if w not in self.used_words]
        if not available_words:
            self.used_words.clear()
            available_words = self.words
        
        start_word = random.choice(available_words)
        self.used_words.add(start_word)
        
        last_letter = start_word[-1]
        
        possible_answers = [w for w in self.words if w.startswith(last_letter) and w not in self.used_words]
        
        if possible_answers:
            self.current_answer = random.choice(possible_answers)
        else:
            self.current_answer = None
        
        self.current_question = f"الكلمة: {start_word}\nاكتب كلمة تبدأ بحرف '{last_letter}'"
        
        return {
            'text': self.current_question,
            'answer': self.current_answer
        }
    
    def check_answer(self, user_id, answer):
        answer = answer.strip()
        
        if not self.current_answer:
            return {
                'correct': True,
                'message': 'لا توجد اجابة محددة، اي كلمة مناسبة',
                'points': 1
            }
        
        if utils.normalize_text(answer) == utils.normalize_text(self.current_answer):
            return {
                'correct': True,
                'message': 'ممتاز! اجابة صحيحة',
                'points': 2
            }
        
        if answer in self.words:
            return {
                'correct': True,
                'message': 'جيد! اجابة صحيحة',
                'points': 1
            }
        else:
            return {
                'correct': False,
                'message': f'الاجابة المتوقعة: {self.current_answer}',
                'points': 0
            }
    
    def _generate_hint(self):
        if not self.current_answer:
            return "لا يوجد تلميح"
        return f"الحل يبدأ بـ: {self.current_answer[:2]}... ({len(self.current_answer)} احرف)"
