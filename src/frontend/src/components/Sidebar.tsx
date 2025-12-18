import React, { useEffect, useState } from 'react';
import { LayoutDashboard, Database, Users, FileText, Bell, X, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { UserRole } from '../types'; // 修复: 移除 .ts 后缀

/**
 * 侧边栏组件属性接口
 */
interface SidebarProps {
    /** 当前登录用户的角色（管理员或普通用户） */
    role: UserRole;
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
}

/**
 * 应用程序侧边导航栏组件
 * * 根据用户角色渲染不同的功能菜单列表。
 */
export const Sidebar: React.FC<SidebarProps> = ({ role, activePage, onNavigate, isOpen, onClose }) => {
    const [isCollapsed, setIsCollapsed] = useState(false);

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

    // 根据角色定义菜单项配置
    const menuItems = role === UserRole.ADMIN ? [
        { id: 'admin_users', label: '用户管理', icon: <Users size={18} /> },
        { id: 'admin_announcements', label: '公告管理', icon: <FileText size={18} /> },
        { id: 'admin_status', label: '系统状态', icon: <LayoutDashboard size={18} /> },
    ] : [
        { id: 'dashboard', label: '项目概览', icon: <LayoutDashboard size={18} /> },
        { id: 'reports', label: '报表分析', icon: <FileText size={18} /> },
        { id: 'glossary', label: '业务术语', icon: <Database size={18} /> },
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
                fixed inset-y-0 left-0 w-64 bg-white border-r border-gray-200 h-screen flex flex-col 
                transition-transform duration-300 ease-in-out z-50
                md:translate-x-0 md:static md:sticky md:top-0
                ${isOpen ? 'translate-x-0' : '-translate-x-full'}
                ${isCollapsed ? 'md:w-20' : 'md:w-64'}
            `}>
                {/* 修改: 
                   1. 减小内边距 (p-6 -> p-4) 以减少头部空间占用
                   2. 使用 scale-125 放大图片主体，裁剪周围留白
                   3. 增加 overflow-hidden 防止放大后的图片溢出
                */}
                <div className="p-4 flex items-center justify-between border-b border-gray-100 relative">
                    <div className={`flex items-center gap-3 min-w-0 ${isCollapsed ? 'md:justify-center md:w-full' : ''}`}>
                        <div className="w-8 h-8 flex items-center justify-center overflow-hidden">
                            <img
                                src="public/database-logo.svg"
                                alt="AutoDB Logo"
                                className="w-full h-full object-contain scale-125 transform"
                            />
                        </div>
                        <h1 className={`font-bold text-gray-800 text-lg tracking-tight truncate ${isCollapsed ? 'md:hidden' : ''}`}>AutoDB</h1>
                    </div>

                    <div className="flex items-center gap-1 shrink-0">
                        {/* 桌面端最小化/展开按钮 */}
                        <button
                            onClick={() => setIsCollapsed(v => !v)}
                            className={`hidden md:inline-flex p-1 text-gray-500 hover:bg-gray-100 rounded-md ${isCollapsed ? 'md:absolute md:right-2 md:top-1/2 md:-translate-y-1/2' : ''}`}
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
            </div>
        </>
    );
};