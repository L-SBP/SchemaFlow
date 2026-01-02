/**
 * @file AdminAnnouncements.tsx
 * @module Pages/Administration/Announcement-Governance
 * @description 系统公告管理与发布中心。
 * 本模块作为 AutoDB 平台的“信息分发中枢”，负责协调管理员向全量用户推送系统变更、
 * 模型升级通知及数据库维护计划。
 * * * 核心管理逻辑：
 * 1. 状态生命周期: 支持“草稿 (Draft)”与“已发布 (Published)”两种生存状态的隔离与转换；
 * 2. 异步流编排: 针对后端 status 筛选限制，采用并发请求合并算法执行全量数据检索；
 * 3. 稳健的去重机制: 引入基于 Map 的唯一性审计，确保前端视图在多流合并时不产生 ID 冲突；
 * 4. 交互式审计: 集成统一的删除确认机制与原子化表单验证。
 * * * 对应需求点：
 * - Requirement 10.1: 系统级公告的发布与维护功能。
 * - Requirement 10.2: 支持富文本预览与状态切换。
 * * @author Wang Lirong (王利蓉)
 * @version 1.5.0
 * @date 2026-01-02
 */

import React, { useState, useEffect } from 'react';
import { Announcement } from '../types.ts';
import { Card, Button, Tag, Input, Modal, message, ConfirmDialog, Select } from '../components/UI.tsx';
import { Pagination } from '../components/Pagination.tsx';
import { Plus, Edit, Trash, Bell, Loader2 } from 'lucide-react';
import { announcementApi, CreateAnnouncementParams, UpdateAnnouncementParams } from '../api/announcement.ts';

/**
 * 分页配置常量
 * @constant PAGE_SIZE - 定义单页渲染的最大数据承载量，用于平衡网络载荷与首屏渲染耗时。
 */
const PAGE_SIZE = 10;

/**
 * @component AdminAnnouncements
 * @description
 * 采用 React 函数式组件构建。该页面为运维人员提供了一个集成的列表视图，
 * 通过分步式分页与模态框编辑，降低了对非技术运营人员的操作门槛。
 */
export const AdminAnnouncements: React.FC = () => {
    // --- 1. 数据集状态管理 (Data Sets) ---
    /** 存储当前视图缓存的公告实体阵列 */
    const [announcements, setAnnouncements] = useState<Announcement[]>([]);
    /** 局部加载锁：用于处理列表刷新及并发请求时的视觉反馈 */
    const [isLoading, setIsLoading] = useState(false);
    /** 异步保存锁：防止在提交表单时由于二次点击产生的网络幂等性问题 */
    const [isSaving, setIsSaving] = useState(false);
    /** 编辑模态框可见性开关 */
    const [isModalOpen, setIsModalOpen] = useState(false);

    // --- 2. 分页状态机 (Pagination Control) ---
    /** 当前激活的物理页码 */
    const [currentPage, setCurrentPage] = useState(1);
    /** 总记录计数：用于驱动分页器的内部逻辑（如省略号计算） */
    const [totalAnnouncements, setTotalAnnouncements] = useState(0);

    // --- 3. 事务上下文状态 (Transaction Context) ---
    /** 标识当前正在操作的公告 ID。若为 null 则表示处于“新公告创建”事务中 */
    const [editingId, setEditingId] = useState<number | null>(null);

    // --- 4. 表单响应式字段 (Form Fields) ---
    /** 公告标题缓存区 */
    const [title, setTitle] = useState('');
    /** 公告正文内容缓存区（支持多行输入） */
    const [content, setContent] = useState('');
    /** * 发布状态控制：
     * - published: 全量用户可见。
     * - draft: 仅管理员内部可见，作为暂存态存在。
     */
    const [status, setStatus] = useState<'published' | 'draft'>('draft');

    // --- 5. 安全风险确认状态 (Deletion Safeguard) ---
    /** 销毁确认弹窗的显示状态 */
    const [isDeleteConfirmOpen, setIsDeleteConfirmOpen] = useState(false);
    /** 物理删除的目标 ID 引用 */
    const [announcementToDelete, setAnnouncementToDelete] = useState<number | null>(null);

    /**
     * 核心逻辑：拉取与数据清洗 (Data Fetching & Cleaning)
     * @async @function fetchAnnouncements
     * @description
     * 这是一个典型的“合并请求”逻辑。由于后端单次接口仅支持单状态过滤，
     * 前端通过 Promise.all 实现并发拉取，并执行跨维度的去重与重排算法。
     */
    const fetchAnnouncements = async (page: number = currentPage) => {
        setIsLoading(true);
        try {
            /** * 步骤 A：并行触发草稿与发布公告的拉取。
             * 旨在确保管理员在同一看板内拥有全量审计视角。
             */
            const [publishedRes, draftRes] = await Promise.all([
                announcementApi.getList(page, PAGE_SIZE, 'published'),
                announcementApi.getList(page, PAGE_SIZE, 'draft')
            ]);

            /** * 步骤 B：执行前端数据聚合。
             * 1. Merging: 合并两组异步返回的 DTO 集合；
             * 2. Deduplication: 利用 Map 特性排除可能存在的重复 ID 记录；
             * 3. Sorting: 基于 created_at 执行严格的时间轴倒序排列。
             */
            const merged = [...publishedRes.items, ...draftRes.items];
            const uniqueById = Array.from(
                new Map(merged.map(a => [a.announcement_id, a])).values()
            ).sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

            setAnnouncements(uniqueById);
            
            /** 步骤 C：更新分页元数据 */
            setTotalAnnouncements(publishedRes.total + draftRes.total);
        } catch (error) {
            // 异常捕获：在此处可集成全局 Sentry 记录
            console.error("Failed to fetch announcements", error);
        } finally {
            // 释放视觉锁
            setIsLoading(false);
        }
    };

    /**
     * 效应钩子：组件挂载初始化
     */
    useEffect(() => {
        fetchAnnouncements();
    }, []);

    // --- 交互业务逻辑集 (User Interaction Logic) ---

    /**
     * 初始化模态框事务
     * @param {Announcement} [announcement] - 可选。若提供则进入编辑态，否则开启空白创建态。
     */
    const handleOpenModal = (announcement?: Announcement) => {
        if (announcement) {
            /** 场景：修正现有公告信息 */
            setEditingId(announcement.announcement_id);
            setTitle(announcement.title);
            setContent(announcement.content);
            setStatus(announcement.status === 'published' ? 'published' : 'draft');
        } else {
            /** 场景：撰写新公告 */
            setEditingId(null);
            setTitle('');
            setContent('');
            setStatus('draft');
        }
        setIsModalOpen(true);
    };

    /**
     * 提交物理持久化事务
     * @async @function handleSave
     * @description
     * 实现了公告实体的全量/增量保存逻辑。
     * 流程：校验 -> 分流 (Update/Create) -> 刷新 -> 关闭。
     */
    const handleSave = async () => {
        // 步骤 1：合法性初审（必填项拦截）
        if (!title || !content) return;

        setIsSaving(true);
        try {
            if (editingId) {
                /** 场景 A：更新现有资源的元数据 */
                const updateData: UpdateAnnouncementParams = { title, content, status };
                await announcementApi.update(editingId, updateData);
            } else {
                /** 场景 B：触发新资源的物理生成 */
                const createData: CreateAnnouncementParams = { title, content, status };
                await announcementApi.create(createData);
            }
            
            /** 步骤 2：数据最终一致性刷新 */
            await fetchAnnouncements(currentPage);
            /** 步骤 3：事务完结，清理交互上下文 */
            setIsModalOpen(false);
        } catch (error) {
            console.error("Failed to save announcement", error);
            message.error("保存失败，请重试");
        } finally {
            setIsSaving(false);
        }
    };

    /**
     * 发起资源销毁事务
     * @param {number} id - 待移除的资源主键
     */
    const handleDelete = async (id: number) => {
        setAnnouncementToDelete(id);
        setIsDeleteConfirmOpen(true);
    };

    /**
     * 确认并执行物理删除
     * @async @function confirmDelete
     * @description
     * 该操作属于不可逆风险行为。
     * 采用“乐观更新 (Optimistic UI Update)”策略，在后端反馈前先行调整本地视图，提升感知性能。
     */
    const confirmDelete = async () => {
        if (!announcementToDelete) return;

        try {
            await announcementApi.delete(announcementToDelete);
            
            /** 性能优化：无需重新拉取列表，直接从本地内存过滤掉已销毁项 */
            setAnnouncements(prev => prev.filter(a => a.announcement_id !== announcementToDelete));
            setTotalAnnouncements(prev => prev - 1);
            
            message.success("公告已删除");
        } catch (error) {
            console.error("Delete failed", error);
            message.error("删除失败");
        }
    };

    /**
     * 处理分页路由跳转
     * @param {number} page - 目标跳转页码
     */
    const handlePageChange = (page: number) => {
        setCurrentPage(page);
        fetchAnnouncements(page);
    };

    return (
        /** 主容器布局：采用 Flex-Col 结构，适配 100% 视口高度并强制隐藏多余溢出 */
        <div className="p-8 max-w-7xl mx-auto h-full flex flex-col overflow-hidden">
            
            {/* 步骤 1：头部控制区 (Action Bar)
                包含语义化标题、品牌图标及主发布入口。
            */}
            <div className="flex justify-between items-center mb-8 flex-shrink-0">
                <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-3">
                    <div className="p-2 bg-blue-100 text-blue-600 rounded-lg shrink-0">
                        <Bell size={20} />
                    </div>
                    公告治理中心
                </h2>
                <Button variant="primary" icon={<Plus size={16} />} onClick={() => handleOpenModal()}>
                    发布新公告
                </Button>
            </div>

            {/* 步骤 2：内容滚动展示区 (List View)
                使用了 flex-1 撑满剩余空间，内置 overflow-y-auto 独立滚动轴。
            */}
            <div className="flex-1 overflow-y-auto min-h-0 custom-scrollbar">
                {isLoading ? (
                    /** 加载骨架：采用居中 Loader 动画 */
                    <div className="flex justify-center items-center h-64">
                        <Loader2 className="animate-spin text-primary" size={32} />
                    </div>
                ) : (
                    <div className="space-y-4 pb-4">
                        {announcements.map(item => (
                            /** 公告卡片：集成阴影过渡与响应式内容布局 */
                            <Card key={item.announcement_id} className="hover:shadow-md transition-shadow">
                                <div className="flex justify-between items-start">
                                    <div className="flex-1 pr-4">
                                        {/* 公告元数据区：包含标题、状态标签及时间戳 */}
                                        <div className="flex items-center gap-3 mb-2">
                                            <h3 className="font-bold text-gray-800 text-lg">{item.title}</h3>
                                            {/* 语义化标签分发：绿色对应发布，橙色对应草稿 */}
                                            <Tag color={item.status === 'published' ? 'green' : 'orange'}>
                                                {item.status === 'published' ? '已发布' : '草稿'}
                                            </Tag>
                                            <span className="text-sm text-gray-400 font-mono">
                                                {new Date(item.created_at).toLocaleDateString()}
                                            </span>
                                        </div>
                                        {/* 核心内容预览：支持两行文本截断 (line-clamp-2) */}
                                        <p className="text-gray-600 text-sm line-clamp-2 leading-relaxed">{item.content}</p>
                                    </div>
                                    
                                    {/* 动作按钮群组：提供编辑与删除入口 */}
                                    <div className="flex gap-2 shrink-0">
                                        <Button variant="text" onClick={() => handleOpenModal(item)} title="编辑内容">
                                            <Edit size={16} className="text-gray-500 hover:text-primary transition-colors" />
                                        </Button>
                                        <Button variant="text" onClick={() => handleDelete(item.announcement_id)} title="注销公告">
                                            <Trash size={16} className="text-gray-500 hover:text-red-500 transition-colors" />
                                        </Button>
                                    </div>
                                </div>
                            </Card>
                        ))}
                        
                        {/* 场景兜底：空状态展示，采用虚线边框样式 */}
                        {announcements.length === 0 && (
                            <div className="text-center py-12 text-gray-500 bg-white rounded-lg border border-dashed border-gray-300">
                                <Bell size={32} className="mx-auto mb-2 opacity-20" />
                                暂无公告记录，请通过上方入口执行发布
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* 步骤 3：数据辅助控制区 (Pagination Area)
                固定在底部，确保在大屏幕或小屏下均具备稳定的物理锚点。
            */}
            {totalAnnouncements > 0 && (
                <div className="pagination-container border-t border-gray-100 mt-4 pt-4 flex-shrink-0">
                    <div className="pagination-wrapper">
                        <Pagination
                            current={currentPage}
                            total={totalAnnouncements}
                            pageSize={PAGE_SIZE}
                            onChange={handlePageChange}
                            showTotal={true}
                            // 响应式自适应：在小屏幕 (width < 640) 下自动切换至 Simple 渲染模式
                            simple={window.innerWidth < 640}
                        />
                    </div>
                </div>
            )}

            {/* 事务模块 A：编辑/新增表单模态框 */}
            <Modal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                title={editingId ? "修改现有公告" : "撰写新公告"}
                footer={
                    <div className="flex justify-end gap-3">
                        <Button onClick={() => setIsModalOpen(false)}>放弃更改</Button>
                        <Button variant="primary" onClick={handleSave} disabled={isSaving}>
                            {isSaving ? '正在同步至云端...' : '保存更改'}
                        </Button>
                    </div>
                }
            >
                <div className="space-y-5">
                    {/* 公告标题录入单元 */}
                    <Input
                        label="公告标题"
                        placeholder="请输入具有概括性的标题"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        required
                    />
                    
                    {/* 状态维度选择器 */}
                    <Select
                        label="发布策略状态"
                        className="w-full"
                        value={status}
                        onChange={(val) => setStatus(val as any)}
                        required
                        options={[
                            { value: 'draft', label: '存为草稿 (暂不对外可见)' },
                            { value: 'published', label: '立即发布 (同步全网用户)' }
                        ]}
                    />

                    {/* 正文录入单元：手写 textarea 样式以实现高度自适应 */}
                    <div className="flex flex-col gap-1.5">
                        <label className="text-sm font-medium text-gray-700">公告核心内容<span className="text-red-500 ml-1">*</span></label>
                        <textarea
                            className="px-3 py-2.5 bg-white border border-gray-300 rounded-lg text-sm focus:border-primary focus:ring-2 focus:ring-blue-100 h-40 resize-none outline-none transition-all shadow-sm placeholder:text-gray-300"
                            placeholder="请详细描述通知事项、操作指引或维护周期..."
                            value={content}
                            onChange={(e) => setContent(e.target.value)}
                        ></textarea>
                        <p className="text-[11px] text-gray-400 italic">内容将以纯文本形式渲染至客户端 Dashboard。</p>
                    </div>
                </div>
            </Modal>

            {/* 事务模块 B：物理注销确认对话框 (Confirm Dialog)
                严格遵循 Usability-2 安全规范，对危险操作执行二次阻断提示。
            */}
            <ConfirmDialog
                isOpen={isDeleteConfirmOpen}
                onClose={() => setIsDeleteConfirmOpen(false)}
                onConfirm={confirmDelete}
                title="高危：资源注销确认"
                message="确定要彻底移除这条公告吗？注销后，所有关联用户的通知流将同步中断且不可回溯。"
                confirmText="立即执行删除"
                cancelText="放弃并返回"
                isDangerous={true}
                showWarningIcon={true}
            />
        </div>
    );
};