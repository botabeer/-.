import random
import re
from linebot.models import TextSendMessage, FlexSendMessage

class LettersWordsGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.current_question = 1
        self.max_questions = 10
        self.words_per_question = 3
        self.players_scores = {}
        self.players_words = {}
        self.hint_used = False
        self.available_letters = []
        self.valid_words_set = set()
        self.used_words = set()

        # ✅ 15 مجموعة حروف منطقية
        self.letter_sets = [
            {"letters":"ق م ر ي ل ن","words":["قمر","ليل","مرق","ريم","نيل","نمر"]},
            {"letters":"ن ج م س و ر","words":["نجم","نجوم","سور","نور","سمر","جرس"]},
            {"letters":"ب ح ر ي ن ل","words":["بحر","بحرين","نحل","نبيل","لبن","حرب"]},
            {"letters":"ك ت ب م ل و","words":["كتب","كتاب","مكتب","ملك","كمل","كلم"]},
            {"letters":"ش ج ر ة ي ن","words":["شجر","شجرة","جرة","نشر","تين","جنة"]},
            {"letters":"س م ك ن ا ه","words":["سمك","سكن","سماء","سما","ماء","سمان"]},
            {"letters":"ع ي ن ر ب د","words":["عين","عربي","عرب","برد","عبد","بعد"]},
            {"letters":"د ر س م ح ل","words":["درس","مدرس","رسم","حلم","سلم","حرم"]},
            {"letters":"ط ل ع م و ب","words":["طلع","علم","طعم","عمل","طمع","بطل"]},
            {"letters":"ح ب ر ط ي ق","words":["حبر","حرب","طرب","طريق","قرب","ربح"]},
            {"letters":"ف ك ر ت ي ن","words":["فكر","فكري","تفكير","ركن","تين","كفن"]},
            {"letters":"ص و ر ة ح ب","words":["صورة","صور","بحر","حرب","صبر","حبر"]},
            {"letters":"ج س م ا ل ن","words":["جسم","جمال","سلام","مجلس","جمل","ماس"]},
            {"letters":"خ ل ق ا ن ي","words":["خلق","خالق","اخلاق","خال","خيل","خيال"]},
            {"letters":"ذ ه ب و ن ي","words":["ذهب","ذهبي","نبي","بون","ذوب","وهن"]}
        ]

    def normalize_text(self, text):
        if not text: return ""
        text = text.strip().lower()
        text = re.sub(r'^ال','',text)
        text = text.replace('أ','ا').replace('إ','ا').replace('آ','ا')
        text = text.replace('ة','ه').replace('ى','ي')
        text = re.sub(r'[\u064B-\u065F]','',text)
        text = re.sub(r'\s+','',text)
        return text

    def start_game(self):
        self.current_question = 1
        self.players_scores = {}
        return self.next_question()

    def next_question(self):
        if self.current_question > self.max_questions:
            return self.end_game()
        letter_set = random.choice(self.letter_sets)
        self.available_letters = letter_set['letters'].split()
        self.valid_words_set = set(letter_set['words'])
        self.used_words.clear()
        self.hint_used = False
        self.players_words = {}
        letters_str = ' '.join(self.available_letters)
        return TextSendMessage(text=f"السؤال {self.current_question}/{self.max_questions}\nكوّن {self.words_per_question} كلمات من هذه الحروف:\n{letters_str}")

    def get_hint(self):
        if self.hint_used:
            return TextSendMessage(text="▫️ تم استخدام التلميح مسبقاً")
        self.hint_used = True
        example_word = random.choice(list(self.valid_words_set))
        first_letter = example_word[0]
        word_length = len(example_word)
        pattern = first_letter + " " + " ".join(["_"]*(word_length-1))
        return TextSendMessage(text=f"💡 تلميح\nأول حرف: {first_letter}\nعدد الحروف: {word_length}\nالنقاط تصبح 1 بدل 2")

    def check_answer(self, answer, user_id):
        word = self.normalize_text(answer)
        if word in self.used_words:
            return TextSendMessage(text=f"▫️ الكلمة '{answer}' مستخدمة مسبقاً")
        # التحقق من إمكانية تكوين الكلمة
        letters_temp = self.available_letters.copy()
        for l in word:
            if l in letters_temp:
                letters_temp.remove(l)
            else:
                return TextSendMessage(text=f"▫️ لا يمكن تكوين '{answer}' من الحروف المتاحة")
        if word not in {self.normalize_text(w) for w in self.valid_words_set}:
            return TextSendMessage(text=f"▫️ '{answer}' ليست من الكلمات الصحيحة")
        # ✅ صحيح
        self.used_words.add(word)
        if user_id not in self.players_words:
            self.players_words[user_id] = 0
        self.players_words[user_id] += 1
        points = 2 if not self.hint_used else 1
        if user_id not in self.players_scores:
            self.players_scores[user_id] = 0
        self.players_scores[user_id] += points
        # تحقق إذا أكمل اللاعب الكلمات المطلوبة
        if self.players_words[user_id] >= self.words_per_question:
            self.current_question += 1
            return TextSendMessage(text=f"🎉 أحسنت! لقد أكملت {self.words_per_question} كلمات.\nالنقاط: {self.players_scores[user_id]}")
        else:
            remaining = self.words_per_question - self.players_words[user_id]
            return TextSendMessage(text=f"✓ صحيح! كلمة أخرى ({remaining} متبقية)")

    def show_answer(self):
        suggestions = sorted(self.valid_words_set, key=len)[:6]
        self.current_question += 1
        return TextSendMessage(text=f"✓ الحل: {', '.join(suggestions)}")

    def end_game(self):
        if not self.players_scores:
            return TextSendMessage(text="▫️ انتهت اللعبة\nلم يشارك أحد")
        sorted_scores = sorted(self.players_scores.items(), key=lambda x: x[1], reverse=True)
        msg = "🏆 النتائج النهائية:\n"
        for i, (uid, score) in enumerate(sorted_scores,1):
            medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
            msg += f"{medal} {uid}: {score} نقطة\n"
        return TextSendMessage(text=msg)
