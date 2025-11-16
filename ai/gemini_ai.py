"""
واجهة Gemini AI
"""
from typing import Optional
import logging

logger = logging.getLogger("whale-bot")

USE_AI = False
ask_gemini = None

try:
    import google.generativeai as genai
    from config import config
    from utils import safe_text

    if config.gemini_keys:
        genai.configure(api_key=config.gemini_keys[0])
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        USE_AI = True
        logger.info(f"✅ Gemini AI جاهز ({len(config.gemini_keys)} مفاتيح)")

        def ask_gemini(prompt: str, max_retries: int = 2) -> Optional[str]:
            """استدعاء Gemini AI مع إعادة المحاولة"""
            for attempt in range(max_retries):
                try:
                    response = model.generate_content(prompt)
                    if response and response.text:
                        return safe_text(response.text.strip(), 1000)
                except Exception as e:
                    logger.error(f"❌ خطأ Gemini (محاولة {attempt + 1}): {e}")
                    # التبديل للمفتاح التالي إذا كان هناك أكثر من مفتاح
                    if attempt < max_retries - 1 and len(config.gemini_keys) > 1:
                        key_index = (attempt + 1) % len(config.gemini_keys)
                        genai.configure(api_key=config.gemini_keys[key_index])
            return None

except ImportError:
    logger.warning("⚠️ مكتبة Gemini غير مثبتة")
except Exception as e:
    logger.warning(f"⚠️ Gemini غير متوفر: {e}")
