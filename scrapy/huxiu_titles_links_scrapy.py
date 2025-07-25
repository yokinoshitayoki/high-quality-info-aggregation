from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import json
from datetime import datetime, timedelta
import re

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

def fetch_huxiu_titles_selenium_scroll(max_scrolls=10, wait_time=1):
    titles = set()
    title_link_dict = {}
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    )
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://www.huxiu.com/channel/105.html")
    time.sleep(3)

    last_count = 0
    no_new_count = 0

    for i in range(max_scrolls):
        title_elements = driver.find_elements(By.CSS_SELECTOR, 'h3.channel-title.two-lines')
        for title_elem in title_elements:
            title = title_elem.text.strip()
            if not title:
                continue
            try:
                ancestor = title_elem.find_element(By.XPATH, './../../..')
                link_elem = ancestor.find_element(By.CSS_SELECTOR, 'a.empty')
                link = link_elem.get_attribute('href')
                # 获取时间
                time_elem = ancestor.find_element(By.CSS_SELECTOR, 'div.bottom-line__time')
                time_str = time_elem.text.strip()
                date_str = parse_time_str(time_str)
                #print(date_str)
            except Exception as e:
                link = ''
                date_str = ''
                print(e)
            # 只保留有链接和日期的
            if link and date_str:
                titles.add(title)
                title_link_dict[title] = [link, date_str, '虎嗅网']
            else:
                print(f"跳过无效数据: {title}, link: {link}, date: {date_str}")
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
    titles, title_link_dict = fetch_huxiu_titles_selenium_scroll(max_scrolls=10, wait_time=1)
    print(f"共抓取到{len(titles)}个标题（去重后）")
    with open('scrapy/huxiu_data/huxiu_titles.txt', 'w', encoding='utf-8') as f:
        for t in titles:
            f.write(t + '\n')
    print("所有标题已写入 huxiu_titles.txt")
    with open('scrapy/huxiu_data/huxiu_title_links.txt', 'w', encoding='utf-8') as f:
        for title, link in title_link_dict.items():
            f.write(f"{title}\t{link}\n")
    print("标题-链接字典已写入 huxiu_title_links.txt")
    with open('scrapy/huxiu_data/huxiu_title_links.json', 'w', encoding='utf-8') as f:
        json.dump(title_link_dict, f, ensure_ascii=False, indent=2)
    print("标题-链接-时间字典已写入 huxiu_title_links.json")