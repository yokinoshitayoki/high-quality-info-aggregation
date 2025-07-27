import json
import os
from collections import defaultdict

class FeedbackManager:
    def __init__(self, feedback_file='feedback.json'):
        # 确保反馈文件始终在backend目录下
        if not os.path.isabs(feedback_file):
            # 获取当前文件所在目录（backend目录）
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.feedback_file = os.path.join(current_dir, feedback_file)
        else:
            self.feedback_file = feedback_file
        self.feedback_data = self._load_feedback()
    
    def _load_feedback(self):
        """加载反馈数据"""
        if os.path.exists(self.feedback_file):
            try:
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_feedback(self):
        """保存反馈数据"""
        with open(self.feedback_file, 'w', encoding='utf-8') as f:
            json.dump(self.feedback_data, f, ensure_ascii=False, indent=2)
    
    def add_feedback(self, title, feedback_type):
        """添加反馈"""
        key = f'"{title}""不可接受：{feedback_type}"'
        if key in self.feedback_data:
            self.feedback_data[key] += 1
        else:
            self.feedback_data[key] = 1
        self._save_feedback()
        return self.feedback_data[key]
    
    def get_feedback_stats(self):
        """获取反馈统计"""
        return self.feedback_data
    
    def get_weighted_prompts(self, count=5):
        """获取加权采样的prompt列表"""
        if not self.feedback_data:
            return []
        
        # 将反馈数据转换为列表，包含标题、反馈类型和次数
        feedback_list = []
        for key, count in self.feedback_data.items():
            # 解析key格式: "标题""不可接受：反馈类型"
            try:
                # 找到第一个和第二个引号的位置
                first_quote = key.find('"', 1)
                second_quote = key.find('"', first_quote + 1)
                third_quote = key.find('"', second_quote + 1)
                
                if first_quote != -1 and second_quote != -1 and third_quote != -1:
                    title = key[1:first_quote]
                    feedback_type = key[third_quote + 1:-1]  # 去掉最后的引号
                    feedback_list.append({
                        'title': title,
                        'feedback_type': feedback_type,
                        'count': count
                    })
            except:
                continue
        
        if not feedback_list:
            return []
        
        # 如果反馈数量不超过要求数量，返回全部
        if len(feedback_list) <= count:
            return [f"{item['title']} - {item['feedback_type']}" for item in feedback_list]
        
        # 加权采样，对"无理由"反馈降低权重
        selected_prompts = []
        import random
        
        for _ in range(count):
            if not feedback_list:
                break
            
            # 计算权重，对"无理由"反馈降低权重
            weights = []
            for item in feedback_list:
                base_weight = item['count']
                # 如果是"无理由"反馈，权重降低到原来的1/3
                if item['feedback_type'] == '无理由':
                    adjusted_weight = base_weight / 3
                else:
                    adjusted_weight = base_weight
                weights.append(adjusted_weight)
            
            total_weight = sum(weights)
            if total_weight == 0:
                break
                
            # 归一化权重
            normalized_weights = [w / total_weight for w in weights]
            
            # 随机选择
            selected = random.choices(feedback_list, weights=normalized_weights, k=1)[0]
            selected_prompts.append(f"{selected['title']} - {selected['feedback_type']}")
            
            # 从列表中移除已选择的项目
            feedback_list.remove(selected)
        
        return selected_prompts

# 全局反馈管理器实例
feedback_manager = FeedbackManager() 