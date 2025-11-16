from linebot.models import TextSendMessage, FlexSendMessage
‏import random
‏import logging

‏logger = logging.getLogger("whale-bot")

‏def handle_text_message(event, line_bot_api, active_games, registered_players, 
‏                       user_message_count, games_lock, players_lock, 
‏                       QUESTIONS, CHALLENGES, CONFESSIONS, MENTIONS, games_map):
    """معالجة الرسائل النصية"""
‏    from utils import safe_text, get_profile_safe, check_rate
‏    from user_manager import UserManager
‏    from game_manager import GameManager
‏    from cards import (get_welcome_card, get_help_card, get_stats_card, 
‏                      get_leaderboard_card, get_registration_card, 
‏                      get_withdrawal_card, get_quick_reply)
‏    from config import NO_POINTS_GAMES
    
‏    user_id = event.source.user_id
‏    text = safe_text(event.message.text, 500) if event.message.text else ""
    
‏    if not text or not check_rate(user_id, user_message_count):
‏        return
    
‏    name = get_profile_safe(user_id, line_bot_api)
‏    game_id = getattr(event.source, 'group_id', user_id)
    
    # تحديث النشاط
‏    UserManager.update_activity(user_id, name)
‏    logger.info(f"رسالة من {name} ({user_id[-4:]}): {text[:50]}")
    
    # الأوامر الأساسية
‏    if text in ['البداية', 'ابدأ', 'start', 'البوت']:
‏        line_bot_api.reply_message(
‏            event.reply_token,
‏            FlexSendMessage(
‏                alt_text=f"مرحباً {name}",
‏                contents=get_welcome_card(name),
‏                quick_reply=get_quick_reply()
            )
        )
‏        return
    
‏    if text in ['مساعدة', 'help', 'كيف ألعب']:
‏        line_bot_api.reply_message(
‏            event.reply_token,
‏            FlexSendMessage(
‏                alt_text="المساعدة",
‏                contents=get_help_card(),
‏                quick_reply=get_quick_reply()
            )
        )
‏        return
    
‏    if text in ['نقاطي', 'إحصائياتي', 'احصائياتي']:
‏        line_bot_api.reply_message(
‏            event.reply_token,
‏            FlexSendMessage(
‏                alt_text="إحصائياتك",
‏                contents=get_stats_card(user_id, name, registered_players),
‏                quick_reply=get_quick_reply()
            )
        )
‏        return
    
‏    if text in ['الصدارة', 'المتصدرين']:
‏        line_bot_api.reply_message(
‏            event.reply_token,
‏            FlexSendMessage(
‏                alt_text="لوحة الصدارة",
‏                contents=get_leaderboard_card(),
‏                quick_reply=get_quick_reply()
            )
        )
‏        return
    
‏    if text in ['إيقاف', 'stop', 'ايقاف']:
‏        with games_lock:
‏            game_data = active_games.pop(game_id, None)
‏            if game_data:
‏                line_bot_api.reply_message(
‏                    event.reply_token,
‏                    TextSendMessage(
‏                        text=f"تم إيقاف لعبة {game_data['type']}",
‏                        quick_reply=get_quick_reply()
                    )
                )
‏            else:
‏                line_bot_api.reply_message(
‏                    event.reply_token,
‏                    TextSendMessage(
‏                        text="لا توجد لعبة نشطة",
‏                        quick_reply=get_quick_reply()
                    )
                )
‏        return
    
‏    if text in ['انضم', 'تسجيل', 'join']:
‏        with players_lock:
‏            if user_id in registered_players:
‏                line_bot_api.reply_message(
‏                    event.reply_token,
‏                    TextSendMessage(
‏                        text=f"أنت مسجل بالفعل يا {name}",
‏                        quick_reply=get_quick_reply()
                    )
                )
‏            else:
‏                registered_players.add(user_id)
‏                line_bot_api.reply_message(
‏                    event.reply_token,
‏                    FlexSendMessage(
‏                        alt_text="تم التسجيل",
‏                        contents=get_registration_card(name),
‏                        quick_reply=get_quick_reply()
                    )
                )
‏                logger.info(f"تسجيل لاعب جديد: {name} ({user_id[-4:]})")
‏        return
    
‏    if text in ['انسحب', 'خروج']:
‏        with players_lock:
‏            if user_id in registered_players:
‏                registered_players.remove(user_id)
‏                line_bot_api.reply_message(
‏                    event.reply_token,
‏                    FlexSendMessage(
‏                        alt_text="تم الانسحاب",
‏                        contents=get_withdrawal_card(name),
‏                        quick_reply=get_quick_reply()
                    )
                )
‏                logger.info(f"انسحاب لاعب: {name} ({user_id[-4:]})")
‏            else:
‏                line_bot_api.reply_message(
‏                    event.reply_token,
‏                    TextSendMessage(
‏                        text="أنت غير مسجل",
‏                        quick_reply=get_quick_reply()
                    )
                )
‏        return
    
    # الأوامر النصية للجميع
‏    if text in ['سؤال', 'سوال'] and QUESTIONS:
‏        line_bot_api.reply_message(
‏            event.reply_token,
‏            TextSendMessage(
‏                text=random.choice(QUESTIONS),
‏                quick_reply=get_quick_reply()
            )
        )
‏        return
    
‏    if text in ['تحدي', 'challenge'] and CHALLENGES:
‏        line_bot_api.reply_message(
‏            event.reply_token,
‏            TextSendMessage(
‏                text=random.choice(CHALLENGES),
‏                quick_reply=get_quick_reply()
            )
        )
‏        return
    
‏    if text in ['اعتراف', 'confession'] and CONFESSIONS:
‏        line_bot_api.reply_message(
‏            event.reply_token,
‏            TextSendMessage(
‏                text=random.choice(CONFESSIONS),
‏                quick_reply=get_quick_reply()
            )
        )
‏        return
    
‏    if text in ['منشن', 'mention'] and MENTIONS:
‏        line_bot_api.reply_message(
‏            event.reply_token,
‏            TextSendMessage(
‏                text=random.choice(MENTIONS),
‏                quick_reply=get_quick_reply()
            )
        )
‏        return
    
    # بدء الألعاب (للمسجلين فقط)
‏    with players_lock:
‏        is_registered = user_id in registered_players
    
‏    if text in games_map:
‏        if not is_registered:
‏            line_bot_api.reply_message(
‏                event.reply_token,
‏                TextSendMessage(
‏                    text="يجب التسجيل أولاً\n\nاكتب: انضم",
‏                    quick_reply=get_quick_reply()
                )
            )
‏            return
        
‏        game_class, game_type = games_map[text]
        
        # معالجة خاصة للعبة التوافق
‏        if text == 'توافق':
‏            if not game_class:
‏                line_bot_api.reply_message(
‏                    event.reply_token,
‏                    TextSendMessage(
‏                        text="اللعبة غير متوفرة",
‏                        quick_reply=get_quick_reply()
                    )
                )
‏                return
            
‏            with games_lock:
‏                game = game_class(line_bot_api)
‏                active_games[game_id] = {
‏                    'game': game,
‏                    'type': 'توافق',
‏                    'created_at': datetime.now(),
‏                    'participants': {user_id},
‏                    'answered_users': set(),
‏                    'last_game': text,
‏                    'waiting_for_names': True
                }
            
‏            response = game.start_game()
‏            if isinstance(response, FlexSendMessage):
‏                line_bot_api.reply_message(event.reply_token, response)
‏            else:
‏                line_bot_api.reply_message(
‏                    event.reply_token,
‏                    TextSendMessage(
‏                        text="لعبة التوافق\n\nاكتب اسمين مفصولين بمسافة\nمثال: أحمد فاطمة",
‏                        quick_reply=get_quick_reply()
                    )
                )
‏            logger.info("بدأت لعبة توافق")
‏            return
        
‏        GameManager.start_game(game_id, game_class, game_type, user_id, event, 
‏                              line_bot_api, active_games, registered_players, 
‏                              games_lock, players_lock)
‏        return
    
    # معالجة إجابات الألعاب
‏    if game_id in active_games:
‏        if not is_registered:
‏            return
        
‏        game_data = active_games[game_id]
        
        # معالجة لعبة التوافق
‏        if game_data.get('type') == 'توافق' and game_data.get('waiting_for_names'):
‏            from datetime import datetime
            
‏            cleaned_text = text.replace('@', '').strip()
            
‏            if '@' in text:
‏                line_bot_api.reply_message(
‏                    event.reply_token,
‏                    TextSendMessage(
‏                        text="اكتب الأسماء بدون @\nمثال: أحمد فاطمة",
‏                        quick_reply=get_quick_reply()
                    )
                )
‏                return
            
‏            names = cleaned_text.split()
‏            if len(names) < 2:
‏                line_bot_api.reply_message(
‏                    event.reply_token,
‏                    TextSendMessage(
‏                        text="يجب كتابة اسمين\nمثال: أحمد فاطمة",
‏                        quick_reply=get_quick_reply()
                    )
                )
‏                return
            
‏            game = game_data['game']
‏            try:
‏                result = game.check_answer(f"{names[0]} {names[1]}", user_id, name)
                
‏                with games_lock:
‏                    active_games.pop(game_id, None)
                
‏                if result and result.get('response'):
‏                    line_bot_api.reply_message(event.reply_token, result['response'])
‏                return
‏            except Exception as e:
‏                logger.error(f"خطأ في لعبة التوافق: {e}")
‏                return
        
        # باقي الألعاب
‏        if game_data['type'] != 'أسرع':
‏            if user_id in game_data.get('answered_users', set()):
‏                return
        
‏        game = game_data['game']
‏        game_type = game_data['type']
        
‏        try:
‏            result = game.check_answer(text, user_id, name)
‏            if result:
‏                if result.get('correct', False):
‏                    with games_lock:
‏                        if 'answered_users' not in game_data:
‏                            game_data['answered_users'] = set()
‏                        game_data['answered_users'].add(user_id)
                
‏                points = result.get('points', 0)
‏                if game_type in NO_POINTS_GAMES:
‏                    points = 0
                
‏                if points != 0:
‏                    UserManager.update_points(user_id, name, points, 
‏                                             result.get('won', False), game_type)
                
‏                if result.get('next_question', False):
‏                    with games_lock:
‏                        game_data['answered_users'] = set()
‏                    next_q = game.next_question()
‏                    if next_q:
‏                        if isinstance(next_q, TextSendMessage):
‏                            next_q.quick_reply = get_quick_reply()
‏                        line_bot_api.reply_message(event.reply_token, next_q)
‏                    return
                
‏                if result.get('game_over', False):
‏                    with games_lock:
‏                        active_games.pop(game_id, None)
                    
‏                    response = result.get('response', TextSendMessage(
‏                        text=result.get('message', '')))
‏                    if isinstance(response, TextSendMessage):
‏                        response.quick_reply = get_quick_reply()
‏                    line_bot_api.reply_message(event.reply_token, response)
‏                    return
                
‏                response = result.get('response', TextSendMessage(
‏                    text=result.get('message', '')))
‏                if isinstance(response, TextSendMessage):
‏                    response.quick_reply = get_quick_reply()
‏                elif isinstance(response, list):
‏                    for r in response:
‏                        if isinstance(r, TextSendMessage):
‏                            r.quick_reply = get_quick_reply()
‏                line_bot_api.reply_message(event.reply_token, response)
‏            return
‏        except Exception as e:
‏            logger.error(f"خطأ في معالجة الإجابة: {e}")
