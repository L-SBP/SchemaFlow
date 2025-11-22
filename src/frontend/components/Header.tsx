import React, { useState, useRef, useEffect } from 'react';
import { UserRole } from '../types';
import { LogOut, User as UserIcon, Settings } from 'lucide-react';

interface HeaderProps {
  user: { name: string; role: UserRole } | null;
  onLogout: () => void;
  onNavigate: (page: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ user, onLogout, onNavigate }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="h-16 bg-white border-b border-gray-200 px-8 flex justify-end items-center sticky top-0 z-20 shrink-0">
      <div className="relative" ref={dropdownRef}>
        <button 
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-3 focus:outline-none hover:bg-gray-50 p-2 rounded-lg transition-colors"
        >
          <div className="text-right hidden sm:block">
            <div className="text-sm font-medium text-gray-700">{user?.name}</div>
            <div className="text-xs text-gray-500">{user?.role === UserRole.ADMIN ? '管理员' : '普通用户'}</div>
          </div>
          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-primary border border-blue-200">
            <UserIcon size={20} />
          </div>
        </button>

        {isOpen && (
          <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-100 py-1 animate-in fade-in zoom-in-95 duration-100 origin-top-right">
            <button 
              onClick={() => {
                setIsOpen(false);
                onNavigate('profile');
              }}
              className="w-full text-left px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
            >
              <Settings size={16} /> 个人设置
            </button>
            <div className="border-t border-gray-100 my-1"></div>
            <button 
              onClick={() => {
                setIsOpen(false);
                onLogout();
              }}
              className="w-full text-left px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
            >
              <LogOut size={16} /> 退出登录
            </button>
          </div>
        )}
      </div>
    </header>
  );
};