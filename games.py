"""
واجهة إدارة الألعاب - Games Manager Interface
ملف موحّد بعد دمج ملفين بدون حذف أو فقدان خصائص.
"""

from linebot.models import FlexSendMessage

# استيراد ملفات الألعاب
from game_opposite import OppositeGame
from game_song import SongGame
from game_chain import ChainWordsGame
from game_order import OrderGame
from game_build import BuildGame
from game_lbgame import LBGame
from game_fast import FastGame
from game_compatibility import CompatibilityGame

# قاموس جميع الألعاب المتاحة (مأخوذ من الملف الثاني + دمج مع الأول)
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


# ---------------------------------------------------------
#               🔵  START GAME (دمج)
# ---------------------------------------------------------
def start_game(group_id, game_type, user_id, user_name):
    """
    بدء لعبة جديدة (دمج بين الوظيفتين بدون فقد أي منطق)
    """
    game_class = GAME_CLASSES.get(game_type)

    if not game_class:
        return {
            'message': f'❌ نوع اللعبة "{game_type}" غير موجود',
            'game_data': None
        }

    try:
        game_instance = game_class()
        result = game_instance.start_game()

        game_data = {
            'type': game_type,
            'instance': game_instance,
            'players': [user_id]
        }

        return {
            'message': f'🎮 بدأت لعبة {game_type}',
            'game_data': game_data,
            'flex': result.contents if isinstance(result, FlexSendMessage) else None
        }

    except Exception as e:
        return {
            'message': f'❌ خطأ في بدء اللعبة: {str(e)}',
            'game_data': None
        }


# ---------------------------------------------------------
#               🔵  CHECK ANSWER (دمج كامل)
# ---------------------------------------------------------
def check_game_answer(game, text, user_id, user_name, group_id, active_games):
    """
    فحص إجابة اللاعب – دمج كامل للمنطقين
    """
    if 'instance' not in game:
        return None

    game_instance = game['instance']

    # معالجة لعبة إنسان/حيوان/نبات/بلد
    if isinstance(game_instance, LBGame):
        return _handle_lbgame_answer(game_instance, text, user_id, user_name, group_id, active_games)

    # الألعاب العادية
    return _handle_standard_game_answer(game_instance, text, user_id, user_name, group_id, active_games)


# ---------------------------------------------------------
#         🔵  معالجة خاصة للعبة LBGame (مُدمجة)
# ---------------------------------------------------------
def _handle_lbgame_answer(game_instance, text, user_id, user_name, group_id, active_games):
    result = game_instance.check_answer(text, user_id, user_name)

    if result and result.get('correct'):
        if result.get('complete'):
            next_q = game_instance.next_question()

            if next_q:
                return {
                    'message': '✅ إجابة صحيحة - السؤال التالي',
                    'correct': True,
                    'points': result['points'],
                    'flex': next_q.contents if isinstance(next_q, FlexSendMessage) else None
                }

            # انتهت اللعبة
            final_results = game_instance.get_final_results()
            if group_id in active_games:
                del active_games[group_id]

            return {
                'message': ' انتهت اللعبة',
                'correct': True,
                'game_over': True,
                'points': result['points'],
                'flex': final_results.contents if isinstance(final_results, FlexSendMessage) else None
            }

        # خطوة جزئية
        next_q = game_instance.next_question()
        return {
            'message': '✅ صحيح - الخطوة التالية',
            'correct': True,
            'points': 0,
            'flex': next_q.contents if isinstance(next_q, FlexSendMessage) else None
        }

    return None


# ---------------------------------------------------------
#    🔵  الألعاب العادية – دمج كامل لمنطق الملفين
# ---------------------------------------------------------
def _handle_standard_game_answer(game_instance, text, user_id, user_name, group_id, active_games):
    result = game_instance.check_answer(text, user_id, user_name)

    if result and result.get('correct'):

        # بعض الألعاب ترجع flex جاهز (مثل لعبة التوافق)
        if result.get('flex'):
            return result

        next_q = game_instance.next_question()

        if next_q:
            return {
                'message': '✅ إجابة صحيحة - السؤال التالي',
                'correct': True,
                'points': result.get('points', 2),
                'flex': next_q.contents if isinstance(next_q, FlexSendMessage) else None
            }

        # لا يوجد سؤال جديد – نهاية اللعبة
        final_results = game_instance.get_final_results()
        if group_id in active_games:
            del active_games[group_id]

        return {
            'message': '🎊 انتهت اللعبة',
            'correct': True,
            'game_over': True,
            'points': result.get('points', 2),
            'flex': final_results.contents if isinstance(final_results, FlexSendMessage) else None
        }

    return None


# ---------------------------------------------------------
#                       🔵 GET HINT
# ---------------------------------------------------------
def get_hint(game):
    if 'instance' not in game:
        return None

    game_instance = game['instance']

    if not hasattr(game_instance, 'get_hint'):
        return None

    hint = game_instance.get_hint()

    if hint and isinstance(hint, FlexSendMessage):
        return hint

    return hint


# ---------------------------------------------------------
#                   🔵 SHOW ANSWER (مدموج)
# ---------------------------------------------------------
def show_answer(game, group_id, active_games):
    if 'instance' not in game:
        return {'message': '❌ لا توجد لعبة نشطة'}

    game_instance = game['instance']

    if not hasattr(game_instance, 'show_answer'):
        return {'message': '❌ هذه اللعبة لا تدعم عرض الإجابة'}

    answer = game_instance.show_answer()

    if not answer:
        return {'message': '❌ لا توجد إجابة متاحة'}

    next_q = game_instance.next_question() if hasattr(game_instance, 'next_question') else None

    if next_q:
        return {
            'message': '✅ الإجابة الصحيحة - السؤال التالي',
            'flex': next_q.contents if isinstance(next_q, FlexSendMessage) else None
        }

    # نهاية اللعبة
    final_results = game_instance.get_final_results() if hasattr(game_instance, 'get_final_results') else None

    if group_id in active_games:
        del active_games[group_id]

    return {
        'message': ' انتهت اللعبة',
        'game_over': True,
        'flex': final_results.contents if isinstance(final_results, FlexSendMessage) else None
    }
