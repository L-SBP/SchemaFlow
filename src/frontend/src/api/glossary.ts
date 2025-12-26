import client from './client.ts';
import {
  KnowledgeTerm,
  KnowledgeListResponse,
  KnowledgeImportResponse,
  KnowledgeExportResponse
} from '../types.ts';

// 对应接口文档的请求参数类型
export interface CreateTermParams {
  term: string;
  definition: string;
  examples?: string;
}

export interface UpdateTermParams {
  term?: string;
  definition?: string;
  examples?: string;
}

export const glossaryApi = {
  /**
   * 2. 获取术语列表
   * GET /api/v1/projects/{project_id}/knowledge
   */
  getList: (projectId: string, page: number = 1, pageSize: number = 20, search?: string) => {
    return client.get<any, KnowledgeListResponse>(`/v1/projects/${projectId}/knowledge`, {
      params: {
        page,
        page_size: pageSize,
        search
      }
    });
  },

  /**
   * 1. 创建业务术语
   * POST /api/v1/projects/{project_id}/knowledge
   */
  create: (projectId: string, data: CreateTermParams) => {
    return client.post<any, KnowledgeTerm>(`/v1/projects/${projectId}/knowledge`, data);
  },

  /**
   * 3. 更新术语信息
   * PATCH /api/v1/projects/{project_id}/knowledge/{knowledge_id}
   */
  update: (projectId: string, knowledgeId: number, data: UpdateTermParams) => {
    return client.patch<any, KnowledgeTerm>(`/v1/projects/${projectId}/knowledge/${knowledgeId}`, data);
  },

  /**
   * 4. 批量删除术语
   * DELETE /api/v1/projects/{project_id}/knowledge/batch
   * Body: { ids: number[] }
   */
  deleteBatch: (projectId: string, ids: number[]) => {
    return client.delete<any, KnowledgeImportResponse>(`/v1/projects/${projectId}/knowledge/batch`, {
      data: { ids } // Axios delete body 必须放在 config.data 中
    });
  },

  /**
   * 5. 导入术语 (文件上传)
   * POST /api/v1/projects/{project_id}/knowledge/import
   * Content-Type: multipart/form-data
   */
  importTerms: (projectId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    return client.post<any, KnowledgeImportResponse>(`/v1/projects/${projectId}/knowledge/import`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  /**
   * 6. 导出术语
   * GET /api/v1/projects/{project_id}/knowledge/export
   */
  exportTerms: (projectId: string) => {
    return client.get<any, KnowledgeExportResponse>(`/v1/projects/${projectId}/knowledge/export`);
  }
};