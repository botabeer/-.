"""
مجلد الألعاب - Whale Bot Games Package
جميع الألعاب المتاحة في البوت
"""

from .speed import SpeedGame
from .word_game import WordGame
from .chain_words import ChainWordsGame
from .song import SongGame
from .opposite import OppositeGame
from .order import OrderGame
from .build import BuildGame
from .compatibility import CompatibilityGame

__all__ = [
    'SpeedGame',
    'WordGame',
    'ChainWordsGame',
    'SongGame',
    'OppositeGame',
    'OrderGame',
    'BuildGame',
    'CompatibilityGame'
    'AiGame'
]

# قاموس الألعاب المتاحة
GAME_CLASSES = {
    'اسرع': SpeedGame,
    'لعبة': WordGame,
    'سلسلة': ChainWordsGame,
    'اغنية': SongGame,
    'ضد': OppositeGame,
    'ترتيب': OrderGame,
    'تكوين': BuildGame,
    'توافق': CompatibilityGame
}

def get_game_instance(game_type):
    """إرجاع instance من اللعبة المط
