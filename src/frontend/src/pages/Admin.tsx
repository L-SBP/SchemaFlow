import React, { useState } from 'react';
import { User, UserRole, UserStatus } from '../types.ts';
import { Card, Button, Tag, Modal, Input } from '../components/UI.tsx';
import { Search, Ban, CheckCircle, Shield, Eye, Database, Edit3 } from 'lucide-react';

/**
 * 管理员面板组件属性接口
 */
interface AdminPanelProps {
    /** 当前系统中的所有用户列表 */
    users: User[];
    /** * 更新用户信息的各个字段（如状态、配额等）的回调函数
     * @param user - 更新后的用户对象
     */
    onUpdateUser: (user: User) => void;
    /**
     * 查看特定用户详情的回调函数
     * @param user - 目标用户
     */
    onViewUser: (user: User) => void;
}

/**
 * 系统管理后台 - 用户管理面板
 * * 提供用户列表的检索、状态变更（封禁/解封）以及资源配额调整功能。
 * * 仅限拥有 ADMIN 角色的用户访问。
 */
export const AdminPanel: React.FC<AdminPanelProps> = ({ users, onUpdateUser, onViewUser }) => {
    // --- 状态管理 ---

    /** 搜索过滤词（匹配用户名或邮箱） */
    const [searchTerm, setSearchTerm] = useState('');

    /** 当前正在编辑配额的用户对象，为 null 时表示模态框关闭 */
    const [editingQuotaUser, setEditingQuotaUser] = useState<User | null>(null);

    /** 配额输入框的临时状态 */
    const [newQuota, setNewQuota] = useState('');

    /** 配额校验错误信息 */
    const [quotaError, setQuotaError] = useState('');

    // --- 业务逻辑处理 ---

    /**
     * 切换用户状态（正常 <-> 封禁）
     * * 触发前会弹出浏览器原生确认框。
     * @param {User} user - 目标用户
     */
    const handleToggleStatus = (user: User) => {
        const action = user.status === UserStatus.NORMAL ? '封禁' : '解封';
        if (confirm(`确定要${action}该用户吗？`)) {
            onUpdateUser({
                ...user,
                status: user.status === UserStatus.NORMAL ? UserStatus.BANNED : UserStatus.NORMAL
            });
        }
    };

    /**
     * 打开配额编辑模态框
     * * 初始化输入框值为用户当前的配额。
     * @param {User} user - 目标用户
     */
    const handleOpenQuotaModal = (user: User) => {
        setEditingQuotaUser(user);
        setNewQuota(user.projectQuota.toString());
        setQuotaError('');
    };

    /**
     * 保存配额更改
     * * 包含输入校验逻辑：必须为非负整数且不超过系统上限。
     */
    const handleSaveQuota = () => {
        if (!editingQuotaUser) return;
        const quota = parseInt(newQuota);

        // 业务规则校验 (Req 3.2.10.3)
        if (isNaN(quota) || quota < 0) {
            setQuotaError('额度不能为负数');
            return;
        }
        if (quota > 100) {
            setQuotaError('额度值超出系统上限 (100)');
            return;
        }

        onUpdateUser({ ...editingQuotaUser, projectQuota: quota });
        setEditingQuotaUser(null);
    };

    // 根据搜索词过滤用户列表
    const filteredUsers = users.filter(u =>
        u.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
        u.email.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="p-8 max-w-7xl mx-auto h-full overflow-y-auto">
            {/* 顶部标题与搜索栏 */}
            <div className="flex justify-between items-center mb-8">
                <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                    <Shield className="text-primary" /> 系统管理后台
                </h2>
                <div className="w-72">
                    <div className="relative">
                        <input
                            type="text"
                            placeholder="搜索用户名或邮箱..."
                            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-primary focus:border-primary text-sm"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                        <Search className="absolute left-3 top-2.5 text-gray-400" size={16} />
                    </div>
                </div>
            </div>

            {/* 用户列表表格 */}
            <Card className="overflow-hidden p-0">
                {/* 修复：添加 overflow-x-auto 容器，防止窄屏下表格挤压变形 */}
                <div className="overflow-x-auto">
                    {/* 修复：设置 min-w-[1000px] 强制表格最小宽度，内容过多时触发横向滚动 */}
                    <table className="w-full text-left text-sm min-w-[1000px]">
                        <thead className="bg-gray-50 border-b border-gray-200">
                            <tr>
                                {/* 修复：添加 whitespace-nowrap 防止表头文字换行 */}
                                <th className="px-6 py-4 font-medium text-gray-600 whitespace-nowrap">用户ID</th>
                                <th className="px-6 py-4 font-medium text-gray-600 whitespace-nowrap">用户名</th>
                                <th className="px-6 py-4 font-medium text-gray-600 whitespace-nowrap">邮箱</th>
                                <th className="px-6 py-4 font-medium text-gray-600 whitespace-nowrap">角色</th>
                                <th className="px-6 py-4 font-medium text-gray-600 whitespace-nowrap">状态</th>
                                <th className="px-6 py-4 font-medium text-gray-600 whitespace-nowrap">额度</th>
                                <th className="px-6 py-4 font-medium text-gray-600 whitespace-nowrap">最后登录</th>
                                <th className="px-6 py-4 font-medium text-gray-600 text-right whitespace-nowrap">操作</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {filteredUsers.map(user => (
                                <tr key={user.id} className="hover:bg-gray-50/50">
                                    <td className="px-6 py-4 text-gray-500 font-mono whitespace-nowrap">{user.id}</td>
                                    <td className="px-6 py-4 font-medium text-gray-800 whitespace-nowrap">{user.username}</td>
                                    <td className="px-6 py-4 text-gray-600 whitespace-nowrap">{user.email}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <Tag color={user.role === UserRole.ADMIN ? 'orange' : 'blue'}>
                                            {user.role === UserRole.ADMIN ? '管理员' : '普通用户'}
                                        </Tag>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <Tag color={user.status === UserStatus.NORMAL ? 'green' : 'red'}>
                                            {user.status === UserStatus.NORMAL ? '正常' : '封禁中'}
                                        </Tag>
                                    </td>
                                    {/* 额度列：非管理员可点击编辑 */}
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="flex items-center gap-2 group cursor-pointer" onClick={() => user.role !== UserRole.ADMIN && handleOpenQuotaModal(user)}>
                                            <span className="font-mono">{user.projectQuota}</span>
                                            {user.role !== UserRole.ADMIN && <Edit3 size={12} className="text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-gray-500 whitespace-nowrap">{user.lastLogin}</td>
                                    <td className="px-6 py-4 text-right flex justify-end gap-2 whitespace-nowrap">
                                        <Button
                                            variant="text"
                                            className="h-8 px-2 text-gray-500 hover:text-primary"
                                            onClick={() => onViewUser(user)}
                                            title="查看详情"
                                        >
                                            <Eye size={16} />
                                        </Button>
                                        {/* 管理员不能操作自己的状态 */}
                                        {user.role !== UserRole.ADMIN && (
                                            <Button
                                                variant={user.status === UserStatus.NORMAL ? 'danger' : 'default'}
                                                className="h-8 px-3 text-xs"
                                                onClick={() => handleToggleStatus(user)}
                                                icon={user.status === UserStatus.NORMAL ? <Ban size={12} /> : <CheckCircle size={12} />}
                                            >
                                                {user.status === UserStatus.NORMAL ? '封禁' : '解封'}
                                            </Button>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                {filteredUsers.length === 0 && (
                    <div className="p-8 text-center text-gray-500">未找到匹配的用户</div>
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
                        <Button variant="primary" onClick={handleSaveQuota}>保存更改</Button>
                    </>
                }
            >
                <div className="space-y-4">
                    <div className="bg-blue-50 p-3 rounded-lg flex items-start gap-3">
                        <Database className="text-primary shrink-0 mt-0.5" size={18} />
                        <div className="text-sm text-blue-900">
                            <p>正在修改用户 <strong>{editingQuotaUser?.username}</strong> 的项目创建配额。</p>
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
                        />
                        {quotaError && <p className="text-red-500 text-xs mt-1">{quotaError}</p>}
                        <p className="text-xs text-gray-400 mt-2">
                            当前已用: N/A (系统将自动校验) <br />
                            系统全局上限: 100
                        </p>
                    </div>
                </div>
            </Modal>
        </div>
    );
};