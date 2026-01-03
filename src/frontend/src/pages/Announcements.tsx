import React, { useState, useEffect } from 'react';
import { Announcement } from '../types.ts';
import { Card, Button, Modal, Tag } from '../components/UI.tsx';
import { Pagination } from '../components/Pagination.tsx';
import { Megaphone, Bell, Calendar, Loader2 } from 'lucide-react';
import { announcementApi } from '../api/announcement.ts';

// 分页配置
const PAGE_SIZE = 8;

/**
 * 用户端系统公告页面
 * 用于展示管理员发布的系统维护通知和功能更新。
 */
export const Announcements: React.FC = () => {
    // --- 状态管理 ---
    const [announcements, setAnnouncements] = useState<Announcement[]>([]);
    const [selected, setSelected] = useState<Announcement | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    // 分页状态
    const [currentPage, setCurrentPage] = useState(1);
    const totalAnnouncements = announcements.length;
    const paginatedAnnouncements = announcements.slice(
        (currentPage - 1) * PAGE_SIZE,
        currentPage * PAGE_SIZE
    );

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

    return (
        <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto h-full flex flex-col overflow-hidden">
            {/* 页面头部：标题与图标 - 固定在顶部 */}
            <div className="flex-shrink-0 flex items-center gap-3 mb-6">
                <div className="p-2 bg-blue-100 text-blue-600 rounded-lg shrink-0">
                    <Bell size={20} className="sm:w-6 sm:h-6" />
                </div>
                <div className="min-w-0">
                    <h2 className="text-xl sm:text-2xl font-bold text-gray-800 truncate">系统公告</h2>
                    <p className="text-gray-500 text-sm hidden sm:block">查看最新的系统维护通知与功能更新</p>
                </div>
            </div>

            {/* 公告列表区域 - 可滚动 */}
            <div className="flex-1 overflow-y-auto min-h-0">
                {isLoading ? (
                    <div className="flex justify-center items-center h-64">
                        <Loader2 className="animate-spin text-primary" size={32} />
                    </div>
                ) : (
                    <div className="space-y-3 sm:space-y-4 pb-4">
                        {paginatedAnnouncements.map(item => (
                            <Card key={item.announcement_id} className="hover:shadow-md transition-shadow cursor-pointer hover:border-primary/50" >
                                <div onClick={() => setSelected(item)} className="p-1">
                                    <div className="flex justify-between items-start">
                                        <div className="flex-1 min-w-0">
                                            {/* 标题行：包含红点指示器、标题和 NEW 标签 */}
                                            <div className="flex flex-wrap items-center gap-2 sm:gap-3 mb-2">
                                                <span className="w-2 h-2 rounded-full bg-primary shrink-0"></span>
                                                <h3 className="font-bold text-gray-800 text-base sm:text-lg truncate max-w-[calc(100%-4rem)]">{item.title}</h3>
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
                            <div className="py-12 sm:py-16 text-center text-gray-400 bg-white rounded-xl border border-gray-200">
                                <Megaphone size={40} className="mx-auto mb-4 opacity-20" />
                                <p className="text-sm sm:text-base">暂无已发布的系统公告</p>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* 分页控件 - 固定在底部，始终显示 */}
            {totalAnnouncements > 0 && (
                <div className="pagination-container">
                    <div className="pagination-wrapper">
                        <Pagination
                            current={currentPage}
                            total={totalAnnouncements}
                            pageSize={PAGE_SIZE}
                            onChange={setCurrentPage}
                            showTotal={true}
                            simple={window.innerWidth < 640}
                        />
                    </div>
                </div>
            )}

            {/* 公告详情模态框 */}
            <Modal
                isOpen={!!selected}
                onClose={() => setSelected(null)}
                title="公告详情"
                maxWidth="max-w-5xl"
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