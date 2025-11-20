# ============================================
# games/game_song.py - لعبة الأغنية
# ============================================

"""
لعبة الأغنية
============
تخمين المغني من كلمات الأغنية
تدعم التلميح وإظهار الإجابة
"""

import random
from .base import BaseGame
from rules import POINTS, GAMES_INFO
from utils import normalize_text


class SongGame(BaseGame):
    """لعبة تخمين المغني"""
    
    def __init__(self):
        game_info = GAMES_INFO['اغنية']
        super().__init__(
            name=game_info['name'],
            rounds=game_info['rounds'],
            supports_hint=game_info['supports_hint']
        )
        
        # قاعدة بيانات الأغاني والمغنيين
        self.songs_database = [
            {
                'lyrics': 'قلبي اطمأن، قلبي ارتاح',
                'singer': 'حسين الجسمي',
                'song': 'قلبي اطمأن'
            },
            {
                'lyrics': 'أنا لو عشقت، ما عرفت أخون',
                'singer': 'محمد عبده',
                'song': 'أنا لو عشقت'
            },
            {
                'lyrics': 'تعالى أقولك، أنا باحبك',
                'singer': 'عمرو دياب',
                'song': 'تعالى'
            },
            {
                'lyrics': 'يا طيرة طيري، وقولي له',
                'singer': 'فيروز',
                'song': 'يا طيرة طيري'
            },
            {
                'lyrics': 'كل ما أقول التوبة، يرجعني الهوى',
                'singer': 'محمد عبده',
                'song': 'كل ما أقول التوبة'
            },
            {
                'lyrics': 'قالوا نسيت، قلت معقولة',
                'singer': 'كاظم الساهر',
                'song': 'معقولة'
            },
            {
                'lyrics': 'اشتقت لك، يا حبيبي اشتقت',
                'singer': 'ماجد المهندس',
                'song': 'اشتقت لك'
            },
            {
                'lyrics': 'يا أيها الطفل، يا ابن الحبايب',
                'singer': 'فيروز',
                'song': 'يا أيها الطفل'
            },
            {
                'lyrics': 'سيبك من الحب، سيبك',
                'singer': 'عمرو دياب',
                'song': 'سيبك'
            },
            {
                'lyrics': 'على بالي، ما يغيب',
                'singer': 'شيرين',
                'song': 'على بالي'
            },
            {
                'lyrics': 'بشرة خير، يا عيني بشرة خير',
                'singer': 'حسين الجسمي',
                'song': 'بشرة خير'
            },
            {
                'lyrics': 'أنا ليه بحبك، مش عارف ليه',
                'singer': 'تامر حسني',
                'song': 'أنا ليه'
            },
            {
                'lyrics': 'يا مسهرني، يا عذابي',
                'singer': 'راشد الماجد',
                'song': 'يا مسهرني'
            },
            {
                'lyrics': 'نسيني الدنيا، ونسيت النوم',
                'singer': 'عبدالمجيد عبدالله',
                'song': 'نسيني الدنيا'
            },
            {
                'lyrics': 'أهواك، وأتمنى أنساك',
                'singer': 'عبدالحليم حافظ',
                'song': 'أهواك'
            },
            {
                'lyrics': 'ولا ليلة، من الليالي',
                'singer': 'نانسي عجرم',
                'song': 'ولا ليلة'
            },
            {
                'lyrics': 'يا ليل يا عين، يا ليلي',
                'singer': 'أم كلثوم',
                'song': 'يا ليل يا عين'
            },
            {
                'lyrics': 'زي العسل، يا حلو',
                'singer': 'إليسا',
                'song': 'زي العسل'
            },
            {
                'lyrics': 'حبيبي يا نور العين',
                'singer': 'عمرو دياب',
                'song': 'نور العين'
            },
            {
                'lyrics': 'تعبت من الحب، تعبت',
                'singer': 'ماجد المهندس',
                'song': 'تعبت'
            }
        ]
        
        self.current_song = None
    
    def generate_question(self):
        """
        توليد سؤال جديد
        
        Returns:
            نص السؤال
        """
        # اختيار أغنية عشوائية
        self.current_song = random.choice(self.songs_database)
        
        # حفظ الإجابة
        self.current_answer = self.current_song['singer']
        
        # إنشاء السؤال
        question = f'من المغني؟\n"{self.current_song["lyrics"]}"'
        
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
        user_answer = normalize_text(answer).lower()
        correct_answer = normalize_text(self.current_answer).lower()
        
        # التحقق من التطابق (مع السماح ببعض الاختلافات البسيطة)
        is_correct = user_answer == correct_answer or \
                     user_answer in correct_answer or \
                     correct_answer in user_answer
        
        # حساب النقاط
        points_earned = 0
        if is_correct:
            points_earned = POINTS['correct']
            self.update_score(user_id, points_earned)
        
        # الانتقال للسؤال التالي
        game_continues = self.next_question()
        
        result = {
            'correct': is_correct,
            'correct_answer': self.current_answer,
            'song_name': self.current_song.get('song', ''),
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
        if not self.current_answer:
            return "لا يوجد تلميح متاح"
        
        singer = self.current_answer
        
        # تلميح: الحرف الأول وعدد الأحرف
        first_letter = singer[0]
        length = len(singer)
        
        hint = f"التلميح: يبدأ بحرف '{first_letter}' وعدد الأحرف: {length}"
        
        return hint
    
    def show_answer(self):
        """
        إظهار الإجابة الصحيحة
        
        Returns:
            الإجابة
        """
        if self.current_song:
            return f'{self.current_answer} - أغنية: {self.current_song.get("song", "")}'
        return self.current_answer
