import os
‏import hashlib
‏from dataclasses import dataclass
‏from typing import List
‏import logging

‏logger = logging.getLogger("whale-bot")

‏@dataclass
‏class BotConfig:
    """إعدادات البوت"""
‏    line_token: str
‏    line_secret: str
‏    gemini_keys: List[str]
‏    admin_token: str
‏    db_name: str = 'game_bot.db'
‏    rate_limit_max: int = 30
‏    rate_limit_window: int = 60
‏    inactive_days: int = 45
‏    game_timeout_minutes: int = 15
‏    cleanup_interval_seconds: int = 300
‏    names_cache_max: int = 1000
    
‏    @classmethod
‏    def from_env(cls):
        """تحميل الإعدادات من المتغيرات البيئية"""
‏        return cls(
‏            line_token=os.getenv('LINE_CHANNEL_ACCESS_TOKEN', ''),
‏            line_secret=os.getenv('LINE_CHANNEL_SECRET', ''),
‏            gemini_keys=[k for k in [
‏                os.getenv('GEMINI_API_KEY_1', ''),
‏                os.getenv('GEMINI_API_KEY_2', '')
‏            ] if k],
‏            admin_token=os.getenv('ADMIN_TOKEN', hashlib.sha256(b'default_admin').hexdigest())
        )
    
‏    def validate(self) -> bool:
        """التحقق من صحة الإعدادات"""
‏        if not self.line_token or not self.line_secret:
‏            logger.error("متغيرات LINE مفقودة")
‏            return False
‏        return True

# نظام الألوان
‏THEME = {
‏    'bg': '#F5F5F7',
‏    'card': '#FFFFFF',
‏    'card_alt': '#FAFAFA',
‏    'text': '#1D1D1F',
‏    'text_secondary': '#86868B',
‏    'text_light': '#A1A1A6',
‏    'accent': '#000000',
‏    'accent_light': '#424245',
‏    'border': '#E5E5EA',
‏    'hover': '#F0F0F2',
‏    'shadow': 'rgba(0, 0, 0, 0.08)'
}

‏NO_POINTS_GAMES = {'اختلاف', 'توافق', 'سؤال', 'اعتراف', 'تحدي', 'منشن'}

‏config = BotConfig.from_env()
