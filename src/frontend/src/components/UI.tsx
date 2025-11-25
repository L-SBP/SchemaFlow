import React, {JSX, ReactNode} from 'react';
import { Check } from 'lucide-react';

// --- Button Component ---

/**
 * 按钮组件属性接口
 * @interface ButtonProps
 * @extends {React.ButtonHTMLAttributes<HTMLButtonElement>} 继承原生 button 属性
 */
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    /**
     * 按钮样式变体
     * - 'primary': 主色调填充（蓝色）
     * - 'default': 白色背景带边框
     * - 'dashed': 虚线边框
     * - 'text': 无边框文本按钮
     * - 'danger': 红色警告样式
     * @default 'default'
     */
    variant?: 'primary' | 'default' | 'dashed' | 'text' | 'danger';
    /**
     * 按钮内显示的图标组件
     */
    icon?: ReactNode;
}

/**
 * 通用按钮组件
 * * 封装了不同状态（hover, focus, disabled）下的 Tailwind 样式。
 *
 * @param children
 * @param variant
 * @param className
 * @param icon
 * @param {ButtonProps} props - 组件属性
 * @returns {JSX.Element} 渲染后的按钮元素
 */
export const Button: React.FC<ButtonProps> = ({ children, variant = 'default', className = '', icon, ...props }) => {
    // 基础样式：布局、内边距、字体、圆角、阴影及过渡效果
    const baseStyles = "inline-flex items-center justify-center px-4 py-1.5 text-sm font-medium transition-all duration-200 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed";
    
    // 不同变体的样式映射
    const variants = {
        primary: "bg-primary text-white hover:bg-primary-hover border border-transparent focus:ring-blue-500",
        default: "bg-white text-gray-700 border border-gray-300 hover:text-primary hover:border-primary focus:ring-gray-200",
        dashed: "bg-white text-gray-700 border border-dashed border-gray-300 hover:text-primary hover:border-primary",
        text: "bg-transparent text-gray-700 shadow-none hover:bg-gray-100 border-none",
        danger: "bg-white text-error border border-error hover:bg-red-50 focus:ring-red-200"
    };
    
    return (
        <button className={`${baseStyles} ${variants[variant]} ${className}`} {...props}>
            {icon && <span className="mr-2">{icon}</span>}
            {children}
        </button>
    );
};

// --- Input Component ---

/**
 * 输入框组件属性接口
 * @interface InputProps
 * @extends {React.InputHTMLAttributes<HTMLInputElement>} 继承原生 input 属性
 */
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    /**
     * 输入框上方的标签文本
     */
    label?: string;
}

/**
 * 通用输入框组件
 * * 包含可选的 Label 显示，并统一了 focus 状态的样式。
 *
 * @param label
 * @param className
 * @param {InputProps} props - 组件属性
 * @returns {JSX.Element} 包含 Label 和 Input 的容器
 */
export const Input: React.FC<InputProps> = ({ label, className = '', ...props }): JSX.Element => (
    <div className="flex flex-col gap-1.5">
        {label && <label className="text-sm font-medium text-gray-700">{label}</label>}
        <input
            className={`px-3 py-2.5 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-primary focus:ring-2 focus:ring-blue-100 transition-all shadow-sm ${className}`}
            {...props}
        />
    </div>
);

// --- Card Component ---

/**
 * 卡片组件属性接口
 */
interface CardProps {
    /** 卡片主体内容 */
    children: ReactNode;
    /** 卡片左上角标题（可选） */
    title?: ReactNode;
    /** 卡片右上角额外操作区（可选），例如按钮或标签 */
    extra?: ReactNode;
    /** 自定义类名 */
    className?: string;
}

/**
 * 通用卡片容器组件
 * * 用于展示分组内容，支持标题栏和主体内容的分离。
 * * @param {CardProps} props - 组件属性
 * @returns {JSX.Element} 渲染后的卡片
 */
export const Card: React.FC<CardProps> = ({ children, title, extra, className = '' }: CardProps): JSX.Element => (
    <div className={`bg-white rounded-xl border border-gray-200 shadow-sm transition-all hover:shadow-md ${className}`}>
        {(title || extra) && (
            <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/30 rounded-t-xl">
                <div className="font-semibold text-gray-800 text-base">{title}</div>
                <div>{extra}</div>
            </div>
        )}
        <div className="p-6">{children}</div>
    </div>
);

// --- Tag Component ---

/**
 * 标签组件属性接口
 */
interface TagProps {
    /** * 标签颜色主题
     * @default 'blue'
     */
    color?: 'blue' | 'green' | 'red' | 'orange' | 'gray';
    /** 标签内容 */
    children: ReactNode;
}

/**
 * 状态标签组件
 * * 用于展示状态、分类等短文本信息，提供多种预设颜色。
 *
 * @param {TagProps} props - 组件属性
 * @returns {JSX.Element} 渲染后的标签
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

// --- ProgressBar Component ---

/**
 * 进度条组件
 * * 显示操作完成的百分比，包含动画效果。
 *
 * @param {Object} props - 组件属性
 * @param {number} props.progress - 当前进度值 (0-100)
 * @returns {JSX.Element} 进度条元素
 */
export const ProgressBar: React.FC<{ progress: number }> = ({ progress }) => {
    return (
        <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden shadow-inner">
            <div
                className="bg-primary h-full rounded-full transition-all duration-700 ease-out shadow-sm relative overflow-hidden"
                style={{ width: `${Math.max(0, Math.min(100, progress))}%` }}
            >
                <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
            </div>
        </div>
    );
};

// --- Steps Component ---

/**
 * 步骤条目定义
 */
interface StepItem {
    /** 步骤标题 */
    title: string;
    /** 步骤描述（可选，当前UI未显示） */
    description?: string;
}

/**
 * 步骤条组件
 * * 用于展示多步骤流程的当前状态。
 *
 * @param {Object} props - 组件属性
 * @param {StepItem[]} props.steps - 步骤数组
 * @param {number} props.current - 当前步骤索引 (0-based)
 * @returns {JSX.Element} 步骤条
 */
export const Steps: React.FC<{ steps: StepItem[]; current: number }> = ({ steps, current }) => {
    return (
        <div className="flex w-full items-center justify-between px-4">
            {steps.map((step, index) => {
                const isCompleted = index < current;
                const isCurrent = index === current;
                
                return (
                    <div key={index} className="flex flex-col items-center relative flex-1 group">
                        {/* 连接线：除了第一个节点外，每个节点左侧都有连接线 */}
                        {index !== 0 && (
                            <div className="absolute top-5 right-[50%] w-full h-[2px] -z-10">
                                <div className={`h-full transition-colors duration-500 ${index <= current ? 'bg-primary' : 'bg-gray-200'}`}></div>
                            </div>
                        )}
                        
                        {/* 步骤图标：完成态显示对号，进行/未进行态显示数字 */}
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-500 z-10 border-2 shadow-sm ${
                            isCompleted ? 'bg-primary border-primary text-white' :
                                isCurrent ? 'bg-white border-primary text-primary ring-4 ring-blue-50 scale-110' :
                                    'bg-white border-gray-200 text-gray-400'
                        }`}>
                            {isCompleted ? <Check size={18} strokeWidth={3} /> : index + 1}
                        </div>
                        {/* 步骤标题 */}
                        <div className={`mt-3 text-sm font-medium transition-colors duration-300 ${
                            isCurrent ? 'text-primary' :
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

// --- Modal Component ---

/**
 * 模态框组件属性接口
 */
interface ModalProps {
    /** 是否显示模态框 */
    isOpen: boolean;
    /** 关闭模态框的回调函数 */
    onClose: () => void;
    /** 模态框标题 */
    title: string;
    /** 模态框内容 */
    children: ReactNode;
    /** 底部操作区内容（可选） */
    footer?: ReactNode;
    /** * 最大宽度限制类名
     * @default 'max-w-md'
     */
    maxWidth?: string;
}

/**
 * 通用模态框组件
 * * 包含遮罩层、动画效果以及标准化的头部和底部布局。
 *
 * @param {ModalProps} props - 组件属性
 * @returns {JSX.Element | null} 如果 isOpen 为 false 则返回 null
 */
export const Modal: React.FC<ModalProps> = ({ isOpen, onClose, title, children, footer, maxWidth = 'max-w-md' }) => {
    if (!isOpen) return null;
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/60 backdrop-blur-sm p-4 transition-opacity duration-300">
            <div className={`bg-white rounded-xl shadow-2xl w-full ${maxWidth} animate-in fade-in zoom-in-95 duration-200 flex flex-col max-h-[90vh] overflow-hidden`}>
                {/* Header */}
                <div className="px-8 py-5 border-b border-gray-100 flex justify-between items-center shrink-0 bg-white">
                    <h3 className="text-lg font-bold text-gray-800 tracking-tight">{title}</h3>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors bg-gray-50 hover:bg-gray-100 p-1 rounded-full">
                        <span className="sr-only">Close</span>
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>
                {/* Content - 可滚动区域 */}
                <div className="p-8 overflow-y-auto bg-white">
                    {children}
                </div>
                {/* Footer */}
                {footer && (
                    <div className="px-8 py-5 bg-gray-50 border-t border-gray-100 flex justify-end gap-3 shrink-0">
                        {footer}
                    </div>
                )}
            </div>
        </div>
    );
};