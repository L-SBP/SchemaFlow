/**
 * @file user.ts
 * @module API/User-Profile
 * @description 用户个人档案与安全中心 API 模块。
 * 本模块深度对接系统需求中的 SF10（个人账户管理）功能，为用户提供全方位的账户治理能力。
 * 核心职能：
 * 1. 档案管理：支持个人基本信息（用户名、头像）的实时维护；
 * 2. 安全加固：实现基于旧密码验证的密码变更流，以及基于邮件网关的身份二次核验；
 * 3. 行为审计：对接登录历史追踪（Reliability-2），确保每一次账户准入均可追溯。
 * @author Wang Lirong (王利蓉)
 * @version 1.5.0
 * @date 2026-01-02
 */

import client from './client.ts';
import { PageData } from '../types.ts';

// --- 类型定义 (参考 OpenAPI Schema V1.3) ---

/**
 * 个人信息核心视图接口
 * @interface UserMe
 * @description 反映当前登录用户的全维画像，包括基础属性与资源消耗状态。
 * @property {number} user_id - 系统内唯一识别码。
 * @property {string} username - 注册用户名。
 * @property {string} email - 绑定的主邮箱。
 * @property {string} status - 账户活跃策略：正常、挂起、封禁。
 * @property {number} used_databases - 当前已创建的物理数据库实例数。
 * @property {number} max_databases - 账户配额上限，受管理员动态调控。
 * @property {string | null} avatar_url - 托管在静态资源服务器上的头像地址。
 * @property {boolean} is_admin - 管理员权限标志。
 * @property {string | null} last_login_at - 最近一次鉴权成功的时间。
 * @property {string} created_at - 账号入库时间。
 */
export interface UserMe {
  user_id: number;
  username: string;
  email: string;
  status: 'normal' | 'suspended' | 'banned';
  used_databases: number;
  max_databases: number;
  avatar_url: string | null;
  is_admin: boolean;
  last_login_at: string | null;
  created_at: string;
}

/**
 * 修改密码请求参数接口
 * @interface UpdatePasswordParams
 * @property {string} old_password - 原始密码，用于后端进行身份再确认。
 * @property {string} new_password - 拟设定的新密码，需符合复杂度校验。
 * @property {string} confirm_password - 用于前端预校对的重复输入。
 */
export interface UpdatePasswordParams {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

/**
 * 变更邮箱请求参数接口
 * @interface UpdateEmailParams
 * @property {string} new_email - 待绑定的新邮箱地址。
 * @property {string} code - 从新邮箱获取的临时验证码。
 */
export interface UpdateEmailParams {
  new_email: string;
  code: string;
}

/**
 * 登录历史审计条目定义
 * @interface LoginHistoryItem
 * @description 对应系统审计日志，记录每次登录的设备环境与最终状态。
 */
export interface LoginHistoryItem {
  login_id: number;
  login_time: string;
  logout_time: string | null;
  ip_address: string;
  user_agent: string | null;
  login_status: 'success' | 'failed' | 'expired' | 'forced_logout';
}

// --- API 方法定义 ---

/**
 * 1. 检索当前在线用户的完整档案
 * 该接口通常在应用初始化及个人中心加载时调用，以同步最新的资源配额。
 * @method getUserProfile
 * @returns {Promise<UserMe>} 返回当前用户详情
 */
export const getUserProfile = () => {
  return client.get<any, UserMe>('/v1/user/me');
};

/**
 * 2. 修改用户个性化展示名称
 * 实现对 username 字段的局部更新。
 * @method updateUsername
 * @param {string} username - 新的用户名
 * @returns {Promise<UserMe>} 返回更新后的用户对象
 */
export const updateUsername = (username: string) => {
  // 发起 PATCH 请求进行增量字段修改
  return client.patch<any, UserMe>('/v1/user/me', { username });
};

/**
 * 3. 账户安全：更新登录密码
 * 后端将验证旧密码。若验证失败，则抛出 400 系列业务错误。
 * @method updatePassword
 * @param {UpdatePasswordParams} data - 包含新旧密码的数据载荷
 */
export const updatePassword = (data: UpdatePasswordParams) => {
  // 使用 PUT 动词执行密码资源的强制覆盖更新
  return client.put<any, void>('/v1/user/me/password', data);
};

/**
 * 4. 更新用户个性化头像
 * 接受已上传至存储服务后的 URL 地址，并更新至用户元数据中。
 * @method updateAvatar
 * @param {string} avatarUrl - 头像的 CDN 或存储地址
 */
export const updateAvatar = (avatarUrl: string) => {
  return client.post<any, { avatar_url: string }>('/v1/user/me/avatar', { avatar_url: avatarUrl });
};

/**
 * 5. 安全辅助：发送邮箱变更验证码
 * 向新申请的邮箱地址发送 6 位验证码，开启邮箱变更事务。
 * @method sendEmailVerificationCode
 * @param {string} newEmail - 新的目标邮箱地址
 */
export const sendEmailVerificationCode = (newEmail: string) => {
  // 触发后端邮件网关服务
  return client.post<any, void>('/v1/user/me/email/send-code', { new_email: newEmail });
};

/**
 * 6. 确认并完成邮箱变更逻辑
 * 验证用户输入的验证码。验证通过后，系统将正式切换绑定的邮箱字段。
 * @method confirmUpdateEmail
 * @param {UpdateEmailParams} data - 包含新邮箱及验证码的 payload
 */
export const confirmUpdateEmail = (data: UpdateEmailParams) => {
  return client.put<any, UserMe>('/v1/user/me/email', data);
};

/**
 * 7. 检索个人登录审计轨迹 (分页模式)
 * 对应非功能性需求中的“故障后追溯”要求。
 * 用户可在安全设置中查看近期的登录设备与 IP 是否存在异常。
 * @method getLoginHistory
 * @param {number} [page=1] - 当前请求页码
 * @param {number} [pageSize=10] - 每页审计记录条数，默认设定为 10 条
 * @returns {Promise<PageData<LoginHistoryItem[]>>} 包含审计历史的分页响应对象
 */
export const getLoginHistory = (page: number = 1, pageSize: number = 10) => {
  // 构建带有分页偏移参数的 GET 请求
  return client.get<any, PageData<LoginHistoryItem[]>>('/v1/user/me/login-history', {
    params: { page, page_size: pageSize }
  });
};