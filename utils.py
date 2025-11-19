import re

# الألوان الموحدة لجميع الألعاب
COLORS = {
    'bg': '#0A0E27',
    'topbg': '#667eea',
    'card': '#1a1f3a',
    'text': '#E8F4FF',
    'text2': '#8FB9D8',
    'cyan': '#00D9FF',
    'glow': '#5EEBFF',
    'sep': '#2C5F8D',
    'border': '#00D9FF50',
    'glass': '#1a1f3a90',
    'success': '#00FF88',
    'warning': '#FFB800'
}

LOGO_URL = 'https://i.imgur.com/qcWILGi.jpeg'

def normalize_text(text):
    """تنسيق النص للمقارنة"""
    if not text:
        return ""
    text = text.strip().lower()
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    text = text.replace('ؤ', 'و').replace('ئ', 'ي').replace('ء', '')
    text = text.replace('ة', 'ه').replace('ى', 'ي')
    text = re.sub(r'[\u064B-\u065F]', '', text)
    text = re.sub(r'\s+', '', text)
    return text

def create_game_card(game_name, question_num, total, content_items):
    """إنشاء بطاقة لعبة موحدة"""
    C = COLORS
    progress = (question_num / total) * 100
    return {
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
                    "paddingAll": "0px",
                    "offsetTop": "60px",
                    "borderWidth": "2px",
                    "borderColor": C['border'],
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "paddingAll": "30px",
                            "paddingBottom": "25px",
                            "backgroundColor": C['card'],
                            "cornerRadius": "30px 30px 0px 0px",
                            "contents": [
                                {"type": "text", "text": game_name, "weight": "bold", "size": "xxl", "align": "center", "color": C['glow']},
                                {"type": "text", "text": f"السؤال {question_num} من {total}", "size": "md", "align": "center", "color": C['text2'], "margin": "md"}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "height": "8px",
                            "backgroundColor": C['sep'],
                            "contents": [
                                {"type": "box", "layout": "vertical", "backgroundColor": C['cyan'], "width": f"{progress}%", "height": "8px"}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "paddingAll": "30px",
                            "spacing": "xl",
                            "contents": content_items + [
                                {"type": "separator", "color": C['sep'], "margin": "xl"},
                                {
                                    "type": "box",
                                    "layout": "horizontal",
                                    "spacing": "md",
                                    "margin": "xl",
                                    "contents": [
                                        {"type": "button", "action": {"type": "message", "label": "لمح", "text": "لمح"}, "style": "secondary", "color": "#FFFFFF", "height": "md"},
                                        {"type": "button", "action": {"type": "message", "label": "جاوب", "text": "جاوب"}, "style": "primary", "color": C['cyan'], "height": "md"}
                                    ]
                                }
                            ]
                        }
                    ]
                }]
            }]
        }
    }

def create_hint_card(hint_text, extra_info=None):
    """إنشاء بطاقة تلميح"""
    C = COLORS
    contents = [{"type": "text", "text": hint_text, "size": "xl", "color": C['text'], "align": "center", "wrap": True, "weight": "bold"}]
    if extra_info:
        contents.append({"type": "text", "text": extra_info, "size": "md", "color": C['text2'], "align": "center", "margin": "md"})
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": C['card'],
            "cornerRadius": "25px",
            "paddingAll": "30px",
            "borderWidth": "2px",
            "borderColor": C['border'],
            "contents": [
                {"type": "text", "text": "تلميح", "weight": "bold", "size": "xxl", "color": C['glow'], "align": "center"},
                {"type": "separator", "color": C['sep'], "margin": "lg"},
                {"type": "box", "layout": "vertical", "backgroundColor": C['glass'], "cornerRadius": "20px", "paddingAll": "25px", "margin": "xl", "borderWidth": "1px", "borderColor": C['border'], "contents": contents},
                {"type": "text", "text": "النقاط ستنخفض إلى نصف القيمة", "size": "sm", "color": C['warning'], "align": "center", "margin": "xl", "wrap": True}
            ]
        }
    }

def create_answer_card(answer_text):
    """إنشاء بطاقة الإجابة الصحيحة"""
    C = COLORS
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": C['card'],
            "cornerRadius": "25px",
            "paddingAll": "30px",
            "borderWidth": "2px",
            "borderColor": C['border'],
            "contents": [
                {"type": "text", "text": "الإجابة الصحيحة", "weight": "bold", "size": "xxl", "color": C['glow'], "align": "center"},
                {"type": "separator", "color": C['sep'], "margin": "lg"},
                {"type": "box", "layout": "vertical", "backgroundColor": C['glass'], "cornerRadius": "20px", "paddingAll": "25px", "margin": "xl", "borderWidth": "2px", "borderColor": C['cyan'], "contents": [
                    {"type": "text", "text": answer_text, "size": "xxl", "weight": "bold", "color": C['cyan'], "align": "center", "wrap": True}
                ]}
            ]
        }
    }

def create_results_card(player_scores):
    """إنشاء بطاقة النتائج النهائية"""
    from linebot.models import TextSendMessage, FlexSendMessage
    C = COLORS
    
    if not player_scores:
        return TextSendMessage(text="لم يشارك أحد في اللعبة")
    
    sorted_players = sorted(player_scores.items(), key=lambda x: x[1]['score'], reverse=True)
    winners_content = []
    rank_emojis = {1: "1", 2: "2", 3: "3"}
    
    for idx, (user_id, data) in enumerate(sorted_players[:5], 1):
        emoji = rank_emojis.get(idx, str(idx))
        winners_content.append({
            "type": "box",
            "layout": "horizontal",
            "backgroundColor": C['glass'],
            "cornerRadius": "15px",
            "paddingAll": "18px",
            "margin": "md" if idx > 1 else "none",
            "borderWidth": "2px" if idx <= 3 else "1px",
            "borderColor": C['cyan'] if idx <= 3 else C['border'],
            "contents": [
                {"type": "text", "text": emoji, "size": "xxl", "flex": 0},
                {"type": "text", "text": data['name'], "size": "lg", "color": C['text'], "flex": 3, "margin": "md", "weight": "bold" if idx <= 3 else "regular"},
                {"type": "text", "text": f"{data['score']} نقطة", "size": "lg", "color": C['cyan'], "align": "end", "flex": 1, "weight": "bold"}
            ]
        })
    
    return FlexSendMessage(alt_text="النتائج النهائية", contents={
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
                        {"type": "text", "text": "انتهت اللعبة", "weight": "bold", "size": "xxl", "align": "center", "color": C['glow']},
                        {"type": "separator", "color": C['sep'], "margin": "xl"},
                        {"type": "text", "text": "لوحة الصدارة", "size": "xl", "align": "center", "color": C['text'], "margin": "xl", "weight": "bold"},
                        {"type": "box", "layout": "vertical", "margin": "xl", "contents": winners_content},
                        {"type": "button", "action": {"type": "message", "label": "لعب مرة أخرى", "text": "إعادة"}, "style": "primary", "color": C['cyan'], "height": "md", "margin": "xxl"}
                    ]
                }]
            }]
        }
    })
