
import React, { useState } from 'react';
import { Card, Button, Tag, ProgressBar } from '../components/UI.tsx';
import { Activity, Server, Shield, Users, AlertTriangle, Zap, CheckCircle2, Clock } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ComposedChart, Bar, Line, Legend } from 'recharts';
import { User, UserRole, RiskEvent } from '../types.ts';

// Mock Data
const MOCK_ADMINS: User[] = [
  { id: '1003', username: 'admin_sys', email: 'admin@sys.com', role: UserRole.ADMIN, status: 'NORMAL' as any, lastLogin: '2025-11-05 14:00', projectQuota: 99, isOnline: true, lastLoginIp: '192.168.1.5' },
  { id: '1004', username: 'admin_sec', email: 'sec@sys.com', role: UserRole.ADMIN, status: 'NORMAL' as any, lastLogin: '2025-11-05 10:00', projectQuota: 99, isOnline: false, lastLoginIp: '10.0.0.2' },
];

const RESOURCE_DATA = [
  { time: '10:00', cpu: 45, memory: 60, requests: 1200 },
  { time: '11:00', cpu: 55, memory: 65, requests: 1500 },
  { time: '12:00', cpu: 80, memory: 75, requests: 2800 },
  { time: '13:00', cpu: 70, memory: 70, requests: 2200 },
  { time: '14:00', cpu: 60, memory: 65, requests: 1800 },
  { time: '15:00', cpu: 50, memory: 62, requests: 1600 },
];

const ACTIVITY_DATA = [
  { date: '11-01', dau: 450, qps: 2300 },
  { date: '11-02', dau: 470, qps: 2500 },
  { date: '11-03', dau: 420, qps: 2100 },
  { date: '11-04', dau: 510, qps: 3200 },
  { date: '11-05', dau: 550, qps: 3500 },
];

const MOCK_RISKS: RiskEvent[] = [
  { id: 'r1', type: 'sql_injection', level: 'high', sourceIp: '203.0.113.42', description: '检测到 SQL 注入尝试: SELECT * FROM users --', timestamp: '2025-11-05 14:22:10', status: 'pending' },
  { id: 'r2', type: 'abnormal_login', level: 'medium', sourceIp: '198.51.100.12', description: '同一 IP 连续失败登录 5 次', timestamp: '2025-11-05 13:15:00', status: 'blocked' },
  { id: 'r3', type: 'high_frequency', level: 'low', sourceIp: '192.168.1.105', description: 'API 调用频率超过阈值 (100/min)', timestamp: '2025-11-05 12:30:00', status: 'ignored' },
];

export const AdminStatus: React.FC = () => {
  const [risks, setRisks] = useState<RiskEvent[]>(MOCK_RISKS);

  const handleRiskAction = (id: string, action: 'blocked' | 'ignored') => {
    setRisks(risks.map(r => r.id === id ? { ...r, status: action } : r));
  };

  return (
    <div className="p-8 max-w-7xl mx-auto h-full overflow-y-auto space-y-8">
      <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
        <Activity className="text-primary" /> 系统运行状态
      </h2>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="bg-gradient-to-br from-blue-50 to-white border-blue-100">
          <div className="flex items-center gap-3 mb-2 text-blue-600">
            <Server size={20} />
            <span className="font-bold">系统可用性</span>
          </div>
          <div className="text-2xl font-bold text-gray-800">99.98%</div>
          <p className="text-xs text-green-600 mt-1 flex items-center gap-1"><CheckCircle2 size={10} /> 运行正常</p>
        </Card>
        <Card className="bg-gradient-to-br from-purple-50 to-white border-purple-100">
          <div className="flex items-center gap-3 mb-2 text-purple-600">
            <Zap size={20} />
            <span className="font-bold">P95 响应时间</span>
          </div>
          <div className="text-2xl font-bold text-gray-800">45ms</div>
          <p className="text-xs text-gray-500 mt-1">目标: &lt;50ms</p>
        </Card>
        <Card className="bg-gradient-to-br from-green-50 to-white border-green-100">
          <div className="flex items-center gap-3 mb-2 text-green-600">
            <CheckCircle2 size={20} />
            <span className="font-bold">部署成功率</span>
          </div>
          <div className="text-2xl font-bold text-gray-800">98.5%</div>
          <p className="text-xs text-green-600 mt-1">昨日: 98.2%</p>
        </Card>
        <Card className="bg-gradient-to-br from-orange-50 to-white border-orange-100">
          <div className="flex items-center gap-3 mb-2 text-orange-600">
            <AlertTriangle size={20} />
            <span className="font-bold">待处理风险</span>
          </div>
          <div className="text-2xl font-bold text-gray-800">{risks.filter(r => r.status === 'pending').length}</div>
          <p className="text-xs text-orange-600 mt-1">高危事件: {risks.filter(r => r.status === 'pending' && r.level === 'high').length}</p>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="资源负载监控 (实时)">
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={RESOURCE_DATA}>
                <defs>
                  <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#1677ff" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#1677ff" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorMem" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#52c41a" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#52c41a" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" fontSize={12} tickLine={false} />
                <YAxis fontSize={12} tickLine={false} />
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                <Tooltip />
                <Area type="monotone" dataKey="cpu" stroke="#1677ff" fillOpacity={1} fill="url(#colorCpu)" name="CPU %" />
                <Area type="monotone" dataKey="memory" stroke="#52c41a" fillOpacity={1} fill="url(#colorMem)" name="Memory %" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="用户活跃度趋势">
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={ACTIVITY_DATA}>
                 <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                 <XAxis dataKey="date" fontSize={12} />
                 <YAxis yAxisId="left" fontSize={12} />
                 <YAxis yAxisId="right" orientation="right" fontSize={12} />
                 <Tooltip />
                 <Legend />
                 <Bar yAxisId="left" dataKey="dau" fill="#1677ff" name="日活用户 (DAU)" barSize={30} radius={[4,4,0,0]} />
                 <Line yAxisId="right" type="monotone" dataKey="qps" stroke="#faad14" strokeWidth={3} name="查询量 (QPS)" />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Risk Control & Admin List */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Control */}
        <div className="lg:col-span-2">
          <Card title="安全风险管控" className="h-full">
             <div className="overflow-x-auto">
               <table className="w-full text-left text-sm">
                 <thead className="bg-gray-50 border-b border-gray-200">
                   <tr>
                     <th className="px-4 py-3">风险类型</th>
                     <th className="px-4 py-3">源IP</th>
                     <th className="px-4 py-3">描述</th>
                     <th className="px-4 py-3">状态</th>
                     <th className="px-4 py-3 text-right">操作</th>
                   </tr>
                 </thead>
                 <tbody className="divide-y divide-gray-100">
                   {risks.map(risk => (
                     <tr key={risk.id} className="hover:bg-gray-50/50">
                       <td className="px-4 py-3">
                         <div className="flex items-center gap-2">
                           {risk.level === 'high' && <AlertTriangle size={14} className="text-red-500" />}
                           {risk.level === 'medium' && <AlertTriangle size={14} className="text-orange-500" />}
                           {risk.level === 'low' && <AlertTriangle size={14} className="text-blue-500" />}
                           <span className="font-medium text-gray-700">
                             {risk.type === 'sql_injection' ? 'SQL注入' : risk.type === 'abnormal_login' ? '异常登录' : '高频调用'}
                           </span>
                         </div>
                       </td>
                       <td className="px-4 py-3 font-mono text-xs text-gray-500">{risk.sourceIp}</td>
                       <td className="px-4 py-3 text-gray-600 max-w-[200px] truncate" title={risk.description}>{risk.description}</td>
                       <td className="px-4 py-3">
                         <Tag color={risk.status === 'pending' ? 'orange' : risk.status === 'blocked' ? 'red' : 'green'}>
                           {risk.status === 'pending' ? '待处理' : risk.status === 'blocked' ? '已阻断' : '已忽略'}
                         </Tag>
                       </td>
                       <td className="px-4 py-3 text-right">
                         {risk.status === 'pending' && (
                           <div className="flex justify-end gap-2">
                             <Button variant="danger" className="h-7 px-2 text-xs" onClick={() => handleRiskAction(risk.id, 'blocked')}>阻断</Button>
                             <Button variant="default" className="h-7 px-2 text-xs" onClick={() => handleRiskAction(risk.id, 'ignored')}>忽略</Button>
                           </div>
                         )}
                       </td>
                     </tr>
                   ))}
                 </tbody>
               </table>
             </div>
          </Card>
        </div>

        {/* Admin Status */}
        <div className="lg:col-span-1">
          <Card title="管理员在线状态" className="h-full">
             <div className="space-y-4">
               {MOCK_ADMINS.map(admin => (
                 <div key={admin.id} className="flex items-center justify-between border-b border-gray-50 pb-3 last:border-0">
                    <div className="flex items-center gap-3">
                       <div className="relative">
                         <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-600 font-bold">
                           {admin.username.charAt(0).toUpperCase()}
                         </div>
                         <div className={`absolute bottom-0 right-0 w-3 h-3 rounded-full border-2 border-white ${admin.isOnline ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                       </div>
                       <div>
                         <div className="font-medium text-gray-800">{admin.username}</div>
                         <div className="text-xs text-gray-500 flex items-center gap-1">
                           <Clock size={10} /> {admin.isOnline ? '在线' : `上次: ${admin.lastLogin.split(' ')[1]}`}
                         </div>
                       </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-gray-400 font-mono">{admin.lastLoginIp}</div>
                      <Tag color={admin.isOnline ? 'green' : 'gray'}>{admin.isOnline ? 'Online' : 'Offline'}</Tag>
                    </div>
                 </div>
               ))}
             </div>
          </Card>
        </div>
      </div>
    </div>
  );
};