"""
闲鱼监控系统 - 数据库模型
"""
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict
import json

DB_PATH = "/home/clawdbot/.openclaw/workspace/xianyu_monitor/data/xianyu.db"

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库表"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 监控商品表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monitored_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            keywords TEXT NOT NULL,
            target_price REAL,
            max_price REAL,
            min_discount_rate REAL DEFAULT 0.7,
            image_url TEXT,
            image_base64 TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            notify_email BOOLEAN DEFAULT 1,
            notify_feishu BOOLEAN DEFAULT 0,
            auto_buy_enabled BOOLEAN DEFAULT 0,
            locked BOOLEAN DEFAULT 0,
            notes TEXT
        )
    """)
    
    # 搜索结果表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            item_id TEXT UNIQUE,
            title TEXT,
            price REAL,
            original_price REAL,
            location TEXT,
            seller_nick TEXT,
            seller_credit INTEGER,
            images TEXT,
            url TEXT,
            posted_time TIMESTAMP,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_bookmarked BOOLEAN DEFAULT 0,
            is_filtered BOOLEAN DEFAULT 0,
            filter_reason TEXT,
            FOREIGN KEY (product_id) REFERENCES monitored_products(id)
        )
    """)
    
    # 价格历史表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id TEXT NOT NULL,
            price REAL NOT NULL,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 通知记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            item_id TEXT,
            notify_type TEXT,
            message TEXT,
            is_sent BOOLEAN DEFAULT 0,
            sent_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES monitored_products(id)
        )
    """)
    
    # 拍下记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            item_id TEXT,
            action TEXT,
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES monitored_products(id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("数据库初始化完成")

# ==================== 监控商品操作 ====================

def add_monitored_product(
    name: str, 
    keywords: str, 
    target_price: float = None,
    max_price: float = None,
    min_discount_rate: float = 0.7,
    image_url: str = None,
    image_base64: str = None,
    **kwargs
) -> int:
    """添加监控商品"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO monitored_products 
        (name, keywords, target_price, max_price, min_discount_rate, image_url, image_base64, 
         notify_email, notify_feishu, auto_buy_enabled, locked, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, keywords, target_price, max_price, min_discount_rate, image_url, image_base64,
          kwargs.get('notify_email', 1), kwargs.get('notify_feishu', 0), 
          kwargs.get('auto_buy_enabled', 0), kwargs.get('locked', 0), kwargs.get('notes', '')))
    conn.commit()
    product_id = cursor.lastrowid
    conn.close()
    return product_id

def get_monitored_products(active_only: bool = True) -> List[Dict]:
    """获取监控商品列表"""
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT * FROM monitored_products"
    if active_only:
        query += " WHERE is_active = 1"
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_monitored_product(product_id: int, **kwargs):
    """更新监控商品"""
    conn = get_db()
    cursor = conn.cursor()
    fields = ', '.join(f"{k} = ?" for k in kwargs.keys())
    cursor.execute(f"UPDATE monitored_products SET {fields} WHERE id = ?", 
                   list(kwargs.values()) + [product_id])
    conn.commit()
    conn.close()

def delete_monitored_product(product_id: int):
    """删除监控商品"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM monitored_products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

# ==================== 搜索结果操作 ====================

def save_search_results(product_id: int, results: List[Dict]):
    """保存搜索结果"""
    conn = get_db()
    cursor = conn.cursor()
    for item in results:
        cursor.execute("""
            INSERT OR REPLACE INTO search_results 
            (product_id, item_id, title, price, original_price, location, seller_nick, 
             seller_credit, images, url, posted_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (product_id, item.get('item_id'), item.get('title'), item.get('price'),
              item.get('original_price'), item.get('location'), item.get('seller_nick'),
              item.get('seller_credit'), json.dumps(item.get('images')), 
              item.get('url'), item.get('posted_time')))
        
        # 记录价格历史
        cursor.execute("""
            INSERT INTO price_history (item_id, price) VALUES (?, ?)
        """, (item.get('item_id'), item.get('price')))
    conn.commit()
    conn.close()

def get_search_results(product_id: int, limit: int = 50) -> List[Dict]:
    """获取搜索结果"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM search_results 
        WHERE product_id = ? 
        ORDER BY scraped_at DESC LIMIT ?
    """, (product_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_bookmarked_items(product_id: int = None) -> List[Dict]:
    """获取收藏的商品"""
    conn = get_db()
    cursor = conn.cursor()
    if product_id:
        cursor.execute("""
            SELECT * FROM search_results 
            WHERE is_bookmarked = 1 AND product_id = ?
            ORDER BY scraped_at DESC
        """, (product_id,))
    else:
        cursor.execute("""
            SELECT * FROM search_results 
            WHERE is_bookmarked = 1 
            ORDER BY scraped_at DESC
        """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def bookmark_item(item_id: int, bookmarked: bool = True):
    """收藏/取消收藏商品"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE search_results SET is_bookmarked = ? WHERE id = ?", 
                   (1 if bookmarked else 0, item_id))
    conn.commit()
    conn.close()

def mark_item_filtered(item_id: int, reason: str):
    """标记商品被过滤"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE search_results SET is_filtered = 1, filter_reason = ? WHERE id = ?", 
                   (reason, item_id))
    conn.commit()
    conn.close()

# ==================== 价格历史操作 ====================

def get_price_history(item_id: str, days: int = 30) -> List[Dict]:
    """获取商品价格历史"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM price_history 
        WHERE item_id = ? AND recorded_at >= datetime('now', '-' || ? || ' days')
        ORDER BY recorded_at ASC
    """, (item_id, days))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_lowest_price(item_id: str, days: int = 90) -> float:
    """获取商品最低价"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT MIN(price) as lowest FROM price_history 
        WHERE item_id = ? AND recorded_at >= datetime('now', '-' || ? || ' days')
    """, (item_id, days))
    result = cursor.fetchone()
    conn.close()
    return result['lowest'] if result else None

# ==================== 通知操作 ====================

def add_notification(product_id: int, item_id: str, notify_type: str, message: str):
    """添加通知记录"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO notifications (product_id, item_id, notify_type, message)
        VALUES (?, ?, ?, ?)
    """, (product_id, item_id, notify_type, message))
    conn.commit()
    conn.close()

def get_pending_notifications() -> List[Dict]:
    """获取待发送的通知"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT n.*, mp.name as product_name, mp.keywords
        FROM notifications n
        JOIN monitored_products mp ON n.product_id = mp.id
        WHERE n.is_sent = 0
        ORDER BY n.created_at ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def mark_notification_sent(notification_id: int):
    """标记通知已发送"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE notifications SET is_sent = 1, sent_at = CURRENT_TIMESTAMP 
        WHERE id = ?
    """, (notification_id,))
    conn.commit()
    conn.close()

# ==================== 拍下日志 ====================

def add_purchase_log(product_id: int, item_id: str, action: str, result: str):
    """添加拍下日志"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO purchase_logs (product_id, item_id, action, result)
        VALUES (?, ?, ?, ?)
    """, (product_id, item_id, action, result))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    import os
    os.makedirs("/home/clawdbot/.openclaw/workspace/xianyu_monitor/data", exist_ok=True)
    init_db()
