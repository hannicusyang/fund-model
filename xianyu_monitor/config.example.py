#闲鱼监控系统配置文件
#复制此文件为config.py并填入真实配置

#闲鱼登录Cookie (从浏览器获取)
XIANYU_COOKIE = ""

#淘宝登录Cookie (用于闲鱼一些需要登录的接口)
TAOBAO_COOKIE = ""

#邮件配置
MAIL_CONFIG = {
    "smtp_host": "smtp.qq.com",
    "smtp_port": 465,
    "smtp_user": "your_email@qq.com",
    "smtp_password": "your_auth_code",  # QQ邮箱授权码
    "from_email": "your_email@qq.com",
    "to_emails": ["target_email@example.com"]
}

#监控配置
MONITOR_CONFIG = {
    "check_interval_minutes": 30,  # 检查间隔
    "max_search_results": 50,       # 每次搜索最大结果数
    "price_history_days": 90,       # 价格历史保留天数
    "min_discount_rate": 0.7,      # 默认7折以下为好价
}

#图片识别配置
IMAGE_CONFIG = {
    "similarity_threshold": 0.85,  # 图片相似度阈值
    "model": "gpt-4o"              # 用于商品图片对比的模型
}

#自动拍下配置
AUTO_BUY_CONFIG = {
    "enabled": False,              # 默认关闭
    "max_price_ratio": 0.8,        # 最高议价比例
    "auto_message": "你好，我对你的商品很感兴趣，请确认是否可以发货",  # 自动发送的消息
}
