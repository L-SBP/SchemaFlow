
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
  id: string;
  title: string;
  content: string;
  status: 'published' | 'draft';
  date: string;
}

export type ReportType = 'bar' | 'line' | 'pie' | 'scatter';

export interface Report {
  id: string;
  projectId: string;
  name: string;
  type: ReportType;
  description: string;
  // Stores the raw data from the query
  data: any[];
  // Configuration for how to map data to the chart
  chartConfig: {
    xAxisKey: string; // Which column is X
    yAxisKey: string; // Which column is Y (Value)
  };
  // Meta info about the source
  sourceQueryId: string;
  sourceQueryText: string;
  updatedAt: string;
}

export interface GlossaryTerm {
  id: string;
  projectId: string;
  term: string;
  definition: string;
  synonyms?: string[]; // 同义词
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


// 通用 API 响应结构
export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T;
}


// 创建项目的参数
export interface CreateProjectParams {
  name: string;
  type: 'MySQL' | 'PostgreSQL';
  description: string;
}

export type CreationStage = 'initializing' | 'generating_schema' | 'generating_ddl' | 'executing_ddl' | 'completed';


export interface CreateProjectParams {
  name: string;
  type: 'MySQL' | 'PostgreSQL';
  description: string;
}

export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T;
}


export interface Project {
  id: string;
  name: string;
  type: 'MySQL' | 'PostgreSQL';
  description: string;
  status: 'active' | 'deploying' | 'error';
  createdAt: string;
  creationStage?: CreationStage;
  analysis?: string;
  ddl?: string;
}