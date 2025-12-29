import React, { useState, useEffect } from 'react';
import { Card, Tag } from '../components/UI.tsx';
import { LayoutDashboard, Server, Users, AlertTriangle, Zap, ShieldAlert } from 'lucide-react';
import { AdminStats, AdminListItem, ViolationLogListItem } from '../types.ts';
import { adminApi } from '../api/admin.ts';

/**
 * 管理员系统监控面板
 * * 严格对接真实 API: Dashboard Stats, Admin List, Violations
 * * 移除所有无后端接口支持的图表和模拟数据
 */
export const AdminStatus: React.FC = () => {
    // --- 状态管理 ---
    const [stats, setStats] = useState<AdminStats | null>(null);
    const [admins, setAdmins] = useState<AdminListItem[]>([]);
    const [violations, setViolations] = useState<ViolationLogListItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    // --- 数据获取 ---
    useEffect(() => {
        const fetchAllData = async () => {
            setIsLoading(true);
            try {
                // 并发请求所有数据
                const [statsRes, adminsRes, violationsRes] = await Promise.all([
                    adminApi.getDashboardStats(),
                    adminApi.getAdmins(1, 100), // 获取更多在线管理员
                    adminApi.getViolations(1, 20) // 获取最新20条违规
                ]);

                setStats(statsRes);
                setAdmins(adminsRes.items);
                setViolations(violationsRes.items);
            } catch (error) {
                console.error("Failed to load admin status data", error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchAllData();
    }, []);

    return (
        <div className="p-8 max-w-7xl mx-auto h-full overflow-y-auto space-y-8">
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-3">
                    <div className="p-2 bg-blue-100 text-blue-600 rounded-lg shrink-0">
                        <LayoutDashboard size={20} />
                    </div>
                    系统状态
                </h2>
                <div className="text-sm text-gray-500">
                    数据最后更新: {new Date().toLocaleTimeString()}
                </div>
            </div>

            {/* 1. 核心指标卡片 (Real API Data: GET /dashboard/stats) */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card className={`bg-gradient-to-br from-blue-50 to-white border-blue-100 ${isLoading ? 'animate-pulse' : ''}`}>
                    <div className="flex items-center gap-3 mb-2 text-blue-600">
                        <Server size={20} />
                        <span className="font-bold">系统健康度</span>
                    </div>
                    <div className="text-2xl font-bold text-gray-800 capitalize">
                        {stats?.system_health || '-'}
                    </div>
                    <p className={`text-xs mt-1 flex items-center gap-1 font-medium ${stats?.system_health === 'good' ? 'text-green-600' : 'text-red-500'}`}>
                        状态: {stats?.system_health === 'good' ? '良好' : '异常'}
                    </p>
                </Card>

                <Card className="bg-gradient-to-br from-purple-50 to-white border-purple-100">
                    <div className="flex items-center gap-3 mb-2 text-purple-600">
                        <Users size={20} />
                        <span className="font-bold">今日活跃用户</span>
                    </div>
                    <div className="text-2xl font-bold text-gray-800">{stats?.active_users_today ?? 0}</div>
                    <p className="text-xs text-purple-400 mt-1">Active Users Today</p>
                </Card>

                <Card className="bg-gradient-to-br from-green-50 to-white border-green-100">
                    <div className="flex items-center gap-3 mb-2 text-green-600">
                        <Zap size={20} />
                        <span className="font-bold">今日查询量</span>
                    </div>
                    <div className="text-2xl font-bold text-gray-800">{stats?.query_count_today ?? 0}</div>
                    <p className="text-xs text-green-600 mt-1">Queries Processed</p>
                </Card>

                <Card className="bg-gradient-to-br from-orange-50 to-white border-orange-100">
                    <div className="flex items-center gap-3 mb-2 text-orange-600">
                        <AlertTriangle size={20} />
                        <span className="font-bold">高危拦截</span>
                    </div>
                    <div className="text-2xl font-bold text-gray-800">{stats?.high_risk_operations_today ?? 0}</div>
                    <p className="text-xs text-orange-600 mt-1">Blocked Operations</p>
                </Card>
            </div>

            {/* 2. 数据列表区域 */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-300px)] min-h-[500px]">
                {/* 违规审计日志 (Real API Data: GET /violations) */}
                <div className="lg:col-span-2 h-full flex flex-col">
                    <Card title="安全违规审计日志" className="flex-1 flex flex-col overflow-hidden" extra={<span className="text-xs text-gray-400">最新20条</span>}>
                        <div className="overflow-auto flex-1">
                            <table className="w-full text-left text-sm min-w-[600px]">
                                <thead className="bg-gray-50 border-b border-gray-200 sticky top-0 z-10">
                                    <tr>
                                        <th className="px-4 py-3 whitespace-nowrap bg-gray-50">风险等级</th>
                                        <th className="px-4 py-3 whitespace-nowrap bg-gray-50">违规类型</th>
                                        <th className="px-4 py-3 whitespace-nowrap bg-gray-50">用户</th>
                                        <th className="px-4 py-3 whitespace-nowrap bg-gray-50">处理状态</th>
                                        <th className="px-4 py-3 whitespace-nowrap bg-gray-50 text-right">时间</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100">
                                    {violations.map(log => (
                                        <tr key={log.violation_id} className="hover:bg-gray-50/50">
                                            <td className="px-4 py-3 whitespace-nowrap">
                                                <div className="flex items-center gap-2">
                                                    {log.risk_level === 'CRITICAL' || log.risk_level === 'HIGH' ? (
                                                        <ShieldAlert size={14} className="text-red-500" />
                                                    ) : (
                                                        <AlertTriangle size={14} className="text-orange-400" />
                                                    )}
                                                    <span className={`font-medium ${log.risk_level === 'CRITICAL' ? 'text-red-600' : 'text-gray-700'}`}>
                                                        {log.risk_level}
                                                    </span>
                                                </div>
                                            </td>
                                            <td className="px-4 py-3">
                                                <div className="flex flex-col">
                                                    <span className="text-gray-700 font-medium text-xs">
                                                        {log.event_type === 'excessive_api_usage' && 'API频率超限'}
                                                        {log.event_type === 'sql_injection_attempt' && 'SQL注入尝试'}
                                                        {log.event_type === 'suspicious_query' && '可疑查询'}
                                                        {log.event_type === 'unauthorized_access_attempt' && '未授权访问'}
                                                        {log.event_type === 'ai_violation_content' && 'AI内容违规'}
                                                        {log.event_type === 'frequent_remote_login' && 'IP频繁变更'}
                                                        {log.event_type === 'multiple_failed_logins' && '多次登录失败'}
                                                        {!['excessive_api_usage', 'sql_injection_attempt', 'suspicious_query', 'unauthorized_access_attempt', 'ai_violation_content', 'frequent_remote_login', 'multiple_failed_logins'].includes(log.event_type) && log.event_type}
                                                    </span>
                                                </div>
                                            </td>
                                            <td className="px-4 py-3 text-gray-600">
                                                {log.username} <span className="text-xs text-gray-400">(ID:{log.user_id})</span>
                                            </td>
                                            <td className="px-4 py-3">
                                                <Tag color={log.resolution_status === 'resolved' ? 'green' : log.resolution_status === 'pending' ? 'orange' : 'gray'}>
                                                    {log.resolution_status}
                                                </Tag>
                                            </td>
                                            <td className="px-4 py-3 text-gray-500 text-xs whitespace-nowrap text-right">
                                                {new Date(log.created_at).toLocaleString()}
                                            </td>
                                        </tr>
                                    ))}
                                    {violations.length === 0 && (
                                        <tr><td colSpan={5} className="text-center py-12 text-gray-400">暂无违规记录</td></tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </Card>
                </div>

                {/* 管理员列表 (Real API Data: GET /admins) */}
                <div className="lg:col-span-1 h-full flex flex-col">
                    <Card title="管理员列表" className="flex-1 flex flex-col overflow-hidden">
                        <div className="space-y-4 overflow-y-auto pr-1 flex-1">
                            {admins.map(admin => (
                                <div key={admin.user_id} className="flex items-center justify-between border-b border-gray-50 pb-3 last:border-0">
                                    <div className="flex items-center gap-3">
                                        <div className="relative">
                                            <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center text-blue-600 font-bold text-sm">
                                                {admin.username.charAt(0).toUpperCase()}
                                            </div>
                                            <div className={`absolute bottom-0 right-0 w-3 h-3 rounded-full border-2 border-white ${admin.is_online ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                                        </div>
                                        <div>
                                            <div className="font-medium text-gray-800 text-sm">{admin.username}</div>
                                            <div className="text-xs text-gray-400">{admin.email}</div>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <Tag color={admin.is_online ? 'green' : 'gray'}>
                                            {admin.is_online ? '在线' : '离线'}
                                        </Tag>
                                        <div className="text-[10px] text-gray-300 mt-1">
                                            ID: {admin.user_id}
                                        </div>
                                    </div>
                                </div>
                            ))}
                            {admins.length === 0 && (
                                <div className="text-center py-8 text-gray-400">暂无管理员信息</div>
                            )}
                        </div>
                    </Card>
                </div>
            </div>
        </div>
    );
};