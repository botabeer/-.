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
            # ... باقي الأغاني
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
        
        # بطاقة Flex محسّنة
        card = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "لعبة الأغنية",
                                "size": "lg",
                                "weight": "bold",
                                "color": "#FFFFFF",
                                "align": "center"
                            }
                        ],
                        "backgroundColor": "#555555",
                        "cornerRadius": "10px",
                        "paddingAll": "16px"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": f"سؤال {self.question_number} من {self.total_questions}",
                                "size": "sm",
                                "color": "#666666",
                                "align": "center",
                                "margin": "md"
                            },
                            {
                                "type": "separator",
                                "margin": "md",
                                "color": "#DDDDDD"
                            },
                            {
                                "type": "text",
                                "text": self.current_song['lyrics'],
                                "size": "md",
                                "weight": "bold",
                                "color": "#333333",
                                "align": "center",
                                "margin": "md",
                                "wrap": True
                            },
                            {
                                "type": "text",
                                "text": "من المغني؟",
                                "size": "sm",
                                "color": "#666666",
                                "align": "center",
                                "margin": "md"
                            }
                        ],
                        "margin": "md"
                    }
                ],
                "backgroundColor": "#FFFFFF",
                "paddingAll": "16px"
            },
            "footer": {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "button",
                        "action": {"type": "message", "label": "تلميح", "text": "لمح"},
                        "style": "secondary",
                        "height": "sm"
                    },
                    {
                        "type": "button",
                        "action": {"type": "message", "label": "الحل", "text": "جاوب"},
                        "style": "secondary",
                        "height": "sm"
                    }
                ],
                "spacing": "sm",
                "backgroundColor": "#F5F5F5",
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
        
        # تلميح محسّن
        if text in ['لمح', 'تلميح']:
            singer = self.current_song['singer']
            num_words = len(singer.split())
            
            hint_text = f"تلميح:\n\n• يبدأ بحرف: {singer[0]}\n• عدد الحروف: {len(singer)}\n• الاسم مكون من: {'كلمة واحدة' if num_words == 1 else f'{num_words} كلمات'}"
            
            return {
                'correct': False,
                'response': TextSendMessage(text=hint_text)
            }
        
        # عرض الحل
        if text in ['جاوب', 'الجواب', 'الحل']:
            self.answered = True
            
            if self.question_number < self.total_questions:
                return {
                    'correct': False,
                    'response': TextSendMessage(
                        text=f"الإجابة الصحيحة:\n{self.current_song['singer']}\n\nأغنية: {self.current_song['lyrics']}"
                    ),
                    'next_question': True
                }
            else:
                return self._end_game()
        
        # إجابة صحيحة
        if text_normalized == singer_normalized or singer_normalized in text_normalized:
            self.answered = True
            points = 10
            
            if user_id not in self.player_scores:
                self.player_scores[user_id] = {'name': display_name, 'score': 0}
            self.player_scores[user_id]['score'] += points
            
            if self.question_number < self.total_questions:
                return {
                    'correct': True,
                    'points': points,
                    'won': True,
                    'response': TextSendMessage(
                        text=f"إجابة صحيحة {display_name}\n\nالمغني: {self.current_song['singer']}\n\n+ {points} نقطة"
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
        
        # بطاقة الفائز
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
            bg_color = "#555555" if i == 1 else ("#888888" if i == 2 else "#F5F5F5")
            text_color = "#FFFFFF" if i <= 2 else "#333333"
            
            score_items.append({
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {"type": "text", "text": f"{i}.", "size": "sm", "color": text_color, "flex": 0},
                    {"type": "text", "text": data['name'], "size": "sm", "color": text_color, "flex": 3, "margin": "md", "wrap": True},
                    {"type": "text", "text": str(data['score']), "size": "sm", "color": text_color, "flex": 1, "align": "end", "weight": "bold"}
                ],
                "backgroundColor": bg_color,
                "cornerRadius": "8px",
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
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "انتهت اللعبة",
                                "size": "xl",
                                "weight": "bold",
                                "color": "#FFFFFF",
                                "align": "center"
                            }
                        ],
                        "backgroundColor": "#555555",
                        "cornerRadius": "10px",
                        "paddingAll": "16px"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "الفائز",
                                "size": "sm",
                                "color": "#888888",
                                "align": "center",
                                "margin": "md"
                            },
                            {
                                "type": "text",
                                "text": winner_name,
                                "size": "xl",
                                "weight": "bold",
                                "color": "#333333",
                                "align": "center",
                                "margin": "xs",
                                "wrap": True
                            },
                            {
                                "type": "text",
                                "text": f"{winner_score} نقطة",
                                "size": "md",
                                "color": "#666666",
                                "align": "center",
                                "margin": "xs"
                            }
                        ],
                        "margin": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "md",
                        "color": "#DDDDDD"
                    },
                    {
                        "type": "text",
                        "text": "النتائج النهائية",
                        "size": "md",
                        "weight": "bold",
                        "color": "#555555",
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": score_items,
                        "margin": "sm"
                    }
                ],
                "backgroundColor": "#FFFFFF",
                "paddingAll": "16px"
            },
            "footer": {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "button",
                        "action": {"type": "message", "label": "لعب مرة أخرى", "text": "أغنية"},
                        "style": "primary",
                        "color": "#555555",
                        "height": "sm"
                    }
                ],
                "backgroundColor": "#F5F5F5",
                "paddingAll": "12px"
            }
        }
