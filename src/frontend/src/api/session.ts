/**
 * @file session.ts
 * @module API/Session-Interaction
 * @description 交互会话与多智能体对话管理 API 模块。
 * 本模块是系统的交互中枢，负责管理用户与底层 AI 代理集群（Schema Agent, DDL Agent 等）之间的通信会话。
 * * 核心功能链：
 * 1. 会话生命周期：支持会话的持久化存储、重命名及逻辑删除；
 * 2. 状态化对话：基于 Session ID 维护多轮对话上下文，实现需求的逐步细化（SF6）；
 * 3. 安全指令确认：实现“人工介入循环 (Human-in-the-loop)”，针对高危 DML 操作执行安全审计与确认（SF3）；
 * 4. 异构模型调度：支持根据业务场景动态切换底层推理模型。
 * * @author Wang Lirong (王利蓉)
 * @version 2.2.0 (适配迭代开发计划 β 版本)
 * @date 2026-01-02
 */

import client from './client.ts';
import { ChatResponse, PageData, AIModelOptionsResponse } from '../types';

/**
 * 会话基础信息实体接口
 * @interface SessionItem
 * @description 对应后端 SessionResponse 架构，记录对话环境的元数据。
 * @property {number} session_id - 会话唯一标识，用于挂载历史消息快照。
 * @property {string} session_name - 用户自定义的会话标题，默认为“新会话”。
 * @property {number} project_id - 所属项目的关联 ID，实现项目级资源隔离。
 * @property {string | null} current_model - 当前会话绑定的 AI 推理模型标识。
 * @property {string} created_at - 会话创建时间（ISO 8601）。
 * @property {string | null} last_activity - 最后一次交互时间，用于会话活跃度分析。
 */
export interface SessionItem {
  session_id: number;
  session_name: string;
  project_id: number;
  current_model: string | null;
  created_at: string;
  last_activity: string | null;
}

/**
 * 会话管理与消息交互 API 核心调用对象
 * 支撑前端“对话面板”与“历史列表”的实时数据同步
 */
export const sessionApi = {
  /**
   * 1.1 分页获取指定项目下的会话列表
   * 用于在工作台左侧导航栏渲染历史对话记录。
   * @method getList
   * @param {number | string} projectId - 归属项目 ID
   * @param {number} [page=0] - 分页起始索引
   * @param {number} [limit=100] - 单页获取上限，默认 100 以覆盖长列表需求
   * @returns {Promise<PageData<SessionItem[]>>} 包含会话数组及总数的分页对象
   */
  getList: (projectId: number | string, page: number = 0, limit: number = 100) => {
    // 执行 GET 请求，并将页码转换为后端的 skip/limit 偏移量模型
    return client.get<any, PageData<SessionItem[]>>('/v1/sessions/', {
      params: {
        project_id: Number(projectId),
        skip: page * limit,
        limit
      }
    });
  },

  /**
   * 1.2 在当前项目下发起新的对话会话
   * 初始化一个新的对话环境，系统将为其分配独立的 Agent 上下文空间。
   * @method create
   * @param {number | string} projectId - 项目 ID
   * @param {string} [name] - 可选的会话名称
   */
  create: (projectId: number | string, name?: string) => {
    // 向服务端提交创建申请，默认名称为“新会话”
    return client.post<any, SessionItem>('/v1/sessions/', {
      project_id: Number(projectId),
      session_name: name || '新会话'
    });
  },

  /**
   * 1.3 获取特定会话的详尽元数据
   * 常用于在页面刷新后恢复特定会话的配置状态。
   * @method getDetail
   * @param {number} sessionId - 会话识别码
   */
  getDetail: (sessionId: number) => {
    return client.get<any, SessionItem>(`/v1/sessions/${sessionId}`);
  },

  /**
   * 1.4 对现有会话进行重命名或属性更新
   * 允许用户自定义会话标识，便于后期资产检索。
   * @method update
   * @param {number} sessionId - 目标会话 ID
   * @param {string} name - 新的会话标题
   */
  update: (sessionId: number, name: string) => {
    return client.put<any, SessionItem>(`/v1/sessions/${sessionId}`, {
      session_id: sessionId,
      session_name: name
    });
  },

  /**
   * 1.5 彻底删除指定的会话记录
   * 注意：此操作通常会连带清理后端存储的对话历史缓存（Short-term memory）。
   * @method delete
   * @param {number} sessionId - 待删除 ID
   * @returns {Promise<{ success: boolean }>}
   */
  delete: (sessionId: number) => {
    return client.delete<any, { success: boolean }>(`/v1/sessions/${sessionId}`);
  },

  /**
   * 2.1 向 AI 代理集群发送自然语言指令
   * 系统将触发路由逻辑，根据内容分发给相应的 Agent 进行处理。
   * 若涉及库表生成，将进入异步 Schema 分析流。
   * @async
   * @method sendMessage
   * @param {number} sessionId - 会话上下文 ID
   * @param {string} content - 用户输入的自然语言文本（如：“帮我加一个用户表”）
   * @param {string} [model] - 可选：指定本次对话使用的推理模型
   * @returns {Promise<ChatResponse>} 包含代理反馈、生成的 SQL 片段及 UI 状态指令
   */
  sendMessage: (sessionId: number, content: string, model?: string) => {
    // AI 调用可能需要较长时间（模型推理、网络延迟等），设置 120 秒超时
    // 这样可以确保前端等待后端完成处理，包括错误消息的持久化
    return client.post<any, ChatResponse>(`/v1/sessions/${sessionId}/messages`, {
      content,
      model
    }, {
      timeout: 120000  // 120秒超时，覆盖大多数AI模型响应场景
    });
  },

  /**
   * 2.2 获取当前会话的全量历史消息轨迹
   * 用于在前端对话窗口渲染气泡流，恢复之前的交流上下文。
   * @method getMessages
   * @param {number} sessionId - 会话 ID
   */
  getMessages: (sessionId: number) => {
    // 返回 ChatResponse 数组，包含 User 与 Assistant 的交互记录
    return client.get<any, ChatResponse[]>(`/v1/sessions/${sessionId}/messages`);
  },

  /**
   * 2.3 核心安全特性：确认并执行 AI 建议的消息指令
   * 实现 SF3 的安全确认逻辑。当 AI 生成删除、修改等 DML 语句时，
   * 必须通过此接口手动触发物理执行。
   * @method confirmMessage
   * @param {number} message_id - 待确认的 AI 消息节点 ID
   * @returns {Promise<ChatResponse>} 执行结果反馈（含受影响行数或执行成功标识）
   */
  confirmMessage: (messageId: number) => {
    // 用户点击“确认执行”按钮后触发，将生成的临时 SQL 正式部署至物理数据库
    return client.post<any, ChatResponse>(`/v1/messages/${messageId}/confirm`);
  },

  /**
   * 2.3.1 撤销或拒绝 AI 建议的消息指令
   * 实现“安全刹车”。若用户发现 AI 生成的逻辑有误，可通过此接口终止操作。
   * @method cancelMessage
   * @param {number} messageId - 待撤销的消息 ID
   */
  cancelMessage: (messageId: number) => {
    // 终止执行并更新 UI 状态为“已取消”，防止误触发
    return client.post<any, ChatResponse>(`/v1/messages/${messageId}/cancel`);
  },

  /**
   * 2.4 获取当前平台支持的 AI 代理推理模型清单
   * 实现迭代计划中的“多模型切换”特性。
   * 前端据此渲染模型切换下拉菜单。
   * @method getAIModelOptions
   * @returns {Promise<AIModelOptionsResponse>} 包含可用模型 ID 及展示名称的列表
   */
  getAIModelOptions: () => {
    // 从后端动态调取当前已注册并在线的模型节点配置
    return client.get<any, AIModelOptionsResponse>('/v1/ai-models/options');
  }
};