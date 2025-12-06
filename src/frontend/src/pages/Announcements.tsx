import React, { useState, useEffect } from 'react';
import { Announcement } from '../types.ts';
import { Card, Button, Modal, Tag } from '../components/UI.tsx';
import { Megaphone, Bell, Calendar, Loader2 } from 'lucide-react';
import { announcementApi } from '../api/announcement.ts';

/**
 * 用户端系统公告页面
 * 用于展示管理员发布的系统维护通知和功能更新。
 */
export const Announcements: React.FC = () => {
    // --- 状态管理 ---
    const [announcements, setAnnouncements] = useState<Announcement[]>([]);
    const [selected, setSelected] = useState<Announcement | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    // --- 数据获取 ---
    const fetchPublishedAnnouncements = async () => {
        setIsLoading(true);
        try {
            // 用户端仅展示 published 状态的公告
            const res = await announcementApi.getList(1, 50, 'published');
            // 按时间倒序排列
            const sorted = res.items.sort((a, b) =>
                new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
            );
            setAnnouncements(sorted);
        } catch (error) {
            console.error("Failed to fetch announcements", error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchPublishedAnnouncements();
    }, []);

    // 辅助函数：判断是否为最近 3 天内发布
    const isNew = (dateStr: string) => {
        return new Date(dateStr) > new Date(Date.now() - 86400000 * 3);
    };

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
            {isLoading ? (
                <div className="flex justify-center items-center h-64">
                    <Loader2 className="animate-spin text-primary" size={32} />
                </div>
            ) : (
                <div className="space-y-4">
                    {announcements.map(item => (
                        <Card key={item.announcement_id} className="hover:shadow-md transition-shadow cursor-pointer hover:border-primary/50" >
                            <div onClick={() => setSelected(item)}>
                                <div className="flex justify-between items-start">
                                    <div className="flex-1">
                                        {/* 标题行：包含红点指示器、标题和 NEW 标签 */}
                                        <div className="flex items-center gap-3 mb-2">
                                            <span className="w-2 h-2 rounded-full bg-primary"></span>
                                            <h3 className="font-bold text-gray-800 text-lg">{item.title}</h3>

                                            {isNew(item.created_at) && (
                                                <Tag color="red">NEW</Tag>
                                            )}
                                        </div>

                                        {/* 内容摘要：限制显示 2 行 */}
                                        <p className="text-gray-600 text-sm line-clamp-2 mb-3">{item.content}</p>

                                        {/* 底部元数据：发布日期 */}
                                        <div className="flex items-center gap-2 text-xs text-gray-400">
                                            <Calendar size={12} /> 发布于 {new Date(item.created_at).toLocaleDateString()}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </Card>
                    ))}

                    {/* 空状态展示 */}
                    {announcements.length === 0 && (
                        <div className="py-16 text-center text-gray-400 bg-white rounded-xl border border-gray-200">
                            <Megaphone size={48} className="mx-auto mb-4 opacity-20" />
                            <p>暂无已发布的系统公告</p>
                        </div>
                    )}
                </div>
            )}

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
                            <Calendar size={14} /> {new Date(selected.created_at).toLocaleString()}
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