"""
闲鱼监控核心服务
定时检查商品并发送通知
"""
import time
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import threading
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.database import (
    get_monitored_products, 
    save_search_results, 
    get_search_results,
    add_notification,
    get_pending_notifications,
    mark_notification_sent,
    add_purchase_log,
    get_lowest_price,
    get_bookmarked_items,
    update_monitored_product
)
from backend.services.xianyu_spider import create_spider
from backend.services.image_recognition import create_recognition_service
from backend.services.notification import create_email_service, create_feishu_service


class MonitorService:
    """监控服务核心类"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.spider = create_spider(use_mock=True)  # 默认使用模拟数据
        self.recognition = create_recognition_service()
        self.email_service = create_email_service()
        self.feishu_service = create_feishu_service()
        self.is_running = False
    
    def check_product(self, product: dict, force_image_check: bool = False) -> List[Dict]:
        """
        检查单个商品
        
        Args:
            product: 监控商品配置
            force_image_check: 是否强制进行图片匹配
        
        Returns:
            符合条件的商品列表
        """
        keywords = product['keywords']
        target_price = product.get('target_price')
        max_price = product.get('max_price')
        min_discount_rate = product.get('min_discount_rate', 0.7)
        image_url = product.get('image_url')
        
        # 搜索商品
        items = self.spider.search_items(keywords, page_size=20)
        
        if not items:
            return []
        
        # 保存搜索结果
        save_search_results(product['id'], items)
        
        # 筛选符合条件的商品
        matched_items = []
        
        for item in items:
            # 价格筛选
            price = item.get('price', 0)
            original_price = item.get('original_price', price)
            
            # 计算折扣率
            discount_rate = price / original_price if original_price > 0 else 1
            
            # 价格条件判断
            price_ok = True
            if max_price and price > max_price:
                price_ok = False
            
            # 好价判断
            is_good_price = discount_rate <= min_discount_rate
            
            # 图片匹配判断
            image_match = True
            match_reason = ""
            
            if force_image_check and image_url:
                # 进行图片识别
                item_images = item.get('images', [])
                if item_images:
                    results = self.recognition.compare_products(
                        image_url, 
                        item_images,
                        keywords
                    )
                    if results:
                        best_match = max(results, key=lambda x: x['similarity'])
                        image_match = best_match['is_match']
                        match_reason = best_match.get('reason', '')
            
            # 综合判断
            if price_ok and (is_good_price or image_match):
                item['is_good_price'] = is_good_price
                item['discount_rate'] = discount_rate
                item['image_match'] = image_match
                item['match_reason'] = match_reason
                item['product_id'] = product['id']
                matched_items.append(item)
        
        return matched_items
    
    def check_all_products(self, force_image_check: bool = False) -> Dict:
        """检查所有监控商品"""
        products = get_monitored_products(active_only=True)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'products_checked': len(products),
            'alerts': []
        }
        
        for product in products:
            try:
                matched = self.check_product(product, force_image_check)
                
                if matched:
                    # 对每个匹配商品发送通知
                    for item in matched:
                        alert = self._create_alert(product, item)
                        results['alerts'].append(alert)
                        
                        # 发送通知
                        self._send_notifications(product, item, alert)
                        
                        # 检查是否需要自动拍下
                        if product.get('auto_buy_enabled'):
                            self._try_auto_buy(product, item)
                
                print(f"检查 {product['name']}: 找到 {len(matched)} 个匹配商品")
                
            except Exception as e:
                print(f"检查 {product['name']} 出错: {e}")
        
        return results
    
    def _create_alert(self, product: dict, item: dict) -> dict:
        """创建告警信息"""
        alert = {
            'product_id': product['id'],
            'product_name': product['name'],
            'item_id': item.get('item_id'),
            'item_title': item.get('title'),
            'price': item.get('price'),
            'original_price': item.get('original_price'),
            'discount_rate': item.get('discount_rate'),
            'url': item.get('url'),
            'is_good_price': item.get('is_good_price', False),
            'image_match': item.get('image_match', False),
            'match_reason': item.get('match_reason', ''),
            'alert_type': []
        }
        
        if alert['is_good_price']:
            alert['alert_type'].append('好价')
        if alert['image_match']:
            alert['alert_type'].append('图片匹配')
        
        return alert
    
    def _send_notifications(self, product: dict, item: dict, alert: dict):
        """发送通知"""
        product_id = product['id']
        item_id = item.get('item_id', '')
        
        # 确定通知类型
        if alert['is_good_price']:
            notify_type = "price_alert"
            message = f"{product['name']} 好价: ¥{item['price']}"
        elif alert['image_match']:
            notify_type = "image_match"
            message = f"{product['name']} 找到匹配商品"
        else:
            return
        
        # 记录通知
        add_notification(product_id, item_id, notify_type, message)
        
        # 发送邮件
        if product.get('notify_email'):
            if alert['is_good_price']:
                self.email_service.send_price_alert(product['name'], item, "price_drop")
            elif alert['image_match']:
                self.email_service.send_matched_product_alert(
                    product['name'], 
                    item, 
                    alert.get('match_reason', '')
                )
        
        # 发送飞书通知
        if product.get('notify_feishu'):
            self._send_feishu_notification(product, item, alert)
    
    def _send_feishu_notification(self, product: dict, item: dict, alert: dict):
        """发送飞书通知"""
        message = f"""
🎉 {product['name']} 监控提醒

商品: {item['title']}
价格: ¥{item['price']} ({(item.get('discount_rate', 1)*100):.0f}%折)
卖家: {item.get('seller_nick', 'N/A')}
地点: {item.get('location', 'N/A')}

类型: {', '.join(alert['alert_type'])}

链接: {item.get('url', '')}
"""
        self.feishu_service.send(message)
    
    def _try_auto_buy(self, product: dict, item: dict):
        """
        尝试自动拍下商品
        注意: 闲鱼有验证码机制，此功能需要配合滑块验证码识别
        """
        # 记录尝试
        add_purchase_log(
            product['id'],
            item.get('item_id'),
            "auto_buy_attempt",
            f"尝试自动拍下: {item.get('title')}"
        )
        
        # TODO: 实现自动拍下逻辑
        # 需要处理:
        # 1. 登录验证
        # 2. 滑块验证码
        # 3. 支付流程
        
        print(f"自动拍下功能待实现: {item.get('title')}")
    
    def get_matched_items(self, product_id: int = None, min_discount: float = None) -> List[Dict]:
        """获取匹配的商品"""
        if product_id:
            items = get_search_results(product_id)
        else:
            items = get_bookmarked_items()
        
        # 过滤
        filtered = []
        for item in items:
            if item.get('is_bookmarked'):
                filtered.append(item)
                continue
            
            discount = item.get('price', 0) / item.get('original_price', item.get('price', 1))
            if min_discount and discount > min_discount:
                continue
            
            filtered.append(item)
        
        return filtered
    
    def lock_product(self, item_id: str, lock: bool = True):
        """锁定/解锁商品"""
        # 更新数据库
        from backend.models.database import get_db
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE search_results SET is_bookmarked = ? WHERE item_id = ?",
            (1 if lock else 0, item_id)
        )
        conn.commit()
        conn.close()


# 全局监控实例
_monitor_service = None

def get_monitor_service(config: dict = None) -> MonitorService:
    """获取监控服务实例"""
    global _monitor_service
    if _monitor_service is None:
        _monitor_service = MonitorService(config)
    return _monitor_service


def run_monitor_task(force_image_check: bool = False):
    """运行监控任务"""
    service = get_monitor_service()
    results = service.check_all_products(force_image_check)
    return results


if __name__ == "__main__":
    # 测试
    from backend.models.database import init_db, add_monitored_product
    
    # 初始化数据库
    init_db()
    
    # 添加测试商品
    product_id = add_monitored_product(
        name="iPhone 15 Pro Max",
        keywords="iPhone 15 Pro Max",
        target_price=8000,
        max_price=9000,
        min_discount_rate=0.8,
        notify_email=1
    )
    print(f"添加监控商品，ID: {product_id}")
    
    # 运行监控
    results = run_monitor_task()
    print(f"监控结果: {json.dumps(results, indent=2, ensure_ascii=False)}")
