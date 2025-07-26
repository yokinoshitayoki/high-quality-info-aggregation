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

def check_new_data():
    """检查是否有新的更新数据"""
    import json
    import os
    
    # 检查各网站的更新文件
    upd_files = [
        'scrapy/huxiu_data/huxiu_title_links_upd.json',
        'scrapy/qq_data/qq_title_links_upd.json', 
        'scrapy/sohu_data/sohu_title_links_upd.json'
    ]
    
    for upd_file in upd_files:
        if os.path.exists(upd_file):
            try:
                with open(upd_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data:  # 如果文件不为空且有数据
                        print(f"发现新数据: {upd_file} - {len(data)}条")
                        return True
            except:
                pass
    return False

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/titles', methods=['GET'])
def get_titles():
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    q = request.args.get('q', '').strip()
    order = request.args.get('order', 'desc').lower()
    if order not in ('asc', 'desc'):
        order = 'desc'
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
    def update_job(): # 更新数据
        try:
            # 并行运行三个爬虫
            import concurrent.futures
            import threading
            
            def run_crawler(script_name):
                try:
                    subprocess.run(['python', script_name], check=True, capture_output=True, text=True)
                    print(f"{script_name} 执行完成")
                    return True
                except subprocess.CalledProcessError as e:
                    print(f"{script_name} 执行失败: {e}")
                    return False
            
            # 定义三个爬虫脚本
            crawler_scripts = [
                'scrapy/upd_scrapy/huxiu_titles_links_scrapy_upd.py',
                'scrapy/upd_scrapy/tencent_titles_links_scrapy_upd.py',
                'scrapy/upd_scrapy/sohu_titles_links_scrapy_upd.py'
            ]
            
            print("开始并行运行三个爬虫...")
            
            # 使用ThreadPoolExecutor并行执行爬虫
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                # 提交所有爬虫任务
                future_to_script = {executor.submit(run_crawler, script): script for script in crawler_scripts}
                
                # 等待所有爬虫完成
                for future in concurrent.futures.as_completed(future_to_script):
                    script = future_to_script[future]
                    try:
                        success = future.result()
                        if success:
                            print(f"✓ {script} 成功完成")
                        else:
                            print(f"✗ {script} 执行失败")
                    except Exception as e:
                        print(f"✗ {script} 发生异常: {e}")
            
            print("所有爬虫执行完成")
            
            # 检查是否有新的更新数据
            has_new_data = check_new_data()
            if not has_new_data:
                print("数据已是最新状态")
                # 写入状态文件，通知前端数据已是最新状态
                with open('update_status.txt', 'w', encoding='utf-8') as f:
                    f.write('already_latest')
                return
            
            # 继续执行后续步骤（这些步骤需要按顺序执行）
            subprocess.run(['python', 'scrapy/upd_scrapy/merge_all_data_upd.py'], check=True)
            subprocess.run(['python', 'filter/upd_filter/ai_titles_bert_filter_upd.py'], check=True)
            subprocess.run(['python', 'filter/upd_filter/ai_titles_ds_filter_upd.py'], check=True)
            subprocess.run(['python', 'bind/upd_bind/bind_upd.py'], check=True)
            subprocess.run(['python', 'database/import_title_links_upd.py'], check=True)
            print("数据更新完成")
            subprocess.run(['python', 'clear_upd_files.py'], check=True)
            
            # 写入状态文件，通知前端更新成功
            with open('update_status.txt', 'w', encoding='utf-8') as f:
                f.write('success')
                
        except Exception as e:
            print("数据更新失败：", e)
            # 写入状态文件，通知前端更新失败
            with open('update_status.txt', 'w', encoding='utf-8') as f:
                f.write(f'failed:{str(e)}')
    
    threading.Thread(target=update_job).start()
    return jsonify({"msg": "已开始更新，稍后自动刷新"})

@app.route('/api/update_status', methods=['GET'])
def get_update_status():
    """获取更新状态"""
    try:
        if os.path.exists('update_status.txt'):
            with open('update_status.txt', 'r', encoding='utf-8') as f:
                status = f.read().strip()
            
            # 删除状态文件，避免重复读取
            os.remove('update_status.txt')
            
            if status == 'success':
                return jsonify({"status": "success", "msg": "数据更新成功！"})
            elif status == 'already_latest':
                return jsonify({"status": "already_latest", "msg": "数据已是最新状态，无需更新。"})
            elif status.startswith('failed:'):
                error_msg = status.split(':', 1)[1] if ':' in status else "未知错误"
                return jsonify({"status": "failed", "msg": f"更新失败：{error_msg}"})
            else:
                return jsonify({"status": "unknown", "msg": "未知状态"})
        else:
            return jsonify({"status": "running", "msg": "正在更新中..."})
    except Exception as e:
        return jsonify({"status": "error", "msg": f"获取状态失败：{str(e)}"})


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