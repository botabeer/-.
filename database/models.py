from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Player:
    user_id: str
    name: str
    points: int = 0
    last_active: Optional[str] = None  # يمكن أن يكون None إذا لم يتم تسجيل آخر نشاط

@dataclass
class GameLog:
    id: Optional[int] = None  # سيحدد تلقائيًا عند الإدراج في DB
    user_id: str = ""
    game_name: str = ""
    result: str = ""
    timestamp: Optional[str] = None  # يمكن أن يكون None، ستُضاف القيمة تلقائيًا في DB
