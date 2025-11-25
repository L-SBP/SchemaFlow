import React, { useState } from 'react';
import { Announcement } from '../types.ts';
import { Card, Button, Modal, Tag } from '../components/UI.tsx';
import { Megaphone, Bell, Calendar } from 'lucide-react';

/**
 * 公告列表组件属性接口
 */
interface AnnouncementsProps {
    /** 系统中的所有公告列表（可能包含草稿状态） */
    announcements: Announcement[];
}

/**
 * 用户端系统公告页面
 * * 用于展示管理员发布的系统维护通知和功能更新。
 * * 包含列表展示、状态过滤（仅显示已发布）以及详情查看功能。
 */
export const Announcements: React.FC<AnnouncementsProps> = ({ announcements }) => {
    /** * 当前选中的公告对象
     * * 用于控制详情模态框的显示与内容。如果不为 null，则模态框打开。
     */
    const [selected, setSelected] = useState<Announcement | null>(null);
    
    /**
     * 过滤后的公告列表
     * * 仅向普通用户展示状态为 'published' 的公告，隐藏草稿。
     */
    const publishedAnnouncements = announcements.filter(a => a.status === 'published');
    
    return (
        <div className="p-8 max-w-7xl mx-auto h-full overflow-y-auto">
            {/* 页面头部：标题与图标 */}
            <div className="flex items-center gap-3 mb-8">
                <div className="p-2 bg-orange-100 text-orange-600 rounded-lg">
                    <Bell size={24} />
                </div>
                <div>
                    <h2 className="text-2xl font-bold text-gray-800">系统公告</h2>
                    <p className="text-gray-500">查看最新的系统维护通知与功能更新</p>
                </div>
            </div>
            
            {/* 公告列表区域 */}
            <div className="space-y-4">
                {publishedAnnouncements.map(item => (
                    <Card key={item.id} className="hover:shadow-md transition-shadow cursor-pointer hover:border-primary/50" >
                        <div onClick={() => setSelected(item)}>
                            <div className="flex justify-between items-start">
                                <div className="flex-1">
                                    {/* 标题行：包含红点指示器、标题和 NEW 标签 */}
                                    <div className="flex items-center gap-3 mb-2">
                                        <span className="w-2 h-2 rounded-full bg-primary"></span>
                                        <h3 className="font-bold text-gray-800 text-lg">{item.title}</h3>
                                        
                                        {/* 逻辑：如果是 3 天内发布的公告，显示 NEW 标签 */}
                                        {new Date(item.date) > new Date(Date.now() - 86400000 * 3) && (
                                            <Tag color="red">NEW</Tag>
                                        )}
                                    </div>
                                    
                                    {/* 内容摘要：限制显示 2 行 */}
                                    <p className="text-gray-600 text-sm line-clamp-2 mb-3">{item.content}</p>
                                    
                                    {/* 底部元数据：发布日期 */}
                                    <div className="flex items-center gap-2 text-xs text-gray-400">
                                        <Calendar size={12} /> 发布于 {item.date}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </Card>
                ))}
                
                {/* 空状态展示 */}
                {publishedAnnouncements.length === 0 && (
                    <div className="py-16 text-center text-gray-400 bg-white rounded-xl border border-gray-200">
                        <Megaphone size={48} className="mx-auto mb-4 opacity-20" />
                        <p>暂无已发布的系统公告</p>
                    </div>
                )}
            </div>
            
            {/* 公告详情模态框 */}
            <Modal
                isOpen={!!selected}
                onClose={() => setSelected(null)}
                title="公告详情"
                footer={<Button onClick={() => setSelected(null)}>关闭</Button>}
            >
                {selected && (
                    <div>
                        <h3 className="text-xl font-bold text-gray-800 mb-2">{selected.title}</h3>
                        <div className="text-sm text-gray-500 mb-6 flex items-center gap-2">
                            <Calendar size={14} /> {selected.date}
                        </div>
                        {/* 这里的 whitespace-pre-wrap 保证了公告内容的换行符能被正确渲染 */}
                        <div className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                            {selected.content}
                        </div>
                    </div>
                )}
            </Modal>
        </div>
    );
};