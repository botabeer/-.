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
        
        # الأغاني الجديدة فقط
        self.all_songs = [
            {"lyrics": "أنا بلياك إذا أرمش إلك تنزل ألف دمعة", "singer": "ماجد المهندس"},
            {"lyrics": "يا بعدهم كلهم .. يا سراجي بينهم", "singer": "عبدالمجيد عبدالله"},
            {"lyrics": "أنا لحبيبي وحبيبي إلي", "singer": "فيروز"},
            {"lyrics": "قولي أحبك كي تزيد وسامتي", "singer": "كاظم الساهر"},
            {"lyrics": "كيف أبيّن لك شعوري دون ما أحكي", "singer": "عايض"},
            {"lyrics": "أريد الله يسامحني لان أذيت نفسي", "singer": "رحمة رياض"},
            {"lyrics": "جنّنت قلبي بحبٍ يلوي ذراعي", "singer": "ماجد المهندس"},
            {"lyrics": "واسِع خيالك إكتبه آنا بكذبك مُعجبه", "singer": "شمة حمدان"},
            {"lyrics": "خذني من ليلي لليلك", "singer": "عبادي الجوهر"},
            {"lyrics": "أنا عندي قلب واحد", "singer": "حسين الجسمي"},
            {"lyrics": "احس اني لقيتك بس عشان تضيع مني", "singer": "عبدالمجيد عبدالله"},
            {"lyrics": "قال الوداع و مقصده يجرح القلب", "singer": "راشد الماجد"},
            {"lyrics": "يا بنات يا بنات", "singer": "نانسي عجرم"},
            {"lyrics": "احبك موت كلمة مالها تفسير", "singer": "ماجد المهندس"},
            {"lyrics": "خلني مني طمني عليك", "singer": "نوال الكويتية"},
            {"lyrics": "رحت عني ما قويت جيت لك لاتردني", "singer": "عبدالمجيد عبدالله"},
            {"lyrics": "انسى هالعالم ولو هم يزعلون", "singer": "عباس ابراهيم"},
            {"lyrics": "مشاعر تشاور تودع تسافر", "singer": "شيرين"},
            {"lyrics": "جلست والخوف بعينيها تتأمل فنجاني", "singer": "عبد الحليم حافظ"},
            {"lyrics": "اسخر لك غلا وتشوفني مقصر", "singer": "عايض"},
            {"lyrics": "أنا استاهل وداع افضل وداع", "singer": "نوال الكويتية"},
            {"lyrics": "ظلمتني والله قويٍ يجازيك", "singer": "طلال مداح"},
            {"lyrics": "خلك من الي ما بقلبه وفا", "singer": "محمد عبده"},
            {"lyrics": "انتى ندمتى", "singer": "تامر عاشور"},
            {"lyrics": "احبك لو تكون حاضر .. احبك لو تكون هاجر", "singer": "عبادي الجوهر"},
            {"lyrics": "منوتي ليتك معي", "singer": "محمد عبده"},
            {"lyrics": "أنا أكثر شخص بالدنيا يحبك .. وأنتي ماتدرين", "singer": "راشد الماجد"},
            {"lyrics": "يردون .. قلت لازم يردون وين مني يروحون", "singer": "وليد الشامي"},
            {"lyrics": "نكتشف مر الحقيقة بعد ما يفوت الأوان", "singer": "أصاله نصري"},
            {"lyrics": "اسميحيلي يالغرام العف", "singer": "محمد عبده"},
            {"lyrics": "تدري كثر ماني من البعد مخنوق", "singer": "راشد الماجد"},
            {"lyrics": "احبه بس مو معناه اسمحله بيه يجرح", "singer": "أصيل هميم"},
            {"lyrics": "يمان حاولت الفراق وما قويت", "singer": "عبدالمجيد عبدالله"},
            {"lyrics": "بيرجع من هواي فيك", "singer": "أميمة طالب"},
            {"lyrics": "قلبك يسألني عنك طمني وينك", "singer": "وائل كفوري"},
            {"lyrics": "بردان أنا تكفى أبي احترق بدفا", "singer": "محمد عبده"},
            {"lyrics": "عايش لك .. ما عيش من دونك", "singer": "عايض"},
            {"lyrics": "انا مش بتاعت الكلام ده", "singer": "شيرين"},
            {"lyrics": "أنا احبك اكثر من اول", "singer": "راشد الماجد"},
            {"lyrics": "تملي معاك ولو حتى بعيد عني", "singer": "عمرو دياب"},
            {"lyrics": "ياليت العمر لو كان مليون مره", "singer": "راشد الماجد"},
            {"lyrics": "يا هي توجع كذبة اخباري تمام", "singer": "أميمة طالب"},
            {"lyrics": "أحبك ليه أنا مدري", "singer": "عبدالمجيد عبدالله"},
            {"lyrics": "يا مغرور جرحني غرورك", "singer": "أصالة"},
            {"lyrics": "سألوني الناس عنك يا حبيبي", "singer": "فيروز"},
            {"lyrics": "أنا ما عيش من دونك", "singer": "ماجد المهندس"},
            {"lyrics": "أمر الله أقوى أحبك والعقل واعي", "singer": "ماجد المهندس"}
        ]
        
        self.questions = []
        self.current_song = None
        self.hints_used = 0
        self.question_number = 0
        self.total_questions = 5
        self.player_scores = {}

    def start_game(self):
        self.questions = random.sample(self.all_songs, min(self.total_questions, len(self.all_songs)))
        self.question_number = 0
        self.player_scores = {}
        return self._next_question()

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
