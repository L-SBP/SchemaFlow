import client from './client';
import { Report, QueryResult } from '../types';

// 后端会从 query_id 关联 QueryResult 获取 data，因此创建报表无需传 data。
export interface CreateReportParams {
  project_id: string;
  name: string;
  type: string;
  description?: string;
  chart_config: {
    x_axis_key: string;
    y_axis_key: string;
  };
  source_query_id: string;
}

export interface HistoryQueryField {
  name: string;
  type: 'string' | 'number' | 'date' | 'bool' | 'object';
}

export interface HistoryQueryResult extends QueryResult {
  fields: HistoryQueryField[];
}

// 定义历史查询记录的类型
export interface HistoryQuery {
  id: string;
  project_id: string;
  query_text: string;
  timestamp: string;
  result: HistoryQueryResult;
  reportable?: boolean;
  unreportable_reason?: string | null;
}

export const reportApi = {
  // 获取指定项目的报表列表
  getReports: (project_id: string) => {
    return client.get<any, Report[]>('/v1/reports', {
      params: { project_id }
    });
  },

  // 创建新报表
  createReport: (data: CreateReportParams) => {
    return client.post<any, Report>(`/v1/projects/${data.project_id}/reports`, {
      report_name: data.name,
      query_id: Number(data.source_query_id),
      chart_type: data.type,
      description: data.description,
      chart_config: data.chart_config
    });
  },

  // 删除报表
  deleteReport: (reportId: string) => {
    return client.delete<any, void>(`/v1/reports/${reportId}`);
  },

  // 获取项目的历史查询记录 (用于向导选择数据源)
  getHistoryQueries: (project_id: string) => {
    return client.get<any, HistoryQuery[]>('/v1/history-queries', {
      params: { project_id }
    });
  }
};