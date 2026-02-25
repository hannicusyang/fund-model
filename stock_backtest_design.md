# 专业策略回测系统设计方案

## 一、整体流程

```
多因子选股 ──→ 组合构建 ──→ 策略回测 ──→ 策略优化
     ↑              ↓            ↓
   股票池       权重/策略    绩效归因
```

## 二、数据流设计

### 1. 从组合构建导入到回测
- 股票列表（代码+名称）
- 目标权重（等权重/MV优化/风险平价等）
- 优化策略类型（用于回测报告）
- 约束条件（最小/最大权重）

### 2. 回测参数（专业级）

#### 基础参数
- 回测期间：30/60/90/180/365天，或自定义日期
- 基准指数：上证指数/沪深300/深证成指/创业板指/科创50/中证500/上证50
- 初始资金：默认100万

#### 调仓策略
- 调仓频率：
  - 日度（Daily）
  - 周度（Weekly）
  - 月度（Monthly）
  - 季度（Quarterly）
  - 年度（Yearly）
  - 事件驱动（Event-driven）
- 调仓时间：开盘/收盘

#### 交易成本
- 佣金费率：默认万三（0.03%），可调
- 印花税：千一（0.1%），仅卖出收取
- 过户费：固定
- 滑点：千一（0.1%），买卖双向

#### 仓位管理
- 建仓方式：一次性建仓 / 分批建仓
- 目标仓位：100% / 80% / 60%（风控）
- 再平衡阈值：权重偏差超过X%触发

#### 风控参数
- 止损线：个股/组合止损比例
- 止盈线：个股/组合止盈比例
- 最大回撤控制
- 单票仓位上限

### 3. 回测结果输出

#### 收益指标
- 累计收益率（Total Return）
- 年化收益率（Annual Return）
- 超额收益（Alpha，相对基准）
- 基准收益（Benchmark Return）

#### 风险指标
- 年化波动率（Volatility）
- 最大回撤（Max Drawdown）
- 回撤持续时间
- 下行波动率（Downside Volatility）
- VaR (95%, 99%)

#### 风险调整收益
- 夏普比率（Sharpe Ratio）
- 索提诺比率（Sortino Ratio）
- 卡玛比率（Calmar Ratio）
- 信息比率（Information Ratio）
- 特雷诺比率（Treynor Ratio）

#### 交易统计
- 总交易次数
- 买入/卖出次数
- 胜率（Win Rate）
- 盈亏比（Profit/Loss Ratio）
- 平均持仓天数
- 换手率（Turnover）
- 总交易成本

#### 归因分析
- 行业归因（Sector Attribution）
- 因子归因（Factor Attribution）
- 择时能力（Market Timing）
- 选股能力（Stock Selection）

## 三、页面功能设计

### 左侧：策略配置面板

#### 1. 数据来源
- 从组合构建导入（推荐）
- 从自选列表导入
- 手动输入股票

#### 2. 组合信息展示
- 股票列表（显示名称+权重）
- 权重分布可视化（饼图）
- 策略类型标识

#### 3. 回测参数配置
- 折叠面板分组（基础/成本/风控）
- 参数预设模板（保守型/稳健型/激进型）
- 参数说明提示

### 右侧：回测结果面板

#### 1. 概览卡片
- 累计收益 vs 基准（大数字）
- 核心指标：年化收益、最大回撤、夏普比率
- 交易统计：交易次数、胜率、成本

#### 2. 收益曲线图
- 组合净值 vs 基准净值
- 支持缩放、 tooltip 显示详细数据
- 标注调仓时间点

#### 3. 回撤分析图
- 动态回撤曲线
- 最大回撤区间标注

#### 4. 月度收益热力图
- 12个月 × 年份矩阵
- 颜色表示盈亏

#### 5. 持仓分析
- 饼图：当前权重分布
- 表格：各股票收益贡献
- 柱状图：行业配置

#### 6. 交易记录
- 完整的买卖记录表格
- 支持筛选（买入/卖出/再平衡）
- 显示成本明细

#### 7. 归因分析（进阶）
- Brinson归因模型
- 因子暴露分析
- 风格分析（Size/Value/Momentum）

## 四、技术实现

### 后端增强

#### 1. 回测引擎优化
```python
class BacktestEngine:
    def __init__(self, config):
        self.initial_capital = config['initialCapital']
        self.benchmark = config['benchmark']
        self.rebalance_freq = config['rebalanceFreq']
        self.commission = config['commissionRate']
        self.slippage = config['slippage']
        
    def run(self, stocks, weights, start_date, end_date):
        # 1. 获取历史数据
        # 2. 按调仓频率执行
        # 3. 计算交易成本
        # 4. 记录持仓变化
        # 5. 生成交易记录
        pass
```

#### 2. 绩效归因
- Brinson模型：资产配置 + 个股选择
- 因子归因：Barra风格因子
- 行业归因：GICS/申万行业分类

#### 3. 数据需求
- 历史行情数据（日K，前复权）
- 基准指数数据
- 行业分类数据
- 因子数据（Size/Value/Momentum等）

### 前端优化

#### 1. 组件结构
```
StockBacktestPro
├── StrategyConfigPanel (左侧配置)
│   ├── DataSourceSelector
│   ├── PortfolioInfoDisplay
│   ├── BacktestParamsForm
│   └── StrategyTemplates
└── BacktestResultPanel (右侧结果)
    ├── SummaryMetrics
    ├── EquityCurveChart
    ├── DrawdownChart
    ├── MonthlyReturnsHeatmap
    ├── PositionAnalysis
    ├── TradeRecordsTable
    └── AttributionAnalysis
```

#### 2. 状态管理
```javascript
const backtestState = {
  // 输入
  portfolio: [],  // 股票+权重
  strategyType: '',  // 优化策略类型
  
  // 参数
  params: {
    period: 60,
    benchmark: 'sh.000300',
    rebalanceFreq: 'monthly',
    commissionRate: 0.0003,
    // ...
  },
  
  // 结果
  result: {
    summary: {},
    curve: {},
    trades: [],
    attribution: {}
  }
}
```

## 五、实施步骤

### Phase 1: 基础功能完善（1-2天）
1. 修复现有回测数据解析问题
2. 增加专业回测参数（成本/调仓频率）
3. 完善交易记录展示

### Phase 2: 数据流打通（2-3天）
1. 组合构建 → 回测的数据传递
2. 权重导入和显示
3. 策略类型标识

### Phase 3: 专业功能（3-5天）
1. 多种调仓策略实现
2. 详细交易统计
3. 绩效归因分析
4. 可视化图表优化

### Phase 4: 高级功能（5-7天）
1. 策略对比（多个策略并行回测）
2. 参数敏感性分析
3. 蒙特卡洛模拟
4. 压力测试

## 六、关键代码结构

### 后端回测引擎
```python
# routes/stock_backtest_pro.py

class BacktestEngine:
    def __init__(self, config):
        self.config = config
        self.positions = {}
        self.cash = config['initialCapital']
        self.trades = []
        
    def get_rebalance_dates(self, start_date, end_date, freq):
        """获取调仓日期列表"""
        if freq == 'monthly':
            return pd.date_range(start_date, end_date, freq='M')
        elif freq == 'quarterly':
            return pd.date_range(start_date, end_date, freq='Q')
        # ...
        
    def execute_trade(self, date, stock_code, shares, price, action):
        """执行交易，记录成本"""
        amount = shares * price
        commission = amount * self.config['commissionRate']
        
        if action == 'sell':
            stamp_duty = amount * self.config['stampDuty']
            commission += stamp_duty
            
        self.trades.append({
            'date': date,
            'code': stock_code,
            'action': action,
            'shares': shares,
            'price': price,
            'amount': amount,
            'cost': commission,
            'net_amount': amount - commission if action == 'sell' else amount + commission
        })
        
    def run(self, stocks, weights, start_date, end_date):
        """主回测逻辑"""
        rebalance_dates = self.get_rebalance_dates(start_date, end_date, 
                                                    self.config['rebalanceFreq'])
        
        for date in rebalance_dates:
            # 1. 获取当前价格
            # 2. 计算目标持仓
            # 3. 执行调仓
            # 4. 记录持仓价值
            pass
            
        # 计算绩效指标
        return {
            'summary': self.calculate_metrics(),
            'trades': self.trades,
            'curve': self.equity_curve
        }
```

### 前端组件
```vue
<!-- StockBacktestPro.vue -->
<template>
  <div class="backtest-pro">
    <a-row :gutter="16">
      <!-- 左侧配置 -->
      <a-col :span="6">
        <ConfigPanel 
          :portfolio="portfolio"
          :params="params"
          @run="runBacktest"
        />
      </a-col>
      
      <!-- 右侧结果 -->
      <a-col :span="18">
        <ResultPanel v-if="result" :data="result" />
        <EmptyState v-else />
      </a-col>
    </a-row>
  </div>
</template>
```

## 七、数据源

### 已实现
- ✅ baostock - A股历史行情
- ✅ 自选列表接口
- ✅ 股票基本信息

### 需要补充
- ⬜ 行业分类数据（申万/中信）
- ⬜ 因子数据（Size/Value/Momentum）
- ⬜ 宏观数据（用于归因）

## 八、性能优化

1. **数据缓存**：历史数据缓存，避免重复获取
2. **增量计算**：只计算变化的部分
3. **异步处理**：长时间回测使用异步任务
4. **结果缓存**：相同参数直接返回缓存结果

## 九、用户体验

1. **加载状态**：长时间回测显示进度条
2. **参数预设**：提供几组典型参数模板
3. **结果对比**：可以同时对比多个策略
4. **导出功能**：导出回测报告（PDF/Excel）
5. **保存策略**：保存参数配置，下次直接使用

## 十、风险评估

### 回测局限性说明
1. **过拟合风险**：历史表现不代表未来
2. **幸存者偏差**：退市股票未纳入
3. **流动性假设**：假设可以按收盘价成交
4. **数据质量**：停牌/除权处理

### 建议
1. 使用样本外数据验证
2. 进行参数敏感性分析
3. 考虑滑点和冲击成本
4. 定期用实盘数据校准模型
