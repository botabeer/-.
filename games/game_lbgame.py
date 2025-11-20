from games.base import BaseGame
import utils
import random

class LBGame(BaseGame):
    def __init__(self):
        super().__init__('لعبة', rounds=5, supports_hint=True, supports_skip=True)
        self.letters = list('ابتجحخدرزسشصضطعغفقكلمنهوي')
        self.categories = {
            'انسان': ['احمد', 'بدر', 'تركي', 'جمال', 'حسن', 'خالد', 'داود', 'راشد', 'زيد', 'سعيد', 'شادي', 'صالح', 'ضياء', 'طارق', 'عمر', 'غسان', 'فهد', 'قاسم', 'كريم', 'ليث', 'محمد', 'نادر', 'هاني', 'وليد', 'ياسر'],
            'حيوان': ['اسد', 'بقرة', 'تمساح', 'جمل', 'حصان', 'خروف', 'دب', 'ريم', 'زرافة', 'سمكة', 'شاة', 'صقر', 'ضبع', 'طاووس', 'عصفور', 'غزال', 'فيل', 'قرد', 'كلب', 'ليث', 'ماعز', 'نمر', 'هر', 'وعل', 'يمامة'],
            'نبات': ['اس', 'بصل', 'تفاح', 'جزر', 'حمص', 'خيار', 'دراق', 'ريحان', 'زيتون', 'سبانخ', 'شمندر', 'صبار', 'ضرو', 'طماطم', 'عنب', 'غار', 'فجل', 'قمح', 'كزبرة', 'ليمون', 'موز', 'نعناع', 'هيل', 'ورد', 'ياسمين'],
            'بلد': ['الامارات', 'البحرين', 'تونس', 'الجزائر', 'الحجاز', 'خراسان', 'دمشق', 'الرياض', 'زنجبار', 'السودان', 'الشام', 'صنعاء', 'ضرماء', 'طرابلس', 'عمان', 'غزة', 'فلسطين', 'قطر', 'الكويت', 'لبنان', 'مصر', 'نجد', 'هولندا', 'واشنطن', 'اليمن']
        }
    
    def generate_question(self):
        letter = random.choice(self.letters)
        self.current_answer = {
            'انسان': self._find_word('انسان', letter),
            'حيوان': self._find_word('حيوان', letter),
            'نبات': self._find_word('نبات', letter),
            'بلد': self._find_word('بلد', letter)
        }
        self.current_question = f"ابحث عن كلمات تبدأ بحرف '{letter}'\nانسان - حيوان - نبات - بلد"
        return {
            'text': self.current_question,
            'answer': self.current_answer
        }
    
    def _find_word(self, category, letter):
        words = [w for w in self.categories[category] if w.startswith(letter)]
        return random.choice(words) if words else None
    
    def check_answer(self, user_id, answer):
        answer = answer.strip()
        parts = answer.split('-')
        
        if len(parts) != 4:
            return {
                'correct': False,
                'message': 'الرجاء الكتابة بالصيغة: انسان - حيوان - نبات - بلد',
                'points': 0
            }
        
        categories = ['انسان', 'حيوان', 'نبات', 'بلد']
        correct_count = 0
        
        for i, part in enumerate(parts):
            part = part.strip()
            correct_answer = self.current_answer[categories[i]]
            if utils.normalize_text(part) == utils.normalize_text(correct_answer):
                correct_count += 1
        
        if correct_count == 4:
            return {
                'correct': True,
                'message': 'ممتاز! جميع الاجابات صحيحة',
                'points': 2
            }
        elif correct_count >= 2:
            return {
                'correct': True,
                'message': f'جيد! {correct_count} من 4 صحيحة',
                'points': 1
            }
        else:
            answers = ' - '.join([self.current_answer[c] for c in categories])
            return {
                'correct': False,
                'message': f'الاجابات الصحيحة:\n{answers}',
                'points': 0
            }
    
    def _generate_hint(self):
        hint_parts = []
        for cat in ['انسان', 'حيوان', 'نبات', 'بلد']:
            word = self.current_answer[cat]
            hint_parts.append(f"{word[:2]}...")
        return ' - '.join(hint_parts)
