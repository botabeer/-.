from linebot.models import TextSendMessage
import random
import re

class SongGame:
    def __init__(self, line_bot_api, use_ai=False, ask_ai=None):
        self.line_bot_api = line_bot_api
        self.use_ai = use_ai
        self.ask_ai = ask_ai
        self.current_song = None
        self.scores = {}
        self.answered = False

        # كل الأغاني مدموجة هنا، كل مقطع أصبح أغنية مستقلة
        self.all_songs = [
            {"lyrics": "رجعت لي أيام الماضي معاك", "singer": "أم كلثوم"},
            {"lyrics": "جلست والخوف بعينيها تتأمل فنجاني", "singer": "عبد الحليم حافظ"},
            {"lyrics": "تملي معاك ولو حتى بعيد عني", "singer": "عمرو دياب"},
            {"lyrics": "يا بنات يا بنات", "singer": "نانسي عجرم"},
            {"lyrics": "قولي أحبك كي تزيد وسامتي", "singer": "كاظم الساهر"},
            {"lyrics": "أنا لحبيبي وحبيبي إلي", "singer": "فيروز"},
            {"lyrics": "حبيبي يا كل الحياة اوعدني تبقى معايا", "singer": "تامر حسني"},
            {"lyrics": "قلبي بيسألني عنك دخلك طمني وينك", "singer": "وائل كفوري"},
            {"lyrics": "كيف أبيّن لك شعوري دون ما أحكي", "singer": "عايض"},
            {"lyrics": "اسخر لك غلا وتشوفني مقصر", "singer": "عايض"},
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
            {"lyrics": "نكتشف مر الحقيقة بعد ما يفوت الأوان", "singer": "أصالة نصري"},
            {"lyrics": "يا هي توجع كذبة اخباري تمام", "singer": "أميمة طالب"},
            {"lyrics": "احس اني لقيتك بس عشان تضيع مني", "singer": "عبدالمجيد عبدالله"},
            {"lyrics": "بردان أنا تكفى أبي احترق بدفا", "singer": "محمد عبده"},
            {"lyrics": "واسِع خيالك إكتبه آنا بكذبك مُعجبه", "singer": "شمة حمدان"},
            {"lyrics": "حبيته بيني وبين نفسي وماقولتلوش ع اللي في نفسي", "singer": "شيرين عبد الوهاب"},
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
            {"lyrics": "ياما حاولت الفراق وما قويت", "singer": "عبدالمجيد عبدالله"},
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
            {"lyrics": "المفروض اعوفك من زمان كون من ذاك الوكت من عليه تغيرت", "singer": "أصيل هميم"}
        ]

        random.shuffle(self.all_songs)

    def normalize_text(self, text):
        if not text:
            return ""
        text = text.strip().lower()
        text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
        text = text.replace('ؤ', 'و').replace('ئ', 'ي').replace('ء', '')
        text = text.replace('ة', 'ه').replace('ى', 'ي')
        text = re.sub(r'[\u064B-\u065F]', '', text)
        text = re.sub(r'\s+', '', text)
        return text

    def start_game(self):
        self.current_song = random.choice(self.all_songs)
        self.answered = False
        return TextSendMessage(text=f"▪️ لعبة الأغنية\n\nأغنية: {self.current_song['lyrics']}\n\nمن المغني؟")

    def check_answer(self, text, user_id, display_name):
        if self.answered:
            return None

        text_normalized = self.normalize_text(text)
        singer_normalized = self.normalize_text(self.current_song['singer'])

        if text in ['لمح', 'تلميح']:
            return {'correct': False, 'response': TextSendMessage(text=f"▪️ تلميح: {self.current_song['lyrics']}")}
        if text in ['جاوب', 'الجواب', 'الحل']:
            self.answered = True
            return {
                'correct': False,
                'game_over': True,
                'response': TextSendMessage(
                    text=f"▪️ الإجابة الصحيحة:\n{self.current_song['singer']}\nأغنية: {self.current_song['lyrics']}"
                )
            }
        if text_normalized == singer_normalized or singer_normalized in text_normalized:
            self.answered = True
            points = 10
            if user_id not in self.scores:
                self.scores[user_id] = {'name': display_name, 'score': 0}
            self.scores[user_id]['score'] += points
            return {
                'correct': True,
                'points': points,
                'won': True,
                'game_over': True,
                'response': TextSendMessage(
                    text=f"✔️ إجابة صحيحة يا {display_name}\n+{points} نقطة\nالمغني: {self.current_song['singer']}\nأغنية: {self.current_song['lyrics']}"
                )
            }
        return None
