/**
 * @file project-overview.ts
 * @module Types/Project-Overview-Feature
 * @description 项目概览优化模块的类型定义集合。
 * 本模块为前端“项目仪表盘”提供严格的类型检查与数据契约保障。
 * * 核心设计目标：
 * 1. 规范化 DTO：定义从后端获取的项目摘要数据结构（ProjectData）；
 * 2. 强类型组件：为 ProjectCard, StatusBadge 等展示组件提供声明式的 Props 接口；
 * 3. 性能优化参考：支持在数据层标识状态，以驱动组件的按需渲染策略。
 * * 对应需求点：
 * - Requirement 4.2: 项目卡片列表展示
 * - Requirement 4.3: 响应式状态标签
 * - Requirement 4.4: 异步部署进度反馈
 * - Requirement 4.6: 快捷编辑与物理删除流
 * * @author Wang Lirong (王利蓉)
 * @version 1.2.0
 * @date 2026-01-02
 */

/**
 * 项目概览核心数据结构定义
 * @interface ProjectData
 * @description 对应后端返回的轻量级项目摘要对象。
 * 旨在通过最小化字段传输，提升 Dashboard 首页的首次加载速度（FCP）。
 */
export interface ProjectData {
  /** 数据库项目在全球系统中的唯一主键序列号 */
  project_id: number;
  /** 数据库项目展示名称（受 6 字符截断算法约束） */
  project_name: string;
  /** * 业务背景描述文本。
   * 用于 Schema Agent 进行初步需求提取，前端展示时会根据空间自动执行物理像素级截断。
   */
  description: string;
  /** * 项目当前生命周期状态：
   * - initializing: 物理数据库正在云端实例中进行初始化或 DDL 部署中。
   * - active: 数据库实例已就绪，可正常进行 NL2SQL 对话交互。
   * - inactive: 逻辑归档状态，资源被暂时挂起。
   */
   project_status: 'initializing' | 'active' | 'pending_confirmation' | 'deleted' | 'completed';
  /** 记录项目的最后变更时间戳（遵循 ISO 8601 标准格式，便于前端时区转换） */
  updated_at: string; 
  /** * 目标数据库引擎类型。
   * 系统将根据此字段切换 DDL 生成器的 Dialect（方言）及对应的可视化图标。
   */
  db_type: 'mysql' | 'postgresql' | 'sqlite';
}

/**
 * 项目卡片组件属性接口
 * @interface ProjectCardProps
 * @description 定义单体项目卡片（ProjectCard）的输入契约及交互回调。
 */
export interface ProjectCardProps {
  /** 当前待渲染的项目核心数据实体 */
  project: ProjectData;
  /** 点击卡片主体区域进入工作台 (Workspace) 的路由跳转回调 */
  onCardClick: (projectId: number) => void;
  /** 触发项目配置微调（如修改描述、重命名）的编辑回调 */
  onEdit: (projectId: number) => void;
  /** 触发带安全令牌校验的删除确认流程回调 */
  onDelete: (projectId: number) => void;
}

/**
 * 数据库类型图标组件属性接口
 * @interface DatabaseIconProps
 */
export interface DatabaseIconProps {
  /** 需要渲染的数据库引擎枚举值 */
  dbType: 'mysql' | 'postgresql' | 'sqlite';
  /** 图标渲染尺寸（单位：px），采用响应式默认值 */
  size?: number;
  /** 扩展 CSS 类名，用于支持外部样式注入 */
  className?: string;
}

/**
 * 项目详情模态框组件属性接口
 * @interface ProjectDetailsModalProps
 * @description 控制项目元数据全量展示对话框的可见性及内容载荷。
 */
export interface ProjectDetailsModalProps {
  /** 当前选中的项目对象。若为 null 则表示模态框处于关闭或重置状态。 */
  project: ProjectData | null;
  /** 控制模态框显隐状态的布尔开关 */
  isOpen: boolean;
  /** 模态框关闭时的清理回调（负责重置局部状态） */
  onClose: () => void;
}

/**
 * 操作按钮组组件属性接口
 * @interface ActionButtonsProps
 */
export interface ActionButtonsProps {
  /** 目标项目识别码 */
  projectId: number;
  /** 编辑逻辑触发函数 */
  onEdit: (projectId: number) => void;
  /** 物理删除逻辑触发函数 */
  onDelete: (projectId: number) => void;
}

/**
 * 项目状态标签组件属性接口
 * @interface ProjectStatusBadgeProps
 */
export interface ProjectStatusBadgeProps {
  /** 实时状态，决定标签的着色方案（Green/Blue/Gray） */
  status: 'initializing' | 'active' | 'inactive';
  /** 容器扩展类名 */
  className?: string;
}

/**
 * 语义化日期格式化器组件属性接口
 * @interface DateFormatterProps
 */
export interface DateFormatterProps {
  /** 待格式化的 ISO 时间戳字符串 */
  date: string;
  /** 样式类名，常用于对 Today/Yesterday 进行特殊高亮处理 */
  className?: string;
}

/**
 * 文本截断工具组件属性接口
 * @interface TextTruncationProps
 * @description 结合 Tooltip 机制，实现超长文本的“预览-详情”交互。
 */
export interface TextTruncationProps {
  /** 原始全量文本内容 */
  text: string;
  /** 强制截断的字符长度临界值 */
  maxLength: number;
  /** 是否在悬停时展示全量内容提示框，默认为 true */
  showTooltip?: boolean;
}

/**
 * 项目概览栅格容器组件属性接口
 * @interface ProjectOverviewGridProps
 * @description 负责管理项目卡片阵列的布局与事件冒泡分发。
 */
export interface ProjectOverviewGridProps {
  /** 聚合渲染的项目数据列表 */
  projects: ProjectData[];
  /** 点击项目事件向下透传 */
  onCardClick: (projectId: number) => void;
  /** 编辑事件向下透传 */
  onEdit: (projectId: number) => void;
  /** 删除事件向下透传 */
  onDelete: (projectId: number) => void;
}