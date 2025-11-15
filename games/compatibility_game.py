from linebot.models import TextSendMessage, FlexSendMessage
import random

class CompatibilityGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.waiting_for_names = True
    
    def start_game(self):
        card = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "لعبة التوافق",
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
                                "text": "اكتب اسمين مفصولين بمسافة",
                                "size": "md",
                                "color": "#1C1C1E",
                                "align": "center",
                                "wrap": True
                            },
                            {
                                "type": "text",
                                "text": "نص فقط بدون رموز",
                                "size": "sm",
                                "color": "#8E8E93",
                                "align": "center",
                                "margin": "md"
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "مثال: اسم اسم",
                                        "size": "sm",
                                        "color": "#1C1C1E",
                                        "align": "center"
                                    }
                                ],
                                "backgroundColor": "#FFFFFF",
                                "cornerRadius": "8px",
                                "paddingAll": "12px",
                                "margin": "md"
                            },
                            {
                                "type": "text",
                                "text": "▫️ لا تُحسب نقاط لهذه اللعبة",
                                "size": "xs",
                                "color": "#8E8E93",
                                "align": "center",
                                "margin": "lg"
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
            }
        }
        
        return FlexSendMessage(alt_text="لعبة التوافق", contents=card)
    
    def check_answer(self, answer, user_id, display_name):
        if not self.waiting_for_names:
            return None
        
        parts = answer.strip().split()
        
        if len(parts) < 2:
            return {
                'response': TextSendMessage(
                    text="يجب كتابة اسمين مفصولين بمسافة\n\nمثال: اسم اسم"
                ),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': False
            }
        
        name1 = parts[0]
        name2 = parts[1]
        
        # نسبة توافق عشوائية
        compatibility = random.randint(50, 100)
        
        # رسائل حسب النسبة
        if compatibility >= 90:
            message = "🖤 توافق مثالي"
            emoji = "🖤"
        elif compatibility >= 75:
            message = "🖤 توافق ممتاز"
            emoji = "🖤"
        elif compatibility >= 60:
            message = "🖤 توافق جيد"
            emoji = "🖤"
        else:
            message = "🖤 توافق متوسط"
            emoji = "🖤"
        
        self.waiting_for_names = False
        
        # بطاقة نتيجة التوافق
        result_card = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "نسبة التوافق",
                        "size": "xl",
                        "weight": "bold",
                        "color": "#1C1C1E",
                        "align": "center"
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
                                "text": f"{name1} 🖤 {name2}",
                                "size": "lg",
                                "weight": "bold",
                                "color": "#1C1C1E",
                                "align": "center",
                                "wrap": True
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": f"{compatibility}%",
                                        "size": "xxl",
                                        "weight": "bold",
                                        "color": "#1C1C1E",
                                        "align": "center"
                                    },
                                    {
                                        "type": "text",
                                        "text": message,
                                        "size": "md",
                                        "color": "#8E8E93",
                                        "align": "center",
                                        "margin": "sm"
                                    }
                                ],
                                "backgroundColor": "#FFFFFF",
                                "cornerRadius": "12px",
                                "paddingAll": "20px",
                                "margin": "lg"
                            },
                            {
                                "type": "text",
                                "text": "▫️ للتسلية فقط - لا تُحسب نقاط",
                                "size": "xs",
                                "color": "#8E8E93",
                                "align": "center",
                                "margin": "lg"
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
            }
        }
        
        return {
            'response': FlexSendMessage(alt_text="نسبة التوافق", contents=result_card),
            'points': 0,  # لا نقاط لهذه اللعبة
            'correct': True,
            'won': False,
            'game_over': True
        }
