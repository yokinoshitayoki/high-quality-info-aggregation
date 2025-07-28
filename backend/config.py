import os

# DeepSeek API配置
DEEPSEEK_API_KEY = os.getenv("OPENAI_API_KEY")
print(DEEPSEEK_API_KEY)
if DEEPSEEK_API_KEY is None:
    raise ValueError("环境变量 OPENAI_API_KEY 未设置，请检查。")
DEEPSEEK_API_URL = "https://api.deepseek.com"

# 其他配置
MAX_CONTENT_LENGTH = 1000  # 发送给API的最大内容长度
MAX_TOKENS = 100  # 生成摘要的最大token数
TEMPERATURE = 0.7  # 生成温度 
