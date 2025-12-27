import React from 'react';
import { PanelLeftClose, PanelLeftOpen, PanelRightClose, PanelRightOpen } from 'lucide-react';

interface PanelToggleButtonProps {
  isOpen: boolean;
  onToggle: () => void;
  position: 'left' | 'right';
  title?: string;
}

/**
 * PanelToggleButton - 面板切换按钮组件
 * 
 * 提供一致的面板切换按钮实现，确保点击区域与视觉边界完全一致
 * 符合 WCAG 2.1 AA 标准的最小可点击区域要求 (44x44px)
 * 
 * Requirements: 6.1, 6.2, 6.4, 6.5
 */
export const PanelToggleButton: React.FC<PanelToggleButtonProps> = ({
  isOpen,
  onToggle,
  position,
  title
}) => {
  // 根据位置和状态选择合适的图标
  const getIcon = () => {
    if (position === 'left') {
      return isOpen ? <PanelLeftClose size={18} /> : <PanelLeftOpen size={18} />;
    } else {
      return isOpen ? <PanelRightClose size={18} /> : <PanelRightOpen size={18} />;
    }
  };

  // 生成默认标题
  const getDefaultTitle = () => {
    if (position === 'left') {
      return isOpen ? '最小化数据库面板' : '展开数据库面板';
    } else {
      return isOpen ? '最小化会话列表' : '展开会话列表';
    }
  };

  return (
    <button
      onClick={onToggle}
      className="panel-toggle-button box-border p-2.5 hover:bg-gray-100 rounded-md text-gray-500 hover:text-gray-800 transition-colors"
      title={title || getDefaultTitle()}
      type="button"
      style={{
        minWidth: '44px',
        minHeight: '44px'
      }}
    >
      {getIcon()}
    </button>
  );
};