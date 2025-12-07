import client from './client.ts';

// 对应文档: SessionResponse
export interface SessionItem {
  session_id: number;
  session_name: string;
  project_id: number;
  created_at: string;
  last_activity: string | null;
}

// 对应文档: ChatResponse
export interface ChatMessageResponse {
  message_id: number;
  content: string;
  message_type: 'user' | 'assistant';
  sql_text: string | null;
  sql_type: string;
  requires_confirmation: boolean;
  data: any[] | null;
}

// 对应文档: Request Body for creating session
export interface CreateSessionParams {
  project_id: number;
  session_name?: string;
}

export const sessionApi = {
  /**
   * 1.1 获取会话列表
   * GET /api/v1/sessions/
   */
  getList: (projectId: number | string, page: number = 0, limit: number = 100) => {
    return client.get<any, SessionItem[]>('/v1/sessions/', {
      params: {
        project_id: Number(projectId), // 确保转为 integer
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
   * 1.3 获取会话详情
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
      session_name: name
    });
  },

  /**
   * 1.5 删除会话
   * DELETE /api/v1/sessions/{session_id}
   */
  delete: (sessionId: number) => {
    return client.delete<any, boolean>(`/v1/sessions/${sessionId}`);
  },

  /**
   * 2.1 发送消息 (对话)
   * POST /api/v1/sessions/{session_id}/messages
   */
  sendMessage: (sessionId: number, content: string) => {
    return client.post<any, ChatMessageResponse>(`/v1/sessions/${sessionId}/messages`, {
      content
    });
  },

  /**
   * 2.2 获取历史消息
   * GET /api/v1/sessions/{session_id}/messages
   */
  getMessages: (sessionId: number) => {
    return client.get<any, ChatMessageResponse[]>(`/v1/sessions/${sessionId}/messages`);
  }
};