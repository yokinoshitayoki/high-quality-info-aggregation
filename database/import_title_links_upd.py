import json
import sqlite3
from datetime import datetime

def parse_date(date_str):
    """解析日期字符串，返回datetime对象用于排序"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except:
        return datetime.min

def import_title_links_upd():
    # 读取更新后的 title_link_upd.json
    try:
        with open('bind/upd_bind/title_link_upd.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"读取到 {len(data)} 条更新数据")
    except FileNotFoundError:
        print("未找到更新文件 bind/upd_bind/title_link_upd.json")
        return
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return

    # 按时间从旧到新排序（旧到新）
    sorted_data = sorted(data.items(), key=lambda x: parse_date(x[1][1]), reverse=False)
    print("数据已按时间从旧到新排序")

    # 连接数据库
    conn = sqlite3.connect('database/title_link.db')
    c = conn.cursor()
    
    # 检查表是否存在，如果不存在则创建
    c.execute('''
        CREATE TABLE IF NOT EXISTS title_link (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            link TEXT,
            date TEXT,
            source TEXT,
            content TEXT
        )
    ''')
    
    # 检查content列是否存在，如果不存在则添加
    try:
        c.execute('SELECT content FROM title_link LIMIT 1')
    except sqlite3.OperationalError:
        print("添加content列...")
        c.execute('ALTER TABLE title_link ADD COLUMN content TEXT')
        conn.commit()

    # 获取现有标题，避免重复插入
    c.execute('SELECT title FROM title_link')
    existing_titles = {row[0] for row in c.fetchall()}
    print(f"数据库中已有 {len(existing_titles)} 条记录")

    # 插入新数据
    inserted_count = 0
    skipped_count = 0
    
    for title, info in sorted_data:
        # 检查是否已存在
        if title in existing_titles:
            print(f"跳过重复标题: {title}")
            skipped_count += 1
            continue
            
        # info = [link, date, source]
        link = info[0] if len(info) > 0 else ''
        date = info[1] if len(info) > 1 else ''
        source = info[2] if len(info) > 2 else ''
        
        try:
            c.execute('INSERT INTO title_link (title, link, date, source, content) VALUES (?, ?, ?, ?, ?)', 
                     (title, link, date, source, ''))
            inserted_count += 1
            print(f"插入: {title} ({date})")
        except Exception as e:
            print(f"插入失败 {title}: {e}")

    # 提交更改
    conn.commit()
    conn.close()
    
    print(f"更新完成！")
    print(f"新增记录: {inserted_count} 条")
    print(f"跳过重复: {skipped_count} 条")
    
    # 验证结果
    conn = sqlite3.connect('database/title_link.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM title_link')
    total_count = c.fetchone()[0]
    conn.close()
    print(f"数据库总记录数: {total_count} 条")

if __name__ == "__main__":
    import_title_links_upd() 