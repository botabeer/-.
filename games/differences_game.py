from linebot.models import TextSendMessage, ImageSendMessage
import random

class DifferencesGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.image_pairs = [
            {"original": "https://up6.cc/2025/10/176308448198881.jpeg", "solution": "https://mrkzgulfup.com/uploads/176303338684742.jpeg", "differences": 5},
            {"original": "https://up6.cc/2025/10/176308448205332.jpeg", "solution": "https://mrkzgulfup.com/uploads/176303338695684.jpeg", "differences": 5},
            {"original": "https://up6.cc/2025/10/176308448209753.jpeg", "solution": "https://mrkzgulfup.com/uploads/176303338714356.jpeg", "differences": 5},
            {"original": "https://up6.cc/2025/10/17630844821154.jpeg", "solution": "https://mrkzgulfup.com/uploads/176303338717158.jpeg", "differences": 5},
            {"original": "https://up6.cc/2025/10/176308448213085.jpeg", "solution": "https://mrkzgulfup.com/uploads/1763033387284912.jpeg", "differences": 5}
        ]
        self.current_pair = None
        self.showed_solution = False
    
    def start_game(self):
        self.current_pair = random.choice(self.image_pairs)
        self.showed_solution = False
        
        return [
            TextSendMessage(text=f"▪️ لعبة الاختلافات\n\nابحث عن {self.current_pair['differences']} اختلافات\n\n▫️ جاوب - لعرض الحل\n\nملاحظة: للتسلية فقط، لا نقاط"),
            ImageSendMessage(original_content_url=self.current_pair['original'], preview_image_url=self.current_pair['original'])
        ]
    
    def check_answer(self, answer, user_id, display_name):
        if not self.current_pair:
            return None
        
        answer_lower = answer.strip().lower()
        
        if answer_lower in ['جاوب', 'الجواب', 'الحل', 'solution']:
            self.showed_solution = True
            return {
                'response': [
                    TextSendMessage(text="▪️ الحل:"),
                    ImageSendMessage(original_content_url=self.current_pair['solution'], preview_image_url=self.current_pair['solution'])
                ],
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': True
            }
        
        return None
