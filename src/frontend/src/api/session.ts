import client from './client.ts';
import { ChatResponse, PageData, AIModelOptionsResponse } from '../types';

// 对应文档: SessionResponse (会话信息)
export interface SessionItem {
  session_id: number;
  session_name: string;
  project_id: number;
  created_at: string;
  last_activity: string | null;
}

export const sessionApi = {
  /**
   * 1.1 获取会话列表
   * GET /api/v1/sessions/
   */
  getList: (projectId: number | string, page: number = 0, limit: number = 100) => {
    return client.get<any, PageData<SessionItem[]>>('/v1/sessions/', {
      params: {
        project_id: Number(projectId),
        skip: page * limit,
        limit
      }
    });
  },

  /**
   * 1.2 创建新会话
   * POST /api/v1/sessions/
   */
  create: (projectId: number | string, name?: string) => {
    return client.post<any, SessionItem>('/v1/sessions/', {
      project_id: Number(projectId),
      session_name: name || '新会话'
    });
  },

  /**
   * 1.3 获取会话详情 (可选，部分场景可能用到)
   * GET /api/v1/sessions/{session_id}
   */
  getDetail: (sessionId: number) => {
    return client.get<any, SessionItem>(`/v1/sessions/${sessionId}`);
  },

  /**
   * 1.4 更新会话信息 (重命名)
   * PUT /api/v1/sessions/{session_id}
   */
  update: (sessionId: number, name: string) => {
    return client.put<any, SessionItem>(`/v1/sessions/${sessionId}`, {
      session_id: sessionId,
      session_name: name
    });
  },

  /**
   * 1.5 删除会话
   * DELETE /api/v1/sessions/{session_id}
   */
  delete: (sessionId: number) => {
    return client.delete<any, { success: boolean }>(`/v1/sessions/${sessionId}`);
  },

  /**
   * 2.1 发送消息 (对话)
   * POST /api/v1/sessions/{session_id}/messages
   */
  sendMessage: (sessionId: number, content: string, model?: string) => {
    return client.post<any, ChatResponse>(`/v1/sessions/${sessionId}/messages`, {
      content,
      model
    });
  },

  /**
   * 2.2 获取历史消息
   * GET /api/v1/sessions/{session_id}/messages
   */
  getMessages: (sessionId: number) => {
    return client.get<any, ChatResponse[]>(`/v1/sessions/${sessionId}/messages`);
  },

  /**
   * 2.3 确认消息 (执行 SQL)
   * POST /api/v1/messages/{message_id}/confirm
   */
  confirmMessage: (messageId: number) => {
    return client.post<any, ChatResponse>(`/v1/messages/${messageId}/confirm`);
  },

  /**
   * 2.4 获取可用的 AI 模型列表
   * GET /api/v1/ai-models/options
   */
  getAIModelOptions: () => {
    return client.get<any, AIModelOptionsResponse>('/v1/ai-models/options');
  }
};