from linebot.models import TextSendMessage, ImageSendMessage, FlexSendMessage
import random

class DifferencesGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.image_pairs = [
            {
                "original": "https://up6.cc/2025/10/176308448198881.jpeg",
                "solution": "https://mrkzgulfup.com/uploads/176303338684742.jpeg",
                "differences": 5
            },
            {
                "original": "https://up6.cc/2025/10/176308448205332.jpeg",
                "solution": "https://mrkzgulfup.com/uploads/176303338695684.jpeg",
                "differences": 5
            },
            {
                "original": "https://up6.cc/2025/10/176308448209753.jpeg",
                "solution": "https://mrkzgulfup.com/uploads/176303338714356.jpeg",
                "differences": 5
            },
            {
                "original": "https://up6.cc/2025/10/17630844821154.jpeg",
                "solution": "https://mrkzgulfup.com/uploads/176303338717158.jpeg",
                "differences": 5
            },
            {
                "original": "https://up6.cc/2025/10/176308448213085.jpeg",
                "solution": "https://mrkzgulfup.com/uploads/1763033387284912.jpeg",
                "differences": 5
            }
        ]
        self.current_pair = None
        self.showed_solution = False
    
    def start_game(self):
        self.current_pair = random.choice(self.image_pairs)
        self.showed_solution = False
        
        # بطاقة تعليمات محسّنة
        intro_card = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "لعبة الاختلافات",
                        "size": "xl",
                        "weight": "bold",
                        "color": "#1C1C1E",
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": "للتسلية فقط",
                        "size": "sm",
                        "color": "#8E8E93",
                        "align": "center",
                        "margin": "sm"
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
                                "text": f"ابحث عن {self.current_pair['differences']} اختلافات",
                                "size": "lg",
                                "weight": "bold",
                                "color": "#1C1C1E",
                                "align": "center"
                            },
                            {
                                "type": "text",
                                "text": "▫️ لا تُحسب نقاط لهذه اللعبة\n▫️ للتسلية والترفيه فقط",
                                "size": "sm",
                                "color": "#8E8E93",
                                "align": "center",
                                "wrap": True,
                                "margin": "md"
                            }
                        ],
                        "backgroundColor": "#F2F2F7",
                        "cornerRadius": "12px",
                        "paddingAll": "16px",
                        "margin": "xl"
                    }
                ],
                "backgroundColor": "#FFFFFF",
                "paddingAll": "24px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {"type": "message", "label": "عرض الحل", "text": "جاوب"},
                        "style": "primary",
                        "color": "#1C1C1E",
                        "height": "sm"
                    }
                ],
                "backgroundColor": "#F2F2F7",
                "paddingAll": "12px"
            }
        }
        
        return [
            FlexSendMessage(alt_text="لعبة الاختلافات", contents=intro_card),
            ImageSendMessage(
                original_content_url=self.current_pair['original'],
                preview_image_url=self.current_pair['original']
            )
        ]
    
    def check_answer(self, answer, user_id, display_name):
        if not self.current_pair:
            return None
        
        answer_lower = answer.strip().lower()
        
        if answer_lower in ['جاوب', 'الجواب', 'الحل', 'solution']:
            self.showed_solution = True
            
            solution_card = {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "الحل",
                            "size": "xl",
                            "weight": "bold",
                            "color": "#1C1C1E",
                            "align": "center"
                        },
                        {
                            "type": "text",
                            "text": "الاختلافات موضحة بالأسفل",
                            "size": "sm",
                            "color": "#8E8E93",
                            "align": "center",
                            "margin": "sm"
                        }
                    ],
                    "backgroundColor": "#FFFFFF",
                    "paddingAll": "20px"
                }
            }
            
            return {
                'response': [
                    FlexSendMessage(alt_text="الحل", contents=solution_card),
                    ImageSendMessage(
                        original_content_url=self.current_pair['solution'],
                        preview_image_url=self.current_pair['solution']
                    )
                ],
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': True
            }
        
        return None
