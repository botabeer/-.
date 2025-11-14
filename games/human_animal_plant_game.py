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

class HumanAnimalPlantGame:
    def __init__(self, line_bot_api, use_ai=False, ask_ai=None):
        self.line_bot_api = line_bot_api
        self.use_ai = use_ai
        self.ask_ai = ask_ai
        
        self.all_letters = ['ا', 'ب', 'ت', 'ج', 'ح', 'خ', 'د', 'ر', 'ز', 'س', 'ش', 'ص', 'ع
        self.database = {
            'ا': {'human': 'احمد', 'animal': 'اسد', 'plant': 'ازهار', 'country': 'الامارات'},
            'ب': {'human': 'باسم', 'animal': 'بقرة', 'plant': 'برتقال', 'country': 'بحرين'},
            'ت': {'human': 'تامر', 'animal': 'تمساح', 'plant': 'توت', 'country': 'تركيا'},
            'ج': {'human': 'جمال', 'animal': 'جمل', 'plant': 'جزر', 'country': 'جيبوتي'},
            'ح': {'human': 'حسن', 'animal': 'حمار', 'plant': 'حمص', 'country': 'الحبشة'},
            'خ': {'human': 'خالد', 'animal': 'خروف', 'plant': 'خوخ', 'country': 'الخرطوم'},
            'د': {'human': 'داود', 'animal': 'ديك', 'plant': 'دراق', 'country': 'دمشق'},
            'ر': {'human': 'رامي', 'animal': 'رنه', 'plant': 'رمان', 'country': 'روسيا'},
            'ز': {'human': 'زياد', 'animal': 'زرافة', 'plant': 'زيتون', 'country': 'زامبيا'},
            'س': {'human': 'سعيد', 'animal': 'سمكة', 'plant': 'سفرجل', 'country': 'سوريا'},
            'ش': {'human': 'شريف', 'animal': 'شاه', 'plant': 'شعير', 'country': 'الشام'},
            'ص': {'human': 'صالح', 'animal': 'صقر', 'plant': 'صبار', 'country': 'صنعاء'},
            'ع': {'human': 'عمر', 'animal': 'عصفور', 'plant': 'عنب', 'country': 'عمان'},
            'ف': {'human': 'فهد', 'animal': 'فيل', 'plant': 'فول', 'country': 'فرنسا'},
            'ق': {'human': 'قاسم', 'animal': 'قط', 'plant': 'قمح', 'country': 'قطر'},
            'ك': {'human': 'كريم', 'animal': 'كلب', 'plant': 'كرز', 'country': 'الكويت'},
            'ل': {'human': 'ليث', 'animal': 'ليمور', 'plant': 'ليمون', 'country': 'لبنان'},
            'م': {'human': 'محمد', 'animal': 'ماعز', 'plant': 'موز', 'country': 'مصر'},
            'ن': {'human': 'ناصر', 'animal': 'نمر', 'plant': 'نعناع', 'country': 'نيجيريا'},
            'ه': {'human': 'هاني', 'animal': 'هر', 'plant': 'هندباء', 'country': 'الهند'},
            'و': {'human': 'وليد', 'animal': 'وزه', 'plant': 'ورد', 'country': 'واشنطن'},
            'ي': {'human': 'ياسر', 'animal': 'يمامه', 'plant': 'يانسون', 'country': 'اليمن'}
        }
        self.questions = []
        self.current_letter = None
        self.hints_used = 0
        self.question_number = 0
        self.total_questions = 5
        self.player_scores = {}
    
    def start_game(self):
        self.questions = random.sample(self.all_letters, self.total_questions)
        self.question_number = 0
        self.player_scores = {}
        return self._next_question()
    
    def _next_question(self):
        self.question_number += 1
        self.current_letter = self.questions[self.question_number - 1]
        self.hints_used = 0
        return TextSendMessage(
            text=f"▪️ لعبة إنسان حيوان نبات\n\nسؤال {self.question_number} من {self.total_questions}\n\nالحرف: {self.current_letter}\n\nاكتب: إنسان، حيوان، نبات، بلاد\nمفصولة بفواصل\n\nمثال: أحمد، أسد، أزهار، الأردن\n\n▫️ لمح - للحصول على تلميح\n▫️ جاوب - لعرض الإجابة"
        )
    
    def next_question(self):
        if self.question_number < self.total_questions:
            return self._next_question()
        return None
    
    def check_answer(self, answer, user_id, display_name):
        if not self.current_letter:
            return None
        
        answer_lower = answer.strip().lower()
        
        if answer_lower in ['لمح', 'تلميح', 'hint']:
            if self.hints_used == 0:
                hint = f"▫️ إنسان: {self.database[self.current_letter]['human']}"
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
            answers = self.database[self.current_letter]
            response_text = f"▪️ الإجابات:\n\n▫️ إنسان: {answers['human']}\n▫️ حيوان: {answers['animal']}\n▫️ نبات: {answers['plant']}\n▫️ بلاد: {answers['country']}"
            
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
        
        # تحليل الإجابة
        parts = [p.strip() for p in answer.split(',')]
        
        if len(parts) >= 4:
            # التحقق من أن جميع الكلمات تبدأ بالحرف المطلوب
            all_correct = True
            for part in parts[:4]:
                if not part or normalize_text(part)[0] != normalize_text(self.current_letter):
                    all_correct = False
                    break
            
            if all_correct:
                points = 25 - (self.hints_used * 5)
                
                if user_id not in self.player_scores:
                    self.player_scores[user_id] = {'name': display_name, 'score': 0}
                self.player_scores[user_id]['score'] += points
                
                if self.question_number < self.total_questions:
                    response_text = f"▪️ صحيح {display_name}\n\n▫️ إنسان: {parts[0]}\n▫️ حيوان: {parts[1]}\n▫️ نبات: {parts[2]}\n▫️ بلاد: {parts[3]}\n\n▫️ النقاط: {points}"
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
        
        return {
            'response': TextSendMessage(text="تأكد من كتابة 4 كلمات مفصولة بفواصل"),
            'points': 0,
            'correct': False,
            'won': False,
            'game_over': False
        }
    
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
