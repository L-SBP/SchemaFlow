import React, { useEffect, useRef, useState } from 'react';
import { LayoutDashboard, BarChart2, Users, Book, Bell, X, PanelLeftClose, PanelLeftOpen, User as UserIcon, Settings, LogOut, Database, Bot } from 'lucide-react';
import { UserRole } from '../types'; // 修复: 移除 .ts 后缀

/**
 * 侧边栏组件属性接口
 */
interface SidebarProps {
    /** 当前登录用户的角色（管理员或普通用户） */
    role: UserRole;
    /** 当前登录用户信息（用于底部展示头像/名称/角色） */
    user?: { name: string; role: UserRole; avatar_url?: string | null } | null;
    /** 当前选择的项目工作区（用于显示“当前工作区”入口） */
    selectedProject?: { id: string; name: string } | null;
    /** 当前激活的页面 ID，用于高亮显示菜单项 */
    activePage: string;
    /** * 页面导航回调函数
     * @param page - 目标页面的 ID
     */
    onNavigate: (page: string) => void;
    /** 移动端菜单是否打开 */
    isOpen?: boolean;
    /** 关闭移动端菜单的回调 */
    onClose?: () => void;
    /** 退出登录回调（用于底部用户菜单） */
    onLogout?: () => void;
}

/**
 * 应用程序侧边导航栏组件
 * * 根据用户角色渲染不同的功能菜单列表。
 */
export const Sidebar: React.FC<SidebarProps> = ({ role, user, selectedProject, activePage, onNavigate, isOpen, onClose, onLogout }) => {
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
    const userMenuRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        try {
            const raw = localStorage.getItem('app.sidebarCollapsed');
            setIsCollapsed(raw === '1');
        } catch {
            // ignore
        }
    }, []);

    useEffect(() => {
        try {
            localStorage.setItem('app.sidebarCollapsed', isCollapsed ? '1' : '0');
        } catch {
            // ignore
        }
    }, [isCollapsed]);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
                setIsUserMenuOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // 根据角色定义菜单项配置
    const menuItems = role === UserRole.ADMIN ? [
        { id: 'admin_users', label: '用户管理', icon: <Users size={18} /> },
        { id: 'admin_announcements', label: '公告管理', icon: <Bell size={18} /> },
        { id: 'admin_ai_models', label: 'AI模型配置', icon: <Bot size={18} /> },
        { id: 'admin_status', label: '系统状态', icon: <LayoutDashboard size={18} /> },
    ] : [
        { id: 'dashboard', label: '项目概览', icon: <LayoutDashboard size={18} /> },
        { id: 'reports', label: '报表分析', icon: <BarChart2 size={18} /> },
        { id: 'glossary', label: '业务术语', icon: <Book size={18} /> },
        { id: 'announcements', label: '系统公告', icon: <Bell size={18} /> },
    ];

    return (
        <>
            {/* 移动端遮罩层 - z-40 ensures it covers the header (z-20) */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-40 md:hidden"
                    onClick={onClose}
                />
            )}

            {/* 侧边栏容器 - z-50 ensures it's on top of everything */}
            <div className={`
                fixed inset-y-0 left-0 w-64 bg-white border-r border-gray-200 h-screen h-[100dvh] flex flex-col 
                transition-[transform,width] duration-300 ease-in-out motion-reduce:transition-none z-50
                md:translate-x-0 md:static md:sticky md:top-0 md:h-screen md:h-[100dvh]
                ${isOpen ? 'translate-x-0' : '-translate-x-full'}
                ${isCollapsed ? 'md:w-16' : 'md:w-64'}
            `}>
                {/* 修改: 
                   1. 减小内边距 (p-6 -> p-4) 以减少头部空间占用
                   2. 使用 scale-125 放大图片主体，裁剪周围留白
                   3. 增加 overflow-hidden 防止放大后的图片溢出
                */}
                <div className="p-4 flex items-center justify-between border-b border-gray-100 relative">
                    {/* 桌面端折叠时：不显示任何图标/Logo，仅保留展开按钮 */}
                    {!isCollapsed && (
                        <div className="flex items-center gap-3 min-w-0">
                            <div className="w-8 h-8 flex items-center justify-center overflow-hidden">
                                <img
                                    src="public/database-logo.svg"
                                    alt="AutoDB Logo"
                                    className="w-full h-full object-contain scale-125 transform"
                                />
                            </div>
                            <h1 className="font-bold text-gray-800 text-lg tracking-tight truncate">AutoDB</h1>
                        </div>
                    )}

                    <div className="flex items-center gap-1 shrink-0">
                        {/* 桌面端最小化/展开按钮 */}
                        <button
                            onClick={() => setIsCollapsed(v => !v)}
                            className={`hidden md:inline-flex p-1 text-gray-500 hover:bg-gray-100 rounded-md items-center justify-center ${isCollapsed ? 'md:mx-auto md:absolute md:left-1/2 md:-translate-x-1/2 md:top-1/2 md:-translate-y-1/2' : ''}`}
                            title={isCollapsed ? '展开侧边栏' : '最小化侧边栏'}
                            type="button"
                        >
                            {isCollapsed ? <PanelLeftOpen size={20} /> : <PanelLeftClose size={20} />}
                        </button>

                        {/* 移动端关闭按钮 */}
                        <button onClick={onClose} className="md:hidden p-1 text-gray-500 hover:bg-gray-100 rounded-md" type="button">
                            <X size={20} />
                        </button>
                    </div>
                </div>

                {/* 菜单列表区域 */}
                <div className="flex-1 py-4 px-3 space-y-1">
                    {/* 当前工作区（仅普通用户显示） */}
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
                            title={selectedProject ? `当前工作区：${selectedProject.name}` : '未选择工作区（去项目概览选择）'}
                            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${activePage === 'workspace'
                                ? 'bg-blue-50 text-primary'
                                : selectedProject
                                    ? 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                                    : 'text-gray-400 hover:bg-gray-50'
                                } ${isCollapsed ? 'md:justify-center md:gap-0 md:px-0 md:h-11 md:w-11 md:mx-auto' : ''}`}
                            type="button"
                        >
                            <span className="shrink-0"><Database size={18} /></span>
                            <span className={`${isCollapsed ? 'md:hidden' : ''} min-w-0 flex-1 text-left`}
                            >
                                <div className="truncate">当前工作区</div>
                                {selectedProject ? (
                                    <div className="text-xs text-gray-500 truncate">{selectedProject.name}</div>
                                ) : (
                                    <div className="text-xs text-gray-400 truncate">未选择</div>
                                )}
                            </span>
                        </button>
                    )}

                    {menuItems.map((item) => (
                        <button
                            key={item.id}
                            onClick={() => {
                                onNavigate(item.id);
                                onClose?.();
                            }}
                            title={item.label}
                            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${activePage === item.id
                                ? 'bg-blue-50 text-primary'
                                : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                                } ${isCollapsed ? 'md:justify-center md:gap-0 md:px-0 md:h-11 md:w-11 md:mx-auto' : ''}`}
                        >
                            <span className="shrink-0">{item.icon}</span>
                            <span className={`${isCollapsed ? 'md:hidden' : ''}`}>{item.label}</span>
                        </button>
                    ))}
                </div>

                {/* 底部：当前用户信息（头像/名称/角色） + 菜单（个人设置/退出登录） */}
                <div className="border-t border-gray-100 p-3 relative" ref={userMenuRef}>
                    <button
                        type="button"
                        onClick={() => setIsUserMenuOpen(v => !v)}
                        title={isCollapsed ? `${user?.name || '当前用户'}（点击展开菜单）` : undefined}
                        className={`w-full flex items-center gap-3 rounded-lg hover:bg-gray-50 transition-colors ${isCollapsed ? 'md:justify-center md:gap-0 md:px-0 md:h-11 md:w-11 md:mx-auto' : 'px-2 py-2'}`}
                    >
                        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-primary border border-blue-200 overflow-hidden shrink-0">
                            {user?.avatar_url ? (
                                <img src={user.avatar_url} alt={user?.name || 'avatar'} className="w-full h-full object-cover" />
                            ) : (
                                <UserIcon size={20} />
                            )}
                        </div>
                        <div className={`${isCollapsed ? 'md:hidden' : ''} min-w-0 flex-1 text-left`}
                        >
                            <div className="text-sm font-medium text-gray-700 truncate">{user?.name || '当前用户'}</div>
                            <div className="text-xs text-gray-500">{user?.role === UserRole.ADMIN ? '管理员' : '普通用户'}</div>
                        </div>
                    </button>

                    {isUserMenuOpen && (
                        <div
                            className={`${isCollapsed ? 'md:absolute md:left-full md:bottom-3 md:ml-2 md:w-48' : 'absolute left-0 bottom-full mb-2 w-full'} bg-white rounded-lg shadow-lg border border-gray-100 py-1 animate-in fade-in zoom-in-95 duration-100 origin-top z-50`}
                        >
                            <button
                                onClick={() => {
                                    setIsUserMenuOpen(false);
                                    onNavigate('profile');
                                    onClose?.();
                                }}
                                className="w-full text-left px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                                type="button"
                            >
                                <Settings size={16} /> 个人设置
                            </button>
                            <div className="border-t border-gray-100 my-1"></div>
                            <button
                                onClick={() => {
                                    setIsUserMenuOpen(false);
                                    onLogout?.();
                                }}
                                className="w-full text-left px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
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