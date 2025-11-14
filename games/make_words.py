from linebot.models import TextSendMessage
import random

class MakeWordsGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.active_games = {}

    def start(self, event):
        """بدء لعبة تكوين الكلمات"""
        user_id = event.source.user_id
        letters = random.choice([
            ["ك", "ت", "ا", "ب"],
            ["ل", "ع", "ب", "ة"],
            ["س", "م", "ا", "ء"],
            ["و", "ر", "د"],
            ["ح", "ي", "ا", "ة"],
            ["ح", "ب", "ر"]
        ])
        self.active_games[user_id] = {"letters": letters}
        shuffled = " ".join(random.sample(letters, len(letters)))
        msg = f"🔠 كوّن كلمة من الحروف التالية:\n{shuffled}"
        self.line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))

    def check_answer(self, event):
        """التحقق من إجابة المستخدم"""
        user_id = event.source.user_id
        text = event.message.text.strip()
        game = self.active_games.get(user_id)
        if not game:
            return
        correct_word = "".join(game["letters"])
        if text == correct_word:
            msg = f"🎉 أحسنت! الكلمة الصحيحة هي: {correct_word}"
        else:
            msg = f"❌ خطأ! حاول مرة أخرى."
        self.line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        del self.active_games[user_id]
