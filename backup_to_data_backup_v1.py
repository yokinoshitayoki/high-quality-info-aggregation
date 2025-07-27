import os
import shutil
import json
from datetime import datetime

def backup_to_data_backup_v1():
    """将现有数据备份到data_backup_v1目录，只备份数据文件"""
    
    # 定义源目录和对应的备份目录（只包含数据文件）
    backup_mappings = [
        # 爬虫数据
        ('scrapy/huxiu_data', 'data_backup_v1/scrapy/huxiu_data'),
        ('scrapy/qq_data', 'data_backup_v1/scrapy/qq_data'),
        ('scrapy/sohu_data', 'data_backup_v1/scrapy/sohu_data'),
        ('scrapy/all_data', 'data_backup_v1/scrapy/all_data'),
        
        # 过滤数据（只备份结果文件）
        ('filter/init_filter', 'data_backup_v1/filter/init_filter'),
        ('filter/upd_filter', 'data_backup_v1/filter/upd_filter'),
        
        # 绑定数据（只备份结果文件）
        ('bind/init_bind', 'data_backup_v1/bind/init_bind'),
        ('bind/upd_bind', 'data_backup_v1/bind/upd_bind'),
        
        # 数据库
        ('database', 'data_backup_v1/database'),
        
        # 后端数据文件
        ('backend/feedback.json', 'data_backup_v1/backend/feedback.json'),
    ]
    
    backed_up_files = []
    
    # 创建备份时间戳
    backup_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    print(f"开始备份数据 - 时间: {backup_time}")
    
    for source_path, backup_path in backup_mappings:
        if os.path.exists(source_path):
            print(f"备份: {source_path} -> {backup_path}")
            
            # 确保备份目录存在
            if os.path.isdir(source_path):
                os.makedirs(backup_path, exist_ok=True)
                
                # 复制目录中的所有数据文件
                for root, dirs, files in os.walk(source_path):
                    # 计算相对路径
                    rel_path = os.path.relpath(root, source_path)
                    backup_root = os.path.join(backup_path, rel_path)
                    
                    # 创建备份子目录
                    os.makedirs(backup_root, exist_ok=True)
                    
                    # 复制文件（只复制数据文件，跳过代码文件）
                    for file in files:
                        # 跳过代码文件
                        if file.endswith(('.py', '.pyc', '__pycache__')):
                            continue
                        
                        source_file = os.path.join(root, file)
                        backup_file = os.path.join(backup_root, file)
                        
                        try:
                            shutil.copy2(source_file, backup_file)
                            backed_up_files.append(backup_file)
                            print(f"  已备份: {backup_file}")
                        except Exception as e:
                            print(f"  备份失败 {backup_file}: {e}")
            else:
                # 复制单个文件
                try:
                    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                    shutil.copy2(source_path, backup_path)
                    backed_up_files.append(backup_path)
                    print(f"  已备份: {backup_path}")
                except Exception as e:
                    print(f"  备份失败 {backup_path}: {e}")
        else:
            print(f"源路径不存在: {source_path}")
    
    print(f"\n备份完成！共备份了 {len(backed_up_files)} 个数据文件:")
    for file in backed_up_files:
        print(f"  - {file}")
    
    # 验证关键数据文件
    print("\n验证关键备份数据文件:")
    key_files = [
        'data_backup_v1/scrapy/all_data/all_title_links.json',
        'data_backup_v1/bind/init_bind/title_link.json',
        'data_backup_v1/database/title_link.db',
        'data_backup_v1/backend/feedback.json'
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
    
    # 创建备份信息文件
    backup_info = {
        "backup_time": backup_time,
        "backup_type": "data_only",
        "total_files": len(backed_up_files),
        "backup_files": backed_up_files
    }
    
    backup_info_file = "data_backup_v1/backup_info.json"
    try:
        with open(backup_info_file, 'w', encoding='utf-8') as f:
            json.dump(backup_info, f, ensure_ascii=False, indent=2)
        print(f"\n备份信息已保存到: {backup_info_file}")
    except Exception as e:
        print(f"保存备份信息失败: {e}")

if __name__ == "__main__":
    backup_to_data_backup_v1() 