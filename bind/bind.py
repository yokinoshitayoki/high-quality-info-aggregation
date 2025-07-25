import json
import os

# 读取AI相关标题
with open('filter/ai_titles_v2.txt', 'r', encoding='utf-8') as f:
    titles = [line.strip() for line in f if line.strip()]

# 读取总的标题-链接字典
with open('scrapy/all_data/all_title_links.json', 'r', encoding='utf-8') as f:
    all_title_links = json.load(f)

# 构建AI标题-链接字典
ai_title_links = {}
for title in titles:
    link = all_title_links.get(title, "")
    ai_title_links[title] = link

# 输出到json文件
with open('bind/title_link.json', 'w', encoding='utf-8') as f:
    json.dump(ai_title_links, f, ensure_ascii=False, indent=2)
print(f"已写入 bind/title_link.json，共{len(ai_title_links)}条")

# 输出到txt文件
with open('bind/title_link.txt', 'w', encoding='utf-8') as f:
    for title, link in ai_title_links.items():
        f.write(f"{title}\t{link}\n")
print(f"已写入 bind/title_link.txt，共{len(ai_title_links)}条")