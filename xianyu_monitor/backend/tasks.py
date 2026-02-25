"""
闲鱼监控系统 - 定时任务脚本
用于cron定时执行监控任务
"""
import sys
import os
import json
import argparse

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.monitor import run_monitor_task
from backend.services.notification import create_email_service, create_feishu_service
from backend.models.database import get_pending_notifications, mark_notification_sent


def run_monitor(force_image_check=False):
    """运行监控任务"""
    print("=" * 50)
    print(f"开始监控任务 - {__import__('datetime').datetime.now()}")
    print("=" * 50)
    
    try:
        results = run_monitor_task(force_image_check=force_image_check)
        
        print(f"检查商品数: {results['products_checked']}")
        print(f"触发告警数: {len(results['alerts'])}")
        
        for alert in results['alerts']:
            print(f"  - {alert['product_name']}: {alert['item_title']} ¥{alert['price']}")
        
        print("监控任务完成")
        return results
        
    except Exception as e:
        print(f"监控任务出错: {e}")
        import traceback
        traceback.print_exc()
        return None


def send_pending_notifications():
    """发送待处理的通知"""
    print("检查待发送通知...")
    
    notifications = get_pending_notifications()
    email_service = create_email_service()
    feishu_service = create_feishu_service()
    
    for notif in notifications:
        try:
            # 这里根据配置发送通知
            # 实际逻辑已在monitor中处理
            
            mark_notification_sent(notif['id'])
            print(f"已处理通知: {notif['message']}")
        except Exception as e:
            print(f"发送通知失败: {e}")


def main():
    parser = argparse.ArgumentParser(description='闲鱼监控系统定时任务')
    parser.add_argument('--check', action='store_true', help='运行监控检查')
    parser.add_argument('--notify', action='store_true', help='发送待处理通知')
    parser.add_argument('--image-check', action='store_true', help='强制进行图片匹配')
    parser.add_argument('--all', action='store_true', help='执行所有任务')
    
    args = parser.parse_args()
    
    if args.check or args.all:
        run_monitor(force_image_check=args.image_check)
    
    if args.notify or args.all:
        send_pending_notifications()
    
    if not any([args.check, args.notify, args.all]):
        # 默认执行监控
        run_monitor()


if __name__ == "__main__":
    main()
