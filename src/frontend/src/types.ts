export enum UserRole {
  USER = 'USER',
  ADMIN = 'ADMIN'
}

export enum UserStatus {
  NORMAL = 'NORMAL',
  BANNED = 'BANNED',
  SUSPENDED = 'SUSPENDED'
}

// 通用 User 接口（用于前端应用内部状态）
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
  type: 'MySQL' | 'PostgreSQL' | 'SQLite';
  description: string;
  status: 'active' | 'deploying' | 'error' | 'deleted';
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
  requiresConfirmation?: boolean;
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

// 旧的 RiskEvent 接口，保留以防有遗留引用，但主要使用 ViolationLogListItem
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
  type: 'MySQL' | 'PostgreSQL' | 'SQLite';
  description: string;
}

export type CreationStage = 'initializing' | 'analyzing' | 'generating_schema' | 'generating_ddl' | 'deploying' | 'completed';

export interface ProjectDTO {
  project_id: string;
  project_name: string;
  db_type: 'mysql' | 'postgresql' | 'sqlite';
  description: string;
  project_status: 'initializing' | 'active' | 'error' | 'deleted';
  created_at: string;
  updated_at?: string;
  creation_stage?: CreationStage;
  progress_percentage?: number;
  schema_definition?: Record<string, any>;
  analysis_result?: string;
  ddl_result?: string;
  deployment_logs?: string[];
}

export interface KnowledgeTerm {
  knowledge_id: number;
  project_id: number;
  term: string;
  definition: string;
  examples?: string | null;
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

// --- Admin API Response Types ---

export interface AdminStats {
  active_users_today: number;
  total_projects: number;
  query_count_today: number;
  high_risk_operations_today: number;
  system_health: 'good' | 'warning' | 'critical';
}

export interface AdminUserListItem {
  user_id: number;
  username: string;
  email: string;
  status: 'normal' | 'suspended' | 'banned';
  project_count: number;
  max_databases: number;
  last_login_at: string | null;
}

export interface AdminUserListResponse {
  total: number;
  page: number;
  page_size: number;
  items: AdminUserListItem[];
}

export interface AdminListItem {
  user_id: number;
  username: string;
  email: string;
  last_login_at: string;
  is_online: boolean;
}

export interface AdminListResponse {
  total: number;
  page: number;
  page_size: number;
  items: AdminListItem[];
}

export interface ViolationLogListItem {
  violation_id: number;
  user_id: number;
  username: string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  resolution_status: 'pending' | 'in_progress' | 'resolved' | 'ignored';
  created_at: string;
}

export interface ViolationLogListResponse {
  total: number;
  page: number;
  page_size: number;
  items: ViolationLogListItem[];
}