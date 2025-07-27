import sqlite3
import os

def read_articles_from_db():
    """从数据库读取文章内容"""
    try:
        # 连接数据库
        db_path = os.path.join(os.path.dirname(__file__), 'title_link.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查询所有文章
        cursor.execute('''
            SELECT title, link, date, source, content 
            FROM title_link 
            ORDER BY date DESC
        ''')
        
        articles = cursor.fetchall()
        conn.close()
        
        print(f"📊 数据库中共有 {len(articles)} 篇文章")
        print("=" * 60)
        
        # 显示文章列表
        for i, (title, link, date, source, content) in enumerate(articles, 1):
            has_content = "✅" if content and content.strip() else "❌"
            print(f"{i:2d}. {has_content} {title}")
            print(f"     📅 {date} | 📰 {source}")
            print(f"     🔗 {link}")
            if content and content.strip():
                print(f"     📝 内容长度: {len(content)} 字符")
                print(f"     📄 内容预览: {content[:100]}...")
            print("-" * 60)
        
        # 统计
        articles_with_content = sum(1 for _, _, _, _, content in articles if content and content.strip())
        print(f"\n📈 统计信息:")
        print(f"   总文章数: {len(articles)}")
        print(f"   有内容的文章: {articles_with_content}")
        print(f"   无内容的文章: {len(articles) - articles_with_content}")
        
        return articles
        
    except Exception as e:
        print(f"❌ 读取数据库失败: {e}")
        return []

def read_specific_article(title):
    """读取特定文章的内容"""
    try:
        # 连接数据库
        db_path = os.path.join(os.path.dirname(__file__), 'title_link.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查询特定文章
        cursor.execute('''
            SELECT title, link, date, source, content 
            FROM title_link 
            WHERE title = ?
        ''', (title,))
        
        article = cursor.fetchone()
        conn.close()
        
        if article:
            title, link, date, source, content = article
            print(f"📰 文章详情:")
            print(f"标题: {title}")
            print(f"链接: {link}")
            print(f"日期: {date}")
            print(f"来源: {source}")
            print("=" * 60)
            print("文章内容:")
            print("=" * 60)
            if content and content.strip():
                print(content)
            else:
                print("❌ 该文章暂无内容")
        else:
            print(f"❌ 未找到标题为 '{title}' 的文章")
            
    except Exception as e:
        print(f"❌ 读取文章失败: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # 如果提供了文章标题参数，读取特定文章
        title = sys.argv[1]
        read_specific_article(title)
    else:
        # 否则显示所有文章列表
        read_articles_from_db() 