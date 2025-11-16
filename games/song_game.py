from linebot.models import TextSendMessage, FlexSendMessage
‏import random
‏import re
‏import logging

‏logger = logging.getLogger("whale-bot")

‏class SongGame:
‏    def __init__(self, line_bot_api, use_ai=False, ask_ai=None):
‏        self.line_bot_api = line_bot_api
‏        self.use_ai = use_ai
‏        self.ask_ai = ask_ai
‏        self.current_song = None
‏        self.scores = {}
‏        self.answered = False
‏        self.question_number = 0
‏        self.total_questions = 5
‏        self.player_scores = {}
        
‏        self.all_songs = [
‏            {"lyrics": "رجعت لي أيام الماضي معاك", "singer": "أم كلثوم"},
‏            {"lyrics": "جلست والخوف بعينيها تتأمل فنجاني", "singer": "عبد الحليم حافظ"},
‏            {"lyrics": "تملي معاك ولو حتى بعيد عني", "singer": "عمرو دياب"},
‏            {"lyrics": "حبيبي يا نور العين", "singer": "عمرو دياب"},
‏            {"lyrics": "على بالي يا ناس", "singer": "فيروز"},
‏            {"lyrics": "قولوا لعيني تسهر", "singer": "عبد الحليم حافظ"},
‏            {"lyrics": "سألوني الناس عليك", "singer": "فيروز"},
‏            {"lyrics": "أهواك يا من لا أهوى سواك", "singer": "أم كلثوم"},
‏            {"lyrics": "على قد الشوق", "singer": "عمرو دياب"},
‏            {"lyrics": "صباح الخير يا سيدي", "singer": "فيروز"}
        ]
‏        random.shuffle(self.all_songs)
    
‏    def normalize_text(self, text):
‏        if not text:
‏            return ""
‏        text = text.strip().lower()
‏        text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
‏        text = text.replace('ؤ', 'و').replace('ئ', 'ي').replace('ء', '')
‏        text = text.replace('ة', 'ه').replace('ى', 'ي')
‏        text = re.sub(r'[\u064B-\u065F]', '', text)
‏        text = re.sub(r'\s+', '', text)
‏        return text
    
‏    def start_game(self):
‏        self.question_number = 0
‏        self.player_scores = {}
‏        return self._next_question()
    
‏    def _next_question(self):
‏        self.question_number += 1
‏        if self.question_number <= len(self.all_songs):
‏            self.current_song = self.all_songs[self.question_number - 1]
‏        else:
‏            self.current_song = random.choice(self.all_songs)
‏        self.answered = False
        
        # بطاقة Flex محسّنة بالستايل الجديد
‏        card = {
‏            "type": "bubble",
‏            "size": "kilo",
‏            "body": {
‏                "type": "box",
‏                "layout": "vertical",
‏                "contents": [
                    {
‏                        "type": "text",
‏                        "text": "🎵 لعبة الأغنية",
‏                        "size": "xl",
‏                        "weight": "bold",
‏                        "color": "#1D1D1F",
‏                        "align": "center"
                    },
                    {
‏                        "type": "separator",
‏                        "margin": "lg",
‏                        "color": "#E5E5EA"
                    },
                    {
‏                        "type": "text",
‏                        "text": f"سؤال {self.question_number} من {self.total_questions}",
‏                        "size": "sm",
‏                        "color": "#86868B",
‏                        "align": "center",
‏                        "margin": "md"
                    },
                    {
‏                        "type": "box",
‏                        "layout": "vertical",
‏                        "contents": [
                            {
‏                                "type": "text",
‏                                "text": self.current_song['lyrics'],
‏                                "size": "md",
‏                                "weight": "bold",
‏                                "color": "#1D1D1F",
‏                                "align": "center",
‏                                "wrap": True
                            }
                        ],
‏                        "backgroundColor": "#F5F5F7",
‏                        "cornerRadius": "12px",
‏                        "paddingAll": "16px",
‏                        "margin": "lg"
                    },
                    {
‏                        "type": "text",
‏                        "text": "من المغني؟",
‏                        "size": "sm",
‏                        "color": "#86868B",
‏                        "align": "center",
‏                        "margin": "md"
                    }
                ],
‏                "backgroundColor": "#FFFFFF",
‏                "paddingAll": "20px"
            },
‏            "footer": {
‏                "type": "box",
‏                "layout": "horizontal",
‏                "contents": [
                    {
‏                        "type": "button",
‏                        "action": {"type": "message", "label": "💡 تلميح", "text": "لمح"},
‏                        "style": "secondary",
‏                        "color": "#424245",
‏                        "height": "sm"
                    },
                    {
‏                        "type": "button",
‏                        "action": {"type": "message", "label": "📝 الحل", "text": "جاوب"},
‏                        "style": "secondary",
‏                        "color": "#424245",
‏                        "height": "sm"
                    }
                ],
‏                "spacing": "sm",
‏                "backgroundColor": "#FAFAFA",
‏                "paddingAll": "16px"
            }
        }
        
‏        return FlexSendMessage(alt_text="🎵 لعبة الأغنية", contents=card)
    
‏    def next_question(self):
‏        if self.question_number < self.total_questions:
‏            return self._next_question()
‏        return None
    
‏    def check_answer(self, text, user_id, display_name):
‏        if self.answered:
‏            return None
        
‏        text_normalized = self.normalize_text(text)
‏        singer_normalized = self.normalize_text(self.current_song['singer'])
        
        # تلميح
‏        if text in ['لمح', 'تلميح']:
‏            singer = self.current_song['singer']
‏            num_words = len(singer.split())
            
‏            hint_text = f"💡 تلميح:\n\n▪️ يبدأ بحرف: {singer[0]}\n▪️ عدد الحروف: {len(singer)}\n▪️ مكون من: {'كلمة واحدة' if num_words == 1 else f'{num_words} كلمات'}"
            
‏            return {
‏                'correct': False,
‏                'response': TextSendMessage(text=hint_text)
            }
        
        # عرض الحل
‏        if text in ['جاوب', 'الجواب', 'الحل']:
‏            self.answered = True
            
‏            if self.question_number < self.total_questions:
‏                return {
‏                    'correct': False,
‏                    'response': TextSendMessage(
‏                        text=f"📝 الإجابة الصحيحة:\n\n▪️ المغني: {self.current_song['singer']}\n▪️ الأغنية: {self.current_song['lyrics']}"
                    ),
‏                    'next_question': True
                }
‏            else:
‏                return self._end_game()
        
        # إجابة صحيحة
‏        if text_normalized == singer_normalized or singer_normalized in text_normalized:
‏            self.answered = True
‏            points = 10
            
‏            if user_id not in self.player_scores:
‏                self.player_scores[user_id] = {'name': display_name, 'score': 0}
‏            self.player_scores[user_id]['score'] += points
            
‏            if self.question_number < self.total_questions:
‏                return {
‏                    'correct': True,
‏                    'points': points,
‏                    'won': True,
‏                    'response': TextSendMessage(
‏                        text=f"✅ إجابة صحيحة {display_name}!\n\n▪️ المغني: {self.current_song['singer']}\n▪️ النقاط: +{points}"
                    ),
‏                    'next_question': True
                }
‏            else:
‏                return self._end_game()
        
‏        return None
    
‏    def _end_game(self):
‏        if not self.player_scores:
‏            return {
‏                'game_over': True,
‏                'response': TextSendMessage(text="⏹️ انتهت اللعبة\n\nلم يشارك أحد")
            }
        
‏        sorted_players = sorted(
‏            self.player_scores.items(),
‏            key=lambda x: x[1]['score'],
‏            reverse=True
        )
        
‏        winner_id, winner_data = sorted_players[0]
        
        # بطاقة النتائج النهائية
‏        score_items = []
‏        for i, (uid, data) in enumerate(sorted_players[:5], 1):
‏            rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            
‏            score_items.append({
‏                "type": "box",
‏                "layout": "horizontal",
‏                "contents": [
‏                    {"type": "text", "text": rank_emoji, "size": "sm", "flex": 0, "color": "#1D1D1F"},
‏                    {"type": "text", "text": data['name'], "size": "sm", "flex": 3, "margin": "md", "wrap": True, "color": "#1D1D1F"},
‏                    {"type": "text", "text": str(data['score']), "size": "sm", "flex": 1, "align": "end", "weight": "bold", "color": "#000000"}
                ],
‏                "backgroundColor": "#F5F5F7" if i > 3 else "#FAFAFA",
‏                "cornerRadius": "8px",
‏                "paddingAll": "12px",
‏                "margin": "sm" if i > 1 else "md"
            })
        
‏        winner_card = {
‏            "type": "bubble",
‏            "size": "kilo",
‏            "body": {
‏                "type": "box",
‏                "layout": "vertical",
‏                "contents": [
                    {
‏                        "type": "text",
‏                        "text": "🏆 انتهت اللعبة",
‏                        "size": "xl",
‏                        "weight": "bold",
‏                        "color": "#1D1D1F",
‏                        "align": "center"
                    },
                    {
‏                        "type": "separator",
‏                        "margin": "lg",
‏                        "color": "#E5E5EA"
                    },
                    {
‏                        "type": "box",
‏                        "layout": "vertical",
‏                        "contents": [
                            {
‏                                "type": "text",
‏                                "text": "الفائز",
‏                                "size": "sm",
‏                                "color": "#86868B",
‏                                "align": "center"
                            },
                            {
‏                                "type": "text",
‏                                "text": winner_data['name'],
‏                                "size": "xl",
‏                                "weight": "bold",
‏                                "color": "#000000",
‏                                "align": "center",
‏                                "margin": "xs",
‏                                "wrap": True
                            },
                            {
‏                                "type": "text",
‏                                "text": f"⭐ {winner_data['score']} نقطة",
‏                                "size": "md",
‏                                "color": "#424245",
‏                                "align": "center",
‏                                "margin": "xs"
                            }
                        ],
‏                        "backgroundColor": "#F5F5F7",
‏                        "cornerRadius": "12px",
‏                        "paddingAll": "16px",
‏                        "margin": "lg"
                    },
                    {
‏                        "type": "text",
‏                        "text": "▪️ النتائج النهائية",
‏                        "size": "md",
‏                        "weight": "bold",
‏                        "color": "#1D1D1F",
‏                        "margin": "lg"
                    },
                    {
‏                        "type": "box",
‏                        "layout": "vertical",
‏                        "contents": score_items,
‏                        "margin": "sm"
                    }
                ],
‏                "backgroundColor": "#FFFFFF",
‏                "paddingAll": "20px"
            },
‏            "footer": {
‏                "type": "box",
‏                "layout": "horizontal",
‏                "contents": [
                    {
‏                        "type": "button",
‏                        "action": {"type": "message", "label": "🔄 لعب مرة أخرى", "text": "أغنية"},
‏                        "style": "primary",
‏                        "color": "#000000",
‏                        "height": "sm"
                    }
                ],
‏                "backgroundColor": "#FAFAFA",
‏                "paddingAll": "16px"
            }
        }
        
‏        return {
‏            'game_over': True,
‏            'won': True,
‏            'response': FlexSendMessage(alt_text="🏆 النتائج النهائية", contents=winner_card),
‏            'points': winner_data['score']
        }
