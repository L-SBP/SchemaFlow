// src/api/glossary.ts
import client from './client';
// 假设你的类型定义在 src/types.ts，如果路径不同请调整
import { GlossaryTerm } from '../types';

// 定义统一的响应结构
interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

// 1. 获取术语列表
export const getTerms = (projectId: string) => {
  return client.get<any, ApiResponse<GlossaryTerm[]>>('/glossary', {
    params: { projectId }
  });
};

// 2. 新增术语 (这就是报错提示缺少的 export)
export const createTerm = (data: Omit<GlossaryTerm, 'id' | 'updatedAt'>) => {
  return client.post<any, ApiResponse<GlossaryTerm>>('/glossary', data);
};

// 3. 更新术语
export const updateTerm = (id: string, data: Partial<GlossaryTerm>) => {
  return client.put<any, ApiResponse<GlossaryTerm>>(`/glossary/${id}`, data);
};

// 4. 删除术语
export const deleteTerm = (id: string) => {
  return client.delete<any, ApiResponse<void>>(`/glossary/${id}`);
};