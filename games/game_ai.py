# ============================================
# games/game_ai.py - محادثة ذكية مع AI
# ============================================

"""
محادثة AI
=========
محادثة قصيرة مع الذكاء الاصطناعي
لعبة ترفيهية بدون تلميح أو إظهار إجابة
جولة واحدة فقط
"""

import random
from .base import BaseGame
from rules import POINTS, GAMES_INFO


class AiChat(BaseGame):
    """محادثة ذكية مع AI (نسخة بسيطة)"""
    
    def __init__(self):
        game_info = GAMES_INFO['ai']
        super().__init__(
            name=game_info['name'],
            rounds=game_info['rounds'],  # جولة واحدة
            supports_hint=game_info['supports_hint']  # False
        )
        
        # قاعدة بيانات الردود الذكية
        self.responses_db = {
            'greeting': [
                'مرحباً! كيف يمكنني مساعدتك اليوم؟',
                'أهلاً وسهلاً! سعيد بالحديث معك',
                'مرحباً بك! ما الذي تود الحديث عنه؟'
            ],
            'how_are_you': [
                'أنا بخير، شكراً لسؤالك! كيف حالك أنت؟',
                'أنا روبوت، لكني أعمل بشكل رائع! وأنت؟',
                'بخير والحمد لله، وأنت كيف حالك؟'
            ],
            'thanks': [
                'العفو! سعيد بمساعدتك',
                'لا شكر على واجب',
                'تسرني خدمتك دائماً'
            ],
            'game': [
                'الألعاب ممتعة! هل تريد لعب شيء معين؟',
                'أحب الألعاب! ما هي لعبتك المفضلة؟',
                'هناك العديد من الألعاب الممتعة هنا'
            ],
            'help': [
                'يمكنني مساعدتك! ماذا تحتاج؟',
                'بالتأكيد، أخبرني كيف أساعدك',
                'أنا هنا للمساعدة، ما المشكلة؟'
            ],
            'joke': [
                'لماذا لا يثق الناس بالسلالم؟ لأنها دائماً تخطط لشيء!',
                'ما الذي يقوله البحر للشاطئ؟ لا شيء، هو فقط يلوح!',
                'لماذا الأسماك ذكية جداً؟ لأنها تعيش في مدارس!'
            ],
            'weather': [
                'لست متأكداً من الطقس، لكني آمل أن يكون جميلاً!',
                'الطقس خارج معرفتي، لكن أتمنى أن يكون مناسباً لك',
                'لا أستطيع معرفة الطقس، لكن أتمنى لك يوماً جميلاً'
            ],
            'name': [
                'اسمي بوت الحوت! سعيد بمعرفتك',
                'يمكنك مناداتي بوت الحوت',
                'أنا بوت الحوت، مساعدك الذكي'
            ],
            'goodbye': [
                'وداعاً! أتمنى أن ألقاك قريباً',
                'إلى اللقاء! كان من الرائع الحديث معك',
                'مع السلامة! استمتع بوقتك'
            ],
            'default': [
                'هذا مثير للاهتمام! أخبرني المزيد',
                'أفهم ما تقول، هل يمكنك التوضيح أكثر؟',
                'رائع! ماذا أيضاً؟',
                'مممم، مثير للتفكير!',
                'أجل، أفهم ذلك'
            ]
        }
        
        # كلمات مفتاحية
        self.keywords = {
            'greeting': ['مرحبا', 'أهلا', 'هلا', 'السلام', 'صباح', 'مساء', 'هاي', 'هلو'],
            'how_are_you': ['كيف حالك', 'كيفك', 'شلونك', 'ايش اخبارك', 'وش اخبارك'],
            'thanks': ['شكرا', 'شكراً', 'تسلم', 'يعطيك العافية', 'مشكور'],
            'game': ['لعبة', 'العاب', 'ألعاب', 'لعب'],
            'help': ['مساعدة', 'ساعدني', 'help'],
            'joke': ['نكتة', 'اضحكني', 'طرفة'],
            'weather': ['طقس', 'جو', 'حرارة', 'مطر'],
            'name': ['اسمك', 'شنو اسمك', 'وش اسمك', 'من انت'],
            'goodbye': ['وداعا', 'باي', 'سلام', 'مع السلامة']
        }
        
        self.conversation_count = 0
        self.max_messages = 5
    
    def generate_question(self):
        """
        توليد سؤال جديد (رسالة ترحيب)
        
        Returns:
            نص السؤال
        """
        welcome_message = random.choice(self.responses_db['greeting'])
        question = f"{welcome_message}\n\nيمكنك إرسال 5 رسائل كحد أقصى"
        
        return question
    
    def detect_intent(self, message):
        """
        تحديد نية المستخدم من الرسالة
        
        Args:
            message: رسالة المستخدم
            
        Returns:
            نوع النية
        """
        message_lower = message.lower()
        
        for intent, keywords in self.keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return intent
        
        return 'default'
    
    def generate_response(self, user_message):
        """
        توليد رد على رسالة المستخدم
        
        Args:
            user_message: رسالة المستخدم
            
        Returns:
            الرد المناسب
        """
        # تحديد النية
        intent = self.detect_intent(user_message)
        
        # اختيار رد عشوائي من القائمة
        responses = self.responses_db.get(intent, self.responses_db['default'])
        response = random.choice(responses)
        
        return response
    
    def check_answer(self, user_id, answer):
        """
        التحقق من الإجابة (معالجة الرسالة)
        
        Args:
            user_id: معرف المستخدم
            answer: رسالة المستخدم
            
        Returns:
            dict مع النتيجة
        """
        self.conversation_count += 1
        
        # توليد رد
        ai_response = self.generate_response(answer)
        
        # التحقق من انتهاء المحادثة
        game_ended = self.conversation_count >= self.max_messages
        
        if game_ended:
            ai_response += "\n\nانتهت المحادثة! شكراً لوقتك الممتع"
            self.is_active = False
        
        result = {
            'correct': True,
            'ai_response': ai_response,
            'message_count': self.conversation_count,
            'max_messages': self.max_messages,
            'points_earned': 0,
            'total_points': 0,
            'current_round': 1,
            'total_rounds': 1,
            'game_ended': game_ended,
            'next_question': None
        }
        
        return result
    
    def get_hint(self):
        """
        لا تدعم التلميح
        
        Returns:
            None
        """
        return None
    
    def show_answer(self):
        """
        لا تدعم إظهار الإجابة
        
        Returns:
            None
        """
        return None
