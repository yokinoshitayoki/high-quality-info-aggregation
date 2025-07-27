import os
import sys
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def run_scrapy_script(script_name, description):
    """运行单个爬虫脚本"""
    try:
        print(f"开始运行 {description}...")
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, 
                              text=True, 
                              encoding='utf-8')
        
        if result.returncode == 0:
            print(f"{description} 运行成功")
            if result.stdout:
                print(f"输出: {result.stdout}")
        else:
            print(f"{description} 运行失败")
            if result.stderr:
                print(f"错误: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"{description} 运行异常: {e}")
        return False

def run_merge_script():
    """运行数据合并脚本"""
    try:
        print("开始运行数据合并脚本...")
        result = subprocess.run([sys.executable, 'merge_all_data.py'], 
                              capture_output=True, 
                              text=True, 
                              encoding='utf-8')
        
        if result.returncode == 0:
            print("数据合并脚本运行成功")
            if result.stdout:
                print(f"输出: {result.stdout}")
        else:
            print("数据合并脚本运行失败")
            if result.stderr:
                print(f"错误: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"数据合并脚本运行异常: {e}")
        return False

def main():
    """主函数：并行运行爬虫脚本，然后运行合并脚本"""
    print("开始并行运行爬虫脚本...")
    
    # 定义要运行的爬虫脚本
    scrapy_scripts = [
        ('huxiu_titles_links_scrapy.py', '虎嗅网爬虫'),
        ('sohu_titles_links_scrapy.py', '搜狐网爬虫'),
        ('tencent_titles_links_scrapy.py', '腾讯网爬虫')
    ]
    
    # 使用线程池并行运行爬虫脚本
    success_count = 0
    with ThreadPoolExecutor(max_workers=3) as executor:
        # 提交所有任务
        future_to_script = {
            executor.submit(run_scrapy_script, script, desc): (script, desc)
            for script, desc in scrapy_scripts
        }
        
        # 等待所有任务完成
        for future in as_completed(future_to_script):
            script, desc = future_to_script[future]
            try:
                success = future.result()
                if success:
                    success_count += 1
            except Exception as e:
                print(f"{desc} 执行异常: {e}")
    
    print(f"\n爬虫脚本执行完成: {success_count}/{len(scrapy_scripts)} 个成功")
    
    # 等待一段时间确保文件写入完成
    print("等待文件写入完成...")
    time.sleep(2)
    
    # 运行数据合并脚本
    print("\n开始运行数据合并脚本...")
    merge_success = run_merge_script()
    
    if merge_success:
        print("\n所有任务执行完成！")
    else:
        print("\n数据合并失败，请检查错误信息")

if __name__ == "__main__":
    # 确保在正确的目录中运行
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 创建必要的目录
    os.makedirs('../huxiu_data', exist_ok=True)
    os.makedirs('../sohu_data', exist_ok=True)
    os.makedirs('../qq_data', exist_ok=True)
    os.makedirs('../all_data', exist_ok=True)
    
    main()
