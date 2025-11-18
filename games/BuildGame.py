from linebot.models import TextSendMessage, FlexSendMessage
import random, re

# --- لعبة تكوين الكلمات ---
class BuildGame:
    def __init__(self):
        self.letter_sets = [
            {"letters":"ق م ر ي ل ن","words":["قمر","ليل","مرق","ريم","نيل","قرن"]},
            {"letters":"ن ج م س و ر","words":["نجم","نجوم","سور","نور","سمر","رسم"]}
        ]
        self.current_letters, self.valid_words, self.used = [], set(), set()
        self.current_q, self.max_q, self.words_needed, self.scores, self.hints_used = 1, 5, 3, {}, 0

    def start_game(self):
        self.current_q, self.scores = 1, {}
        return self.next_question()

    def next_question(self):
        if self.current_q > self.max_q: return None
        letter_set = random.choice(self.letter_sets)
        self.current_letters = letter_set['letters'].split()
        self.valid_words = set(letter_set['words'])
        random.shuffle(self.current_letters)
        self.used, self.hints_used = set(), 0

        letter_boxes = [
            {"type":"box","layout":"vertical","contents":[{"type":"text","text":letter,"size":"xxl","weight":"bold","color":C['glow'],"align":"center"}],
             "backgroundColor":C['card'],"cornerRadius":"16px","width":"55px","height":"60px","justifyContent":"center","borderWidth":"2px","borderColor":C['border']}
            for letter in self.current_letters
        ]

        row1, row2 = letter_boxes[:3], letter_boxes[3:]

        return FlexSendMessage(
            alt_text=f"الجولة {self.current_q}",
            contents=create_game_card(
                game_header("تكوين الكلمات",f"الجولة {self.current_q}/{self.max_q}"),
                [
                    {"type":"box","layout":"vertical","contents":[
                        {"type":"box","layout":"horizontal","contents":row1,"spacing":"sm","justifyContent":"center"},
                        {"type":"box","layout":"horizontal","contents":row2,"spacing":"sm","justifyContent":"center","margin":"sm"}
                    ],"margin":"lg"},
                    glass_box([{"type":"text","text":f"كوّن {self.words_needed} كلمات صحيحة","size":"sm","color":C['text'],"align":"center","wrap":True}],"16px"),
                    progress_bar(self.current_q, self.max_q)
                ],
                [btn("لمح","لمح"),btn("جاوب","جاوب")]
            )
        )

    def check_answer(self, text, user_id, name):
        ans = text.strip().lower()

        if ans in ['لمح','تلميح']:
            if self.hints_used > 0: return {'response':TextSendMessage(text="تم استخدام التلميح"),'correct':False}
            self.hints_used = 1
            example = random.choice(list(self.valid_words))
            hint = example[0] + " " + "_ " * (len(example) - 1)
            return {'response':FlexSendMessage(
                alt_text="تلميح",
                contents=create_game_card(
                    game_header("تلميح","الحرف الأول + عدد الحروف"),
                    [glass_box([{"type":"text","text":hint,"size":"3xl","weight":"bold","color":C['glow'],"align":"center","letterSpacing":"6px"}],"28px")]
                )
            ),'correct':False}

        if ans in ['جاوب','الحل']:
            suggestions = sorted(self.valid_words, key=len, reverse=True)[:4]
            self.current_q += 1
            return {'response':FlexSendMessage(
                alt_text="الحل",
                contents=create_game_card(
                    game_header("الحل","بعض الكلمات الصحيحة"),
                    [glass_box([{"type":"text","text":" • ".join(suggestions),"size":"lg","color":C['glow'],"weight":"bold","align":"center","wrap":True}],"24px")]
                )
            ),'correct':False,'next_question':self.current_q<=self.max_q}

        word = normalize_text(text)
        if word in self.used: return {'response':TextSendMessage(text=f"الكلمة '{text}' مستخدمة"),'correct':False}

        letters_copy = self.current_letters.copy()
        can_form = all(c in letters_copy and (letters_copy.remove(c) or True) for c in word)
        if not can_form: return {'response':TextSendMessage(text=f"لا يمكن تكوين '{text}'"),'correct':False}
        if len(word) < 2: return {'response':TextSendMessage(text="حرفين على الأقل"),'correct':False}
        if word not in {normalize_text(w) for w in self.valid_words}: return {'response':TextSendMessage(text=f"'{text}' ليست صحيحة"),'correct':False}

        self.used.add(word)
        points = 2 if not self.hints_used else 1
        if user_id not in self.scores: self.scores[user_id] = {'name':name,'score':0,'words':0}
        self.scores[user_id]['score'] += points
        self.scores[user_id]['words'] += 1

        if self.scores[user_id]['words'] >= self.words_needed:
            self.current_q += 1
            return {'response':FlexSendMessage(
                alt_text="أحسنت",
                contents=create_game_card(
                    game_header("أحسنت","أكملت الجولة"),
                    [glass_box([
                        {"type":"text","text":name,"size":"xl","weight":"bold","color":C['text'],"align":"center"},
                        {"type":"text","text":f"+{points} نقطة","size":"xxl","color":C['glow'],"align":"center","margin":"md","weight":"bold"}
                    ],"28px")]
                )
            ),'correct':True,'won_round':True,'next_question':self.current_q<=self.max_q}

        return {'response':TextSendMessage(text=f"'{text}' صحيحة! +{points}"),'correct':True}
