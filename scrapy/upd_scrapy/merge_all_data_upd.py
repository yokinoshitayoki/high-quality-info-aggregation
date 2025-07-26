import os
import json

def read_title_links_txt(file_path):
    title_link_dict = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        if not content:  # 如果文件为空
            return {}
        for line in content.split('\n'):
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                title = parts[0]
                link = parts[1]
                title_link_dict[title] = link
    return title_link_dict

def read_title_links_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        if not content:  # 如果文件为空
            return {}
        return json.loads(content)

def read_titles_txt(file_path):
    titles = set()
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        if not content:  # 如果文件为空
            return set()
        for line in content.split('\n'):
            title = line.strip()
            if title:
                titles.add(title)
    return titles

def merge_all_title_links_and_titles_upd():
    base_dirs = [
        'scrapy/huxiu_data',
        'scrapy/qq_data',
        'scrapy/sohu_data'
    ]
    all_title_link_dict = {}
    all_titles = set()

    # 首先读取原有的all_data文件
    out_dir = 'scrapy/all_data'
    existing_all_title_links_json = {}
    existing_all_titles = set()
    
    # 读取原有的all_title_links.json
    existing_json_file = os.path.join(out_dir, 'all_title_links.json')
    if os.path.exists(existing_json_file):
        print(f"读取原有数据：{existing_json_file}")
        existing_all_title_links_json = read_title_links_json(existing_json_file)
    
    # 读取原有的all_titles.txt
    existing_titles_file = os.path.join(out_dir, 'all_titles.txt')
    if os.path.exists(existing_titles_file):
        print(f"读取原有标题：{existing_titles_file}")
        existing_all_titles = read_titles_txt(existing_titles_file)

    # 合并各网站的更新文件
    for base_dir in base_dirs:
        site_name = os.path.basename(base_dir).replace('_data', '')
        
        # 读取更新文件
        upd_txt_file = os.path.join(base_dir, f"{site_name}_title_links_upd.txt")
        upd_json_file = os.path.join(base_dir, f"{site_name}_title_links_upd.json")
        upd_titles_file = os.path.join(base_dir, f"{site_name}_title_upd.txt")
        
        # 处理更新文件
        if os.path.exists(upd_txt_file):
            print(f"读取更新文件：{upd_txt_file}")
            title_link_dict = read_title_links_txt(upd_txt_file)
            all_title_link_dict.update(title_link_dict)
        
        if os.path.exists(upd_json_file):
            print(f"读取更新文件：{upd_json_file}")
            title_link_dict = read_title_links_json(upd_json_file)
            all_title_link_dict.update(title_link_dict)
        
        if os.path.exists(upd_titles_file):
            print(f"读取更新标题：{upd_titles_file}")
            titles = read_titles_txt(upd_titles_file)
            all_titles.update(titles)

    # 合并原有数据和更新数据
    final_all_title_links_json = existing_all_title_links_json.copy()
    final_all_title_links_json.update(all_title_link_dict)
    
    final_all_titles = existing_all_titles.copy()
    final_all_titles.update(all_titles)

    # 检查是否有新数据
    if not all_title_link_dict and not all_titles:
        print("没有发现新数据，无需更新")
        return

    # 确保输出目录存在
    os.makedirs(out_dir, exist_ok=True)
    
    # 输出更新后的all_title_links.json
    with open(os.path.join(out_dir, 'all_title_links.json'), 'w', encoding='utf-8') as f:
        json.dump(final_all_title_links_json, f, ensure_ascii=False, indent=2)
    print(f"已更新 {out_dir}/all_title_links.json，共{len(final_all_title_links_json)}条")

    # 输出更新后的all_titles.txt
    with open(os.path.join(out_dir, 'all_titles.txt'), 'w', encoding='utf-8') as f:
        for title in final_all_titles:
            f.write(title + '\n')
    print(f"已更新 {out_dir}/all_titles.txt，共{len(final_all_titles)}条")

    # 输出更新数据到all_title_upd.json
    with open(os.path.join(out_dir, 'all_title_links_upd.json'), 'w', encoding='utf-8') as f:
        json.dump(all_title_link_dict, f, ensure_ascii=False, indent=2)
    print(f"已写入 {out_dir}/all_title_links_upd.json，共{len(all_title_link_dict)}条")

    # 输出更新标题到all_titles_upd.txt
    with open(os.path.join(out_dir, 'all_titles_upd.txt'), 'w', encoding='utf-8') as f:
        for title in all_titles:
            f.write(title + '\n')
    print(f"已写入 {out_dir}/all_titles_upd.txt，共{len(all_titles)}条")

    # 输出合并后的txt（标题-链接）
    with open(os.path.join(out_dir, 'all_title_links.txt'), 'w', encoding='utf-8') as f:
        for title, link_info in final_all_title_links_json.items():
            if isinstance(link_info, list):
                f.write(f"{title}\t{link_info[0]}\n")
            else:
                f.write(f"{title}\t{link_info}\n")
    print(f"已更新 {out_dir}/all_title_links.txt，共{len(final_all_title_links_json)}条")

if __name__ == "__main__":
    merge_all_title_links_and_titles_upd()