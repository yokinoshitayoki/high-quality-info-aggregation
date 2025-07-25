from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import json
import os
import re
from datetime import datetime, timedelta

def parse_time_str(time_str):
    now = datetime.now()
    # 1. 分钟前
    if "分钟前" in time_str:
        match = re.search(r"(\d+)分钟前", time_str)
        if match:
            minutes = int(match.group(1))
            dt = now - timedelta(minutes=minutes)
            return dt.strftime("%Y-%m-%d")
        else:
            return ''
    # 2. 小时前
    elif "小时前" in time_str:
        match = re.search(r"(\d+)小时前", time_str)
        if match:
            hours = int(match.group(1))
            dt = now - timedelta(hours=hours)
            return dt.strftime("%Y-%m-%d")
        else:
            return ''
    # 3. 天前
    elif "天前" in time_str:
        match = re.search(r"(\d+)天前", time_str)
        if match:
            days = int(match.group(1))
            dt = now - timedelta(days=days)
            return dt.strftime("%Y-%m-%d")
        else:
            return ''
    # 4. 昨天
    elif time_str.startswith("昨天"):
        dt = now - timedelta(days=1)
        return dt.strftime("%Y-%m-%d")
    # 5. 前天
    elif time_str.startswith("前天"):
        dt = now - timedelta(days=2)
        return dt.strftime("%Y-%m-%d")
    # 6. 其它情况，尝试只保留年月日
    match = re.search(r"(\d{4}-\d{2}-\d{2})", time_str)
    if match:
        return match.group(1)
    return ''

def fetch_qq_titles_and_links(max_scrolls=10, wait_time=1):
    titles = set()
    title_link_dict = {}
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    )
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://news.qq.com/ch/tech")
    time.sleep(3)

    last_count = 0
    no_new_count = 0

    for i in range(max_scrolls):
        card_elements = driver.find_elements(By.CSS_SELECTOR, 'a.article-title')
        for card in card_elements:
            # 筛掉视频跳转元素
            if 'video-jump' in card.get_attribute('class').split():
                continue
            try:
                link = card.get_attribute('href')
                title_elem = card.find_element(By.CSS_SELECTOR, 'span.article-title-text')
                title = title_elem.text.strip()
                # 获取下一个兄弟节点的时间
                time_str = ''
                try:
                    sibling = card.find_element(By.XPATH, 'following-sibling::*[1]')
                    time_elem = sibling.find_element(By.CSS_SELECTOR, 'span.time')
                    time_str = time_elem.text.strip()
                except Exception as e:
                    print(f"未找到时间")
                    continue
                date_str = parse_time_str(time_str)
                if title and link and date_str:
                    titles.add(title)
                    title_link_dict[title] = [link, date_str, '腾讯网']
                else:
                    print(f"跳过无效数据: {title}, link: {link}, date: {date_str}")
            except Exception as e:
                continue
        print(f"第{i+1}次下滑，已抓取{len(titles)}个标题")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(wait_time)
        if len(titles) == last_count:
            no_new_count += 1
            if no_new_count >= 3:
                print("检测到没有新内容，停止下滑。")
                break
        else:
            no_new_count = 0
            last_count = len(titles)

    driver.quit()
    return list(titles), title_link_dict

if __name__ == "__main__":
    os.makedirs('scrapy', exist_ok=True)
    titles, title_link_dict = fetch_qq_titles_and_links(max_scrolls=10, wait_time=1)
    print(f"共抓取到{len(titles)}个标题（去重后）")
    with open('scrapy/qq_data/qq_titles.txt', 'w', encoding='utf-8') as f:
        for t in titles:
            f.write(t + '\n')
    print("所有标题已写入 qq_titles.txt")
    with open('scrapy/qq_data/qq_title_links.json', 'w', encoding='utf-8') as f:
        json.dump(title_link_dict, f, ensure_ascii=False, indent=2)
    print("标题-链接-时间-来源字典已写入 qq_title_links.json")
