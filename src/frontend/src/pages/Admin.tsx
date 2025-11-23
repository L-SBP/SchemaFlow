
import React, { useState } from 'react';
import { User, UserRole, UserStatus } from '../types.ts';
import { Card, Button, Tag, Modal, Input } from '../components/UI.tsx';
import { Search, Ban, CheckCircle, Shield, Eye, Database, Edit3 } from 'lucide-react';

interface AdminPanelProps {
  users: User[];
  onUpdateUser: (user: User) => void;
  onViewUser: (user: User) => void;
}

export const AdminPanel: React.FC<AdminPanelProps> = ({ users, onUpdateUser, onViewUser }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [editingQuotaUser, setEditingQuotaUser] = useState<User | null>(null);
  const [newQuota, setNewQuota] = useState('');
  const [quotaError, setQuotaError] = useState('');

  const handleToggleStatus = (user: User) => {
    if (confirm(`确定要${user.status === UserStatus.NORMAL ? '封禁' : '解封'}该用户吗？`)) {
      onUpdateUser({ 
        ...user, 
        status: user.status === UserStatus.NORMAL ? UserStatus.BANNED : UserStatus.NORMAL 
      });
    }
  };

  const handleOpenQuotaModal = (user: User) => {
    setEditingQuotaUser(user);
    setNewQuota(user.projectQuota.toString());
    setQuotaError('');
  };

  const handleSaveQuota = () => {
    if (!editingQuotaUser) return;
    const quota = parseInt(newQuota);
    
    // Validation per Req 3.2.10.3
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

  const filteredUsers = users.filter(u => 
    u.username.toLowerCase().includes(searchTerm.toLowerCase()) || 
    u.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-8 max-w-7xl mx-auto h-full overflow-y-auto">
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

      <Card className="overflow-hidden p-0">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-4 font-medium text-gray-600">用户ID</th>
              <th className="px-6 py-4 font-medium text-gray-600">用户名</th>
              <th className="px-6 py-4 font-medium text-gray-600">邮箱</th>
              <th className="px-6 py-4 font-medium text-gray-600">角色</th>
              <th className="px-6 py-4 font-medium text-gray-600">状态</th>
              <th className="px-6 py-4 font-medium text-gray-600">额度</th>
              <th className="px-6 py-4 font-medium text-gray-600">最后登录</th>
              <th className="px-6 py-4 font-medium text-gray-600 text-right">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filteredUsers.map(user => (
              <tr key={user.id} className="hover:bg-gray-50/50">
                <td className="px-6 py-4 text-gray-500 font-mono">{user.id}</td>
                <td className="px-6 py-4 font-medium text-gray-800">{user.username}</td>
                <td className="px-6 py-4 text-gray-600">{user.email}</td>
                <td className="px-6 py-4">
                  <Tag color={user.role === UserRole.ADMIN ? 'orange' : 'blue'}>
                    {user.role === UserRole.ADMIN ? '管理员' : '普通用户'}
                  </Tag>
                </td>
                <td className="px-6 py-4">
                  <Tag color={user.status === UserStatus.NORMAL ? 'green' : 'red'}>
                    {user.status === UserStatus.NORMAL ? '正常' : '封禁中'}
                  </Tag>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2 group cursor-pointer" onClick={() => user.role !== UserRole.ADMIN && handleOpenQuotaModal(user)}>
                    <span className="font-mono">{user.projectQuota}</span>
                    {user.role !== UserRole.ADMIN && <Edit3 size={12} className="text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />}
                  </div>
                </td>
                <td className="px-6 py-4 text-gray-500">{user.lastLogin}</td>
                <td className="px-6 py-4 text-right flex justify-end gap-2">
                   <Button 
                      variant="text"
                      className="h-8 px-2 text-gray-500 hover:text-primary"
                      onClick={() => onViewUser(user)}
                      title="查看详情"
                    >
                      <Eye size={16} />
                    </Button>
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
        {filteredUsers.length === 0 && (
          <div className="p-8 text-center text-gray-500">未找到匹配的用户</div>
        )}
      </Card>

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
               当前已用: N/A (系统将自动校验) <br/>
               系统全局上限: 100
             </p>
          </div>
        </div>
      </Modal>
    </div>
  );
};
