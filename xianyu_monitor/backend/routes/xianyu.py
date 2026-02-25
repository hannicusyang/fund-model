"""
闲鱼监控系统 - API路由
"""
from flask import Blueprint, jsonify, request
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.database import (
    init_db,
    add_monitored_product,
    get_monitored_products,
    update_monitored_product,
    delete_monitored_product,
    get_search_results,
    get_bookmarked_items,
    bookmark_item,
    get_price_history,
    get_lowest_price,
    get_pending_notifications,
    mark_notification_sent
)
from backend.services.monitor import get_monitor_service, run_monitor_task

# 创建蓝图
api = Blueprint('api', __name__, url_prefix='/api/xianyu')

# 初始化数据库
init_db()


# ==================== 监控商品管理 ====================

@api.route('/products', methods=['GET'])
def get_products():
    """获取监控商品列表"""
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    products = get_monitored_products(active_only=active_only)
    return jsonify({
        'code': 0,
        'data': products
    })


@api.route('/products', methods=['POST'])
def create_product():
    """添加监控商品"""
    data = request.json
    
    product_id = add_monitored_product(
        name=data.get('name'),
        keywords=data.get('keywords'),
        target_price=data.get('target_price'),
        max_price=data.get('max_price'),
        min_discount_rate=data.get('min_discount_rate', 0.7),
        image_url=data.get('image_url'),
        image_base64=data.get('image_base64'),
        notify_email=data.get('notify_email', 1),
        notify_feishu=data.get('notify_feishu', 0),
        auto_buy_enabled=data.get('auto_buy_enabled', 0),
        locked=data.get('locked', 0),
        notes=data.get('notes', '')
    )
    
    return jsonify({
        'code': 0,
        'message': '添加成功',
        'data': {'id': product_id}
    })


@api.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """更新监控商品"""
    data = request.json
    
    # 允许更新的字段
    allowed_fields = [
        'name', 'keywords', 'target_price', 'max_price', 'min_discount_rate',
        'image_url', 'image_base64', 'is_active', 'notify_email', 'notify_feishu',
        'auto_buy_enabled', 'locked', 'notes'
    ]
    
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    
    if update_data:
        update_monitored_product(product_id, **update_data)
    
    return jsonify({
        'code': 0,
        'message': '更新成功'
    })


@api.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """删除监控商品"""
    delete_monitored_product(product_id)
    return jsonify({
        'code': 0,
        'message': '删除成功'
    })


@api.route('/products/<int:product_id>/toggle', methods=['POST'])
def toggle_product(product_id):
    """启用/禁用监控"""
    products = get_monitored_products(active_only=False)
    product = next((p for p in products if p['id'] == product_id), None)
    
    if product:
        update_monitored_product(product_id, is_active=not product['is_active'])
        return jsonify({
            'code': 0,
            'message': f"已{'禁用' if product['is_active'] else '启用'}"
        })
    
    return jsonify({
        'code': 404,
        'message': '商品不存在'
    })


# ==================== 商品搜索 ====================

@api.route('/search/<int:product_id>', methods=['GET'])
def search_product(product_id):
    """搜索并检查商品"""
    products = get_monitored_products()
    product = next((p for p in products if p['id'] == product_id), None)
    
    if not product:
        return jsonify({
            'code': 404,
            'message': '商品不存在'
        })
    
    # 运行检查
    service = get_monitor_service()
    matched = service.check_product(product, force_image_check=True)
    
    return jsonify({
        'code': 0,
        'data': {
            'product': product,
            'matched_items': matched,
            'total_searched': 20
        }
    })


@api.route('/search-all', methods=['POST'])
def search_all():
    """检查所有监控商品"""
    force_image = request.json.get('force_image_check', False) if request.json else False
    results = run_monitor_task(force_image_check=force_image)
    
    return jsonify({
        'code': 0,
        'data': results
    })


# ==================== 搜索结果 ====================

@api.route('/results/<int:product_id>', methods=['GET'])
def get_results(product_id):
    """获取搜索结果"""
    limit = request.args.get('limit', 50, type=int)
    results = get_search_results(product_id, limit=limit)
    
    return jsonify({
        'code': 0,
        'data': results
    })


@api.route('/results/bookmarked', methods=['GET'])
def get_bookmarked():
    """获取收藏的商品"""
    product_id = request.args.get('product_id', type=int)
    items = get_bookmarked_items(product_id)
    
    return jsonify({
        'code': 0,
        'data': items
    })


@api.route('/results/<int:item_id>/bookmark', methods=['POST'])
def bookmark_result(item_id):
    """收藏商品"""
    bookmark = request.json.get('bookmark', True) if request.json else True
    bookmark_item(item_id, bookmark)
    
    return jsonify({
        'code': 0,
        'message': '操作成功'
    })


# ==================== 价格历史 ====================

@api.route('/price-history/<item_id>', methods=['GET'])
def price_history(item_id):
    """获取价格历史"""
    days = request.args.get('days', 30, type=int)
    history = get_price_history(item_id, days)
    lowest = get_lowest_price(item_id, days)
    
    return jsonify({
        'code': 0,
        'data': {
            'history': history,
            'lowest_price': lowest
        }
    })


# ==================== 通知 ====================

@api.route('/notifications', methods=['GET'])
def get_notifications():
    """获取待发送的通知"""
    notifications = get_pending_notifications()
    
    return jsonify({
        'code': 0,
        'data': notifications
    })


@api.route('/notifications/<int:notification_id>/send', methods=['POST'])
def send_notification(notification_id):
    """标记通知已发送"""
    mark_notification_sent(notification_id)
    
    return jsonify({
        'code': 0,
        'message': '已标记'
    })


# ==================== 系统状态 ====================

@api.route('/status', methods=['GET'])
def get_status():
    """获取系统状态"""
    products = get_monitored_products()
    active_products = [p for p in products if p.get('is_active')]
    bookmarked = get_bookmarked_items()
    
    return jsonify({
        'code': 0,
        'data': {
            'total_products': len(products),
            'active_products': len(active_products),
            'bookmarked_items': len(bookmarked),
            'monitor_running': True
        }
    })


def register_routes(app):
    """注册路由到Flask应用"""
    app.register_blueprint(api)
