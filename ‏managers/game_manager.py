"""إدارة الألعاب"""
‏from datetime import datetime, timedelta
‏from typing import Dict
‏from linebot.models import TextSendMessage
‏import logging

‏logger = logging.getLogger("whale-bot")

‏class GameManager:
    """مدير الألعاب"""
    
‏    @staticmethod
‏    def start_game(game_id: str, game_class: any, game_type: str, 
‏                   user_id: str, event, line_bot_api, active_games: dict, 
‏                   registered_players: set, games_lock, players_lock) -> bool:
        """بدء لعبة جديدة"""
‏        from ui import get_quick_reply
‏        from ai import USE_AI, ask_gemini
        
‏        if not game_class:
‏            try:
‏                line_bot_api.reply_message(
‏                    event.reply_token,
‏                    TextSendMessage(
‏                        text=f"لعبة {game_type} غير متوفرة حالياً",
‏                        quick_reply=get_quick_reply()
                    )
                )
‏            except Exception as e:
‏                logger.error(f"خطأ في إرسال رسالة: {e}")
‏            return False
        
‏        try:
‏            with games_lock:
                # إنشاء اللعبة
‏                game_classes_with_ai = ['SongGame', 'HumanAnimalPlantGame', 'LettersWordsGame']
‏                if game_class.__name__ in game_classes_with_ai:
‏                    game = game_class(line_bot_api, use_ai=USE_AI, ask_ai=ask_gemini)
‏                else:
‏                    game = game_class(line_bot_api)
                
                # إضافة المشاركين
‏                with players_lock:
‏                    participants = registered_players.copy()
‏                    participants.add(user_id)
                
                # حفظ اللعبة
‏                active_games[game_id] = {
‏                    'game': game,
‏                    'type': game_type,
‏                    'created_at': datetime.now(),
‏                    'participants': participants,
‏                    'answered_users': set(),
‏                    'last_game': game_type
                }
            
            # بدء اللعبة
‏            response = game.start_game()
            
            # إضافة Quick Reply
‏            if isinstance(response, TextSendMessage):
‏                response.quick_reply = get_quick_reply()
‏            elif isinstance(response, list):
‏                for r in response:
‏                    if isinstance(r, TextSendMessage):
‏                        r.quick_reply = get_quick_reply()
            
‏            line_bot_api.reply_message(event.reply_token, response)
‏            logger.info(f"✅ بدأت لعبة {game_type} للمستخدم {user_id[-4:]}")
‏            return True
        
‏        except Exception as e:
‏            logger.error(f"❌ خطأ في بدء لعبة {game_type}: {e}")
‏            try:
‏                line_bot_api.reply_message(
‏                    event.reply_token,
‏                    TextSendMessage(
‏                        text="حدث خطأ في بدء اللعبة، يرجى المحاولة مرة أخرى",
‏                        quick_reply=get_quick_reply()
                    )
                )
‏            except:
‏                pass
‏            return False
    
‏    @staticmethod
‏    def cleanup_old_games(active_games: dict, games_lock, timeout_minutes: int = 15) -> int:
        """حذف الألعاب القديمة"""
‏        count = 0
‏        now = datetime.now()
        
‏        with games_lock:
‏            to_delete = [
‏                gid for gid, gdata in active_games.items()
‏                if (now - gdata.get('created_at', now)) > timedelta(minutes=timeout_minutes)
            ]
            
‏            for gid in to_delete:
‏                active_games.pop(gid, None)
‏                count += 1
        
‏        if count > 0:
‏            logger.info(f"🧹 تم حذف {count} لعبة قديمة")
        
‏        return count
