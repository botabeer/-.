"""
Song Game - لعبة خمن المغني
"""

import random
from games.base_game import BaseGame, normalize_text

class SongGame(BaseGame):
    def __init__(self):
        super().__init__('اغنية', rounds=5, supports_hint=True, supports_skip=True)
        
        self.songs = [
            {'lyrics': 'رجعت لي أيام الماضي معاك', 'artist': 'أم كلثوم'},
            {'lyrics': 'جلست والخوف بعينيها تتأمل فنجاني', 'artist': 'عبد الحليم حافظ'},
            {'lyrics': 'تملي معاك ولو حتى بعيد عني', 'artist': 'عمرو دياب'},
            {'lyrics': 'قولي أحبك كي تزيد وسامتي', 'artist': 'كاظم الساهر'},
            {'lyrics': 'أنا لحبيبي وحبيبي إلي', 'artist': 'فيروز'},
            {'lyrics': 'حبيبي يا كل الحياة اوعدني تبقى معايا', 'artist': 'تامر حسني'},
            {'lyrics': 'كيف أبيّن لك شعوري دون ما أحكي', 'artist': 'عايض'},
            {'lyrics': 'اسخر لك غلا وتشوفني مقصر', 'artist': 'عايض'},
            {'lyrics': 'منوتي ليتك معي', 'artist': 'محمد عبده'},
            {'lyrics': 'أحبك ليه أنا مدري', 'artist': 'عبدالمجيد عبدالله'},
            {'lyrics': 'أحبك موت كلمة مالها تفسير', 'artist': 'ماجد المهندس'},
            {'lyrics': 'هيجيلي موجوع دموعه ف عينه', 'artist': 'تامر عاشور'},
            {'lyrics': 'أنا ودي إذا ودك نعيد الماضي', 'artist': 'رابح صقر'},
            {'lyrics': 'يراودني شعور إني أحبك أكثر من أول', 'artist': 'راشد الماجد'},
            {'lyrics': 'واسع خيالك اكتبه أنا بكذبك معجبه', 'artist': 'شمة حمدان'},
            {'lyrics': 'حبيته بيني وبين نفسي', 'artist': 'شيرين'},
            {'lyrics': 'مقادير يا قلبي العنا مقادير', 'artist': 'طلال مداح'},
            {'lyrics': 'فزيت من نومي أناديلك', 'artist': 'ذكرى'},
            {'lyrics': 'كلمة ولو جبر خاطر', 'artist': 'عبادي الجوهر'},
            {'lyrics': 'إلحق عيني إلحق', 'artist': 'وليد الشامي'},
            {'lyrics': 'أنا استاهل وداع أفضل وداع', 'artist': 'نوال الكويتية'},
            {'lyrics': 'غريبة الناس غريبة الدنيا', 'artist': 'وائل جسار'},
            {'lyrics': 'ماعاد يمديني ولا عاد يمديك', 'artist': 'عبدالمجيد عبدالله'},
            {'lyrics': 'يا بعدهم كلهم يا سراجي بينهم', 'artist': 'عبدالمجيد عبدالله'},
            {'lyrics': 'حتى الكره احساس', 'artist': 'عبدالمجيد عبدالله'}
        ]
    
    def generate_question(self):
        """توليد سؤال جديد"""
        song = random.choice(self.songs)
        self.current_question = f'من المغني؟\n\n"{song["lyrics"]}"'
        self.current_answer = song['artist']
        return self.current_question
    
    def check_user_answer(self, answer):
        """فحص إجابة المستخدم"""
        answer = answer.strip()
        
        if normalize_text(answer) == normalize_text(self.current_answer):
            return True, 2, f'✅ رائع! إجابة صحيحة\nالمغني: {self.current_answer}'
        
        return False, 0, f'❌ خطأ!\nالمغني الصحيح: {self.current_answer}'
