/**
 * @file AdminPanel.tsx
 * @module Pages/Administration/User-Management
 * @description 系统管理后台 - 全量用户治理与资源配额中心。
 * 本模块作为 AutoDB 平台的运维核心，负责处理用户生命周期管理及物理资源配额的分发。
 * * * 核心管理逻辑：
 * 1. 资源隔离与配额 (SF11): 动态调整各用户可创建的数据库实例上限，防止单用户过度占用物理集群资源；
 * 2. 账号合规控制 (Security-4): 实现封禁/解封流，集成违规原因审计追踪，确保管理操作可追溯；
 * 3. 智能检索引擎: 支持基于内存过滤与服务端分页的混合检索策略；
 * 4. 数据协议适配: 通过 mapToUser 适配器模式，实现管理端 DTO 与通用用户模型的解耦。
 * * * 对应需求点：
 * - Requirement 11.1: 管理员可动态调整用户数据库创建限额。
 * - Requirement 11.2: 支持用户状态的强制干预（正常/异常/封禁）。
 * * @author Wang Lirong (王利蓉)
 * @version 2.2.0
 * @date 2026-01-02
 */

import React, { useState, useEffect } from 'react';
import { User, UserRole, UserStatus, AdminUserListItem } from '../types.ts';
import { Card, Button, Tag, Modal, Input, message, Select } from '../components/UI.tsx';
import { Search, Ban, CheckCircle, Users, Eye, Database, Edit3, Loader2, Filter, AlertTriangle } from 'lucide-react';
import { adminApi } from '../api/admin.ts';

/**
 * 管理面板组件属性定义
 * @interface AdminPanelProps
 * @property {Function} onViewUser - 当管理员需要调取特定用户全维画像时的路由/弹窗回调。
 */
interface AdminPanelProps {
    onViewUser: (user: User) => void;
}

/**
 * @component AdminPanel
 * @description
 * 采用 React 函数式组件构建。该页面集成了全量用户的状态监控视图。
 * 内部状态机驱动复杂的业务弹窗流，确保在进行高危操作（如账号封禁）时具备强制性的二次确认逻辑。
 */
export const AdminPanel: React.FC<AdminPanelProps> = ({ onViewUser }) => {
    // --- 核心数据集状态 (Data States) ---
    /** 存储当前分页下的用户列表快照 */
    const [users, setUsers] = useState<AdminUserListItem[]>([]);
    /** 页面级全局加载锁 */
    const [isLoading, setIsLoading] = useState(false);

    // --- 过滤、搜索与分页控制 (Context States) ---
    /** 检索关键字缓冲区 */
    const [searchTerm, setSearchTerm] = useState('');
    /** 状态漏斗：支持全量、正常、挂起、封禁四维度过滤 */
    const [statusFilter, setStatusFilter] = useState<'all' | 'normal' | 'suspended' | 'banned'>('all');
    /** 分页器：当前激活页码 */
    const [page, setPage] = useState(1);
    /** 后端符合过滤条件的总条目数，用于驱动分页 UI 计算 */
    const [total, setTotal] = useState(0);
    /** 业务规范：固定单页容量为 10 条 */
    const pageSize = 10;

    // --- 资源配额治理状态 (Quota Management) ---
    /** 当前正在进行配额编辑的目标用户引用 */
    const [editingQuotaUser, setEditingQuotaUser] = useState<AdminUserListItem | null>(null);
    /** 配额输入框实时值 */
    const [newQuota, setNewQuota] = useState('');
    /** 针对配额输入的即时校验错误信息 */
    const [quotaError, setQuotaError] = useState('');
    /** 提交配额变更时的异步状态锁 */
    const [isSavingQuota, setIsSavingQuota] = useState(false);

    // --- 账号安全干预状态 (Status & Risk Control) ---
    /** 封禁/解封事务弹窗的显隐状态 */
    const [isStatusModalOpen, setIsStatusModalOpen] = useState(false);
    /** 状态变更事务的目标用户快照 */
    const [statusTargetUser, setStatusTargetUser] = useState<AdminUserListItem | null>(null);
    /** 目标操作倾向：normal 代表恢复正常/解封，banned 代表强制封禁 */
    const [targetStatusAction, setTargetStatusAction] = useState<'normal' | 'banned'>('normal'); 
    /** 审计理由字段：记录操作原因以备日后安全审计 */
    const [statusReason, setStatusReason] = useState('');
    /** 状态变更请求的异步处理锁 */
    const [isSavingStatus, setIsSavingStatus] = useState(false);

    /**
     * 服务端数据拉取核心逻辑
     * @async @function fetchUsers
     * @description
     * 对应 SF11 基础数据获取。执行以下流程：
     * 1. 开启全局加载状态；
     * 2. 调用 adminApi.getUsers 执行服务端分页检索；
     * 3. 对返回结果执行 ID 级升序排列（确保列表稳定性）；
     * 4. 更新本地状态并刷新总数计数。
     */
    const fetchUsers = async () => {
        setIsLoading(true);
        try {
            // 发起异步请求，透传分页与搜索权重参数
            const res = await adminApi.getUsers(page, pageSize, searchTerm || undefined, statusFilter);

            /**
             * 排序算法：保证 UI 层的展示一致性。
             * 虽然后端通常已处理排序，但在前端执行显式校验可提升防御性编程水平。
             */
            const sortedItems = res.items.sort((a, b) => a.user_id - b.user_id);

            setUsers(sortedItems);
            setTotal(res.total);
        } catch (error) {
            // 异常路径：记录日志并可通过全局错误拦截器抛出 UI 提示
            console.error("Fetch users failed", error);
        } finally {
            // 释放加载锁，恢复 UI 交互
            setIsLoading(false);
        }
    };

    /**
     * 效应钩子：依赖追踪与自动同步。
     * 当分页码或状态过滤器发生偏移时，自动触发重测。
     */
    useEffect(() => {
        fetchUsers();
    }, [page, statusFilter]);

    /**
     * 搜索交互处理
     * @param {React.KeyboardEvent} e - 键盘事件对象
     */
    const handleSearchKeyDown = (e: React.KeyboardEvent) => {
        // 监听 Enter 键，执行非实时搜索以降低 API 峰值负载
        if (e.key === 'Enter') {
            setPage(1); // 搜索条件变化时，强制重置至第一页
            fetchUsers();
        }
    };

    // --- 业务事务处理集 (Business Transaction Handlers) ---

    /**
     * 开启账户状态变更事务
     * @param {AdminUserListItem} user - 目标用户
     * @param {'normal' | 'banned'} action - 预执行的动作方向
     */
    const handleOpenStatusModal = (user: AdminUserListItem, action: 'normal' | 'banned') => {
        setStatusTargetUser(user);
        setTargetStatusAction(action);
        setStatusReason(''); // 事务初始化：强制清空审计原因缓冲区
        setIsStatusModalOpen(true);
    };

    /**
     * 核心事务：提交账户状态修改
     * @async @function handleConfirmStatusChange
     * @description 
     * 该函数实现了账号治理的完整闭环。包含：
     * 1. 输入完整性校验（审计原因必填）；
     * 2. 异步 API 调用；
     * 3. 乐观 UI 更新（Optimistic Update），在请求成功后立即同步本地列表状态；
     * 4. 事务资源清理。
     */
    const handleConfirmStatusChange = async () => {
        if (!statusTargetUser) return;

        // 根据动作方向计算语义化描述
        const targetStatus = targetStatusAction;
        const actionText = targetStatus === 'normal' ?
            (statusTargetUser.status === 'banned' ? '解封' : '恢复正常') :
            '封禁';

        /**
         * 审计合规校验：
         * 任何对账户状态的干预操作必须提供原因说明。
         */
        if (!statusReason.trim()) {
            message.error(`请输入${actionText}原因`);
            return;
        }

        setIsSavingStatus(true);
        try {
            // 调用管理端专用更新接口
            await adminApi.updateUserStatus(statusTargetUser.user_id, {
                status: targetStatus,
                reason: statusReason
            });
            
            // 业务层反馈
            message.success(`用户已${actionText}`);

            /**
             * 乐观 UI 同步：
             * 无需重新拉取整个列表，仅对修改项执行局部深拷贝更新。
             */
            setUsers(prev => prev.map(u => u.user_id === statusTargetUser.user_id ? { ...u, status: targetStatus } : u));

            // 事务完成：销毁所有临时上下文
            setIsStatusModalOpen(false);
            setStatusTargetUser(null);
        } catch (error) {
            console.error("Status update failed", error);
        } finally {
            setIsSavingStatus(false);
        }
    };

    /**
     * 开启配额编辑事务
     * @param {AdminUserListItem} user - 目标用户
     */
    const handleOpenQuotaModal = (user: AdminUserListItem) => {
        setEditingQuotaUser(user);
        setNewQuota(user.max_databases.toString());
        setQuotaError(''); // 重置错误信号
    };

    /**
     * 核心事务：保存配额变更
     * @async @function handleSaveQuota
     * @description
     * 实现了对物理资源上限的强力管控。
     * 包含输入合法性判定（非负整数）及系统级峰值限流校验（Max: 1000）。
     */
    const handleSaveQuota = async () => {
        if (!editingQuotaUser) return;
        const quota = parseInt(newQuota);

        // 数据合法性预检
        if (isNaN(quota) || quota < 0) {
            setQuotaError('额度不能为负数');
            return;
        }
        // 系统级策略保护：单用户最大数据库数不得超过 1000
        if (quota > 1000) {
            setQuotaError('额度值超出系统上限 (1000)');
            return;
        }

        setIsSavingQuota(true);
        try {
            // 执行配额写入操作
            await adminApi.updateUserQuota(editingQuotaUser.user_id, quota);
            message.success('额度更新成功');
            
            // 同步本地状态，刷新“项目数/额度”列的展示
            setUsers(prev => prev.map(u => u.user_id === editingQuotaUser.user_id ? { ...u, max_databases: quota } : u));
            setEditingQuotaUser(null); // 事务关闭
        } catch (error) {
            console.error("Quota update failed", error);
        } finally {
            setIsSavingQuota(false);
        }
    };

    /**
     * 数据模型转换器 (Adapter Pattern)
     * @function mapToUser
     * @description
     * 将管理端特有的 AdminUserListItem 转换为应用通用的 User 对象定义。
     * 解决了管理侧接口字段（user_id）与用户侧标准字段（id）的不一致性问题。
     * @param {AdminUserListItem} item - 原始后端 DTO
     * @returns {User} 标准化 User 对象
     */
    const mapToUser = (item: AdminUserListItem): User => ({
        id: item.user_id.toString(),
        username: item.username,
        email: item.email,
        role: UserRole.USER, // 管理员视角下默认作为普通用户处理
        status: item.status === 'normal' ? UserStatus.NORMAL : UserStatus.BANNED,
        // 时间戳本地化处理：针对从未登录的用户进行语义化兜底
        lastLogin: item.last_login_at ? new Date(item.last_login_at).toLocaleString() : '从未登录',
        projectQuota: item.max_databases
    });

    /**
     * 渲染视图层
     */
    return (
        <div className="p-8 max-w-7xl mx-auto h-full overflow-y-auto">
            
            {/* 步骤 1：顶部状态区 - 包含标题及响应式检索组件 */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-3">
                    <div className="p-2 bg-blue-100 text-blue-600 rounded-lg shrink-0">
                        <Users size={20} />
                    </div>
                    用户治理中心
                </h2>

                <div className="flex gap-2 w-full md:w-auto">
                    {/* 过滤器组：状态筛选下行菜单 */}
                    <div className="flex items-center gap-2 bg-white px-3 rounded-lg border border-gray-300 shadow-sm h-[38px] hover:border-gray-400 transition-colors">
                        <Filter size={16} className="text-gray-400" />
                        <Select
                            variant="minimal"
                            className="min-w-[90px]"
                            value={statusFilter}
                            onChange={(val) => { setStatusFilter(val as any); setPage(1); }}
                            options={[
                                { value: 'all', label: '全部状态' },
                                { value: 'normal', label: '正常' },
                                { value: 'suspended', label: '异常' },
                                { value: 'banned', label: '已封禁' }
                            ]}
                        />
                    </div>

                    {/* 搜索控制：全局关键字搜索 */}
                    <div className="relative flex-1 md:w-64">
                        <input
                            type="text"
                            placeholder="搜索用户名/邮箱 (回车)..."
                            className="w-full h-[38px] pl-10 pr-4 border border-gray-300 rounded-lg focus:ring-primary focus:border-primary text-sm"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            onKeyDown={handleSearchKeyDown}
                        />
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 cursor-pointer" size={16} onClick={() => { setPage(1); fetchUsers(); }} />
                    </div>
                </div>
            </div>

            {/* 步骤 2：数据展示区 - 响应式表格设计 */}
            <Card className="overflow-hidden p-0 min-h-[400px]">
                {isLoading ? (
                    /** 加载态：采用 Loader 动画替代空列表 */
                    <div className="flex justify-center items-center h-64">
                        <Loader2 className="animate-spin text-primary" size={32} />
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm min-w-[1000px]">
                            {/* 表头定义：声明各列业务语义 */}
                            <thead className="bg-gray-50 border-b border-gray-200">
                                <tr>
                                    <th className="px-6 py-4 font-medium text-gray-600 whitespace-nowrap">ID</th>
                                    <th className="px-6 py-4 font-medium text-gray-600 whitespace-nowrap">用户名</th>
                                    <th className="px-6 py-4 font-medium text-gray-600 whitespace-nowrap">邮箱</th>
                                    <th className="px-6 py-4 font-medium text-gray-600 whitespace-nowrap">实时状态</th>
                                    <th className="px-6 py-4 font-medium text-gray-600 whitespace-nowrap">项目数/额度</th>
                                    <th className="px-6 py-4 font-medium text-gray-600 whitespace-nowrap">最近访问</th>
                                    <th className="px-6 py-4 font-medium text-gray-600 text-right whitespace-nowrap">治理操作</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                {users.map(user => (
                                    <tr key={user.user_id} className="hover:bg-gray-50/50 transition-colors">
                                        <td className="px-6 py-4 text-gray-500 font-mono whitespace-nowrap">{user.user_id}</td>
                                        <td className="px-6 py-4 font-medium text-gray-800 whitespace-nowrap">{user.username}</td>
                                        <td className="px-6 py-4 text-gray-600 whitespace-nowrap">{user.email}</td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            {/* 状态标签：通过色彩语义强化风险识别 */}
                                            <Tag color={user.status === 'normal' ? 'green' : user.status === 'banned' ? 'red' : 'orange'}>
                                                {user.status === 'normal' ? '正常' : user.status === 'banned' ? '封禁' : '异常活跃'}
                                            </Tag>
                                        </td>
                                        
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            {/* 额度交互区：点击触发向导修改 */}
                                            <div
                                                className="flex items-center gap-2 group cursor-pointer"
                                                onClick={() => handleOpenQuotaModal(user)}
                                                title="点击调整资源上限"
                                            >
                                                <span className="font-mono text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
                                                    {user.project_count} / {user.max_databases}
                                                </span>
                                                <Edit3 size={12} className="text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                                            </div>
                                        </td>

                                        <td className="px-6 py-4 text-gray-500 whitespace-nowrap">
                                            {user.last_login_at ? new Date(user.last_login_at).toLocaleString() : '-'}
                                        </td>

                                        <td className="px-6 py-4 text-right whitespace-nowrap">
                                            <div className="flex justify-end items-center gap-2">
                                                {/* 动作 A：查看全维视图 */}
                                                <Button
                                                    variant="text"
                                                    className="h-8 px-2 text-gray-500 hover:text-primary"
                                                    onClick={() => onViewUser(mapToUser(user))}
                                                    title="查看全量档案"
                                                >
                                                    <Eye size={16} />
                                                </Button>

                                                {/* 策略逻辑：针对不同状态渲染差异化的干预按钮 */}
                                                {user.status === 'normal' && (
                                                    <Button
                                                        variant="danger"
                                                        className="h-8 px-3 text-xs"
                                                        onClick={() => handleOpenStatusModal(user, 'banned')}
                                                        icon={<Ban size={12} />}
                                                    >
                                                        强制封禁
                                                    </Button>
                                                )}

                                                {user.status === 'banned' && (
                                                    <Button
                                                        variant="default"
                                                        className="h-8 px-3 text-xs border-green-200 text-green-600 hover:bg-green-50"
                                                        onClick={() => handleOpenStatusModal(user, 'normal')}
                                                        icon={<CheckCircle size={12} />}
                                                    >
                                                        立即解封
                                                    </Button>
                                                )}

                                                {user.status === 'suspended' && (
                                                    <div className="flex gap-1">
                                                        <Button
                                                            variant="default"
                                                            className="h-8 px-3 text-xs border-green-200 text-green-600 hover:bg-green-50"
                                                            onClick={() => handleOpenStatusModal(user, 'normal')}
                                                            icon={<CheckCircle size={12} />}
                                                        >
                                                            恢复
                                                        </Button>
                                                        <Button
                                                            variant="danger"
                                                            className="h-8 px-3 text-xs"
                                                            onClick={() => handleOpenStatusModal(user, 'banned')}
                                                            icon={<Ban size={12} />}
                                                        >
                                                            封禁
                                                        </Button>
                                                    </div>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                                {/* 空态兜底 */}
                                {users.length === 0 && !isLoading && (
                                    <tr>
                                        <td colSpan={7} className="text-center py-12 text-gray-500">
                                            <div className="flex flex-col items-center">
                                                <AlertTriangle size={32} className="text-gray-300 mb-2" />
                                                未检索到符合条件的租户记录
                                            </div>
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* 步骤 3：数据辅助层 - 分页控制 */}
                {total > 0 && (
                    <div className="flex justify-between items-center px-6 py-4 border-t border-gray-100 bg-gray-50/50">
                        <span className="text-xs text-gray-500 font-medium">
                            数据体量：总计 {total} 项，分步浏览中 (Page: {page})
                        </span>
                        <div className="flex gap-2">
                            <Button variant="default" className="h-8 px-3 text-xs" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>上一页</Button>
                            <Button variant="default" className="h-8 px-3 text-xs" disabled={page * pageSize >= total} onClick={() => setPage(p => p + 1)}>下一页</Button>
                        </div>
                    </div>
                )}
            </Card>

            {/* 事务模块 A：配额调整对话框 */}
            <Modal
                isOpen={!!editingQuotaUser}
                onClose={() => setEditingQuotaUser(null)}
                title="物理资源限制参数调整"
                maxWidth="max-w-sm"
                footer={
                    <div className="flex justify-end gap-2">
                        <Button onClick={() => setEditingQuotaUser(null)}>取消</Button>
                        <Button variant="primary" onClick={handleSaveQuota} disabled={isSavingQuota}>
                            {isSavingQuota ? '正在同步云端...' : '更新配置'}
                        </Button>
                    </div>
                }
            >
                <div className="space-y-4">
                    <div className="bg-blue-50 p-3 rounded-lg flex items-start gap-3 border border-blue-100">
                        <Database className="text-primary shrink-0 mt-0.5" size={18} />
                        <div className="text-xs text-blue-900 leading-relaxed">
                            <p>正在调整租户 <strong>{editingQuotaUser?.username}</strong> 的资源隔离配额。</p>
                            <p className="mt-1 opacity-70">变更将实时影响该用户的多智能体部署能力。</p>
                        </div>
                    </div>

                    <div>
                        <Input
                            label="最大项目允许数 (Max Databases)"
                            type="number"
                            value={newQuota}
                            onChange={(e) => setNewQuota(e.target.value)}
                            placeholder="请输入配额整数"
                            min={0}
                            required
                        />
                        {quotaError && <p className="text-red-500 text-[11px] mt-1 font-medium">{quotaError}</p>}
                    </div>
                </div>
            </Modal>

            {/* 事务模块 B：账户干预确认对话框 (Security Critical) */}
            <Modal
                isOpen={isStatusModalOpen}
                onClose={() => setIsStatusModalOpen(false)}
                title={
                    targetStatusAction === 'normal' ?
                        (statusTargetUser?.status === 'banned' ? '撤销账户封禁' : '恢复正常服务') :
                        '执行账户封禁审计'
                }
                maxWidth="max-w-md"
                footer={
                    <div className="flex justify-end gap-2">
                        <Button onClick={() => setIsStatusModalOpen(false)}>放弃操作</Button>
                        <Button
                            variant={targetStatusAction === 'banned' ? 'danger' : 'primary'}
                            onClick={handleConfirmStatusChange}
                            disabled={isSavingStatus}
                        >
                            {isSavingStatus ? '正在下发指令...' : (
                                targetStatusAction === 'normal' ?
                                    (statusTargetUser?.status === 'banned' ? '确认撤销' : '确认恢复') :
                                    '立即执行封禁'
                            )}
                        </Button>
                    </div>
                }
            >
                <div className="space-y-4">
                    {/* 风险告知面板 */}
                    <div className={`p-4 rounded-lg flex items-start gap-3 border ${targetStatusAction === 'banned' ? 'bg-red-50 border-red-100 text-red-800' :
                        statusTargetUser?.status === 'banned' ? 'bg-green-50 border-green-100 text-green-800' :
                            'bg-blue-50 border-blue-100 text-blue-800'
                        }`}>
                        <AlertTriangle size={18} className="mt-0.5 shrink-0" />
                        <div className="text-sm">
                            <p className="font-bold mb-1">
                                {targetStatusAction === 'banned' ? '安全红线警示' :
                                    statusTargetUser?.status === 'banned' ? '服务恢复确认' :
                                        '状态正常化处理'}
                            </p>
                            <div className="opacity-90 leading-relaxed text-xs">
                                您正在对租户 <strong>{statusTargetUser?.username}</strong> 执行
                                账号状态强制干预。
                                {targetStatusAction === 'banned' ? 
                                    '封禁后，该用户的所有活跃 Agent 任务将立即挂起，API 访问令牌将永久失效。' :
                                    '操作后，用户将重新获得系统登录及 Agent 协作权限。'}
                            </div>
                        </div>
                    </div>

                    {/* 强制审计原因录入 */}
                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-gray-700 flex justify-between">
                            <span>干预原因记录 (Audit Reason)</span>
                            <span className="text-red-500 font-normal">必填项</span>
                        </label>
                        <textarea
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all min-h-[100px] resize-none placeholder:text-gray-300"
                            placeholder={
                                targetStatusAction === 'banned' ? "请详细描述违规证据或封禁理由..." :
                                    "请输入恢复服务的原因（如：误判处理、风险解除等）..."
                            }
                            value={statusReason}
                            onChange={(e) => setStatusReason(e.target.value)}
                        />
                        <p className="text-[10px] text-gray-400 italic">该记录将持久化至系统审计日志系统。</p>
                    </div>
                </div>
            </Modal>
        </div>
    );
};