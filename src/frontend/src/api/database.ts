import client from './client';

export interface TableInfo {
  name: string;
  type?: string;
}

export interface ColumnInfo {
  field: string;
  type: string;
  null: string;
  key: string;
  default: any;
  extra: string;
}

// =========================================================
// 基于 Session ID 的 API（保留兼容性）
// =========================================================

export const fetchDatabaseStructure = async (sessionId: number): Promise<TableInfo[]> => {
  return client.get<any, TableInfo[]>(`/v1/database/${sessionId}/tables`);
};

export const fetchTableData = async (sessionId: number, tableName: string): Promise<any[]> => {
  return client.get<any, any[]>(`/v1/database/${sessionId}/tables/${tableName}/data`, {
    params: { limit: 100 }
  });
};

export const fetchTableSchema = async (sessionId: number, tableName: string): Promise<ColumnInfo[]> => {
  return client.get<any, ColumnInfo[]>(`/v1/database/${sessionId}/tables/${tableName}/schema`);
};

// =========================================================
// 基于 Project ID 的 API（无需创建会话）
// =========================================================

export const fetchDatabaseStructureByProject = async (projectId: number): Promise<TableInfo[]> => {
  return client.get<any, TableInfo[]>(`/v1/database/project/${projectId}/tables`);
};

export const fetchTableDataByProject = async (projectId: number, tableName: string): Promise<any[]> => {
  return client.get<any, any[]>(`/v1/database/project/${projectId}/tables/${tableName}/data`, {
    params: { limit: 100 }
  });
};

export const fetchTableSchemaByProject = async (projectId: number, tableName: string): Promise<ColumnInfo[]> => {
  return client.get<any, ColumnInfo[]>(`/v1/database/project/${projectId}/tables/${tableName}/schema`);
};

