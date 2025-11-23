import React from 'react';
import { User, Project, UserRole, UserStatus } from '../types.ts';
import { Card, Button, Tag } from '../components/UI.tsx';
import { ArrowLeft, Clock, Database, Shield, MapPin, Globe } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface UserProfileProps {
  user: User;
  onBack: () => void;
}

// Mock Data for specific user view
const MOCK_USER_PROJECTS: Project[] = [
  { id: '101', name: '电商订单系统', type: 'MySQL', description: '主业务数据库', status: 'active', createdAt: '2025-10-20' },
  { id: '102', name: '日志归档', type: 'PostgreSQL', description: '历史日志存储', status: 'active', createdAt: '2025-10-25' },
  { id: '103', name: '测试环境', type: 'MySQL', description: '开发测试用', status: 'error', createdAt: '2025-11-02' },
];

const MOCK_LOGIN_HISTORY = [
  { id: 1, ip: '192.168.1.101', location: '北京, 中国', device: 'Chrome / Windows', timestamp: '2025-11-05 14:30:22', status: 'success' },
  { id: 2, ip: '192.168.1.101', location: '北京, 中国', device: 'Chrome / Windows', timestamp: '2025-11-04 09:15:00', status: 'success' },
  { id: 3, ip: '10.0.0.55', location: '上海, 中国', device: 'Safari / iPhone', timestamp: '2025-11-03 18:20:11', status: 'success' },
  { id: 4, ip: '203.0.113.42', location: '未知', device: 'Unknown', timestamp: '2025-11-01 03:45:12', status: 'failed' },
];

export const UserProfile: React.FC<UserProfileProps> = ({ user, onBack }) => {
  // Calculate Quota Data
  const usedQuota = MOCK_USER_PROJECTS.length;
  const maxQuota = user.projectQuota;
  const usagePercentage = (usedQuota / maxQuota) * 100;
  
  const quotaChartData = [
    { name: '已用', value: usedQuota, color: '#1677ff' },
    { name: '剩余', value: maxQuota - usedQuota, color: '#f0f0f0' },
  ];

  return (
    <div className="p-8 max-w-7xl mx-auto h-full overflow-y-auto">
      {/* Header */}
      <div className="mb-6">
        <Button variant="text" onClick={onBack} className="mb-4 text-gray-500 hover:text-gray-800 pl-0">
          <ArrowLeft size={16} className="mr-1" /> 返回用户列表
        </Button>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-6">
            <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center text-primary text-2xl font-bold border-4 border-white shadow-sm">
              {user.username.charAt(0).toUpperCase()}
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-3">
                {user.username}
                <Tag color={user.role === UserRole.ADMIN ? 'orange' : 'blue'}>
                  {user.role === UserRole.ADMIN ? '管理员' : '普通用户'}
                </Tag>
                <Tag color={user.status === UserStatus.NORMAL ? 'green' : 'red'}>
                  {user.status === UserStatus.NORMAL ? '状态正常' : '已封禁'}
                </Tag>
              </h2>
              <div className="text-gray-500 mt-2 flex items-center gap-6 text-sm">
                <span className="flex items-center gap-1"><Shield size={14} /> ID: {user.id}</span>
                <span className="flex items-center gap-1">📧 {user.email}</span>
                <span className="flex items-center gap-1"><Clock size={14} /> 上次登录: {user.lastLogin}</span>
              </div>
            </div>
          </div>
          <div className="text-right">
             {/* Additional actions could go here */}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Quota & Login History */}
        <div className="lg:col-span-1 space-y-6">
          {/* Quota Usage Card */}
          <Card title="资源配额使用情况">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-600 font-medium">数据库项目</span>
              <span className="text-xl font-bold text-gray-800">{usedQuota} <span className="text-gray-400 text-sm font-normal">/ {maxQuota}</span></span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2.5 mb-6 overflow-hidden">
              <div 
                className={`h-2.5 rounded-full ${usagePercentage > 90 ? 'bg-red-500' : 'bg-primary'}`} 
                style={{ width: `${Math.min(usagePercentage, 100)}%` }}
              ></div>
            </div>
            
            <div className="h-40">
               <ResponsiveContainer width="100%" height="100%">
                 <BarChart data={[{ name: 'Usage', used: usedQuota, remaining: maxQuota - usedQuota }]} layout="vertical" barSize={20}>
                    <XAxis type="number" hide />
                    <YAxis type="category" dataKey="name" hide />
                    <Tooltip cursor={{fill: 'transparent'}} />
                    <Bar dataKey="used" stackId="a" fill="#1677ff" radius={[4, 0, 0, 4]} />
                    <Bar dataKey="remaining" stackId="a" fill="#f5f5f5" radius={[0, 4, 4, 0]} />
                 </BarChart>
               </ResponsiveContainer>
            </div>
            <p className="text-xs text-gray-500 mt-2 text-center">当前用户已创建 {usedQuota} 个项目，剩余可创建 {maxQuota - usedQuota} 个。</p>
          </Card>

          {/* Login History */}
          <Card title="近期登录历史">
            <div className="space-y-4">
              {MOCK_LOGIN_HISTORY.map((log) => (
                <div key={log.id} className="flex items-start gap-3 text-sm border-b border-gray-50 pb-3 last:border-0 last:pb-0">
                  <div className={`w-2 h-2 mt-1.5 rounded-full ${log.status === 'success' ? 'bg-green-500' : 'bg-red-500'}`}></div>
                  <div className="flex-1">
                    <div className="flex justify-between">
                      <span className="font-medium text-gray-700">{log.ip}</span>
                      <span className="text-gray-400 text-xs">{log.timestamp}</span>
                    </div>
                    <div className="flex items-center gap-2 text-gray-500 text-xs mt-1">
                      <span className="flex items-center gap-0.5"><MapPin size={10} /> {log.location}</span>
                      <span className="flex items-center gap-0.5"><Globe size={10} /> {log.device}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Right Column: Project List */}
        <div className="lg:col-span-2">
          <Card title={`已创建的项目 (${MOCK_USER_PROJECTS.length})`}>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-gray-50 border-b border-gray-100">
                  <tr>
                    <th className="px-4 py-3 font-medium text-gray-600">项目名称</th>
                    <th className="px-4 py-3 font-medium text-gray-600">类型</th>
                    <th className="px-4 py-3 font-medium text-gray-600">状态</th>
                    <th className="px-4 py-3 font-medium text-gray-600">创建时间</th>
                    <th className="px-4 py-3 font-medium text-gray-600">描述</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {MOCK_USER_PROJECTS.map((project) => (
                    <tr key={project.id} className="hover:bg-gray-50/50">
                      <td className="px-4 py-3 font-medium text-gray-800 flex items-center gap-2">
                        <Database size={14} className="text-gray-400" />
                        {project.name}
                      </td>
                      <td className="px-4 py-3 text-gray-600">{project.type}</td>
                      <td className="px-4 py-3">
                        <Tag color={project.status === 'active' ? 'green' : project.status === 'error' ? 'red' : 'blue'}>
                          {project.status === 'active' ? '运行中' : project.status === 'error' ? '异常' : '部署中'}
                        </Tag>
                      </td>
                      <td className="px-4 py-3 text-gray-500">{project.createdAt}</td>
                      <td className="px-4 py-3 text-gray-500 max-w-xs truncate" title={project.description}>
                        {project.description}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {MOCK_USER_PROJECTS.length === 0 && (
                <div className="py-8 text-center text-gray-400">该用户暂未创建任何数据库项目</div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};