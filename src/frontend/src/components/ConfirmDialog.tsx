/**
 * 统一的确认对话框组件
 * 用于替换所有浏览器默认的 confirm() 弹窗
 */

import React from 'react';
import { AlertTriangle, X } from 'lucide-react';
import { Button } from './UI';

interface ConfirmDialogProps {
  /** 是否显示对话框 */
  isOpen: boolean;
  /** 关闭对话框的回调 */
  onClose: () => void;
  /** 确认操作的回调 */
  onConfirm: () => void;
  /** 对话框标题 */
  title: string;
  /** 对话框内容/描述 */
  message: string;
  /** 确认按钮文本 */
  confirmText?: string;
  /** 取消按钮文本 */
  cancelText?: string;
  /** 是否为危险操作（红色确认按钮） */
  isDangerous?: boolean;
  /** 是否显示警告图标 */
  showWarningIcon?: boolean;
}

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
  if (!isOpen) return null;

  const handleConfirm = () => {
    onConfirm();
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-gray-900/60 backdrop-blur-sm p-4 transition-opacity duration-300">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md animate-in fade-in zoom-in-95 duration-200 overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center min-h-[56px]">
          <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2 flex-1 min-w-0">
            {showWarningIcon && <AlertTriangle size={20} className="text-orange-500 flex-shrink-0" />}
            <span className="truncate">{title}</span>
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-full hover:bg-gray-100 w-7 h-7 flex items-center justify-center flex-shrink-0 ml-3"
            aria-label="关闭对话框"
          >
            <X size={14} />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-4">
          <p className="text-gray-600 leading-relaxed">{message}</p>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex justify-end gap-3">
          <Button onClick={onClose} variant="default">
            {cancelText}
          </Button>
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