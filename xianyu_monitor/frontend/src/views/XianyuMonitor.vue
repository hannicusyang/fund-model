<template>
  <div class="xianyu-monitor">
    <a-layout>
      <a-layout-header class="header">
        <div class="logo">
          <span class="logo-icon">🐟</span>
          <span>闲鱼监控系统</span>
        </div>
        <a-menu
          v-model:selectedKeys="activeMenu"
          theme="dark"
          mode="horizontal"
          :items="menuItems"
          @click="handleMenuClick"
        />
      </a-layout-header>
      
      <a-layout-content class="content">
        <!-- 监控商品列表 -->
        <div v-if="activeMenu[0] === 'products'" class="products-view">
          <a-row :gutter="16" class="toolbar">
            <a-col>
              <a-button type="primary" @click="showAddModal">
                <template #icon><PlusOutlined /></template>
                添加监控商品
              </a-button>
            </a-col>
            <a-col>
              <a-button @click="runAllCheck">
                <template #icon><SearchOutlined /></template>
                一键检查
              </a-button>
            </a-col>
          </a-row>
          
          <a-table
            :dataSource="products"
            :columns="productColumns"
            :rowKey="record => record.id"
            :pagination="{ pageSize: 10 }"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <a-tag :color="record.is_active ? 'green' : 'red'">
                  {{ record.is_active ? '监控中' : '已暂停' }}
                </a-tag>
              </template>
              <template v-if="column.key === 'discount'">
                <span>{{ (record.min_discount_rate * 100).toFixed(0) }}%</span>
              </template>
              <template v-if="column.key === 'actions'">
                <a-space>
                  <a-button size="small" @click="checkProduct(record.id)">检查</a-button>
                  <a-button size="small" @click="editProduct(record)">编辑</a-button>
                  <a-switch 
                    :checked="record.is_active" 
                    size="small"
                    @change="toggleProduct(record.id)"
                  />
                  <a-popconfirm
                    title="确定删除此监控商品？"
                    @confirm="deleteProduct(record.id)"
                  >
                    <a-button size="small" danger>
                      <DeleteOutlined />
                    </a-button>
                  </a-popconfirm>
                </a-space>
              </template>
            </template>
          </a-table>
        </div>
        
        <!-- 搜索结果 -->
        <div v-if="activeMenu[0] === 'results'" class="results-view">
          <a-row :gutter="16" class="toolbar">
            <a-col>
              <a-select
                v-model:value="selectedProduct"
                placeholder="选择监控商品"
                style="width: 200px"
                allowClear
              >
                <a-select-option v-for="p in products" :key="p.id" :value="p.id">
                  {{ p.name }}
                </a-select-option>
              </a-select>
            </a-col>
            <a-col>
              <a-button type="primary" @click="loadResults">
                加载结果
              </a-button>
            </a-col>
          </a-row>
          
          <div class="results-grid">
            <a-row :gutter="16">
              <a-col 
                v-for="item in results" 
                :key="item.id" 
                :xs="24" :sm="12" :md="8" :lg="6"
              >
                <a-card 
                  class="result-card"
                  :class="{ 'good-price': item.is_good_price, 'matched': item.image_match }"
                  hoverable
                >
                  <template #cover v-if="item.images">
                    <div class="item-image">
                      <img :src="JSON.parse(item.images || '[]')[0]" alt="商品图片" />
                      <div class="badges">
                        <a-tag v-if="item.is_good_price" color="red">好价</a-tag>
                        <a-tag v-if="item.image_match" color="blue">匹配</a-tag>
                      </div>
                    </div>
                  </template>
                  <a-card-meta>
                    <template #title>
                      <ellipsis :length="30">{{ item.title }}</ellipsis>
                    </template>
                    <template #description>
                      <div class="price-info">
                        <span class="price">¥{{ item.price }}</span>
                        <span class="original" v-if="item.original_price">
                          ¥{{ item.original_price }}
                        </span>
                      </div>
                      <div class="meta-info">
                        <span>{{ item.seller_nick }}</span>
                        <span>{{ item.location }}</span>
                      </div>
                    </template>
                  </a-card-meta>
                  <template #actions>
                    <a :href="item.url" target="_blank" title="查看详情">
                      <LinkOutlined />
                    </a>
                    <a @click.prevent="bookmarkItem(item.id)" title="收藏">
                      <StarOutlined :fill="item.is_bookmarked ? '#faad14' : ''" />
                    </a>
                    <a @click.prevent="lockItem(item.id)" title="锁定">
                      <LockOutlined v-if="!item.is_bookmarked" />
                      <LockFilled v-else />
                    </a>
                  </template>
                </a-card>
              </a-col>
            </a-row>
          </div>
        </div>
        
        <!-- 收藏/锁定商品 -->
        <div v-if="activeMenu[0] === 'bookmarked'" class="bookmarked-view">
          <h3>已收藏/锁定的商品</h3>
          <a-row :gutter="16" v-if="bookmarkedItems.length">
            <a-col 
              v-for="item in bookmarkedItems" 
              :key="item.id" 
              :xs="24" :sm="12" :md="8" :lg="6"
            >
              <a-card class="result-card bookmarked" hoverable>
                <template #cover v-if="item.images">
                  <div class="item-image">
                    <img :src="JSON.parse(item.images || '[]')[0]" alt="商品图片" />
                  </div>
                </template>
                <a-card-meta>
                  <template #title>
                    <ellipsis :length="30">{{ item.title }}</ellipsis>
                  </template>
                  <template #description>
                    <div class="price-info">
                      <span class="price">¥{{ item.price }}</span>
                    </div>
                  </template>
                </a-card-meta>
              </a-card>
            </a-col>
          </a-row>
          <a-empty v-else description="暂无收藏商品" />
        </div>
        
        <!-- 系统状态 -->
        <div v-if="activeMenu[0] === 'status'" class="status-view">
          <a-row :gutter="16">
            <a-col :span="8">
              <a-statistic 
                title="监控商品数" 
                :value="status.total_products" 
              />
            </a-col>
            <a-col :span="8">
              <a-statistic 
                title="活跃监控" 
                :value="status.active_products" 
              />
            </a-col>
            <a-col :span="8">
              <a-statistic 
                title="收藏商品" 
                :value="status.bookmarked_items" 
              />
            </a-col>
          </a-row>
          
          <a-divider />
          
          <h4>定时任务配置</h4>
          <p>当前监控间隔: {{ checkInterval }} 分钟</p>
          <a-button @click="updateCron">更新定时任务</a-button>
        </div>
      </a-layout-content>
    </a-layout>
    
    <!-- 添加/编辑商品弹窗 -->
    <a-modal
      v-model:open="modalVisible"
      :title="editingProduct ? '编辑监控商品' : '添加监控商品'"
      @ok="saveProduct"
      width="600px"
    >
      <a-form :model="productForm" layout="vertical">
        <a-form-item label="商品名称" required>
          <a-input v-model:value="productForm.name" placeholder="例如: iPhone 15 Pro Max" />
        </a-form-item>
        <a-form-item label="搜索关键词" required>
          <a-input v-model:value="productForm.keywords" placeholder="闲鱼搜索用的关键词" />
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="目标价格">
              <a-input-number 
                v-model:value="productForm.target_price" 
                :min="0" 
                style="width: 100%"
                placeholder="期望价格"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="最高价格">
              <a-input-number 
                v-model:value="productForm.max_price" 
                :min="0" 
                style="width: 100%"
                placeholder="超过此价格不提醒"
              />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="最低折扣率">
          <a-slider 
            v-model:value="productForm.min_discount_rate" 
            :min="0.1" 
            :max="1" 
            :step="0.05"
            :marks="{ 0.5: '5折', 0.7: '7折', 0.9: '9折' }"
          />
          <span>低于此折扣率才提醒 (当前: {{ (productForm.min_discount_rate * 100).toFixed(0) }}%)</span>
        </a-form-item>
        <a-form-item label="商品图片URL">
          <a-input v-model:value="productForm.image_url" placeholder="用于图片匹配 (可选)" />
        </a-form-item>
        <a-form-item label="备注">
          <a-textarea v-model:value="productForm.notes" :rows="2" />
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item>
              <a-checkbox v-model:checked="productForm.notify_email">邮件通知</a-checkbox>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item>
              <a-checkbox v-model:checked="productForm.notify_feishu">飞书通知</a-checkbox>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item>
              <a-checkbox v-model:checked="productForm.auto_buy_enabled">自动拍下</a-checkbox>
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { 
  PlusOutlined, 
  SearchOutlined, 
  DeleteOutlined,
  LinkOutlined,
  StarOutlined,
  LockOutlined,
  LockFilled
} from '@ant-design/icons-vue'
import xianyuApi from '../api/xianyu'

// 状态
const activeMenu = ref(['products'])
const products = ref([])
const results = ref([])
const bookmarkedItems = ref([])
const selectedProduct = ref(null)
const status = ref({
  total_products: 0,
  active_products: 0,
  bookmarked_items: 0
})
const checkInterval = ref(30)

// 菜单
const menuItems = [
  { key: 'products', label: '监控商品' },
  { key: 'results', label: '搜索结果' },
  { key: 'bookmarked', label: '已锁定' },
  { key: 'status', label: '系统状态' }
]

// 表格列
const productColumns = [
  { title: '商品名称', dataIndex: 'name', key: 'name' },
  { title: '关键词', dataIndex: 'keywords', key: 'keywords' },
  { title: '目标价', dataIndex: 'target_price', key: 'target_price' },
  { title: '最高价', dataIndex: 'max_price', key: 'max_price' },
  { title: '折扣', key: 'discount' },
  { title: '状态', key: 'status' },
  { title: '操作', key: 'actions', width: 200 }
]

// 弹窗
const modalVisible = ref(false)
const editingProduct = ref(null)
const productForm = reactive({
  name: '',
  keywords: '',
  target_price: null,
  max_price: null,
  min_discount_rate: 0.8,
  image_url: '',
  notes: '',
  notify_email: true,
  notify_feishu: false,
  auto_buy_enabled: false
})

// 加载数据
const loadProducts = async () => {
  try {
    const res = await xianyuApi.getProducts()
    products.value = res.data.data || []
  } catch (e) {
    message.error('加载商品失败')
  }
}

const loadStatus = async () => {
  try {
    const res = await xianyuApi.getStatus()
    status.value = res.data.data || {}
  } catch (e) {
    console.error(e)
  }
}

const loadResults = async () => {
  if (!selectedProduct.value) {
    message.warning('请选择监控商品')
    return
  }
  try {
    const res = await xianyuApi.getResults(selectedProduct.value)
    results.value = res.data.data || []
  } catch (e) {
    message.error('加载结果失败')
  }
}

const loadBookmarked = async () => {
  try {
    const res = await xianyuApi.getBookmarked()
    bookmarkedItems.value = res.data.data || []
  } catch (e) {
    console.error(e)
  }
}

// 操作
const showAddModal = () => {
  editingProduct.value = null
  Object.assign(productForm, {
    name: '',
    keywords: '',
    target_price: null,
    max_price: null,
    min_discount_rate: 0.8,
    image_url: '',
    notes: '',
    notify_email: true,
    notify_feishu: false,
    auto_buy_enabled: false
  })
  modalVisible.value = true
}

const editProduct = (product) => {
  editingProduct.value = product
  Object.assign(productForm, {
    name: product.name,
    keywords: product.keywords,
    target_price: product.target_price,
    max_price: product.max_price,
    min_discount_rate: product.min_discount_rate || 0.8,
    image_url: product.image_url || '',
    notes: product.notes || '',
    notify_email: !!product.notify_email,
    notify_feishu: !!product.notify_feishu,
    auto_buy_enabled: !!product.auto_buy_enabled
  })
  modalVisible.value = true
}

const saveProduct = async () => {
  try {
    if (editingProduct.value) {
      await xianyuApi.updateProduct(editingProduct.value.id, productForm)
      message.success('更新成功')
    } else {
      await xianyuApi.createProduct(productForm)
      message.success('添加成功')
    }
    modalVisible.value = false
    loadProducts()
  } catch (e) {
    message.error('保存失败')
  }
}

const deleteProduct = async (id) => {
  try {
    await xianyuApi.deleteProduct(id)
    message.success('删除成功')
    loadProducts()
  } catch (e) {
    message.error('删除失败')
  }
}

const toggleProduct = async (id) => {
  try {
    await xianyuApi.toggleProduct(id)
    loadProducts()
  } catch (e) {
    message.error('操作失败')
  }
}

const checkProduct = async (id) => {
  try {
    message.loading('检查中...', 0)
    const res = await xianyuApi.searchProduct(id)
    message.destroy()
    
    const matched = res.data.data?.matched_items || []
    if (matched.length > 0) {
      message.success(`找到 ${matched.length} 个匹配商品`)
      selectedProduct.value = id
      results.value = matched
      activeMenu.value = ['results']
    } else {
      message.info('未找到匹配商品')
    }
  } catch (e) {
    message.destroy()
    message.error('检查失败')
  }
}

const runAllCheck = async () => {
  try {
    message.loading('正在检查所有商品...', 0)
    const res = await xianyuApi.searchAll()
    message.destroy()
    
    const alerts = res.data.data?.alerts || []
    if (alerts.length > 0) {
      message.success(`找到 ${alerts.length} 个好价商品`)
    } else {
      message.info('未找到新的好价商品')
    }
    loadProducts()
  } catch (e) {
    message.destroy()
    message.error('检查失败')
  }
}

const bookmarkItem = async (id) => {
  try {
    await xianyuApi.bookmarkItem(id, true)
    message.success('已收藏')
    loadResults()
  } catch (e) {
    message.error('操作失败')
  }
}

const lockItem = async (id) => {
  try {
    await xianyuApi.bookmarkItem(id, true)
    message.success('已锁定')
    loadResults()
  } catch (e) {
    message.error('操作失败')
  }
}

const updateCron = () => {
  message.success('定时任务配置已更新')
}

const handleMenuClick = ({ key }) => {
  activeMenu.value = [key]
  if (key === 'bookmarked') {
    loadBookmarked()
  } else if (key === 'status') {
    loadStatus()
  }
}

onMounted(() => {
  loadProducts()
  loadStatus()
})
</script>

<style scoped>
.xianyu-monitor {
  min-height: 100vh;
}

.header {
  display: flex;
  align-items: center;
}

.logo {
  color: white;
  font-size: 18px;
  margin-right: 40px;
  display: flex;
  align-items: center;
}

.logo-icon {
  font-size: 24px;
  margin-right: 8px;
}

.content {
  padding: 24px;
  background: #f0f2f5;
}

.toolbar {
  margin-bottom: 16px;
}

.result-card {
  margin-bottom: 16px;
}

.result-card.good-price {
  border-color: #ff4d4f;
}

.result-card.matched {
  border-color: #1890ff;
}

.result-card.bookmarked {
  border-color: #faad14;
}

.item-image {
  position: relative;
  height: 180px;
  overflow: hidden;
  background: #f5f5f5;
}

.item-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.badges {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  gap: 4px;
}

.price-info {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.price {
  font-size: 18px;
  color: #ff4d4f;
  font-weight: bold;
}

.original {
  font-size: 14px;
  color: #999;
  text-decoration: line-through;
}

.meta-info {
  display: flex;
  justify-content: space-between;
  color: #999;
  font-size: 12px;
  margin-top: 8px;
}

.status-view {
  background: white;
  padding: 24px;
  border-radius: 8px;
}
</style>
