from sentence_transformers import SentenceTransformer, util

# 读取scrapy/all_data/all_titles.txt中的标题
with open('scrapy/all_data/all_titles_upd.txt', 'r', encoding='utf-8') as f:
    titles = [line.strip() for line in f if line.strip()]

print(f"共读取到{len(titles)}个标题")

def filter_ai_titles(titles, threshold=0.3):
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    ai_keywords = ["人工智能", "AI", "大模型", "深度学习","机器人","多模态","AI Agent","OpenAI","ChatGPT","AGI"]
    ai_vec = model.encode(ai_keywords, convert_to_tensor=True)
    filtered = []
    for title in titles:
        title_vec = model.encode(title, convert_to_tensor=True)
        sim = util.cos_sim(title_vec, ai_vec).max().item()
        if sim > threshold:
            filtered.append((title, sim))
    return filtered

filtered_titles = filter_ai_titles(titles, threshold=0.3)
print("与人工智能相关的标题：")
for title, sim in filtered_titles:
    print(f"{title}（相似度：{sim:.2f}）")

# 写入到新文件（只保留标题）
with open('filter/upd_filter/ai_titles_v1_upd.txt', 'w', encoding='utf-8') as f:
    for title, sim in filtered_titles:
        f.write(f"{title}\n")
print("筛选后的AI相关标题已写入") 