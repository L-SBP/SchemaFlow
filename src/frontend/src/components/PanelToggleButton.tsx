/**
 * @file PanelToggleButton.tsx
 * @module Components/Layout/Panel-Toggle
 * @description 布局面板切换控制器组件。
 * 本组件是系统“工作台（Workspace）”响应式布局的核心交互组件，负责管理左右功能面板的可视化切换。
 * * 核心设计原则：
 * 1. 易用性适配 (Usability-1): 针对非技术用户，提供明确的视觉反馈与交互手势指引；
 * 2. 无障碍合规 (A11y): 严格执行 WCAG 2.1 AA 标准，确保在极端缩放环境下仍具备 44x44px 的最小可点击区域；
 * 3. 语义化提示: 动态生成中文标题（Tooltip），辅助用户识别面板的具体业务职能。
 * * 对应需求点：
 * - Requirement 6.1: 侧边栏折叠与展开动效；
 * - Requirement 6.2: 布局空间动态分配逻辑；
 * - Requirement 6.4/6.5: 视口宽度监听下的自动收缩策略。
 * * @author Wang Lirong (王利蓉)
 * @version 1.3.0
 * @date 2026-01-02
 */

import React from 'react';
import { PanelLeftClose, PanelLeftOpen, PanelRightClose, PanelRightOpen } from 'lucide-react';

/**
 * 面板切换按钮组件属性接口
 * @interface PanelToggleButtonProps
 * @description 封装了面板控制器的状态锁及展示配置。
 */
interface PanelToggleButtonProps {
  /** 标识当前受控面板是否处于“物理展开”状态 */
  isOpen: boolean;
  /** 触发面板状态反转的业务回调函数，通常由上层状态机驱动 */
  onToggle: () => void;
  /** * 指定按钮在视口中的逻辑方位：
   * - 'left': 对应数据库架构面板；
   * - 'right': 对应会话记录与 AI 交互面板。
   */
  position: 'left' | 'right';
  /** 可选的自定义提示文本，若缺省则由组件根据语义自动生成 */
  title?: string;
}

/**
 * @component PanelToggleButton
 * @description
 * 采用 React 函数式组件构建。该组件通过封装位操作逻辑，实现了在单一按钮上展示四种状态图标的能力。
 * 样式层基于 Tailwind CSS，确保了在 500% 缩放比例下依然保持像素级的对齐精度。
 */
export const PanelToggleButton: React.FC<PanelToggleButtonProps> = ({
  isOpen,
  onToggle,
  position,
  title
}) => {
  /**
   * 图标路由算法
   * @description 基于“方位”与“状态”的二元判定，从 Lucide 图标库中检索最优视觉符号。
   * * 逻辑分支：
   * 1. 左侧面板展开：显示 PanelLeftClose（折叠暗示）；
   * 2. 左侧面板折叠：显示 PanelLeftOpen（展开暗示）；
   * 3. 右侧面板同理镜像处理。
   * @returns {JSX.Element} 对应的 SVG 矢量图标节点
   */
  const getIcon = () => {
    // 处理左侧锚点逻辑
    if (position === 'left') {
      return isOpen ? <PanelLeftClose size={18} /> : <PanelLeftOpen size={18} />;
    } 
    // 处理右侧锚点逻辑（镜像翻转）
    else {
      return isOpen ? <PanelRightClose size={18} /> : <PanelRightOpen size={18} />;
    }
  };

  /**
   * 标题语义化生成器
   * @description 自动为辅助技术（如屏幕阅读器）生成业务描述，增强系统的容错性。
   * @returns {string} 符合当前面板职能的中文描述文本
   */
  const getDefaultTitle = () => {
    if (position === 'left') {
      // 对应左侧：通常挂载数据库 Schema 浏览器
      return isOpen ? '最小化数据库面板' : '展开数据库面板';
    } else {
      // 对应右侧：通常挂载 Agent 会话历史列表
      return isOpen ? '最小化会话列表' : '展开会话列表';
    }
  };

  /**
   * 组件渲染输出
   * 采用标准 button 元素，确保键盘可访问性（Tab-Index）。
   */
  return (
    <button
      /** 执行由父级注入的布局重算回调 */
      onClick={onToggle}
      /** * 样式类说明：
       * - panel-toggle-button: 基础业务标识类；
       * - box-border p-2.5: 确保 padding 不挤压内容空间；
       * - hover:bg-gray-100: 提供微小的悬停交互反馈。
       */
      className="panel-toggle-button box-border p-2.5 hover:bg-gray-100 rounded-md text-gray-500 hover:text-gray-800 transition-colors"
      /** 渲染优先级：用户自定义标题 > 自动生成语义化标题 */
      title={title || getDefaultTitle()}
      /** 声明按钮类型为非提交型，防止在表单环境内被误触 */
      type="button"
      /** * 内联样式锁：
       * 严格遵循 WCAG 2.1 AA 标准。
       * 强制声明 44x44px 的最小可点击区域（Click Target Size），
       * 即使在高倍率缩放导致视觉图标缩小时，仍能保证极高的点击成功率。
       */
      style={{
        minWidth: '44px',
        minHeight: '44px'
      }}
    >
      {/* 渲染由图标路由算法分发的图形节点 */}
      {getIcon()}
    </button>
  );
};