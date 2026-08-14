import request from './request'

// 获取分类树（后端在 /books/categories 下）
export function getCategoryTree() {
  return request({ url: '/books/categories', method: 'get' })
}

// 新增分类
export function createCategory(data) {
  return request({ url: '/books/categories', method: 'post', data })
}

// 更新分类
export function updateCategory(id, data) {
  return request({ url: `/books/categories/${id}`, method: 'put', data })
}

// 删除分类
export function deleteCategory(id) {
  return request({ url: `/books/categories/${id}`, method: 'delete' })
}
