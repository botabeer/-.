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
        
        # جميع الأغاني كمقاطع مستقلة
        self.all_songs = [
            {"lyrics": "رجعت لي أيام الماضي معاك", "singer": "أم كلثوم"},
            {"lyrics": "جلست والخوف بعينيها تتأمل فنجاني", "singer": "عبد الحليم حافظ"},
            {"lyrics": "تملي معاك ولو حتى بعيد عني", "singer": "عمرو دياب"},
            {"lyrics": "يا بنات يا بنات", "singer": "نانسي عجرم"},
            {"lyrics": "قولي أحبك كي تزيد وسامتي", "singer": "كاظم الساهر"},
            {"lyrics": "أنا لحبيبي وحبيبي إلي", "singer": "فيروز"},
            {"lyrics": "حبيبي يا كل الحياة اوعدني تبقى معايا", "singer": "تامر حسني"},
            {"lyrics": "قلبي بيسألني عنك دخلك طمني وينك", "singer": "وائل كفوري"},
            {"lyrics": "كيف أبيّن لك شعوري دون ما أحكي\nخابرك لمّاح لكن مالمحته\nلاتغرّك كثرة مزوحي وضحكي\nوالله إن قلبي لغيرك ما فتحته", "singer": "عايض"},
            {"lyrics": "اسخر لك غلا وتشوفني مقصر\nمعاك الحق ..\nوش الي يملي عيونك\nأنا ما عيش من دونك\nأحد ربي يجيبه لك حبيب\nويقدر يخونك", "singer": "عايض"},
            {"lyrics": "رحت عني ما قويت جيت لك لاتردني", "singer": "عبدالمجيد عبدالله"},
            {"lyrics": "خذني من ليلي لليلك", "singer": "عبادي الجوهر"},
            {"lyrics": "تدري كثر ماني من البعد مخنوق", "singer": "راشد الماجد"},
            {"lyrics": "انسى هالعالم ولو هم يزعلون", "singer": "عباس ابراهيم"},
            {"lyrics": "أنا عندي قلب واحد", "singer": "حسين الجسمي"},
            {"lyrics": "منوتي ليتك معي", "singer": "محمد عبده"},
            {"lyrics": "خلنا مني طمني عليك", "singer": "نوال الكويتية"},
            {"lyrics": "أحبك ليه أنا مدري", "singer": "عبدالمجيد عبدالله"},
            {"lyrics": "أمر الله أقوى أحبك والعقل واعي", "singer": "ماجد المهندس"},
            {"lyrics": "الحب يتعب من يدله والله في حبه بلاني", "singer": "راشد الماجد"},
            {"lyrics": "محد غيرك شغل عقلي شغل بالي", "singer": "وليد الشامي"},
            {"lyrics": "نكتشف مر الحقيقة بعد ما يفوت الأوان", "singer": "أصاله نصري"},
            {"lyrics": "يا هي توجع كذبة اخباري تمام", "singer": "أميمة طالب"},
            {"lyrics": "احس اني لقيتك بس عشان تضيع مني", "singer": "عبدالمجيد عبدالله"},
            {"lyrics": "بردان أنا تكفى أبي احترق بدفا لعيونك التحنان فعيونك المنفى", "singer": "محمد عبده"},
            {"lyrics": "أشوفك كل يوم وأروح وأقول نظرة ترد الروح أعيش فيها عشان بكره عشان ليلي إللي كلّه جروح", "singer": "محمد عبده"},
            {"lyrics": "في زحمة الناس صعبة حالتي فجأة اختلف لوني وضاعت خطوتي", "singer": "محمد عبده"},
            {"lyrics": "اختـلفنا مين يـحب الـثـاني أكثر واتـفــقــنــا إنـك أكــثــر وأنا أكـثـر", "singer": "محمد عبده"},
            {"lyrics": "لبيه يابو عيون وساع ما غيرك أحد ألبي له معذور لو صرت بك طماع من حبكم مالنا حيلة", "singer": "محمد عبده"},
            {"lyrics": "إسمحيلي يالغرام العف الـوجه السمـوح إن لزمت الصمت أو حتى لبست الأقنعة", "singer": "محمد عبده"},
            {"lyrics": "سألوني الناس عنّك يا حبيبي كتبوا المكاتيب وأخدها الهوا", "singer": "فيروز"},
            {"lyrics": "أنا لحبيبي وحبيبي إلي يا عصفورة بيضا لا بقى تسألي", "singer": "فيروز"},
            {"lyrics": "احبك موت كلمة مالها تفسير ولين اليوم ما ادري كيف افسرها", "singer": "ماجد المهندس"},
            {"lyrics": "جنّنت قلبي بحبٍ يلوي ذراعي", "singer": "ماجد المهندس"},
            {"lyrics": "بديت اطيب بديت احس بك عادي", "singer": "ماجد المهندس"},
            {"lyrics": "من اول نظره شفتك قلت هذا اللي تمنيته", "singer": "ماجد المهندس"},
            {"lyrics": "أنا بلياك إذا أرمش إلك تنزل ألف دمعة", "singer": "ماجد المهندس"},
            {"lyrics": "عطشان يا برق السما بموت من طول الغياب", "singer": "ماجد المهندس"},
            {"lyrics": "هيجيلي موجوع.. دموعه ف عينه تعبان", "singer": "تامر عاشور"},
            {"lyrics": "تيجى نتراهن إنّ هيجى اليوم وتقولى ان انتى ندمتى", "singer": "تامر عاشور"},
            {"lyrics": "خليني ف حضنك يا حبيبي ده ف حضنك بهدى وبرتاح", "singer": "تامر عاشور"},
            {"lyrics": "أريد الله يسامحني لان أذيت نفسي هواي طيبة قلبي أذتني تعبتج ياروحي وياي", "singer": "رحمة رياض"},
            {"lyrics": "كون نصير اني وياك نجمه بالسما وغيمه", "singer": "رحمة رياض"},
            {"lyrics": "على طاري الزعل والدمعتين الي على فرقاك", "singer": "أصيل هميم"},
            {"lyrics": "يشبهْك قلبي..كنّـك إلقلبي مخلوق", "singer": "أصيل هميم"},
            {"lyrics": "احبه بس مو معناه اسمحله بيه يجرح", "singer": "أصيل هميم"},
            {"lyrics": "المفروض اعوفك من زمان كون من ذاك الوكت من عليه تغيرت", "singer": "أصيل هميم"},
            {"lyrics": "ضعت منك وانهدم جسر التلاقي والسبب أوهام ظنك", "singer": "أميمة طالب"},
            {"lyrics": "بيان صادر من معاناة المحبة والسنين", "singer": "أميمة طالب"},
            {"lyrics": "انا ودي اذا ودك نعيد الماضي ونرجع", "singer": "رابح صقر"},
            {"lyrics": "مثل ما تحب ياروحي بلبّي رغبتك وأرحل", "singer": "رابح صقر"},
            {"lyrics": "كل مابلل مطر وصلك ثيابي ‎ارتوت كل المعاليق الحزينه", "singer": "رابح صقر"},
            {"lyrics": "يراودني شعور .. اني أحبك اكثر مْن اول", "singer": "راشد الماجد"},
            {"lyrics": "أنا أكثر شخص بالدنيا يحبك .. وأنتي ماتدرين", "singer": "راشد الماجد"},
            {"lyrics": "ليت العمر لو كان مليون مره", "singer": "راشد الماجد"},
            {"lyrics": "تلمّست لك عذر وتأملت بك ميعاد", "singer": "راشد الماجد"},
            {"lyrics": "عظيم إحساسي ومْن الشوق فيني شي ما ينقال", "singer": "راشد الماجد"},
            {"lyrics": "خذ راحتك .. ماعادها تفرق معي", "singer": "راشد الماجد"},
            {"lyrics": "قال الوداع و مقصده يجرح القلب", "singer": "راشد الماجد"},
            {"lyrics": "اللي لقى احبابه .. نسى اصحابه", "singer": "راشد الماجد"},
            {"lyrics": "واسِع خيالك إكتبه آنا بكذبك مُعجبه", "singer": "شمة حمدان"},
            {"lyrics": "مادريت .. إني أحبك مادريت لين رحت وشفت قلبي يتبعك", "singer": "شمة حمدان"},
            {"lyrics": "حبيته بيني وبين نفسي وماقولتلوش ع اللي في نفسي", "singer": "شيرين عبد الوهاب"},
            {"lyrics": "كلها غيرانة بتحقد والنفسية سواد", "singer": "شيرين عبد الوهاب"},
            {"lyrics": "مشاعر تشاور تودع تسافر مشاعر تموت و تحي مشاعر", "singer": "شيرين عبد الوهاب"},
            {"lyrics": "انا مش بتاعت الكلام ده انا كنت طول عمري جامدة", "singer": "شيرين عبد الوهاب"},
            {"lyrics": "مقادير يا قلبي العنا مقادير وش ذنبي انا", "singer": "طلال مداح"},
            {"lyrics": "ظلمتني والله قويٍ يجازيك", "singer": "طلال مداح"},
            {"lyrics": "فزيت من نومي اناديلك رد الصدى عنك", "singer": "ذكرى"},
            {"lyrics": "ابد علـى حطة يدك .. لو كان هذا يسعدك", "singer": "ذكرى"},
            {"lyrics": "انا لولا الغلا هو والمحبه والعيون السود", "singer": "فؤاد عبد الواحد"},
            {"lyrics": "كلمة ولو جبر خاطر .. والا سلام من بعيد", "singer": "عبادي الجوهر"},
            {"lyrics": "احبك لو تكون حاضر .. احبك لو تكون هاجر", "singer": "عبادي الجوهر"},
            {"lyrics": "إلحق عيني إلحق .. إلحق لايروح منك حبيبك", "singer": "وليد الشامي"},
            {"lyrics": "يردون .. قلت لازم يردون وين مني يروحون", "singer": "وليد الشامي"},
            {"lyrics": "ولهان انا ولهان و الوقت محسوب", "singer": "وليد الشامي"},
            {"lyrics": "اقولها كبر عن الدنيا حبيبي اشتقت لك", "singer": "وليد الشامي"},
            {"lyrics": "انا استاهل وداع افضل وداع يليق فيني و فيك", "singer": "نوال الكويتية"},
            {"lyrics": "خلنا مني .. طمني عليك ما انام الليل من خوفي عليك", "singer": "نوال الكويتية"},
            {"lyrics": "لقيت روحي بعد ما انا لقيتك", "singer": "نوال الكويتية"},
            {"lyrics": "غريبة الناس غريبة الدنيا ديّا", "singer": "وائل جسار"},
            {"lyrics": "اعذريني يوم زفافك مقدرتش افرح زيهم", "singer": "وائل جسار"},
            {"lyrics": "ماعاد يمديني ولا عاد يمديك قلوبنا حبت ولا استاذنتنا", "singer": "عبدالمجيد عبدالله"},
            {"lyrics": "يـا بعدهم كلهم .. يـا سراجي بينهم", "singer": "عبدالمجيد عبدالله"},
            {"lyrics": "حتى الكره احساس لا تبلاني انا ما اكرهك", "singer": "عبدالمجيد عبدالله"},
            {"lyrics": "استكثرك وقتي علي وغدابك عادة زماني كل ما طاب هوّن", "singer": "عبدالمجيد عبدالله"},
            {"lyrics": "ياما حاولت الفراق وما قويت", "singer": "عبدالمجيد عبدالله"}
        ]

        random.shuffle(self.all_songs)
        
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
                return {'response': TextSendMessage(text=hint), 'points': 0, 'correct': False, 'won': False, 'game_over': False}
            else:
                return {'response': TextSendMessage(text="استخدمت التلميح"), 'points': 0, 'correct': False, 'won': False, 'game_over': False}
        
        if answer_lower in ['جاوب', 'الجواب', 'answer']:
            response_text = f"▪️ الإجابة: {self.current_song['singer']}"
            
            if self.question_number < self.total_questions:
                return {'response': TextSendMessage(text=response_text), 'points': 0, 'correct': False, 'won': False, 'game_over': False, 'next_question': True}
            else:
                return self._end_game()
        
        if normalize_text(answer) == normalize_text(self.current_song['singer']):
            points = 20 - (self.hints_used * 5)
            
            if user_id not in self.player_scores:
                self.player_scores[user_id] = {'name': display_name, 'score': 0}
            self.player_scores[user_id]['score'] += points
            
            if self.question_number < self.total_questions:
                response_text = f"▪️ صحيح {display_name}\n\nالمغني: {self.current_song['singer']}\n\n▫️ النقاط: {points}"
                return {'response': TextSendMessage(text=response_text), 'points': points, 'correct': True, 'won': True, 'game_over': False, 'next_question': True}
            else:
                return self._end_game()
        
        return None

    def _end_game(self):
        if self.player_scores:
            sorted_players = sorted(self.player_scores.items(), key=lambda x: x[1]['score'], reverse=True)
            winner = sorted_players[0][1]
            all_scores = [(data['name'], data['score']) for uid, data in sorted_players]
            
            # افترض أن لديك دالة get_winner_card في app.py
            from app import get_winner_card
            winner_card = get_winner_card(winner['name'], winner['score'], all_scores)
            
            return {'points': 0, 'correct': False, 'won': True, 'game_over': True, 'winner_card': winner_card}
        else:
            return {'response': TextSendMessage(text="انتهت اللعبة"), 'points': 0, 'correct': False, 'won': False, 'game_over': True}
