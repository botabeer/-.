from linebot.models import TextSendMessage, FlexSendMessage
import random, re

# ============================
#   🎨 ألوان موحدة
# ============================
C = {
    'bg': '#0A0E27',
    'card': '#0F2440',
    'text': '#E0F2FF',
    'text2': '#7FB3D5',
    'cyan': '#00D9FF',
    'glow': '#5EEBFF',
    'sep': '#2C5F8D',
    'border': '#00D9FF40'
}

# ============================
#   🔤 دوال مساعدة
# ============================
def normalize_text(t):
    if not t:
        return ""
    t = t.strip().lower()
    t = re.sub('[أإآ]', 'ا', t)
    t = re.sub('[ؤ]', 'و', t)
    t = re.sub('[ئ]', 'ي', t)
    t = re.sub('[ءةى]', '', t)
    t = re.sub('[\u064B-\u065F]', '', t)
    return re.sub(r'\s+', ' ', t).strip()

def glass_box(contents, padding="20px"):
    return {
        "type": "box",
        "layout": "vertical",
        "contents": contents,
        "backgroundColor": C['card'],
        "cornerRadius": "16px",
        "paddingAll": padding,
        "borderWidth": "1px",
        "borderColor": C['border'],
        "margin": "md"
    }

def progress_bar(current, total):
    return {
        "type": "box",
        "layout": "horizontal",
        "contents": [
            {
                "type": "box",
                "layout": "vertical",
                "contents": [],
                "backgroundColor": C['cyan'],
                "height": "6px",
                "flex": current,
                "cornerRadius": "3px"
            },
            {
                "type": "box",
                "layout": "vertical",
                "contents": [],
                "backgroundColor": C['card'],
                "height": "6px",
                "flex": max(1, total - current),
                "cornerRadius": "3px"
            }
        ],
        "spacing": "xs",
        "margin": "lg"
    }

def game_header(title, subtitle):
    return [
        {
            "type": "text",
            "text": "♓",
            "size": "6xl",
            "color": C['glow'],
            "align": "center",
            "margin": "none"
        },
        {
            "type": "text",
            "text": title,
            "size": "xl",
            "weight": "bold",
            "color": C['cyan'],
            "align": "center",
            "margin": "md"
        },
        {
            "type": "text",
            "text": subtitle,
            "size": "sm",
            "color": C['text2'],
            "align": "center",
            "margin": "xs"
        },
        {
            "type": "separator",
            "margin": "lg",
            "color": C['sep']
        }
    ]

def create_game_card(header, body_contents, footer_buttons=None):
    card = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": header + body_contents,
            "backgroundColor": C['bg'],
            "paddingAll": "24px"
        }
    }

    if footer_buttons:
        card["footer"] = {
            "type": "box",
            "layout": "horizontal",
            "contents": footer_buttons,
            "spacing": "sm",
            "backgroundColor": C['bg'],
            "paddingAll": "16px"
        }

    return card

def btn(label, text):
    return {
        "type": "button",
        "action": {"type": "message", "label": label, "text": text},
        "style": "secondary",
        "height": "md"
    }

# ============================
#   🔥 لعبة سلسلة الكلمات
# ============================
class ChainWordsGame:
    def __init__(self):
        self.start_words = ["قلم", "كتاب", "مدرسة", "باب", "نافذة"]
        self.current_word = None
        self.used = set()
        self.round = 0
        self.max_rounds = 5
        self.scores = {}

    # ----------------------------
    #   🎮 بداية اللعبة
    # ----------------------------
    def start_game(self):
        self.current_word = random.choice(self.start_words)
        self.used = {normalize_text(self.current_word)}
        self.round = 1
        self.scores = {}

        return FlexSendMessage(
            alt_text="سلسلة الكلمات",
            contents=create_game_card(
                game_header("سلسلة الكلمات", f"الجولة {self.round}/{self.max_rounds}"),
                [
                    glass_box(
                        [
                            {"type": "text", "text": "الكلمة السابقة", "size": "sm", "color": C['text2'], "align": "center"},
                            {"type": "text", "text": self.current_word, "size": "xl", "weight": "bold", "color": C['text'], "align": "center", "margin": "sm"},
                        ],
                        "20px",
                    ),
                    glass_box(
                        [
                            {"type": "text", "text": "ابدأ بحرف", "size": "sm", "color": C['text2'], "align": "center"},
                            {"type": "text", "text": self.current_word[-1], "size": "5xl", "weight": "bold", "color": C['glow'], "align": "center", "margin": "md"},
                        ],
                        "32px",
                    ),
                    progress_bar(self.round, self.max_rounds),
                ],
            ),
        )

    # ----------------------------
    #   ✔ التحقق من الإجابة
    # ----------------------------
    def check_answer(self, text, user_id, name):
        text = text.strip()
        last = self.current_word[-1]

        norm_last = 'ه' if last in ['ة', 'ه'] else last
        norm_ans = normalize_text(text)

        if norm_ans in self.used:
            return {"response": TextSendMessage(text="❗ الكلمة مستخدمة مسبقًا"), "correct": False}

        first = 'ه' if text[0].lower() in ['ة', 'ه'] else text[0].lower()

        if first == norm_last:
            self.used.add(norm_ans)
            old_word = self.current_word
            self.current_word = text
            self.round += 1

            # نقاط
            points = 2
            if user_id not in self.scores:
                self.scores[user_id] = {"name": name, "score": 0}
            self.scores[user_id]["score"] += points

            # استمرار اللعبة
            if self.round <= self.max_rounds:
                return {
                    "response": FlexSendMessage(
                        alt_text="إجابة صحيحة",
                        contents=create_game_card(
                            game_header("صحيح ✔", "كلمة ممتازة"),
                            [
                                glass_box(
                                    [
                                        {"type": "text", "text": name, "size": "xl", "weight": "bold", "color": C['text'], "align": "center"},
                                        {"type": "text", "text": f"{old_word} → {text}", "size": "lg", "color": C['text2'], "align": "center", "margin": "sm"},
                                        {"type": "text", "text": f"+{points} نقطة", "size": "xxl", "color": C['glow'], "align": "center", "margin": "md", "weight": "bold"},
                                    ],
                                    "28px",
                                )
                            ],
                        ),
                    ),
                    "points": points,
                    "correct": True,
                    "next_question": True,
                }

            # انتهاء اللعبة
            return {"points": 0, "correct": True, "won": True, "game_over": True}

        return {"response": TextSendMessage(text=f"❗ يجب أن تبدأ الكلمة بحرف: {last}"), "correct": False}
