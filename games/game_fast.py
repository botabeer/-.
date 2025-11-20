from games.base import BaseGame
import utils
import random

class FastGame(BaseGame):
    def __init__(self):
        super().__init__('اسرع', rounds=5, supports_hint=False, supports_skip=False)
        self.words = [
            'برمجة', 'حاسوب', 'تطوير', 'تصميم', 'شبكة',
            'قاعدة بيانات', 'خوارزمية', 'واجهة مستخدم', 'نظام تشغيل',
            'الذكاء الاصطناعي', 'تعلم الآلة', 'امن المعلومات',
            'سحابة الكترونية', 'تطبيق جوال', 'موقع الكتروني',
            'البيانات الضخمة', 'انترنت الاشياء', 'الواقع الافتراضي',
            'سرعة البرق', 'قوة النمر', 'ذكاء الثعلب',
            'جمال الطبيعة', 'روعة الفن', 'عبقرية العلم'
        ]
    
    def generate_question(self):
        word = random.choice(self.words)
        self.current_question = f"اكتب: {word}"
        self.current_answer = word
        return {
            'text': self.current_question,
            'answer': self.current_answer
        }
    
    def check_answer(self, user_id, answer):
        answer = answer.strip()
        
        if utils.normalize_text(answer) == utils.normalize_text(self.current_answer):
            return {
                'correct': True,
                'message': 'احسنت! اجابة صحيحة',
                'points': 2
            }
        else:
            return {
                'correct': False,
                'message': f'خطأ! الاجابة الصحيحة: {self.current_answer}',
                'points': 0
            }
