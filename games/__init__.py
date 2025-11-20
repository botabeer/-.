# ============================================
# games/__init__.py - نقطة دخول مجلد الألعاب
# ============================================

"""
مجلد الألعاب
============
هذا الملف يستورد جميع الألعاب ويوفر واجهة موحدة للوصول إليها
"""

from .game_ai import AiChat
from .game_build import LettersWordsGame
from .game_chain import ChainWordsGame
from .game_compatibility import CompatibilityGame
from .game_fast import FastTypingGame
from .game_lbgame import HumanAnimalPlantGame
from .game_opposite import OppositeGame
from .game_order import OrderGame
from .game_song import SongGame

# قاموس الألعاب المتاحة
GAME_CLASSES = {
    'FastTypingGame': FastTypingGame,
    'HumanAnimalPlantGame': HumanAnimalPlantGame,
    'ChainWordsGame': ChainWordsGame,
    'SongGame': SongGame,
    'OppositeGame': OppositeGame,
    'OrderGame': OrderGame,
    'LettersWordsGame': LettersWordsGame,
    'CompatibilityGame': CompatibilityGame,
    'AiChat': AiChat
}

# تخزين الألعاب النشطة
active_games = {}


def start_game(game_type: str, group_id: str, **kwargs):
    """
    بدء لعبة جديدة
    
    Args:
        game_type: نوع اللعبة (اسم الكلاس)
        group_id: معرف المجموعة/المستخدم
        **kwargs: معاملات إضافية
        
    Returns:
        كائن اللعبة أو None
    """
    # التحقق من وجود لعبة نشطة
    if group_id in active_games:
        return None
    
    # الحصول على كلاس اللعبة
    game_class = GAME_CLASSES.get(game_type)
    if not game_class:
        return None
    
    # إنشاء اللعبة
    try:
        game = game_class(**kwargs)
        active_games[group_id] = game
        return game
    except Exception as e:
        print(f"Error starting game {game_type}: {e}")
        return None


def get_active_game(group_id: str):
    """
    الحصول على اللعبة النشطة
    
    Args:
        group_id: معرف المجموعة/المستخدم
        
    Returns:
        كائن اللعبة أو None
    """
    return active_games.get(group_id)


def stop_game(group_id: str) -> bool:
    """
    إيقاف اللعبة النشطة
    
    Args:
        group_id: معرف المجموعة/المستخدم
        
    Returns:
        True إذا تم الإيقاف بنجاح
    """
    if group_id in active_games:
        del active_games[group_id]
        return True
    return False


def check_game_answer(group_id: str, user_id: str, answer: str):
    """
    التحقق من إجابة المستخدم
    
    Args:
        group_id: معرف المجموعة/المستخدم
        user_id: معرف المستخدم
        answer: الإجابة
        
    Returns:
        نتيجة التحقق (dict) أو None
    """
    game = active_games.get(group_id)
    if not game:
        return None
    
    try:
        result = game.check_answer(user_id, answer)
        
        # إذا انتهت اللعبة، احذفها من القائمة
        if result and result.get('game_ended', False):
            del active_games[group_id]
        
        return result
    except Exception as e:
        print(f"Error checking answer: {e}")
        return None


def get_hint(group_id: str):
    """
    الحصول على تلميح
    
    Args:
        group_id: معرف المجموعة/المستخدم
        
    Returns:
        التلميح أو None
    """
    game = active_games.get(group_id)
    if not game or not hasattr(game, 'get_hint'):
        return None
    
    try:
        return game.get_hint()
    except Exception as e:
        print(f"Error getting hint: {e}")
        return None


def show_answer(group_id: str):
    """
    إظهار الإجابة الصحيحة
    
    Args:
        group_id: معرف المجموعة/المستخدم
        
    Returns:
        الإجابة أو None
    """
    game = active_games.get(group_id)
    if not game or not hasattr(game, 'show_answer'):
        return None
    
    try:
        answer = game.show_answer()
        
        # الانتقال للسؤال التالي إذا كانت اللعبة تدعم ذلك
        if hasattr(game, 'next_question'):
            game.next_question()
        
        return answer
    except Exception as e:
        print(f"Error showing answer: {e}")
        return None


def get_game_state(group_id: str):
    """
    الحصول على حالة اللعبة
    
    Args:
        group_id: معرف المجموعة/المستخدم
        
    Returns:
        حالة اللعبة (dict) أو None
    """
    game = active_games.get(group_id)
    if not game or not hasattr(game, 'get_state'):
        return None
    
    try:
        return game.get_state()
    except Exception as e:
        print(f"Error getting game state: {e}")
        return None


# تصدير كل شيء
__all__ = [
    'GAME_CLASSES',
    'active_games',
    'start_game',
    'get_active_game',
    'stop_game',
    'check_game_answer',
    'get_hint',
    'show_answer',
    'get_game_state',
    # الألعاب
    'AiChat',
    'LettersWordsGame',
    'ChainWordsGame',
    'CompatibilityGame',
    'FastTypingGame',
    'HumanAnimalPlantGame',
    'OppositeGame',
    'OrderGame',
    'SongGame'
]
