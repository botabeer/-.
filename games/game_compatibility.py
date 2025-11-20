from games.base import BaseGame
import random

class CompatibilityGame(BaseGame):
    def __init__(self):
        super().__init__('توافق', rounds=1, supports_hint=False, supports_skip=False)
    
    def generate_question(self):
        self.current_question = "اكتب اسمين مفصولين بمسافة"
        return {
            'text': self.current_question,
            'answer': None
        }
    
    def check_answer(self, user_id, answer):
        answer = answer.strip()
        parts = answer.split()
        
        if len(parts) < 2:
            return {
                'correct': False,
                'message': 'الرجاء كتابة اسمين مفصولين بمسافة',
                'points': 0
            }
        
        name1 = parts[0]
        name2 = ' '.join(parts[1:])
        
        percentage = self._calculate_compatibility(name1, name2)
        
        emoji = self._get_emoji(percentage)
        description = self._get_description(percentage)
        
        message = f"{emoji} نسبة التوافق بين:\n{name1} و {name2}\n\n{percentage}%\n\n{description}"
        
        return {
            'correct': True,
            'message': message,
            'points': 0
        }
    
    def _calculate_compatibility(self, name1, name2):
        combined = name1 + name2
        seed = sum(ord(c) for c in combined)
        random.seed(seed)
        percentage = random.randint(1, 100)
        random.seed()
        return percentage
    
    def _get_emoji(self, percentage):
        if percentage >= 90:
            return ''
        elif percentage >= 70:
            return ''
        elif percentage >= 50:
            return ''
        elif percentage >= 30:
            return ''
        else:
            return ''
    
    def _get_description(self, percentage):
        if percentage >= 90:
            return 'توافق رائع! علاقة مثالية'
        elif percentage >= 70:
            return 'توافق ممتاز! علاقة قوية'
        elif percentage >= 50:
            return 'توافق جيد! علاقة متوازنة'
        elif percentage >= 30:
            return 'توافق متوسط! تحتاج جهد'
        else:
            return 'توافق ضعيف! علاقة صعبة'
