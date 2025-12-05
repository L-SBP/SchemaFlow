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

// 修改为与后端一致的字段结构
export interface Announcement {
  announcement_id: number; // 后端为 integer
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

export interface GlossaryTerm {
  id: string;
  projectId: string;
  term: string;
  definition: string;
  synonyms?: string[];
  relatedTable?: string;
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

export type CreationStage = 'initializing' | 'generating_schema' | 'generating_ddl' | 'executing_ddl' | 'completed';

export interface ProjectDTO {
  project_id: string;
  project_name: string;
  project_type: 'MySQL' | 'PostgreSQL';
  description: string;
  project_status: 'initializing' | 'active' | 'error';
  created_at: string;
  creation_stage?: CreationStage;
  progress_percentage?: number;
  analysis_result?: string;
  ddl_result?: string;
  deployment_logs?: string[];
}