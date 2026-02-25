"""
邮件通知服务
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import os
from typing import List, Dict
import json
from datetime import datetime

class EmailService:
    """邮件服务"""
    
    def __init__(self, config: dict = None):
        self.config = config or self._load_config()
    
    def _load_config(self) -> dict:
        """加载配置"""
        try:
            # 尝试导入配置
            from backend.config import MAIL_CONFIG
            return MAIL_CONFIG
        except:
            # 使用默认配置
            return {
                "smtp_host": "smtp.qq.com",
                "smtp_port": 465,
                "smtp_user": os.getenv("MAIL_USER", ""),
                "smtp_password": os.getenv("MAIL_PASSWORD", ""),
                "from_email": os.getenv("MAIL_USER", ""),
                "to_emails": []
            }
    
    def send_mail(
        self, 
        subject: str, 
        content: str, 
        to_emails: List[str] = None,
        html: bool = False
    ) -> bool:
        """发送邮件"""
        if not self.config.get("smtp_user") or not self.config.get("smtp_password"):
            print("邮件配置不完整，跳过发送")
            return False
        
        to_emails = to_emails or self.config.get("to_emails", [])
        if not to_emails:
            print("没有收件人，跳过发送")
            return False
        
        msg = MIMEMultipart('alternative')
        msg['From'] = self.config.get("from_email")
        msg['To'] = ', '.join(to_emails)
        msg['Subject'] = Header(subject, 'utf-8')
        
        if html:
            msg.attach(MIMEText(content, 'html', 'utf-8'))
        else:
            msg.attach(MIMEText(content, 'plain', 'utf-8'))
        
        try:
            smtp = smtplib.SMTP_SSL(
                self.config.get("smtp_host", "smtp.qq.com"),
                self.config.get("smtp_port", 465)
            )
            smtp.login(
                self.config.get("smtp_user"),
                self.config.get("smtp_password")
            )
            smtp.sendmail(
                self.config.get("from_email"),
                to_emails,
                msg.as_string()
            )
            smtp.quit()
            print(f"邮件发送成功: {subject}")
            return True
        except Exception as e:
            print(f"邮件发送失败: {e}")
            return False
    
    def send_price_alert(
        self, 
        product_name: str, 
        item: Dict,
        alert_type: str = "price_drop"
    ) -> bool:
        """发送价格提醒"""
        if alert_type == "price_drop":
            subject = f"【好价提醒】{product_name} 价格下降了！"
            discount_rate = item['price'] / item['original_price'] if item.get('original_price') else 0
            
            content = f"""
<h2>🎉 好价提醒！</h2>

<p>您关注的 <strong>{product_name}</strong> 出现好价了！</p>

<table>
<tr><td><strong>商品标题</strong></td><td>{item['title']}</td></tr>
<tr><td><strong>当前价格</strong></td><td style="color:red;font-size:18px;">¥{item['price']}</td></tr>
<tr><td><strong>原价</strong></td><td>¥{item['original_price']}</td></tr>
<tr><td><strong>折扣</strong></td><td>{discount_rate*10:.1f}折</td></tr>
<tr><td><strong>卖家</strong></td><td>{item['seller_nick']}</td></tr>
<tr><td><strong>地点</strong></td><td>{item['location']}</td></tr>
<tr><td><strong>发布时间</strong></td><td>{item.get('posted_time', '')}</td></tr>
</table>

<p><a href="{item['url']}">查看商品链接</a></p>

<p style="color:#888;font-size:12px;">
收到时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</p>
"""
        elif alert_type == "new_item":
            subject = f"【新商品】{product_name} 有新上架！"
            content = f"""
<h2>📢 新商品上架！</h2>

<p>您关注的 <strong>{product_name}</strong> 有新商品上架！</p>

<table>
<tr><td><strong>商品标题</strong></td><td>{item['title']}</td></tr>
<tr><td><strong>价格</strong></td><td>¥{item['price']}</td></tr>
<tr><td><strong>卖家</strong></td><td>{item['seller_nick']}</td></tr>
<tr><td><strong>地点</strong></td><td>{item['location']}</td></tr>
</table>

<p><a href="{item['url']}">查看商品链接</a></p>
"""
        else:
            subject = f"【{product_name}】监控提醒"
            content = f"<p>{item.get('title', '')}</p>"
        
        return self.send_mail(subject, content, html=True)
    
    def send_matched_product_alert(
        self,
        product_name: str,
        item: Dict,
        match_reason: str
    ) -> bool:
        """发送商品匹配提醒"""
        subject = f"【商品匹配】{product_name} 找到匹配商品！"
        
        content = f"""
<h2>🔍 商品匹配提醒！</h2>

<p>您设置的商品 <strong>{product_name}</strong> 找到了匹配商品！</p>

<p><strong>匹配原因:</strong> {match_reason}</p>

<table>
<tr><td><strong>商品标题</strong></td><td>{item['title']}</td></tr>
<tr><td><strong>价格</strong></td><td>¥{item['price']}</td></tr>
<tr><td><strong>原价</strong></td><td>¥{item.get('original_price', 'N/A')}</td></tr>
<tr><td><strong>卖家</strong></td><td>{item['seller_nick']}</td></tr>
<tr><td><strong>地点</strong></td><td>{item['location']}</td></tr>
</table>

<p><a href="{item['url']}">查看商品链接</a></p>
"""
        
        return self.send_mail(subject, content, html=True)


class FeishuNotifyService:
    """飞书通知服务"""
    
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or os.getenv("FEISHU_WEBHOOK_URL", "")
    
    def send(self, message: str) -> bool:
        """发送飞书消息"""
        if not self.webhook_url:
            print("飞书webhook未配置")
            return False
        
        try:
            import requests
            response = requests.post(
                self.webhook_url,
                json={"msg_type": "text", "content": {"text": message}},
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"飞书通知失败: {e}")
            return False
    
    def send_card(self, title: str, items: List[Dict]) -> bool:
        """发送卡片消息"""
        if not self.webhook_url:
            return False
        
        # 构建卡片内容
        elements = []
        for item in items:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**{item.get('label', '')}**: {item.get('value', '')}"
                }
            })
        
        card = {
            "msg_type": "interactive",
            "card": {
                "header": {"title": {"tag": "plain_text", "content": title}},
                "elements": elements
            }
        }
        
        try:
            import requests
            response = requests.post(self.webhook_url, json=card, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"飞书卡片发送失败: {e}")
            return False


def create_email_service(config: dict = None) -> EmailService:
    """创建邮件服务"""
    return EmailService(config)


def create_feishu_service(webhook_url: str = None) -> FeishuNotifyService:
    """创建飞书服务"""
    return FeishuNotifyService(webhook_url)


if __name__ == "__main__":
    # 测试
    service = EmailService()
    print("邮件服务已创建")
