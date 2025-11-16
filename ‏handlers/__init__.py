"""استيراد معالجات الأحداث"""
‏from .message_handler import handle_text_message

‏__all__ = ['handle_text_message']

# ═══════════════════════════════════════════════════════════════
‏# handlers/message_handler.py
# ═══════════════════════════════════════════════════════════════
"""معالجة الرسائل النصية"""
‏from linebot.models import TextSendMessage, FlexSendMessage
‏from datetime import datetime
‏import random
‏import logging

‏logger = logging.getLogger("whale-bot")

‏def handle_text_message(event, line_bot_api, active_games, registered_players, 
‏                       user_message_count, games_lock, players_lock, 
‏                       QUESTIONS, CHALLENGES, CONFESSIONS, MENTIONS, games_map):
    """معالجة الرسائل النصية"""
‏    from utils import safe_text, get_profile_safe, check_rate
‏    from managers import UserManager, GameManager
‏    from ui import (get_welcome_card, get_help_card, get_stats_card, 
‏                   get_leaderboard_card, get_registration_card, 
‏                   get_withdrawal_card, get_quick_reply)
‏    from config import NO_POINTS_GAMES
    
‏    user_id = event.source.user_id
‏    text = safe_text(event.message.text, 500) if event.message.text else ""
    
‏    if not text or not check_rate(user_id, user_message_count):
‏        return
    
‏    name = get_profile_safe(user_id, line_bot_api)
‏    game_id = getattr(event.source, 'group_id', user_id)
    
    # تحديث النشاط
‏    UserManager.update_activity(user_id, name)
‏    logger.info(f"💬 رسالة من {name} ({user_id[-4:]}): {text[:50]}")
