from linebot.models import TextSendMessage
import random

class HumanAnimalPlantGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.categories = ["إنسان", "حيوان", "نبات", "جماد", "بلد"]

    def start_game(self):
        letter = random.choice(list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي"))
        category = random.choice(self.categories)
        return TextSendMessage(text=f"لعبة إنسان – حيوان – نبات 🔤\n\nالحرف: {letter}\nالفئة: {category}")

    def check_answer(self, text):
        if len(text.strip()) < 2:
            return TextSendMessage(text="الإجابة قصيرة جدًا! حاول مرة أخرى.")
        return TextSendMessage(text="تم تسجيل إجابتك ✔️")
