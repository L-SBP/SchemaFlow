/**
 * @file announcement.ts
 * @module API/Announcement
 * @description 系统公告管理 API 模块。
 * 本模块负责系统全局通知的发布与维护，用于向用户传达系统维护、版本更新及重要政策变动。
 * 根据项目需求，系统公告支持全生命周期管理，包括草稿保存、立即发布及撤回功能 [cite: 521]。
 * @author Wang Lirong (王利蓉)
 * @version 1.3.0
 * @date 2026-01-02
 */

import client from './client.ts';
import { Announcement } from '../types.ts';

/**
 * 公告列表响应接口定义
 * @interface AnnouncementListResponse
 * @description 封装分页查询公告列表时的标准返回结构 [cite: 525, 533]
 * @property {number} total - 符合过滤条件的公告总数
 * @property {number} page - 当前返回的数据页码
 * @property {number} page_size - 单页数据容量
 * @property {Announcement[]} items - 包含公告详细对象的数组
 */
interface AnnouncementListResponse {
  total: number;
  page: number;
  page_size: number;
  items: Announcement[];
}

/**
 * 创建公告的请求参数接口
 * @export @interface CreateAnnouncementParams
 * @description 管理员创建新公告时所需的最小数据集 [cite: 526, 533]
 * @property {string} title - 公告标题，需精炼表达通知核心内容
 * @property {string} content - 公告正文，支持详细的业务逻辑或维护说明
 * @property {string} [status] - 初始状态：'published' (立即发布) 或 'draft' (存为草稿)
 */
export interface CreateAnnouncementParams {
  title: string;
  content: string;
  status?: 'published' | 'draft';
}

/**
 * 更新公告的请求参数接口
 * @export @interface UpdateAnnouncementParams
 * @description 允许对现有公告进行增量或全量修改的参数集合 [cite: 533]
 * @property {string} [title] - 修改后的标题
 * @property {string} [content] - 修改后的公告内容
 * @property {string} [status] - 变更后的公告状态：发布、草稿、撤下或过期
 */
export interface UpdateAnnouncementParams {
  title?: string;
  content?: string;
  status?: 'published' | 'draft' | 'unpublished' | 'expired';
}

/**
 * 公告 API 核心调用对象
 * 支撑管理员端 (Admin.Announce) 与普通用户端 (SF12) 的通知交互需求 [cite: 108, 591]
 */
export const announcementApi = {
  /**
   * 4.2.1 在系统中创建新的公告条目
   * 管理员可通过此接口发布全局维护公告或功能更新通知。
   * 系统将根据 status 字段决定是否立即对全平台用户可见 [cite: 533]。
   * @method create
   * @param {CreateAnnouncementParams} data - 包含标题、内容及发布状态的请求载荷
   * @returns {Promise<Announcement>} 返回后端生成的公告完整对象，包含自增 ID 和时间戳
   */
  create: (data: CreateAnnouncementParams) => {
    // 发起 POST 请求至公告管理端点，执行入库操作
    return client.post<any, Announcement>('/v1/announcements', data);
  },

  /**
   * 4.2.2 更新指定 ID 的公告内容或状态
   * 允许管理员修改已发布的公告文字，或将已发布的公告设为“已撤下”状态。
   * 撤下操作会使公告对普通用户立即失效 [cite: 533]。
   * @method update
   * @param {number} id - 待更新公告的唯一识别 ID
   * @param {UpdateAnnouncementParams} data - 包含待修改字段的更新对象
   * @returns {Promise<Announcement>} 返回更新后的公告对象
   */
  update: (id: number, data: UpdateAnnouncementParams) => {
    // 使用 PUT 方法对公告资源执行全量/部分更新
    return client.put<any, Announcement>(`/v1/announcements/${id}`, data);
  },

  /**
   * 4.2.3 物理删除系统公告
   * 从数据库中永久移除公告记录。通常用于清理过时的维护通知或测试数据 [cite: 533]。
   * @method delete
   * @param {number} id - 目标公告的 ID
   * @returns {Promise<void>} 
   */
  delete: (id: number) => {
    // 调用 DELETE 动词执行移除逻辑
    return client.delete<any, void>(`/v1/announcements/${id}`);
  },

  /**
   * 获取公告列表 (支持分页与状态过滤)
   * 对于普通用户，通常仅调用 status='published' 的列表进行首页轮播或横幅展示 [cite: 530]。
   * 对于管理员，则返回包含草稿和撤下公告的全量列表 [cite: 525]。
   * @method getList
   * @param {number} [page=1] - 当前请求页码
   * @param {number} [pageSize=10] - 每页展示的数据量，默认为 10 条
   * @param {string} [status='published'] - 过滤公告状态，默认为已发布
   * @returns {Promise<AnnouncementListResponse>} 包含分页元数据和公告数组的 Promise
   */
  getList: (page: number = 1, pageSize: number = 10, status: string = 'published') => {
    // 对应系统会自动调用 AnnouncementService.get_announcement_list 逻辑 [cite: 530]
    return client.get<any, AnnouncementListResponse>('/v1/announcements/', {
      params: {
        page,
        page_size: pageSize,
        status
      }
    });
  },

  /**
   * 获取单条公告的详细内容全文
   * 当用户在首页点击公告标题或摘要后，调用此接口加载并展示完整详情页 [cite: 531]。
   * @method getDetail
   * @param {number} id - 公告 ID
   * @returns {Promise<Announcement>} 返回包含完整正文内容的公告对象
   */
  getDetail: (id: number) => {
    // 调用公告详情接口，常用于前端弹窗或详情页面的数据渲染
    return client.get<any, Announcement>(`/v1/announcements/${id}`);
  }
};