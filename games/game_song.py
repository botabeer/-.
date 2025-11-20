from games.base import BaseGame
import utils
import random

class SongGame(BaseGame):
    def __init__(self):
        super().__init__('اغنية', rounds=5, supports_hint=True, supports_skip=True)
        self.songs = [
            {'lyrics': 'يا طير يا طاير', 'artist': 'عبدالمجيد عبدالله'},
            {'lyrics': 'كل ما اقول التوبة', 'artist': 'ماجد المهندس'},
            {'lyrics': 'على البال', 'artist': 'محمد عبده'},
            {'lyrics': 'قل للمليحة', 'artist': 'فيروز'},
            {'lyrics': 'سيرة الحب', 'artist': 'عبدالحليم حافظ'},
            {'lyrics': 'في يوم وليلة', 'artist': 'كاظم الساهر'},
            {'lyrics': 'بحبك يا صاحبي', 'artist': 'فضل شاكر'},
            {'lyrics': 'حبيبي يا نور العين', 'artist': 'عمرو دياب'},
            {'lyrics': 'انا وليلى', 'artist': 'عبدالحليم حافظ'},
            {'lyrics': 'يا مسافر وحدك', 'artist': 'عبدالكريم عبدالقادر'}
        ]
    
    def generate_question(self):
        song = random.choice(self.songs)
        self.current_question = f"من المغني؟\n\"{song['lyrics']}\""
        self.current_answer = song['artist']
        return {
            'text': self.current_question,
            'answer': self.current_answer
        }
    
    def check_answer(self, user_id, answer):
        answer = answer.strip()
        
        if utils.normalize_text(answer) == utils.normalize_text(self.current_answer):
            return {
                'correct': True,
                'message': 'رائع! اجابة صحيحة',
                'points': 2
            }
        else:
            return {
                'correct': False,
                'message': f'خطأ! المغني هو: {self.current_answer}',
                'points': 0
            }
    
    def _generate_hint(self):
        words = self.current_answer.split()
        if len(words) > 1:
            return f"الاسم: {words[0][:2]}... {words[-1][:2]}..."
        return f"الحل يبدأ بـ: {self.current_answer[:3]}..."
