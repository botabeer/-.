import sqlite3

DB_NAME = 'database.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # جدول اللاعبين
    c.execute('''
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT UNIQUE,
        name TEXT,
        points INTEGER DEFAULT 0,
        games_played INTEGER DEFAULT 0,
        games_won INTEGER DEFAULT 0,
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # جدول الألعاب (يمكنك تعديل لاحقاً حسب مشروعك)
    c.execute('''
    CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_name TEXT UNIQUE,
        description TEXT
    )
    ''')

    # سجل النقاط لكل لاعب في كل لعبة
    c.execute('''
    CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER,
        game_id INTEGER,
        points INTEGER DEFAULT 0,
        FOREIGN KEY(player_id) REFERENCES players(id),
        FOREIGN KEY(game_id) REFERENCES games(id)
    )
    ''')

    conn.commit()
    conn.close()
    print("[✔] تم إنشاء قاعدة البيانات والجداول بنجاح")

if __name__ == '__main__':
    init_db()
