import React, { useState } from 'react';
import { Announcement } from '../types.ts';
import { Card, Button, Tag, Input, Modal } from '../components/UI.tsx';
import { Plus, Edit, Trash, Megaphone } from 'lucide-react';

/**
 * 公告管理组件属性接口
 */
interface AdminAnnouncementsProps {
    /** 当前公告列表数据 */
    announcements: Announcement[];
    /** 更新公告列表的 Setter */
    setAnnouncements: React.Dispatch<React.SetStateAction<Announcement[]>>;
}

/**
 * 管理员公告发布面板
 * * 允许管理员创建、编辑、删除系统公告。
 * * 支持区分 "published" (已发布) 和 "draft" (草稿) 状态。
 */
export const AdminAnnouncements: React.FC<AdminAnnouncementsProps> = ({ announcements, setAnnouncements }) => {
    // --- 状态管理 ---
    const [isModalOpen, setIsModalOpen] = useState(false);
    
    /** * 当前编辑的公告 ID
     * * 如果为 null，表示正在创建新公告
     */
    const [editingId, setEditingId] = useState<string | null>(null);
    
    // 表单状态
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [status, setStatus] = useState<'published' | 'draft'>('draft');
    
    /**
     * 打开模态框（新增或编辑）
     * @param {Announcement} [announcement] - 如果传入则为编辑模式，否则为新增模式
     */
    const handleOpenModal = (announcement?: Announcement) => {
        if (announcement) {
            // 编辑模式：回填数据
            setEditingId(announcement.id);
            setTitle(announcement.title);
            setContent(announcement.content);
            setStatus(announcement.status);
        } else {
            // 新增模式：重置表单
            setEditingId(null);
            setTitle('');
            setContent('');
            setStatus('draft');
        }
        setIsModalOpen(true);
    };
    
    /**
     * 保存公告（新增或更新）
     * * 自动生成 ID 和当前日期。
     */
    const handleSave = () => {
        if (!title || !content) return;
        
        if (editingId) {
            // 更新现有公告
            setAnnouncements(prev => prev.map(a =>
                a.id === editingId ? { ...a, title, content, status, date: new Date().toISOString().split('T')[0] } : a
            ));
        } else {
            // 创建新公告
            const newAnnouncement: Announcement = {
                id: Date.now().toString(),
                title,
                content,
                status,
                date: new Date().toISOString().split('T')[0]
            };
            setAnnouncements([newAnnouncement, ...announcements]);
        }
        setIsModalOpen(false);
    };
    
    /**
     * 删除公告
     * @param {string} id - 目标公告 ID
     */
    const handleDelete = (id: string) => {
        if (confirm('确定要删除这条公告吗？')) {
            setAnnouncements(prev => prev.filter(a => a.id !== id));
        }
    };
    
    return (
        <div className="p-8 max-w-7xl mx-auto h-full overflow-y-auto">
            {/* 顶部操作栏 */}
            <div className="flex justify-between items-center mb-8">
                <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                    <Megaphone className="text-primary" /> 公告管理
                </h2>
                <Button variant="primary" icon={<Plus size={16} />} onClick={() => handleOpenModal()}>
                    发布新公告
                </Button>
            </div>
            
            {/* 公告列表 */}
            <div className="space-y-4">
                {announcements.map(item => (
                    <Card key={item.id} className="hover:shadow-md transition-shadow">
                        <div className="flex justify-between items-start">
                            <div className="flex-1 pr-4">
                                <div className="flex items-center gap-3 mb-2">
                                    <h3 className="font-bold text-gray-800 text-lg">{item.title}</h3>
                                    <Tag color={item.status === 'published' ? 'green' : 'orange'}>
                                        {item.status === 'published' ? '已发布' : '草稿'}
                                    </Tag>
                                    <span className="text-sm text-gray-400">{item.date}</span>
                                </div>
                                <p className="text-gray-600 text-sm line-clamp-2">{item.content}</p>
                            </div>
                            <div className="flex gap-2 shrink-0">
                                <Button variant="text" onClick={() => handleOpenModal(item)}>
                                    <Edit size={16} className="text-gray-500 hover:text-primary" />
                                </Button>
                                <Button variant="text" onClick={() => handleDelete(item.id)}>
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
            
            {/* 编辑/新增模态框 */}
            <Modal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                title={editingId ? "编辑公告" : "发布新公告"}
                footer={
                    <>
                        <Button onClick={() => setIsModalOpen(false)}>取消</Button>
                        <Button variant="primary" onClick={handleSave}>保存</Button>
                    </>
                }
            >
                <div className="space-y-4">
                    <Input
                        label="公告标题"
                        placeholder="请输入标题"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                    />
                    <div className="flex flex-col gap-1">
                        <label className="text-sm text-gray-600">状态</label>
                        <select
                            className="px-3 py-2 bg-white border border-gray-300 rounded-md text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                            value={status}
                            onChange={(e) => setStatus(e.target.value as any)}
                        >
                            <option value="draft">存为草稿</option>
                            <option value="published">立即发布</option>
                        </select>
                    </div>
                    <div className="flex flex-col gap-1">
                        <label className="text-sm text-gray-600">内容</label>
                        <textarea
                            className="px-3 py-2 bg-white border border-gray-300 rounded-md text-sm focus:border-primary focus:ring-1 focus:ring-primary h-32 resize-none"
                            placeholder="请输入公告内容..."
                            value={content}
                            onChange={(e) => setContent(e.target.value)}
                        ></textarea>
                    </div>
                </div>
            </Modal>
        </div>
    );
};