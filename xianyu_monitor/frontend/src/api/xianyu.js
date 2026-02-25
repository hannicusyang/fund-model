/**
 * 闲鱼监控系统 API
 */
import axios from 'axios'

const API_BASE = '/api/xianyu'

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 响应拦截
apiClient.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// ==================== 监控商品API ====================

export default {
  // 获取监控商品列表
  getProducts(activeOnly = true) {
    return apiClient.get('/products', { params: { active_only: activeOnly } })
  },
  
  // 添加监控商品
  createProduct(data) {
    return apiClient.post('/products', data)
  },
  
  // 更新监控商品
  updateProduct(id, data) {
    return apiClient.put(`/products/${id}`, data)
  },
  
  // 删除监控商品
  deleteProduct(id) {
    return apiClient.delete(`/products/${id}`)
  },
  
  // 启用/禁用监控
  toggleProduct(id) {
    return apiClient.post(`/products/${id}/toggle`)
  },
  
  // 搜索并检查单个商品
  searchProduct(productId) {
    return apiClient.get(`/search/${productId}`)
  },
  
  // 检查所有商品
  searchAll(forceImageCheck = false) {
    return apiClient.post('/search-all', { force_image_check: forceImageCheck })
  },
  
  // 获取搜索结果
  getResults(productId, limit = 50) {
    return apiClient.get(`/results/${productId}`, { params: { limit } })
  },
  
  // 获取收藏的商品
  getBookmarked(productId = null) {
    const params = productId ? { product_id: productId } : {}
    return apiClient.get('/results/bookmarked', { params })
  },
  
  // 收藏商品
  bookmarkItem(itemId, bookmark = true) {
    return apiClient.post(`/results/${itemId}/bookmark`, { bookmark })
  },
  
  // 获取价格历史
  getPriceHistory(itemId, days = 30) {
    return apiClient.get(`/price-history/${itemId}`, { params: { days } })
  },
  
  // 获取通知列表
  getNotifications() {
    return apiClient.get('/notifications')
  },
  
  // 标记通知已发送
  sendNotification(notificationId) {
    return apiClient.post(`/notifications/${notificationId}/send`)
  },
  
  // 获取系统状态
  getStatus() {
    return apiClient.get('/status')
  }
}
