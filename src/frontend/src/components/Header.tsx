import React from 'react';
import { Menu } from 'lucide-react';

/**
 * 顶部导航栏属性接口
 */
interface HeaderProps {
    /** 切换侧边栏显示状态 */
    onToggleSidebar: () => void;
}

/**
 * 全局顶部导航栏组件
 * * 包含用户头像、名称展示以及下拉菜单（个人设置、退出登录）。
 * 实现了点击外部区域自动关闭下拉菜单的逻辑。
 *
 * @param {HeaderProps} props - 组件属性
 * @returns {JSX.Element} 顶部栏元素
 */
export const Header: React.FC<HeaderProps> = ({ onToggleSidebar }) => {
    return (
        <header className="h-16 bg-white border-b border-gray-200 px-4 flex items-center sticky top-0 z-20 shrink-0 md:hidden">
            <div className="flex items-center">
                <button
                    onClick={onToggleSidebar}
                    className="p-2 text-gray-600 hover:bg-gray-100 rounded-md"
                >
                    <Menu size={24} />
                </button>
            </div>
        </header>
    );
};