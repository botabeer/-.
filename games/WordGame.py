# --- لعبة أطول كلمة ---
class WordGame:
    def __init__(self):
        self.categories = ["حيوان","نبات","بلد","طعام"]
        self.current_category, self.current_q, self.max_q, self.scores, self.answers = None, 0, 5, {}, {}

    def start_game(self):
        self.current_q, self.scores, self.answers = 1, {}, {}
        return self.next_question()

    def next_question(self):
        if self.current_q > self.max_q: return None
        self.current_category = random.choice(self.categories)
        self.answers = {}
        return FlexSendMessage(
            alt_text=f"الجولة {self.current_q}",
            contents=create_game_card(
                game_header("أطول كلمة",f"الجولة {self.current_q}/{self.max_q}"),
                [
                    glass_box([
                        {"type":"text","text":"اكتب أطول كلمة من فئة","size":"sm","color":C['text2'],"align":"center"},
                        {"type":"text","text":self.current_category,"size":"4xl","weight":"bold","color":C['glow'],"align":"center","margin":"md"}
                    ],"32px"),
                    progress_bar(self.current_q, self.max_q)
                ]
            )
        )

    def check_answer(self, text, user_id, name):
        if user_id in self.answers:
            return None
        word = text.strip()
        if len(word) >= 3:
            self.answers[user_id] = {'name':name,'word':word,'length':len(word)}
            # بعد وصول 3 إجابات يتم تحديد الفائز
            if len(self.answers) >= 3:
                winner = max(self.answers.items(), key=lambda x: x[1]['length'])
                points = 3
                self.current_q += 1
                if winner[0] not in self.scores: self.scores[winner[0]] = {'name':winner[1]['name'],'score':0}
                self.scores[winner[0]]['score'] += points
                return {
                    'response':FlexSendMessage(
                        alt_text="الفائز",
                        contents=create_game_card(
                            game_header("الفائز","أطول كلمة"),
                            [
                                glass_box([
                                    {"type":"text","text":winner[1]['name'],"size":"xl","weight":"bold","color":C['text'],"align":"center"},
                                    {"type":"text","text":winner[1]['word'],"size":"3xl","color":C['glow'],"align":"center","margin":"md","weight":"bold"},
                                    {"type":"text","text":f"{winner[1]['length']} حرف - +{points} نقطة","size":"lg","color":C['cyan'],"align":"center","margin":"md"}
                                ],"28px")
                            ]
                        )
                    ),
                    'correct':True,
                    'points':points,
                    'next_question':self.current_q<=self.max_q
                }
            return {'response':TextSendMessage(text=f"تم تسجيل: {word} ({len(word)} حرف)"),'correct':True}
        return None
