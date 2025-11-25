import React from 'react';
import { LayoutDashboard, MessageSquare, Database, Users, FileText, Bell } from 'lucide-react';
import { UserRole } from '../types.ts';

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
}

/**
 * 应用程序侧边导航栏组件
 * * 根据用户角色渲染不同的功能菜单列表。
 * - 管理员：用户管理、公告管理、系统状态
 * - 普通用户：项目概览、报表分析、业务术语、系统公告
 *
 * @param {SidebarProps} props - 组件属性
 * @returns {JSX.Element} 侧边栏元素
 */
export const Sidebar: React.FC<SidebarProps> = ({ role, activePage, onNavigate }) => {
    // 根据角色定义菜单项配置
    const menuItems = role === UserRole.ADMIN ? [
        { id: 'admin_users', label: '用户管理', icon: <Users size={18} /> },
        { id: 'admin_announcements', label: '公告管理', icon: <FileText size={18} /> },
        { id: 'admin_status', label: '系统状态', icon: <LayoutDashboard size={18} /> },
    ] : [
        { id: 'dashboard', label: '项目概览', icon: <LayoutDashboard size={18} /> },
        // Workspace 通常通过仪表盘的项目选择进入，但在需要时可作为占位符启用
        // { id: 'workspace', label: '智能工作台', icon: <MessageSquare size={18} /> },
        { id: 'reports', label: '报表分析', icon: <FileText size={18} /> },
        { id: 'glossary', label: '业务术语', icon: <Database size={18} /> },
        { id: 'announcements', label: '系统公告', icon: <Bell size={18} /> },
    ];
    
    return (
        <div className="w-64 bg-white border-r border-gray-200 h-screen flex flex-col sticky top-0">
            {/* 应用 Logo 区域 */}
            <div className="p-6 flex items-center gap-3 border-b border-gray-100">
                <div className="w-8 h-8 bg-primary rounded-md flex items-center justify-center text-white font-bold">AI</div>
                <h1 className="font-bold text-gray-800 text-lg tracking-tight">DB Master</h1>
            </div>
            
            {/* 菜单列表区域 */}
            <div className="flex-1 py-4 px-3 space-y-1">
                {menuItems.map((item) => (
                    <button
                        key={item.id}
                        onClick={() => onNavigate(item.id)}
                        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
                            activePage === item.id
                                ? 'bg-blue-50 text-primary'
                                : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                        }`}
                    >
                        {item.icon}
                        {item.label}
                    </button>
                ))}
            </div>
            
            {/* 注：退出登录功能已移动至 Header 组件 */}
        </div>
    );
};