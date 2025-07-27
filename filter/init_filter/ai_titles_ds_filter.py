import openai
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import json
import random
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 从config文件获取API密钥
from backend.config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL

# 设置DeepSeek API Key
openai.api_key = DEEPSEEK_API_KEY
openai.base_url = DEEPSEEK_API_URL

def load_feedback_prompts():
    """加载反馈数据作为prompt"""
    # 获取当前文件所在目录，然后构建到backend/feedback.json的路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))  # 回到项目根目录
    feedback_file = os.path.join(project_root, 'backend', 'feedback.json')
    
    if not os.path.exists(feedback_file):
        return []
    
    try:
        with open(feedback_file, 'r', encoding='utf-8') as f:
            feedback_data = json.load(f)
        
        # 将反馈数据转换为prompt列表
        feedback_list = []
        for key, count in feedback_data.items():
            try:
                # 解析key格式: "标题""不可接受：反馈类型"
                first_quote = key.find('"', 1)
                second_quote = key.find('"', first_quote + 1)
                third_quote = key.find('"', second_quote + 1)
                
                if first_quote != -1 and second_quote != -1 and third_quote != -1:
                    title = key[1:first_quote]
                    feedback_type = key[third_quote + 1:-1]
                    feedback_list.append({
                        'title': title,
                        'feedback_type': feedback_type,
                        'count': count
                    })
            except:
                continue
        
        if not feedback_list:
            return []
        
        # 加权采样，最多5个
        count = min(5, len(feedback_list))
        if len(feedback_list) <= count:
            return [f"{item['title']} - {item['feedback_type']}" for item in feedback_list]
        
        # 加权随机采样
        total_weight = sum(item['count'] for item in feedback_list)
        selected_prompts = []
        
        for _ in range(count):
            if not feedback_list:
                break
            
            weights = [item['count'] / total_weight for item in feedback_list]
            selected = random.choices(feedback_list, weights=weights, k=1)[0]
            selected_prompts.append(f"{selected['title']} - {selected['feedback_type']}")
            
            feedback_list.remove(selected)
            total_weight -= selected['count']
        
        return selected_prompts
    except Exception as e:
        print(f"加载反馈数据失败: {e}")
        return [] 

# 读取AI相关标题
with open('filter/init_filter/ai_titles_v1.txt', 'r', encoding='utf-8') as f:
    titles = [line.strip() for line in f if line.strip()]

print(f"共读取到{len(titles)}个AI相关标题")

def is_acceptable(title):
    # 加载反馈数据作为system prompt
    feedback_prompts = load_feedback_prompts()
    
    system_prompt = "你是一个AI内容筛选助手。请根据用户反馈来改进筛选标准。"
    if feedback_prompts:
        system_prompt += "\n\n用户反馈示例：\n" + "\n".join(feedback_prompts)
        system_prompt += "\n\n请参考这些反馈来改进筛选标准。"
    
    user_prompt = (
        f"请判断以下标题是否浮夸或娱乐性太强：‘{title}’。\n"
        "如果是，返回0，否则返回1。\n"
        "如果该标题与AI无关，也返回0。\n"
        "例如：“当DeepSeek都认为“DeepSeek向王一博道歉”了” 提到了DeepSeek,所以它与AI相关，"
        "但是它提到了向王一博道歉，所以它娱乐性太强，所以返回应该为0。\n"
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    messages.append({"role": "user", "content": user_prompt})
    
    response = openai.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
    )
    content = response.choices[0].message.content.strip()
    last_line = content.strip().splitlines()[-1].strip()
    return last_line == "1"

results = []
with ThreadPoolExecutor(max_workers=5) as executor:  # 并发数可调整
    future_to_title = {executor.submit(is_acceptable, title): title for title in titles}
    for future in as_completed(future_to_title):
        title = future_to_title[future]
        try:
            if future.result():
                results.append(title)
                print(f"可接受标题: {title}")
            else:
                print(f"不可接受标题: {title}")
        except Exception as e:
            print(f"处理标题出错: {title}，错误: {e}")

with open('filter/init_filter/ai_titles_v2.txt', 'w', encoding='utf-8') as f:
    for title in results:
        f.write(title + '\n')
print(f"可接受AI标题已写入 filter/init_filter/ai_titles_v2.txt，共{len(results)}条") 