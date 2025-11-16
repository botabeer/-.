import random
import re
from linebot.models import TextSendMessage

class LettersWordsGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.available_letters = []
        self.used_words = set()
        self.current_question = 1
        self.max_questions = 10
        self.players_scores = {}
        self.hint_used = False
        self.words_per_question = 3  # الآن نطلب 3 كلمات لكل سؤال
        self.current_round_words = 0

        # مجموعات الحروف (كل مجموعة 6 أحرف)
        self.letter_sets = [
            list("س م ا ء ن ج"),
            list("ب ي ت ك م ل"),
            list("ق ل م د ر س"),
            list("ش ج ر ة و ر"),
            list("ح ب ر ط ع م"),
            list("ط ع ا م ش ر"),
            list("ن ج م س م ا"),
            list("م ك ت ب ق ل"),
            list("س ر ي ر ب ا"),
            list("ق م ر ل ي ل")
        ]

        # كلمات صحيحة شائعة
        self.valid_words = {
            "سماء", "سما", "نجم", "ماء", "جم", 
            "بيت", "بتي", "كمل", "مل", "تيك",
            "قلم", "مدر", "درس", "سرد", "مكد",
            "شجرة", "شجر", "زهرة", "هرة", "جور",
            "حبر", "حرب", "بر", "طر", "عم",
            "طعام", "معط", "شراب", "شرب", "راب",
            "نجم", "سما", "ماء", "سام", "جم"
        }

    def normalize_text(self, text):
        text = text.strip().lower()
        text = re.sub(r'^ال', '', text)
        text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
        text = text.replace('ة', 'ه')
        text = text.replace('ى', 'ي')
        text = re.sub(r'[\u064B-\u065F]', '', text)
        return text

    def start_game(self):
        self.current_question = 1
        self.players_scores = {}
        return self.next_question()

    def next_question(self):
        if self.current_question > self.max_questions:
            return self.end_game()

        self.available_letters = random.choice(self.letter_sets).copy()
        random.shuffle(self.available_letters)
        self.used_words.clear()
        self.hint_used = False
        self.current_round_words = 0

        letters_str = ' '.join(self.available_letters)
        return TextSendMessage(
            text=f"السؤال {self.current_question}/{self.max_questions}\n\nكون 3 كلمات من هذه الحروف:\n{letters_str}"
        )

    def get_hint(self):
        if self.hint_used:
            return TextSendMessage(text="تم استخدام التلميح مسبقاً")
        self.hint_used = True
        hint = "حاول تكوين كلمات من 2-3 أحرف"
        return TextSendMessage(text=f"تلميح:\n{hint}")

    def show_answer(self):
        letters_str = ''.join(self.available_letters).lower()
        suggestions = []
        for word in self.valid_words:
            temp_letters = list(letters_str)
            valid = True
            for char in word:
                if char in temp_letters:
                    temp_letters.remove(char)
                else:
                    valid = False
                    break
            if valid:
                suggestions.append(word)

        if suggestions:
            msg = f"كلمات مقترحة:\n{', '.join(suggestions[:3])}"
        else:
            msg = "لم نجد كلمات مقترحة"

        self.current_question += 1
        if self.current_question <= self.max_questions:
            next_q = self.next_question()
            return TextSendMessage(text=f"{msg}\n\n{next_q.text}")
        else:
            end_msg = self.end_game()
            return TextSendMessage(text=f"{msg}\n\n{end_msg.text}")

    def end_game(self):
        if not self.players_scores:
            return TextSendMessage(text="انتهت اللعبة\nلم يشارك أحد")

        sorted_players = sorted(self.players_scores.items(), key=lambda x: x[1]['score'], reverse=True)
        msg = "النتائج النهائية\n\n"
        for i, (name, data) in enumerate(sorted_players[:5], 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"  {i}."
            msg += f"{emoji} {name}: {data['score']} نقطة\n"

        winner = sorted_players[0]
        msg += f"\nالفائز: {winner[0]}"
        return TextSendMessage(text=msg)

    def check_answer(self, answer, user_id, display_name):
        answer_word = answer.strip().lower()

        if answer_word in self.used_words:
            return TextSendMessage(text=f"الكلمة '{answer_word}' مستخدمة مسبقاً")

        temp_letters = self.available_letters.copy()
        for letter in answer_word:
            if letter in temp_letters:
                temp_letters.remove(letter)
            else:
                letters_str = ' '.join(self.available_letters)
                return TextSendMessage(text=f"الحرف '{letter}' غير متوفر\nالحروف المتاحة: {letters_str}")

        if len(answer_word) < 2:
            return TextSendMessage(text="الكلمة يجب أن تكون حرفين على الأقل")

        normalized_word = self.normalize_text(answer_word)
        normalized_valid = {self.normalize_text(w) for w in self.valid_words}
        if normalized_word not in normalized_valid:
            return TextSendMessage(text=f"'{answer_word}' ليست كلمة صحيحة")

        self.used_words.add(answer_word)
        self.current_round_words += 1
        points = 5 if not self.hint_used else 3

        if display_name not in self.players_scores:
            self.players_scores[display_name] = {'score': 0}
        self.players_scores[display_name]['score'] += points

        if self.current_round_words >= self.words_per_question:
            msg = f"صحيح يا {display_name}"
            self.current_question += 1
            if self.current_question <= self.max_questions:
                next_q = self.next_question()
                return TextSendMessage(text=f"{msg}\n\n{next_q.text}")
            else:
                end_msg = self.end_game()
                return TextSendMessage(text=f"{msg}\n\n{end_msg.text}")
        else:
            remaining = self.words_per_question - self.current_round_words
            letters_str = ' '.join(self.available_letters)
            msg = f"صحيح يا {display_name}\nكلمة أخرى ({remaining} متبقية)\n\n{letters_str}"
            return TextSendMessage(text=msg)
