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

