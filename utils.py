import os
‏import re
‏from typing import List
‏from datetime import datetime, timedelta
‏from linebot.exceptions import LineBotApiError
‏import logging

‏logger = logging.getLogger("whale-bot")

‏def safe_text(text: any, max_length: int = 500) -> str:
    """تنظيف النص من الأحرف الخطرة"""
‏    if text is None:
‏        return ""
    
‏    text = str(text).strip()
‏    text = text.replace('"', '').replace("'", '').replace('\\', '')
‏    text = text.replace('<', '').replace('>', '')
‏    return text[:max_length]

‏def normalize_text(text: str) -> str:
    """تطبيع النص العربي للمقارنة"""
‏    if not text:
‏        return ""
    
‏    text = text.strip().lower()
‏    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
‏    text = text.replace('ؤ', 'و').replace('ئ', 'ي').replace('ء', '')
‏    text = text.replace('ة', 'ه').replace('ى', 'ي')
‏    text = re.sub(r'[\u064B-\u065F]', '', text)
‏    text = re.sub(r'\s+', ' ', text)
‏    return text

‏def load_file(filename: str) -> List[str]:
    """تحميل ملف نصي بشكل آمن"""
‏    try:
‏        filepath = os.path.join('games', filename)
‏        if not os.path.exists(filepath):
‏            logger.warning(f"الملف غير موجود: {filename}")
‏            return []
        
‏        with open(filepath, 'r', encoding='utf-8') as f:
‏            lines = [safe_text(line) for line in f if line.strip()]
        
‏        logger.info(f"تم تحميل {len(lines)} سطر من {filename}")
‏        return lines
‏    except Exception as e:
‏        logger.error(f"خطأ في تحميل {filename}: {e}")
‏        return []

‏def get_profile_safe(user_id: str, line_bot_api) -> str:
    """جلب اسم المستخدم بشكل آمن"""
‏    from cache import names_cache
    
‏    cached = names_cache.get(user_id)
‏    if cached:
‏        return cached
    
‏    fallback_name = f"لاعب {user_id[-4:]}"
    
‏    if not line_bot_api:
‏        return fallback_name
    
‏    try:
‏        profile = line_bot_api.get_profile(user_id)
‏        display_name = safe_text(profile.display_name, 50) if profile.display_name else fallback_name
‏        names_cache.set(user_id, display_name)
‏        return display_name
‏    except LineBotApiError as e:
‏        if e.status_code != 404:
‏            logger.error(f"خطأ LINE API ({e.status_code}): {e.message}")
‏    except Exception as e:
‏        logger.error(f"خطأ غير متوقع في جلب الملف: {e}")
    
‏    names_cache.set(user_id, fallback_name)
‏    return fallback_name

‏def check_rate(user_id: str, user_message_count: dict) -> bool:
    """فحص معدل الرسائل"""
‏    from config import config
    
‏    now = datetime.now()
‏    data = user_message_count[user_id]
    
‏    if now - data['reset_time'] > timedelta(seconds=config.rate_limit_window):
‏        data['count'] = 0
‏        data['reset_time'] = now
    
‏    if data['count'] >= config.rate_limit_max:
‏        return False
    
‏    data['count'] += 1
‏    return True
