"""
闲鱼监控系统 - Flask主应用
"""
from flask import Flask, jsonify
from flask_cors import CORS
import os

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 配置
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'xianyu-monitor-secret')
    
    # 允许跨域
    CORS(app)
    
    # 注册路由
    from backend.routes.xianyu import register_routes
    register_routes(app)
    
    # 健康检查
    @app.route('/health')
    def health():
        return jsonify({'status': 'ok'})
    
    return app


# 创建应用实例
app = create_app()


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
