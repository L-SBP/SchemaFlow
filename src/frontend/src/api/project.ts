/**
 * @file project.ts
 * @module API/Project-Lifecycle-Management
 * @description 项目生命周期与 AI 协同核心 API 模块。
 * 本模块是“基于大模型多智能体框架的数据库自动部署与库表生成系统”的业务引擎核心。
 * 负责处理从项目初始化、自然语言需求分析、Schema 逻辑建模、DDL 语句生成到物理部署的全链路流程。
 * * 核心特性支撑：
 * 1. 异步生成流：对接后端基于 Celery/FastAPI 的异步任务队列，支持进度实时回显（SF2）；
 * 2. 智能可视化：触发动态 ER 图渲染逻辑（SF5）；
 * 3. 安全删除锁：实施基于二次令牌验证的资源销毁保护策略。
 * * @author Wang Lirong (王利蓉)
 * @version 3.0.0 (适配迭代开发计划第三稿)
 * @date 2026-01-02
 */

import client from './client';
import { ProjectDTO, PageData } from '../types';

/** * 透传项目数据传输对象类型定义 
 */
export type { ProjectDTO };

/**
 * 创建新项目的请求参数接口
 * @interface CreateProjectParams
 * @description 封装项目初始化的元数据。
 * @property {string} name - 项目展示名称，用于在 Dashboard 识别不同业务模块。
 * @property {string} type - 目标数据库类型。新增支持 SQLite 以满足轻量级本地化实验需求。
 * @property {string} description - 业务背景描述，作为 Schema Agent 进行需求提取的原始语料。
 */
export interface CreateProjectParams {
  name: string;
  type: 'MySQL' | 'PostgreSQL' | 'SQLite';
  description: string;
}

/**
 * 更新项目信息的请求参数接口 (PATCH)
 * @interface UpdateProjectParams
 * @description 对应需求微调场景，允许用户在不销毁项目的前提下修改业务逻辑倾向。
 * @property {string} [project_name] - 可选的项目重命名。
 * @property {string} [description] - 增量更新的业务描述。
 * @property {Record<string, any>} [schema_definition] - AI 生成的逻辑 Schema JSON 对象。
 */
export interface UpdateProjectParams {
  project_name?: string;
  description?: string;
  schema_definition?: Record<string, any>;
}

/**
 * 确认删除操作的响应结构
 * @interface ConfirmDeleteResponse
 * @description 实现双重确认机制。后端生成临时令牌以防止误操作导致的数据丢失。
 * @property {string} confirmation_token - 具有时效性的二次验证令牌。
 * @property {string} expires_at - 令牌过期的时间戳（ISO 8601）。
 */
export interface ConfirmDeleteResponse {
  confirmation_token: string;
  expires_at: string;
}

/**
 * 项目创建初始响应
 * @interface CreateProjectResponse
 */
export interface CreateProjectResponse {
  project_id: number;
  message: string;
}

// =========================================================
// 项目管理核心服务集
// =========================================================

/**
 * 1. 获取当前用户所属的所有项目列表
 * 实现 Workspace 主页的项目卡片网格渲染。
 * 采用 PageData 包装器以适配后端的统一分页协议。
 * @async
 * @function fetchProjects
 * @returns {Promise<PageData<ProjectDTO[]>>} 包含项目简明信息的列表
 */
export const fetchProjects = async (): Promise<PageData<ProjectDTO[]>> => {
  // 响应拦截器会自动从 UnifiedResponse<PageData<ProjectDTO[]>> 中提取 data 部分
  return await client.get('/v1/projects/');
};

/**
 * 2. 初始化创建新数据库项目
 * 该操作会触发后端的项目命名空间分配及元数据入库流程。
 * @async
 * @function createProject
 * @param {CreateProjectParams} params - 项目创建所需的配置参数
 * @returns {Promise<CreateProjectResponse>} 包含新生成的项目 ID
 */
export const createProject = async (params: CreateProjectParams): Promise<CreateProjectResponse> => {
  // 适配接口文档：POST /api/v1/projects/
  return await client.post('/v1/projects/', {
    project_name: params.name,
    db_type: params.type.toLowerCase(), // 严格遵循后端数据库标识规范（全小写）
    description: params.description
  });
};

/**
 * 3. 获取特定项目的详尽档案信息
 * 返回数据涵盖生成进度、逻辑 Schema 定义、当前 DDL 语句及数据库连接参数。
 * 常用于工作台 (Workspace) 的状态恢复与初始化加载。
 * @async
 * @function getProjectDetail
 * @param {string | number} projectId - 目标项目唯一标识
 * @returns {Promise<ProjectDTO>}
 */
export const getProjectDetail = async (projectId: string | number): Promise<ProjectDTO> => {
  // 后端返回 UnifiedResponse<ProjectDetailOut>，此处直接解包为业务对象
  return await client.get(`/v1/projects/${projectId}`);
};

/**
 * 3.1 触发 DDL 语句自动化生成流程
 * 核心逻辑：用户确认逻辑 Schema 后，调用 DDL Agent 基于目标数据库方言（Dialect）生成部署脚本。
 * 该操作通常为异步任务，前端需监听进度条状态。
 * @async
 * @function generateDDL
 * @param {string | number} projectId - 项目 ID
 * @param {string} confirmedSchema - 用户核对并微调后的 JSON Schema 文本
 * @param {string} [requirements] - 额外的约束需求（如：必须包含审计字段、使用 InnoDB 等）
 */
export const generateDDL = async (projectId: string | number, confirmedSchema: string, requirements?: string): Promise<void> => {
  // 调用后端异步任务端点，启动多智能体协作流
  await client.post(`/v1/projects/${projectId}/generate-ddl`, {
    confirmed_schema: confirmedSchema,
    requirements
  });
};

/**
 * 3.2 执行物理数据库部署
 * 这是“技术无感”流程的最后一步。后端会在独立 MySQL/PostgreSQL 实例中执行 DDL 语句。
 * 实现 SF1 自动化部署特性。
 * @async
 * @function deployProject
 * @param {string | number} projectId - 项目 ID
 * @param {string} confirmedDDL - 最终核准的 SQL 语句全集
 * @param {string} [confirmedSchema] - 同步更新的逻辑架构定义
 * @param {boolean} [useSmartParse=false] - 是否启用智能解析以优化字段映射
 * @returns {Promise<ProjectDTO>} 返回部署完成后的最新项目状态
 */
export const deployProject = async (projectId: string | number, confirmedDDL: string, confirmedSchema?: string, useSmartParse: boolean = false): Promise<ProjectDTO> => {
  return await client.post(`/v1/projects/${projectId}/deploy`, {
    confirmed_ddl: confirmedDDL,
    confirmed_schema: confirmedSchema,
    use_smart_parse: useSmartParse
  });
};

/**
 * 3.3 异步重新生成 ER 关系图数据
 * 基于当前的 Schema 定义，通过可视化智能体生成符合 Mermaid 或 Graphviz 规范的渲染描述。
 * 对应 SF5 可视化增强特性 [cite: 85-87]。
 * @async
 * @function regenerateER
 * @param {string | number} projectId - 项目 ID
 * @param {string} schemaText - 用于生成图形的 Schema 原始定义
 * @param {string} [aiModel='gpt4'] - 指定绘图辅助大模型，默认为 GPT-4o 以获得最佳逻辑关联性
 * @returns {Promise<{ task_id: string; message: string }>} 返回异步任务 ID 用于轮询状态
 */
export const regenerateER = async (projectId: string | number, schemaText: string, aiModel: string = 'gpt4'): Promise<{ task_id: string; message: string }> => {
  return await client.post(`/v1/projects/${projectId}/regenerate-er`, {
    schema_text: schemaText,
    ai_model: aiModel
  });
};

/**
 * 4. 动态更新项目核心元数据
 * 用于在项目进行过程中，手动触发需求微调或修正 AI 生成的错误定义。
 * 修改后通常需要重新调用生成流程以保证数据一致性。
 * @async
 * @function updateProject
 */
export const updateProject = async (projectId: string | number, params: UpdateProjectParams): Promise<ProjectDTO> => {
  // 使用局部更新动词 PATCH
  return await client.patch(`/v1/projects/${projectId}`, params);
};

/**
 * 5. 安全审计：发起删除确认请求
 * 对应 Usability-2 与 Security-3 约束：针对危险操作执行双重确认提示 。
 * 管理员或用户需在前端输入项目名称作为确认文本。
 * @async
 * @function confirmDeleteProject
 * @param {string | number} projectId - 待删除项目 ID
 * @param {string} confirmationText - 用户输入的确认标识（通常为项目名）
 * @returns {Promise<ConfirmDeleteResponse>} 包含下一步操作所需的临时 Token
 */
export const confirmDeleteProject = async (projectId: string | number, confirmationText: string): Promise<ConfirmDeleteResponse> => {
  return await client.post(`/v1/projects/${projectId}/confirm-delete`, {
    confirmation_text: confirmationText
  });
};

/**
 * 6. 执行物理资源的最终删除
 * 此操作不可逆。需要携带上一步获取的授权 Token 方可执行。
 * 实现 Security-1 项目级物理隔离的闭环管理。
 * @async
 * @function deleteProject
 * @param {string | number} projectId - 项目 ID
 * @param {string} token - 由 confirmDeleteProject 签发的限时确认令牌
 */
export const deleteProject = async (projectId: string | number, token: string): Promise<void> => {
  // 将授权令牌注入自定义 Header 字段 X-Confirmation-Token
  await client.delete(`/v1/projects/${projectId}`, {
    headers: {
      'X-Confirmation-Token': token
    }
  });
};