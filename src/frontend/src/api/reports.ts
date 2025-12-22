import client from './client';
import { Report, QueryResult } from '../types';

// 后端会从 query_id 关联 QueryResult 获取 data，因此创建报表无需传 data。
export interface CreateReportParams {
  projectId: string;
  name: string;
  type: string;
  description?: string;
  chartConfig: {
    xAxisKey: string;
    yAxisKey: string;
  };
  sourceQueryId: string;
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
  projectId: string;
  queryText: string;
  timestamp: string;
  result: HistoryQueryResult;
  reportable?: boolean;
  unreportableReason?: string | null;
}

export const reportApi = {
  // 获取指定项目的报表列表
  getReports: (projectId: string) => {
    return client.get<any, Report[]>('/v1/reports', {
      params: { projectId }
    });
  },

  // 创建新报表
  createReport: (data: CreateReportParams) => {
    return client.post<any, Report>(`/v1/projects/${data.projectId}/reports`, {
      report_name: data.name,
      query_id: Number(data.sourceQueryId),
      chart_type: data.type,
      description: data.description,
      chartConfig: data.chartConfig
    });
  },

  // 删除报表
  deleteReport: (reportId: string) => {
    return client.delete<any, void>(`/v1/reports/${reportId}`);
  },

  // 获取项目的历史查询记录 (用于向导选择数据源)
  getHistoryQueries: (projectId: string) => {
    return client.get<any, HistoryQuery[]>('/v1/history-queries', {
      params: { projectId }
    });
  }
};