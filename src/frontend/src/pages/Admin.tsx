import React, { useState, useEffect } from 'react';
import { User, UserRole, UserStatus, AdminUserListItem } from '../types.ts';
import { Card, Button, Tag, Modal, Input, message, Select } from '../components/UI.tsx';
import { Pagination } from '../components/Pagination.tsx';
import { Search, Ban, CheckCircle, Users, Eye, Database, Edit3, Loader2, Filter, AlertTriangle } from 'lucide-react';
import { adminApi } from '../api/admin.ts';

interface AdminPanelProps {
    onViewUser: (user: User) => void;
}

/**
 * 系统管理后台 - 用户管理面板
 * * 对接真实 API (GET /users, PATCH /status, PATCH /quota)
 */
export const AdminPanel: React.FC<AdminPanelProps> = ({ onViewUser }) => {
    // --- 状态管理 ---
    const [users, setUsers] = useState<AdminUserListItem[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    // 过滤与分页
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState<'all' | 'normal' | 'suspended' | 'banned'>('all');
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0);
    const pageSize = 10;

    // 配额编辑状态
    const [editingQuotaUser, setEditingQuotaUser] = useState<AdminUserListItem | null>(null);
    const [newQuota, setNewQuota] = useState('');
    const [quotaError, setQuotaError] = useState('');
    const [isSavingQuota, setIsSavingQuota] = useState(false);

    // 状态修改 (封禁/解封) 弹窗状态
    const [isStatusModalOpen, setIsStatusModalOpen] = useState(false);
    const [statusTargetUser, setStatusTargetUser] = useState<AdminUserListItem | null>(null);
    const [targetStatusAction, setTargetStatusAction] = useState<'normal' | 'banned'>('normal'); // 目标状态
    const [statusReason, setStatusReason] = useState('');
    const [isSavingStatus, setIsSavingStatus] = useState(false);

    // --- 数据获取 ---
    const fetchUsers = async () => {
        setIsLoading(true);
        try {
            const res = await adminApi.getUsers(page, pageSize, searchTerm || undefined, statusFilter);

            // 需求：用户列表按 id 升序排列
            const sortedItems = res.items.sort((a, b) => a.user_id - b.user_id);

            setUsers(sortedItems);
            setTotal(res.total);
        } catch (error) {
            console.error("Fetch users failed", error);
        } finally {
            setIsLoading(false);
        }
    };

    // 监听筛选条件变化
    useEffect(() => {
        fetchUsers();
    }, [page, statusFilter]);

    const handleSearchKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            setPage(1);
            fetchUsers();
        }
    };

    // --- 业务逻辑处理 ---

    /**
     * 打开状态修改弹窗
     */
    const handleOpenStatusModal = (user: AdminUserListItem, action: 'normal' | 'banned') => {
        setStatusTargetUser(user);
        setTargetStatusAction(action);
        setStatusReason(''); // 重置原因输入
        setIsStatusModalOpen(true);
    };

    /**
     * 确认提交状态修改 (封禁/解封/恢复正常)
     */
    const handleConfirmStatusChange = async () => {
        if (!statusTargetUser) return;

        const targetStatus = targetStatusAction;
        const actionText = targetStatus === 'normal' ?
            (statusTargetUser.status === 'banned' ? '解封' : '恢复正常') :
            '封禁';

        // 简单的必填校验
        if (!statusReason.trim()) {
            message.error(`请输入${actionText}原因`);
            return;
        }

        setIsSavingStatus(true);
        try {
            await adminApi.updateUserStatus(statusTargetUser.user_id, {
                status: targetStatus,
                reason: statusReason
            });
            message.success(`用户已${actionText}`);

            // 乐观更新 UI
            setUsers(prev => prev.map(u => u.user_id === statusTargetUser.user_id ? { ...u, status: targetStatus } : u));

            // 关闭弹窗
            setIsStatusModalOpen(false);
            setStatusTargetUser(null);
        } catch (error) {
            console.error(error);
        } finally {
            setIsSavingStatus(false);
        }
    };

    /**
     * 打开配额编辑
     */
    const handleOpenQuotaModal = (user: AdminUserListItem) => {
        setEditingQuotaUser(user);
        setNewQuota(user.max_databases.toString());
        setQuotaError('');
    };

    /**
     * 保存配额
     */
    const handleSaveQuota = async () => {
        if (!editingQuotaUser) return;
        const quota = parseInt(newQuota);

        if (isNaN(quota) || quota < 0) {
            setQuotaError('额度不能为负数');
            return;
        }
        if (quota > 1000) {
            setQuotaError('额度值超出系统上限 (1000)');
            return;
        }

        setIsSavingQuota(true);
        try {
            await adminApi.updateUserQuota(editingQuotaUser.user_id, quota);
            message.success('额度更新成功');
            setUsers(prev => prev.map(u => u.user_id === editingQuotaUser.user_id ? { ...u, max_databases: quota } : u));
            setEditingQuotaUser(null);
        } catch (error) {
            console.error(error);
        } finally {
            setIsSavingQuota(false);
        }
    };

    // 辅助：将 AdminUserListItem 转换为 User 对象以适配 UserProfile 组件
    const mapToUser = (item: AdminUserListItem): User => ({
        id: item.user_id.toString(),
        username: item.username,
        email: item.email,
        role: UserRole.USER, // 列表默认视为普通用户，详情页可细化
        status: item.status === 'normal' ? UserStatus.NORMAL : UserStatus.BANNED,
        lastLogin: item.last_login_at ? new Date(item.last_login_at).toLocaleString() : '从未登录',
        projectQuota: item.max_databases
    });

    return (
        <div className="p-8 max-w-7xl mx-auto h-full overflow-y-auto">
            {/* 顶部标题与操作栏 */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-3">
                    <div className="p-2 bg-blue-100 text-blue-600 rounded-lg shrink-0">
                        <Users size={20} />
                    </div>
                    用户管理
                </h2>

                <div className="flex gap-2 w-full md:w-auto">
                    {/* 状态筛选 */}
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

                    {/* 搜索框 */}
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

            {/* 用户列表表格 */}
            <Card className="overflow-hidden p-0 min-h-[400px]">
                {isLoading ? (
                    <div className="flex justify-center items-center h-64">
                        <Loader2 className="animate-spin text-primary" size={32} />
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm min-w-[1000px]">
                            <thead className="bg-gray-50 border-b border-gray-200">
                                <tr>
                                    <th className="px-6 py-4 font-medium text-gray-600 whitespace-nowrap">ID</th>
                                    <th className="px-6 py-4 font-medium text-gray-600 whitespace-nowrap">用户名</th>
                                    <th className="px-6 py-4 font-medium text-gray-600 whitespace-nowrap">邮箱</th>
                                    <th className="px-6 py-4 font-medium text-gray-600 whitespace-nowrap">状态</th>
                                    <th className="px-6 py-4 font-medium text-gray-600 whitespace-nowrap">项目数/额度</th>
                                    <th className="px-6 py-4 font-medium text-gray-600 whitespace-nowrap">最后登录</th>
                                    <th className="px-6 py-4 font-medium text-gray-600 text-right whitespace-nowrap">操作</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                {users.map(user => (
                                    <tr key={user.user_id} className="hover:bg-gray-50/50">
                                        <td className="px-6 py-4 text-gray-500 font-mono whitespace-nowrap">{user.user_id}</td>
                                        <td className="px-6 py-4 font-medium text-gray-800 whitespace-nowrap">{user.username}</td>
                                        <td className="px-6 py-4 text-gray-600 whitespace-nowrap">{user.email}</td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <Tag color={user.status === 'normal' ? 'green' : user.status === 'banned' ? 'red' : 'orange'}>
                                                {user.status === 'normal' ? '正常' : user.status === 'banned' ? '封禁' : '异常'}
                                            </Tag>
                                        </td>
                                        {/* 额度列 */}
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div
                                                className="flex items-center gap-2 group cursor-pointer"
                                                onClick={() => handleOpenQuotaModal(user)}
                                                title="点击修改配额"
                                            >
                                                <span className="font-mono">{user.project_count} / {user.max_databases}</span>
                                                <Edit3 size={12} className="text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-gray-500 whitespace-nowrap">
                                            {user.last_login_at ? new Date(user.last_login_at).toLocaleString() : '-'}
                                        </td>
                                        <td className="px-6 py-4 text-right whitespace-nowrap">
                                            <div className="flex justify-end items-center gap-2">
                                                <Button
                                                    variant="text"
                                                    className="h-8 px-2 text-gray-500 hover:text-primary"
                                                    onClick={() => onViewUser(mapToUser(user))}
                                                    title="查看详情"
                                                >
                                                    <Eye size={16} />
                                                </Button>

                                                {/* 正常用户：显示封禁按钮 */}
                                                {user.status === 'normal' && (
                                                    <Button
                                                        variant="danger"
                                                        className="h-8 px-3 text-xs"
                                                        onClick={() => handleOpenStatusModal(user, 'banned')}
                                                        icon={<Ban size={12} />}
                                                    >
                                                        封禁
                                                    </Button>
                                                )}

                                                {/* 已封禁用户：显示解封按钮 */}
                                                {user.status === 'banned' && (
                                                    <Button
                                                        variant="default"
                                                        className="h-8 px-3 text-xs border-green-200 text-green-600 hover:bg-green-50"
                                                        onClick={() => handleOpenStatusModal(user, 'normal')}
                                                        icon={<CheckCircle size={12} />}
                                                    >
                                                        解封
                                                    </Button>
                                                )}

                                                {/* 异常用户：显示恢复和封禁两个按钮 */}
                                                {user.status === 'suspended' && (
                                                    <>
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
                                                    </>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                                {users.length === 0 && (
                                    <tr>
                                        <td colSpan={7} className="text-center py-12 text-gray-500">未找到匹配的用户</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* 分页器 */}
                {total > 0 && (
                    <div className="border-t border-gray-100 bg-gray-50/50">
                        <Pagination
                            current={page}
                            total={total}
                            pageSize={pageSize}
                            onChange={setPage}
                            showTotal={true}
                        />
                    </div>
                )}
            </Card>

            {/* 配额修改模态框 */}
            <Modal
                isOpen={!!editingQuotaUser}
                onClose={() => setEditingQuotaUser(null)}
                title="修改用户数据库额度"
                maxWidth="max-w-sm"
                footer={
                    <>
                        <Button onClick={() => setEditingQuotaUser(null)}>取消</Button>
                        <Button variant="primary" onClick={handleSaveQuota} disabled={isSavingQuota}>
                            {isSavingQuota ? '保存中...' : '保存更改'}
                        </Button>
                    </>
                }
            >
                <div className="space-y-4">
                    <div className="bg-blue-50 p-3 rounded-lg flex items-start gap-3">
                        <Database className="text-primary shrink-0 mt-0.5" size={18} />
                        <div className="text-sm text-blue-900">
                            <p>正在修改用户 <strong>{editingQuotaUser?.username}</strong> 的最大项目创建数。</p>
                        </div>
                    </div>

                    <div>
                        <Input
                            label="新额度上限"
                            type="number"
                            value={newQuota}
                            onChange={(e) => setNewQuota(e.target.value)}
                            placeholder="请输入整数"
                            min={0}
                            required
                        />
                        {quotaError && <p className="text-red-500 text-xs mt-1">{quotaError}</p>}
                    </div>
                </div>
            </Modal>

            {/* 状态修改 (封禁/解封) 模态框 */}
            <Modal
                isOpen={isStatusModalOpen}
                onClose={() => setIsStatusModalOpen(false)}
                title={
                    targetStatusAction === 'normal' ?
                        (statusTargetUser?.status === 'banned' ? '解封用户账号' : '恢复用户为正常状态') :
                        '封禁用户账号'
                }
                maxWidth="max-w-md"
                footer={
                    <>
                        <Button onClick={() => setIsStatusModalOpen(false)}>取消</Button>
                        <Button
                            variant={targetStatusAction === 'banned' ? 'danger' : 'primary'}
                            onClick={handleConfirmStatusChange}
                            disabled={isSavingStatus}
                        >
                            {isSavingStatus ? '处理中...' : (
                                targetStatusAction === 'normal' ?
                                    (statusTargetUser?.status === 'banned' ? '确认解封' : '确认恢复正常') :
                                    '确认封禁'
                            )}
                        </Button>
                    </>
                }
            >
                <div className="space-y-4">
                    {/* 警告提示 */}
                    <div className={`p-4 rounded-lg flex items-start gap-3 border ${targetStatusAction === 'banned' ? 'bg-red-50 border-red-100 text-red-800' :
                        statusTargetUser?.status === 'banned' ? 'bg-green-50 border-green-100 text-green-800' :
                            'bg-blue-50 border-blue-100 text-blue-800'
                        }`}>
                        <AlertTriangle size={18} className="mt-0.5 shrink-0" />
                        <div className="text-sm">
                            <p className="font-bold mb-1">
                                {targetStatusAction === 'banned' ? '高风险操作' :
                                    statusTargetUser?.status === 'banned' ? '解封操作' :
                                        '恢复正常状态'}
                            </p>
                            <p>
                                您正在对用户 <strong>{statusTargetUser?.username}</strong> 执行
                                {targetStatusAction === 'banned' ? '封禁' :
                                    statusTargetUser?.status === 'banned' ? '解封' :
                                        '恢复正常'}操作。
                                {targetStatusAction === 'banned' ? '封禁后该用户将无法登录系统或使用任何API服务。' :
                                    statusTargetUser?.status === 'banned' ? '解封后用户将恢复正常权限。' :
                                        '恢复后用户将变为正常状态，移除异常标记。'}
                            </p>
                        </div>
                    </div>

                    {/* 原因输入 */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-700">
                            {targetStatusAction === 'banned' ? '封禁原因' :
                                statusTargetUser?.status === 'banned' ? '解封原因' :
                                    '恢复原因'} <span className="text-red-500">*</span>
                        </label>
                        <textarea
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-colors min-h-[100px] resize-none"
                            placeholder={
                                targetStatusAction === 'banned' ? "请输入违规行为或封禁理由..." :
                                    statusTargetUser?.status === 'banned' ? "请输入解封理由或申诉处理结果..." :
                                        "请输入恢复正常的原因（如：确认为误判、用户行为已恢复正常等）..."
                            }
                            value={statusReason}
                            onChange={(e) => setStatusReason(e.target.value)}
                        />
                    </div>
                </div>
            </Modal>
        </div>
    );
};