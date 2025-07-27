import os
import shutil
import json

def restore_from_backup():
    """从data_backup_v1还原所有数据文件到初始化位置"""
    
    # 定义备份目录和对应的目标目录（只包含数据文件）
    backup_mappings = [
        # 爬虫数据
        ('data_backup_v1/scrapy/huxiu_data', 'scrapy/huxiu_data'),
        ('data_backup_v1/scrapy/qq_data', 'scrapy/qq_data'),
        ('data_backup_v1/scrapy/sohu_data', 'scrapy/sohu_data'),
        ('data_backup_v1/scrapy/all_data', 'scrapy/all_data'),
        
        # 过滤数据（只还原结果文件）
        ('data_backup_v1/filter/init_filter', 'filter/init_filter'),
        ('data_backup_v1/filter/upd_filter', 'filter/upd_filter'),
        
        # 绑定数据（只还原结果文件）
        ('data_backup_v1/bind/init_bind', 'bind/init_bind'),
        ('data_backup_v1/bind/upd_bind', 'bind/upd_bind'),
        
        # 数据库
        ('data_backup_v1/database', 'database'),
        
        # 后端数据文件
        ('data_backup_v1/backend/feedback.json', 'backend/feedback.json'),
    ]
    
    restored_files = []
    
    for backup_path, target_path in backup_mappings:
        if os.path.exists(backup_path):
            print(f"还原: {backup_path} -> {target_path}")
            
            # 确保目标目录存在
            if os.path.isdir(backup_path):
                os.makedirs(target_path, exist_ok=True)
                
                # 复制所有数据文件
                for root, dirs, files in os.walk(backup_path):
                    # 计算相对路径
                    rel_path = os.path.relpath(root, backup_path)
                    target_root = os.path.join(target_path, rel_path)
                    
                    # 创建目标子目录
                    os.makedirs(target_root, exist_ok=True)
                    
                    # 复制文件（只复制数据文件，跳过代码文件）
                    for file in files:
                        # 跳过代码文件
                        if file.endswith(('.py', '.pyc', '__pycache__')):
                            continue
                        
                        source_file = os.path.join(root, file)
                        target_file = os.path.join(target_root, file)
                        
                        try:
                            shutil.copy2(source_file, target_file)
                            restored_files.append(target_file)
                            print(f"  已还原: {target_file}")
                        except Exception as e:
                            print(f"  还原失败 {target_file}: {e}")
            else:
                # 复制单个文件
                try:
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    shutil.copy2(backup_path, target_path)
                    restored_files.append(target_path)
                    print(f"  已还原: {target_path}")
                except Exception as e:
                    print(f"  还原失败 {target_path}: {e}")
        else:
            print(f"备份路径不存在: {backup_path}")
    
    print(f"\n还原完成！共还原了 {len(restored_files)} 个数据文件:")
    for file in restored_files:
        print(f"  - {file}")
    
    # 验证关键数据文件
    print("\n验证关键数据文件:")
    key_files = [
        'scrapy/all_data/all_title_links.json',
        'bind/init_bind/title_link.json',
        'database/title_link.db',
        'backend/feedback.json'
    ]
    
    for key_file in key_files:
        if os.path.exists(key_file):
            if key_file.endswith('.json'):
                try:
                    with open(key_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, dict):
                        print(f"  ✓ {key_file} - {len(data)}条数据")
                    elif isinstance(data, list):
                        print(f"  ✓ {key_file} - {len(data)}条数据")
                    else:
                        print(f"  ✓ {key_file} - 数据文件")
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