from games.game_fast import FastGame
from games.game_lbgame import LBGame
from games.game_chain import ChainGame
from games.game_song import SongGame
from games.game_opposite import OppositeGame
from games.game_order import OrderGame
from games.game_build import BuildGame
from games.game_compatibility import CompatibilityGame
from games.game_ai import AIGame

GAME_CLASSES = {
    'fast': FastGame,
    'lbgame': LBGame,
    'chain': ChainGame,
    'song': SongGame,
    'opposite': OppositeGame,
    'order': OrderGame,
    'build': BuildGame,
    'compatibility': CompatibilityGame,
    'ai': AIGame
}

def get_game_class(game_key):
    return GAME_CLASSES.get(game_key)

def get_all_games():
    return GAME_CLASSES
