from linebot.models import TextSendMessage, FlexSendMessage
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
        self.question_number = 0
        self.total_questions = 5
        self.player_scores = {}
        
        self.all_songs = [
            {"lyrics": "رجعت لي أيام الماضي معاك", "singer": "أم كلثوم"},
            {"lyrics": "جلست والخوف بعينيها تتأمل فنجاني", "singer": "عبد الحليم حافظ"},
            {"lyrics": "تملي معاك ولو حتى بعيد عني", "singer": "عمرو دياب"},
            {"lyrics": "كل ده كان ليه", "singer": "عمرو دياب"},
            {"lyrics": "انا كل ما اقول التوبة", "singer": "محمد عبده"},
            {"lyrics": "يا طيبة يا أهل الطيبة", "singer": "محمد عبده"},
            {"lyrics": "احلف بسماها وأرضها", "singer": "راشد الماجد"},
            {"lyrics": "ودي ارجع طفل", "singer": "ماجد المهندس"},
            {"lyrics": "بعيش وحدي في دنيا تانية", "singer": "وردة الجزائرية"},
            {"lyrics": "حبيتك بالتلاتة", "singer": "شيرين عبد الوهاب"}
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
        self.question_number = 0
        self.player_scores = {}
        return self._next_question()
    
    def _next_question(self):
        self.question_number += 1
        self.current_song = random.choice(self.all_songs)
        self.answered = False
        
        # بطاقة Flex - iOS Style نظيف
        card = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "لعبة الأغنية",
                        "size": "xl",
                        "weight": "bold",
                        "color": "#1C1C1E",
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": f"سؤال {self.question_number} من {self.total_questions}",
                        "size": "sm",
                        "color": "#8E8E93",
                        "align": "center",
                        "margin": "sm"
                    },
                    {
                        "type": "separator",
                        "margin": "lg",
                        "color": "#F2F2F7"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": self.current_song['lyrics'],
                                "size": "md",
                                "color": "#1C1C1E",
                                "align": "center",
                                "wrap": True,
                                "weight": "bold"
                            },
                            {
                                "type": "text",
                                "text": "من المغني؟",
                                "size": "sm",
                                "color": "#8E8E93",
                                "align": "center",
                                "margin": "md"
                            }
                        ],
                        "backgroundColor": "#F2F2F7",
                        "cornerRadius": "12px",
                        "paddingAll": "16px",
                        "margin": "lg"
                    }
                ],
                "paddingAll": "20px",
                "backgroundColor": "#FFFFFF"
            },
            "footer": {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "button",
                        "action": {"type": "message", "label": "▫️ لمح", "text": "لمح"},
                        "style": "secondary",
                        "height": "sm",
                        "color": "#8E8E93"
                    },
                    {
                        "type": "button",
                        "action": {"type": "message", "label": "▫️ جاوب", "text": "جاوب"},
                        "style": "secondary",
                        "height": "sm",
                        "color": "#8E8E93"
                    }
                ],
                "spacing": "sm",
                "backgroundColor": "#F2F2F7",
                "paddingAll": "12px"
            }
        }
        
        return FlexSendMessage(alt_text="لعبة الأغنية", contents=card)
    
    def next_question(self):
        if self.question_number < self.total_questions:
            return self._next_question()
        return None
    
    def check_answer(self, text, user_id, display_name):
        if self.answered:
            return None
        
        text_normalized = self.normalize_text(text)
        singer_normalized = self.normalize_text(self.current_song['singer'])
        
        # تلميح محسّن - نظام النقاط الجديد
        if text in ['لمح', 'تلميح', 'hint']:
            singer = self.current_song['singer']
            
            hint_text = f"▫️ تلميح\n\nيبدأ بحرف: {singer[0]}\nعدد الحروف: {len(singer)}"
            
            # خصم نقطة
            if user_id not in self.player_scores:
                self.player_scores[user_id] = {'name': display_name, 'score': 0}
            self.player_scores[user_id]['score'] -= 1
            
            return {
                'correct': False,
                'points': -1,
                'response': TextSendMessage(text=hint_text)
            }
        
        # عرض الحل - 0 نقاط
        if text in ['جاوب', 'الجواب', 'الحل', 'answer']:
            self.answered = True
            
            if self.question_number < self.total_questions:
                return {
                    'correct': False,
                    'points': 0,
                    'response': TextSendMessage(
                        text=f"▫️ الإجابة الصحيحة\n\n{self.current_song['singer']}"
                    ),
                    'next_question': True
                }
            else:
                return self._end_game()
        
        # إجابة صحيحة - نظام النقاط الجديد +2
        if text_normalized == singer_normalized or singer_normalized in text_normalized:
            self.answered = True
            points = 2  # النقاط الجديدة
            
            if user_id not in self.player_scores:
                self.player_scores[user_id] = {'name': display_name, 'score': 0}
            self.player_scores[user_id]['score'] += points
            
            if self.question_number < self.total_questions:
                return {
                    'correct': True,
                    'points': points,
                    'won': True,
                    'response': TextSendMessage(
                        text=f"▫️ إجابة صحيحة {display_name}\n\n{self.current_song['singer']}\n\n+{points} نقطة"
                    ),
                    'next_question': True
                }
            else:
                return self._end_game()
        
        return None
    
    def _end_game(self):
        if not self.player_scores:
            return {
                'game_over': True,
                'response': TextSendMessage(text="انتهت اللعبة\n\nلم يشارك أحد")
            }
        
        sorted_players = sorted(
            self.player_scores.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )
        
        winner_id, winner_data = sorted_players[0]
        winner_name = winner_data['name']
        winner_score = winner_data['score']
        
        # بطاقة الفائز - iOS Style
        winner_card = self._create_winner_card(winner_name, winner_score, sorted_players)
        
        return {
            'game_over': True,
            'won': True,
            'winner_card': winner_card,
            'points': winner_score
        }
    
    def _create_winner_card(self, winner_name, winner_score, all_players):
        score_items = []
        for i, (uid, data) in enumerate(all_players, 1):
            if i == 1:
                rank_emoji = "🥇"
                bg_color = "#F2F2F7"
            elif i == 2:
                rank_emoji = "🥈"
                bg_color = "#F2F2F7"
            elif i == 3:
                rank_emoji = "🥉"
                bg_color = "#F2F2F7"
            else:
                rank_emoji = f"{i}"
                bg_color = "#FFFFFF"
            
            score_items.append({
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {"type": "text", "text": rank_emoji, "size": "md", "color": "#1C1C1E", "flex": 0, "weight": "bold"},
                    {"type": "text", "text": data['name'], "size": "sm", "color": "#1C1C1E", "flex": 3, "margin": "md", "wrap": True},
                    {"type": "text", "text": str(data['score']), "size": "md", "color": "#1C1C1E", "flex": 1, "align": "end", "weight": "bold"}
                ],
                "backgroundColor": bg_color,
                "cornerRadius": "12px",
                "paddingAll": "12px",
                "margin": "sm" if i > 1 else "md"
            })
        
        return {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🏆",
                        "size": "xxl",
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": "انتهت اللعبة",
                        "size": "xl",
                        "weight": "bold",
                        "color": "#1C1C1E",
                        "align": "center",
                        "margin": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "xl",
                        "color": "#F2F2F7"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "الفائز",
                                "size": "sm",
                                "color": "#8E8E93",
                                "align": "center"
                            },
                            {
                                "type": "text",
                                "text": winner_name,
                                "size": "xl",
                                "weight": "bold",
                                "color": "#1C1C1E",
                                "align": "center",
                                "margin": "sm",
                                "wrap": True
                            },
                            {
                                "type": "text",
                                "text": f"{winner_score} نقطة",
                                "size": "md",
                                "color": "#8E8E93",
                                "align": "center",
                                "margin": "sm"
                            }
                        ],
                        "margin": "xl"
                    },
                    {
                        "type": "separator",
                        "margin": "xl",
                        "color": "#F2F2F7"
                    },
                    {
                        "type": "text",
                        "text": "النتائج النهائية",
                        "size": "md",
                        "weight": "bold",
                        "color": "#1C1C1E",
                        "margin": "xl"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": score_items,
                        "margin": "sm"
                    }
                ],
                "backgroundColor": "#FFFFFF",
                "paddingAll": "20px"
            }
        }
