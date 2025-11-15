from linebot.models import TextSendMessage, FlexSendMessage
import random, re

class SongGame:
    def __init__(self, line_bot_api, use_ai=False, ask_ai=None):
        self.line_bot_api = line_bot_api
        self.use_ai = use_ai
        self.ask_ai = ask_ai
        self.current_song = None
        self.question_number = 0
        self.total_questions = 5
        self.player_scores = {}
        self.hints_used = 0
        
        self.songs = [
            {"lyrics": "رجعت لي أيام الماضي معاك", "singer": "أم كلثوم"},
            {"lyrics": "جلست والخوف بعينيها تتأمل فنجاني", "singer": "عبد الحليم حافظ"},
            {"lyrics": "تملي معاك ولو حتى بعيد عني", "singer": "عمرو دياب"},
            {"lyrics": "يا مسافر وحدك", "singer": "محمد عبده"},
            {"lyrics": "قالوا إيه عليا", "singer": "تامر حسني"},
            {"lyrics": "حبيبي يا نور العين", "singer": "عمرو دياب"},
            {"lyrics": "على بالي", "singer": "شيرين"},
            {"lyrics": "قصاد عيني", "singer": "أحمد سعد"},
            {"lyrics": "بحبك وحشتني", "singer": "أصالة"},
            {"lyrics": "هو صحيح الهوى غلاب", "singer": "أم كلثوم"}
        ]
        random.shuffle(self.songs)
    
    def normalize(self, text):
        if not text: return ""
        text = text.strip().lower()
        text = text.replace('أ','ا').replace('إ','ا').replace('آ','ا')
        text = text.replace('ؤ','و').replace('ئ','ي').replace('ء','')
        text = text.replace('ة','ه').replace('ى','ي')
        text = re.sub(r'[\u064B-\u065F]', '', text)
        return re.sub(r'\s+', '', text)
    
    def start_game(self):
        self.question_number = 0
        self.player_scores = {}
        return self._next_question()
    
    def _next_question(self):
        self.question_number += 1
        self.current_song = self.songs[(self.question_number - 1) % len(self.songs)]
        self.hints_used = 0
        
        return FlexSendMessage(alt_text="لعبة الأغنية", contents={
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "box", "layout": "vertical", "contents": [
                        {"type": "text", "text": "🎵 لعبة الأغنية", "size": "lg", "weight": "bold", "color": "#FFFFFF", "align": "center"}
                    ], "backgroundColor": "#555555", "cornerRadius": "10px", "paddingAll": "16px"},
                    {"type": "text", "text": f"سؤال {self.question_number} من {self.total_questions}", "size": "sm", "color": "#8E8E93", "align": "center", "margin": "md"},
                    {"type": "separator", "margin": "md", "color": "#F2F2F7"},
                    {"type": "text", "text": self.current_song['lyrics'], "size": "md", "weight": "bold", "color": "#1C1C1E", "align": "center", "margin": "md", "wrap": True},
                    {"type": "text", "text": "من المغني؟", "size": "sm", "color": "#8E8E93", "align": "center", "margin": "sm"}
                ],
                "backgroundColor": "#FFFFFF",
                "paddingAll": "20px"
            },
            "footer": {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {"type": "button", "action": {"type": "message", "label": "▫️ لمح", "text": "لمح"}, "style": "secondary", "height": "sm"},
                    {"type": "button", "action": {"type": "message", "label": "▫️ جاوب", "text": "جاوب"}, "style": "secondary", "height": "sm"}
                ],
                "spacing": "sm",
                "backgroundColor": "#F2F2F7",
                "paddingAll": "12px"
            }
        })
    
    def next_question(self):
        return self._next_question() if self.question_number < self.total_questions else None
    
    def check_answer(self, text, user_id, name):
        if not self.current_song:
            return None
        
        text_lower = text.strip().lower()
        
        # تلميح
        if text_lower in ['لمح', 'تلميح']:
            if self.hints_used == 0:
                singer = self.current_song['singer']
                self.hints_used += 1
                return {
                    'correct': False,
                    'response': TextSendMessage(text=f"▫️ يبدأ بحرف: {singer[0]}\n▫️ عدد الحروف: {len(singer)}")
                }
            return {'correct': False, 'response': TextSendMessage(text="▫️ استخدمت التلميح")}
        
        # الحل
        if text_lower in ['جاوب', 'الجواب', 'الحل']:
            if self.question_number < self.total_questions:
                return {
                    'correct': False,
                    'response': TextSendMessage(text=f"▪️ الإجابة: {self.current_song['singer']}\n\n▫️ {self.current_song['lyrics']}"),
                    'next_question': True
                }
            return self._end_game()
        
        # إجابة صحيحة
        if self.normalize(text) == self.normalize(self.current_song['singer']) or self.normalize(self.current_song['singer']) in self.normalize(text):
            points = 10 - (self.hints_used * 2)
            
            if user_id not in self.player_scores:
                self.player_scores[user_id] = {'name': name, 'score': 0}
            self.player_scores[user_id]['score'] += points
            
            if self.question_number < self.total_questions:
                return {
                    'correct': True,
                    'points': points,
                    'won': True,
                    'response': TextSendMessage(text=f"▪️ صحيح {name}\n\n▫️ {self.current_song['singer']}\n▫️ +{points} نقطة"),
                    'next_question': True
                }
            return self._end_game()
        
        return None
    
    def _end_game(self):
        if not self.player_scores:
            return {'game_over': True, 'response': TextSendMessage(text="▪️ انتهت اللعبة\n\n▫️ لم يشارك أحد")}
        
        sorted_players = sorted(self.player_scores.items(), key=lambda x: x[1]['score'], reverse=True)
        winner = sorted_players[0][1]
        
        score_items = []
        for i, (uid, data) in enumerate(sorted_players, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}"
            bg = "#F2F2F7" if i == 1 else "#FAFAFA"
            
            score_items.append({
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {"type": "text", "text": emoji, "size": "md", "color": "#1C1C1E", "flex": 0, "weight": "bold"},
                    {"type": "text", "text": data['name'], "size": "sm", "color": "#1C1C1E", "flex": 3, "margin": "md", "wrap": True},
                    {"type": "text", "text": str(data['score']), "size": "md", "color": "#1C1C1E", "flex": 1, "align": "end", "weight": "bold"}
                ],
                "backgroundColor": bg,
                "cornerRadius": "8px",
                "paddingAll": "12px",
                "margin": "sm" if i > 1 else "none"
            })
        
        winner_card = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "🏆 انتهت اللعبة", "size": "xl", "weight": "bold", "color": "#1C1C1E", "align": "center"},
                    {"type": "separator", "margin": "md", "color": "#F2F2F7"},
                    {"type": "box", "layout": "vertical", "contents": [
                        {"type": "text", "text": "الفائز", "size": "sm", "color": "#8E8E93", "align": "center"},
                        {"type": "text", "text": winner['name'], "size": "xxl", "weight": "bold", "color": "#1C1C1E", "align": "center", "margin": "xs", "wrap": True},
                        {"type": "text", "text": f"{winner['score']} نقطة", "size": "md", "color": "#8E8E93", "align": "center", "margin": "xs"}
                    ], "margin": "md"},
                    {"type": "separator", "margin": "md", "color": "#F2F2F7"},
                    {"type": "text", "text": "النتائج النهائية", "size": "md", "weight": "bold", "color": "#1C1C1E", "margin": "md"},
                    {"type": "box", "layout": "vertical", "contents": score_items, "margin": "sm"}
                ],
                "backgroundColor": "#FFFFFF",
                "paddingAll": "20px"
            }
        }
        
        return {'game_over': True, 'won': True, 'winner_card': winner_card, 'points': winner['score']}
