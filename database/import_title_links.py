import json
import sqlite3

# 读取 title_link.json
with open('bind/title_link.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 创建数据库
conn = sqlite3.connect('database/title_link.db')
c = conn.cursor()
c.execute('DROP TABLE IF EXISTS title_link')
c.execute('''
    CREATE TABLE title_link (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        link TEXT,
        date TEXT,
        source TEXT
    )
''')

for title, info in data.items():
    # info = [link, date, source]
    link = info[0] if len(info) > 0 else ''
    date = info[1] if len(info) > 1 else ''
    source = info[2] if len(info) > 2 else ''
    c.execute('INSERT INTO title_link (title, link, date, source) VALUES (?, ?, ?, ?)', (title, link, date, source))

conn.commit()
conn.close()
print('已导入到 database/title_link.db')