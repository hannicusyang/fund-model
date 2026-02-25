<template>
  <div class="stock-market-list">
    <a-card :bordered="false" class="search-card">
      <template #title>
        <div class="card-header">
          <span class="card-title">股票实时行情</span>
          <a-space>
            <a-button type="primary" @click="handleRefresh" :loading="loading">
              <template #icon><ReloadOutlined /></template>
              刷新
            </a-button>
          </a-space>
        </div>
      </template>
      
      <a-row :gutter="16" class="search-row">
        <a-col :xs="24" :sm="12" :md="8" :lg="6">
          <a-input
            v-model:value="searchKeyword"
            placeholder="输入股票代码或名称搜索"
            allow-clear
            @press-enter="handleSearch"
          >
            <template #prefix>
              <SearchOutlined />
            </template>
          </a-input>
        </a-col>
        <a-col :xs="24" :sm="12" :md="8" :lg="6">
          <a-space>
            <a-button type="primary" @click="handleSearch">搜索</a-button>
            <a-button @click="handleReset">重置</a-button>
          </a-space>
        </a-col>
      </a-row>
    </a-card>

    <a-card :bordered="false" class="table-card" style="margin-top: 16px;">
      <a-table
        :columns="columns"
        :data-source="filteredData"
        :loading="loading"
        :pagination="paginationConfig"
        :scroll="{ x: 1500 }"
        row-key="代码"
        size="middle"
        @change="handleTableChange"
        @row-click="handleRowClick"
      >
        <!-- 涨跌幅列 -->
        <template #bodyCell="{ column, record, text }">
          <template v-if="column.dataIndex === '涨跌幅'">
            <span :class="getChangeClass(text)">
              {{ formatChange(text) }}
            </span>
          </template>
          
          <template v-else-if="column.dataIndex === '涨跌额'">
            <span :class="getChangeClass(text)">
              {{ formatChangeAmount(text) }}
            </span>
          </template>

          <template v-else-if="column.dataIndex === '最新价'">
            <span :class="getPriceChangeClass(record)">
              {{ formatPrice(text) }}
            </span>
          </template>

          <template v-else-if="column.dataIndex === '成交额'">
            <span>{{ formatAmount(text) }}</span>
          </template>

          <template v-else-if="column.dataIndex === '总市值' || column.dataIndex === '流通市值'">
            <span>{{ formatAmount(text) }}</span>
          </template>

          <template v-else-if="column.dataIndex === '成交量'">
            <span>{{ formatVolume(text) }}</span>
          </template>

          <template v-else-if="column.dataIndex === '5分钟涨跌' || column.dataIndex === '60日涨跌幅' || column.dataIndex === '年初至今涨跌幅'">
            <span :class="getChangeClass(text)">
              {{ formatPercent(text) }}
            </span>
          </template>

          <template v-else-if="column.dataIndex === '换手率' || column.dataIndex === '振幅' || column.dataIndex === '市盈率-动态'">
            <span>{{ formatPercent(text, column.dataIndex === '市盈率-动态' ? false : true) }}</span>
          </template>

          <template v-else-if="column.dataIndex === '涨速'">
            <span :class="getChangeClass(text)">
              {{ formatChangeSpeed(text) }}
            </span>
          </template>

          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click.stop="handleAddToWatchlist(record)">
                <template #icon><StarOutlined /></template>
                加自选
              </a-button>
              <a-button type="link" size="small" @click.stop="handleViewDetail(record)">
                详情
              </a-button>
            </a-space>
          </template>

          <template v-else-if="column.dataIndex === 'sparkline'">
            <div class="sparkline-container">
              <div :id="`sparkline-${record['代码']}`" class="sparkline"></div>
            </div>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { SearchOutlined, ReloadOutlined, StarOutlined } from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import axios from '@/utils/axios'
import * as echarts from 'echarts'

const router = useRouter()

// 状态
const loading = ref(false)
const searchKeyword = ref('')
const stockData = ref([])
const sparklineCharts = ref({})

// 分页配置
const paginationConfig = ref({
  current: 1,
  pageSize: 50,
  pageSizeOptions: ['20', '50', '100'],
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total) => `共 ${total} 条`,
  total: 0
})

// 表格列定义
const columns = [
  {
    title: '序号',
    dataIndex: '序号',
    width: 60,
    fixed: 'left',
    align: 'center'
  },
  {
    title: '代码',
    dataIndex: '代码',
    width: 100,
    fixed: 'left',
    align: 'center'
  },
  {
    title: '名称',
    dataIndex: '名称',
    width: 120,
    fixed: 'left',
    align: 'center'
  },
  {
    title: '最新价',
    dataIndex: '最新价',
    width: 100,
    align: 'right',
    sorter: (a, b) => a['最新价'] - b['最新价']
  },
  {
    title: '涨跌幅',
    dataIndex: '涨跌幅',
    width: 100,
    align: 'right',
    sorter: (a, b) => a['涨跌幅'] - b['涨跌幅']
  },
  {
    title: '涨跌额',
    dataIndex: '涨跌额',
    width: 100,
    align: 'right',
    sorter: (a, b) => a['涨跌额'] - b['涨跌额']
  },
  {
    title: '成交量',
    dataIndex: '成交量',
    width: 100,
    align: 'right',
    sorter: (a, b) => a['成交量'] - b['成交量']
  },
  {
    title: '成交额',
    dataIndex: '成交额',
    width: 100,
    align: 'right',
    sorter: (a, b) => a['成交额'] - b['成交额']
  },
  {
    title: '振幅',
    dataIndex: '振幅',
    width: 80,
    align: 'right',
    sorter: (a, b) => a['振幅'] - b['振幅']
  },
  {
    title: '最高',
    dataIndex: '最高',
    width: 90,
    align: 'right',
    sorter: (a, b) => a['最高'] - b['最高']
  },
  {
    title: '最低',
    dataIndex: '最低',
    width: 90,
    align: 'right',
    sorter: (a, b) => a['最低'] - b['最低']
  },
  {
    title: '今开',
    dataIndex: '今开',
    width: 90,
    align: 'right',
    sorter: (a, b) => a['今开'] - b['今开']
  },
  {
    title: '昨收',
    dataIndex: '昨收',
    width: 90,
    align: 'right',
    sorter: (a, b) => a['昨收'] - b['昨收']
  },
  {
    title: '量比',
    dataIndex: '量比',
    width: 80,
    align: 'right',
    sorter: (a, b) => a['量比'] - b['量比']
  },
  {
    title: '换手率',
    dataIndex: '换手率',
    width: 90,
    align: 'right',
    sorter: (a, b) => a['换手率'] - b['换手率']
  },
  {
    title: '市盈率',
    dataIndex: '市盈率-动态',
    width: 90,
    align: 'right',
    sorter: (a, b) => (a['市盈率-动态'] || 0) - (b['市盈率-动态'] || 0)
  },
  {
    title: '市净率',
    dataIndex: '市净率',
    width: 90,
    align: 'right',
    sorter: (a, b) => (a['市净率'] || 0) - (b['市净率'] || 0)
  },
  {
    title: '总市值',
    dataIndex: '总市值',
    width: 100,
    align: 'right',
    sorter: (a, b) => a['总市值'] - b['总市值']
  },
  {
    title: '流通市值',
    dataIndex: '流通市值',
    width: 100,
    align: 'right',
    sorter: (a, b) => a['流通市值'] - b['流通市值']
  },
  {
    title: '涨速',
    dataIndex: '涨速',
    width: 80,
    align: 'right',
    sorter: (a, b) => a['涨速'] - b['涨速']
  },
  {
    title: '5分钟涨跌',
    dataIndex: '5分钟涨跌',
    width: 110,
    align: 'right',
    sorter: (a, b) => a['5分钟涨跌'] - b['5分钟涨跌']
  },
  {
    title: '60日涨跌',
    dataIndex: '60日涨跌幅',
    width: 110,
    align: 'right',
    sorter: (a, b) => a['60日涨跌幅'] - b['60日涨跌幅']
  },
  {
    title: '年初至今',
    dataIndex: '年初至今涨跌幅',
    width: 110,
    align: 'right',
    sorter: (a, b) => a['年初至今涨跌幅'] - b['年初至今涨跌幅']
  },
  {
    title: '走势',
    dataIndex: 'sparkline',
    width: 120,
    align: 'center',
    fixed: 'right'
  },
  {
    title: '操作',
    key: 'action',
    width: 150,
    fixed: 'right',
    align: 'center'
  }
]

// 过滤后的数据
const filteredData = computed(() => {
  if (!searchKeyword.value) {
    return stockData.value
  }
  const keyword = searchKeyword.value.toLowerCase()
  return stockData.value.filter(item => 
    item['代码'].toLowerCase().includes(keyword) ||
    item['名称'].toLowerCase().includes(keyword)
  )
})

// 格式化函数
const formatPrice = (value) => {
  if (value === null || value === undefined) return '-'
  return value.toFixed(2)
}

const formatChange = (value) => {
  if (value === null || value === undefined) return '-'
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}%`
}

const formatChangeAmount = (value) => {
  if (value === null || value === undefined) return '-'
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}`
}

const formatPercent = (value, addPercent = true) => {
  if (value === null || value === undefined || value === '-') return '-'
  const suffix = addPercent ? '%' : ''
  return `${value.toFixed(2)}${suffix}`
}

const formatChangeSpeed = (value) => {
  if (value === null || value === undefined) return '-'
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}`
}

const formatAmount = (value) => {
  if (value === null || value === undefined) return '-'
  const yi = value / 100000000
  if (yi >= 10000) {
    return `${(yi / 10000).toFixed(2)}万亿`
  }
  return `${yi.toFixed(2)}亿`
}

const formatVolume = (value) => {
  if (value === null || value === undefined) return '-'
  if (value >= 10000) {
    return `${(value / 10000).toFixed(2)}万手`
  }
  return `${value}手`
}

// 获取涨跌样式类
const getChangeClass = (value) => {
  if (value > 0) return 'stock-up'
  if (value < 0) return 'stock-down'
  return 'stock-flat'
}

const getPriceChangeClass = (record) => {
  const change = record['涨跌幅']
  if (change > 0) return 'stock-up'
  if (change < 0) return 'stock-down'
  return 'stock-flat'
}

// 获取股票数据
const fetchStockData = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/stock/realtime')
    stockData.value = response.data || []
    paginationConfig.value.total = stockData.value.length
    
    // 初始化迷你图
    nextTick(() => {
      initSparklines()
    })
  } catch (error) {
    message.error('获取股票数据失败：' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 初始化迷你走势图
const initSparklines = () => {
  // 清理旧的图表实例
  Object.values(sparklineCharts.value).forEach(chart => {
    chart.dispose()
  })
  sparklineCharts.value = {}
  
  // 为每行创建迷你图
  filteredData.value.slice(0, 20).forEach(record => {
    const chartId = `sparkline-${record['代码']}`
    const chartDom = document.getElementById(chartId)
    if (chartDom) {
      const chart = echarts.init(chartDom)
      const option = generateSparklineOption(record)
      chart.setOption(option)
      sparklineCharts.value[record['代码']] = chart
    }
  })
}

// 生成迷你图配置
const generateSparklineOption = (record) => {
  // 模拟历史数据用于展示
  const data = generateMockHistory(record)
  const isUp = record['涨跌幅'] >= 0
  
  return {
    grid: {
      left: 0,
      right: 0,
      top: 2,
      bottom: 2
    },
    xAxis: {
      type: 'category',
      show: false,
      data: data.map((_, i) => i)
    },
    yAxis: {
      type: 'value',
      show: false,
      min: Math.min(...data),
      max: Math.max(...data)
    },
    series: [{
      type: 'line',
      data: data,
      smooth: true,
      symbol: 'none',
      lineStyle: {
        width: 1.5,
        color: isUp ? '#ff4d4f' : '#52c41a'
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: isUp ? 'rgba(255,77,79,0.3)' : 'rgba(82,196,26,0.3)' },
            { offset: 1, color: isUp ? 'rgba(255,77,79,0.05)' : 'rgba(82,196,26,0.05)' }
          ]
        }
      }
    }],
    tooltip: { show: false }
  }
}

// 生成模拟历史数据
const generateMockHistory = (record) => {
  const basePrice = record['昨收'] || record['最新价']
  const volatility = basePrice * 0.02
  const data = []
  let currentPrice = basePrice
  
  for (let i = 0; i < 30; i++) {
    const change = (Math.random() - 0.5) * volatility
    currentPrice += change
    data.push(currentPrice)
  }
  // 确保最后一个点接近最新价
  data[data.length - 1] = record['最新价']
  return data
}

// 搜索
const handleSearch = () => {
  paginationConfig.value.current = 1
}

// 重置
const handleReset = () => {
  searchKeyword.value = ''
  paginationConfig.value.current = 1
}

// 刷新
const handleRefresh = () => {
  fetchStockData()
  message.success('数据已刷新')
}

// 表格变化
const handleTableChange = (pagination) => {
  paginationConfig.value.current = pagination.current
  paginationConfig.value.pageSize = pagination.pageSize
  nextTick(() => {
    initSparklines()
  })
}

// 行点击
const handleRowClick = (record) => {
  handleViewDetail(record)
}

// 查看详情
const handleViewDetail = (record) => {
  router.push(`/stock/detail/${record['代码']}`)
}

// 添加到自选
const handleAddToWatchlist = async (record) => {
  try {
    await axios.post('/api/stock/watchlist', {
      code: record['代码'],
      name: record['名称']
    })
    message.success(`已将 ${record['名称']}(${record['代码']}) 添加到自选`)
  } catch (error) {
    message.error('添加自选失败：' + (error.message || '未知错误'))
  }
}

// 自动刷新
let autoRefreshTimer = null
const startAutoRefresh = () => {
  autoRefreshTimer = setInterval(() => {
    fetchStockData()
  }, 30000) // 30秒刷新
}

const stopAutoRefresh = () => {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer)
    autoRefreshTimer = null
  }
}

onMounted(() => {
  fetchStockData()
  startAutoRefresh()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  stopAutoRefresh()
  window.removeEventListener('resize', handleResize)
  // 清理图表实例
  Object.values(sparklineCharts.value).forEach(chart => {
    chart.dispose()
  })
})

const handleResize = () => {
  Object.values(sparklineCharts.value).forEach(chart => {
    chart.resize()
  })
}
</script>

<style scoped lang="less">
.stock-market-list {
  padding: 16px;
  
  .search-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .card-title {
      font-size: 16px;
      font-weight: 600;
    }
    
    .search-row {
      margin-top: 8px;
    }
  }
  
  .table-card {
    :deep(.ant-table-cell) {
      white-space: nowrap;
    }
    
    :deep(.ant-table-row) {
      cursor: pointer;
      
      &:hover {
        background-color: #f0f5ff;
      }
    }
  }
  
  // 红涨绿跌样式
  .stock-up {
    color: #ff4d4f;
    font-weight: 500;
  }
  
  .stock-down {
    color: #52c41a;
    font-weight: 500;
  }
  
  .stock-flat {
    color: #8c8c8c;
  }
  
  .sparkline-container {
    width: 100px;
    height: 30px;
    
    .sparkline {
      width: 100%;
      height: 100%;
    }
  }
}

// 响应式调整
@media (max-width: 768px) {
  .stock-market-list {
    padding: 8px;
    
    .search-row {
      .ant-col {
        margin-bottom: 8px;
      }
    }
  }
}
</style>