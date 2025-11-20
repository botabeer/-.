# ============================================
# gemini_service.py - خدمة Gemini AI
# ============================================

import google.generativeai as genai
from rules import GEMINI_CONFIG
import logging

logger = logging.getLogger(__name__)

class GeminiService:
    """خدمة Gemini AI مع Load Balancing بين API Keys"""
    
    def __init__(self):
        self.api_keys = [k for k in GEMINI_CONFIG['api_keys'] if k]
        self.current_key_index = 0
        self.model_name = GEMINI_CONFIG['model']
        self.model = None
        self._init_model()
    
    def _init_model(self):
        """تهيئة النموذج"""
        if not self.api_keys:
            logger.error("No Gemini API keys available")
            return
        
        try:
            genai.configure(api_key=self.api_keys[self.current_key_index])
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    'temperature': GEMINI_CONFIG['temperature'],
                    'max_output_tokens': GEMINI_CONFIG['max_tokens']
                },
                system_instruction=GEMINI_CONFIG['system_instruction']
            )
            logger.info(f"Gemini initialized with key {self.current_key_index + 1}")
        except Exception as e:
            logger.error(f"Gemini init failed: {e}")
            self.model = None
    
    def _rotate_key(self):
        """تبديل API Key عند الفشل"""
        if len(self.api_keys) <= 1:
            return False
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self._init_model()
        return True
    
    def generate_response(self, message, retry=True):
        """توليد رد من Gemini"""
        if not self.model:
            return "عذراً، خدمة المحادثة الذكية غير متاحة حالياً"
        
        try:
            response = self.model.generate_content(message)
            return response.text
        except Exception as e:
            logger.error(f"Gemini generate error: {e}")
            if retry and self._rotate_key():
                return self.generate_response(message, retry=False)
            return "عذراً، حدث خطأ في المحادثة"
    
    def chat(self, user_message, context=None):
        """محادثة مع سياق"""
        full_message = f"{context}\n\n{user_message}" if context else user_message
        return self.generate_response(full_message)

gemini = GeminiService()
