#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI过滤脚本调试工具
用于诊断"处理标题出错"的问题
"""

import os
import sys
import json

def check_file_exists(file_path):
    """检查文件是否存在"""
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        print(f"✓ 文件存在: {file_path} (大小: {size} 字节)")
        return True
    else:
        print(f"✗ 文件不存在: {file_path}")
        return False

def check_api_config():
    """检查API配置"""
    try:
        sys.path.append('backend')
        from config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL
        
        print(f"API URL: {DEEPSEEK_API_URL}")
        if DEEPSEEK_API_KEY and DEEPSEEK_API_KEY != "your_deepseek_api_key_here":
            print(f"✓ API密钥已配置: {DEEPSEEK_API_KEY[:10]}...")
            return True
        else:
            print("✗ API密钥未正确配置")
            return False
    except Exception as e:
        print(f"✗ 检查API配置失败: {e}")
        return False

def check_feedback_file():
    """检查反馈文件"""
    feedback_file = 'backend/feedback.json'
    if check_file_exists(feedback_file):
        try:
            with open(feedback_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✓ 反馈文件有效，包含 {len(data)} 条反馈")
            return True
        except Exception as e:
            print(f"✗ 反馈文件格式错误: {e}")
            return False
    return False

def check_input_files():
    """检查输入文件"""
    files_to_check = [
        'filter/upd_filter/ai_titles_v1_upd.txt',
        'filter/init_filter/ai_titles_v1.txt'
    ]
    
    for file_path in files_to_check:
        if check_file_exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = [line.strip() for line in f if line.strip()]
                print(f"  - 包含 {len(lines)} 个标题")
                if lines:
                    print(f"  - 示例标题: {lines[0]}")
            except Exception as e:
                print(f"  - 读取失败: {e}")

def test_simple_api_call():
    """测试简单的API调用"""
    try:
        import openai
        sys.path.append('backend')
        from config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL
        
        if DEEPSEEK_API_KEY == "your_deepseek_api_key_here":
            print("⚠️  API密钥未配置，跳过API测试")
            return False
            
        openai.api_key = DEEPSEEK_API_KEY
        openai.base_url = DEEPSEEK_API_URL
        
        print("🔍 测试API连接...")
        response = openai.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": "你好"}],
            max_tokens=10
        )
        print(f"✓ API调用成功: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"✗ API调用失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 AI过滤脚本调试工具")
    print("=" * 50)
    
    # 检查文件结构
    print("\n📁 检查文件结构:")
    check_file_exists('filter/upd_filter/ai_titles_ds_filter_upd.py')
    check_file_exists('backend/config.py')
    check_file_exists('backend/feedback.py')
    
    # 检查API配置
    print("\n🔑 检查API配置:")
    api_ok = check_api_config()
    
    # 检查反馈文件
    print("\n📊 检查反馈文件:")
    feedback_ok = check_feedback_file()
    
    # 检查输入文件
    print("\n📄 检查输入文件:")
    check_input_files()
    
    # 测试API调用
    print("\n🌐 测试API连接:")
    api_test_ok = test_simple_api_call()
    
    # 总结
    print("\n📋 诊断总结:")
    print(f"  API配置: {'✓' if api_ok else '✗'}")
    print(f"  反馈文件: {'✓' if feedback_ok else '✗'}")
    print(f"  API连接: {'✓' if api_test_ok else '✗'}")
    
    if not api_ok:
        print("\n💡 建议:")
        print("  1. 编辑 backend/config.py 文件")
        print("  2. 将 DEEPSEEK_API_KEY 设置为实际的API密钥")
        print("  3. 重新运行此脚本")
    
    if not api_test_ok and api_ok:
        print("\n💡 建议:")
        print("  1. 检查网络连接")
        print("  2. 验证API密钥是否有效")
        print("  3. 检查API配额是否充足")

if __name__ == "__main__":
    main() 