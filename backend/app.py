from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sqlite3
import subprocess
import threading
import os
import requests
import json
from feedback import feedback_manager
from config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL, MAX_CONTENT_LENGTH, MAX_TOKENS, TEMPERATURE
# v1新增按时间排序功能
# v2新增更新功能,并行爬虫，数据库逻辑更改，数据备份和还原，前端页面优化
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
    data = [{"id": row["id"], "title": row["title"], "link": row["link"], "date": row["date"], "source": row["source"]} for row in rows]
    return jsonify({
        "total_articles": total,
        "page": page,
        "size": size,
        "data": data
    })

@app.route('/api/article/<int:article_id>', methods=['GET'])
def get_article_detail(article_id):
    """获取单篇文章的详细信息"""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute('SELECT * FROM title_link WHERE id = ?', (article_id,))
        row = cur.fetchone()
        
        if row:
            article = {
                "id": row["id"],
                "title": row["title"],
                "link": row["link"],
                "date": row["date"],
                "source": row["source"],
                "content": row["content"] if row["content"] else ""
            }
            conn.close()
            return jsonify({"success": True, "article": article})
        else:
            conn.close()
            return jsonify({"success": False, "error": "文章不存在"}), 404
            
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """提交反馈"""
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        feedback_type = data.get('feedback_type', '').strip()
        
        if not title or not feedback_type:
            return jsonify({"success": False, "error": "标题和反馈类型不能为空"}), 400
        
        # 验证反馈类型
        valid_types = ['这个新闻与AI无关', '标题过于浮夸', '实际内容质量低', '无理由']
        if feedback_type not in valid_types:
            return jsonify({"success": False, "error": "无效的反馈类型"}), 400
        
        # 添加反馈
        count = feedback_manager.add_feedback(title, feedback_type)
        
        return jsonify({
            "success": True, 
            "message": "反馈提交成功",
            "count": count
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/feedback/stats', methods=['GET'])
def get_feedback_stats():
    """获取反馈统计"""
    try:
        stats = feedback_manager.get_feedback_stats()
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/feedback/prompts', methods=['GET'])
def get_feedback_prompts():
    """获取反馈prompt列表"""
    try:
        count = request.args.get('count', 5, type=int)
        prompts = feedback_manager.get_weighted_prompts(count)
        return jsonify({
            "success": True,
            "prompts": prompts
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/summary', methods=['POST'])
def generate_summary():
    """生成文章摘要"""
    try:
        data = request.get_json()
        article_id = data.get('article_id')
        title = data.get('title')
        
        if not article_id or not title:
            return jsonify({"success": False, "error": "缺少必要参数"}), 400
        
        # 获取文章内容
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT content FROM title_link WHERE id = ?', (article_id,))
        row = cur.fetchone()
        conn.close()
        
        if not row or not row['content']:
            return jsonify({"success": False, "error": "文章内容为空"}), 404
        
        content = row['content']
        
        # 调用DeepSeek API生成摘要
        summary = generate_deepseek_summary(title, content)
        
        return jsonify({
            "success": True,
            "summary": summary
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/summary/stream', methods=['POST'])
def generate_summary_stream():
    """流式生成文章摘要"""
    try:
        data = request.get_json()
        article_id = data.get('article_id')
        title = data.get('title')
        
        if not article_id or not title:
            return jsonify({"success": False, "error": "缺少必要参数"}), 400
        
        # 获取文章内容
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT content FROM title_link WHERE id = ?', (article_id,))
        row = cur.fetchone()
        conn.close()
        
        if not row or not row['content']:
            return jsonify({"success": False, "error": "文章内容为空"}), 404
        
        content = row['content']
        
        def generate():
            try:
                # 使用配置文件中的API密钥
                api_key = DEEPSEEK_API_KEY
                url = f"{DEEPSEEK_API_URL}/chat/completions"
                
                # 构建提示词
                prompt = f"""请为以下AI相关新闻生成一个50字左右的简洁摘要，要求：
1. 突出核心信息
2. 语言简洁明了
3. 适合快速预览
4. 直接输出摘要，不要输出任何其他内容。

标题：{title}
内容：{content[:MAX_CONTENT_LENGTH]}..."""
                
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": MAX_TOKENS,
                    "temperature": TEMPERATURE,
                    "stream": True
                }
                
                # 发送流式请求
                response = requests.post(url, headers=headers, json=data, stream=True)
                
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            line = line.decode('utf-8')
                            if line.startswith('data: '):
                                data_str = line[6:]
                                if data_str == '[DONE]':
                                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                                    break
                                try:
                                    data_json = json.loads(data_str)
                                    if 'choices' in data_json and len(data_json['choices']) > 0:
                                        delta = data_json['choices'][0].get('delta', {})
                                        if 'content' in delta:
                                            yield f"data: {json.dumps({'type': 'content', 'content': delta['content']})}\n\n"
                                except json.JSONDecodeError:
                                    continue
                else:
                    yield f"data: {json.dumps({'type': 'error', 'error': f'API调用失败: {response.status_code}'})}\n\n"
                    
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        
        return app.response_class(generate(), mimetype='text/plain')
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def generate_deepseek_summary(title, content):
    """调用DeepSeek API生成摘要"""
    try:
        # 使用配置文件中的API密钥
        api_key = DEEPSEEK_API_KEY
        url = f"{DEEPSEEK_API_URL}/chat/completions"
        
        # 构建提示词
        prompt = f"""请为以下AI相关新闻生成一个50字左右的简洁摘要，要求：
1. 突出核心信息
2. 语言简洁明了
3. 适合快速预览

标题：{title}
内容：{content[:MAX_CONTENT_LENGTH]}..."""  # 限制内容长度避免token过多
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": MAX_TOKENS,
            "temperature": TEMPERATURE,
            "stream": True  # 启用流式响应
        }
        
        # 发送流式请求
        response = requests.post(url, headers=headers, json=data, stream=True)
        
        if response.status_code == 200:
            summary = ""
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str == '[DONE]':
                            break
                        try:
                            data_json = json.loads(data_str)
                            if 'choices' in data_json and len(data_json['choices']) > 0:
                                delta = data_json['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    summary += delta['content']
                                    # 这里可以添加实时返回逻辑
                        except json.JSONDecodeError:
                            continue
            
            return summary.strip()
        else:
            return f"API调用失败: {response.status_code}"
            
    except Exception as e:
        return f"生成摘要失败: {str(e)}"

@app.route('/api/update', methods=['POST'])
def update_articles():
    # 启动爬虫和数据库更新的后台线程
    def update_job(): # 更新数据
        try:
            # 写入爬取状态
            with open('update_status.txt', 'w', encoding='utf-8') as f:
                f.write('crawling:爬取数据中...')
            
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
            
            # 写入AI分析状态
            with open('update_status.txt', 'w', encoding='utf-8') as f:
                f.write('analyzing:AI分析中...')
            
            # 继续执行后续步骤（这些步骤需要按顺序执行）
            subprocess.run(['python', 'scrapy/upd_scrapy/merge_all_data_upd.py'], check=True)
            subprocess.run(['python', 'filter/upd_filter/ai_titles_bert_filter_upd.py'], check=True)
            subprocess.run(['python', 'filter/upd_filter/ai_titles_ds_filter_upd.py'], check=True)
            subprocess.run(['python', 'bind/upd_bind/bind_upd.py'], check=True)
            
            # 写入数据库导入状态
            with open('update_status.txt', 'w', encoding='utf-8') as f:
                f.write('importing:导入数据库中...')
            
            subprocess.run(['python', 'database/import_title_links_upd.py'], check=True)
            print("数据更新完成")
            
            # 写入文章爬取状态
            with open('update_status.txt', 'w', encoding='utf-8') as f:
                f.write('crawling_articles:爬取文章内容中...')

            # 并行爬取文章内容
            try:
                subprocess.run(['python', 'get_article/__update__.py'], check=True)
                print("文章内容爬取完成")
            except subprocess.CalledProcessError as e:
                print(f"文章内容爬取失败: {e}")
                # 即使文章爬取失败，也不影响整体更新流程
            
            # 移除对clear_upd_files.py的调用，保留更新文件用于后续分析
            print("更新完成，保留更新文件")
            
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
            
            print(f"DEBUG: 读取到状态: '{status}'")  # 调试信息
            
            # 对于中间状态，不删除文件，让前端继续轮询
            if status.startswith('crawling:'):
                msg = status.split(':', 1)[1] if ':' in status else "爬取数据中..."
                return jsonify({"status": "crawling", "msg": msg})
            elif status.startswith('crawling_articles:'):
                msg = status.split(':', 1)[1] if ':' in status else "爬取文章内容中..."
                return jsonify({"status": "crawling_articles", "msg": msg})
            elif status.startswith('analyzing:'):
                msg = status.split(':', 1)[1] if ':' in status else "AI分析中..."
                return jsonify({"status": "analyzing", "msg": msg})
            elif status.startswith('importing:'):
                msg = status.split(':', 1)[1] if ':' in status else "导入数据库中..."
                return jsonify({"status": "importing", "msg": msg})
            elif status == 'success':
                # 成功状态才删除文件
                os.remove('update_status.txt')
                return jsonify({"status": "success", "msg": "数据更新成功！"})
            elif status == 'already_latest':
                # 已是最新状态才删除文件
                os.remove('update_status.txt')
                return jsonify({"status": "already_latest", "msg": "数据已是最新状态，无需更新。"})
            elif status.startswith('failed:'):
                # 失败状态才删除文件
                os.remove('update_status.txt')
                error_msg = status.split(':', 1)[1] if ':' in status else "未知错误"
                return jsonify({"status": "failed", "msg": f"更新失败：{error_msg}"})
            else:
                print(f"DEBUG: 未知状态: '{status}'")  # 调试信息
                return jsonify({"status": "unknown", "msg": f"未知状态: {status}"})
        else:
            return jsonify({"status": "running", "msg": "正在更新中..."})
    except Exception as e:
        print(f"DEBUG: 获取状态异常: {e}")  # 调试信息
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

@app.route('/article')
def article():
    return send_from_directory(app.static_folder, 'article.html')

# 提供前端静态资源
@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    app.run(debug=True)