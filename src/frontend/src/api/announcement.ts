import client from './client.ts';
import { Announcement } from '../types.ts';

// 列表响应接口
interface AnnouncementListResponse {
  total: number;
  page: number;
  page_size: number;
  items: Announcement[];
}

// 创建请求参数
export interface CreateAnnouncementParams {
  title: string;
  content: string;
  status?: 'published' | 'draft';
}

// 更新请求参数
export interface UpdateAnnouncementParams {
  title?: string;
  content?: string;
  status?: 'published' | 'draft' | 'unpublished' | 'expired';
}

export const announcementApi = {
  /**
   * 4.2.1 创建公告
   * POST /api/v1/announcements
   */
  create: (data: CreateAnnouncementParams) => {
    return client.post<any, Announcement>('/v1/announcements', data);
  },

  /**
   * 4.2.2 更新公告
   * PUT /api/v1/announcements/{announcement_id}
   */
  update: (id: number, data: UpdateAnnouncementParams) => {
    return client.put<any, Announcement>(`/v1/announcements/${id}`, data);
  },

  /**
   * 4.2.3 删除公告
   * DELETE /api/v1/announcements/{announcement_id}
   */
  delete: (id: number) => {
    return client.delete<any, void>(`/v1/announcements/${id}`);
  },

  /**
   * 获取公告列表
   * GET /api/v1/announcements/
   * 注意：OpenAPI 中此路径带有末尾斜杠
   */
  getList: (page: number = 1, pageSize: number = 10, status: string = 'published') => {
    return client.get<any, AnnouncementListResponse>('/v1/announcements/', {
      params: {
        page,
        page_size: pageSize,
        status
      }
    });
  },

  /**
   * 获取公告详情
   * GET /api/v1/announcements/{announcement_id}
   */
  getDetail: (id: number) => {
    return client.get<any, Announcement>(`/v1/announcements/${id}`);
  }
};