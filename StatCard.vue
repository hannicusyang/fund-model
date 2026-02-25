<template>
  <a-card class="stat-card" :bordered="false" :body-style="{ padding: '20px' }">
    <div class="stat-header">
      <div class="stat-icon" :style="{ backgroundColor: color + '15', color }">
        <span class="icon-text">{{ icon }}</span>
      </div>
      <div v-if="trend !== 0" class="stat-trend" :class="trend > 0 ? 'trend-up' : 'trend-down'">
        <ArrowUpOutlined v-if="trend > 0" />
        <ArrowDownOutlined v-else />
        <span>{{ Math.abs(trend).toFixed(2) }}%</span>
      </div>
    </div>
    
    <div class="stat-content">
      <div class="stat-value" :title="formattedValue">
        {{ displayValue }}
      </div>
      <div class="stat-unit">{{ unit }}</div>
    </div>
    
    <div class="stat-title">{{ title }}</div>
    
    <!-- 迷你趋势图 -->
    <div v-if="sparklineData.length" class="stat-sparkline">
      <div ref="sparklineRef" class="sparkline-container"></div>
    </div>
  </a-card>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons-vue'
import * as echarts from 'echarts'

const props = defineProps({
  title: { type: String, required: true },
  value: { type: Number, default: 0 },
  unit: { type: String, default: '' },
  precision: { type: Number, default: 2 },
  trend: { type: Number, default: 0 },
  icon: { type: String, default: '📊' },
  color: { type: String, default: '#1890ff' },
  sparklineData: { type: Array, default: () => [] }
})

const sparklineRef = ref(null)
let sparklineChart = null

// 格式化数值
const formattedValue = computed(() => {
  if (props.value == null || isNaN(props.value)) return '--'
  return props.value.toLocaleString('zh-CN', {
    minimumFractionDigits: props.precision,
    maximumFractionDigits: props.precision
  })
})

// 显示的数值（缩写）
const displayValue = computed(() => {
  const val = props.value
  if (val == null || isNaN(val)) return '--'
  
  // 大数值缩写
  if (Math.abs(val) >= 1e12) {
    return (val / 1e12).toFixed(props.precision)
  } else if (Math.abs(val) >= 1e8) {
    return (val / 1e8).toFixed(props.precision)
  } else if (Math.abs(val) >= 1e4) {
    return (val / 1e4).toFixed(props.precision)
  }
  return val.toFixed(props.precision)
})

// 初始化迷你趋势图
function initSparkline() {
  if (!sparklineRef.value || !props.sparklineData.length) return
  
  if (!sparklineChart) {
    sparklineChart = echarts.init(sparklineRef.value)
  }
  
  const option = {
    grid: {
      left: 0,
      right: 0,
      top: 2,
      bottom: 2
    },
    xAxis: {
      type: 'category',
      show: false,
      data: props.sparklineData.map((_, i) => i)
    },
    yAxis: {
      type: 'value',
      show: false,
      min: Math.min(...props.sparklineData) * 0.95,
      max: Math.max(...props.sparklineData) * 1.05
    },
    series: [{
      type: 'line',
      data: props.sparklineData,
      smooth: true,
      symbol: 'none',
      lineStyle: {
        color: props.color,
        width: 2
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: props.color + '40' },
            { offset: 1, color: props.color + '05' }
          ]
        }
      }
    }]
  }
  
  sparklineChart.setOption(option)
}

// 监听数据变化
watch(() => props.sparklineData, () => {
  if (props.sparklineData.length) {
    initSparkline()
  }
}, { immediate: true })

onMounted(() => {
  if (props.sparklineData.length) {
    initSparkline()
  }
  
  const handleResize = () => sparklineChart?.resize()
  window.addEventListener('resize', handleResize)
  
  onUnmounted(() => {
    window.removeEventListener('resize', handleResize)
    sparklineChart?.dispose()
  })
})
</script>

<style scoped>
.stat-card {
  height: 100%;
  transition: all 0.3s ease;
  cursor: pointer;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.icon-text {
  font-size: 24px;
  line-height: 1;
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 4px;
}

.trend-up {
  color: #f5222d;
  background: rgba(245, 34, 45, 0.1);
}

.trend-down {
  color: #52c41a;
  background: rgba(82, 196, 26, 0.1);
}

.stat-content {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #262626;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stat-unit {
  font-size: 14px;
  color: #8c8c8c;
  font-weight: 400;
}

.stat-title {
  font-size: 14px;
  color: #8c8c8c;
  font-weight: 400;
}

.stat-sparkline {
  margin-top: 12px;
  height: 40px;
}

.sparkline-container {
  width: 100%;
  height: 100%;
}

/* 暗色模式 */
html[data-theme='dark'] .stat-value {
  color: rgba(255, 255, 255, 0.85);
}

html[data-theme='dark'] .stat-title {
  color: rgba(255, 255, 255, 0.45);
}

html[data-theme='dark'] .stat-unit {
  color: rgba(255, 255, 255, 0.45);
}

@media (max-width: 768px) {
  .stat-value {
    font-size: 22px;
  }
  
  .stat-icon {
    width: 40px;
    height: 40px;
  }
  
  .icon-text {
    font-size: 20px;
  }
}
</style>
