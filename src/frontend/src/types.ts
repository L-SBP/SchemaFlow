export enum UserRole {
  USER = 'USER',
  ADMIN = 'ADMIN'
}

export enum UserStatus {
  NORMAL = 'NORMAL',
  BANNED = 'BANNED'
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  lastLogin: string;
  projectQuota: number;
  isOnline?: boolean;
  lastLoginIp?: string;
  avatar_url?: string;
}

export interface Project {
  id: string;
  name: string;
  type: 'MySQL' | 'PostgreSQL';
  description: string;
  status: 'active' | 'deploying' | 'error';
  createdAt: string;
}

export interface ChartData {
  [key: string]: any;
}

export interface QueryResult {
  columns: string[];
  data: any[];
}

export interface Message {
  id: string;
  role: 'user' | 'model';
  text: string;
  type: 'text' | 'table' | 'chart' | 'error' | 'code-block';
  tableData?: QueryResult;
  chartData?: ChartData[];
  sql?: string;
  code?: string;
  language?: string;
  timestamp: number;
  status?: 'pending' | 'executed' | 'cancelled';
}

export interface ChatSession {
  id: string;
  name: string;
  messages: Message[];
  updatedAt: number;
}

export interface Announcement {
  announcement_id: number;
  title: string;
  content: string;
  status: 'published' | 'draft' | 'unpublished' | 'expired';
  created_at: string;
  updated_at?: string | null;
  created_by?: number | null;
}

export type ReportType = 'bar' | 'line' | 'pie' | 'scatter';

export interface Report {
  id: string;
  projectId: string;
  name: string;
  type: ReportType;
  description: string;
  data: any[];
  chartConfig: {
    xAxisKey: string;
    yAxisKey: string;
  };
  sourceQueryId: string;
  sourceQueryText: string;
  updatedAt: string;
}

export interface RiskEvent {
  id: string;
  type: 'sql_injection' | 'abnormal_login' | 'high_frequency';
  level: 'high' | 'medium' | 'low';
  sourceIp: string;
  description: string;
  timestamp: string;
  status: 'pending' | 'blocked' | 'ignored';
}

export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T;
}

export interface CreateProjectParams {
  name: string;
  type: 'MySQL' | 'PostgreSQL';
  description: string;
}

export type CreationStage = 'initializing' | 'analyzing' | 'generating_schema' | 'generating_ddl' | 'deploying' | 'completed';

// 对应文档中的 ProjectResponse 数据模型
export interface ProjectDTO {
  project_id: string;
  project_name: string;
  project_type: 'MySQL' | 'PostgreSQL';
  description: string;
  project_status: 'initializing' | 'active' | 'error';
  created_at: string;
  updated_at?: string;

  // 详情字段 (用于进度展示)
  creation_stage?: CreationStage;
  progress_percentage?: number;

  // 核心生成结果
  schema_definition?: Record<string, any>; // 对应文档 schema_definition
  analysis_result?: string; // Schema 分析文本
  ddl_result?: string;      // SQL DDL

  deployment_logs?: string[];
}

// --- 业务术语管理类型 (Knowledge) ---

export interface KnowledgeTerm {
  knowledge_id: number;
  project_id: number;
  term: string;       // 业务术语名称
  definition: string; // 术语定义
  examples?: string | null; // 使用示例
  created_at: string;
}

export interface KnowledgeCreateRequest {
  term: string;
  definition: string;
  examples?: string;
}

export interface KnowledgeUpdateRequest {
  term?: string;
  definition?: string;
  examples?: string;
}

export interface KnowledgeListResponse {
  total: number;
  page: number;
  page_size: number;
  items: KnowledgeTerm[];
}

export interface KnowledgeImportResponse {
  imported_count: number;
  failed_count: number;
  failures: {
    row: number;
    error: string;
  }[];
}

export interface KnowledgeExportResponse {
  download_url: string;
  expires_at: string;
}

