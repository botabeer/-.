# games/__init__.py
"""
نظام إدارة الألعاب - بوت الحوت
"""

# استيراد جميع الألعاب
from .game_ai import AI_Game
from .game_build import BuildGame
from .game_chain import ChainWordsGame
from .game_compatibility import CompatibilityGame
from .game_fast import FastGame
from .game_lbgame import LBGame
from .game_opposite import OppositeGame
from .game_order import OrderGame
from .game_song import SongGame

# قاموس جميع الألعاب المتاحة
GAME_CLASSES = {
    "ai": AI_Game,
    "اي": AI_Game,
    "build": BuildGame,
    "تكوين": BuildGame,
    "chain": ChainWordsGame,
    "سلسلة": ChainWordsGame,
    "compatibility": CompatibilityGame,
    "توافق": CompatibilityGame,
    "fast": FastGame,
    "اسرع": FastGame,
    "lbgame": LBGame,
    "لعبة": LBGame,
    "opposite": OppositeGame,
    "ضد": OppositeGame,
    "order": OrderGame,
    "ترتيب": OrderGame,
    "song": SongGame,
    "اغنية": SongGame,
}

def get_game(name):
    """الحصول على كلاس اللعبة بالاسم"""
    return GAME_CLASSES.get(name.lower())

def start_game(group_id, game_type, user_id, user_name):
    """
    بدء لعبة جديدة
    
    Args:
        group_id: معرف المجموعة
        game_type: نوع اللعبة (عربي أو انجليزي)
        user_id: معرف المستخدم
        user_name: اسم المستخدم
    
    Returns:
        dict: {
            'game_data': بيانات اللعبة,
            'message': رسالة نصية,
            'flex': Flex Message (اختياري)
        }
    """
    game_class = get_game(game_type)
    
    if not game_class:
        return {
            'game_data': {'type': game_type, 'error': True},
            'message': f"❌ اللعبة '{game_type}' غير موجودة\nاكتب 'ابدأ' لاختيار لعبة عشوائية"
        }
    
    try:
        game = game_class()
        result = game.start(group_id, user_id, user_name)
        
        # إضافة نوع اللعبة لبيانات اللعبة
        if 'game_data' in result:
            result['game_data']['type'] = game_type
            result['game_data']['class'] = game.__class__.__name__
        
        return result
    except Exception as e:
        import logging
        logging.error(f"خطأ في بدء اللعبة {game_type}: {e}")
        return {
            'game_data': {'type': game_type, 'error': True},
            'message': f"❌ حدث خطأ في بدء اللعبة\nالرجاء المحاولة مرة أخرى"
        }

def check_game_answer(game_data, answer, user_id, user_name, group_id, active_games):
    """
    التحقق من إجابة اللاعب
    
    Args:
        game_data: بيانات اللعبة الحالية
        answer: إجابة اللاعب
        user_id: معرف المستخدم
        user_name: اسم المستخدم
        group_id: معرف المجموعة
        active_games: قاموس الألعاب النشطة
    
    Returns:
        dict: {
            'correct': هل الإجابة صحيحة؟,
            'game_over': هل انتهت اللعبة؟,
            'message': رسالة الرد (اختياري),
            'flex': Flex Message (اختياري)
        }
    """
    if not game_data or game_data.get('error'):
        return {'correct': False, 'game_over': False}
    
    game_type = game_data.get('type', 'fast')
    game_class = get_game(game_type)
    
    if not game_class:
        return {'correct': False, 'game_over': False}
    
    try:
        game = game_class()
        result = game.check_answer(game_data, answer, user_id, user_name, group_id, active_games)
        return result if result else {'correct': False, 'game_over': False}
    except Exception as e:
        import logging
        logging.error(f"خطأ في فحص الإجابة {game_type}: {e}")
        return {'correct': False, 'game_over': False}

def get_hint(game_data):
    """
    الحصول على تلميح للعبة
    
    Args:
        game_data: بيانات اللعبة الحالية
    
    Returns:
        str: نص التلميح أو None
    """
    if not game_data or game_data.get('error'):
        return None
    
    game_type = game_data.get('type', 'fast')
    game_class = get_game(game_type)
    
    if not game_class:
        return None
    
    try:
        game = game_class()
        if hasattr(game, 'get_hint'):
            return game.get_hint(game_data)
        else:
            return "💡 التلميح غير متوفر لهذه اللعبة"
    except Exception as e:
        import logging
        logging.error(f"خطأ في الحصول على التلميح {game_type}: {e}")
        return None

def show_answer(game_data, group_id, active_games):
    """
    عرض الإجابة الصحيحة والانتقال للسؤال التالي
    
    Args:
        game_data: بيانات اللعبة الحالية
        group_id: معرف المجموعة
        active_games: قاموس الألعاب النشطة
    
    Returns:
        dict: {
            'message': رسالة الإجابة,
            'flex': Flex Message (اختياري)
        }
    """
    if not game_data or game_data.get('error'):
        return {'message': '❌ لا توجد لعبة نشطة'}
    
    game_type = game_data.get('type', 'fast')
    game_class = get_game(game_type)
    
    if not game_class:
        return {'message': '❌ اللعبة غير موجودة'}
    
    try:
        game = game_class()
        if hasattr(game, 'show_answer'):
            return game.show_answer(game_data, group_id, active_games)
        else:
            # سلوك افتراضي: عرض الإجابة فقط
            answer = game_data.get('answer', 'غير متوفر')
            return {
                'message': f"✅ الإجابة الصحيحة:\n{answer}\n\n💡 اكتب 'ابدأ' للعبة جديدة"
            }
    except Exception as e:
        import logging
        logging.error(f"خطأ في عرض الإجابة {game_type}: {e}")
        return {'message': '❌ حدث خطأ في عرض الإجابة'}

# تصدير الدوال والكلاسات المهمة
__all__ = [
    'start_game',
    'check_game_answer',
    'get_hint',
    'show_answer',
    'get_game',
    'GAME_CLASSES',
    'AI_Game',
    'BuildGame',
    'ChainWordsGame',
    'CompatibilityGame',
    'FastGame',
    'LBGame',
    'OppositeGame',
    'OrderGame',
    'SongGame',
]
