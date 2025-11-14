from linebot.models import TextSendMessage
import random
import re

def normalize_text(text):
    if not text:
        return ""
    text = text.strip().lower()
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    text = text.replace('ؤ', 'و').replace('ئ', 'ي').replace('ء', '')
    text = text.replace('ة', 'ه').replace('ى', 'ي')
    text = re.sub(r'[\u064B-\u065F]', '', text)
    text = re.sub(r'\s+', '', text)
    return text

class SongGame:
    def __init__(self, line_bot_api, use_ai=False, ask_ai=None):
        self.line_bot_api = line_bot_api
        self.use_ai = use_ai
        self.ask_ai = ask_ai
        
        self.all_songs = [
            {"lyrics": "يا بعد عمري وروحي وكل شي أملكه", "singer": "راشد الماجد"},
            {"lyrics": "الأماكن ما تنسى تبقى في البال", "singer": "محمد عبده"},
            {"lyrics": "أحبك موت أحبك موت يا غالي", "singer": "عبدالمجيد عبدالله"},
            {"lyrics": "بعثر خاطري وبعثر أفكاري", "singer": "ماجد المهندس"},
            {"lyrics": "متعب عمري الغلا وانت ما فيك غلا", "singer": "نوال الكويتية"},
            {"lyrics": "خلاص سكرنا الموضوع وانتهينا", "singer": "عبدالله الرويشد"},
            {"lyrics": "حبيبي مجنني وذبحني وشفته", "singer": "نبيل شعيل"},
            {"lyrics": "زدني عشقاً زدني عشقاً زدني جنوناً", "singer": "كاظم الساهر"},
            {"lyrics": "يا مغرور جرحني غرورك", "singer": "أصالة"},
            {"lyrics": "عكس اللي شايفينها الحب مش سهل", "singer": "إليسا"}
        ]
        
        self.questions = []
        self.current_song = None
        self.hints_used = 0
        self.question_number = 0
        self.total_questions = 5
        self.player_scores = {}
    
    def start_game(self):
        if self.use_ai and self.ask_ai:
            self._generate_ai_songs()
        
        self.questions = random.sample(self.all_songs, min(self.total_questions, len(self.all_songs)))
        self.question_number = 0
        self.player_scores = {}
        return self._next_question()
    
    def _generate_ai_songs(self):
        """توليد أسئلة بواسطة AI"""
        try:
            prompt = """اعطني 10 مقاطع من أغاني عربية مشهورة مع اسم المغني.
الصيغة:
مقطع الأغنية | اسم المغني

مثال:
يا بعد عمري وروحي | راشد الماجد"""
            
            response = self.ask_ai(prompt)
            if response:
                lines = response.strip().split('\n')
                new_songs = []
                for line in lines:
                    if '|' in line:
                        parts = line.split('|')
                        if len(parts) == 2:
                            new_songs.append({
                                'lyrics': parts[0].strip(),
                                'singer': parts[1].strip()
                            })
                
                if new_songs:
                    self.all_songs = new_songs
        except Exception as e:
            pass
    
    def _next_question(self):
        self.question_number += 1
        self.current_song = self.questions[self.question_number - 1]
        self.hints_used = 0
        return TextSendMessage(
            text=f"▪️ لعبة الأغاني\n\nسؤال {self.question_number} من {self.total_questions}\n\n{self.current_song['lyrics']}\n\nمن المغني؟\n\n▫️ لمح - للحصول على تلميح\n▫️ جاوب - لعرض الإجابة"
        )
    
    def next_question(self):
        if self.question_number < self.total_questions:
            return self._next_question()
        return None
    
    def check_answer(self, answer, user_id, display_name):
        if not self.current_song:
            return None
        
        answer_lower = answer.strip().lower()
        
        if answer_lower in ['لمح', 'تلميح', 'hint']:
            if self.hints_used == 0:
                singer_name = self.current_song['singer']
                first_letter = singer_name[0]
                name_length = len(singer_name.replace(' ', ''))
                words = singer_name.split()
                word_info = f"{len(words)} كلمة" if len(words) > 1 else "كلمة واحدة"
                
                hint = f"▫️ يبدأ بحرف: {first_letter}\n▫️ عدد الحروف: {name_length}\n▫️ {word_info}"
                self.hints_used += 1
                return {
                    'response': TextSendMessage(text=hint),
                    'points': 0,
                    'correct': False,
                    'won': False,
                    'game_over': False
                }
            else:
                return {
                    'response': TextSendMessage(text="استخدمت التلميح"),
                    'points': 0,
                    'correct': False,
                    'won': False,
                    'game_over': False
                }
        
        if answer_lower in ['جاوب', 'الجواب', 'answer']:
            response_text = f"▪️ الإجابة: {self.current_song['singer']}"
            
            if self.question_number < self.total_questions:
                return {
                    'response': TextSendMessage(text=response_text),
                    'points': 0,
                    'correct': False,
                    'won': False,
                    'game_over': False,
                    'next_question': True
                }
            else:
                return self._end_game()
        
        if normalize_text(answer) == normalize_text(self.current_song['singer']):
            points = 20 - (self.hints_used * 5)
            
            if user_id not in self.player_scores:
                self.player_scores[user_id] = {'name': display_name, 'score': 0}
            self.player_scores[user_id]['score'] += points
            
            if self.question_number < self.total_questions:
                response_text = f"▪️ صحيح {display_name}\n\nالمغني: {self.current_song['singer']}\n\n▫️ النقاط: {points}"
                return {
                    'response': TextSendMessage(text=response_text),
                    'points': points,
                    'correct': True,
                    'won': True,
                    'game_over': False,
                    'next_question': True
                }
            else:
                return self._end_game()
        
        return None
    
    def _end_game(self):
        if self.player_scores:
            sorted_players = sorted(self.player_scores.items(), key=lambda x: x[1]['score'], reverse=True)
            winner = sorted_players[0][1]
            all_scores = [(data['name'], data['score']) for uid, data in sorted_players]
            
            from app import get_winner_card
            winner_card = get_winner_card(winner['name'], winner['score'], all_scores)
            
            return {
                'points': 0,
                'correct': False,
                'won': True,
                'game_over': True,
                'winner_card': winner_card
            }
        else:
            return {
                'response': TextSendMessage(text="انتهت اللعبة"),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': True
            }
