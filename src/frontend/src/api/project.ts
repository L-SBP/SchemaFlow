import client from './client';
// 引入类型定义
import { ProjectDTO } from '../types';

export type { ProjectDTO };

// 修正：增加 SQLite 到类型定义中
export interface CreateProjectParams {
  name: string;
  type: 'MySQL' | 'PostgreSQL' | 'SQLite';
  description: string;
}

// 对应文档: Body 请求参数 (PATCH)
export interface UpdateProjectParams {
  project_name?: string;
  description?: string;
  schema_definition?: Record<string, any>;
}

// 对应文档: Confirm Delete 响应
export interface ConfirmDeleteResponse {
  confirmation_token: string;
  expires_at: string;
}

// 1. 获取项目列表
export const fetchProjects = async (): Promise<ProjectDTO[]> => {
  const response = await client.get('/v1/projects/');
  // 适配: 后端返回 { items: [...] }
  return (response as any).items || response.data || response || [];
};

// 2. 创建新项目
export const createProject = async (params: CreateProjectParams): Promise<{ project_id: string; message: string }> => {
  // 对应文档: POST /api/v1/projects/
  const response = await client.post('/v1/projects/', {
    project_name: params.name,
    db_type: params.type.toLowerCase(), // 确保转为小写: mysql/postgresql/sqlite
    description: params.description
  });
  return response as any;
};

// 3. 获取项目详情 (包含生成进度、Schema、DDL)
export const getProjectDetail = async (projectId: string | number): Promise<ProjectDTO> => {
  // 对应文档: GET /api/v1/projects/{project_id}
  const response = await client.get(`/v1/projects/${projectId}`);
  return (response as any).data || response;
};

// 3.1 生成 DDL
export const generateDDL = async (projectId: string | number, confirmedSchema: string, requirements?: string): Promise<void> => {
  // 对应文档: POST /api/v1/projects/{project_id}/generate-ddl
  await client.post(`/v1/projects/${projectId}/generate-ddl`, {
    confirmed_schema: confirmedSchema,
    requirements
  });
};

// 3.2 部署项目
export const deployProject = async (projectId: string | number, confirmedDDL: string, confirmedSchema?: string, useSmartParse: boolean = false): Promise<ProjectDTO> => {
  // 对应文档: POST /api/v1/projects/{project_id}/deploy
  const response = await client.post(`/v1/projects/${projectId}/deploy`, {
    confirmed_ddl: confirmedDDL,
    confirmed_schema: confirmedSchema,
    use_smart_parse: useSmartParse
  });
  return (response as any).data || response;
};

// 4. 更新项目信息 (用于需求微调、触发重生成)
export const updateProject = async (projectId: string | number, params: UpdateProjectParams): Promise<ProjectDTO> => {
  // 对应文档: PATCH /api/v1/projects/{project_id}
  const response = await client.patch(`/v1/projects/${projectId}`, params);
  return (response as any).data || response;
};

// 5. 确认删除 (获取 Token)
export const confirmDeleteProject = async (projectId: string | number, confirmationText: string): Promise<ConfirmDeleteResponse> => {
  // 对应文档: POST /api/v1/projects/{project_id}/confirm-delete
  const response = await client.post(`/v1/projects/${projectId}/confirm-delete`, {
    confirmation_text: confirmationText
  });
  // 适配可能的数据包裹结构
  return (response as any).data || response;
};

// 6. 删除项目 (需要 Token)
export const deleteProject = async (projectId: string | number, token: string): Promise<void> => {
  // 对应文档: DELETE /api/v1/projects/{project_id}
  // 需要 Header: X-Confirmation-Token
  await client.delete(`/v1/projects/${projectId}`, {
    headers: {
      'X-Confirmation-Token': token
    }
  });
};