from linebot.models import FlexSendMessage
from game_opposite import OppositeGame
from game_song import SongGame
from game_chain import ChainWordsGame
from game_order import OrderGame
from game_build import BuildGame
from game_lbgame import LBGame
from game_fast import FastGame
from game_compatibility import CompatibilityGame

# قاموس جميع الألعاب المتاحة
GAME_CLASSES = {
    'ضد': OppositeGame,
    'اغنية': SongGame,
    'سلسلة': ChainWordsGame,
    'ترتيب': OrderGame,
    'تكوين': BuildGame,
    'لعبة': LBGame,
    'اسرع': FastGame,
    'توافق': CompatibilityGame
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
    
    # التعامل الخاص مع لعبة LBGame (إنسان حيوان نبات بلد)
    if isinstance(game_instance, LBGame):
        result = game_instance.check_answer(text, user_id, user_name)
        
        if result and result.get('correct'):
            if result.get('complete'):
                # انتهت جميع الخطوات، الانتقال للسؤال التالي
                next_q = game_instance.next_question()
                if next_q:
                    return {
                        'message': 'إجابة صحيحة - السؤال التالي',
                        'correct': True,
                        'points': result['points'],
                        'flex': next_q.contents if isinstance(next_q, FlexSendMessage) else None
                    }
                else:
                    # انتهت اللعبة
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
            else:
                # الانتقال للخطوة التالية في نفس السؤال
                next_q = game_instance.next_question()
                return {
                    'message': 'صحيح - الخطوة التالية',
                    'correct': True,
                    'points': 0,
                    'flex': next_q.contents if isinstance(next_q, FlexSendMessage) else None
                }
        return None
    
    # التعامل مع بقية الألعاب
    result = game_instance.check_answer(text, user_id, user_name)
    
    if result and result.get('correct'):
        # إذا كانت اللعبة لها flex خاص (مثل التوافق)
        if result.get('flex'):
            return result
        
        # الألعاب العادية
        next_q = game_instance.next_question()
        if next_q:
            return {
                'message': 'إجابة صحيحة - السؤال التالي',
                'correct': True,
                'points': result.get('points', 2),
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
                'points': result.get('points', 2),
                'flex': final_results.contents if isinstance(final_results, FlexSendMessage) else None
            }
    
    return None

def get_hint(game):
    """الحصول على تلميح"""
    if 'instance' not in game:
        return None
    
    game_instance = game['instance']
    hint = game_instance.get_hint() if hasattr(game_instance, 'get_hint') else None
    
    if hint and isinstance(hint, FlexSendMessage):
        return hint
    elif hint:
        return hint
    return None

def show_answer(game, group_id, active_games):
    """عرض الإجابة والانتقال للسؤال التالي"""
    if 'instance' not in game:
        return {'message': 'لا توجد لعبة نشطة'}
    
    game_instance = game['instance']
    answer = game_instance.show_answer() if hasattr(game_instance, 'show_answer') else None
    
    # إذا لم تكن اللعبة تدعم عرض الإجابة
    if not answer:
        return {'message': 'هذه اللعبة لا تدعم عرض الإجابة'}
    
    next_q = game_instance.next_question() if hasattr(game_instance, 'next_question') else None
    if next_q:
        return {
            'message': 'الإجابة الصحيحة - السؤال التالي',
            'flex': next_q.contents if isinstance(next_q, FlexSendMessage) else None
        }
    else:
        final_results = game_instance.get_final_results() if hasattr(game_instance, 'get_final_results') else None
        if group_id in active_games:
            del active_games[group_id]
        return {
            'message': 'انتهت اللعبة',
            'game_over': True,
            'flex': final_results.contents if isinstance(final_results, FlexSendMessage) else None
        }
