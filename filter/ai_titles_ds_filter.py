import openai
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
# 设置DeepSeek API Key
openai.api_key = os.getenv("OPENAI_API_KEY")
if openai.api_key is None:
    raise ValueError("环境变量 OPENAI_API_KEY 未设置，请检查。")
openai.base_url = "https://api.deepseek.com" 

# 读取AI相关标题
with open('filter/ai_titles_v1.txt', 'r', encoding='utf-8') as f:
    titles = [line.strip() for line in f if line.strip()]

print(f"共读取到{len(titles)}个AI相关标题")

def is_acceptable(title):
    prompt = (
        f"请判断以下标题是否浮夸或言之无物：‘{title}’。\n"
        "如果是，返回0，否则返回1。\n"
        "如果该标题与AI无关，也返回0。\n"
        "请注意不要返回其它任何值。"
    )
    response = openai.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
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

with open('filter/ai_titles_v2.txt', 'w', encoding='utf-8') as f:
    for title in results:
        f.write(title + '\n')
print(f"可接受AI标题已写入 filter/ai_titles_v2.txt，共{len(results)}条") 