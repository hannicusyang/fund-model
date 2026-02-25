<template>
  <div v-if="error" class="error-container">
    <a-empty description="数据加载失败，请刷新重试" />
    <a-button type="primary" @click="refreshData">重试</a-button>
  </div>
  
  <div class="market-situation-container">
    <!-- 顶部筛选栏 -->
    <a-card class="filter-card" :bordered="false">
      <a-row :gutter="16" align="middle">
        <a-col :xs="24" :sm="12" :md="16">
          <a-space wrap>
            <!-- 日期选择 -->
            <a-date-picker
              v-if="isMonthlyData"
              v-model:value="selectedPeriod"
              picker="month"
              :disabled-date="disabledMonth"
              value-format="YYYY-MM"
              @change="handleDateChange"
              style="width: 140px"
            />
            <a-date-picker
              v-else
              v-model:value="selectedDate"
              :disabled-date="disabledDate"
              value-format="YYYY-MM-DD"
              @change="handleDateChange"
              style="width: 140px"
            />
            
            <!-- 交易所选择 -->
            <a-segmented
              v-if="dataType === 'summary'"
              v-model:value="exchangeType"
              :options="exchangeOptions"
              @change="loadData"
            />
            
            <!-- 数据类型选择 -->
            <a-segmented
              v-model:value="dataType"
              :options="dataTypeOptions"
              @change="onDataTypeChange"
            />
            
            <a-divider type="vertical" />
            
            <span class="update-time">
              <ClockCircleOutlined />
              更新: {{ formattedUpdateTime }}
            </span>
          </a-space>
        </a-col>
        
        <a-col :xs="24" :sm="12" :md="8" style="text-align: right">
          <a-button type="primary" @click="refreshData" :loading="loading">
            <template #icon><SyncOutlined /></template>
            刷新
          </a-button>
        </a-col>
      </a-row>
    </a-card>

    <!-- 市场概览卡片 - 仅在 summary 模式显示 -->
    <a-row v-if="showSummaryCards" :gutter="16" class="summary-row">
      <a-col :xs="24" :sm="12" :lg="6">
        <StatCard
          title="总市值"
          :value="marketStats.totalMV"
          unit="亿元"
          :precision="2"
          :trend="marketStats.trendMV"
          icon="💰"
          color="#1890ff"
        />
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6">
        <StatCard
          title="上市公司数"
          :value="marketStats.companies"
          unit="家"
          :precision="0"
          :trend="marketStats.trendCompanies"
          icon="🏢"
          color="#52c41a"
        />
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6">
        <StatCard
          title="平均市盈率"
          :value="marketStats.avgPE"
          unit="倍"
          :precision="2"
          :trend="marketStats.trendPE"
          icon="📊"
          color="#faad14"
        />
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6">
        <StatCard
          title="成交金额"
          :value="marketStats.turnover"
          unit="亿元"
          :precision="2"
          :trend="marketStats.trendTurnover"
          icon="💹"
          color="#722ed1"
        />
      </a-col>
    </a-row>

    <!-- 子板详情 - 仅在 summary 模式显示 -->
    <a-row v-if="showSummaryCards && boardDetails.length" :gutter="16" class="board-row">
      <a-col :span="24">
        <a-card title="板块详情" size="small">
          <a-row :gutter="8">
            <a-col v-for="board in boardDetails" :key="board.key" :xs="12" :sm="12" :md="12" :lg="6">
              <div class="board-item" :style="{ borderLeftColor: board.color }">
                <div class="board-name">{{ board.name }}</div>
                <div class="board-stats">
                  <span>市值: {{ formatNumber(board.mv) }}亿</span>
                  <span>PE: {{ board.pe }}倍</span>
                  <span>家数: {{ board.companies }}家</span>
                </div>
              </div>
            </a-col>
          </a-row>
        </a-card>
      </a-col>
    </a-row>

    <!-- 双图表布局 -->
    <a-row :gutter="16" class="charts-row">
      <a-col :xs="24" :lg="12">
        <a-card :title="chartTitle1" size="small" class="chart-card">
          <div ref="pieChartRef" class="chart-container"></div>
        </a-card>
      </a-col>
      <a-col :xs="24" :lg="12">
        <a-card :title="chartTitle2" size="small" class="chart-card">
          <div ref="barChartRef" class="chart-container"></div>
        </a-card>
      </a-col>
    </a-row>

    <!-- 详细数据表格 -->
    <a-card :title="tableTitle" size="small" class="table-card">
      <a-table
        :columns="tableColumns"
        :data-source="tableData"
        :loading="loading"
        :row-key="record => record.key"
        :pagination="tablePagination"
        :scroll="{ x: 'max-content' }"
        size="small"
      >
        <template #bodyCell="{ column, text, record }">
          <!-- 名称列加粗 -->
          <template v-if="['project', 'region', 'sector', 'security_type'].includes(column.key)">
            <span class="cell-bold">{{ text }}</span>
          </template>
          
          <!-- 数值列格式化 -->
          <template v-else-if="isNumberColumn(column.key)">
            <span :class="getValueClass(text, column.key)">
              {{ formatTableValue(text, column.key) }}
            </span>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { message } from 'ant-design-vue'
import { SyncOutlined, ClockCircleOutlined } from '@ant-design/icons-vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import axios from '@/utils/axios'

// ==================== 常量配置 ====================
const EXCHANGE_OPTIONS = [
  { label: '上交所', value: 'sse' },
  { label: '深交所', value: 'szse' }
]

const DATA_TYPE_OPTIONS = [
  { label: '市场总貌', value: 'summary' },
  { label: '地区交易', value: 'area' },
  { label: '行业成交', value: 'sector' }
]

const CHART_COLORS = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4']

// ==================== 响应式数据 ====================
const loading = ref(false)
const error = ref(null)

const selectedDate = ref(dayjs().format('YYYY-MM-DD'))
const selectedPeriod = ref(dayjs().subtract(1, 'month'))
const exchangeType = ref('sse')
const dataType = ref('summary')
const updateTime = ref('')

// 原始数据存储
const sseData = ref(null)
const szseData = ref([])
const szseAreaData = ref([])
const szseSectorData = ref([])

// 图表实例
const pieChartRef = ref(null)
const barChartRef = ref(null)
let pieChartInstance = null
let barChartInstance = null

// ==================== 计算属性 ====================
const exchangeOptions = computed(() => EXCHANGE_OPTIONS)
const dataTypeOptions = computed(() => DATA_TYPE_OPTIONS)

const isMonthlyData = computed(() => dataType.value === 'area' || dataType.value === 'sector')

const formattedUpdateTime = computed(() => {
  if (!updateTime.value) return '暂无'
  return dayjs(updateTime.value).format('MM-DD HH:mm')
})

const showSummaryCards = computed(() => {
  return dataType.value === 'summary' && (sseData.value || szseData.value.length)
})

// 市场统计数据
const marketStats = computed(() => {
  if (!showSummaryCards.value) return {}
  
  if (exchangeType.value === 'sse' && sseData.value) {
    const { main_board = {}, star_board = {} } = sseData.value
    const totalMV = (main_board.total_mv || 0) + (star_board.total_mv || 0)
    const dealDaily = sseData.value.deal_daily || {}
    const companies = dealDaily.stock || 0
    const peData = sseData.value.deal_daily_pe || {}
    const avgPE = peData.stock || 0
    const turnoverData = sseData.value.deal_daily_turnover || {}
    const turnover = turnoverData.stock || 0
    
    return {
      totalMV,
      companies,
      avgPE,
      turnover,
      trendMV: 0, // 需要历史数据计算
      trendCompanies: 0,
      trendPE: 0,
      trendTurnover: 0
    }
  }
  
  if (exchangeType.value === 'szse' && szseData.value.length) {
    // 只统计A股相关数据
    const aShareTypes = ['主板A股', '创业板A股', '中小板A股']
    let totalMV = 0, totalCompanies = 0, totalTurnover = 0
    
    szseData.value.forEach(item => {
      if (aShareTypes.some(type => item.security_type?.includes(type))) {
        totalMV += item.total_mv || 0
        totalCompanies += item.quantity || 0
        totalTurnover += item.turnover_amount || 0
      }
    })
    
    return {
      totalMV,
      companies: totalCompanies,
      avgPE: null, // 深交所summary没有直接提供平均PE
      turnover: totalTurnover,
      trendMV: 0,
      trendCompanies: 0,
      trendPE: 0,
      trendTurnover: 0
    }
  }
  
  return {}
})

// 板块详情
const boardDetails = computed(() => {
  if (!showSummaryCards.value) return []
  
  if (exchangeType.value === 'sse' && sseData.value) {
    const { main_board = {}, star_board = {}, deal_daily = {}, deal_daily_pe = {} } = sseData.value
    return [
      {
        key: 'main',
        name: '上证主板',
        mv: main_board.total_mv || 0,
        pe: deal_daily_pe.main_a || 0,
        companies: deal_daily.main_a || 0,
        color: '#1890ff'
      },
      {
        key: 'star',
        name: '科创板',
        mv: star_board.total_mv || 0,
        pe: deal_daily_pe.star || 0,
        companies: deal_daily.star || 0,
        color: '#52c41a'
      },
      {
        key: 'main_b',
        name: '主板B股',
        mv: 0,
        pe: deal_daily_pe.main_b || 0,
        companies: deal_daily.main_b || 0,
        color: '#faad14'
      },
      {
        key: 'repo',
        name: '股票回购',
        mv: 0,
        pe: deal_daily_pe.repo || 0,
        companies: deal_daily.repo || 0,
        color: '#722ed1'
      }
    ].filter(b => b.companies > 0 || b.mv > 0)
  }
  
  if (exchangeType.value === 'szse' && szseData.value.length) {
    return szseData.value
      .filter(item => item.quantity > 0)
      .map((item, index) => ({
        key: item.security_type,
        name: item.security_type,
        mv: (item.total_mv || 0) / 1e8,
        pe: null,
        companies: item.quantity,
        color: CHART_COLORS[index % CHART_COLORS.length]
      }))
  }
  
  return []
})

// 图表标题
const chartTitle1 = computed(() => {
  const titles = {
    summary: exchangeType.value === 'sse' ? '板块市值分布' : '证券类别分布',
    area: '地区交易额占比',
    sector: '行业成交额占比'
  }
  return titles[dataType.value]
})

const chartTitle2 = computed(() => {
  const titles = {
    summary: '成交额TOP统计',
    area: '地区交易额TOP10',
    sector: '行业成交额TOP10'
  }
  return titles[dataType.value]
})

// 表格标题
const tableTitle = computed(() => {
  const titles = {
    summary: exchangeType.value === 'sse' ? '上交所每日交易统计' : '深交所证券类别统计',
    area: '深交所地区交易明细',
    sector: '深交所行业成交明细'
  }
  return titles[dataType.value]
})

// 表格列定义
const tableColumns = computed(() => {
  switch (dataType.value) {
    case 'summary':
      return exchangeType.value === 'sse' 
        ? getSSETableColumns()
        : getSZSETableColumns()
    case 'area':
      return getAreaTableColumns()
    case 'sector':
      return getSectorTableColumns()
    default:
      return []
  }
})

// 表格数据
const tableData = computed(() => {
  switch (dataType.value) {
    case 'summary':
      return exchangeType.value === 'sse' 
        ? getSSETableData()
        : getSZSETableData()
    case 'area':
      return getAreaTableData()
    case 'sector':
      return getSectorTableData()
    default:
      return []
  }
})

const tablePagination = computed(() => ({
  pageSize: 10,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: total => `共 ${total} 条`
}))

// ==================== 表格列配置 ====================
function getSSETableColumns() {
  const categories = [
    { key: 'stock', title: '股票' },
    { key: 'main_a', title: '主板A' },
    { key: 'main_b', title: '主板B' },
    { key: 'star', title: '科创板' },
    { key: 'repo', title: '回购' }
  ]
  
  return [
    { title: '统计项目', dataIndex: 'label', key: 'label', width: 120, fixed: 'left' },
    ...categories.map(c => ({
      title: c.title,
      dataIndex: c.key,
      key: c.key,
      align: 'right',
      width: 110
    }))
  ]
}

function getSZSETableColumns() {
  return [
    { title: '证券类别', dataIndex: 'security_type', key: 'security_type', width: 140 },
    { title: '数量', dataIndex: 'quantity', key: 'quantity', align: 'right', width: 100 },
    { title: '总市值(亿)', dataIndex: 'total_mv', key: 'total_mv', align: 'right', width: 130 },
    { title: '流通市值(亿)', dataIndex: 'circulating_mv', key: 'circulating_mv', align: 'right', width: 130 },
    { title: '成交金额(亿)', dataIndex: 'turnover_amount', key: 'turnover_amount', align: 'right', width: 130 }
  ]
}

function getAreaTableColumns() {
  return [
    { title: '排名', dataIndex: 'rank', key: 'rank', width: 60, align: 'center' },
    { title: '地区', dataIndex: 'area', key: 'area', width: 100 },
    { title: '总交易额(亿)', dataIndex: 'total_turnover', key: 'total_turnover', align: 'right', width: 130 },
    { title: '市场占比(%)', dataIndex: 'market_share', key: 'market_share', align: 'right', width: 110 },
    { title: '股票交易额(亿)', dataIndex: 'stock_turnover', key: 'stock_turnover', align: 'right', width: 130 },
    { title: '基金交易额(亿)', dataIndex: 'fund_turnover', key: 'fund_turnover', align: 'right', width: 130 }
  ]
}

function getSectorTableColumns() {
  return [
    { title: '行业', dataIndex: 'sector_chinese', key: 'sector_chinese', width: 140 },
    { title: '交易天数', dataIndex: 'trading_days', key: 'trading_days', align: 'center', width: 80 },
    { title: '成交金额(亿)', dataIndex: 'turnover_amount', key: 'turnover_amount', align: 'right', width: 130 },
    { title: '占比(%)', dataIndex: 'turnover_ratio', key: 'turnover_ratio', align: 'right', width: 90 },
    { title: '成交股数(亿)', dataIndex: 'volume_shares', key: 'volume_shares', align: 'right', width: 130 },
    { title: '成交笔数(万)', dataIndex: 'deal_count', key: 'deal_count', align: 'right', width: 120 }
  ]
}

// ==================== 表格数据生成 ====================
function getSSETableData() {
  if (!sseData.value) return []
  
  const fields = [
    { key: 'deal_daily', label: '挂牌数(只)' },
    { key: 'deal_daily_mv', label: '市价总值(亿元)' },
    { key: 'deal_daily_circ_mv', label: '流通市值(亿元)' },
    { key: 'deal_daily_turnover', label: '成交金额(亿元)' },
    { key: 'deal_daily_volume', label: '成交量(亿股)' },
    { key: 'deal_daily_pe', label: '平均市盈率' },
    { key: 'deal_daily_turnover_rate', label: '换手率(%)' },
    { key: 'deal_daily_circ_turnover_rate', label: '流通换手率(%)' }
  ]
  
  return fields.map((field, index) => {
    const data = sseData.value[field.key] || {}
    return {
      key: index,
      label: field.label,
      stock: data.stock,
      main_a: data.main_a,
      main_b: data.main_b,
      star: data.star,
      repo: data.repo
    }
  })
}

function getSZSETableData() {
  if (!szseData.value.length) return []
  
  return szseData.value.map((item, index) => ({
    key: index,
    security_type: item.security_type,
    quantity: item.quantity,
    total_mv: (item.total_mv || 0) / 1e8,
    circulating_mv: (item.circulating_mv || 0) / 1e8,
    turnover_amount: (item.turnover_amount || 0) / 1e8
  }))
}

function getAreaTableData() {
  if (!szseAreaData.value.length) return []
  
  return szseAreaData.value
    .sort((a, b) => b.total_turnover - a.total_turnover)
    .map((item, index) => ({
      key: index,
      rank: index + 1,
      area: item.area,
      total_turnover: (item.total_turnover || 0) / 1e8,
      market_share: item.market_share,
      stock_turnover: (item.stock_turnover || 0) / 1e8,
      fund_turnover: (item.fund_turnover || 0) / 1e8
    }))
}

function getSectorTableData() {
  if (!szseSectorData.value.length) return []
  
  return szseSectorData.value
    .sort((a, b) => b.turnover_amount_cny - a.turnover_amount_cny)
    .map((item, index) => ({
      key: index,
      sector_chinese: item.sector_chinese,
      trading_days: item.trading_days,
      turnover_amount: (item.turnover_amount_cny || 0) / 1e8,
      turnover_ratio: item.turnover_amount_pct,
      volume_shares: (item.volume_shares || 0) / 1e8,
      deal_count: (item.deal_count || 0) / 1e4
    }))
}

// ==================== 格式化函数 ====================
function formatNumber(value, precision = 2) {
  if (value == null || isNaN(value)) return '--'
  if (Math.abs(value) >= 1e12) return (value / 1e12).toFixed(precision) + '万亿'
  if (Math.abs(value) >= 1e8) return (value / 1e8).toFixed(precision) + '亿'
  if (Math.abs(value) >= 1e4) return (value / 1e4).toFixed(precision) + '万'
  return value.toFixed(precision)
}

function formatTableValue(value, columnKey) {
  if (value == null || value === '') return '--'
  
  // 百分比列
  if (columnKey.includes('pct') || columnKey.includes('ratio') || columnKey.includes('share') || columnKey.includes('rate')) {
    return typeof value === 'number' ? value.toFixed(2) + '%' : value
  }
  
  // 金额列
  if (columnKey.includes('mv') || columnKey.includes('amount') || columnKey.includes('turnover')) {
    return formatNumber(value)
  }
  
  // 数量列
  if (columnKey.includes('volume') || columnKey.includes('count') || columnKey.includes('quantity')) {
    return formatNumber(value, 0)
  }
  
  return typeof value === 'number' ? value.toFixed(2) : value
}

function isNumberColumn(columnKey) {
  const numberKeys = ['mv', 'amount', 'turnover', 'volume', 'count', 'quantity', 'pe', 'share', 'ratio', 'pct', 'rate']
  return numberKeys.some(k => columnKey.includes(k))
}

function getValueClass(value, columnKey) {
  if (typeof value !== 'number') return ''
  if (columnKey.includes('ratio') || columnKey.includes('share')) {
    return value > 5 ? 'value-high' : 'value-normal'
  }
  return value > 0 ? 'value-up' : value < 0 ? 'value-down' : ''
}

// ==================== 数据加载 ====================
async function loadData() {
  loading.value = true
  error.value = null
  
  try {
    switch (dataType.value) {
      case 'summary':
        await loadSummaryData()
        break
      case 'area':
        await loadAreaData()
        break
      case 'sector':
        await loadSectorData()
        break
    }
    
    await nextTick()
    renderCharts()
  } catch (err) {
    console.error('加载数据失败:', err)
    error.value = err.message
    message.error(`加载数据失败: ${err.message}`)
  } finally {
    loading.value = false
  }
}

async function loadSummaryData() {
  if (exchangeType.value === 'sse') {
    const response = await axios.get('/api/stock/sse-summary', {
      params: { date: selectedDate.value }
    })
    if (response?.success) {
      sseData.value = response.data
      updateTime.value = response.data.update_time || new Date().toISOString()
    } else {
      throw new Error(response?.msg || 'SSE数据加载失败')
    }
  } else {
    const response = await axios.get('/api/stock/szse-summary', {
      params: { date: selectedDate.value }
    })
    if (response?.success) {
      szseData.value = response.data || []
      updateTime.value = response.data?.[0]?.update_time || new Date().toISOString()
    } else {
      throw new Error(response?.msg || 'SZSE数据加载失败')
    }
  }
}

async function loadAreaData() {
  const period = selectedPeriod.value.format('YYYY-MM')
  const response = await axios.get('/api/stock/szse-area-summary', {
    params: { date: period }
  })
  if (response?.success) {
    szseAreaData.value = response.data || []
    updateTime.value = new Date().toISOString()
  } else {
    throw new Error(response?.msg || '地区数据加载失败')
  }
}

async function loadSectorData() {
  const period = selectedPeriod.value.format('YYYY-MM')
  const response = await axios.get('/api/stock/szse-sector-summary', {
    params: { date: period, symbol: '当月' }
  })
  if (response?.success) {
    szseSectorData.value = response.data || []
    updateTime.value = new Date().toISOString()
  } else {
    throw new Error(response?.msg || '行业数据加载失败')
  }
}

function refreshData() {
  loadData()
}

function handleDateChange() {
  loadData()
}

function onDataTypeChange() {
  // 切换数据类型时重置数据并重新加载
  sseData.value = null
  szseData.value = []
  szseAreaData.value = []
  szseSectorData.value = []
  loadData()
}

function disabledDate(current) {
  return current && current.isAfter(dayjs().endOf('day'))
}

function disabledMonth(current) {
  return current && current.isSameOrAfter(dayjs().startOf('month'))
}

// ==================== 图表渲染 ====================
function renderCharts() {
  renderPieChart()
  renderBarChart()
}

function renderPieChart() {
  if (!pieChartRef.value) return
  
  if (!pieChartInstance) {
    pieChartInstance = echarts.init(pieChartRef.value)
  }
  
  let option = {}
  
  if (dataType.value === 'summary') {
    option = getSummaryPieOption()
  } else if (dataType.value === 'area') {
    option = getAreaPieOption()
  } else if (dataType.value === 'sector') {
    option = getSectorPieOption()
  }
  
  pieChartInstance.setOption(option, true)
}

function getSummaryPieOption() {
  const data = boardDetails.value.map((item, index) => ({
    name: item.name,
    value: item.mv || item.companies || 0,
    itemStyle: { color: item.color || CHART_COLORS[index % CHART_COLORS.length] }
  })).filter(d => d.value > 0)
  
  return {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      textStyle: { fontSize: 12 }
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['35%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 8,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: false,
        position: 'center'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 16,
          fontWeight: 'bold'
        }
      },
      labelLine: { show: false },
      data
    }]
  }
}

function getAreaPieOption() {
  const data = szseAreaData.value
    .slice(0, 8)
    .map((item, index) => ({
      name: item.area,
      value: item.total_turnover || 0,
      itemStyle: { color: CHART_COLORS[index % CHART_COLORS.length] }
    }))
  
  return {
    tooltip: {
      trigger: 'item',
      formatter: params => {
        const value = (params.value / 1e8).toFixed(2)
        return `${params.name}<br/>交易额: ${value}亿元 (${params.percent}%)`
      }
    },
    legend: {
      orient: 'horizontal',
      bottom: 0,
      left: 'center',
      textStyle: { fontSize: 11 },
      itemWidth: 12,
      itemHeight: 12
    },
    series: [{
      type: 'pie',
      radius: ['35%', '60%'],
      center: ['50%', '45%'],
      itemStyle: {
        borderRadius: 6,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: { show: false },
      emphasis: {
        label: {
          show: true,
          fontSize: 14,
          fontWeight: 'bold'
        }
      },
      data
    }]
  }
}

function getSectorPieOption() {
  const data = szseSectorData.value
    .slice(0, 8)
    .map((item, index) => ({
      name: item.sector_chinese,
      value: item.turnover_amount_cny || 0,
      itemStyle: { color: CHART_COLORS[index % CHART_COLORS.length] }
    }))

  return {
    tooltip: {
      trigger: 'item',
      formatter: params => {
        const value = (params.value / 1e8).toFixed(2)
        return `${params.name}<br/>成交额: ${value}亿元 (${params.percent}%)`
      }
    },
    legend: {
      orient: 'horizontal',
      bottom: 0,
      left: 'center',
      textStyle: { fontSize: 11 },
      itemWidth: 12,
      itemHeight: 12
    },
    series: [{
      type: 'pie',
      radius: ['35%', '60%'],
      center: ['50%', '45%'],
      itemStyle: {
        borderRadius: 6,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: { show: false },
      emphasis: {
        label: {
          show: true,
          fontSize: 14,
          fontWeight: 'bold'
        }
      },
      data
    }]
  }
}

function renderBarChart() {
  if (!barChartRef.value) return
  
  if (!barChartInstance) {
    barChartInstance = echarts.init(barChartRef.value)
  }
  
  let option = {}
  
  if (dataType.value === 'summary') {
    option = getSummaryBarOption()
  } else if (dataType.value === 'area') {
    option = getAreaBarOption()
  } else if (dataType.value === 'sector') {
    option = getSectorBarOption()
  }
  
  barChartInstance.setOption(option, true)
}

function getSummaryBarOption() {
  // 使用表格中的成交额数据
  let categories = []
  let values = []
  
  if (exchangeType.value === 'sse' && sseData.value) {
    const turnoverData = sseData.value.deal_daily_turnover || {}
    categories = ['股票', '主板A', '主板B', '科创板', '回购']
    values = [
      turnoverData.stock || 0,
      turnoverData.main_a || 0,
      turnoverData.main_b || 0,
      turnoverData.star || 0,
      turnoverData.repo || 0
    ]
  } else if (exchangeType.value === 'szse' && szseData.value.length) {
    const sorted = [...szseData.value]
      .sort((a, b) => (b.turnover_amount || 0) - (a.turnover_amount || 0))
      .slice(0, 6)
    categories = sorted.map(item => item.security_type.replace('A股', '').replace('债券', '债'))
    values = sorted.map(item => (item.turnover_amount || 0) / 1e8)
  }
  
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: params => {
        const value = params[0].value
        const formatted = value >= 1e4 ? (value / 1e4).toFixed(2) + '万亿' : value.toFixed(2) + '亿'
        return `${params[0].name}<br/>成交额: ${formatted}`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: { rotate: 30, fontSize: 11 },
      axisTick: { alignWithLabel: true }
    },
    yAxis: {
      type: 'value',
      name: '亿元',
      axisLabel: {
        formatter: value => {
          if (value >= 1e4) return (value / 1e4).toFixed(0) + '万亿'
          if (value >= 1e8) return (value / 1e8).toFixed(0) + '亿'
          return value
        }
      }
    },
    series: [{
      type: 'bar',
      barWidth: '50%',
      data: values,
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#83bff6' },
          { offset: 0.5, color: '#188df0' },
          { offset: 1, color: '#188df0' }
        ]),
        borderRadius: [4, 4, 0, 0]
      },
      emphasis: {
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#2378f7' },
            { offset: 0.7, color: '#2378f7' },
            { offset: 1, color: '#83bff6' }
          ])
        }
      }
    }]
  }
}

function getAreaBarOption() {
  const top10 = [...szseAreaData.value]
    .sort((a, b) => b.total_turnover - a.total_turnover)
    .slice(0, 10)
  
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: params => {
        const value = (params[0].value / 1e8).toFixed(2)
        return `${params[0].name}<br/>总交易额: ${value}亿元`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '5%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: top10.map(item => item.area),
      axisLabel: { rotate: 45, fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      name: '万亿元',
      axisLabel: {
        formatter: value => (value / 1e12).toFixed(1)
      }
    },
    series: [{
      type: 'bar',
      barWidth: '60%',
      data: top10.map(item => item.total_turnover),
      itemStyle: {
        color: '#5470c6',
        borderRadius: [4, 4, 0, 0]
      }
    }]
  }
}

function getSectorBarOption() {
  const top10 = [...szseSectorData.value]
    .sort((a, b) => b.turnover_amount_cny - a.turnover_amount_cny)
    .slice(0, 10)
  
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: params => {
        const value = (params[0].value / 1e8).toFixed(2)
        return `${params[0].name}<br/>成交额: ${value}亿元`
      }
    },
    grid: {
      left: '3%',
      right: '15%',
      bottom: '3%',
      top: '5%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: '亿元',
      axisLabel: {
        formatter: value => {
          if (value >= 1e8) return (value / 1e8).toFixed(0)
          return value
        }
      }
    },
    yAxis: {
      type: 'category',
      data: top10.map(item => item.sector_chinese).reverse(),
      axisLabel: { fontSize: 11 }
    },
    series: [{
      type: 'bar',
      barWidth: '60%',
      data: top10.map(item => item.turnover_amount_cny).reverse(),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
          { offset: 0, color: '#91cc75' },
          { offset: 1, color: '#5470c6' }
        ]),
        borderRadius: [0, 4, 4, 0]
      },
      label: {
        show: true,
        position: 'right',
        formatter: params => {
          const value = params.value / 1e8
          return value >= 1e4 ? (value / 1e4).toFixed(1) + '万亿' : value.toFixed(0) + '亿'
        },
        fontSize: 10
      }
    }]
  }
}

// ==================== 生命周期 ====================
onMounted(() => {
  loadData()
  
  const handleResize = () => {
    pieChartInstance?.resize()
    barChartInstance?.resize()
  }
  
  window.addEventListener('resize', handleResize)
  
  onUnmounted(() => {
    window.removeEventListener('resize', handleResize)
    pieChartInstance?.dispose()
    barChartInstance?.dispose()
  })
})
</script>

<style scoped>
.market-situation-container {
  padding: 16px;
  min-height: calc(100vh - 64px);
  background: #f5f5f5;
}

.filter-card {
  margin-bottom: 16px;
}

.update-time {
  color: #8c8c8c;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.summary-row {
  margin-bottom: 16px;
}

.summary-row .ant-col {
  margin-bottom: 16px;
}

.board-row {
  margin-bottom: 16px;
}

.board-item {
  padding: 12px;
  background: #f6ffed;
  border-left: 4px solid;
  border-radius: 4px;
  margin-bottom: 8px;
}

.board-name {
  font-weight: 600;
  font-size: 14px;
  color: #262626;
  margin-bottom: 8px;
}

.board-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 12px;
  color: #595959;
}

.board-stats span {
  white-space: nowrap;
}

.charts-row {
  margin-bottom: 16px;
}

.charts-row .ant-col {
  margin-bottom: 16px;
}

.chart-card {
  height: 400px;
}

.chart-container {
  width: 100%;
  height: 360px;
}

.table-card {
  margin-bottom: 16px;
}

.cell-bold {
  font-weight: 600;
  color: #262626;
}

.value-high {
  color: #f5222d;
  font-weight: 600;
}

.value-normal {
  color: #52c41a;
}

.value-up {
  color: #f5222d;
}

.value-down {
  color: #52c41a;
}

/* 错误容器 */
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  gap: 16px;
}

/* 响应式 */
@media (max-width: 768px) {
  .market-situation-container {
    padding: 8px;
  }
  
  .chart-card {
    height: 320px;
  }
  
  .chart-container {
    height: 280px;
  }
  
  .board-stats {
    flex-direction: column;
    gap: 4px;
  }
}

/* 暗色模式 */
html[data-theme='dark'] .market-situation-container {
  background: #141414;
}

html[data-theme='dark'] .board-item {
  background: rgba(255, 255, 255, 0.04);
}
</style>
