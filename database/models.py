from dataclasses import dataclass

@dataclass
class Player:
    user_id: str
    name: str
    points: int
    last_active: str = None

@dataclass
class GameLog:
    id: int
    user_id: str
    game_name: str
    result: str
    timestamp: str
