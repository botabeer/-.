# games/game_ai.py
from games.base import BaseGame

# ============================================
# خدمة Gemini مع تبديل المفاتيح تلقائياً
# ============================================
class GeminiService:
    def __init__(self):
        self.api_keys = [
            "GEMINI_API_KEY_1",
            "GEMINI_API_KEY_2",
            "GEMINI_API_KEY_3"
        ]
        self.current_key_index = 0
        self.model = "gemini-2.0-flash-exp"
        self.client = self._create_client(self.api_keys[self.current_key_index])

    def _create_client(self, api_key):
        # افترض وجود واجهة Gemini مشابهة لـ OpenAI API
        from openai import Gemini
        return Gemini(api_key=api_key, model=self.model)

    def _rotate_key(self):
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self.client = self._create_client(self.api_keys[self.current_key_index])

    def generate_response(self, prompt):
        for _ in range(len(self.api_keys)):
            try:
                response = self.client.chat(prompt=prompt)
                return response['text']  # حسب هيكل الاستجابة
            except Exception as e:
                print(f"[GeminiService] خطأ مع المفتاح {self.api_keys[self.current_key_index]}: {e}")
                self._rotate_key()
        return "عذرًا، حدث خطأ في الاتصال بالـ AI."

# ============================================
# لعبة AiChat
# ============================================
class AiChat(BaseGame):
    """
    لعبة ترفيهية: محادثة AI
    ========================
    المميزات:
    ✅ ذكاء شبيه بشات GPT
    ✅ ردود مختصرة وواضحة
    ✅ بدون إيموجي
    ❌ بدون سياق
    ❌ بدون حد للرسائل
    """

    def __init__(self):
        super().__init__('محادثة AI', rounds=1, supports_hint=False, supports_skip=False)
        self.gemini = GeminiService()

    def generate_question(self):
        self.current_question = "ابدأ المحادثة..."
        return {
            'text': self.current_question,
            'answer': None
        }

    def check_answer(self, user_id, answer):
        answer = answer.strip()
        if not answer:
            return {
                'correct': False,
                'message': 'الرجاء كتابة رسالة',
                'points': 0
            }

        # توليد رد ذكي بدون سياق، مختصر، وبدون ايموجي
        prompt = (
            "أنت مساعد ذكي يشبه ChatGPT، أجب على كل رسالة بمفردها، "
            "ردود مختصرة وواضحة، بدون أي إيموجي.\n\n"
            f"المستخدم: {answer}\nAI:"
        )
        response = self.gemini.generate_response(prompt).strip()

        return {
            'correct': True,
            'message': response,
            'points': 0
        }
