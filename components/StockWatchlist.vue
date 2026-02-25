<template>
  <div class="stock-watchlist">
    <a-card :bordered="false" class="watchlist-card">
      <template #title>
        <div class="card-header">
          <div class="header-left">
            <StarOutlined class="watchlist-icon" />
            <span class="card-title">我的自选</span>
            <a-tag color="blue">{{ watchlistData.length }} 只</a-tag>
          </div>
          <a-space>
            <a-button @click="showAddModal = true">
              <template #icon><PlusOutlined /></template>
              添加自选
            </a-button>
            <a-button @click="showAlertModal = true">
              <template #icon><BellOutlined /></template>
              提醒设置
            </a-button>
            <a-button type="primary" @click="handleRefresh" :loading="loading">
              <template #icon><ReloadOutlined /></template>
              刷新
            </a-button>
          </a-space>
        </div>
      </template>

      <!-- 自选统计 -->
      <a-row :gutter="16" class="stats-row" v-if="watchlistData.length > 0">
        <a-col :xs="12" :sm="6">
          <a-statistic title="上涨" :value="upCount" :value-style="{ color: '#ff4d4f' }">
            <template #suffix>
              <ArrowUpOutlined />
            </template>
          </a-statistic>
        </a-col>
        <a-col :xs="12" :sm="6">
          <a-statistic title="下跌" :value="downCount" :value-style="{ color: '#52c41a' }">
            <template #suffix>
              <ArrowDownOutlined />
            </template>
          </a-statistic>
        </a-col>
        <a-col :xs="12" :sm="6">
          <a-statistic title="平均涨跌幅" :value="avgChange" :precision="2" :value-style="avgChangeStyle">
            <template #suffix>% </suffix>
          </a-statistic>
        </a-col>
        <a-col :xs="12" :sm="6">
          <a-statistic title="最后更新" :value="lastUpdateTime" />
        </a-col>
      </a-row>

      <a-divider v-if="watchlistData.length > 0" />

      <!-- 自选列表表格 -->
      <a-table
        :columns="columns"
        :data-source="watchlistData"
        :loading="loading"
        :pagination="paginationConfig"
        :scroll="{ x: 1200 }"
        row-key="代码"
        size="middle"
        :locale="{ emptyText: '暂无自选股票，点击上方按钮添加' }"
      >
        <template #bodyCell="{ column, record, text }">
          <template v-if="column.dataIndex === '最新价'">
            <span :class="getPriceChangeClass(record)">
              {{ formatPrice(text) }}
            </span>
          </template>

          <template v-else-if="column.dataIndex === '涨跌幅'">
            <span :class="getChangeClass(text)">
              {{ formatChange(text) }}
            </span>
          </template>

          <template v-else-if="column.dataIndex === '涨跌额'">
            <span :class="getChangeClass(text)">
              {{ formatChangeAmount(text) }}
            </span>
          </template>

          <template v-else-if="column.dataIndex === '换手率'">
            <span>{{ formatPercent(text) }}</span>
          </template>

          <template v-else-if="column.dataIndex === '总市值' || column.dataIndex === '流通市值'">
            <span>{{ formatAmount(text) }}</span>
          </template>

          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="handleViewDetail(record)">
                <template #icon><EyeOutlined /></template>
                详情
              </a-button>
              <a-popconfirm
                title="确定要从自选列表中删除这只股票吗？"
                @confirm="handleDelete(record)"
                ok-text="确定"
                cancel-text="取消"
              >
                <a-button type="link" danger size="small">
                  <template #icon><DeleteOutlined /></template>
                  删除
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>

          <template v-else-if="column.key === 'alert'">
            <a-badge
              v-if="hasAlert(record)"
              :dot="true"
              :color="isAlertTriggered(record) ? '#ff4d4f' : '#1890ff'"
            >
              <a-tag size="small" :color="isAlertTriggered(record) ? 'error' : 'processing'">
                {{ getAlertText(record) }}
              </a-tag>
            </a-badge>
            <span v-else class="no-alert">-</span>
          </template>
        </template>
      </a-table>

      <!-- 自动刷新提示 -->
      <a-alert
        v-if="watchlistData.length > 0"
        class="auto-refresh-tip"
        type="info"
        show-icon
        :message="`数据每 30 秒自动刷新，下次刷新倒计时: ${countdown} 秒`"
      />
    </a-card>

    <!-- 添加自选弹窗 -->
    <a-modal
      v-model:visible="showAddModal"
      title="添加自选股票"
      width="700px"
      :footer="null"
      destroy-on-close
    >
      <a-input
        v-model:value="searchStockKeyword"
        placeholder="输入股票代码或名称搜索"
        allow-clear
        @change="handleStockSearch"
        style="margin-bottom: 16px;"
      >
        <template #prefix>
          <SearchOutlined />
        </template>
      </a-input>

      <a-table
        :columns="searchColumns"
        :data-source="searchResults"
        :loading="searchLoading"
        :pagination="{ pageSize: 5 }"
        size="small"
        row-key="代码"
        :locale="{ emptyText: searchStockKeyword ? '未找到匹配的股票' : '请输入关键词搜索' }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action'">
            <a-button
              type="primary"
              size="small"
              :disabled="isInWatchlist(record['代码'])"
              @click="handleAddStock(record)"
            >
              <template #icon><PlusOutlined /></template>
              {{ isInWatchlist(record['代码']) ? '已添加' : '添加' }}
            </a-button>
          </template>

          <template v-else-if="column.dataIndex === '涨跌幅'">
            <span :class="getChangeClass(record['涨跌幅'])">
              {{ formatChange(record['涨跌幅']) }}
            </span>
          </template>
        </template>
      </a-table>
    </a-modal>

    <!-- 提醒设置弹窗 -->
    <a-modal
      v-model:visible="showAlertModal"
      title="涨跌幅提醒设置"
      width="600px"
      @ok="handleSaveAlertSettings"
      ok-text="保存"
      cancel-text="取消"
    >
      <a-form :model="alertForm" layout="vertical">
        <a-form-item label="监控股票">
          <a-select
            v-model:value="alertForm.selectedStocks"
            mode="multiple"
            placeholder="选择要设置提醒的股票"
            style="width: 100%"
          >
            <a-select-option v-for="stock in watchlistData" :key="stock['代码']" :value="stock['代码']">
              {{ stock['名称'] }} ({{ stock['代码'] }})
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="涨幅提醒阈值 (%)">
              <a-input-number
                v-model:value="alertForm.upThreshold"
                :min="0"
                :max="100"
                :precision="2"
                style="width: 100%"
                placeholder="如: 5.00"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="跌幅提醒阈值 (%)">
              <a-input-number
                v-model:value="alertForm.downThreshold"
                :min="0"
                :max="100"
                :precision="2"
                style="width: 100%"
                placeholder="如: 5.00"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="提醒方式">
          <a-checkbox-group v-model:value="alertForm.notifyMethods"
          >
            <a-checkbox value="browser">浏览器通知</a-checkbox>
            <a-checkbox value="email">邮件提醒</a-checkbox>
            <a-checkbox value="sms">短信提醒</a-checkbox>
          </a-checkbox-group>
        </a-form-item>
      </a-form>

      <a-divider />

      <h4>当前提醒设置</h4>
      <a-list
        :data-source="alertSettings"
        size="small"
        :locale="{ emptyText: '暂无提醒设置' }"
      >
        <template #renderItem="{ item }">
          <a-list-item>
            <a-list-item-meta
              :title="`${item.name} (${item.code})`"
              :description="`上涨 ≥ ${item.upThreshold}% 或 下跌 ≥ ${item.downThreshold}%`"
            />
            <template #actions>
              <a-button type="link" danger size="small" @click="removeAlertSetting(item.code)">
                删除
              </a-button>
            </template>
          </a-list-item>
        </template>
      </a-list>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  StarOutlined,
  PlusOutlined,
  ReloadOutlined,
  DeleteOutlined,
  EyeOutlined,
  SearchOutlined,
  BellOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined
} from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import axios from '@/utils/axios'
import { debounce } from 'lodash-es'

const router = useRouter()

// 状态
const loading = ref(false)
const searchLoading = ref(false)
const showAddModal = ref(false)
const showAlertModal = ref(false)
const searchStockKeyword = ref('')
const searchResults = ref([])
const watchlistData = ref([])
const lastUpdateTime = ref('-')
const countdown = ref(30)

// 提醒设置
const alertForm = ref({
  selectedStocks: [],
  upThreshold: 5,
  downThreshold: 5,
  notifyMethods: ['browser']
})
const alertSettings = ref([])

// 分页配置
const paginationConfig = ref({
  pageSize: 20,
  showSizeChanger: true,
  pageSizeOptions: ['10', '20', '50'],
  showQuickJumper: true,
  showTotal: (total) => `共 ${total} 只自选`,
  total: 0
})

// 表格列定义
const columns = [
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
    align: 'right'
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
    align: 'right'
  },
  {
    title: '换手率',
    dataIndex: '换手率',
    width: 90,
    align: 'right',
    sorter: (a, b) => a['换手率'] - b['换手率']
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
    align: 'right'
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
    align: 'right'
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
    align: 'right'
  },
  {
    title: '提醒',
    key: 'alert',
    width: 100,
    align: 'center'
  },
  {
    title: '操作',
    key: 'action',
    width: 150,
    fixed: 'right',
    align: 'center'
  }
]

// 搜索表格列
const searchColumns = [
  {
    title: '代码',
    dataIndex: '代码',
    width: 100,
    align: 'center'
  },
  {
    title: '名称',
    dataIndex: '名称',
    width: 120,
    align: 'center'
  },
  {
    title: '最新价',
    dataIndex: '最新价',
    width: 100,
    align: 'right'
  },
  {
    title: '涨跌幅',
    dataIndex: '涨跌幅',
    width: 100,
    align: 'right'
  },
  {
    title: '操作',
    key: 'action',
    width: 100,
    align: 'center'
  }
]

// 计算属性：统计
const upCount = computed(() => {
  return watchlistData.value.filter(item => item['涨跌幅'] > 0).length
})

const downCount = computed(() => {
  return watchlistData.value.filter(item => item['涨跌幅'] < 0).length
})

const avgChange = computed(() => {
  if (watchlistData.value.length === 0) return 0
  const sum = watchlistData.value.reduce((acc, item) => acc + (item['涨跌幅'] || 0), 0)
  return sum / watchlistData.value.length
})

const avgChangeStyle = computed(() => {
  if (avgChange.value > 0) return { color: '#ff4d4f' }
  if (avgChange.value < 0) return { color: '#52c41a' }
  return { color: '#8c8c8c' }
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

const formatPercent = (value) => {
  if (value === null || value === undefined) return '-'
  return `${value.toFixed(2)}%`
}

const formatAmount = (value) => {
  if (value === null || value === undefined) return '-'
  const yi = value / 100000000
  if (yi >= 10000) {
    return `${(yi / 10000).toFixed(2)}万亿`
  }
  return `${yi.toFixed(2)}亿`
}

// 样式类
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

// 检查是否在自选列表
const isInWatchlist = (code) => {
  return watchlistData.value.some(item => item['代码'] === code)
}

// 提醒相关
const hasAlert = (record) => {
  return alertSettings.value.some(alert => alert.code === record['代码'])
}

const isAlertTriggered = (record) => {
  const alert = alertSettings.value.find(a => a.code === record['代码'])
  if (!alert) return false
  const change = record['涨跌幅']
  return change >= alert.upThreshold || change <= -alert.downThreshold
}

const getAlertText = (record) => {
  const alert = alertSettings.value.find(a => a.code === record['代码'])
  if (!alert) return ''
  return `涨≥${alert.upThreshold}% 跌≥${alert.downThreshold}%`
}

// 获取自选列表
const fetchWatchlist = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/stock/watchlist')
    // 后端返回的是自选股票代码列表，需要获取实时数据
    const codes = response.data || []
    
    if (codes.length > 0) {
      // 获取这些股票的实时数据
      const realtimeResponse = await axios.get('/api/stock/realtime')
      const allStocks = realtimeResponse.data || []
      
      watchlistData.value = allStocks.filter(stock => 
        codes.some(code => code.code === stock['代码'])
      )
      
      // 合并自选的额外信息
      watchlistData.value = watchlistData.value.map(stock => {
        const watchInfo = codes.find(c => c.code === stock['代码'])
        return {
          ...stock,
          watchId: watchInfo?.id,
          addedAt: watchInfo?.addedAt
        }
      })
    } else {
      watchlistData.value = []
    }
    
    paginationConfig.value.total = watchlistData.value.length
    lastUpdateTime.value = dayjs().format('HH:mm:ss')
  } catch (error) {
    message.error('获取自选列表失败：' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 搜索股票
const handleStockSearch = debounce(async () => {
  if (!searchStockKeyword.value.trim()) {
    searchResults.value = []
    return
  }
  
  searchLoading.value = true
  try {
    const response = await axios.get('/api/stock/search', {
      params: { keyword: searchStockKeyword.value }
    })
    searchResults.value = response.data || []
  } catch (error) {
    message.error('搜索失败：' + (error.message || '未知错误'))
  } finally {
    searchLoading.value = false
  }
}, 300)

// 添加股票到自选
const handleAddStock = async (record) => {
  try {
    await axios.post('/api/stock/watchlist', {
      code: record['代码'],
      name: record['名称']
    })
    message.success(`添加成功: ${record['名称']}(${record['代码']})`)
    // 刷新列表
    await fetchWatchlist()
  } catch (error) {
    message.error('添加失败：' + (error.message || '未知错误'))
  }
}

// 删除自选
const handleDelete = async (record) => {
  try {
    await axios.delete(`/api/stock/watchlist/${record['代码']}`)
    message.success(`已删除: ${record['名称']}(${record['代码']})`)
    await fetchWatchlist()
  } catch (error) {
    message.error('删除失败：' + (error.message || '未知错误'))
  }
}

// 查看详情
const handleViewDetail = (record) => {
  router.push(`/stock/detail/${record['代码']}`)
}

// 刷新
const handleRefresh = async () => {
  await fetchWatchlist()
  message.success('数据已刷新')
  countdown.value = 30
}

// 保存提醒设置
const handleSaveAlertSettings = () => {
  const newSettings = alertForm.value.selectedStocks.map(code => {
    const stock = watchlistData.value.find(s => s['代码'] === code)
    return {
      code,
      name: stock?.['名称'] || code,
      upThreshold: alertForm.value.upThreshold,
      downThreshold: alertForm.value.downThreshold,
      notifyMethods: alertForm.value.notifyMethods
    }
  })
  
  // 合并设置，避免重复
  const existingCodes = alertSettings.value.map(s => s.code)
  const uniqueNewSettings = newSettings.filter(s => !existingCodes.includes(s.code))
  alertSettings.value = [...alertSettings.value, ...uniqueNewSettings]
  
  message.success('提醒设置已保存')
  showAlertModal.value = false
  
  // 重置表单
  alertForm.value.selectedStocks = []
}

// 删除提醒设置
const removeAlertSetting = (code) => {
  alertSettings.value = alertSettings.value.filter(s => s.code !== code)
  message.success('提醒设置已删除')
}

// 自动刷新
let autoRefreshTimer = null
let countdownTimer = null

const startAutoRefresh = () => {
  autoRefreshTimer = setInterval(() => {
    fetchWatchlist()
    countdown.value = 30
  }, 30000)
  
  countdownTimer = setInterval(() => {
    if (countdown.value > 0) {
      countdown.value--
    }
  }, 1000)
}

const stopAutoRefresh = () => {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer)
    autoRefreshTimer = null
  }
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
}

// 检查提醒
const checkAlerts = () => {
  alertSettings.value.forEach(alert => {
    const stock = watchlistData.value.find(s => s['代码'] === alert.code)
    if (stock && isAlertTriggered(stock)) {
      const change = stock['涨跌幅']
      const direction = change > 0 ? '上涨' : '下跌'
      
      if (alert.notifyMethods.includes('browser') && Notification.permission === 'granted') {
        new Notification('股票提醒', {
          body: `${stock['名称']}(${stock['代码']}) ${direction} ${Math.abs(change).toFixed(2)}%`,
          icon: '/favicon.ico'
        })
      }
    }
  })
}

onMounted(() => {
  fetchWatchlist()
  startAutoRefresh()
  
  // 请求浏览器通知权限
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission()
  }
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped lang="less">
.stock-watchlist {
  padding: 16px;
  
  .watchlist-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      
      .header-left {
        display: flex;
        align-items: center;
        gap: 8px;
        
        .watchlist-icon {
          color: #faad14;
          font-size: 20px;
        }
        
        .card-title {
          font-size: 16px;
          font-weight: 600;
        }
      }
    }
    
    .stats-row {
      margin-bottom: 8px;
      
      :deep(.ant-statistic-title) {
        font-size: 12px;
        color: #8c8c8c;
      }
      
      :deep(.ant-statistic-content) {
        font-size: 24px;
        font-weight: 600;
      }
    }
    
    .auto-refresh-tip {
      margin-top: 16px;
    }
    
    :deep(.ant-table-row) {
      cursor: pointer;
      
      &:hover {
        background-color: #f0f5ff;
      }
    }
    
    :deep(.ant-empty-description) {
      color: #8c8c8c;
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
  
  .no-alert {
    color: #bfbfbf;
  }
}

// 响应式调整
@media (max-width: 768px) {
  .stock-watchlist {
    padding: 8px;
    
    .card-header {
      flex-direction: column;
      align-items: flex-start;
      
      .ant-space {
        width: 100%;
        justify-content: flex-start;
      }
    }
    
    .stats-row {
      .ant-col {
        margin-bottom: 12px;
      }
    }
  }
}
</style>