from games.base import BaseGame
import utils
import random

class BuildGame(BaseGame):
    def __init__(self):
        super().__init__('تكوين', rounds=5, supports_hint=True, supports_skip=True)
        self.puzzles = [
            {
                'letters': ['ك', 'ت', 'ا', 'ب', 'ة', 'م'],
                'words': ['كتاب', 'تاب', 'كات']
            },
            {
                'letters': ['م', 'د', 'ر', 'س', 'ة', 'ي'],
                'words': ['مدرسة', 'درس', 'سيد']
            },
            {
                'letters': ['ج', 'م', 'ي', 'ل', 'ة', 'س'],
                'words': ['جميلة', 'جمل', 'سيل']
            },
            {
                'letters': ['ب', 'ح', 'ر', 'ي', 'ة', 'ن'],
                'words': ['بحرية', 'بحر', 'رين']
            },
            {
                'letters': ['ن', 'ج', 'م', 'ة', 'و', 'ي'],
                'words': ['نجمة', 'نجم', 'جوي']
            }
        ]
    
    def generate_question(self):
        puzzle = random.choice(self.puzzles)
        shuffled_letters = puzzle['letters'].copy()
        random.shuffle(shuffled_letters)
        
        self.current_question = f"كون 3 كلمات من الاحرف:\n{' - '.join(shuffled_letters)}"
        self.current_answer = puzzle['words']
        
        return {
            'text': self.current_question,
            'answer': self.current_answer
        }
    
    def check_answer(self, user_id, answer):
        answer = answer.strip()
        words = [w.strip() for w in answer.split('-')]
        
        if len(words) != 3:
            return {
                'correct': False,
                'message': 'الرجاء كتابة 3 كلمات مفصولة بـ -',
                'points': 0
            }
        
        correct_count = 0
        for word in words:
            normalized_word = utils.normalize_text(word)
            normalized_answers = [utils.normalize_text(a) for a in self.current_answer]
            if normalized_word in normalized_answers:
                correct_count += 1
        
        if correct_count == 3:
            return {
                'correct': True,
                'message': 'ممتاز! جميع الكلمات صحيحة',
                'points': 2
            }
        elif correct_count >= 2:
            return {
                'correct': True,
                'message': f'جيد! {correct_count} من 3 صحيحة',
                'points': 1
            }
        else:
            correct = ' - '.join(self.current_answer)
            return {
                'correct': False,
                'message': f'الكلمات الصحيحة:\n{correct}',
                'points': 0
            }
    
    def _generate_hint(self):
        return f"احدى الكلمات تبدأ بـ: {self.current_answer[0][:2]}..."
