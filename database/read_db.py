import sqlite3

db_path = 'database/title_link.db'

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# 查询所有表名
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cur.fetchall()
print("所有表：", tables)

# 查询 title_link 表的前10条数据
cur.execute("SELECT * FROM title_link LIMIT 10;")
rows = cur.fetchall()
for row in rows:
    print(row)

conn.close()