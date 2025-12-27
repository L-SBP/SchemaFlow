import client from './client.ts';
import {
  AdminStats,
  AdminUserDetailResponse,
  PageData,
  ViolationLogListItem,
  AdminUserListItem,
  AdminListItem,
  AIModelConfigResponse,
  AIModelConfigListResponse,
  AIModelConfigDetailResponse,
  AIModelConfigCreate,
  AIModelConfigUpdate
} from '../types.ts';

// 2.2 更新用户状态请求体
interface UpdateUserStatusParams {
  status: 'normal' | 'banned' | 'suspended';
  reason: string;
}

// 2.3 更新用户配额请求体
interface UpdateUserQuotaParams {
  max_databases: number;
}

export const adminApi = {
  /**
   * 1.1 获取系统统计看板
   * GET /api/v1/dashboard/stats
   */
  getDashboardStats: () => {
    return client.get<any, AdminStats>('/v1/dashboard/stats');
  },

  /**
   * 2.1 获取用户列表
   * GET /api/v1/users
   */
  getUsers: (page: number = 1, pageSize: number = 20, search?: string, status: string = 'all') => {
    return client.get<any, PageData<AdminUserListItem[]>>('/v1/users', {
      params: {
        page,
        page_size: pageSize,
        search,
        status
      }
    });
  },

  /**
   * 2.4 获取用户详情
   * GET /api/v1/users/{user_id}
   */
  getUserDetail: (userId: number | string, projectLimit: number = 100, loginLimit: number = 20) => {
    return client.get<any, AdminUserDetailResponse>(`/v1/users/${userId}`, {
      params: {
        project_limit: projectLimit,
        login_limit: loginLimit
      }
    });
  },

  /**
   * 2.2 修改用户状态 (封禁/解封)
   * PATCH /api/v1/users/{user_id}/status
   */
  updateUserStatus: (userId: number | string, data: UpdateUserStatusParams) => {
    return client.patch<any, any>(`/v1/users/${userId}/status`, data);
  },

  /**
   * 2.3 调整用户资源额度
   * PATCH /api/v1/users/{user_id}/quota
   */
  updateUserQuota: (userId: number | string, maxDatabases: number) => {
    const data: UpdateUserQuotaParams = { max_databases: maxDatabases };
    return client.patch<any, any>(`/v1/users/${userId}/quota`, data);
  },

  /**
   * 4.1 获取管理员列表
   * GET /api/v1/admins
   */
  getAdmins: (page: number = 1, pageSize: number = 20) => {
    return client.get<any, PageData<AdminListItem[]>>('/v1/admins', {
      params: {
        page,
        page_size: pageSize
      }
    });
  },

  /**
   * 4.2 获取违规记录列表
   * GET /api/v1/violations
   */
  getViolations: (
    page: number = 1,
    pageSize: number = 20,
    riskLevel?: string,
    resolutionStatus?: string
  ) => {
    return client.get<any, PageData<ViolationLogListItem[]>>('/v1/violations', {
      params: {
        page,
        page_size: pageSize,
        risk_level: riskLevel,
        resolution_status: resolutionStatus
      }
    });
  },

  // ========================================
  // 5. AI 模型配置管理
  // ========================================

  /**
   * 5.1 获取 AI 模型配置列表
   * GET /api/v1/ai-models
   */
  getAIModels: (page: number = 1, pageSize: number = 20, activeOnly: boolean = false) => {
    return client.get<any, AIModelConfigListResponse>('/v1/ai-models', {
      params: {
        page,
        page_size: pageSize,
        active_only: activeOnly
      }
    });
  },

  /**
   * 5.2 获取 AI 模型配置详情
   * GET /api/v1/ai-models/{config_id}
   */
  getAIModelDetail: (configId: number) => {
    return client.get<any, AIModelConfigDetailResponse>(`/v1/ai-models/${configId}`);
  },

  /**
   * 5.3 创建 AI 模型配置
   * POST /api/v1/ai-models
   */
  createAIModel: (data: AIModelConfigCreate) => {
    return client.post<any, AIModelConfigResponse>('/v1/ai-models', data);
  },

  /**
   * 5.4 更新 AI 模型配置
   * PUT /api/v1/ai-models/{config_id}
   */
  updateAIModel: (configId: number, data: AIModelConfigUpdate) => {
    return client.put<any, AIModelConfigResponse>(`/v1/ai-models/${configId}`, data);
  },

  /**
   * 5.5 删除 AI 模型配置
   * DELETE /api/v1/ai-models/{config_id}
   */
  deleteAIModel: (configId: number) => {
    return client.delete<any, null>(`/v1/ai-models/${configId}`);
  }
};