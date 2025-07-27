import json
import sqlite3
from datetime import datetime

def parse_date(date_str):
    """解析日期字符串，返回datetime对象用于排序"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except:
        return datetime.min

def import_title_links():
    # 读取 title_link.json
    try:
        with open('bind/init_bind/title_link.json', 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:  # 如果文件为空
                print("文件为空，没有数据可导入")
                return
            data = json.loads(content)
        print(f"读取到 {len(data)} 条数据")
    except FileNotFoundError:
        print("未找到文件 bind/init_bind/title_link.json")
        return
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return

    # 按时间从旧到新排序
    sorted_data = sorted(data.items(), key=lambda x: parse_date(x[1][1]), reverse=False)
    print("数据已按时间从旧到新排序")

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
            source TEXT,
            content TEXT
        )
    ''')

    # 插入数据
    inserted_count = 0
    
    for title, info in sorted_data:
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
    
    print(f"导入完成！")
    print(f"成功导入: {inserted_count} 条记录")
    
    # 验证结果
    conn = sqlite3.connect('database/title_link.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM title_link')
    total_count = c.fetchone()[0]
    conn.close()
    print(f"数据库总记录数: {total_count} 条")

if __name__ == "__main__":
    import_title_links()