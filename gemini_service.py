import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

class GeminiService:
    def __init__(self):
        self.api_keys = []
        for i in range(1, 10):
            key = os.getenv(f'GEMINI_API_KEY_{i}')
            if key:
                self.api_keys.append(key)
        
        if not self.api_keys:
            raise ValueError("لا توجد مفاتيح Gemini API في ملف .env")
        
        self.current_key_index = 0
        self.model_name = 'gemini-2.0-flash-exp'
        self.system_instruction = '''أنت مساعد ذكي عربي ودود ومفيد. 
تحدث بطريقة طبيعية وودية.
أجب على الأسئلة بشكل مختصر وواضح.
استخدم اللغة العربية الفصحى البسيطة.
كن محترما ومهذبا في جميع الردود.'''
        
        self._configure_current_key()
    
    def _configure_current_key(self):
        current_key = self.api_keys[self.current_key_index]
        genai.configure(api_key=current_key)
    
    def _rotate_key(self):
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self._configure_current_key()
    
    def generate_response(self, message, retry=True):
        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=self.system_instruction
            )
            
            generation_config = {
                'temperature': 0.9,
                'top_p': 0.95,
                'top_k': 40,
                'max_output_tokens': 500
            }
            
            response = model.generate_content(
                message,
                generation_config=generation_config
            )
            
            return response.text
        
        except Exception as e:
            error_msg = str(e)
            
            if 'quota' in error_msg.lower() or 'limit' in error_msg.lower():
                if retry and len(self.api_keys) > 1:
                    self._rotate_key()
                    return self.generate_response(message, retry=False)
            
            return "عذرا، حدث خطأ في معالجة طلبك. حاول مرة أخرى."
    
    def chat(self, messages_history):
        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=self.system_instruction
            )
            
            chat = model.start_chat(history=[])
            
            for msg in messages_history:
                chat.send_message(msg)
            
            return chat.last.text
        
        except Exception as e:
            return "عذرا، حدث خطأ في المحادثة."
