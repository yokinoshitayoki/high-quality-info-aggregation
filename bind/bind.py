# v1新增按时间排序
import json
from datetime import datetime

# 读取AI相关标题
with open('filter/ai_titles_v2.txt', 'r', encoding='utf-8') as f:
    titles = [line.strip() for line in f if line.strip()]

# 读取总的标题-链接字典（值为列表：[link, date, source]）
with open('scrapy/all_data/all_title_links.json', 'r', encoding='utf-8') as f:
    all_title_links = json.load(f)

# 构建AI标题-链接-日期-来源列表
ai_title_links = []
for title in titles:
    info = all_title_links.get(title)
    if isinstance(info, list) and len(info) >= 3:
        link, date, source = info[0], info[1], info[2]
    else:
        link, date, source = '', '', ''
    ai_title_links.append({'title': title, 'link': link, 'date': date, 'source': source})

# 按date降序排序（新到旧），无日期的排最后
def parse_date(d):
    try:
        return datetime.strptime(d, '%Y-%m-%d')
    except Exception:
        return datetime.min

ai_title_links.sort(key=lambda x: parse_date(x['date']), reverse=True)

# 输出到json文件（title: [link, date, source]）
with open('bind/title_link.json', 'w', encoding='utf-8') as f:
    json.dump({item['title']: [item['link'], item['date'], item['source']] for item in ai_title_links}, f, ensure_ascii=False, indent=2)
print(f"已写入 bind/title_link.json，共{len(ai_title_links)}条")

# 输出到txt文件
with open('bind/title_link.txt', 'w', encoding='utf-8') as f:
    for item in ai_title_links:
        f.write(f"{item['title']}\t{item['link']}\t{item['date']}\t{item['source']}\n")
print(f"已写入 bind/title_link.txt，共{len(ai_title_links)}条")