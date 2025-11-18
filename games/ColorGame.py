# --- لعبة تخمين اللون ---
class ColorGame:
    def __init__(self):
        self.colors = [
            {"name":"أحمر","hex":"#EF4444"},
            {"name":"أزرق","hex":"#3B82F6"},
            {"name":"أخضر","hex":"#10B981"},
            {"name":"أصفر","hex":"#FACC15"},
            {"name":"برتقالي","hex":"#F97316"},
            {"name":"بنفسجي","hex":"#8B5CF6"}
        ]
        self.current_color, self.current_q, self.max_q, self.scores, self.hints_used = None, 0, 5, {}, 0

    def start_game(self):
        self.current_q, self.scores = 1, {}
        return self.next_question()

    def next_question(self):
        if self.current_q > self.max_q: return None
        self.current_color = random.choice(self.colors)
        self.hints_used = 0
        return FlexSendMessage(
            alt_text=f"السؤال {self.current_q}",
            contents=create_game_card(
                game_header("تخمين اللون",f"السؤال {self.current_q}/{self.max_q}"),
                [
                    glass_box([
                        {"type":"text","text":"ما هذا اللون؟","size":"sm","color":C['text2'],"align":"center"},
                        {"type":"box","layout":"vertical","contents":[],"height":"140px","backgroundColor":self.current_color['hex'],
                         "cornerRadius":"20px","margin":"md","borderWidth":"3px","borderColor":"#ffffff30"}
                    ],"32px"),
                    progress_bar(self.current_q, self.max_q)
                ],
                [btn("لمح","لمح")]
            )
        )

    def check_answer(self, text, user_id, name):
        ans = text.strip().lower()
        correct_name = normalize_text(self.current_color['name'])
        if ans in ['لمح','تلميح']:
            if self.hints_used > 0: return {'response':TextSendMessage(text="تم استخدام التلميح"),'correct':False}
            self.hints_used = 1
            hint = self.current_color['name'][0] + " " + "_ " * (len(self.current_color['name']) - 1)
            return {
                'response':FlexSendMessage(
                    alt_text="تلميح",
                    contents=create_game_card(
                        game_header("تلميح","الحرف الأول"),
                        [
                            glass_box([{"type":"text","text":hint,"size":"3xl","color":C['glow'],
                                        "align":"center","weight":"bold","letterSpacing":"6px"}],"28px")
                        ]
                    )
                ),
                'correct':False
            }
        if normalize_text(text) == correct_name:
            points = 2 if self.hints_used == 0 else 1
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
                                {"type":"text","text":self.current_color['name'],"size":"3xl","color":self.current_color['hex'],
                                 "align":"center","margin":"md","weight":"bold"},
                                {"type":"text","text":f"+{points} نقطة","size":"xxl","color":C['glow'],"align":"center","margin":"md","weight":"bold"}
                            ],"28px")
                        ]
                    )
                ),
                'correct':True,
                'points':points,
                'next_question':self.current_q <= self.max_q
            }
        return None
