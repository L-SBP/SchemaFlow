import React, { useState, useEffect } from 'react';
import { Announcement } from '../types.ts';
import { Card, Button, Tag, Input, Modal, message, ConfirmDialog, Select } from '../components/UI.tsx';
import { Pagination } from '../components/Pagination.tsx';
import { Plus, Edit, Trash, Bell, Loader2 } from 'lucide-react';
import { announcementApi, CreateAnnouncementParams, UpdateAnnouncementParams } from '../api/announcement.ts';

// 分页配置
const PAGE_SIZE = 10;

export const AdminAnnouncements: React.FC = () => {
    // --- 状态管理 ---
    const [announcements, setAnnouncements] = useState<Announcement[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [isModalOpen, setIsModalOpen] = useState(false);

    // 分页状态
    const [currentPage, setCurrentPage] = useState(1);
    const [totalAnnouncements, setTotalAnnouncements] = useState(0);

    // 当前编辑的公告 ID (null 为新增)
    const [editingId, setEditingId] = useState<number | null>(null);

    // 表单状态
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [status, setStatus] = useState<'published' | 'draft'>('draft');

    // 确认删除对话框状态
    const [isDeleteConfirmOpen, setIsDeleteConfirmOpen] = useState(false);
    const [announcementToDelete, setAnnouncementToDelete] = useState<number | null>(null);

    // --- 数据获取 ---
    const fetchAnnouncements = async (page: number = currentPage) => {
        setIsLoading(true);
        try {
            // 管理员通常需要看到所有状态的公告
            // 由于后端接口目前通过 status 筛选，这里并发请求 draft 和 published 两种状态并合并
            // 实际生产中建议后端提供一个不带 status 过滤的 "all" 选项或专门的管理员列表接口
            const [publishedRes, draftRes] = await Promise.all([
                announcementApi.getList(page, PAGE_SIZE, 'published'),
                announcementApi.getList(page, PAGE_SIZE, 'draft')
            ]);

            // 合并并按 announcement_id 去重，再按创建时间倒序
            const merged = [...publishedRes.items, ...draftRes.items];
            const uniqueById = Array.from(
                new Map(merged.map(a => [a.announcement_id, a])).values()
            ).sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

            setAnnouncements(uniqueById);
            // 设置总数（这里简化处理，实际应该从后端获取准确的总数）
            setTotalAnnouncements(publishedRes.total + draftRes.total);
        } catch (error) {
            console.error("Failed to fetch announcements", error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchAnnouncements();
    }, []);

    // --- 交互处理 ---

    const handleOpenModal = (announcement?: Announcement) => {
        if (announcement) {
            // 编辑模式
            setEditingId(announcement.announcement_id);
            setTitle(announcement.title);
            setContent(announcement.content);
            // 确保 status 是符合类型的
            setStatus(announcement.status === 'published' ? 'published' : 'draft');
        } else {
            // 新增模式
            setEditingId(null);
            setTitle('');
            setContent('');
            setStatus('draft');
        }
        setIsModalOpen(true);
    };

    const handleSave = async () => {
        if (!title.trim()) {
            message.error('请输入公告标题');
            return;
        }
        if (!status) {
            message.error('请选择公告状态');
            return;
        }
        if (!content.trim()) {
            message.error('请输入公告内容');
            return;
        }

        setIsSaving(true);
        try {
            if (editingId) {
                // 更新现有公告
                const updateData: UpdateAnnouncementParams = { title, content, status };
                await announcementApi.update(editingId, updateData);
            } else {
                // 创建新公告
                const createData: CreateAnnouncementParams = { title, content, status };
                await announcementApi.create(createData);
            }
            // 刷新列表并关闭模态框
            await fetchAnnouncements(currentPage);
            setIsModalOpen(false);
        } catch (error) {
            console.error("Failed to save announcement", error);
            message.error("保存失败，请重试");
        } finally {
            setIsSaving(false);
        }
    };

    const handleDelete = async (id: number) => {
        setAnnouncementToDelete(id);
        setIsDeleteConfirmOpen(true);
    };

    const confirmDelete = async () => {
        if (!announcementToDelete) return;

        try {
            await announcementApi.delete(announcementToDelete);
            // 乐观更新 UI
            setAnnouncements(prev => prev.filter(a => a.announcement_id !== announcementToDelete));
            setTotalAnnouncements(prev => prev - 1);
            message.success("公告已删除");
        } catch (error) {
            console.error("Delete failed", error);
            message.error("删除失败");
        }
    };

    // 分页处理
    const handlePageChange = (page: number) => {
        setCurrentPage(page);
        fetchAnnouncements(page);
    };

    return (
        <div className="p-8 max-w-7xl mx-auto h-full flex flex-col overflow-hidden">
            {/* 顶部操作栏 */}
            <div className="flex justify-between items-center mb-8 flex-shrink-0">
                <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-3">
                    <div className="p-2 bg-blue-100 text-blue-600 rounded-lg shrink-0">
                        <Bell size={20} />
                    </div>
                    公告管理
                </h2>
                <Button variant="primary" icon={<Plus size={16} />} onClick={() => handleOpenModal()}>
                    发布新公告
                </Button>
            </div>

            {/* 公告列表 */}
            <div className="flex-1 overflow-y-auto min-h-0">
                {isLoading ? (
                    <div className="flex justify-center items-center h-64">
                        <Loader2 className="animate-spin text-primary" size={32} />
                    </div>
                ) : (
                    <div className="space-y-4 pb-4">
                        {announcements.map(item => (
                            <Card key={item.announcement_id} className="hover:shadow-md transition-shadow">
                                <div className="flex justify-between items-start">
                                    <div className="flex-1 pr-4">
                                        <div className="flex items-center gap-3 mb-2">
                                            <h3 className="font-bold text-gray-800 text-lg">{item.title}</h3>
                                            <Tag color={item.status === 'published' ? 'green' : 'orange'}>
                                                {item.status === 'published' ? '已发布' : '草稿'}
                                            </Tag>
                                            <span className="text-sm text-gray-400">
                                                {new Date(item.created_at).toLocaleDateString()}
                                            </span>
                                        </div>
                                        <p className="text-gray-600 text-sm line-clamp-2">{item.content}</p>
                                    </div>
                                    <div className="flex gap-2 shrink-0">
                                        <Button variant="text" onClick={() => handleOpenModal(item)}>
                                            <Edit size={16} className="text-gray-500 hover:text-primary" />
                                        </Button>
                                        <Button variant="text" onClick={() => handleDelete(item.announcement_id)}>
                                            <Trash size={16} className="text-gray-500 hover:text-red-500" />
                                        </Button>
                                    </div>
                                </div>
                            </Card>
                        ))}
                        {announcements.length === 0 && (
                            <div className="text-center py-12 text-gray-500 bg-white rounded-lg border border-dashed border-gray-300">
                                暂无公告，点击右上角发布
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* 分页控件 - 固定在底部，始终显示 */}
            {totalAnnouncements > 0 && (
                <div className="pagination-container flex-shrink-0">
                    <div className="pagination-wrapper">
                        <Pagination
                            current={currentPage}
                            total={totalAnnouncements}
                            pageSize={PAGE_SIZE}
                            onChange={handlePageChange}
                            showTotal={true}
                            simple={window.innerWidth < 640}
                        />
                    </div>
                </div>
            )}

            {/* 编辑/新增模态框 */}
            <Modal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                title={editingId ? "编辑公告" : "发布新公告"}
                footer={
                    <>
                        <Button onClick={() => setIsModalOpen(false)}>取消</Button>
                        <Button variant="primary" onClick={handleSave} disabled={isSaving}>
                            {isSaving ? '保存中...' : '保存'}
                        </Button>
                    </>
                }
            >
                <div className="space-y-4">
                    <Input
                        label="公告标题"
                        placeholder="请输入标题"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        required
                    />
                    <Select
                        label="状态"
                        className="w-full"
                        value={status}
                        onChange={(val) => setStatus(val as any)}
                        required
                        options={[
                            { value: 'draft', label: '存为草稿' },
                            { value: 'published', label: '立即发布' }
                        ]}
                    />
                    <div className="flex flex-col gap-1.5">
                        <label className="text-sm font-medium text-gray-700">内容<span className="text-red-500 ml-1">*</span></label>
                        <textarea
                            className="px-3 py-2.5 bg-white border border-gray-300 rounded-lg text-sm focus:border-primary focus:ring-2 focus:ring-blue-100 h-32 resize-none outline-none transition-all shadow-sm"
                            placeholder="请输入公告内容..."
                            value={content}
                            onChange={(e) => setContent(e.target.value)}
                        ></textarea>
                    </div>
                </div>
            </Modal>

            {/* 删除公告确认对话框 */}
            <ConfirmDialog
                isOpen={isDeleteConfirmOpen}
                onClose={() => setIsDeleteConfirmOpen(false)}
                onConfirm={confirmDelete}
                title="删除公告"
                message="确定要删除这条公告吗？删除后无法恢复。"
                confirmText="删除"
                cancelText="取消"
                isDangerous={true}
                showWarningIcon={true}
            />
        </div>
    );
};