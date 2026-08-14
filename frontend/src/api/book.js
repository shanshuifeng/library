import request from './request'

// 图书列表（分页 + 多条件搜索）
export function getBookList(params) {
  return request({ url: '/books/', method: 'get', params })
}

// 图书详情
export function getBookDetail(id) {
  return request({ url: `/books/${id}`, method: 'get' })
}

// 新增图书
export function createBook(data) {
  return request({ url: '/books/', method: 'post', data })
}

// 更新图书
export function updateBook(id, data) {
  return request({ url: `/books/${id}`, method: 'put', data })
}

// 删除图书
export function deleteBook(id) {
  return request({ url: `/books/${id}`, method: 'delete' })
}

// 上传封面图片
export function uploadCover(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request({
    url: '/books/upload-cover',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}
