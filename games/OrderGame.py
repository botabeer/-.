# --- لعبة ترتيب الحروف ---
class OrderGame:
    def __init__(self):
        self.words = ["مدرسة","حديقة","كتاب","طائرة"]
        self.current_word, self.shuffled, self.current_q, self.max_q, self.scores = None, None, 0, 5, {}

    def start_game(self):
        self.current_q, self.scores = 1, {}
        return self.next_question()

    def next_question(self):
        if self.current_q > self.max_q: return None
        self.current_word = random.choice(self.words)
        letters = list(self.current_word)
        random.shuffle(letters)
        self.shuffled = ''.join(letters)

        return FlexSendMessage(
            alt_text=f"السؤال {self.current_q}",
            contents=create_game_card(
                game_header("ترتيب الحروف",f"السؤال {self.current_q}/{self.max_q}"),
                [
                    glass_box([
                        {"type":"text","text":"رتب الحروف","size":"sm","color":C['text2'],"align":"center"},
                        {"type":"text","text":self.shuffled,"size":"4xl","weight":"bold","color":C['glow'],"align":"center","margin":"md","letterSpacing":"10px"}
                    ],"32px"),
                    progress_bar(self.current_q, self.max_q)
                ]
            )
        )

    def check_answer(self, text, user_id, name):
        if normalize_text(text) == normalize_text(self.current_word):
            points = 2
            self.current_q += 1
            if user_id not in self.scores: self.scores[user_id] = {'name':name,'score':0}
            self.scores[user_id]['score'] += points
            return {
                'response':FlexSendMessage(
                    alt_text="صحيح",
                    contents=create_game_card(
                        game_header("صحيح","ممتاز"),
                        [
                            glass_box([
                                {"type":"text","text":name,"size":"xl","weight":"bold","color":C['text'],"align":"center"},
                                {"type":"text","text":self.current_word,"size":"3xl","color":C['glow'],"align":"center","margin":"md","weight":"bold"},
                                {"type":"text","text":f"+{points} نقطة","size":"xxl","color":C['cyan'],"align":"center","margin":"md","weight":"bold"}
                            ],"28px")
                        ]
                    )
                ),
                'correct':True,
                'points':points,
                'next_question':self.current_q<=self.max_q
            }
        return None
