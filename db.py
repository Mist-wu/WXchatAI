import sqlite3

path = 'history'

# 创建数据库
def create_db():
    conn = sqlite3.connect(f'{path}.db')
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS history (
        user_id TEXT,
        role TEXT,
        content TEXT
    )
    ''')
    conn.commit()
    conn.close()

# 添加历史记录
def add_history(user_id, role, content):
    conn = sqlite3.connect(f'{path}.db')
    c = conn.cursor()
    c.execute(
        'INSERT INTO history (user_id, role, content) VALUES (?, ?, ?)',
        (user_id, role, content)
    )
    conn.commit()
    conn.close()

# 获取历史记录
def get_history(user_id):
    try:
        conn = sqlite3.connect(f'{path}.db')
        c = conn.cursor()
        c.execute(
            'SELECT role, content FROM history WHERE user_id=? ORDER BY rowid',
            (user_id,)
        )
        history = c.fetchall()
        conn.close()
        return [{'role': row[0], 'content': row[1]} for row in history]
    except Exception as e:
        print(f"DB error: {e}")
        return []