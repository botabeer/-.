# __init__.py

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

# يمكن تعريف قاموس لجميع الألعاب لتسهيل الوصول
GAME_CLASSES = {
    "ai": AI_Game,
    "build": BuildGame,
    "chain": ChainWordsGame,
    "compatibility": CompatibilityGame,
    "fast": FastGame,
    "lbgame": LBGame,
    "opposite": OppositeGame,
    "order": OrderGame,
    "song": SongGame,
}

# اختيار اللعبة بسهولة
def get_game(name):
    return GAME_CLASSES.get(name.lower())
