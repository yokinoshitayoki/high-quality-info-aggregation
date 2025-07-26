from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import json
from datetime import datetime, timedelta
import re
import os

def parse_time_str(time_str):
    now = datetime.now()
    if "分钟前" in time_str:
        match = re.search(r"(\d+)分钟前", time_str)
        if match:
            minutes = int(match.group(1))
            dt = now - timedelta(minutes=minutes)
            return dt.strftime("%Y-%m-%d")
        else:
            return ''
    elif "小时前" in time_str:
        match = re.search(r"(\d+)小时前", time_str)
        if match:
            hours = int(match.group(1))
            dt = now - timedelta(hours=hours)
            return dt.strftime("%Y-%m-%d")
        else:
            return ''
    elif "天前" in time_str:
        match = re.search(r"(\d+)天前", time_str)
        if match:
            days = int(match.group(1))
            dt = now - timedelta(days=days)
            return dt.strftime("%Y-%m-%d")
        else:
            return ''
    # 直接显示日期，保留年月日（如2025-07-18）
    if re.match(r"\d{4}-\d{2}-\d{2}", time_str):
        return time_str[:10]
    return ''

def load_existing_titles():
    """加载现有的标题列表"""
    existing_titles = set()
    titles_file = 'scrapy/huxiu_data/huxiu_titles.txt'
    if os.path.exists(titles_file):
        with open(titles_file, 'r', encoding='utf-8') as f:
            for line in f:
                title = line.strip()
                if title:
                    existing_titles.add(title)
        print(f"已加载 {len(existing_titles)} 个现有标题")
    else:
        print("未找到现有标题文件，将创建新文件")
    return existing_titles

def fetch_huxiu_titles_update(existing_titles, max_scrolls=10, wait_time=1):
    """增量更新虎嗅网标题，遇到重复标题时停止"""
    new_titles = []
    new_title_link_dict = {}
    duplicate_found = False
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    )
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://www.huxiu.com/channel/105.html")
    time.sleep(3)

    for i in range(max_scrolls):
        if duplicate_found:
            print("发现重复标题，停止爬取")
            break
            
        title_elements = driver.find_elements(By.CSS_SELECTOR, 'h3.channel-title.two-lines')
        for title_elem in title_elements:
            title = title_elem.text.strip()
            if not title:
                continue
                
            # 检查是否已存在
            if title in existing_titles:
                print(f"发现重复标题: {title}")
                duplicate_found = True
                break
                
            try:
                ancestor = title_elem.find_element(By.XPATH, './../../..')
                link_elem = ancestor.find_element(By.CSS_SELECTOR, 'a.empty')
                link = link_elem.get_attribute('href')
                # 获取时间
                time_elem = ancestor.find_element(By.CSS_SELECTOR, 'div.bottom-line__time')
                time_str = time_elem.text.strip()
                date_str = parse_time_str(time_str)
            except Exception as e:
                link = ''
                date_str = ''
                print(f"解析标题 '{title}' 时出错: {e}")
                
            # 只保留有链接和日期的
            if link and date_str:
                new_titles.append(title)
                new_title_link_dict[title] = [link, date_str, '虎嗅网']
                print(f"新增标题: {title}")
            else:
                print(f"跳过无效数据: {title}, link: {link}, date: {date_str}")
        
        if duplicate_found:
            break
            
        print(f"第{i+1}次下滑，已抓取{len(new_titles)}个新标题")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(wait_time)

    driver.quit()
    return new_titles, new_title_link_dict

if __name__ == "__main__":
    # 加载现有标题
    existing_titles = load_existing_titles()
    
    # 增量爬取新标题
    new_titles, new_title_link_dict = fetch_huxiu_titles_update(existing_titles, max_scrolls=10, wait_time=1)
    
    print(f"本次更新共抓取到{len(new_titles)}个新标题")
    
    if new_titles:
        # 写入新标题到更新文件
        with open('scrapy/huxiu_data/huxiu_title_upd.txt', 'w', encoding='utf-8') as f:
            for t in new_titles:
                f.write(t + '\n')
        print("新标题已写入 huxiu_title_upd.txt")
        
        # 写入新标题-链接到更新文件
        with open('scrapy/huxiu_data/huxiu_title_links_upd.txt', 'w', encoding='utf-8') as f:
            for title, link_info in new_title_link_dict.items():
                f.write(f"{title}\t{link_info[0]}\t{link_info[1]}\t{link_info[2]}\n")
        print("新标题-链接已写入 huxiu_title_links_upd.txt")
        
        # 写入JSON格式
        with open('scrapy/huxiu_data/huxiu_title_links_upd.json', 'w', encoding='utf-8') as f:
            json.dump(new_title_link_dict, f, ensure_ascii=False, indent=2)
        print("新标题-链接-时间字典已写入 huxiu_title_links_upd.json")
        
        # 自动更新原有文件
        # 更新原有标题文件
        all_titles = list(existing_titles) + new_titles
        with open('scrapy/huxiu_data/huxiu_titles.txt', 'w', encoding='utf-8') as f:
            for t in all_titles:
                f.write(t + '\n')
        print("已更新 huxiu_titles.txt")
        
        # 更新原有链接文件
        all_title_links = {}
        # 先加载原有的
        old_file = 'scrapy/huxiu_data/huxiu_title_links.json'
        if os.path.exists(old_file):
            with open(old_file, 'r', encoding='utf-8') as f:
                all_title_links = json.load(f)
        # 添加新的
        all_title_links.update(new_title_link_dict)
        
        with open('scrapy/huxiu_data/huxiu_title_links.json', 'w', encoding='utf-8') as f:
            json.dump(all_title_links, f, ensure_ascii=False, indent=2)
        print("已更新 huxiu_title_links.json")
    else:
        print("没有发现新标题，无需更新")