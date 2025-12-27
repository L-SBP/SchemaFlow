import client from './client';
import { ProjectDTO, PageData } from '../types';

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

// 项目创建响应
export interface CreateProjectResponse {
  project_id: number;
  message: string;
}

// 1. 获取项目列表 - 适配分页响应
export const fetchProjects = async (): Promise<PageData<ProjectDTO[]>> => {
  // 后端返回 UnifiedResponse<PageData<ProjectDTO[]>>，客户端自动提取 data
  return await client.get('/v1/projects/');
};

// 2. 创建新项目 - 适配统一响应
export const createProject = async (params: CreateProjectParams): Promise<CreateProjectResponse> => {
  // 对应文档: POST /api/v1/projects/
  // 后端返回 UnifiedResponse<CreateProjectResponse>，客户端自动提取 data
  return await client.post('/v1/projects/', {
    project_name: params.name,
    db_type: params.type.toLowerCase(), // 确保转为小写: mysql/postgresql/sqlite
    description: params.description
  });
};

// 3. 获取项目详情 (包含生成进度、Schema、DDL) - 适配统一响应
export const getProjectDetail = async (projectId: string | number): Promise<ProjectDTO> => {
  // 后端返回 UnifiedResponse<ProjectDetailOut>
  // 响应拦截器提取后直接得到 ProjectDetailOut
  return await client.get(`/v1/projects/${projectId}`);
};

// 3.1 生成 DDL - 适配统一响应
export const generateDDL = async (projectId: string | number, confirmedSchema: string, requirements?: string): Promise<void> => {
  // 对应文档: POST /api/v1/projects/{project_id}/generate-ddl
  // 后端返回 UnifiedResponse<null>，客户端自动处理
  await client.post(`/v1/projects/${projectId}/generate-ddl`, {
    confirmed_schema: confirmedSchema,
    requirements
  });
};

// 3.2 部署项目 - 适配统一响应
export const deployProject = async (projectId: string | number, confirmedDDL: string, confirmedSchema?: string, useSmartParse: boolean = false): Promise<ProjectDTO> => {
  // 后端返回 UnifiedResponse<ProjectDetailOut>
  // 响应拦截器提取后直接得到 ProjectDetailOut
  return await client.post(`/v1/projects/${projectId}/deploy`, {
    confirmed_ddl: confirmedDDL,
    confirmed_schema: confirmedSchema,
    use_smart_parse: useSmartParse
  });
};

// 4. 更新项目信息 (用于需求微调、触发重生成) - 适配统一响应
export const updateProject = async (projectId: string | number, params: UpdateProjectParams): Promise<ProjectDTO> => {
  // 后端返回 UnifiedResponse<ProjectDetailOut>
  // 响应拦截器提取后直接得到 ProjectDetailOut
  return await client.patch(`/v1/projects/${projectId}`, params);
};

// 5. 确认删除 (获取 Token) - 适配统一响应
export const confirmDeleteProject = async (projectId: string | number, confirmationText: string): Promise<ConfirmDeleteResponse> => {
  // 对应文档: POST /api/v1/projects/{project_id}/confirm-delete
  // 后端返回 UnifiedResponse<ConfirmDeleteResponse>，客户端自动提取 data
  return await client.post(`/v1/projects/${projectId}/confirm-delete`, {
    confirmation_text: confirmationText
  });
};

// 6. 删除项目 (需要 Token) - 适配统一响应
export const deleteProject = async (projectId: string | number, token: string): Promise<void> => {
  // 对应文档: DELETE /api/v1/projects/{project_id}
  // 需要 Header: X-Confirmation-Token
  // 后端返回 UnifiedResponse<null>，客户端自动处理
  await client.delete(`/v1/projects/${projectId}`, {
    headers: {
      'X-Confirmation-Token': token
    }
  });
};