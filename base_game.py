"""
الفئة الأساسية للألعاب - Base Game Class
تحتوي على المنطق المشترك بين جميع الألعاب
"""

from abc import ABC, abstractmethod
from datetime import datetime
from linebot.models import TextSendMessage, FlexSendMessage
import random
import logging

from game_config import GameConfig
from flex_templates import FlexTemplates

logger = logging.getLogger(__name__)


class BaseGame(ABC):
    """الفئة الأساسية لجميع الألعاب"""
    
    def __init__(self, line_bot_api, game_type):
        """
        تهيئة اللعبة
        
        Args:
            line_bot_api: LINE Bot API instance
            game_type: نوع اللعبة (من GameConfig.GAME_TYPES)
        """
        self.line_bot_api = line_bot_api
        self.game_type = game_type
        self.max_questions = GameConfig.QUESTIONS_PER_GAME
        
        # حالة اللعبة
        self.current_question = 0
        self.total_score = 0
        self.correct_answers = 0
        self.wrong_answers = 0
        self.hints_used = 0
        self.answers_shown = 0
        
        # معلومات اللاعب
        self.current_player_id = None
        self.current_player_name = None
        
        # الوقت
        self.game_start_time = None
        self.question_start_time = None
        
        # البيانات
        self.current_answer = None
        self.used_hints = False
        
        logger.info(f"تم إنشاء لعبة {game_type}")
    
    def start_game(self):
        """بدء اللعبة - إنشاء السؤال الأول"""
        self.game_start_time = datetime.now()
        self.current_question = 1
        return self._generate_question()
    
    @abstractmethod
    def _generate_question(self):
        """
        توليد سؤال جديد (يجب تنفيذها في كل لعبة)
        
        Returns:
            TextSendMessage or FlexSendMessage: رسالة السؤال
        """
        pass
    
    @abstractmethod
    def _check_answer_logic(self, user_answer):
        """
        فحص الإجابة (منطق خاص بكل لعبة)
        
        Args:
            user_answer: إجابة المستخدم
            
        Returns:
            bool: True إذا كانت الإجابة صحيحة
        """
        pass
    
    def check_answer(self, user_answer, user_id, display_name):
        """
        فحص إجابة المستخدم (دالة موحدة)
        
        Args:
            user_answer: النص المرسل من المستخدم
            user_id: معرف المستخدم
            display_name: اسم المستخدم
            
        Returns:
            dict: معلومات النتيجة
        """
        self.current_player_id = user_id
        self.current_player_name = display_name
        
        # التعامل مع الأوامر الخاصة
        if user_answer in ['لمح', 'تلميح', 'hint']:
            return self._handle_hint_request()
        
        if user_answer in ['جاوب', 'الجواب', 'answer']:
            return self._handle_show_answer()
        
        # فحص الإجابة
        is_correct = self._check_answer_logic(user_answer)
        
        if is_correct:
            return self._handle_correct_answer()
        else:
            return self._handle_wrong_answer()
    
    def _handle_correct_answer(self):
        """معالجة الإجابة الصحيحة"""
        points = GameConfig.POINTS['correct_answer']
        
        # خصم نقاط التلميحات
        if self.used_hints:
            points += GameConfig.POINTS['hint_penalty']
        
        self.total_score += max(points, 0)
        self.correct_answers += 1
        self.used_hints = False
        
        # التحقق من انتهاء اللعبة
        if self.current_question >= self.max_questions:
            return self._end_game(won=True)
        
        # السؤال التالي
        self.current_question += 1
        message = f"{GameConfig.get_random_correct_message()}\n\n"
        message += f"النقاط: +{points} ⭐\n"
        message += f"المجموع: {self.total_score}\n\n"
        message += f"━━━━━━━━━━━━━━━━\n\n"
        
        next_question = self._generate_question()
        
        if isinstance(next_question, FlexSendMessage):
            return {
                'points': points,
                'won': False,
                'game_over': False,
                'response': [
                    TextSendMessage(text=message),
                    next_question
                ]
            }
        else:
            message += next_question.text if hasattr(next_question, 'text') else str(next_question)
            return {
                'points': points,
                'won': False,
                'game_over': False,
                'response': TextSendMessage(text=message)
            }
    
    def _handle_wrong_answer(self):
        """معالجة الإجابة الخاطئة"""
        self.wrong_answers += 1
        
        message = f"{GameConfig.get_random_wrong_message()}\n\n"
        message += f"الإجابة الصحيحة: {self.current_answer}\n"
        message += f"المجموع: {self.total_score} نقطة\n\n"
        
        # التحقق من انتهاء الأسئلة
        if self.current_question >= self.max_questions:
            return self._end_game(won=False)
        
        # السؤال التالي
        self.current_question += 1
        message += f"━━━━━━━━━━━━━━━━\n\n"
        
        next_question = self._generate_question()
        
        if isinstance(next_question, FlexSendMessage):
            return {
                'points': 0,
                'won': False,
                'game_over': False,
                'response': [
                    TextSendMessage(text=message),
                    next_question
                ]
            }
        else:
            message += next_question.text if hasattr(next_question, 'text') else str(next_question)
            return {
                'points': 0,
                'won': False,
                'game_over': False,
                'response': TextSendMessage(text=message)
            }
    
    def _handle_hint_request(self):
        """معالجة طلب التلميح"""
        if self.used_hints:
            return {
                'points': 0,
                'won': False,
                'game_over': False,
                'message': "⚠️ لقد استخدمت التلميح بالفعل لهذا السؤال"
            }
        
        hint = self._get_hint()
        self.used_hints = True
        self.hints_used += 1
        
        return {
            'points': 0,
            'won': False,
            'game_over': False,
            'message': GameConfig.MESSAGES['hint_used'].format(hint)
        }
    
    def _handle_show_answer(self):
        """معالجة عرض الإجابة"""
        self.answers_shown += 1
        self.wrong_answers += 1
        
        message = f"الإجابة الصحيحة: {self.current_answer}\n\n"
        
        # التحقق من انتهاء الأسئلة
        if self.current_question >= self.max_questions:
            return self._end_game(won=False)
        
        # السؤال التالي
        self.current_question += 1
        message += f"━━━━━━━━━━━━━━━━\n\n"
        
        next_question = self._generate_question()
        
        if isinstance(next_question, FlexSendMessage):
            return {
                'points': GameConfig.POINTS['show_answer_penalty'],
                'won': False,
                'game_over': False,
                'response': [
                    TextSendMessage(text=message),
                    next_question
                ]
            }
        else:
            message += next_question.text if hasattr(next_question, 'text') else str(next_question)
            return {
                'points': GameConfig.POINTS['show_answer_penalty'],
                'won': False,
                'game_over': False,
                'response': TextSendMessage(text=message)
            }
    
    def _get_hint(self):
        """
        الحصول على تلميح (افتراضي)
        يمكن تجاوزها في الألعاب المحددة
        """
        if not self.current_answer:
            return "لا يوجد تلميح متاح"
        
        answer = str(self.current_answer)
        hint_length = max(1, len(answer) // 3)
        return answer[:hint_length] + "..."
    
    def _end_game(self, won):
        """
        إنهاء اللعبة وعرض النتائج
        
        Args:
            won: True إذا فاز اللاعب
        """
        # حساب الوقت المستغرق
        time_taken = ""
        if self.game_start_time:
            elapsed = datetime.now() - self.game_start_time
            minutes = int(elapsed.total_seconds() // 60)
            seconds = int(elapsed.total_seconds() % 60)
            time_taken = f"{minutes}د {seconds}ث" if minutes > 0 else f"{seconds}ث"
        
        # مكافأة اللعبة المثالية
        if self.correct_answers == self.max_questions and self.hints_used == 0:
            self.total_score += GameConfig.POINTS['perfect_game_bonus']
        
        # إنشاء رسالة الفوز
        winner_flex = FlexTemplates.get_winner_announcement(
            winner_name=self.current_player_name or "اللاعب",
            game_type=self.game_type,
            total_score=self.total_score,
            questions_count=self.max_questions,
            correct_answers=self.correct_answers,
            wrong_answers=self.wrong_answers,
            time_taken=time_taken
        )
        
        logger.info(f"انتهت لعبة {self.game_type} - النقاط: {self.total_score}")
        
        return {
            'points': self.total_score,
            'won': won,
            'game_over': True,
            'response': FlexSendMessage(
                alt_text=f"انتهت اللعبة - النقاط: {self.total_score}",
                contents=winner_flex
            )
        }
    
    def _normalize_text(self, text):
        """تطبيع النص للمقارنة"""
        if not text:
            return ""
        
        import re
        text = text.strip().lower()
        text = re.sub(r'^ال', '', text)
        text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
        text = text.replace('ة', 'ه')
        text = text.replace('ى', 'ي')
        text = re.sub(r'[\u064B-\u065F]', '', text)
        return text
