/**
 * @file Sidebar.tsx
 * @module Components/Layout/Global-Sidebar
 * @description 应用程序全局侧边导航组件。
 * 本组件作为“基于大模型多智能体框架的数据库自动部署与库表生成系统”的交互枢纽。
 * * 核心设计目标：
 * 1. 动态权限渲染 (RBAC): 根据用户角色 (Admin/User) 分发差异化的功能菜单项；
 * 2. 交互偏好持久化: 自动同步侧边栏折叠状态至本地存储空间，确保视觉体验的连续性；
 * 3. 响应式适配架构: 采用双轨布局逻辑，支持移动端侧滑抽屉与桌面端迷你栏切换；
 * 4. 工作台深度联动: 实时反馈当前选中的数据库项目上下文 (Context-Awareness)。
 * * @author Wang Lirong (王利蓉)
 * @version 2.4.0
 * @date 2026-01-02
 */

import React, { useEffect, useRef, useState } from 'react';
import { LayoutDashboard, BarChart2, Users, Book, Bell, X, PanelLeftClose, PanelLeftOpen, User as UserIcon, Settings, LogOut, Database, Bot } from 'lucide-react';
import { UserRole } from '../types';

/**
 * 侧边栏组件属性接口定义
 * @interface SidebarProps
 * @description 封装了侧边栏渲染所需的权限、用户信息及路由导航回调。
 */
interface SidebarProps {
    /** 当前登录用户的角色标识（决定菜单权限矩阵） */
    role: UserRole;
    /** 当前登录用户的档案数据摘要（头像、名称、角色展示） */
    user?: { name: string; role: UserRole; avatar_url?: string | null } | null;
    /** 全局选中的活跃项目上下文，用于显示“当前工作区”状态 */
    selectedProject?: { id: string; name: string } | null;
    /** 当前活跃页面的 ID，用于驱动导航项的激活态高亮显示 */
    activePage: string;
    /** * 路由导航触发函数
     * @param {string} page - 目标页面的唯一路由标识符 
     */
    onNavigate: (page: string) => void;
    /** 移动端环境下的展示状态开关（由父级布局容器控制） */
    isOpen?: boolean;
    /** 触发移动端侧边栏关闭逻辑的回调函数 */
    onClose?: () => void;
    /** 退出登录并清理安全凭证的业务回调 */
    onLogout?: () => void;
}

/**
 * @component Sidebar
 * @description 
 * 一个具备高度自律性的响应式布局组件。
 * 内部通过 Side Effect 管理视口状态，并采用原子化 CSS (Tailwind) 实现复杂的动画过渡。
 */
export const Sidebar: React.FC<SidebarProps> = ({ role, user, selectedProject, activePage, onNavigate, isOpen, onClose, onLogout }) => {
    /** * 桌面端折叠状态锁
     * 控制侧边栏在 256px (w-64) 与 64px (w-16) 宽度之间的切换。
     */
    const [isCollapsed, setIsCollapsed] = useState(false);
    /** 底部个人信息面板的下拉菜单可见性状态 */
    const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
    /** 引用底部用户菜单容器，用于执行“点击外部自动关闭”的 DOM 监听逻辑 */
    const userMenuRef = useRef<HTMLDivElement>(null);

    /**
     * 生命周期 A：偏好恢复。
     * 在组件初次挂载时，从 localStorage 中同步用户上次设置的侧边栏形态。
     */
    useEffect(() => {
        try {
            const raw = localStorage.getItem('app.sidebarCollapsed');
            setIsCollapsed(raw === '1');
        } catch {
            // 容错：若 Storage 访问受限（如隐私模式），维持默认展开状态
        }
    }, []);

    /**
     * 生命周期 B：偏好存储。
     * 当折叠状态发生变化时，执行离线持久化存储。
     */
    useEffect(() => {
        try {
            localStorage.setItem('app.sidebarCollapsed', isCollapsed ? '1' : '0');
        } catch {
            // 静默处理非关键性存储失败
        }
    }, [isCollapsed]);

    /**
     * 生命周期 C：外部点击捕获。
     * 注册全局鼠标监听器，实现典型的 Dropdown 失焦关闭逻辑。
     */
    useEffect(() => {
        /**
         * 判定点击是否发生在目标容器之外
         * @param {MouseEvent} event - 原生浏览器点击事件
         */
        const handleClickOutside = (event: MouseEvent) => {
            if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
                setIsUserMenuOpen(false);
            }
        };
        // 在 document 层面委托监听，确保能捕获所有点击流
        document.addEventListener('mousedown', handleClickOutside);
        // 卸载钩子：注销监听器，防止内存泄漏
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    /**
     * 核心逻辑：菜单权限路由表。
     * 采用静态映射策略，根据当前 UserRole 派发特定的导航矩阵。
     * 管理员侧重系统治理，普通用户侧重业务建模。
     */
    const menuItems = role === UserRole.ADMIN ? [
        { id: 'admin_users', label: '用户管理', icon: <Users size={18} /> },
        { id: 'admin_announcements', label: '公告管理', icon: <Bell size={18} /> },
        { id: 'admin_ai_models', label: '模型配置', icon: <Bot size={18} /> },
        { id: 'admin_status', label: '系统状态', icon: <LayoutDashboard size={18} /> },
    ] : [
        { id: 'dashboard', label: '项目概览', icon: <LayoutDashboard size={18} /> },
        { id: 'reports', label: '报表分析', icon: <BarChart2 size={18} /> },
        { id: 'glossary', label: '业务术语', icon: <Book size={18} /> },
        { id: 'announcements', label: '系统公告', icon: <Bell size={18} /> },
    ];

    return (
        <>
            {/* 移动端背景蒙层 (Overlay Mask)
                - z-40 层级确保其覆盖 Header 但低于侧边栏本身。
                - 点击遮罩将触发 onClose 事件，关闭移动端菜单。
            */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-40 md:hidden animate-in fade-in duration-300"
                    onClick={onClose}
                />
            )}

            {/* 侧边栏主容器 (Sidebar Main Container)
                - transition-[transform,width]: 允许宽度和位置属性参与过渡动画。
                - z-50: 确保侧边栏处于全局最高层级。
                - md:static: 桌面端回归标准文档流或使用 sticky 停靠。
            */}
            <div className={`
                fixed inset-y-0 left-0 w-64 bg-white border-r border-gray-200 h-screen h-[100dvh] flex flex-col 
                transition-[transform,width] duration-300 ease-in-out motion-reduce:transition-none z-50 overflow-x-hidden
                md:translate-x-0 md:static md:sticky md:top-0 md:h-screen md:h-[100dvh]
                ${isOpen ? 'translate-x-0' : '-translate-x-full'}
                ${isCollapsed ? 'md:w-16' : 'md:w-64'}
            `}>

                {/* 头部 Logo 区域 (Header & Branding)
                    集成了品牌标识与折叠控制器。
                */}
                <div className="p-4 flex items-center justify-between border-b border-gray-100 relative">
                    {/* 非折叠状态下展示品牌图形与文字 */}
                    {!isCollapsed && (
                        <div className="flex items-center gap-3 min-w-0">
                            <div className="w-8 h-8 flex items-center justify-center overflow-hidden">
                                {/* scale-125: 采用放大裁剪策略提升图标视觉冲击力 */}
                                <img
                                    src="/database-logo.svg"
                                    alt="AutoDB Logo"
                                    className="w-full h-full object-contain scale-125 transform transition-transform duration-500 hover:rotate-6"
                                />
                            </div>
                            <h1 className="font-bold text-gray-800 text-lg tracking-tight truncate">AutoDB</h1>
                        </div>
                    )}

                    {/* 侧边栏交互控制按钮群组 */}
                    <div className="flex items-center gap-1 shrink-0">
                        {/* 桌面端特有：折叠状态切换器 */}
                        <button
                            onClick={() => setIsCollapsed(v => !v)}
                            className={`hidden md:inline-flex p-1 text-gray-500 hover:bg-gray-100 rounded-md items-center justify-center ${isCollapsed ? 'md:mx-auto md:absolute md:left-1/2 md:-translate-x-1/2 md:top-1/2 md:-translate-y-1/2' : ''}`}
                            title={isCollapsed ? '展开侧边栏' : '最小化侧边栏'}
                            type="button"
                        >
                            {/* 动态切换展开/折叠图标语义 */}
                            {isCollapsed ? <PanelLeftOpen size={20} /> : <PanelLeftClose size={20} />}
                        </button>

                        {/* 移动端特有：明确的关闭动作出口 */}
                        <button onClick={onClose} className="md:hidden p-1 text-gray-500 hover:bg-gray-100 rounded-md" type="button">
                            <X size={20} />
                        </button>
                    </div>
                </div>

                {/* 主体导航区域 (Main Navigation Links)
                    采用 flex-1 占据中间剩余空间，内容超出时支持内部滚动。
                */}
                <div className={`flex-1 py-4 space-y-1 overflow-y-auto custom-scrollbar ${isCollapsed ? 'px-2' : 'px-3'}`}>

                    {/* 当前工作区上下文入口 (Dynamic Context Slot)
                        仅对普通用户展示，用于快速定位当前的 AI 建模任务。
                    */}
                    {role !== UserRole.ADMIN && (
                        <button
                            onClick={() => {
                                if (selectedProject) {
                                    onNavigate('workspace');
                                } else {
                                    onNavigate('dashboard');
                                }
                                onClose?.();
                            }}
                            title={selectedProject ? `当前工作区：${selectedProject.name}` : '未选择工作区'}
                            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-all duration-200 ${activePage === 'workspace'
                                ? 'bg-blue-50 text-primary shadow-sm ring-1 ring-blue-100'
                                : selectedProject
                                    ? 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                                    : 'text-gray-400 hover:bg-gray-50'
                                } ${isCollapsed ? 'md:justify-center md:gap-0 md:px-0 md:h-11 md:w-11 md:mx-auto' : ''}`}
                            type="button"
                        >
                            <span className="shrink-0"><Database size={18} /></span>
                            <span className={`${isCollapsed ? 'md:hidden' : ''} min-w-0 flex-1 text-left`}
                            >
                                <div className="truncate font-semibold">当前工作区</div>
                                {selectedProject ? (
                                    <div className="text-[10px] text-gray-500 truncate leading-tight">{selectedProject.name}</div>
                                ) : (
                                    <div className="text-[10px] text-gray-400 truncate leading-tight">未选择</div>
                                )}
                            </span>
                        </button>
                    )}

                    {/* 映射并渲染核心菜单阵列 */}
                    {menuItems.map((item) => (
                        <button
                            key={item.id}
                            onClick={() => {
                                onNavigate(item.id);
                                onClose?.();
                            }}
                            title={item.label}
                            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-all duration-200 ${activePage === item.id
                                ? 'bg-blue-50 text-primary shadow-sm ring-1 ring-blue-100'
                                : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                                } ${isCollapsed ? 'md:justify-center md:gap-0 md:px-0 md:h-11 md:w-11 md:mx-auto' : ''}`}
                        >
                            <span className="shrink-0">{item.icon}</span>
                            <span className={`${isCollapsed ? 'md:hidden' : ''}`}>{item.label}</span>
                        </button>
                    ))}
                </div>

                {/* 底部账户管理中心 (Bottom Account Section)
                    集成了用户身份标识与浮动快捷菜单。
                */}
                <div className={`border-t border-gray-100 relative ${isCollapsed ? 'p-2' : 'p-3'}`} ref={userMenuRef}>
                    {/* 触发器：点击展现个人中心菜单 */}
                    <button
                        type="button"
                        onClick={() => setIsUserMenuOpen(v => !v)}
                        title={isCollapsed ? `${user?.name || '当前用户'}（点击展开菜单）` : undefined}
                        className={`w-full flex items-center gap-3 rounded-lg hover:bg-gray-50 transition-colors ${isCollapsed ? 'md:justify-center md:gap-0 md:px-0 md:h-11 md:w-11 md:mx-auto' : 'px-2 py-2'}`}
                    >
                        {/* 头像渲染容器：支持外部图片与通用图标兜底 */}
                        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-primary border border-blue-200 overflow-hidden shrink-0">
                            {user?.avatar_url ? (
                                <img src={user.avatar_url} alt={user?.name || 'avatar'} className="w-full h-full object-cover" />
                            ) : (
                                <UserIcon size={20} />
                            )}
                        </div>
                        {/* 身份描述：仅在非折叠状态下渲染 */}
                        <div className={`${isCollapsed ? 'md:hidden' : ''} min-w-0 flex-1 text-left`}
                        >
                            <div className="text-sm font-medium text-gray-700 truncate">{user?.name || '当前用户'}</div>
                            <div className="text-xs text-gray-500 font-normal">{user?.role === UserRole.ADMIN ? '系统管理员' : '普通用户'}</div>
                        </div>
                    </button>

                    {/* 个人操作浮层 (User Action Floating Menu)
                        - 利用绝对定位实现“上浮”弹出效果。
                        - 具备 animate-in 动画以增强视觉质感。
                    */}
                    {isUserMenuOpen && (
                        <div
                            className={`${isCollapsed ? 'md:absolute md:left-full md:bottom-3 md:ml-2 md:w-48' : 'absolute left-0 bottom-full mb-2 w-full'} bg-white rounded-lg shadow-lg border border-gray-100 py-1 animate-in fade-in zoom-in-95 duration-150 origin-bottom z-50`}
                        >
                            {/* 设置项入口 */}
                            <button
                                onClick={() => {
                                    setIsUserMenuOpen(false);
                                    onNavigate('profile');
                                    onClose?.();
                                }}
                                className="w-full text-left px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2 transition-colors"
                                type="button"
                            >
                                <Settings size={16} /> 个人设置
                            </button>
                            {/* 分割线：视觉分区 */}
                            <div className="border-t border-gray-100 my-1"></div>
                            {/* 退出登录：具备警示语义的颜色提示 */}
                            <button
                                onClick={() => {
                                    setIsUserMenuOpen(false);
                                    onLogout?.();
                                }}
                                className="w-full text-left px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2 transition-colors"
                                type="button"
                            >
                                <LogOut size={16} /> 退出登录
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </>
    );
};