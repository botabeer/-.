import random
from linebot.models import FlexSendMessage
from utils import COLORS

class CompatibilityGame:
    def __init__(self):
        self.total_questions = 1  # جولة واحدة فقط
        self.question_number = 0
        self.player_scores = {}

    def start_game(self):
        self.question_number = 0
        self.player_scores = {}
        return self.next_question()

    def next_question(self):
        if self.question_number >= self.total_questions:
            return None
        self.question_number += 1
        
        C = COLORS
        content = [
            {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": C['glass'],
                "cornerRadius": "20px",
                "paddingAll": "28px",
                "borderWidth": "2px",
                "borderColor": C['border'],
                "contents": [
                    {"type": "text", "text": "▫️ لعبة التوافق", "size": "xxl", "weight": "bold", "color": C['cyan'], "align": "center"},
                    {"type": "text", "text": "احسب نسبة التوافق بين اسمين", "size": "md", "color": C['text2'], "align": "center", "margin": "md", "wrap": True}
                ]
            },
            {"type": "text", "text": "اكتب الاسمين مفصولين بفاصلة\nمثال: احمد، فاطمة", "size": "sm", "color": C['text'], "align": "center", "margin": "lg", "wrap": True}
        ]
        
        card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": C['bg'],
                "paddingAll": "0px",
                "contents": [{
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": C['topbg'],
                    "paddingTop": "40px",
                    "paddingBottom": "150px",
                    "contents": [{
                        "type": "box",
                        "layout": "vertical",
                        "cornerRadius": "30px",
                        "backgroundColor": C['bg'],
                        "paddingAll": "30px",
                        "offsetTop": "60px",
                        "borderWidth": "2px",
                        "borderColor": C['border'],
                        "contents": content
                    }]
                }]
            }
        }
        
        return FlexSendMessage(alt_text="لعبة التوافق", contents=card)

    def calculate_compatibility(self, name1, name2):
        """حساب نسبة التوافق بناءً على الأحرف المشتركة"""
        # تنظيف الأسماء
        name1 = name1.strip().replace(' ', '')
        name2 = name2.strip().replace(' ', '')
        
        # حساب الأحرف المشتركة
        common = len(set(name1) & set(name2))
        total = len(set(name1) | set(name2))
        
        if total == 0:
            return random.randint(50, 90)
        
        # نسبة أساسية من الأحرف المشتركة
        base_percentage = (common / total) * 100
        
        # إضافة عامل عشوائي للمرح
        random_factor = random.randint(-15, 25)
        
        # النسبة النهائية
        percentage = max(10, min(100, int(base_percentage + random_factor)))
        
        return percentage

    def get_hint(self):
        # لا يدعم التلميحات
        return None

    def show_answer(self):
        # لا توجد إجابة محددة
        return None

    def check_answer(self, answer, user_id, display_name):
        """معالجة الإجابة وحساب التوافق"""
        # تقسيم الإجابة إلى اسمين
        parts = [p.strip() for p in answer.replace('،', ',').split(',')]
        
        if len(parts) != 2:
            return None
        
        name1, name2 = parts
        
        if not name1 or not name2:
            return None
        
        # حساب نسبة التوافق
        percentage = self.calculate_compatibility(name1, name2)
        
        # تحديد الرسالة بناءً على النسبة
        if percentage >= 90:
            message = "توافق مثالي! "
            emoji = ""
        elif percentage >= 75:
            message = "توافق رائع! "
            emoji = ""
        elif percentage >= 60:
            message = "توافق جيد! "
            emoji = ""
        elif percentage >= 45:
            message = "توافق متوسط "
            emoji = ""
        else:
            message = "توافق ضعيف "
            emoji = ""
        
        # إنشاء بطاقة النتيجة
        C = COLORS
        result_card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": C['bg'],
                "paddingAll": "0px",
                "contents": [{
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": C['topbg'],
                    "paddingTop": "40px",
                    "paddingBottom": "150px",
                    "contents": [{
                        "type": "box",
                        "layout": "vertical",
                        "cornerRadius": "30px",
                        "backgroundColor": C['bg'],
                        "paddingAll": "35px",
                        "offsetTop": "60px",
                        "borderWidth": "2px",
                        "borderColor": C['border'],
                        "contents": [
                            {"type": "text", "text": "🖤 نتيجة التوافق", "weight": "bold", "size": "xxl", "align": "center", "color": C['glow']},
                            {"type": "separator", "color": C['sep'], "margin": "xl"},
                            {
                                "type": "box",
                                "layout": "vertical",
                                "backgroundColor": C['glass'],
                                "cornerRadius": "20px",
                                "paddingAll": "25px",
                                "margin": "xl",
                                "borderWidth": "2px",
                                "borderColor": C['cyan'],
                                "contents": [
                                    {"type": "text", "text": f"{name1} & {name2}", "size": "xl", "weight": "bold", "color": C['text'], "align": "center", "wrap": True},
                                    {"type": "text", "text": f"{emoji} {percentage}% {emoji}", "size": "3xl", "weight": "bold", "color": C['cyan'], "align": "center", "margin": "lg"},
                                    {"type": "text", "text": message, "size": "lg", "color": C['text2'], "align": "center", "margin": "md"}
                                ]
                            },
                            {"type": "button", "action": {"type": "message", "label": "🔄 جرب مرة أخرى", "text": "توافق"}, "style": "primary", "color": C['cyan'], "height": "md", "margin": "xxl"}
                        ]
                    }]
                }]
            }
        }
        
        return {
            'correct': True,
            'points': 0,
            'message': f'نسبة التوافق: {percentage}%',
            'flex': result_card
        }

    def get_final_results(self):
        # لا توجد نتائج نهائية لهذه اللعبة
        C = COLORS
        card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": C['card'],
                "cornerRadius": "25px",
                "paddingAll": "30px",
                "contents": [
                    {"type": "text", "text": "شكراً للعب! 🖤", "weight": "bold", "size": "xxl", "color": C['glow'], "align": "center"},
                    {"type": "text", "text": "هذه لعبة ترفيهية فقط", "size": "md", "color": C['text2'], "align": "center", "margin": "md"}
                ]
            }
        }
        return FlexSendMessage(alt_text="شكراً للعب", contents=card)
