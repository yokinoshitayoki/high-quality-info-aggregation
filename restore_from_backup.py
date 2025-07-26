import os
import shutil
import json

def restore_from_backup():
    """从data_backup还原所有数据到初始化位置"""
    
    # 定义备份目录和对应的目标目录
    backup_mappings = [
        # 爬虫数据
        ('data_backup/scrapy/huxiu_data', 'scrapy/huxiu_data'),
        ('data_backup/scrapy/qq_data', 'scrapy/qq_data'),
        ('data_backup/scrapy/sohu_data', 'scrapy/sohu_data'),
        ('data_backup/scrapy/all_data', 'scrapy/all_data'),
        
        # 过滤数据
        ('data_backup/filter', 'filter'),
        
        # 绑定数据
        ('data_backup/bind', 'bind'),
        
        # 数据库
        ('data_backup/database', 'database'),
    ]
    
    restored_files = []
    
    for backup_dir, target_dir in backup_mappings:
        if os.path.exists(backup_dir):
            print(f"还原目录: {backup_dir} -> {target_dir}")
            
            # 确保目标目录存在
            os.makedirs(target_dir, exist_ok=True)
            
            # 复制所有文件
            for root, dirs, files in os.walk(backup_dir):
                # 计算相对路径
                rel_path = os.path.relpath(root, backup_dir)
                target_root = os.path.join(target_dir, rel_path)
                
                # 创建目标子目录
                os.makedirs(target_root, exist_ok=True)
                
                # 复制文件
                for file in files:
                    source_file = os.path.join(root, file)
                    target_file = os.path.join(target_root, file)
                    
                    try:
                        shutil.copy2(source_file, target_file)
                        restored_files.append(target_file)
                        print(f"  已还原: {target_file}")
                    except Exception as e:
                        print(f"  还原失败 {target_file}: {e}")
        else:
            print(f"备份目录不存在: {backup_dir}")
    
    print(f"\n还原完成！共还原了 {len(restored_files)} 个文件:")
    for file in restored_files:
        print(f"  - {file}")
    
    # 验证关键文件
    print("\n验证关键文件:")
    key_files = [
        'scrapy/all_data/all_title_links.json',
        'bind/title_link.json',
        'database/title_link.db'
    ]
    
    for key_file in key_files:
        if os.path.exists(key_file):
            if key_file.endswith('.json'):
                try:
                    with open(key_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    print(f"  ✓ {key_file} - {len(data)}条数据")
                except:
                    print(f"  ✓ {key_file} - 文件存在但格式错误")
            elif key_file.endswith('.db'):
                print(f"  ✓ {key_file} - 数据库文件")
            else:
                print(f"  ✓ {key_file} - 文件存在")
        else:
            print(f"  ✗ {key_file} - 文件不存在")

if __name__ == "__main__":
    restore_from_backup() 