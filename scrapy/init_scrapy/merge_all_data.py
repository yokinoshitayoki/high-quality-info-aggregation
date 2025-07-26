import os
import json

def read_title_links_txt(file_path):
    title_link_dict = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) == 2:
                title, link = parts
                title_link_dict[title] = link
    return title_link_dict

def read_title_links_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def read_titles_txt(file_path):
    titles = set()
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            title = line.strip()
            if title:
                titles.add(title)
    return titles

def merge_all_title_links_and_titles():
    base_dirs = [
        'scrapy/huxiu_data',
        'scrapy/qq_data',
        'scrapy/sohu_data'
    ]
    all_title_link_dict = {}
    all_titles = set()

    # 合并txt（标题-链接）
    for base_dir in base_dirs:
        txt_file = os.path.join(base_dir, f"{os.path.basename(base_dir).replace('_data','')}_title_links.txt")
        if os.path.exists(txt_file):
            print(f"读取：{txt_file}")
            title_link_dict = read_title_links_txt(txt_file)
            all_title_link_dict.update(title_link_dict)
        else:
            print(f"未找到：{txt_file}")

    # 输出合并后的txt（标题-链接）
    out_dir = 'scrapy/all_data'
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'all_title_links.txt'), 'w', encoding='utf-8') as f:
        for title, link in all_title_link_dict.items():
            f.write(f"{title}\t{link}\n")
    print(f"已写入 {out_dir}/all_title_links.txt，共{len(all_title_link_dict)}条")

    # 合并json（标题-链接）
    all_title_link_dict_json = {}
    for base_dir in base_dirs:
        json_file = os.path.join(base_dir, f"{os.path.basename(base_dir).replace('_data','')}_title_links.json")
        if os.path.exists(json_file):
            print(f"读取：{json_file}")
            title_link_dict = read_title_links_json(json_file)
            all_title_link_dict_json.update(title_link_dict)
        else:
            print(f"未找到：{json_file}")

    # 输出合并后的json（标题-链接）
    with open(os.path.join(out_dir, 'all_title_links.json'), 'w', encoding='utf-8') as f:
        json.dump(all_title_link_dict_json, f, ensure_ascii=False, indent=2)
    print(f"已写入 {out_dir}/all_title_links.json，共{len(all_title_link_dict_json)}条")

    # 合并所有title
    for base_dir in base_dirs:
        titles_file = os.path.join(base_dir, f"{os.path.basename(base_dir).replace('_data','')}_titles.txt")
        if os.path.exists(titles_file):
            print(f"读取：{titles_file}")
            titles = read_titles_txt(titles_file)
            all_titles.update(titles)
        else:
            print(f"未找到：{titles_file}")
    # 输出合并后的title
    with open(os.path.join(out_dir, 'all_titles.txt'), 'w', encoding='utf-8') as f:
        for title in all_titles:
            f.write(title + '\n')
    print(f"已写入 {out_dir}/all_titles.txt，共{len(all_titles)}条")

if __name__ == "__main__":
    merge_all_title_links_and_titles() 