"""
مجلد الألعاب - Whale Bot Games Package
يحتوي على جميع الألعاب المتاحة في البوت
"""

from .game_opposite import OppositeGame
from .game_song import SongGame
from .game_chain import ChainWordsGame
from .game_order import OrderGame
from .game_build import BuildGame
from .game_lbgame import LBGame
from .game_fast import FastGame
from .game_compatibility import CompatibilityGame

__all__ = [
    'OppositeGame',
    'SongGame',
    'ChainWordsGame',
    'OrderGame',
    'BuildGame',
    'LBGame',
    'FastGame',
    'CompatibilityGame'
]

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
