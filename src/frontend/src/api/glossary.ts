/**
 * @file glossary.ts
 * @module API/Glossary-Knowledge-Base
 * @description 业务术语库（知识库）管理 API 模块。
 * 本模块对应系统核心特性 SF7（领域知识增强），旨在通过建立业务术语与技术字段的映射关系，
 * 为多智能体框架提供行业上下文支持。
 * 核心功能：
 * 1. 术语的 CRUD 管理；
 * 2. 批量审计与清理；
 * 3. 基于 Multipart/form-data 的外部知识导入。
 * @author Wang Lirong (王利蓉)
 * @version 1.2.0
 * @date 2026-01-02
 */

import client from './client.ts';
import {
  KnowledgeTerm,
  KnowledgeListResponse,
  KnowledgeImportResponse
} from '../types.ts';

/**
 * 创建业务术语的请求参数接口
 * @interface CreateTermParams
 * @description 封装新术语录入时的核心元数据
 * @property {string} term - 业务术语名称（如：“日活”、“订单状态”）
 * @property {string} definition - 术语的精确业务定义，用于 LLM 的 Prompt 增强
 * @property {string} [examples] - 可选：提供该术语在实际场景中的应用示例或枚举值
 */
export interface CreateTermParams {
  term: string;
  definition: string;
  examples?: string;
}

/**
 * 更新业务术语的请求参数接口
 * @interface UpdateTermParams
 * @description 支持对现有术语进行增量更新
 */
export interface UpdateTermParams {
  term?: string;
  definition?: string;
  examples?: string;
}

/**
 * 业务术语 API 核心调用对象
 * 为“知识增强”面板提供数据交互支撑
 */
export const glossaryApi = {
  /**
   * 2. 分页获取当前项目的术语列表
   * 允许用户在工作台右侧面板中检索已录入的知识条目。
   * 支持基于关键词的模糊搜索，提升大规模术语库下的定位效率。
   * @method getList
   * @param {string} projectId - 关联的项目唯一识别码
   * @param {number} [page=1] - 当前请求页码
   * @param {number} [pageSize=20] - 每页展示的数据量
   * @param {string} [search] - 搜索关键词（匹配术语名或定义）
   * @returns {Promise<KnowledgeListResponse>} 包含分页元数据与术语数组的 Promise
   */
  getList: (projectId: string, page: number = 1, pageSize: number = 20, search?: string) => {
    // 构造带有分页和搜索过滤器的 GET 请求
    return client.get<any, KnowledgeListResponse>(`/v1/projects/${projectId}/knowledge`, {
      params: {
        page,
        page_size: pageSize,
        search
      }
    });
  },

  /**
   * 1. 在指定项目下创建新的业务术语
   * 录入后的术语将立即进入 Agent 的感知范围，辅助后续的 SQL 生成。
   * @method create
   * @param {string} projectId - 项目 ID
   * @param {CreateTermParams} data - 术语定义数据载荷
   * @returns {Promise<KnowledgeTerm>} 返回新创建的术语对象（含服务端生成的 ID）
   */
  create: (projectId: string, data: CreateTermParams) => {
    // 发起 POST 请求执行知识入库
    return client.post<any, KnowledgeTerm>(`/v1/projects/${projectId}/knowledge`, data);
  },

  /**
   * 3. 更新现有术语的详细信息
   * 允许用户修正过时的业务定义或补充应用示例。
   * @method update
   * @param {string} projectId - 项目 ID
   * @param {number} knowledgeId - 待修改术语的自增 ID
   * @param {UpdateTermParams} data - 包含待修改字段的对象
   */
  update: (projectId: string, knowledgeId: number, data: UpdateTermParams) => {
    // 使用 PATCH 方法进行局部字段更新，符合 RESTful 设计范式
    return client.patch<any, KnowledgeTerm>(`/v1/projects/${projectId}/knowledge/${knowledgeId}`, data);
  },

  /**
   * 4. 批量删除选定的业务术语
   * 支持在管理面板中进行多选后的统一清理操作。
   * @method deleteBatch
   * @param {string} projectId - 项目 ID
   * @param {number[]} ids - 待删除的术语 ID 数组
   * @returns {Promise<KnowledgeImportResponse>}
   */
  deleteBatch: (projectId: string, ids: number[]) => {
    /**
     * 注意：根据 Axios 规范，DELETE 请求若需携带请求体 (Body)，
     * 必须显式放置在配置对象的 data 属性中。
     */
    return client.delete<any, KnowledgeImportResponse>(`/v1/projects/${projectId}/knowledge/batch`, {
      data: { ids } 
    });
  },

  /**
   * 5. 导入术语库文件 (支持 Excel/CSV)
   * 对应项目需求中的“批量导入”功能。通过上传标准化模板，
   * 快速构建特定行业的知识图谱初步原型。
   * @method importTerms
   * @param {string} projectId - 项目 ID
   * @param {File} file - 待上传的二进制文件对象
   */
  importTerms: (projectId: string, file: File) => {
    // 初始化 FormData 对象以支持 RFC 7578 标准的多部分表单上传
    const formData = new FormData();
    // 注入文件流，后端将通过 'file' 键名进行解析
    formData.append('file', file);

    /**
     * 发起文件上传请求。
     * 必须显式声明 Content-Type 为 multipart/form-data，
     * 确保底层传输协议能够正确处理二进制数据流。
     */
    return client.post<any, KnowledgeImportResponse>(`/v1/projects/${projectId}/knowledge/import`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  }
};