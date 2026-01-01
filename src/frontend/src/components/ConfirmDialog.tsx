/**
 * @file ConfirmDialog.tsx
 * @module Components/Feedback/Confirm-Dialog
 * @description 基于 React 的原子化统一确认对话框组件。
 * 本组件作为系统交互层的“安全闸门”，替代了不可控的浏览器原生 confirm() 接口。
 * * 核心设计目标：
 * [cite_start]1. 安全确认机制 (Usability-2): 针对物理数据库删除、DML 指令执行等高风险操作提供二次确认逻辑 [cite: 617]；
 * 2. 交互一致性: 采用高斯模糊背景与平滑动效，确保系统视觉语言的统一；
 * 3. 语义化视觉反馈: 支持危险操作（Danger）与普通操作（Primary）的视觉分级。
 * * 对应需求点：
 * - [cite_start]Security-3: 对 AI 生成的 SQL 删除/更新操作强制确认 [cite: 555-556]；
 * - Usability-2: 提供明确的双重确认提示以防止非技术用户误操作。
 * * @author Wang Lirong (王利蓉)
 * @version 2.0.0
 * @date 2026-01-02
 */

import React from 'react';
import { AlertTriangle, X } from 'lucide-react';
import { Button } from './UI';

/**
 * 确认对话框组件属性接口
 * @interface ConfirmDialogProps
 * @description 封装了对话框的展示内容、交互行为及视觉风格配置。
 */
interface ConfirmDialogProps {
  /** * 控制对话框的渲染状态
   * true 时展示遮罩与内容，false 时不渲染任何 DOM 节点。
   */
  isOpen: boolean;
  /** * 关闭对话框的回调函数
   * 触发场景：点击取消按钮、右上角关闭按钮或遮罩层。
   */
  onClose: () => void;
  /** * 用户执行“确认”动作后的业务回调
   * 该函数通常包含实际的 DDL/DML 提交逻辑或项目删除指令。
   */
  onConfirm: () => void;
  /** 对话框顶部的标题文本，需简明扼要说明操作意图 */
  title: string;
  /** 对话框的核心描述内容，用于向用户解释该操作的后果及风险 */
  message: string;
  /** 确认按钮的自定义文本，默认为“确认” */
  confirmText?: string;
  /** 取消按钮的自定义文本，默认为“取消” */
  cancelText?: string;
  /** * 视觉风险标识开关
   * 设置为 true 时，确认按钮将应用红色警示色调，适用于不可逆的销毁操作。
   */
  isDangerous?: boolean;
  /** * 警告图标显隐控制
   * 启用后会在标题左侧显示橙色警示符号，增强用户视觉注意。
   */
  showWarningIcon?: boolean;
}

/**
 * 统一确认对话框组件实体
 * @component ConfirmDialog
 * @description
 * 采用 React 函数式组件构建，结合 Tailwind CSS 实现全分辨率适配与平滑过渡。
 * 组件层级设计遵循 Z-Index 规范（z-[60]），确保其始终浮动在全局蒙层与侧边栏之上。
 */
export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = '确认',
  cancelText = '取消',
  isDangerous = false,
  showWarningIcon = false,
}) => {
  /**
   * 步骤 1：条件渲染守卫
   * 若对话框处于关闭状态，立即终止渲染流以优化虚拟 DOM 性能。
   */
  if (!isOpen) return null;

  /**
   * 步骤 2：封装确认逻辑
   * 在执行业务回调的同时自动关闭当前模态框，保证交互闭环。
   */
  const handleConfirm = () => {
    // 触发父级透传的业务指令（如 API 调用）
    onConfirm();
    // 逻辑流完成后关闭弹窗
    onClose();
  };

  /**
   * 步骤 3：视觉布局构建 (Atomic Layout)
   * 采用 Fixed 布局覆盖全屏，配合 backdrop-blur 实现现代 UI 的通透感。
   */
  return (
    // 全屏遮罩层：提供 60% 透明度的深色背景及毛玻璃滤镜
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-gray-900/60 backdrop-blur-sm p-4 transition-opacity duration-300">
      
      {/* 对话框主体容器：具备自适应宽度及进入动画 (animate-in) */}
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md animate-in fade-in zoom-in-95 duration-200 overflow-hidden">
        
        {/* 对话框头部 (Header Section) */}
        <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center min-h-[56px]">
          {/* 标题区域：包含可选的警告图标与截断保护文本 */}
          <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2 flex-1 min-w-0">
            {/* 条件渲染：显示警示图标以提示操作风险 */}
            {showWarningIcon && <AlertTriangle size={20} className="text-orange-500 flex-shrink-0" />}
            <span className="truncate">{title}</span>
          </h3>
          
          {/* 交互控件：右上角关闭图标，提供圆角悬停反馈 */}
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-full hover:bg-gray-100 w-7 h-7 flex items-center justify-center flex-shrink-0 ml-3"
            aria-label="关闭对话框"
          >
            <X size={14} />
          </button>
        </div>

        {/* 内容主体区域 (Content Section) */}
        <div className="px-6 py-4">
          {/* 渲染业务描述文本，使用宽松的行高 (leading-relaxed) 以提升阅读舒适度 */}
          <p className="text-gray-600 leading-relaxed">{message}</p>
        </div>

        {/* 底部操作栏 (Footer Section) */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex justify-end gap-3">
          {/* 取消动作：默认变体按钮 */}
          <Button onClick={onClose} variant="default">
            {cancelText}
          </Button>
          
          {/* 确认动作：根据 isDangerous 参数动态切换按钮视觉语义 (Danger vs Primary) */}
          <Button
            onClick={handleConfirm}
            variant={isDangerous ? 'danger' : 'primary'}
          >
            {confirmText}
          </Button>
        </div>
      </div>
    </div>
  );
};