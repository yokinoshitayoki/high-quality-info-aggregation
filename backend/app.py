from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sqlite3
import subprocess
import threading
import os
# v1新增按时间排序功能

app = Flask(__name__, static_folder='../frontend', static_url_path='/')
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'database', 'title_link.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/titles', methods=['GET'])
def get_titles():
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    q = request.args.get('q', '').strip()
    order = request.args.get('order', 'asc').lower()
    if order not in ('asc', 'desc'):
        order = 'asc'
    offset = (page - 1) * size

    conn = get_db()
    cur = conn.cursor()
    if q:
        cur.execute('SELECT COUNT(*) FROM title_link WHERE title LIKE ?', (f'%{q}%',))
        total = cur.fetchone()[0]
        cur.execute(f'SELECT * FROM title_link WHERE title LIKE ? ORDER BY id {order.upper()} LIMIT ? OFFSET ?', (f'%{q}%', size, offset))
    else:
        cur.execute('SELECT COUNT(*) FROM title_link')
        total = cur.fetchone()[0]
        cur.execute(f'SELECT * FROM title_link ORDER BY id {order.upper()} LIMIT ? OFFSET ?', (size, offset))
    rows = cur.fetchall()
    conn.close()
    data = [{"title": row["title"], "link": row["link"], "date": row["date"], "source": row["source"]} for row in rows]
    return jsonify({
        "total_articles": total,
        "page": page,
        "size": size,
        "data": data
    })

@app.route('/api/update', methods=['POST'])
def update_articles():
    # 启动爬虫和数据库更新的后台线程
    def update_job():
        try:
            subprocess.run(['python', 'scrapy/huxiu_titles_links_scrapy.py'], check=True)
            subprocess.run(['python', 'scrapy/tencent_titles_links_scrapy.py'], check=True)
            subprocess.run(['python', 'scrapy/sohu_titles_links_scrapy.py'], check=True)
            subprocess.run(['python', 'scrapy/merge_all_data.py'], check=True)
            subprocess.run(['python', 'filter/ai_titles_bert_filter.py'], check=True)
            subprocess.run(['python', 'filter/ai_titles_ds_filter.py'], check=True)
            subprocess.run(['python', 'bind/bind.py'], check=True)
            subprocess.run(['python', 'backend/import_title_links.py'], check=True)
            print("数据更新完成")
        except Exception as e:
            print("数据更新失败：", e)
    threading.Thread(target=update_job).start()
    return jsonify({"msg": "已开始更新，稍后自动刷新"})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM title_link')
    total = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM title_link')  # 你可以加条件如 status='summarized'
    summarized = cur.fetchone()[0]
    cur.execute('SELECT substr(link, 1, 20) as source, COUNT(*) FROM title_link GROUP BY source')
    sources = {row[0]: row[1] for row in cur.fetchall()}
    conn.close()
    return jsonify({
        "total_articles_in_db": total,
        "summarized_articles": summarized,
        "sources_distribution": sources
    })

# 提供前端页面
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

# 提供前端静态资源
@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    app.run(debug=True)