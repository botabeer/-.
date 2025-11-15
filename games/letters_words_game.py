from linebot.models import TextSendMessage
import random

class LettersWordsGame:
    def __init__(self, line_bot_api, use_ai=False, ask_ai=None):
        self.line_bot_api = line_bot_api
        self.use_ai = use_ai
        self.ask_ai = ask_ai

        # أمثلة جاهزة للنسخ الاحتياطي إذا الـ AI ما اشتغل
        self.examples = [
            {"letters": "م ك ت ا ب ه", "words": ["كتاب", "كتب", "تبسم", "بكم", "تم"]},
            {"letters": "س ل ا م ت ه", "words": ["سلام", "سلم", "هلس", "مساء"]},
            {"letters": "ح ب ك م ل ا", "words": ["حب", "كمل", "لحم", "محل"]},
            {"letters": "ر س ا م ن ه", "words": ["رسم", "سنه", "نسر", "مرن"]},
            {"letters": "م د ر س ه", "words": ["مدرسة", "مدرس", "درس", "سرد"]},
            {"letters": "ق ل م ا ت ه", "words": ["قلم", "قل", "مقل", "تم", "قلات"]},
        ]

    def generate_letters(self):
        letters = random.choice(self.examples)["letters"]
        return letters

    def start_game(self):
        item = random.choice(self.examples)
        letters = item["letters"]
        return TextSendMessage(text=f"🔤 لعبة تكوين الكلمات\n\nالحروف:\n{letters}\n\nكوّن أكبر عدد ممكن من الكلمات!")

    def get_words(self, letters):
        if self.use_ai and self.ask_ai:
            try:
                prompt = f"استخرج كلمات صحيحة يمكن تكوينها من الحروف التالية فقط: {letters}"
                response = self.ask_ai(prompt)
                return response
            except:
                pass

        # رجوع للنسخة الجاهزة لو AI ما اشتغل
        for item in self.examples:
            if item["letters"] == letters:
                return "\n".join(item["words"])
        return "لا توجد كلمات مسجلة."
