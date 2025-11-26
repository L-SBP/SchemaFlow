import client from './client';

// 定义与后端一致的数据结构 (参考接口文档)
export interface ProjectDTO {
  project_id: string;
  project_name: string;
  project_type: 'MySQL' | 'PostgreSQL';
  description: string;
  project_status: 'initializing' | 'active' | 'error';
  created_at: string;
  // 详情字段 (轮询时返回)
  creation_stage?: 'analyzing' | 'generating_ddl' | 'deploying' | 'completed';
  progress_percentage?: number;
  analysis_result?: string;
  ddl_result?: string;
  deployment_logs?: string[];
}

export interface CreateProjectParams {
  name: string;
  type: 'MySQL' | 'PostgreSQL';
  description: string;
}

// 1. 获取项目列表
export const fetchProjects = async (): Promise<ProjectDTO[]> => {
  const response = await client.get('/projects');
  // 假设后端返回格式 { code: 200, data: [...] }，client拦截器已经解包了data
  return response.data || [];
};

// 2. 创建新项目
export const createProject = async (params: CreateProjectParams): Promise<{ project_id: string }> => {
  const response = await client.post('/projects', params);
  return response.data;
};

// 3. 获取项目详情 (包含生成进度、Schema、DDL)
export const getProjectDetail = async (projectId: string): Promise<ProjectDTO> => {
  const response = await client.get(`/projects/${projectId}`);
  return response.data;
};