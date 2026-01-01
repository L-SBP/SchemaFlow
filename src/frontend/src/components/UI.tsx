/**
 * @file UI.tsx
 * @module Components/Foundation/Design-System
 * @description 系统底层原子化 UI 组件库。
 * 本模块遵循“原子设计 (Atomic Design)”哲学，封装了全站通用的基础交互组件。
 * * * 核心职能：
 * 1. 交互一致性 (Usability-1): 统一全站按钮、输入框、选择器的视觉反馈与手势路径；
 * 2. 响应式适配: 所有组件均集成 Tailwind 响应式类名，完美适配 500% 缩放（SF12）；
 * 3. 架构解耦: 引入事件总线 (Event Bus) 模式，实现 API 拦截器与 UI 反馈层的跨层级通讯；
 * 4. 视觉增强: 集成 Backdrop-blur (毛玻璃) 与渐进式动效，提升分析类软件的专业感。
 * * * 对应需求：
 * - Requirement 1.1: 界面多分辨率自适应。
 * - Requirement 7.1: 全局统一的异常与消息反馈机制。
 * * @author Wang Lirong (王利蓉)
 * @version 2.6.0
 * @date 2026-01-02
 */

import React, { JSX, ReactNode, useState, useEffect } from 'react';
import { Check, X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';

// =========================================================
// 1. Button Component - 交互触发器
// =========================================================

/**
 * 按钮组件属性接口
 * @interface ButtonProps
 * @extends {React.ButtonHTMLAttributes<HTMLButtonElement>}
 */
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    /**
     * 视觉变体策略：
     * - primary: 高强度引导（如：提交 DDL、确认部署）；
     * - default: 次级操作（如：取消、重置）；
     * - dashed: 弱关联动作（如：添加筛选条件）；
     * - text: 无背景文本（如：查看日志详情）；
     * - danger: 破坏性操作（如：彻底销毁项目）。
     */
    variant?: 'primary' | 'default' | 'dashed' | 'text' | 'danger';
    /** 允许在文本左侧插入 Lucide 图标节点 */
    icon?: ReactNode;
}

/**
 * @component Button
 * @description 
 * 核心交互基座。
 * 严格执行 WCAG 2.1 AA 标准，强制锁定最小点击高度为 44px，确保在高缩放模式下的可触达性。
 */
export const Button: React.FC<ButtonProps> = ({ children, variant = 'default', className = '', icon, ...props }) => {
    /** * 布局基准样式说明：
     * - inline-flex: 保证内联布局下的居中对齐；
     * - transition-all: 开启全属性 GPU 加速动效；
     * - focus:ring-2: 增强键盘聚焦时的辅助边框。
     */
    const baseStyles = "inline-flex items-center justify-center px-3 sm:px-4 py-2 sm:py-2.5 min-h-[44px] text-sm font-medium transition-all duration-200 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap";

    /** 样式变体映射矩阵 */
    const variants = {
        primary: "bg-primary text-white hover:bg-primary-hover border border-transparent focus:ring-blue-500",
        default: "bg-white text-gray-700 border border-gray-300 hover:text-primary hover:border-primary focus:ring-gray-200",
        dashed: "bg-white text-gray-700 border border-dashed border-gray-300 hover:text-primary hover:border-primary",
        text: "bg-transparent text-gray-700 shadow-none hover:bg-gray-100 border-none min-h-0",
        danger: "bg-white text-error border border-error hover:bg-red-50 focus:ring-red-200"
    };

    return (
        <button className={`${baseStyles} ${variants[variant]} ${className}`} {...props}>
            {/* 图标渲染逻辑：当存在子元素时，自动追加右边距以维持间距平衡 */}
            {icon && <span className={children ? "mr-1.5 sm:mr-2" : ""}>{icon}</span>}
            {children}
        </button>
    );
};

// =========================================================
// 2. Input Component - 结构化输入
// =========================================================

/**
 * 输入框组件属性接口
 * @interface InputProps
 */
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    /** 顶部语义化标签内容 */
    label?: string;
}

/**
 * @component Input
 * @description 
 * 标准化表单输入单元。
 * 针对 iOS 环境优化了 16px 字体，解决移动端自动缩放导致的视口跳变问题。
 */
export const Input: React.FC<InputProps> = ({ label, className = '', ...props }): JSX.Element => (
    <div className="flex flex-col gap-1.5">
        {/* 条件渲染：展示字段名称及必填红星标识 */}
        {label && (
            <label className="text-sm font-medium text-gray-700">
                {label}
                {props.required && <span className="text-red-500 ml-1">*</span>}
            </label>
        )}
        <input
            className={`px-3 py-2.5 min-h-[44px] bg-white border border-gray-300 rounded-lg text-base sm:text-sm focus:outline-none focus:border-primary focus:ring-2 focus:ring-blue-100 transition-all shadow-sm ${className}`}
            {...props}
        />
    </div>
);

// =========================================================
// 3. Select Component - 维度选择器
// =========================================================

/**
 * 下拉选项元数据定义
 */
export interface SelectOption {
    /** 业务后端预期的原始值 */
    value: string;
    /** 用户端展示的语义化标签 */
    label: string;
    /** 禁用特定选项的布尔锁 */
    disabled?: boolean;
}

/**
 * @interface SelectProps
 */
interface SelectProps {
    label?: string;
    options: SelectOption[];
    value: string;
    onChange: (value: string) => void;
    variant?: 'default' | 'minimal';
    className?: string;
    placeholder?: string;
    disabled?: boolean;
    required?: boolean;
}

/**
 * @component Select
 * @description 
 * 完全自主实现的虚拟化下拉组件。
 * 相比原生 select，具备更好的样式可控性，支持“浮动定位算法”以适应嵌套容器边界。
 */
export const Select: React.FC<SelectProps> = ({
    label,
    options,
    value,
    onChange,
    variant = 'default',
    className = '',
    placeholder = '请选择',
    disabled = false,
    required = false
}) => {
    // 下拉面板的状态锁
    const [isOpen, setIsOpen] = useState(false);
    /** * 几何位置计算：
     * 用于在 Fixed 定位模式下，动态追随触发按钮的物理坐标，防止菜单被局部 overflow 容器裁剪。
     */
    const [menuPosition, setMenuPosition] = useState({ top: 0, left: 0, width: 0 });
    
    // DOM 节点物理引用
    const selectRef = React.useRef<HTMLDivElement>(null);
    const buttonRef = React.useRef<HTMLButtonElement>(null);

    /**
     * 效应钩子：失焦自动关闭。
     * 实现典型的下拉组件点击外部即收起的 UX 行为。
     */
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (selectRef.current && !selectRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // 查找当前选中态的显示文本，实现回显逻辑
    const selectedOption = options.find(opt => opt.value === value);
    const displayText = selectedOption?.label || placeholder;

    /**
     * 面板开关切换函数
     * @description
     * 包含复杂的边界计算逻辑：当开启时，通过 getBoundingClientRect() 获取按钮的几何矩阵。
     */
    const handleToggle = () => {
        if (disabled) return;
        if (!isOpen && buttonRef.current) {
            /** * 策略：对于 Minimal 变体，尝试向上追溯带边框的物理容器，
             * 以确保下拉菜单的对齐视觉一致性。
             */
            let targetElement: HTMLElement | null = buttonRef.current;
            if (variant === 'minimal') {
                let parent = buttonRef.current.parentElement;
                while (parent && parent !== document.body) {
                    const style = window.getComputedStyle(parent);
                    if (style.borderWidth && parseFloat(style.borderWidth) > 0) {
                        targetElement = parent;
                        break;
                    }
                    parent = parent.parentElement;
                }
            }
            
            // 物理坐标重算
            const rect = targetElement!.getBoundingClientRect();
            setMenuPosition({
                top: rect.bottom + 4,
                left: rect.left,
                width: rect.width
            });
        }
        setIsOpen(!isOpen);
    };

    /** 派发值变更事件并关闭视图 */
    const handleSelect = (optionValue: string) => {
        onChange(optionValue);
        setIsOpen(false);
    };

    /** 基于变体参数生成的样式字符串 */
    const triggerStyles = variant === 'default'
        ? `px-3 py-2.5 min-h-[44px] bg-white border border-gray-300 rounded-lg text-base sm:text-sm shadow-sm ${isOpen ? 'border-primary ring-2 ring-blue-100' : 'hover:border-gray-400'}`
        : `bg-transparent text-sm font-medium text-gray-800 py-1 ${isOpen ? 'text-primary' : ''}`;

    return (
        <div className="flex flex-col gap-1.5" ref={selectRef}>
            {/* Label 区域 */}
            {label && (
                <label className="text-sm font-medium text-gray-700">
                    {label}
                    {required && <span className="text-red-500 ml-1">*</span>}
                </label>
            )}
            <div className={`relative ${className}`}>
                {/* 触发按钮组件：集成了 rotate 图标动效 */}
                <button
                    ref={buttonRef}
                    type="button"
                    onClick={handleToggle}
                    disabled={disabled}
                    className={`w-full flex items-center justify-between gap-2 transition-all cursor-pointer ${triggerStyles} ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                    <span className={`truncate ${!selectedOption ? 'text-gray-400' : ''}`}>
                        {displayText}
                    </span>
                    <svg
                        className={`w-4 h-4 text-gray-400 transition-transform shrink-0 ${isOpen ? 'rotate-180' : ''}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                </button>

                {/* 下拉面板：采用 Fixed 布局及 Z-Index 策略确保不被层级覆盖 */}
                {isOpen && (
                    <div
                        className="fixed bg-white border border-gray-200 rounded-lg shadow-md overflow-hidden animate-in fade-in zoom-in-95 duration-150"
                        style={{
                            zIndex: 9999,
                            top: menuPosition.top,
                            left: menuPosition.left,
                            minWidth: menuPosition.width
                        }}
                    >
                        {/* 内部滚动区：最大高度限制为 5 个标准列表项的高度 */}
                        <div className="overflow-y-auto py-1" style={{ maxHeight: 'calc(5 * 44px)' }}>
                            {options.map((option) => (
                                <div
                                    key={option.value}
                                    onClick={() => !option.disabled && handleSelect(option.value)}
                                    className={`px-3 py-2.5 text-sm cursor-pointer transition-colors flex items-center justify-between gap-3
                                        ${option.value === value
                                            ? 'bg-blue-50 text-primary font-medium'
                                            : 'text-gray-700 hover:bg-gray-50'
                                        }
                                        ${option.disabled ? 'opacity-50 cursor-not-allowed' : ''}
                                    `}
                                >
                                    <span className="whitespace-nowrap">{option.label}</span>
                                    {/* 选中态视觉回显：蓝勾图标 */}
                                    {option.value === value && (
                                        <Check size={16} className="text-primary shrink-0" />
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

// =========================================================
// 4. Card Component - 信息分屏器
// =========================================================

/**
 * 卡片组件属性接口
 */
interface CardProps {
    children: ReactNode;
    title?: ReactNode;
    extra?: ReactNode;
    className?: string;
}

/**
 * @component Card
 * @description 
 * 信息分组的核心容器。
 * 支持响应式内边距调节与悬停视觉浮起动效。
 */
export const Card: React.FC<CardProps> = ({ children, title, extra, className = '' }: CardProps): JSX.Element => (
    <div className={`bg-white rounded-xl border border-gray-200 shadow-sm transition-all hover:shadow-md ${className}`}>
        {/* 顶部标题栏区域 */}
        {(title || extra) && (
            <div className="px-4 sm:px-6 py-3 sm:py-4 border-b border-gray-100 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 bg-gray-50/30 rounded-t-xl">
                <div className="font-semibold text-gray-800 text-sm sm:text-base min-w-0 truncate max-w-full">{title}</div>
                {/* 渲染右上角扩展内容（如：更多按钮、状态标签） */}
                <div className="shrink-0">{extra}</div>
            </div>
        )}
        {/* 内容插槽区域 */}
        <div className="p-4 sm:p-6">{children}</div>
    </div>
);

// =========================================================
// 5. Tag Component - 语义化标签
// =========================================================

/**
 * 标签组件属性接口
 */
interface TagProps {
    color?: 'blue' | 'green' | 'red' | 'orange' | 'gray';
    children: ReactNode;
}

/**
 * @component Tag
 * @description 
 * 短文本状态展示组件。通过配色方案对应业务状态：
 * - green: 运行中 / 已激活；
 * - blue: 部署中 / 初始化中；
 * - red: 封禁 / 错误；
 * - orange: 异常活跃 / 告警。
 */
export const Tag: React.FC<TagProps> = ({ color = 'blue', children }) => {
    const colors = {
        blue: "bg-blue-50 text-blue-600 border-blue-200",
        green: "bg-green-50 text-green-600 border-green-200",
        red: "bg-red-50 text-red-600 border-red-200",
        orange: "bg-orange-50 text-orange-600 border-orange-200",
        gray: "bg-gray-50 text-gray-600 border-gray-200",
    };
    return (
        <span className={`inline-block px-2.5 py-0.5 text-xs font-medium border rounded-full ${colors[color]}`}>
            {children}
        </span>
    );
};

// =========================================================
// 6. ProgressBar Component - 进度反馈系统
// =========================================================

/**
 * @component ProgressBar
 * @description 
 * 线性进度条。用于反馈 AI 模型生成 Schema 或执行 DDL 的长事务进度。
 */
export const ProgressBar: React.FC<{ progress: number }> = ({ progress }) => {
    return (
        <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden shadow-inner">
            {/* 内层填充条：利用 transition 实现物理惯性动画感 */}
            <div
                className="bg-primary h-full rounded-full transition-all duration-700 ease-out shadow-sm relative overflow-hidden"
                style={{ width: `${Math.max(0, Math.min(100, progress))}%` }}
            >
                {/* 动态呼吸动效，增强“处理中”的视觉暗示 */}
                <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
            </div>
        </div>
    );
};

// =========================================================
// 7. Steps Component - 流程导航器
// =========================================================

interface StepItem {
    title: string;
    description?: string;
}

/**
 * @component Steps
 * @description 
 * 步骤条。驱动 ProjectWizard 向导的分步状态展示。
 */
export const Steps: React.FC<{ steps: StepItem[]; current: number }> = ({ steps, current }) => {
    return (
        <div className="flex w-full items-center justify-between px-4">
            {steps.map((step, index) => {
                const isCompleted = index < current;
                const isCurrent = index === current;

                return (
                    <div key={index} className="flex flex-col items-center relative flex-1 group">
                        {/* 逻辑：渲染节点间的物理连接线。若当前节点已达标，则线段高亮。 */}
                        {index !== 0 && (
                            <div className="absolute top-5 right-[50%] w-full h-[2px] -z-10">
                                <div className={`h-full transition-colors duration-500 ${index <= current ? 'bg-primary' : 'bg-gray-200'}`}></div>
                            </div>
                        )}

                        {/* 节点图标：完成态展示 Check 图标，否则展示索引数字。 */}
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-500 z-10 border-2 shadow-sm ${isCompleted ? 'bg-primary border-primary text-white' :
                            isCurrent ? 'bg-white border-primary text-primary ring-4 ring-blue-50 scale-110' :
                                'bg-white border-gray-200 text-gray-400'
                            }`}>
                            {isCompleted ? <Check size={18} strokeWidth={3} /> : index + 1}
                        </div>
                        
                        {/* 节点描述文本 */}
                        <div className={`mt-3 text-sm font-medium transition-colors duration-300 ${isCurrent ? 'text-primary' :
                            isCompleted ? 'text-gray-800' :
                                'text-gray-400'
                            }`}>
                            {step.title}
                        </div>
                    </div>
                );
            })}
        </div>
    );
};

// =========================================================
// 8. Modal Component - 高级模态对话框
// =========================================================

interface ModalProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    children: ReactNode;
    footer?: ReactNode;
    maxWidth?: string;
}

/**
 * @component Modal
 * @description 
 * 系统级对话框容器。
 * 集成了毛玻璃背景效果 (backdrop-blur-sm) 与 200ms 的入场/退场动画，提供极佳的沉浸式体验。
 */
export const Modal: React.FC<ModalProps> = ({ isOpen, onClose, title, children, footer, maxWidth = 'max-w-md' }) => {
    // 渲染守卫
    if (!isOpen) return null;

    return (
        /**
         * 遮罩层布局：
         * - bg-gray-900/60: 半透明遮蔽，聚焦视觉中心；
         * - overflow-y-auto: 允许在内容溢出时进行全屏滚动。
         */
        <div className="fixed inset-0 z-50 flex items-start justify-center bg-gray-900/60 backdrop-blur-sm p-2 sm:p-4 transition-opacity duration-300 overflow-y-auto">
            
            {/* 模态框主体：应用 zoom-in 动画效果 */}
            <div className={`bg-white rounded-xl shadow-2xl w-full ${maxWidth} animate-in fade-in zoom-in-95 duration-200 flex flex-col my-auto shrink-0`}>
                
                {/* 头部标题区域 */}
                <div className="px-4 sm:px-8 py-4 sm:py-5 border-b border-gray-100 flex justify-between items-center shrink-0 bg-white gap-2 min-h-[64px] rounded-t-xl">
                    <h3 className="text-base sm:text-lg font-bold text-gray-800 tracking-tight truncate flex-1 min-w-0 flex items-center">{title}</h3>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600 transition-colors hover:bg-gray-100 rounded-full shrink-0 w-7 h-7 flex items-center justify-center ml-2"
                        aria-label="关闭弹窗"
                    >
                        <X size={14} />
                    </button>
                </div>

                {/* 主内容插槽区 */}
                <div className="p-4 sm:p-8 bg-white flex-1 min-h-0 overflow-hidden">
                    {children}
                </div>

                {/* 底部操作区：通过 flex-wrap 适配小屏设备下的按钮堆叠 */}
                {footer && (
                    <div className="px-4 sm:px-8 py-4 sm:py-5 bg-gray-50 border-t border-gray-100 flex flex-wrap justify-end gap-2 sm:gap-3 shrink-0 rounded-b-xl">
                        {footer}
                    </div>
                )}
            </div>
        </div>
    );
};

// =========================================================
// 9. Toast/Message System - 异步消息通知中心
// =========================================================

/**
 * 消息通知类型定义
 */
export type ToastType = 'success' | 'error' | 'info' | 'warning';

/**
 * 消息通知单条记录的数据结构
 */
export interface ToastData {
    /** 唯一的 UUID，用于精准移除 DOM 节点 */
    id: string;
    type: ToastType;
    content: string;
    /** 自动销毁时长，单位毫秒 */
    duration?: number;
}

/**
 * 消息分发总线 (Observer Pattern)
 * @class MessageBus
 * @description
 * 解决 React 组件树外的脚本（如 Axios 拦截器）无法直接调用 UI 的问题。
 * 通过订阅模式实现非侵入式全局通知。
 */
class MessageBus {
    // 观察者回调列表
    private listeners: ((toast: ToastData) => void)[] = [];

    /**
     * 注册订阅者
     * @param {Function} listener - 接收新消息的回调
     * @returns {Function} 清理函数，用于注销订阅
     */
    subscribe(listener: (toast: ToastData) => void) {
        this.listeners.push(listener);
        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        };
    }

    /**
     * 广播新消息
     * @param {ToastType} type - 消息权重类型
     * @param {string} content - 通知文本
     * @param {number} [duration=3000] - 持续展示时间
     */
    emit(type: ToastType, content: string, duration = 3000) {
        const toast: ToastData = {
            id: Math.random().toString(36).substr(2, 9), // 快速生成唯一随机 ID
            type,
            content,
            duration
        };
        // 顺序触发所有已注册的活跃订阅者
        this.listeners.forEach(l => l(toast));
    }
}

/** 单例消息总线实例 */
const messageBus = new MessageBus();

/**
 * 全局消息交互工具对象 (Public API)
 * 允许在业务代码中执行链式调用：message.success("Success!")
 */
export const message = {
    success: (content: string, duration?: number) => messageBus.emit('success', content, duration),
    error: (content: string, duration?: number) => messageBus.emit('error', content, duration),
    info: (content: string, duration?: number) => messageBus.emit('info', content, duration),
    warning: (content: string, duration?: number) => messageBus.emit('warning', content, duration),
};

/**
 * 全局消息容器挂载点
 * @component ToastContainer
 * @description 
 * 必须挂载在应用 Root 节点。它通过监听全局 messageBus 来动态管理 toasts 数组的生命周期。
 */
export const ToastContainer: React.FC = () => {
    // 管理内存中的活跃消息队列
    const [toasts, setToasts] = useState<ToastData[]>([]);

    useEffect(() => {
        /**
         * 核心订阅逻辑：
         * 当接收到广播时，将消息压入队列，并设定定时炸弹 (setTimeout) 自动离场。
         */
        return messageBus.subscribe((toast) => {
            setToasts(prev => [...prev, toast]);
            if (toast.duration && toast.duration > 0) {
                setTimeout(() => {
                    removeToast(toast.id);
                }, toast.duration);
            }
        });
    }, []);

    /**
     * 执行消息移除
     * @param {string} id - 待销毁的消息 ID
     */
    const removeToast = (id: string) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    };

    return (
        /**
         * 容器布局：
         * fixed inset-0 + flex items-center: 确保消息垂直居中悬浮在全屏幕最顶层。
         */
        <div className="fixed inset-0 z-[100] pointer-events-none flex items-center justify-center">
            <div className="flex flex-col gap-3 max-w-md w-full mx-4">
                {toasts.map(toast => (
                    <div
                        key={toast.id}
                        /** pointer-events-auto: 允许用户点击关闭按钮 */
                        className={`pointer-events-auto w-full p-4 rounded-lg shadow-xl border transform transition-all duration-300 animate-in zoom-in-95 fade-in bg-white flex items-center gap-3 min-h-[56px]
                ${toast.type === 'success' ? 'border-green-200 bg-green-50/90 backdrop-blur-sm' :
                                toast.type === 'error' ? 'border-red-200 bg-red-50/90 backdrop-blur-sm' :
                                    toast.type === 'warning' ? 'border-orange-200 bg-orange-50/90 backdrop-blur-sm' : 'border-blue-200 bg-blue-50/90 backdrop-blur-sm'}`}
                    >
                        {/* 状态图标：通过 type 属性分发 Lucide 语义图标 */}
                        <div className="shrink-0 flex items-center justify-center">
                            {toast.type === 'success' && <CheckCircle size={20} className="text-green-600" />}
                            {toast.type === 'error' && <AlertCircle size={20} className="text-red-600" />}
                            {toast.type === 'warning' && <AlertTriangle size={20} className="text-orange-600" />}
                            {toast.type === 'info' && <Info size={20} className="text-blue-600" />}
                        </div>
                        
                        {/* 核心消息载荷区域：支持长文本自动折行 (break-words) */}
                        <div className="flex-1 text-sm text-gray-800 font-medium break-words leading-relaxed min-w-0 flex items-center">
                            {toast.content}
                        </div>
                        
                        {/* 手动关闭触发器 */}
                        <button
                            onClick={() => removeToast(toast.id)}
                            className="text-gray-400 hover:text-gray-600 transition-colors shrink-0 rounded-full hover:bg-gray-100 w-6 h-6 flex items-center justify-center ml-2"
                            aria-label="关闭消息"
                        >
                            <X size={12} />
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
};

/** 统一导出业务关联组件 */
export { ConfirmDialog } from './ConfirmDialog';