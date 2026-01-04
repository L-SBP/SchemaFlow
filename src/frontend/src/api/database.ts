/**
 * @file database.ts
 * @module API/Database-Inspector
 * @description 数据库自省与元数据提取 API 服务模块。
 * 本模块是系统“技术无感”设计理念的核心支撑，负责从物理 MySQL/Postgres 实例中提取库表结构。
 * 提取的元数据用于驱动前端的“库表结构面板”、“动态 ER 图渲染引擎”以及“数据探查器”。
 * * 模块设计遵循以下原则：
 * 1. 结构透明化：打破 AI 生成的“黑盒”，让非技术用户直观感知数据库状态 [cite: 669]；
 * 2. 采样安全：默认采用 limit 约束，防止大数据量请求造成的瞬时链路阻塞。
 * * @author Wang Lirong (王利蓉)
 * @version 2.1.0
 * @date 2026-01-02
 */

import client from './client';

/**
 * 数据库表基础信息接口
 * @interface TableInfo
 * @description 用于 Explorer 侧边栏展示的轻量级表描述对象。
 * @property {string} name - 数据库表名
 * @property {string} [type] - 表类型（如：BASE TABLE, VIEW 等）
 */
export interface TableInfo {
  name: string;
  type?: string;
}

/**
 * 字段/列元数据详细信息接口
 * @interface ColumnInfo
 * @description 适配数据库 DESCRIBE 或 information_schema 输出的标准结构。
 * 这些元数据是 Schema Agent 验证逻辑范式 (3NF) 的重要参考 [cite: 341, 704]。
 * @property {string} field - 字段名称
 * @property {string} type - 数据类型（如：varchar(255), int 等）
 * @property {string} null - 是否允许为空 (YES/NO)
 * @property {string} key - 索引类型（PRI 为主键，UNI 为唯一键，MUL 为普通索引）
 * @property {any} default - 默认值
 * @property {string} extra - 额外属性（如：auto_increment）
 */
export interface ColumnInfo {
  field: string;
  type: string;
  null: string;
  key: string;
  default: any;
  extra: string;
}

// =========================================================
// 第一部分：基于会话 (Session ID) 的 API 体系
// 旨在支持“对话式管理”，确保查询上下文与特定分析话题绑定 [cite: 407, 706]。
// =========================================================

/**
 * 获取指定会话关联的数据库完整表结构列表
 * 常用于在对话窗口右侧实时渲染“库表可视化面板” [cite: 380, 411]。
 * @async
 * @function fetchDatabaseStructure
 * @param {number} sessionId - 当前活跃的分析会话 ID
 * @returns {Promise<TableInfo[]>} 返回包含所有业务逻辑表的数组
 */
export const fetchDatabaseStructure = async (sessionId: number): Promise<TableInfo[]> => {
  // 执行 GET 请求，获取该会话上下文下的元数据快照
  return client.get<any, TableInfo[]>(`/v1/database/${sessionId}/tables`);
};

/**
 * 分页/限量获取指定表的实时行数据
 * 用于在前端以结构化表格形式呈现原始数据采样，满足 SF5 智能结果呈现需求 [cite: 212, 602]。
 * @async
 * @function fetchTableData
 * @param {number} sessionId - 会话识别码
 * @param {string} tableName - 目标查询表名
 * @returns {Promise<any[]>} 返回 JSON 格式的行记录数组
 */
export const fetchTableData = async (sessionId: number, tableName: string): Promise<any[]> => {
  // 默认限制返回 100 条记录，以平衡加载性能与用户探查需求
  return client.get<any, any[]>(`/v1/database/${sessionId}/tables/${tableName}/data`, {
    params: { limit: 100 }
  });
};

/**
 * 获取指定表的详细 Schema 定义（列元数据）
 * 该接口为“图形化 ER 关系图”组件提供数据支撑，展示字段含义及约束 [cite: 101, 682]。
 * @async
 * @function fetchTableSchema
 * @param {number} sessionId - 会话标识
 * @param {string} tableName - 待分析的表名
 * @returns {Promise<ColumnInfo[]>} 字段详情定义列表
 */
export const fetchTableSchema = async (sessionId: number, tableName: string): Promise<ColumnInfo[]> => {
  // 从后端元数据库或物理实例中实时检索列属性
  return client.get<any, ColumnInfo[]>(`/v1/database/${sessionId}/tables/${tableName}/schema`);
};

// =========================================================
// 第二部分：基于项目 (Project ID) 的 API 体系
// 旨在支持“项目级隔离”与全局管理逻辑，无需依赖特定对话上下文 [cite: 104, 286]。
// 适用于项目工作台 (Workspace) 的初始化加载流程。
// =========================================================

/**
 * 通过项目 ID 获取物理数据库的所有表清单
 * 实现项目工作台 (Workspace) 左侧 Explorer 树状菜单的动态构建 [cite: 247]。
 * @async
 * @function fetchDatabaseStructureByProject
 * @param {number} projectId - 物理项目 ID
 * @returns {Promise<TableInfo[]>}
 */
export const fetchDatabaseStructureByProject = async (projectId: number): Promise<TableInfo[]> => {
  // 调用项目级元数据端点，该操作不涉及会话上下文记忆
  return client.get<any, TableInfo[]>(`/v1/database/project/${projectId}/tables`);
};

/**
 * 通过项目 ID 探查特定表的数据样本
 * 用于非会话模式下的通用数据管理与内容核对逻辑。
 * @async
 * @function fetchTableDataByProject
 * @param {number} projectId - 项目唯一标识
 * @param {string} tableName - 物理表名
 */
export const fetchTableDataByProject = async (projectId: number, tableName: string): Promise<any[]> => {
  // 执行带参数的数据采样请求
  return client.get<any, any[]>(`/v1/database/project/${projectId}/tables/${tableName}/data`, {
    params: { limit: 100 }
  });
};

/**
 * 通过项目 ID 调取表的 Schema 详细架构信息
 * 用于构建项目级的“数据字典”或静态 ER 图展示。
 * @async
 * @function fetchTableSchemaByProject
 * @param {number} projectId - 项目 ID
 * @param {string} tableName - 表名
 * @returns {Promise<ColumnInfo[]>}
 */
export const fetchTableSchemaByProject = async (projectId: number, tableName: string): Promise<ColumnInfo[]> => {
  // 发起对特定项目下表结构的深度检索
  return client.get<any, ColumnInfo[]>(`/v1/database/project/${projectId}/tables/${tableName}/schema`);
};