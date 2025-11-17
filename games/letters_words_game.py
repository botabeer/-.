import random
import re
from linebot.models import TextSendMessage, FlexSendMessage

class LettersWordsGame:
    def __init__(self, line_bot_api, use_ai=False, ask_ai=None):
        self.line_bot_api = line_bot_api
        self.use_ai = use_ai
        self.ask_ai = ask_ai
        
        self.available_letters = []
        self.used_words = set()
        self.current_question = 1
        self.max_questions = 10
        self.players_scores = {}
        self.players_words = {}
        self.hint_used = False
        self.words_per_question = 3
        
        # مجموعات الحروف والكلمات الصحيحة
        self.letter_sets = [
            {"letters": "ق م ر ي ل ن", "words": ["قمر","ليل","مرق","ريم","نيل","نمر"]},
            {"letters": "ن ج م س و ر", "words": ["نجم","نجوم","سور","نور","سمر","جرس"]},
            {"letters": "ب ح ر ي ن ل", "words": ["بحر","بحرين","نحل","نبيل","لبن","حرب"]},
            {"letters": "ك ت ب م ل و", "words": ["كتب","كتاب","مكتب","ملك","كمل","كلم"]},
            {"letters": "ش ج ر ة ي ن", "words": ["شجر","شجرة","جرة","نشر","تين","جنة"]},
            {"letters": "س م ك ن ا ه", "words": ["سمك","سكن","سماء","ماء","سام","هام"]},
            {"letters": "ع ي ن ر ب د", "words": ["عين","عربي","عرب","برد","عبد","بعد"]},
            {"letters": "د ر س م ح ل", "words": ["درس","مدرس","رسم","حلم","سلم","حرم"]},
            {"letters": "ط ل ع م و ب", "words": ["طلع","علم","طعم","عمل","طمع","بطل"]},
            {"letters": "ح ب ر ط ي ق", "words": ["حبر","حرب","طرب","طريق","قرب","ربح"]},
            {"letters": "ف ك ر ت ي ن", "words": ["فكر","فكري","تفكير","ركن","تين","كفن"]},
            {"letters": "ص و ر ة ح ب", "words": ["صورة","صور","بحر","حرب","صبر","حبر"]},
            {"letters": "ج س م ا ل ن", "words": ["جسم","جمال","سلام","مجلس","جمل","ماس"]},
            {"letters": "خ ل ق ا ن ي", "words": ["خلق","خالق","اخلاق","خال","خيال","نقي"]},
            {"letters": "ذ ه ب و ن ي", "words": ["ذهب","ذهبي","نبي","بون","ذوب","وهن"]}
        ]

    def normalize_text(self, text):
        if not text:
            return ""
        text = text.strip().lower()
        text = re.sub(r'^ال', '', text)
        text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
        text = text.replace('ؤ', 'و').replace('ئ', 'ي').replace('ء', '')
        text = text.replace('ة', 'ه').replace('ى', 'ي')
        text = re.sub(r'[\u064B-\u065F]', '', text)
        text = re.sub(r'\s+', '', text)
        return text

    def get_neumorphism_card(self, title, question_num, letters_str, instruction):
        letters_list = letters_str.split()
        letter_boxes = [{
            "type": "box",
            "layout": "vertical",
            "contents":[{"type":"text","text":l,"size":"xl","weight":"bold","color":"#A78BFA","align":"center"}],
            "backgroundColor":"#1F2937","cornerRadius":"12px","width":"50px","height":"60px","justifyContent":"center","paddingAll":"8px"
        } for l in letters_list]
        
        first_row = letter_boxes[:3]
        second_row = letter_boxes[3:] if len(letter_boxes)>3 else []
        letters_display = {"type":"box","layout":"vertical","contents":[{"type":"box","layout":"horizontal","contents":first_row,"spacing":"md","justifyContent":"center"}]}
        if second_row:
            letters_display["contents"].append({"type":"box","layout":"horizontal","contents":second_row,"spacing":"md","justifyContent":"center"})
        
        bubble = {
            "type":"bubble",
            "body":{
                "type":"box",
                "layout":"vertical",
                "contents":[
                    {"type":"text","text":title,"size":"xl","weight":"bold","color":"#F3F4F6","align":"center"},
                    {"type":"text","text":f"سؤال {question_num} من {self.max_questions}","size":"sm","color":"#9CA3AF","align":"center","margin":"sm"},
                    letters_display,
                    {"type":"text","text":instruction,"size":"sm","color":"#D1D5DB","align":"center","wrap":True,"weight":"bold","margin":"md"}
                ],
                "backgroundColor":"#0F172A","paddingAll":"24px"
            }
        }
        return bubble

    # --- بداية اللعبة ---
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
        flex_card = self.get_neumorphism_card(
            title="▪️ لعبة تكوين الكلمات",
            question_num=self.current_question,
            letters_str=letters_str,
            instruction=f"كوّن {self.words_per_question} كلمات صحيحة من الحروف"
        )

        return {"response": FlexSendMessage(alt_text=f"سؤال {self.current_question}", contents=flex_card),
                "points": 0, "correct": False, "next_question": True}

    # --- التلميح ---
    def get_hint(self):
        if self.hint_used:
            return {"response": TextSendMessage(text="▫️ تم استخدام التلميح مسبقاً"),
                    "points": 0, "correct": False, "next_question": False}
        self.hint_used = True
        example_word = random.choice(list(self.valid_words_set))
        first_letter = example_word[0]
        word_length = len(example_word)
        pattern = first_letter + " " + " ".join(["_"]*(word_length-1))
        hint_msg = f"💡 تلميح\n{pattern}\nعدد الحروف: {word_length}\n⚠️ النقاط ستصبح 1 بدل 2"
        return {"response": TextSendMessage(text=hint_msg),
                "points": 0, "correct": False, "next_question": False}

    # --- عرض الإجابات ---
    def show_answer(self):
        suggestions = sorted(self.valid_words_set,key=len,reverse=True)[:4]
        return {"response": TextSendMessage(text=f"✓ بعض الكلمات الصحيحة:\n{', '.join(suggestions)}"),
                "points": 0, "correct": False, "next_question": False}

    # --- التحقق من الإجابة ---
    def check_answer(self, answer, user_id, display_name):
        answer_word = self.normalize_text(answer)
        if answer_word in ['لمح','تلميح','hint']:
            return self.get_hint()
        if answer_word in ['جاوب','الحل','answer']:
            return self.show_answer()
        if answer_word in self.used_words:
            return {"response": TextSendMessage(text=f"▫️ الكلمة '{answer}' مستخدمة مسبقاً"),
                    "points": 0, "correct": False, "next_question": False}

        letters_copy = self.available_letters.copy()
        for char in answer_word:
            if char in letters_copy:
                letters_copy.remove(char)
            else:
                return {"response": TextSendMessage(text=f"▫️ لا يمكن تكوين '{answer}' من الحروف: {' '.join(self.available_letters)}"),
                        "points": 0, "correct": False, "next_question": False}

        if len(answer_word)<2:
            return {"response": TextSendMessage(text="▫️ الكلمة يجب أن تكون حرفين على الأقل"),
                    "points": 0, "correct": False, "next_question": False}

        if answer_word not in {self.normalize_text(w) for w in self.valid_words_set}:
            return {"response": TextSendMessage(text=f"▫️ '{answer}' ليست كلمة صحيحة"),
                    "points": 0, "correct": False, "next_question": False}

        self.used_words.add(answer_word)
        if user_id not in self.players_words:
            self.players_words[user_id] = 0
        self.players_words[user_id] += 1

        points = 1 if self.hint_used else 2
        if display_name not in self.players_scores:
            self.players_scores[display_name] = {'score':0}
        self.players_scores[display_name]['score'] += points

        if self.players_words[user_id]>=self.words_per_question:
            self.current_question += 1
            if self.current_question > self.max_questions:
                resp = self._end_game()
                return {"response": resp, "points": points, "correct": True, "next_question": False}
            next_q = self.next_question()
            return {"response": TextSendMessage(text=f"✅ أحسنت يا {display_name}!\n{next_q['response'].alt_text}"),
                    "points": points, "correct": True, "next_question": True}
        else:
            remaining = self.words_per_question - self.players_words[user_id]
            return {"response": TextSendMessage(text=f"✅ صحيح يا {display_name}!\nكلمة أخرى ({remaining} متبقية)"),
                    "points": points, "correct": True, "next_question": False}

    # --- نهاية اللعبة ---
    def _end_game(self):
        if not self.players_scores:
            return TextSendMessage(text="▫️ انتهت اللعبة\nلم يشارك أحد")
        sorted_players = sorted(self.players_scores.items(),key=lambda x:x[1]['score'],reverse=True)
        msg="🏆 النتائج النهائية:\n"
        for i,(name,data) in enumerate(sorted_players[:5],1):
            emoji="🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
            msg+=f"{emoji} {name}: {data['score']} نقطة\n"
        winner=sorted_players[0]
        msg+=f"\n🎉 الفائز: {winner[0]}"
        return TextSendMessage(text=msg)
