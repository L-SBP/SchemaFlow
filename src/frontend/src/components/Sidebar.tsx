
import React from 'react';
import { LayoutDashboard, MessageSquare, Database, Users, FileText, Bell } from 'lucide-react';
import { UserRole } from '../types.ts';

interface SidebarProps {
  role: UserRole;
  activePage: string;
  onNavigate: (page: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ role, activePage, onNavigate }) => {
  const menuItems = role === UserRole.ADMIN ? [
    { id: 'admin_users', label: '用户管理', icon: <Users size={18} /> },
    { id: 'admin_announcements', label: '公告管理', icon: <FileText size={18} /> },
    { id: 'admin_status', label: '系统状态', icon: <LayoutDashboard size={18} /> },
  ] : [
    { id: 'dashboard', label: '项目概览', icon: <LayoutDashboard size={18} /> },
    // Workspace usually accessed via dashboard project selection, but keeping as placeholder if needed
    // { id: 'workspace', label: '智能工作台', icon: <MessageSquare size={18} /> }, 
    { id: 'reports', label: '报表分析', icon: <FileText size={18} /> },
    { id: 'glossary', label: '业务术语', icon: <Database size={18} /> },
    { id: 'announcements', label: '系统公告', icon: <Bell size={18} /> },
  ];

  return (
    <div className="w-64 bg-white border-r border-gray-200 h-screen flex flex-col sticky top-0">
      <div className="p-6 flex items-center gap-3 border-b border-gray-100">
        <div className="w-8 h-8 bg-primary rounded-md flex items-center justify-center text-white font-bold">AI</div>
        <h1 className="font-bold text-gray-800 text-lg tracking-tight">DB Master</h1>
      </div>

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
      
      {/* Logout section removed, moved to Header */}
    </div>
  );
};
