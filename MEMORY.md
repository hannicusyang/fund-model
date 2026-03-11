# 长期记忆

## ⚠️ 代码推送规则 (永久)
- **未经用户允许，禁止推送到远程仓库**
- 改造过程可自主进行，每阶段完成后主动汇报
- 代码开发完成后等待用户指示再推送

## ⚠️ 开发自测规则 (永久)
- **每阶段开发完成后，必须自行测试代码是否正常**
- 遇到问题要自己排查修复
- 测试通过后再汇报完成

## 2026-03-08 财经资讯监控优化

### 问题
1. 监控任务获取的正文包含HTML标签，需要清洗
2. 新闻平台筛选器失效，大部分API无数据
3. 前端下拉框选项与数据源不匹配
4. API请求路径重复

### 解决
1. **HTML清洗**：在`market_intelligence.py`和`news_service.py`中添加`clean_html_content()`函数
2. **筛选逻辑优化**：
   - 后端：用户选择的源无数据时返回空，不使用备用源
   - 前端：精简下拉框选项，只保留有效项
3. **数据源配置**：
   - 资讯监控：财联社+华尔街见闻+格隆汇+东方财富（约300条/天）
   - 东方财富API：约100条/天
   - 全部：合并上述两者
4. **修复路径**：移除重复的`/api`前缀

### 关键文件
- `Fund_backend/services/news_service.py` - 新闻服务
- `Fund_backend/routes/market_intelligence.py` - 资讯API
- `Fund_front/src/views/MarketIntelligence.vue` - 前端页面

---

## 2026-03-06 Bilibili监控AI总结Bug修复

### 问题
用户反馈AI总结和字幕原文与视频完全不匹配

### 根因
Flask服务器缓存问题 + B站API返回错误字幕

### 解决
- 清除Python缓存后重启Flask
- 清理错误数据重新获取
- 添加DEBUG日志排查

### 验证
ID 11视频"哈梅内伊遇害细节曝光"现在字幕和总结都正确

---

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
