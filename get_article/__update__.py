import os
import sys
import json
import time
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加get_article目录到Python路径
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'get_article'))

def load_title_link_data():
    """加载更新后的title_link_upd.json文件"""
    try:
        # 读取bind/upd_bind/title_link_upd.json文件
        json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                'bind', 'upd_bind', 'title_link_upd.json')
        
        if not os.path.exists(json_path):
            print(f"未找到更新文件: {json_path}")
            return None
        
        # 检查文件是否为空
        with open(json_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                print("更新文件为空，没有数据可处理")
                return None
            data = json.loads(content)
        
        print(f"成功加载 {len(data)} 条更新数据")
        return data
    
    except Exception as e:
        print(f"加载更新数据失败: {e}")
        return None

def get_article_content(title, link_info):
    """根据网站类型调用相应的爬虫获取文章内容"""
    try:
        link, date, source = link_info
        
        if source == '虎嗅网':
            from huxiu_crawler_artcle import get_article_content as huxiu_crawler
            result = huxiu_crawler(link)
        elif source == '搜狐网':
            from sohu_crawler_artcle import get_article_content as sohu_crawler
            result = sohu_crawler(link)
        elif source == '腾讯网':
            from tencent_crawler_artcle import get_article_content as tencent_crawler
            result = tencent_crawler(link)
        else:
            print(f"未知的网站来源: {source}")
            return None
        
        if result['success']:
            print(f"成功获取文章: {title}")
            return result['content']
        else:
            print(f"获取文章失败: {title} - {result['error']}")
            return None
            
    except Exception as e:
        print(f"处理文章时出错: {title} - {e}")
        return None

def process_single_article(title, link_info):
    """处理单篇文章"""
    content = get_article_content(title, link_info)
    if content:
        # 将文章内容添加到原始数据中
        return title, list(link_info) + [content]
    else:
        # 如果获取失败，返回None表示删除该数据
        return None

def process_article_batch(articles_batch):
    """处理一批文章 - 并行处理"""
    results = {}
    
    # 使用线程池并行处理文章
    with ThreadPoolExecutor(max_workers=5) as executor:
        # 提交所有任务
        future_to_title = {
            executor.submit(process_single_article, title, link_info): title
            for title, link_info in articles_batch.items()
        }
        
        # 收集结果
        for future in as_completed(future_to_title):
            title = future_to_title[future]
            try:
                result = future.result()
                if result is not None:
                    title, article_data = result
                    results[title] = article_data
                    print(f"✅ 成功获取: {title}")
                else:
                    print(f"❌ 删除失败数据: {title}")
            except Exception as e:
                print(f"❌ 处理失败: {title} - {e}")
    
    return results

def save_to_database(all_results):
    """将文章内容保存到数据库，只更新成功爬取的文章内容"""
    try:
        # 连接数据库
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'title_link.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取数据库中所有标题
        cursor.execute('SELECT title FROM title_link')
        db_titles = {row[0] for row in cursor.fetchall()}
        
        # 获取成功爬取的文章标题
        success_titles = set(all_results.keys())
        
        # 只更新成功爬取的文章内容，不删除任何现有数据
        updated_count = 0
        skipped_count = 0
        
        for title, article_data in all_results.items():
            if len(article_data) > 3:  # 确保有内容字段
                content = article_data[3]
                try:
                    # 检查文章是否在数据库中
                    if title in db_titles:
                        cursor.execute('UPDATE title_link SET content = ? WHERE title = ?', (content, title))
                        if cursor.rowcount > 0:
                            updated_count += 1
                            print(f"✅ 更新文章内容: {title}")
                        else:
                            skipped_count += 1
                            print(f"⚠️ 文章不存在于数据库: {title}")
                    else:
                        skipped_count += 1
                        print(f"⚠️ 文章不存在于数据库: {title}")
                except Exception as e:
                    print(f"❌ 更新数据库失败 {title}: {e}")
        
        # 提交更改
        conn.commit()
        conn.close()
        
        print(f"📊 数据库操作完成:")
        print(f"   ✅ 成功更新: {updated_count} 篇文章内容")
        print(f"   ⚠️ 跳过处理: {skipped_count} 篇文章（不在数据库中）")
        return True
        
    except Exception as e:
        print(f"❌ 保存到数据库失败: {e}")
        return False

def main():
    """主函数：从更新数据获取文章内容"""
    print("开始处理更新数据文章内容爬取任务...")
    
    # 加载更新数据
    title_link_data = load_title_link_data()
    if not title_link_data:
        print("无法加载更新数据，程序退出")
        return
    
    # 按网站分组数据
    huxiu_articles = {}
    sohu_articles = {}
    tencent_articles = {}
    
    for title, link_info in title_link_data.items():
        source = link_info[2]  # 第三个元素是网站来源
        if source == '虎嗅网':
            huxiu_articles[title] = link_info
        elif source == '搜狐网':
            sohu_articles[title] = link_info
        elif source == '腾讯网':
            tencent_articles[title] = link_info
    
    print(f"更新数据分组完成:")
    print(f"虎嗅网: {len(huxiu_articles)} 篇")
    print(f"搜狐网: {len(sohu_articles)} 篇")
    print(f"腾讯网: {len(tencent_articles)} 篇")
    
    # 合并所有文章到一个字典中
    all_articles = {}
    all_articles.update(huxiu_articles)
    all_articles.update(sohu_articles)
    all_articles.update(tencent_articles)
    
    print(f"开始并行处理 {len(all_articles)} 篇更新文章...")
    
    # 使用线程池并行处理所有文章
    all_results = process_article_batch(all_articles)
    
    # 保存结果到数据库
    print(f"总共处理了 {len(all_results)} 篇更新文章")
    
    # 统计成功获取内容的文章数量
    success_count = sum(1 for article_data in all_results.values() 
                      if len(article_data) > 3 and article_data[3])
    
    print(f"成功获取内容的文章: {success_count}/{len(all_results)}")
    
    # 保存到数据库
    if save_to_database(all_results):
        print("✅ 所有更新文章内容已成功保存到数据库")
    else:
        print("❌ 保存到数据库失败")
    
    # 同时保存一份JSON备份
    output_dir = os.path.dirname(__file__)  # 直接使用当前目录
    output_file = os.path.join(output_dir, 'updated_articles_with_content.json')
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"📄 更新文章JSON备份已保存到: {output_file}")
    except Exception as e:
        print(f"❌ 保存更新文章JSON备份失败: {e}")

if __name__ == "__main__":
    # 确保在正确的目录中运行
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 创建必要的目录
    os.makedirs('../huxiu_data', exist_ok=True)
    os.makedirs('../sohu_data', exist_ok=True)
    os.makedirs('../qq_data', exist_ok=True)
    os.makedirs('../all_data', exist_ok=True)
    
    main() 