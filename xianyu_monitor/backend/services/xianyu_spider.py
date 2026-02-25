"""
闲鱼API爬虫服务
基于闲鱼H5接口实现商品搜索
"""
import requests
import json
import hashlib
import time
import re
from typing import List, Dict, Optional
from urllib.parse import quote

class XianyuSpider:
    """闲鱼爬虫类"""
    
    BASE_URL = "https://gw-xianyu.m.goofish.com"
    
    def __init__(self, cookie: str = None):
        self.session = requests.Session()
        self.cookie = cookie or ""
        self._setup_headers()
    
    def _setup_headers(self):
        """设置请求头"""
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.0(0x18000000) NetType/WIFI Language/zh_CN",
            "Referer": "https://market.m.taobao.com/",
            "Accept": "application/json",
        })
        if self.cookie:
            self.session.headers.update({"Cookie": self.cookie})
    
    def search_items(self, keywords: str, page: int = 1, page_size: int = 20) -> List[Dict]:
        """
        搜索闲鱼商品
        """
        try:
            # 闲鱼搜索接口（需要根据实际接口调整）
            url = f"{self.BASE_URL}/gwu/xianyu/h5/mtop.taobao.idlemsearch.search"
            
            params = {
                "keyword": keywords,
                "pageNo": page,
                "pageSize": page_size,
                "sort": "default",  # default, price_asc, price_desc, time_desc
            }
            
            # 尝试使用淘宝/闲鱼H5搜索接口
            search_url = "https://s.goofish.com/search/q"
            
            response = self.session.get(search_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_search_results(data)
            else:
                print(f"搜索失败: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"搜索出错: {e}")
            return []
    
    def _parse_search_results(self, data: dict) -> List[Dict]:
        """解析搜索结果"""
        results = []
        try:
            # 尝试解析不同的响应格式
            items = []
            if isinstance(data, dict):
                # 尝试找items数组
                items = data.get('data', {}).get('result', []) or data.get('items', [])
            
            for item in items:
                parsed = self._parse_item(item)
                if parsed:
                    results.append(parsed)
        except Exception as e:
            print(f"解析结果出错: {e}")
        
        return results
    
    def _parse_item(self, item: dict) -> Optional[Dict]:
        """解析单个商品"""
        try:
            return {
                'item_id': item.get('itemId') or item.get('item_id') or item.get('id', ''),
                'title': item.get('title') or item.get('itemName', ''),
                'price': float(item.get('price') or item.get('salePrice', 0)),
                'original_price': float(item.get('originalPrice') or item.get('price', 0)),
                'location': item.get('location') or item.get('province', ''),
                'seller_nick': item.get('nick') or item.get('sellerNick', ''),
                'seller_credit': item.get('credit') or item.get('sellerCredit', 0),
                'images': [item.get('image') or item.get('picUrl', '')],
                'url': f"https://2.taobao.com/item.htm?id={item.get('itemId') or item.get('item_id', '')}",
                'posted_time': item.get('postTime') or item.get('createTime', ''),
            }
        except Exception as e:
            return None
    
    def get_item_detail(self, item_id: str) -> Optional[Dict]:
        """获取商品详情"""
        try:
            url = f"https://item.taobao.com/item.htm?id={item_id}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                # 尝试从页面提取信息
                html = response.text
                
                # 提取价格
                price_match = re.search(r'"price":"?([\d.]+)"?', html)
                price = float(price_match.group(1)) if price_match else 0
                
                # 提取标题
                title_match = re.search(r'<title>([^<]+)</title>', html)
                title = title_match.group(1) if title_match else ""
                
                return {
                    'item_id': item_id,
                    'title': title,
                    'price': price,
                    'detail_url': url,
                }
        except Exception as e:
            print(f"获取详情失败: {e}")
        
        return None


class MockXianyuSpider(XianyuSpider):
    """模拟闲鱼爬虫（用于测试）"""
    
    MOCK_PRODUCTS = [
        {
            'item_id': '1',
            'title': 'iPhone 15 Pro Max 256G 蓝色 全新未拆封',
            'price': 7999.0,
            'original_price': 9999.0,
            'location': '深圳',
            'seller_nick': '数码玩家88',
            'seller_credit': 650,
            'images': ['https://img.alicdn.com/tao/i1/O1CN01xxx1.jpg'],
            'url': 'https://2.taobao.com/item.htm?id=1',
            'posted_time': '2小时前'
        },
        {
            'item_id': '2',
            'title': 'iPhone 15 Pro 128G 钛金属 99新',
            'price': 6200.0,
            'original_price': 7999.0,
            'location': '广州',
            'seller_nick': '诚信数码商',
            'seller_credit': 720,
            'images': ['https://img.alicdn.com/tao/i2/O1CN01xxx2.jpg'],
            'url': 'https://2.taobao.com/item.htm?id=2',
            'posted_time': '5小时前'
        },
        {
            'item_id': '3',
            'title': 'iPhone 15 Pro Max 256G 白色 95新 带盒子',
            'price': 7500.0,
            'original_price': 9999.0,
            'location': '北京',
            'seller_nick': '果粉之家',
            'seller_credit': 580,
            'images': ['https://img.alicdn.com/tao/i3/O1CN01xxx3.jpg'],
            'url': 'https://2.taobao.com/item.htm?id=3',
            'posted_time': '1天前'
        },
        {
            'item_id': '4',
            'title': 'iPhone 14 Pro 256G 暗紫色 98新',
            'price': 4800.0,
            'original_price': 6999.0,
            'location': '上海',
            'seller_nick': '二手优品',
            'seller_credit': 800,
            'images': ['https://img.alicdn.com/tao/i4/O1CN01xxx4.jpg'],
            'url': 'https://2.taobao.com/item.htm?id=4',
            'posted_time': '3天前'
        },
        {
            'item_id': '5',
            'title': 'iPhone 15 128G 蓝色 全新未拆封',
            'price': 5200.0,
            'original_price': 5999.0,
            'location': '杭州',
            'seller_nick': 'Apple专营店',
            'seller_credit': 900,
            'images': ['https://img.alicdn.com/tao/i5/O1CN01xxx5.jpg'],
            'url': 'https://2.taobao.com/item.htm?id=5',
            'posted_time': '6小时前'
        },
    ]
    
    def search_items(self, keywords: str, page: int = 1, page_size: int = 20) -> List[Dict]:
        """模拟搜索"""
        # 简单的关键词匹配模拟
        keywords_lower = keywords.lower()
        results = []
        
        for product in self.MOCK_PRODUCTS:
            if keywords_lower in product['title'].lower():
                # 模拟价格波动
                import random
                product_copy = product.copy()
                product_copy['price'] = product_copy['price'] * random.uniform(0.9, 1.1)
                results.append(product_copy)
        
        # 模拟分页
        start = (page - 1) * page_size
        end = start + page_size
        
        return results[start:end]


def create_spider(cookie: str = None, use_mock: bool = True) -> XianyuSpider:
    """创建爬虫实例"""
    if use_mock:
        return MockXianyuSpider(cookie)
    return XianyuSpider(cookie)


if __name__ == "__main__":
    # 测试
    spider = create_spider(use_mock=True)
    results = spider.search_items("iPhone 15")
    for item in results:
        print(f"{item['title']} - ¥{item['price']}")
