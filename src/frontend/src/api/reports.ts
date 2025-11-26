import client from './client';
import { Report, QueryResult } from '../types'; // 假设类型定义在这里

// 定义创建报表的参数类型 (去掉 id 和 updatedAt，由后端生成)
export interface CreateReportParams {
  projectId: string;
  name: string;
  type: string;
  description: string;
  data: any[];
  chartConfig: {
    xAxisKey: string;
    yAxisKey: string;
  };
  sourceQueryId: string;
  sourceQueryText: string;
}

// 定义历史查询记录的类型
export interface HistoryQuery {
  id: string;
  projectId: string;
  queryText: string;
  timestamp: string;
  result: QueryResult;
}

export const reportApi = {
  // 获取指定项目的报表列表
  getReports: (projectId: string) => {
    return client.get<any, Report[]>('/reports', {
      params: { projectId }
    });
  },

  // 创建新报表
  createReport: (data: CreateReportParams) => {
    return client.post<any, Report>('/reports', data);
  },

  // 删除报表
  deleteReport: (reportId: string) => {
    return client.delete<any, void>(`/reports/${reportId}`);
  },

  // 获取项目的历史查询记录 (用于向导选择数据源)
  getHistoryQueries: (projectId: string) => {
    return client.get<any, HistoryQuery[]>('/history-queries', {
      params: { projectId }
    });
  }
};