from linebot.models import FlexSendMessage
from game_opposite import OppositeGame
from game_song import SongGame
from game_chain import ChainWordsGame
from game_order import OrderGame

GAME_CLASSES = {
    'ضد': OppositeGame,
    'اغنية': SongGame,
    'سلسلة': ChainWordsGame,
    'ترتيب': OrderGame
}

def start_game(group_id, game_type, user_id, user_name):
    """بدء لعبة جديدة"""
    game_class = GAME_CLASSES.get(game_type)
    if not game_class:
        return {'message': 'نوع اللعبة غير موجود', 'game_data': None}
    
    game_instance = game_class()
    result = game_instance.start_game()
    
    game_data = {
        'type': game_type,
        'instance': game_instance,
        'players': [user_id]
    }
    
    return {
        'message': f'بدأت لعبة {game_type}',
        'game_data': game_data,
        'flex': result.contents if isinstance(result, FlexSendMessage) else None
    }

def check_game_answer(game, text, user_id, user_name, group_id, active_games):
    """فحص إجابة اللاعب"""
    if 'instance' not in game:
        return None
    
    game_instance = game['instance']
    result = game_instance.check_answer(text, user_id, user_name)
    
    if result and result.get('correct'):
        next_q = game_instance.next_question()
        if next_q:
            return {
                'message': 'إجابة صحيحة - السؤال التالي',
                'correct': True,
                'points': result['points'],
                'flex': next_q.contents if isinstance(next_q, FlexSendMessage) else None
            }
        else:
            final_results = game_instance.get_final_results()
            if group_id in active_games:
                del active_games[group_id]
            return {
                'message': 'انتهت اللعبة',
                'correct': True,
                'game_over': True,
                'points': result['points'],
                'flex': final_results.contents if isinstance(final_results, FlexSendMessage) else None
            }
    
    return None

def get_hint(game):
    """الحصول على تلميح"""
    if 'instance' not in game:
        return None
    
    game_instance = game['instance']
    hint = game_instance.get_hint()
    return hint if hint else None

def show_answer(game, group_id, active_games):
    """عرض الإجابة والانتقال للسؤال التالي"""
    if 'instance' not in game:
        return {'message': 'لا توجد لعبة نشطة'}
    
    game_instance = game['instance']
    answer = game_instance.show_answer()
    
    next_q = game_instance.next_question()
    if next_q:
        return {
            'message': 'الإجابة الصحيحة - السؤال التالي',
            'flex': next_q.contents if isinstance(next_q, FlexSendMessage) else None
        }
    else:
        final_results = game_instance.get_final_results()
        if group_id in active_games:
            del active_games[group_id]
        return {
            'message': 'انتهت اللعبة',
            'game_over': True,
            'flex': final_results.contents if isinstance(final_results, FlexSendMessage) else None
        }
