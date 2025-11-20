from games.base import BaseGame
from gemini_service import GeminiService

class AIGame(BaseGame):
    def __init__(self):
        super().__init__('محادثة AI', rounds=1, supports_hint=False, supports_skip=False)
        self.gemini = GeminiService()
        self.message_count = 0
        self.max_messages = 5
    
    def generate_question(self):
        self.current_question = "ابدأ المحادثة..."
        self.message_count = 0
        return {
            'text': self.current_question,
            'answer': None
        }
    
    def check_answer(self, user_id, answer):
        if self.message_count >= self.max_messages:
            return {
                'correct': False,
                'message': 'انتهى حد المحادثة (5 رسائل كحد اقصى)',
                'points': 0
            }
        
        answer = answer.strip()
        
        if not answer:
            return {
                'correct': False,
                'message': 'الرجاء كتابة رسالة',
                'points': 0
            }
        
        response = self.gemini.generate_response(answer)
        
        self.message_count += 1
        
        return {
            'correct': True,
            'message': response,
            'points': 0
        }
