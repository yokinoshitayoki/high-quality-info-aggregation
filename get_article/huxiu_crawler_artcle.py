import requests
from bs4 import BeautifulSoup
import time
import random

class HuxiuCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def get_article_content(self, url):
        """
        爬取虎嗅网文章内容
        返回: {'title': str, 'content': str, 'success': bool, 'error': str}
        """
        try:
            # 添加随机延迟（减少延迟时间）
            time.sleep(random.uniform(0.5, 1.5))
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 获取文章标题
            title = self._extract_title(soup)
            
            # 获取文章内容
            content = self._extract_content(soup)
            
            if not content:
                return {
                    'title': title,
                    'content': '',
                    'success': False,
                    'error': '未找到文章内容'
                }
            
            return {
                'title': title,
                'content': content,
                'success': True,
                'error': None
            }
            
        except requests.RequestException as e:
            return {
                'title': '',
                'content': '',
                'success': False,
                'error': f'网络请求失败: {str(e)}'
            }
        except Exception as e:
            return {
                'title': '',
                'content': '',
                'success': False,
                'error': f'爬取失败: {str(e)}'
            }
    
    def _extract_title(self, soup):
        """提取文章标题"""
        # 尝试多种标题选择器
        title_selectors = [
            'h1.article-title',
            'h1.title',
            '.article-title',
            '.title',
            'h1',
            'title'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text().strip()
                if title:
                    return title
        
        return ''
    
    def _extract_content(self, soup):
        """提取文章内容"""
        # 根据虎嗅网的文章元素结构，查找带有data-check-id属性的<p>标签
        content_paragraphs = []
        
        # 查找所有<p>标签，特别关注有data-check-id属性的
        p_tags = soup.find_all('p')
        
        for p in p_tags:
            # 优先处理有data-check-id属性的段落
            if p.get('data-check-id') and self._is_valid_content(p):
                text = p.get_text().strip()
                if text and len(text) > 10:
                    content_paragraphs.append(text)
        
        # 如果没有找到带data-check-id的段落，尝试其他<p>标签
        if not content_paragraphs:
            for p in p_tags:
                if self._is_valid_content(p):
                    text = p.get_text().strip()
                    if text and len(text) > 10:
                        content_paragraphs.append(text)
        
        return '\n\n'.join(content_paragraphs)
    
    def _is_valid_content(self, p_tag):
        """判断是否为有效的文章内容"""
        # 检查是否包含导航、广告等关键词
        invalid_keywords = ['广告', '推广', '赞助', '版权', '免责声明', '相关阅读', '虎嗅', 'huxiu']
        text = p_tag.get_text().lower()
        
        for keyword in invalid_keywords:
            if keyword in text:
                return False
        
        # 检查class属性
        class_attr = p_tag.get('class', [])
        invalid_classes = ['ad', 'advertisement', 'nav', 'navigation', 'footer', 'header', 'sidebar']
        
        for invalid_class in invalid_classes:
            if any(invalid_class in str(cls).lower() for cls in class_attr):
                return False
        
        # 检查是否为空或太短
        text = p_tag.get_text().strip()
        if not text or len(text) < 10:
            return False
        
        return True

def get_article_content(url):
    """便捷函数，直接调用爬取器"""
    crawler = HuxiuCrawler()
    return crawler.get_article_content(url)

if __name__ == "__main__":
    # 处理命令行传入的URL
    import sys
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
        print(f"正在处理URL: {url}")
        result = get_article_content(url)
        print("虎嗅网文章爬取结果:")
        print(f"成功: {result['success']}")
        print(f"标题: {result['title']}")
        print(f"内容长度: {len(result['content'])}")
        if result['error']:
            print(f"错误: {result['error']}")
        else:
            print(f"内容预览: {result['content'][:200]}...")
    else:
        print("使用方法: python huxiu_crawler_artcle.py <URL>")
        print("示例: python huxiu_crawler_artcle.py https://www.huxiu.com/article/4621458.html") 