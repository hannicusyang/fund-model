# 长期记忆

## 闲鱼商品监测系统

### 项目概述
监测闲鱼商品价格，支持图片识别匹配、好价判断、邮件/飞书通知、自动拍下（待实现）

### 项目路径
`/home/clawdbot/.openclaw/workspace/xianyu_monitor/`

### 技术栈
- 后端：Python Flask
- 前端：Vue 3 + Ant Design Vue
- 数据库：SQLite
- 图片识别：OpenAI Vision API
- 通知：邮件 + 飞书webhook

### 核心模块
- `backend/models/database.py` - 数据库模型
- `backend/services/xianyu_spider.py` - 闲鱼爬虫（支持Mock模式）
- `backend/services/image_recognition.py` - 图片识别服务
- `backend/services/notification.py` - 通知服务
- `backend/services/monitor.py` - 核心监控逻辑
- `backend/routes/xianyu.py` - API路由
- `backend/tasks.py` - 定时任务脚本
- `frontend/src/views/XianyuMonitor.vue` - 前端页面

### 使用方式
1. 复制config.example.py为config.py并配置
2. 初始化数据库：python3 backend/models/database.py
3. 启动后端：python3 backend/app.py
4. 配置cron定时任务：参考crontab.txt

### 待实现功能
- [ ] 真实闲鱼API接入（需要Cookie）
- [ ] 自动拍下功能（需要处理滑块验证码）
- [ ] 接入OpenClaw定时任务

---

## 2026-03-02 技术分析移动端修复

### K线图溢出问题
- **问题**：K线图在移动端超出容器边界
- **根因**：ECharts通过JS内部设置canvas宽度，CSS无法覆盖
- **解决方案**：在StockAnalysis.vue添加`fixKlineWidth()`函数，onMounted时调用chart.resize()重新设置宽度

### 修改文件
- `Fund_front/src/components/model/stock/StockAnalysis.vue`

---

## 股票模型实验项目

### 项目概述
开发专业量化投资股票模型实验室，包含：
- 多因子选股（StockScreening）
- 技术分析（StockAnalysis）
- 组合构建（StockPortfolio）
- 策略回测（StockBacktest）- 待开发

### 技术栈
- 前端：Vue 3 + Ant Design Vue + ECharts
- 后端：Python Flask（待接入）
- API路径：/api

### 关键文件
- `src/views/ModelExperiment.vue` - 主页面
- `src/components/model/stock/` - 股票模型组件目录
- `src/api/stockModel.js` - 股票API接口

### 架构参考
- 参考 `fundModel.js` API模式
- 参考 `FundBacktest.vue` 回测组件架构
- 复用 Fund_backtest.py 后端逻辑

### 硬编码/模拟数据
- `StockScreening.vue`: DEFAULT_FACTORS, MOCK_STOCKS (10只A股)
- `StockAnalysis.vue`: MOCK_STOCK_DATA (4只A股), 前端计算技术指标
- `StockPortfolio.vue`: STOCK_DATABASE (10只A股), 前端计算组合指标

### 待办
- [ ] StockBacktest 策略回测模块
- [x] 后端API接入 (多因子筛选API已可用)
- [x] 替换模拟数据为真实数据 (组合构建页面已完成)

### 2026-02-24 组合构建优化

#### 已完成
- 移除所有硬编码数据，股票池从自选列表加载
- 搜索功能使用真实筛选API
- 新增6种优化策略：等权重/均值-方差/风险平价/最小方差/最大夏普/最大收益
- 策略说明与约束条件
- 指标计算使用真实20日涨跌幅

#### 待后端完善
- 组合指标API（目前前端计算）
- 策略参数持久化

### 2026-02-19 架构升级进展

#### 新增架构组件
- **TypeScript类型定义**: `src/types/stock.ts` - 完整数据模型
- **Pinia状态管理**: `src/stores/stock/` - pool/screening/analysis/portfolio stores
- **通用组件**: `src/components/stock/common/` - FactorSlider/StockTable/StockTag/LoadingOverlay
- **面板组件**: `src/components/stock/` - ScreeningPanel/AnalysisPanel/PortfolioPanel

#### 后端工具
- `schemas/stock.py` - 参数验证
- `utils/api_response.py` - 统一API响应格式
- `utils/cache.py` - 缓存工具
- `models/screening_strategy.py` - 策略持久化模型
- `routes/stock_screening_v2.py` - 重构API路由

#### 当前阻塞
- Vue模板标签错误(Invalid end tag) - 需修复新组件
- 需在app.py注册新蓝图
- 需执行数据库迁移
