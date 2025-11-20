# ============================================
# games/game_order.py - لعبة الترتيب
# ============================================

"""
لعبة الترتيب
============
ترتيب العناصر حسب المطلوب
تدعم التلميح وإظهار الإجابة
"""

import random
from .base import BaseGame
from rules import POINTS, GAMES_INFO
from utils import normalize_text


class OrderGame(BaseGame):
    """لعبة ترتيب العناصر"""
    
    def __init__(self):
        game_info = GAMES_INFO['ترتيب']
        super().__init__(
            name=game_info['name'],
            rounds=game_info['rounds'],
            supports_hint=game_info['supports_hint']
        )
        
        # قاعدة بيانات أسئلة الترتيب
        self.order_questions = [
            {
                'question': 'رتب الأشهر الهجرية:',
                'items': ['محرم', 'صفر', 'ربيع الأول', 'ربيع الثاني'],
                'type': 'months'
            },
            {
                'question': 'رتب الأرقام من الأصغر للأكبر:',
                'items': ['5', '2', '9', '1'],
                'answer': ['1', '2', '5', '9'],
                'type': 'numbers'
            },
            {
                'question': 'رتب حسب الحجم (من الأصغر للأكبر):',
                'items': ['فيل', 'نملة', 'قط', 'أسد'],
                'answer': ['نملة', 'قط', 'أسد', 'فيل'],
                'type': 'size'
            },
            {
                'question': 'رتب الدول حسب المساحة (من الأكبر للأصغر):',
                'items': ['البحرين', 'السعودية', 'قطر', 'الإمارات'],
                'answer': ['السعودية', 'الإمارات', 'قطر', 'البحرين'],
                'type': 'area'
            },
            {
                'question': 'رتب مراحل حياة الإنسان:',
                'items': ['شيخوخة', 'طفولة', 'شباب', 'مراهقة'],
                'answer': ['طفولة', 'مراهقة', 'شباب', 'شيخوخة'],
                'type': 'life'
            },
            {
                'question': 'رتب الوجبات حسب الوقت:',
                'items': ['عشاء', 'فطور', 'غداء'],
                'answer': ['فطور', 'غداء', 'عشاء'],
                'type': 'meals'
            },
            {
                'question': 'رتب الكواكب حسب البعد عن الشمس:',
                'items': ['المريخ', 'الأرض', 'عطارد', 'الزهرة'],
                'answer': ['عطارد', 'الزهرة', 'الأرض', 'المريخ'],
                'type': 'planets'
            },
            {
                'question': 'رتب الفصول:',
                'items': ['خريف', 'صيف', 'ربيع', 'شتاء'],
                'answer': ['ربيع', 'صيف', 'خريف', 'شتاء'],
                'type': 'seasons'
            },
            {
                'question': 'رتب حسب السرعة (من الأبطأ للأسرع):',
                'items': ['طائرة', 'سيارة', 'دراجة', 'شخص يمشي'],
                'answer': ['شخص يمشي', 'دراجة', 'سيارة', 'طائرة'],
                'type': 'speed'
            },
            {
                'question': 'رتب الألوان حسب ألوان قوس قزح:',
                'items': ['أزرق', 'أحمر', 'أصفر', 'أخضر'],
                'answer': ['أحمر', 'أصفر', 'أخضر', 'أزرق'],
                'type': 'colors'
            }
        ]
        
        self.current_question_data = None
        self.shuffled_items = []
    
    def generate_question(self):
        """
        توليد سؤال جديد
        
        Returns:
            نص السؤال
        """
        # اختيار سؤال عشوائي
        self.current_question_data = random.choice(self.order_questions)
        
        # خلط العناصر
        self.shuffled_items = self.current_question_data['items'].copy()
        random.shuffle(self.shuffled_items)
        
        # حفظ الإجابة الصحيحة
        if 'answer' in self.current_question_data:
            self.current_answer = self.current_question_data['answer']
        else:
            self.current_answer = self.current_question_data['items']
        
        # إنشاء السؤال
        question = f"{self.current_question_data['question']}\n"
        question += ', '.join(self.shuffled_items)
        question += "\n\nأجب بترتيب العناصر مفصولة بفواصل"
        
        return question
    
    def check_answer(self, user_id, answer):
        """
        التحقق من الإجابة
        
        Args:
            user_id: معرف المستخدم
            answer: إجابة المستخدم
            
        Returns:
            dict مع النتيجة
        """
        # تنظيف وتقسيم إجابة المستخدم
        user_items = [normalize_text(item.strip()).lower() 
                      for item in answer.split(',')]
        
        # تنظيف الإجابة الصحيحة
        correct_items = [normalize_text(item).lower() 
                        for item in self.current_answer]
        
        # التحقق من التطابق
        is_correct = user_items == correct_items
        
        # حساب النقاط
        points_earned = 0
        if is_correct:
            points_earned = POINTS['correct']
            self.update_score(user_id, points_earned)
        
        # الانتقال للسؤال التالي
        game_continues = self.next_question()
        
        result = {
            'correct': is_correct,
            'correct_answer': ', '.join(self.current_answer),
            'user_answer': ', '.join(user_items),
            'points_earned': points_earned,
            'total_points': self.get_score(user_id),
            'current_round': self.current_round,
            'total_rounds': self.total_rounds,
            'game_ended': not game_continues,
            'next_question': self.current_question if game_continues else None
        }
        
        return result
    
    def get_hint(self):
        """
        الحصول على تلميح
        
        Returns:
            التلميح
        """
        if not self.current_answer or len(self.current_answer) < 2:
            return "لا يوجد تلميح متاح"
        
        # تلميح: أول عنصرين في الترتيب الصحيح
        hint = f"التلميح: يبدأ الترتيب بـ: {self.current_answer[0]}, {self.current_answer[1]}"
        
        return hint
    
    def show_answer(self):
        """
        إظهار الإجابة الصحيحة
        
        Returns:
            الإجابة
        """
        return f'الترتيب الصحيح: {", ".join(self.current_answer)}'
