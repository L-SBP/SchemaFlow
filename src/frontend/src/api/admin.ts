/**
 * @file admin.ts
 * @module API/Admin
 * @description 系统管理员专用 API 服务模块。
 * 本模块深度集成于“基于大模型多智能体框架的数据库自动部署与库表生成系统”的管理后台，
 * 负责处理高权限等级的操作指令，包括但不限于全局状态监控、用户生命周期管理、
 * 资源配额动态调整以及底层 AI 代理模型的参数化配置。
 * @author Wang Lirong (王利蓉)
 * @version 2.1.0
 * @date 2026-01-02
 */

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
  AIModelConfigUpdate,
  AIModelTestConnectionRequest,
  AIModelTestConnectionResponse
} from '../types.ts';

/**
 * 更新用户状态时的请求参数接口定义
 * @interface UpdateUserStatusParams
 * @property {string} status - 目标状态，可选值：正常(normal)、封禁(banned)、挂起(suspended)
 * @property {string} reason - 变更状态的操作原因说明，用于审计日志记录
 */
interface UpdateUserStatusParams {
  status: 'normal' | 'banned' | 'suspended';
  reason: string;
}

/**
 * 调整用户资源额度时的请求参数接口定义
 * @interface UpdateUserQuotaParams
 * [cite_start]@property {number} max_databases - 允许该用户创建的最大数据库项目上限 [cite: 518]
 */
interface UpdateUserQuotaParams {
  max_databases: number;
}

/**
 * 管理员 API 核心调用对象
 * [cite_start]封装了所有涉及系统治理与运维的 RESTful 交互逻辑 [cite: 170-173, 218-219]
 */
export const adminApi = {
  /**
   * 1.1 获取系统统计看板数据
   * 从后端 APM 监控模块调取实时数据，包含系统健康度、活跃用户及高危拦截统计。
   * [cite_start]对应业务目标 BO-4 的系统监控需求 [cite: 55-60, 253]。
   * @method getDashboardStats
   * @returns {Promise<AdminStats>} 包含全局运行指标的响应对象
   */
  getDashboardStats: () => {
    return client.get<any, AdminStats>('/v1/dashboard/stats');
  },

  /**
   * 2.1 分页获取全平台用户列表
   * [cite_start]允许管理员检索注册用户清单，并根据活跃状态、用户名或邮箱进行筛选 [cite: 484-487, 496]。
   * @method getUsers
   * @param {number} [page=1] - 请求页码
   * @param {number} [pageSize=20] - 每页数据量
   * @param {string} [search] - 搜索关键词
   * @param {string} [status='all'] - 状态过滤
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
   * 2.4 获取特定用户的详细档案
   * [cite_start]调阅包含用户基本信息、项目清单及最近登录记录的完整档案 [cite: 488-489]。
   * @method getUserDetail
   * @param {number | string} userId - 用户唯一标识
   * @param {number} [projectLimit=100] - 项目展示限制
   * @param {number} [loginLimit=20] - 登录记录展示限制
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
   * [cite_start]针对违规账号执行状态变更，封禁操作将强制清除用户会话 [cite: 490-493, 617]。
   * @method updateUserStatus
   * @param {number | string} userId - 目标用户 ID
   * @param {UpdateUserStatusParams} data - 状态变更数据
   */
  updateUserStatus: (userId: number | string, data: UpdateUserStatusParams) => {
    return client.patch<any, any>(`/v1/users/${userId}/status`, data);
  },

  /**
   * 2.3 调整用户资源额度
   * [cite_start]根据分配策略手动调整用户允许创建的数据库项目上限 [cite: 509, 518]。
   * @method updateUserQuota
   * @param {number | string} userId - 目标用户 ID
   * @param {number} maxDatabases - 新的配额上限值
   */
  updateUserQuota: (userId: number | string, maxDatabases: number) => {
    const data: UpdateUserQuotaParams = { max_databases: maxDatabases };
    return client.patch<any, any>(`/v1/users/${userId}/quota`, data);
  },

  /**
   * 4.1 获取管理员列表
   * [cite_start]调阅系统中所有管理账户的实时在线状态及最后登录时间 [cite: 499, 506]。
   * @method getAdmins
   * @param {number} [page=1]
   * @param {number} [pageSize=20]
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
   * 4.2 获取全平台违规记录列表
   * [cite_start]查看系统安全审计引擎捕获的违规行为或异常 SQL 操作记录 [cite: 107, 218]。
   * @method getViolations
   * @param {number} [page=1]
   * @param {number} [pageSize=20]
   * @param {string} [riskLevel] - 风险等级过滤
   * @param {string} [resolutionStatus] - 处理状态过滤
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

  /**
   * 5.1 获取 AI 模型配置列表
   * [cite_start]获取多智能体框架中已集成的 LLM 服务配置信息 [cite: 81-84, 287-292]。
   * @method getAIModels
   * @param {number} [page=1]
   * @param {number} [pageSize=20]
   * @param {boolean} [activeOnly=false]
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
   * 查看特定模型配置的推理参数及 API 连接详情。
   * @method getAIModelDetail
   * @param {number} configId - 配置项唯一识别码
   */
  getAIModelDetail: (configId: number) => {
    return client.get<any, AIModelConfigDetailResponse>(`/v1/ai-models/${configId}`);
  },

  /**
   * 5.3 创建 AI 模型配置
   * 向系统注册新的大语言模型服务实例。
   * @method createAIModel
   * @param {AIModelConfigCreate} data - 模型接入配置信息
   */
  createAIModel: (data: AIModelConfigCreate) => {
    return client.post<any, AIModelConfigResponse>('/v1/ai-models', data);
  },

  /**
   * 5.4 更新 AI 模型配置
   * 修改已注册模型的 API 密钥、端点或模型权重参数。
   * @method updateAIModel
   * @param {number} configId - 目标配置 ID
   * @param {AIModelConfigUpdate} data - 待更新的数据包
   */
  updateAIModel: (configId: number, data: AIModelConfigUpdate) => {
    return client.put<any, AIModelConfigResponse>(`/v1/ai-models/${configId}`, data);
  },

  /**
   * 5.5 删除 AI 模型配置
   * 从系统配置库中物理移除指定的 AI 模型接入点。
   * @method deleteAIModel
   * @param {number} configId - 待删除的配置 ID
   */
  deleteAIModel: (configId: number) => {
    return client.delete<any, null>(`/v1/ai-models/${configId}`);
  },

  /**
   * 5.6 测试 AI 模型连接
   * 通过发送握手请求验证当前 AI 模型配置的连通性及授权有效性。
   * @method testAIModelConnection
   * @param {AIModelTestConnectionRequest} data - 临时测试连接数据
   */
  testAIModelConnection: (data: AIModelTestConnectionRequest) => {
    return client.post<any, AIModelTestConnectionResponse>('/v1/ai-models/test-connection', data);
  }
};