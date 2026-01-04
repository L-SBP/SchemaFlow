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
  updated_at: number;
  current_model?: string | null;
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
  project_id: string;
  name: string;
  type: ReportType;
  description: string;
  data: any[];
  chart_config: {
    x_axis_key: string;
    y_axis_key: string;
  };
  source_query_id: string;
  source_query_text: string;
  updated_at: string;
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

// Unified Response Structure (replacing ApiResponse)
export interface UnifiedResponse<T = any> {
  code: number;
  message: string;
  data: T | null;
}

// Pagination Data Structure
export interface PageData<T = any> {
  total: number;
  page: number;
  page_size: number;
  items: T;
}

// Business Status Code Enumeration
export enum BusinessCode {
  SUCCESS = 0,
  VALIDATION_ERROR = 10000,
  BUSINESS_ERROR = 20000,
  PERMISSION_ERROR = 30000,
  SYSTEM_ERROR = 50000
}

// Business Error Class
export class BusinessError extends Error {
  constructor(
    public code: number,
    message: string,
    public details?: any
  ) {
    super(message);
    this.name = 'BusinessError';
  }

  isValidationError(): boolean {
    return this.code >= 10000 && this.code < 20000;
  }

  isBusinessError(): boolean {
    return this.code >= 20000 && this.code < 30000;
  }

  isPermissionError(): boolean {
    return this.code >= 30000 && this.code < 40000;
  }

  isSystemError(): boolean {
    return this.code >= 50000 || (this.code >= 40000 && this.code < 50000);
  }

  isHttpError(): boolean {
    return this.code >= 400 && this.code < 600;
  }
}

// Legacy alias for backward compatibility
export interface ApiResponse<T = any> extends UnifiedResponse<T> { }

export interface CreateProjectParams {
  name: string;
  type: 'MySQL' | 'PostgreSQL' | 'SQLite';
  description: string;
}

export enum ProjectStatusEnum {
  INITIALIZING = 'initializing',
  PENDING_CONFIRMATION = 'pending_confirmation',
  ACTIVE = 'active',
  DELETED = 'deleted'
}

export enum CreationStageEnum {
  INITIALIZING = 'initializing',
  GENERATING_SCHEMA = 'generating_schema',
  SCHEMA_GENERATED = 'schema_generated',
  GENERATING_DDL = 'generating_ddl',
  DDL_GENERATED = 'ddl_generated',
  EXECUTING_DDL = 'executing_ddl',
  COMPLETED = 'completed'
}

export interface ProjectDTO {
  project_id: number;
  project_name: string;
  db_type: 'mysql' | 'postgresql' | 'sqlite';
  description: string;
  project_status: ProjectStatusEnum;
  created_at: string;
  updated_at?: string;
  creation_stage?: CreationStageEnum;
  schema_definition?: Record<string, any>;
  ddl_statement?: string;
  er_diagram_code?: string;
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
  avatar_url?: string;
}

export interface AdminUserListResponse {
  total: number;
  page: number;
  page_size: number;
  items: AdminUserListItem[];
}

export interface AdminUserProjectItem {
  project_id: number;
  project_name: string;
  db_type: string | null;
  project_status: string;
  created_at: string;
  description: string | null;
}

export interface AdminUserLoginHistoryItem {
  login_id: number;
  login_time: string;
  logout_time: string | null;
  ip_address: string;
  user_agent: string | null;
  login_status: string;
  failure_reason: string | null;
}

export interface AdminUserDetailResponse {
  user_id: number;
  username: string;
  email: string;
  status: 'normal' | 'suspended' | 'banned';
  max_databases: number;
  project_count: number;
  last_login_at: string | null;
  created_at: string | null;
  avatar_url?: string;
  projects: AdminUserProjectItem[];
  login_history: AdminUserLoginHistoryItem[];
}

export interface AdminListItem {
  user_id: number;
  username: string;
  email: string;
  avatar_url?: string;
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
  event_type: string;
  event_description: string;
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

export interface ChatRequest {
  content: string;
  model?: string;
}

export interface ChatResponse {
  message_id: number;
  session_id?: number;
  message_type: 'user' | 'assistant';
  content: string;
  sql_text?: string;              // 与后端一致
  sql_type: string;               // 新增字段
  requires_confirmation: boolean; // 新增字段
  data?: Array<Record<string, any>>; // 与后端一致，替代query_result
  created_at?: string;
}

// Session API Types
export interface SessionItem {
  session_id: number;
  session_name: string;
  project_id: number;
  created_at: string;
  last_activity: string | null;
}

// User API Types
export interface UserMe {
  user_id: number;
  username: string;
  email: string;
  status: 'normal' | 'suspended' | 'banned';
  used_databases: number;
  max_databases: number;
  avatar_url: string | null;
  is_admin: boolean;
  last_login_at: string | null;
  created_at: string;
}

export interface LoginData {
  access_token: string;
  token_type: string;
  user: UserMe;
}

export interface LoginHistoryItem {
  login_id: number;
  login_time: string;
  logout_time: string | null;
  ip_address: string;
  user_agent: string | null;
  login_status: 'success' | 'failed' | 'expired' | 'forced_logout';
}

// ========================================
// AI 模型配置相关类型（精简版）
// ========================================

export interface AIModelConfigResponse {
  config_id: number;
  model_name: string;
  api_url: string;
  model_id: string;
  model_type: 'local_finetune' | 'general_llm';
  created_at: string;
  updated_at: string;
}

export interface AIModelConfigDetailResponse extends AIModelConfigResponse {
  api_key_masked: string;
}

export interface AIModelConfigListResponse {
  total: number;
  items: AIModelConfigResponse[];
}

export interface AIModelConfigCreate {
  model_name: string;
  api_url: string;
  model_id: string;
  api_key: string;
  model_type: 'local_finetune' | 'general_llm';
}

export interface AIModelConfigUpdate {
  model_name?: string;
  api_url?: string;
  model_id?: string;
  api_key?: string;
  model_type?: 'local_finetune' | 'general_llm';
}

// 测试连接请求/响应
export interface AIModelTestConnectionRequest {
  api_url: string;
  api_key?: string;  // 可选，编辑模式下可以使用已保存的密钥
  model_id: string;
  config_id?: number;  // 可选，编辑模式下传递以使用已保存的密钥
}

export interface AIModelTestConnectionResponse {
  success: boolean;
  message: string;
  response_time_ms?: number;
}

export interface AIModelOption {
  model_name: string;
  model_type: string;
}

export interface AIModelOptionsResponse {
  items: AIModelOption[];
}
