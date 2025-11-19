# games/game_ai.py
"""
لعبة المحادثة الذكية (AI Chat)
محادثة قصيرة مع الذكاء الاصطناعي
"""

import random
import logging

logger = logging.getLogger(__name__)

class AI_Game:
    """لعبة المحادثة مع AI"""
    
    def __init__(self):
        self.name = "AI Chat"
        self.name_ar = "محادثة ذكية"
        self.description = "تحدث مع الذكاء الاصطناعي واحصل على ردود ذكية"
        
        # ردود جاهزة لمواضيع مختلفة
        self.responses = {
            'مرحبا': ['مرحباً بك! كيف يمكنني مساعدتك اليوم؟', 'أهلاً وسهلاً! أنا هنا للمساعدة'],
            'السلام': ['وعليكم السلام ورحمة الله وبركاته', 'السلام عليكم! كيف حالك؟'],
            'هاي': ['هاي! كيف أقدر أساعدك؟', 'هلا! وش اللي تبغاه؟'],
            'هلا': ['هلا والله! تفضل', 'هلا فيك! كيف أقدر أخدمك؟'],
            
            'كيف حالك': ['الحمدلله بخير! وأنت كيف حالك؟', 'تمام والحمدلله! شكراً على السؤال'],
            'وش اخبارك': ['أخباري طيبة! وأنت وش أخبارك؟', 'كله تمام! شكراً'],
            'شلونك': ['زين الحمدلله! وانت شلونك؟', 'بخير وصحة!'],
            
            'اسمك': ['اسمي بوت الحوت!', 'يمكنك مناداتي بـ "بوت الحوت"'],
            'من انت': ['أنا بوت ذكي للألعاب والترفيه!', 'بوت الحوت في خدمتك!'],
            'وش اسمك': ['بوت الحوت!', 'اسمي الحوت، تشرفت!'],
            
            'وش تقدر تسوي': ['أقدر ألعب معك 9 ألعاب مختلفة! جرب اكتب "ابدأ"', 'ألعاب، نقاط، صدارة، وأشياء كثيرة!'],
            'ساعدني': ['تفضل! كيف أقدر أساعدك؟ اكتب "مساعدة" لرؤية الأوامر', 'أنا هنا! وش اللي تحتاجه؟'],
            
            'الطقس': ['الطقس اليوم جميل!', 'ما عندي معلومات عن الطقس، بس أقدر ألعب معك!'],
            'الوقت': ['الوقت دائماً مناسب للعب!', 'ما أعرف الوقت بالضبط، بس وقتنا معك يمر بسرعة!'],
            
            'لماذا': ['سؤال فلسفي! الجواب يعتمد على السياق', 'لأن كل شيء له سبب!'],
            'كيف': ['بطرق مختلفة! وش اللي تحتاج تعرفه بالضبط؟', 'الطريقة تعتمد على الموقف'],
            
            'احبك': ['وأنا أحب أن ألعب معك!', 'شكراً! أنت رائع!'],
            'شكرا': ['العفو! دائماً في الخدمة', 'لا شكر على واجب!'],
            'جميل': ['أنت الأجمل!', 'شكراً! أنت لطيف جداً'],
            'رائع': ['أنت الرائع!', 'سعيد أنك أعجبت!'],
            
            'سيء': ['آسف على ذلك، كيف أقدر أحسّن؟', 'دعني أحاول مرة أخرى!'],
            'غبي': ['آسف إذا أخطأت، أنا أتعلم دائماً', 'أحاول أن أكون أفضل!'],
            
            'لون': ['الأزرق! مثل البحر والحوت', 'كل الألوان جميلة!'],
            'رقم': ['رقمي المفضل 9 - عدد ألعابنا!', '7 رقم محظوظ!'],
            'طعام': ['البيتزا! بس أنا ما آكل، أنا بوت', 'الكبسة رائعة!'],
            
            'العب': ['يلا! اكتب "ابدأ" ونبدأ اللعب!', 'تمام! جاهز؟ اكتب "ابدأ"'],
            'لعبة': ['عندنا 9 ألعاب! اكتب "ابدأ"', 'يلا نلعب!'],
            
            'باي': ['باي باي! ارجع لنا قريب', 'مع السلامة! نلتقي قريباً'],
            'مع السلامة': ['الله يسلمك!', 'في أمان الله!'],
        }
        
        self.smart_responses = [
            'مثير للاهتمام! أخبرني المزيد',
            'فهمت! هل تريد أن نلعب؟',
            'رائع! ماذا تريد أن تفعل الآن؟',
            'حسناً! جرب اكتب "ابدأ" للعب',
            'ممتاز! عندي فكرة - لنلعب لعبة!',
            'أنت محق! وش رأيك نلعب شوية؟',
            'صحيح! اكتب "ابدأ" ونبدأ المتعة',
            'هذا جيد! هل تريد تجربة لعبة؟',
            'فكرة جميلة! جرب ألعابنا الـ9',
            'عندنا ألعاب كثيرة، جربها!',
        ]
        
        self.confused_responses = [
            'معليش ما فهمت! جرب تكتب بطريقة ثانية',
            'اعذرني! ممكن توضح أكثر؟',
            'ما قدرت أفهم، جرب كلمات أبسط',
            'همم... ممكن تعيد السؤال؟',
            'صعبة شوي! وش اللي تقصده؟',
        ]
    
    def start(self, group_id, user_id, user_name):
        """بدء المحادثة مع AI"""
        game_data = {
            'type': 'ai',
            'mode': 'chat',
            'user_id': user_id,
            'user_name': user_name,
            'conversation_count': 0
        }
        
        message = f"""**محادثة ذكية**

مرحباً {user_name}!

أنا هنا للدردشة معك! تكلم معي عن أي شيء:
• اسألني أي سؤال
• شاركني أفكارك
• أو فقط سلّم عليّ

نصيحة: اكتب "ابدأ" في أي وقت للعب!
"""
        
        return {
            'game_data': game_data,
            'message': message
        }
    
    def check_answer(self, game_data, answer, user_id, user_name, group_id, active_games):
        """معالجة رسالة المستخدم وإرجاع رد"""
        if not answer or len(answer.strip()) == 0:
            return {'correct': False}
        
        game_data['conversation_count'] = game_data.get('conversation_count', 0) + 1
        answer_lower = answer.lower().strip()
        response = self._find_response(answer_lower)
        
        if game_data['conversation_count'] >= 5:
            response += '\n\nجربت ألعابنا؟ اكتب "ابدأ" !'
        
        return {
            'correct': False,
            'message': response,
            'game_over': False
        }
    
    def _find_response(self, text):
        """البحث عن أفضل رد"""
        for keyword, responses in self.responses.items():
            if keyword in text:
                return random.choice(responses)
        
        words = text.split()
        for word in words:
            for keyword, responses in self.responses.items():
                if word == keyword or word in keyword or keyword in word:
                    return random.choice(responses)
        
        return random.choice(self.smart_responses if random.random() < 0.7 else self.confused_responses)
    
    def get_hint(self, game_data):
        """لا يوجد تلميح في المحادثة"""
        return "هذه محادثة حرة! تكلم معي عن أي شيء أو اكتب 'ابدأ' لبدء لعبة جديدة"
    
    def show_answer(self, game_data, group_id, active_games):
        """إنهاء المحادثة"""
        conversation_count = game_data.get('conversation_count', 0)
        message = f"""**انتهت المحادثة**

تحدثنا {conversation_count} مرة!

هل تريد:
• محادثة جديدة → اكتب "اي"
• لعبة مختلفة → اكتب "ابدأ"
"""
        if group_id in active_games:
            del active_games[group_id]
        
        return {'message': message}
    
    def create_flex_message(self, title, content, color='#00D9FF'):
        """إنشاء Flex Message للمحادثة"""
        return {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": f"{title}", "weight": "bold", "size": "xl", "color": color},
                    {"type": "separator", "margin": "md"},
                    {"type": "text", "text": content, "wrap": True, "margin": "md", "size": "sm"}
                ]
            }
        }
