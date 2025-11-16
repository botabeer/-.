import random
import re
from linebot.models import TextSendMessage, FlexSendMessage

class LettersWordsGame:
    def __init__(self, line_bot_api, max_questions=5, words_per_question=3):
        self.line_bot_api = line_bot_api
        self.max_questions = max_questions
        self.words_per_question = words_per_question
        self.current_question = 1
        self.available_letters = []
        self.valid_words_set = set()
        self.used_words = set()
        self.players_scores = {}  # user_id: {"name": display_name, "score": points}
        self.players_words = {}   # user_id: عدد الكلمات المكتملة
        self.hint_used = False

        # ✅ مجموعات حروف وكلمات حقيقية
        self.letter_sets = [
            {"letters": "ق م ر ي ل ن",
             "words": ["قمر","ليل","مرق","ريم","نيل","قرن","ملي","مير","قيل","ليم","نمر","مرن"]},
            {"letters": "ن ج م س و ر",
             "words": ["نجم","نجوم","سور","نور","سمر","رسم","جور","نمر","جرس","سجن","مرج","رسوم","سمور","نسور"]},
            {"letters": "ب ح ر ي ن ل",
             "words": ["بحر","بحرين","بحري","حرب","نحل","نيل","لبن","حبل","نبيل","نبل","ربح","بين","حين"]},
            {"letters": "ك ت ب م ل و",
             "words": ["كتب","كتاب","مكتب","ملك","كمل","كلم","بلوت","موت","كوم","ملت","بكت","تكلم"]},
            {"letters": "ش ج ر ة ي ن",
             "words": ["شجر","شجرة","جرة","نشر","شرن","تين","جنة","جين","رجة","شين","شجن","جشن"]},
            {"letters": "س م ك ن ا ه",
             "words": ["سمك","سكن","سماء","سما","ماء","سمان","نام","سام","هام","سهم","اسم","امن","نهم","مهن"]},
            {"letters": "ع ي ن ر ب د",
             "words": ["عين","عربي","عرب","برد","عبد","بعد","دين","عيد","برع","عبر","رعد","عرين","بعير"]},
            {"letters": "د ر س م ح ل",
             "words": ["درس","مدرس","رسم","حلم","سلم","حرم","حرس","سحر","حمل","رحم","حسد","ملح","رمح"]},
            {"letters": "ط ل ع م و ب",
             "words": ["طلع","علم","طعم","عمل","طمع","بطل","طول","علب","موعد","معلم","طبع","بعل"]},
            {"letters": "ح ب ر ط ي ق",
             "words": ["حبر","حرب","طرب","طريق","قرب","طيب","قطر","حرق","بحر","قبر","حقب","ربح"]},
            {"letters": "ف ك ر ت ي ن",
             "words": ["فكر","فكري","تفكير","ركن","تين","فني","كفر","نير","فرن","فتن","ترف","كفن"]},
            {"letters": "ص و ر ة ح ب",
             "words": ["صورة","صور","بحر","حرب","صبر","حبر","وحش","بحة","حصر","روح","صحة","حوض"]},
            {"letters": "ج س م ا ل ن",
             "words": ["جسم","جمال","سلام","مجلس","جمل","سام","نام","مال","جان","لسان","سلم","ماس"]},
            {"letters": "خ ل ق ا ن ي",
             "words": ["خلق","خالق","اخلاق","خال","خيل","لقي","نقي","خان","نخيل","قلي","خيال"]},
            {"letters": "ذ ه ب و ن ي",
             "words": ["ذهب","ذهبي","نبي","بون","ذوب","وهن","نهب","ذنب","بيون","هون"]}
        ]

    def normalize_text(self, text):
        if not text:
            return ""
        text = text.strip().lower()
        text = re.sub(r'^ال', '', text)
        text = text.replace('أ','ا').replace('إ','ا').replace('آ','ا')
        text = text.replace('ؤ','و').replace('ئ','ي').replace('ء','')
        text = text.replace('ة','ه').replace('ى','ي')
        text = re.sub(r'[\u064B-\u065F]', '', text)
        text = re.sub(r'\s+','', text)
        return text

    def start_game(self):
        self.current_question = 1
        self.players_scores = {}
        self.players_words = {}
        return self.next_question()

    def next_question(self):
        if self.current_question > self.max_questions:
            return self._end_game()
        letter_set = random.choice(self.letter_sets)
        self.available_letters = letter_set['letters'].split()
        self.valid_words_set = set(letter_set['words'])
        random.shuffle(self.available_letters)
        self.used_words.clear()
        self.hint_used = False
        self.players_words = {}
        letters_str = ' '.join(self.available_letters)
        return self.get_question_card(self.current_question, letters_str, self.words_per_question)

    # --- Flex Cards جاهزة لكل خطوة ---
    def get_question_card(self, question_num, letters, words_needed):
        letter_boxes = [{"type":"box","layout":"vertical","contents":[{"type":"text","text":l,"size":"xxl","weight":"bold","color":"#A78BFA","align":"center"}],"backgroundColor":"#1F2937","cornerRadius":"12px","width":"50px","height":"60px","justifyContent":"center","paddingAll":"8px","shadow":{"offsetX":"4px","offsetY":"4px","blur":"8px","color":"#000000"}} for l in letters.split()]
        first_row = letter_boxes[:3]
        second_row = letter_boxes[3:] if len(letter_boxes)>3 else []
        letters_display = {"type":"box","layout":"vertical","contents":[{"type":"box","layout":"horizontal","contents":first_row,"justifyContent":"center"}]}
        if second_row:
            letters_display["contents"].append({"type":"box","layout":"horizontal","contents":second_row,"justifyContent":"center"})
        bubble = {"type":"bubble","body":{"type":"box","layout":"vertical","contents":[{"type":"text","text":f"▪️ تكوين كلمات - سؤال {question_num}","size":"xl","weight":"bold","color":"#F3F4F6","align":"center"},{"type":"separator","margin":"lg","color":"#374151"},{"type":"text","text":f"كوّن {words_needed} كلمات صحيحة من الحروف","size":"sm","color":"#D1D5DB","align":"center","wrap":True},letters_display],"backgroundColor":"#0F172A","paddingAll":"20px"},"footer":{"type":"box","layout":"horizontal","contents":[{"type":"button","action":{"type":"message","label":"💡 تلميح","text":"لمح"},"style":"secondary","color":"#6366F1"},{"type":"button","action":{"type":"message","label":"✓ الحل","text":"جاوب"},"style":"secondary","color":"#8B5CF6"}],"backgroundColor":"#1E293B","paddingAll":"16px"}}
        return FlexSendMessage(alt_text=f"سؤال {question_num}", contents=bubble)

    def get_hint(self):
        if self.hint_used:
            return {"response":TextSendMessage(text="▫️ تم استخدام التلميح مسبقاً"), "points":0}
        self.hint_used = True
        example_word = random.choice(list(self.valid_words_set))
        first_letter = example_word[0]
        word_length = len(example_word)
        hint_pattern = first_letter + " " + " ".join(["_"]*(word_length-1))
        bubble = {"type":"bubble","body":{"type":"box","layout":"vertical","contents":[{"type":"text","text":"💡 تلميح","size":"xl","weight":"bold","color":"#FCD34D","align":"center"},{"type":"separator","margin":"lg","color":"#374151"},{"type":"text","text":f"أول حرف: {hint_pattern}","size":"xxl","weight":"bold","color":"#A78BFA","align":"center"},{"type":"text","text":f"عدد الحروف: {word_length}","size":"sm","color":"#10B981","align":"center"},{"type":"text","text":"⚠️ النقاط ستنخفض إلى نصف القيمة","size":"xxs","color":"#F59E0B","align":"center"}],"backgroundColor":"#0F172A","paddingAll":"20px"}}
        return {"response":FlexSendMessage(alt_text="تلميح", contents=bubble), "points":-1}

    def show_answer(self):
        suggestions = sorted(self.valid_words_set,key=len,reverse=True)[:4]
        bubble = {"type":"bubble","body":{"type":"box","layout":"vertical","contents":[{"type":"text","text":"✓ الحل","size":"xl","weight":"bold","color":"#10B981","align":"center"},{"type":"separator","margin":"lg","color":"#374151"},{"type":"text","text":"بعض الكلمات الصحيحة:","size":"sm","color":"#9CA3AF","margin":"lg"},{"type":"text","text"," ، ".join(suggestions),"size":"lg","weight":"bold","color":"#A78BFA","align":"center"}],"backgroundColor":"#0F172A","paddingAll":"20px"}}
        self.current_question +=1
        if self.current_question>self.max_questions:
            return self._end_game()
        return {"response":FlexSendMessage(alt_text="الحل", contents=bubble)}

    def _end_game(self):
        if not self.players_scores:
            return {"response":TextSendMessage(text="▫️ انتهت اللعبة\n\nلم يشارك أحد")}
        sorted_players = sorted(self.players_scores.items(),key=lambda x:x[1]['score'],reverse=True)
        lines = [f"🥇 {data['name']}: {data['score']} نقطة" if i==0 else f"🥈 {data['name']}: {data['score']} نقطة" if i==1 else f"🥉 {data['name']}: {data['score']} نقطة" if i==2 else f"{i+1}. {data['name']}: {data['score']} نقطة" for i,(uid,data) in enumerate(sorted_players)]
        bubble = {"type":"bubble","body":{"type":"box","layout":"vertical","contents":[{"type":"text","text":"🏆 النتائج النهائية","size":"xl","weight":"bold","color":"#FCD34D","align":"center"},{"type":"separator","margin":"lg","color":"#374151"}]+[{"type":"text","text":line,"size":"md","color":"#F3F4F6","align":"center"} for line in lines],"backgroundColor":"#0F172A","paddingAll":"20px"}}
        return {"response":FlexSendMessage(alt_text="نهاية اللعبة", contents=bubble)}

    def can_form_word(self, word, letters):
        letters_list = letters.copy()
        for c in word:
            if c in letters_list:
                letters_list.remove(c)
            else:
                return False
        return True

    def check_answer(self, answer, user_id=None, display_name=None):
        ans = self.normalize_text(answer)
        if ans in ['لمح','تلميح','hint']:
            return self.get_hint()
        if ans in ['جاوب','الحل','answer']:
            return self.show_answer()
        if ans in self.used_words:
            return {"response":TextSendMessage(text=f"▫️ الكلمة '{answer}' مستخدمة مسبقاً")}
        if not self.can_form_word(ans,self.available_letters):
            return {"response":TextSendMessage(text=f"▫️ لا يمكن تكوين '{answer}' من الحروف المتاحة")}
        if len(ans)<2:
            return {"response":TextSendMessage(text="▫️ الكلمة يجب أن تكون حرفين على الأقل")}
        normalized_valid = {self.normalize_text(w) for w in self.valid_words_set}
        if ans not in normalized_valid:
            return {"response":TextSendMessage(text=f"▫️ '{answer}' ليست من الكلمات المطلوبة")}
        # ✅ الإجابة صحيحة
        self.used_words.add(ans)
        if user_id not in self.players_words:
            self.players_words[user_id] = 0
        self.players_words[user_id] += 1
        points = 2 if not self.hint_used else 1
        if user_id not in self.players_scores:
            self.players_scores[user_id] = {"name": display_name, "score": 0}
        self.players_scores[user_id]['score'] += points
        remaining = self.words_per_question - self.players_words[user_id]
        if remaining<=0:
            self.current_question +=1
            return {"response":TextSendMessage(text=f"🎉 {display_name} أكمل جميع الكلمات! +{points} نقطة")}
        return {"response":TextSendMessage(text=f"✓ صحيح {display_name} +{points} نقطة\nمتبقي {remaining} كلمة")}
