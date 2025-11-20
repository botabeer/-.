from games.base import BaseGame
import utils
import random

class OppositeGame(BaseGame):
    def __init__(self):
        super().__init__('ضد', rounds=5, supports_hint=True, supports_skip=True)
        self.opposites = {
            'كبير': 'صغير',
            'طويل': 'قصير',
            'سريع': 'بطيء',
            'ساخن': 'بارد',
            'قوي': 'ضعيف',
            'جميل': 'قبيح',
            'نظيف': 'قذر',
            'غني': 'فقير',
            'سهل': 'صعب',
            'قريب': 'بعيد',
            'ثقيل': 'خفيف',
            'واسع': 'ضيق',
            'عالي': 'منخفض',
            'جديد': 'قديم',
            'مبكر': 'متأخر',
            'نهار': 'ليل',
            'شمال': 'جنوب',
            'شرق': 'غرب',
            'صيف': 'شتاء',
            'ذكر': 'انثى',
            'ابيض': 'اسود',
            'حلو': 'مر',
            'صح': 'خطأ',
            'حي': 'ميت',
            'اول': 'اخير'
        }
    
    def generate_question(self):
        word = random.choice(list(self.opposites.keys()))
        self.current_question = f"ما هو عكس:\n{word}"
        self.current_answer = self.opposites[word]
        return {
            'text': self.current_question,
            'answer': self.current_answer
        }
    
    def check_answer(self, user_id, answer):
        answer = answer.strip()
        
        if utils.normalize_text(answer) == utils.normalize_text(self.current_answer):
            return {
                'correct': True,
                'message': 'صحيح! اجابة ممتازة',
                'points': 2
            }
        else:
            return {
                'correct': False,
                'message': f'خطأ! العكس هو: {self.current_answer}',
                'points': 0
            }
    
    def _generate_hint(self):
        return f"يبدأ بحرف '{self.current_answer[0]}' وعدد الاحرف: {len(self.current_answer)}"
