"""
🐋 بوت الحوت - نظام الألعاب
"""

import random
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# استيراد الألعاب الفردية
try:
    from .game_opposite import OppositeGame
    from .game_song import SongGame
    from .game_chain import ChainWordsGame
    from .game_order import OrderGame
    from .game_build import BuildGame
    from .game_lbgame import LBGame
    from .game_fast import FastGame
    from .game_compatibility import CompatibilityGame
    from .game_ai import AiChat
    
    GAMES_AVAILABLE = True
except ImportError as e:
    logger.error(f"خطأ في استيراد الألعاب: {e}")
    GAMES_AVAILABLE = False

# قاموس الألعاب
GAME_CLASSES = {
    'ضد': OppositeGame if GAMES_AVAILABLE else None,
    'اغنية': SongGame if GAMES_AVAILABLE else None,
    'سلسلة': ChainWordsGame if GAMES_AVAILABLE else None,
    'ترتيب': OrderGame if GAMES_AVAILABLE else None,
    'تكوين': BuildGame if GAMES_AVAILABLE else None,
    'لعبة': LBGame if GAMES_AVAILABLE else None,
    'اسرع': FastGame if GAMES_AVAILABLE else None,
    'توافق': CompatibilityGame if GAMES_AVAILABLE else None,
    'ai': AiChat if GAMES_AVAILABLE else None
}

def start_game(group_id: str, game_type: str, user_id: str, user_name: str) -> Dict[str, Any]:
    """
    بدء لعبة جديدة
    
    Args:
        group_id: معرف المجموعة
        game_type: نوع اللعبة
        user_id: معرف المستخدم
        user_name: اسم المستخدم
        
    Returns:
        قاموس يحتوي على بيانات اللعبة والرسالة
    """
    try:
        game_class = GAME_CLASSES.get(game_type.lower())
        
        if not game_class:
            return {
                'success': False,
                'message': f"❌ اللعبة '{game_type}' غير متوفرة",
                'game_data': None
            }
        
        # إنشاء كائن اللعبة
        game = game_class()
        game_data = game.start()
        
        # إضافة معلومات إضافية
        game_data['type'] = game_type
        game_data['creator'] = user_id
        game_data['creator_name'] = user_name
        game_data['players'] = [user_id]
        game_data['player_scores'] = {user_id: {'name': user_name, 'score': 0}}
        
        return {
            'success': True,
            'message': game_data.get('message', 'بدأت اللعبة!'),
            'game_data': game_data,
            'flex': game_data.get('flex')
        }
        
    except Exception as e:
        logger.error(f"خطأ في بدء اللعبة {game_type}: {e}", exc_info=True)
        return {
            'success': False,
            'message': f"❌ حدث خطأ عند بدء اللعبة: {str(e)}",
            'game_data': None
        }

def check_game_answer(game: Dict[str, Any], answer: str, user_id: str, 
                      user_name: str, group_id: str, active_games: Dict) -> Dict[str, Any]:
    """
    التحقق من إجابة اللاعب
    
    Args:
        game: بيانات اللعبة الحالية
        answer: إجابة المستخدم
        user_id: معرف المستخدم
        user_name: اسم المستخدم
        group_id: معرف المجموعة
        active_games: قاموس الألعاب النشطة
        
    Returns:
        قاموس يحتوي على نتيجة التحقق
    """
    try:
        game_type = game.get('type', 'unknown')
        game_class = GAME_CLASSES.get(game_type.lower())
        
        if not game_class:
            return {'message': None}
        
        # إنشاء كائن اللعبة
        game_obj = game_class()
        result = game_obj.check_answer(game, answer, user_id, user_name)
        
        # تحديث بيانات اللعبة
        if result.get('correct'):
            # تحديث النقاط
            if 'player_scores' not in game:
                game['player_scores'] = {}
            if user_id not in game['player_scores']:
                game['player_scores'][user_id] = {'name': user_name, 'score': 0}
            
            points = result.get('points', 2)
            game['player_scores'][user_id]['score'] += points
            
            # الانتقال للسؤال التالي
            if result.get('next_question'):
                game['current_question'] = result['next_question']
                game['current_round'] += 1
        
        # التحقق من انتهاء اللعبة
        if game.get('current_round', 0) >= game.get('total_rounds', 5):
            result['game_over'] = True
            result['final_scores'] = game.get('player_scores', {})
            
            # حذف اللعبة من القائمة النشطة
            if group_id in active_games:
                del active_games[group_id]
        
        return result
        
    except Exception as e:
        logger.error(f"خطأ في التحقق من الإجابة: {e}", exc_info=True)
        return {'message': None}

def get_hint(game: Dict[str, Any]) -> Optional[str]:
    """
    الحصول على تلميح للسؤال الحالي
    
    Args:
        game: بيانات اللعبة الحالية
        
    Returns:
        نص التلميح أو None
    """
    try:
        game_type = game.get('type', 'unknown')
        game_class = GAME_CLASSES.get(game_type.lower())
        
        if not game_class:
            return None
        
        game_obj = game_class()
        return game_obj.get_hint(game)
        
    except Exception as e:
        logger.error(f"خطأ في الحصول على تلميح: {e}")
        return None

def show_answer(game: Dict[str, Any], group_id: str, active_games: Dict) -> Dict[str, Any]:
    """
    عرض الإجابة الصحيحة والانتقال للسؤال التالي
    
    Args:
        game: بيانات اللعبة الحالية
        group_id: معرف المجموعة
        active_games: قاموس الألعاب النشطة
        
    Returns:
        قاموس يحتوي على الإجابة والسؤال التالي
    """
    try:
        game_type = game.get('type', 'unknown')
        game_class = GAME_CLASSES.get(game_type.lower())
        
        if not game_class:
            return {'message': "❌ اللعبة غير متوفرة"}
        
        game_obj = game_class()
        result = game_obj.show_answer(game)
        
        # الانتقال للسؤال التالي
        game['current_round'] += 1
        
        if game['current_round'] < game.get('total_rounds', 5):
            # توليد سؤال جديد
            next_q = game_obj.generate_question()
            if next_q:
                game['current_question'] = next_q
                result['flex'] = next_q.get('flex')
                result['message'] = "الإجابة الصحيحة: " + result.get('answer', 'غير متوفر')
        else:
            # انتهت اللعبة
            result['game_over'] = True
            result['final_scores'] = game.get('player_scores', {})
            
            # حذف اللعبة
            if group_id in active_games:
                del active_games[group_id]
        
        return result
        
    except Exception as e:
        logger.error(f"خطأ في عرض الإجابة: {e}", exc_info=True)
        return {'message': "❌ حدث خطأ"}

__all__ = [
    'GAME_CLASSES',
    'start_game',
    'check_game_answer',
    'get_hint',
    'show_answer',
    'GAMES_AVAILABLE'
]
