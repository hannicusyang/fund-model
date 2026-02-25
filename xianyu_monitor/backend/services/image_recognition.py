"""
图片识别服务
使用AI模型判断商品图片是否匹配目标商品
"""
import base64
import requests
from typing import List, Dict, Optional
import json
import os

class ImageRecognitionService:
    """图片识别服务"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4o"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model
    
    def compare_products(
        self, 
        target_image_url: str, 
        candidate_image_urls: List[str],
        target_description: str = ""
    ) -> List[Dict]:
        """
        比较目标商品图片与候选商品图片的相似度
        
        Args:
            target_image_url: 目标商品图片URL或base64
            candidate_image_urls: 候选商品图片列表
            target_description: 目标商品描述（如型号、规格等）
        
        Returns:
            匹配结果列表，每个包含 item_id, similarity, reason
        """
        results = []
        
        for idx, image_url in enumerate(candidate_image_urls):
            similarity, reason = self._compare_single(
                target_image_url, 
                image_url, 
                target_description
            )
            
            results.append({
                'index': idx,
                'image_url': image_url,
                'similarity': similarity,
                'reason': reason,
                'is_match': similarity >= 0.8
            })
        
        return results
    
    def _compare_single(
        self, 
        target_image: str, 
        candidate_image: str,
        description: str
    ) -> tuple:
        """比较单张图片"""
        # 这里使用OpenAI Vision API
        if not self.api_key:
            # 如果没有API key，返回默认的中等相似度
            return 0.5, "未配置API密钥，使用默认相似度"
        
        try:
            # 构建prompt
            prompt = f"""
请比较以下两张商品图片，判断它们是否是同款商品。

目标商品描述: {description}

请从以下角度分析:
1. 商品外观相似度
2. 品牌/型号是否一致
3. 颜色、尺寸是否匹配
4. 整体相似度评分 (0-100)

请返回JSON格式:
{{
    "similarity": 85,
    "reason": "分析原因"
}}
"""
            
            # 构建消息
            messages = [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {"url": target_image if target_image.startswith('http') else f"data:image/jpeg;base64,{target_image}"}
                },
                {
                    "type": "image_url", 
                    "image_url": {"url": candidate_image if candidate_image.startswith('http') else f"data:image/jpeg;base64,{candidate_image}"}
                }
            ]
            
            # 调用API
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": messages}],
                    "max_tokens": 300
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # 尝试解析JSON
                try:
                    data = json.loads(content)
                    similarity = data.get('similarity', 50) / 100
                    reason = data.get('reason', '')
                    return similarity, reason
                except:
                    return 0.5, content[:100]
            else:
                return 0.5, f"API错误: {response.status_code}"
                
        except Exception as e:
            return 0.5, f"比较失败: {str(e)}"
    
    def extract_product_info(self, image_url: str) -> Dict:
        """
        从图片中提取商品信息
        使用OCR + AI识别
        """
        if not self.api_key:
            return {"error": "未配置API密钥"}
        
        prompt = """
请分析这张商品图片，提取以下信息:
1. 商品类型/品类
2. 品牌
3. 型号
4. 颜色
5. 新旧程度（全新/99新/95新等）
6. 是否有包装
7. 其他显著特征

请返回JSON格式:
{
    "category": "手机",
    "brand": "Apple",
    "model": "iPhone 15 Pro",
    "color": "蓝色",
    "condition": "99新",
    "has_box": true,
    "other_features": "带原厂充电器"
}
"""
        
        try:
            messages = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": messages}],
                    "max_tokens": 500
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                return json.loads(content)
            else:
                return {"error": f"API错误: {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}


class SimpleImageComparator:
    """简单的图片比较器（基于URL/特征）"""
    
    def __init__(self):
        pass
    
    def compare(self, target_image: str, candidate_image: str) -> float:
        """简单的相似度比较"""
        # 如果图片URL完全相同
        if target_image == candidate_image:
            return 1.0
        
        # 尝试提取图片ID
        target_id = self._extract_image_id(target_image)
        candidate_id = self._extract_image_id(candidate_image)
        
        if target_id and candidate_id:
            # 如果ID部分匹配
            if target_id == candidate_id:
                return 0.95
            # 检查域名是否相同
            if self._extract_domain(target_image) == self._extract_domain(candidate_image):
                return 0.3
        
        return 0.1
    
    def _extract_image_id(self, url: str) -> str:
        """提取图片ID"""
        import re
        # 尝试匹配淘宝图片ID格式
        match = re.search(r'/([a-zA-Z0-9_]+)\.(jpg|png|jpeg)', url)
        return match.group(1) if match else ""
    
    def _extract_domain(self, url: str) -> str:
        """提取域名"""
        import re
        match = re.search(r'https?://([^/]+)', url)
        return match.group(1) if match else ""


def create_recognition_service(api_key: str = None) -> ImageRecognitionService:
    """创建识别服务实例"""
    return ImageRecognitionService(api_key)


if __name__ == "__main__":
    # 测试
    service = ImageRecognitionService()
    results = service.compare_products(
        "https://example.com/target.jpg",
        ["https://example.com/candidate1.jpg", "https://example.com/candidate2.jpg"],
        "iPhone 15 Pro Max 256G"
    )
    print(json.dumps(results, indent=2, ensure_ascii=False))
