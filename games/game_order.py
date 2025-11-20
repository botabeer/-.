from games.base import BaseGame
import utils
import random

class OrderGame(BaseGame):
    def __init__(self):
        super().__init__('ترتيب', rounds=5, supports_hint=True, supports_skip=True)
        self.sequences = [
            {
                'type': 'ايام',
                'items': ['السبت', 'الاحد', 'الاثنين', 'الثلاثاء', 'الاربعاء', 'الخميس', 'الجمعة']
            },
            {
                'type': 'اشهر',
                'items': ['يناير', 'فبراير', 'مارس', 'ابريل', 'مايو', 'يونيو', 'يوليو', 'اغسطس', 'سبتمبر', 'اكتوبر', 'نوفمبر', 'ديسمبر']
            },
            {
                'type': 'اشهر هجرية',
                'items': ['محرم', 'صفر', 'ربيع الاول', 'ربيع الثاني', 'جمادى الاولى', 'جمادى الثانية', 'رجب', 'شعبان', 'رمضان', 'شوال', 'ذو القعدة', 'ذو الحجة']
            },
            {
                'type': 'ارقام',
                'items': ['واحد', 'اثنان', 'ثلاثة', 'اربعة', 'خمسة', 'ستة', 'سبعة', 'ثمانية', 'تسعة', 'عشرة']
            },
            {
                'type': 'احجام',
                'items': ['صغير جدا', 'صغير', 'متوسط', 'كبير', 'كبير جدا']
            }
        ]
    
    def generate_question(self):
        sequence = random.choice(self.sequences)
        correct_order = sequence['items'].copy()
        
        sample_size = min(4, len(correct_order))
        sampled = random.sample(correct_order, sample_size)
        
        shuffled = sampled.copy()
        random.shuffle(shuffled)
        
        self.current_question = f"رتب {sequence['type']} التالية:\n{' - '.join(shuffled)}"
        self.current_answer = [item for item in correct_order if item in sampled]
        
        return {
            'text': self.current_question,
            'answer': self.current_answer
        }
    
    def check_answer(self, user_id, answer):
        answer = answer.strip()
        parts = [p.strip() for p in answer.split('-')]
        
        if len(parts) != len(self.current_answer):
            return {
                'correct': False,
                'message': f'الرجاء ترتيب {len(self.current_answer)} عناصر مفصولة بـ -',
                'points': 0
            }
        
        normalized_answer = [utils.normalize_text(p) for p in parts]
        normalized_correct = [utils.normalize_text(p) for p in self.current_answer]
        
        if normalized_answer == normalized_correct:
            return {
                'correct': True,
                'message': 'ممتاز! الترتيب صحيح',
                'points': 2
            }
        else:
            correct = ' - '.join(self.current_answer)
            return {
                'correct': False,
                'message': f'خطأ! الترتيب الصحيح:\n{correct}',
                'points': 0
            }
    
    def _generate_hint(self):
        if len(self.current_answer) >= 2:
            return f"يبدأ بـ: {self.current_answer[0]}"
        return "لا يوجد تلميح"
