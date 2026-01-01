/**
 * @file reports.ts
 * @module API/Report-Visualization
 * @description 报表与可视化分析 API 服务模块。
 * 本模块支撑系统核心特性 SF5（结果可视化），负责处理从分析查询到图形化报表的转化逻辑。
 * 核心流程：
 * 1. 溯源追踪：从历史查询记录中提取结果集元数据；
 * 2. 维度映射：配置 X/Y 轴业务指标及图表类型（柱状图、折线图等）；
 * 3. 持久化存储：将报表配置保存至项目仪表盘，实现分析结果的资产化管理。
 * @author Wang Lirong (王利蓉)
 * @version 1.4.0
 * @date 2026-01-02
 */

import client from './client';
import { Report, QueryResult } from '../types';

/**
 * 创建报表的请求参数接口
 * @interface CreateReportParams
 * @description 封装报表生成的配置元数据。
 * 注意：后端将通过 source_query_id 自动关联历史快照数据，前端无需传输冗余的结果集明细。
 * @property {string} project_id - 归属的项目 ID，确保报表在项目间物理隔离。
 * @property {string} name - 报表展示名称。
 * @property {string} type - 图表样式类型（如 'bar', 'line', 'pie' 等）。
 * @property {string} [description] - 对该可视化分析的业务背景描述。
 * @property {Object} chart_config - 图表维度配置。
 * @property {string} chart_config.x_axis_key - 映射至横轴的字段键名。
 * @property {string} chart_config.y_axis_key - 映射至纵轴的数值字段键名。
 * @property {string} source_query_id - 对应查询历史记录的唯一 ID。
 */
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

/**
 * 历史查询结果中的字段元数据定义
 * @interface HistoryQueryField
 */
export interface HistoryQueryField {
  name: string;
  type: 'string' | 'number' | 'date' | 'bool' | 'object';
}

/**
 * 携带字段类型信息的增强版查询结果集
 * @interface HistoryQueryResult
 * @extends QueryResult
 */
export interface HistoryQueryResult extends QueryResult {
  fields: HistoryQueryField[];
}

/**
 * 历史查询记录实体定义
 * @interface HistoryQuery
 * @description 用于在报表创建向导中供用户回溯和选择数据源。
 * @property {string} id - 查询记录唯一标识。
 * @property {string} project_id - 项目关联 ID。
 * @property {string} query_text - 原始 SQL 或自然语言查询文本。
 * @property {string} timestamp - 执行时间戳。
 * @property {HistoryQueryResult} result - 包含数据及字段结构的快照。
 * @property {boolean} [reportable] - 标识该查询结果是否满足可视化条件（如：必须包含数值列）。
 * @property {string | null} [unreportable_reason] - 若不可生成报表，提供业务逻辑说明。
 */
export interface HistoryQuery {
  id: string;
  project_id: string;
  query_text: string;
  timestamp: string;
  result: HistoryQueryResult;
  reportable?: boolean;
  unreportable_reason?: string | null;
}

/**
 * 报表管理 API 核心调用对象
 * 驱动“报表主界面”与“报表制作向导”的数据交互
 */
export const reportApi = {
  /**
   * 获取指定项目下的所有已保存报表列表
   * 用于渲染项目工作台中的“分析报表”选项卡及仪表盘卡片。
   * @method getReports
   * @param {string} project_id - 项目 ID
   * @returns {Promise<Report[]>} 报表对象数组
   */
  getReports: (project_id: string) => {
    // 发起 GET 请求，携带项目过滤参数执行检索
    return client.get<any, Report[]>('/v1/reports', {
      params: { project_id }
    });
  },

  /**
   * 基于选定的历史查询创建新报表
   * 实现从对话式分析到结构化可视化的跃迁。
   * @method createReport
   * @param {CreateReportParams} data - 包含报表名称、图表类型及轴配置的载荷
   * @returns {Promise<Report>} 返回新生成的报表实体
   */
  createReport: (data: CreateReportParams) => {
    // 执行 POST 请求，将前端字段名映射为后端预期的 API 字段名（如 report_name, chart_type）
    return client.post<any, Report>(`/v1/projects/${data.project_id}/reports`, {
      report_name: data.name,
      query_id: Number(data.source_query_id),
      chart_type: data.type,
      description: data.description,
      chart_config: data.chart_config
    });
  },

  /**
   * 从项目中移除指定的报表配置
   * 执行该操作仅删除可视化层级的配置，不会影响底层的查询历史或原始数据。
   * @method deleteReport
   * @param {string} reportId - 待删除报表的唯一 ID
   */
  deleteReport: (reportId: string) => {
    // 调用 DELETE 动词执行资源注销逻辑
    return client.delete<any, void>(`/v1/reports/${reportId}`);
  },

  /**
   * 调取当前项目的全量历史查询记录
   * 在“报表制作向导”的第一步中调用，允许用户基于之前的对话分析结果选择数据源。
   * @method getHistoryQueries
   * @param {string} project_id - 目标项目 ID
   * @returns {Promise<HistoryQuery[]>}
   */
  getHistoryQueries: (project_id: string) => {
    // 后端执行历史记录过滤，确保用户仅能访问其权限范围内的查询轨迹
    return client.get<any, HistoryQuery[]>('/v1/history-queries', {
      params: { project_id }
    });
  }
};