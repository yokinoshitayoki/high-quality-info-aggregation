import os
import glob

def clear_upd_files():
    """清空所有带有upd后缀的json和txt文件"""
    
    # 定义要搜索的目录
    search_dirs = [
        'scrapy/huxiu_data',
        'scrapy/qq_data', 
        'scrapy/sohu_data',
        'scrapy/all_data',
        'bind/upd_bind',
        'filter/upd_filter'
    ]
    
    cleared_files = []
    
    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            print(f"搜索目录: {search_dir}")
            
            # 搜索所有*_upd.json文件
            json_pattern = os.path.join(search_dir, '*_upd.json')
            json_files = glob.glob(json_pattern)
            
            # 搜索所有*_upd.txt文件
            txt_pattern = os.path.join(search_dir, '*_upd.txt')
            txt_files = glob.glob(txt_pattern)
            
            # 清空json文件
            for json_file in json_files:
                try:
                    with open(json_file, 'w', encoding='utf-8') as f:
                        f.write('')
                    cleared_files.append(json_file)
                    print(f"已清空: {json_file}")
                except Exception as e:
                    print(f"清空失败 {json_file}: {e}")
            
            # 清空txt文件
            for txt_file in txt_files:
                try:
                    with open(txt_file, 'w', encoding='utf-8') as f:
                        f.write('')
                    cleared_files.append(txt_file)
                    print(f"已清空: {txt_file}")
                except Exception as e:
                    print(f"清空失败 {txt_file}: {e}")
        else:
            print(f"目录不存在: {search_dir}")
    
    print(f"\n清空完成！共清空了 {len(cleared_files)} 个文件:")
    for file in cleared_files:
        print(f"  - {file}")

if __name__ == "__main__":
    clear_upd_files() 