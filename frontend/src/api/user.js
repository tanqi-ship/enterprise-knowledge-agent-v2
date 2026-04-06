import request from './index.js'

// 获取所有用户（管理员）
export const getUserListAPI = () => request.get('/admin/users')

// 修改用户角色（管理员）
export const updateUserRoleAPI = (userId, role) =>
  request.put(`/admin/users/${userId}/role`, { role })
