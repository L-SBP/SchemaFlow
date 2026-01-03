import React, { useEffect, useMemo, useState } from 'react';
import { User, Project, UserRole, UserStatus, AdminUserDetailResponse } from '../types.ts';
import { Card, Button, Tag } from '../components/UI.tsx';
import { ArrowLeft, Clock, Database, Shield, MapPin, Globe, Loader2 } from 'lucide-react';
import { adminApi } from '../api/admin.ts';

interface UserProfileProps {
  user: User;
  onBack: () => void;
}

const mapDbType = (dbType?: string | null): 'MySQL' | 'PostgreSQL' | 'SQLite' => {
  if (!dbType) return 'MySQL';
  const normalized = dbType.toLowerCase();
  if (normalized.includes('postgres')) return 'PostgreSQL';
  if (normalized.includes('sqlite')) return 'SQLite';
  return 'MySQL';
};

const mapProjectStatus = (projectStatus?: string | null): 'active' | 'deploying' | 'error' | 'deleted' => {
  const normalized = (projectStatus || '').toLowerCase();
  if (normalized === 'active' || normalized === 'completed') return 'active';
  if (normalized === 'deleted') return 'deleted';
  return 'deploying';
};

const formatDateTime = (value?: string | number | null): string => {
  if (value === null || value === undefined) return '-';

  const toText = (d: Date, fallback: string) => (Number.isNaN(d.getTime()) ? fallback : d.toLocaleString());

  if (typeof value === 'number') {
    // 兼容秒/毫秒时间戳
    const ms = value < 1e12 ? value * 1000 : value;
    return toText(new Date(ms), String(value));
  }

  const raw = String(value).trim();
  if (!raw) return '-';

  // 兼容纯数字字符串时间戳
  if (/^\d+$/.test(raw)) {
    const n = Number(raw);
    const ms = n < 1e12 ? n * 1000 : n;
    return toText(new Date(ms), raw);
  }

  return toText(new Date(raw), raw);
};

export const UserProfile: React.FC<UserProfileProps> = ({ user, onBack }) => {
  const [detail, setDetail] = useState<AdminUserDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  // 登录历史分页（前端限制展示长度）
  const [loginPage, setLoginPage] = useState(1);
  const loginPageSize = 5;

  useEffect(() => {
    let cancelled = false;

    const fetchDetail = async () => {
      setLoading(true);
      setLoadError(null);
      try {
        const res = await adminApi.getUserDetail(user.id, 100, 20);
        if (!cancelled) setDetail(res);
      } catch (e: any) {
        console.error('Fetch user detail error:', e);
        // 错误已由API客户端统一处理，这里只需记录日志和设置本地错误状态
        if (!cancelled) {
          setLoadError(e?.message || '加载用户详情失败，请稍后重试');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchDetail();
    return () => {
      cancelled = true;
    };
  }, [user.id]);

  // 用户切换 / 数据刷新时，重置登录历史分页
  useEffect(() => {
    setLoginPage(1);
  }, [detail?.user_id]);

  const projects: Project[] = useMemo(() => {
    if (!detail) return [];
    return detail.projects.map((p) => ({
      id: p.project_id.toString(),
      name: p.project_name,
      type: mapDbType(p.db_type),
      description: p.description || '',
      status: mapProjectStatus(p.project_status),
      createdAt: p.created_at
    }));
  }, [detail]);

  // Calculate Quota Data
  const usedQuota = detail?.project_count ?? 0;
  const maxQuota = detail?.max_databases ?? user.projectQuota;
  const usagePercentage = maxQuota > 0 ? (usedQuota / maxQuota) * 100 : 0;
  const remainingQuota = Math.max(maxQuota - usedQuota, 0);

  const lastLoginText = useMemo(() => {
    const last = detail?.last_login_at;
    if (!last) return '从未登录';
    const date = new Date(last);
    return Number.isNaN(date.getTime()) ? last : date.toLocaleString();
  }, [detail?.last_login_at]);

  const normalizeStatus = (status: UserStatus | AdminUserDetailResponse['status'] | undefined): UserStatus => {
    const normalized = (status ?? '').toString().toLowerCase();
    if (normalized === 'normal') return UserStatus.NORMAL;
    if (normalized === 'suspended') return UserStatus.SUSPENDED;
    if (normalized === 'banned') return UserStatus.BANNED;
    return UserStatus.NORMAL;
  };

  const currentStatus = normalizeStatus(detail?.status ?? user.status);
  const statusLabel = currentStatus === UserStatus.NORMAL ? '状态正常' : currentStatus === UserStatus.SUSPENDED ? '异常' : '已封禁';
  const statusColor = currentStatus === UserStatus.NORMAL ? 'green' : currentStatus === UserStatus.SUSPENDED ? 'orange' : 'red';

  if (loading) {
    return (
      <div className="p-8 max-w-7xl mx-auto h-full overflow-y-auto">
        <Button variant="text" onClick={onBack} className="mb-4 text-gray-500 hover:text-gray-800 pl-0">
          <ArrowLeft size={16} className="mr-1" /> 返回用户列表
        </Button>
        <div className="flex justify-center items-center h-64">
          <Loader2 className="animate-spin text-primary" size={32} />
        </div>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="p-8 max-w-7xl mx-auto h-full overflow-y-auto">
        <Button variant="text" onClick={onBack} className="mb-4 text-gray-500 hover:text-gray-800 pl-0">
          <ArrowLeft size={16} className="mr-1" /> 返回用户列表
        </Button>
        <Card title="加载失败">
          <div className="text-sm text-gray-600">{loadError}</div>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto h-full overflow-y-auto">
      {/* Header */}
      <div className="mb-6">
        <Button variant="text" onClick={onBack} className="mb-4 text-gray-500 hover:text-gray-800 pl-0">
          <ArrowLeft size={16} className="mr-1" /> 返回用户列表
        </Button>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-6">
            <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center text-primary text-2xl font-bold border-4 border-white shadow-sm overflow-hidden">
              {(detail?.avatar_url || user.avatar_url) ? (
                <img src={detail?.avatar_url || user.avatar_url} alt={user.username} className="w-full h-full object-cover" />
              ) : (
                user.username.charAt(0).toUpperCase()
              )}
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-3">
                {user.username}
                <Tag color={user.role === UserRole.ADMIN ? 'orange' : 'blue'}>
                  {user.role === UserRole.ADMIN ? '管理员' : '普通用户'}
                </Tag>
                <Tag color={statusColor}>
                  {statusLabel}
                </Tag>
              </h2>
              <div className="text-gray-500 mt-2 flex items-center gap-6 text-sm">
                <span className="flex items-center gap-1"><Shield size={14} /> ID: {user.id}</span>
                <span className="flex items-center gap-1">📧 {user.email}</span>
                <span className="flex items-center gap-1"><Clock size={14} /> 上次登录: {lastLoginText}</span>
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
            <p className="text-xs text-gray-500 mt-2 text-center">当前用户已创建 {usedQuota} 个项目，剩余可创建 {remainingQuota} 个。</p>
          </Card>

          {/* Login History */}
          <Card title="近期登录历史">
            {(() => {
              const all = detail?.login_history || [];
              const total = all.length;
              const totalPages = Math.max(Math.ceil(total / loginPageSize), 1);
              const safePage = Math.min(Math.max(loginPage, 1), totalPages);
              const start = (safePage - 1) * loginPageSize;
              const pageItems = all.slice(start, start + loginPageSize);

              return (
                <>
                  <div className="space-y-4">
                    {pageItems.map((log) => {
                      const loginTime = new Date(log.login_time);
                      const timeText = Number.isNaN(loginTime.getTime()) ? log.login_time : loginTime.toLocaleString();
                      const isFailed = (log.login_status || '').toLowerCase() === 'failed';
                      return (
                        <div key={log.login_id} className="flex items-start gap-3 text-sm border-b border-gray-50 pb-3 last:border-0 last:pb-0">
                          <div className={`w-2 h-2 mt-1.5 rounded-full ${isFailed ? 'bg-red-500' : 'bg-green-500'}`}></div>
                          <div className="flex-1">
                            <div className="flex justify-between">
                              <span className="font-medium text-gray-700">{log.ip_address}</span>
                              <span className="text-gray-400 text-xs">{timeText}</span>
                            </div>
                            <div className="flex items-center gap-2 text-gray-500 text-xs mt-1">
                              <span className="flex items-center gap-0.5"><MapPin size={10} /> {log.login_status === 'success' ? '成功' : 
                               log.login_status === 'forced_logout' ? '已登出' : 
                               log.login_status === 'expired' ? '已过期' : '失败'}</span>
                              <span className="flex items-center gap-0.5 max-w-[220px] truncate" title={log.user_agent || 'Unknown'}>
                                <Globe size={10} /> {log.user_agent || 'Unknown'}
                              </span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                    {total === 0 && (
                      <div className="py-2 text-center text-gray-400 text-sm">暂无登录历史</div>
                    )}
                  </div>

                  {total > 0 && totalPages > 1 && (
                    <div className="flex items-center justify-between pt-4 border-t border-gray-50 mt-4">
                      <span className="text-xs text-gray-400">第 {safePage} / {totalPages} 页</span>
                      <div className="flex gap-2">
                        <Button
                          variant="default"
                          className="h-8 px-3 text-xs"
                          disabled={safePage <= 1}
                          onClick={() => setLoginPage((p) => Math.max(p - 1, 1))}
                        >
                          上一页
                        </Button>
                        <Button
                          variant="default"
                          className="h-8 px-3 text-xs"
                          disabled={safePage >= totalPages}
                          onClick={() => setLoginPage((p) => p + 1)}
                        >
                          下一页
                        </Button>
                      </div>
                    </div>
                  )}
                </>
              );
            })()}
          </Card>
        </div>

        {/* Right Column: Project List */}
        <div className="lg:col-span-2">
          <Card title={`已创建的项目 (${detail?.project_count ?? projects.length})`}>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[900px] table-fixed text-left text-sm">
                <thead className="bg-gray-50 border-b border-gray-100">
                  <tr>
                    <th className="px-4 py-3 font-medium text-gray-600 w-72">项目名称</th>
                    <th className="px-4 py-3 font-medium text-gray-600 w-28 whitespace-nowrap">类型</th>
                    <th className="px-4 py-3 font-medium text-gray-600 w-24 whitespace-nowrap">状态</th>
                    <th className="px-4 py-3 font-medium text-gray-600 w-44 whitespace-nowrap">创建时间</th>
                    <th className="px-4 py-3 font-medium text-gray-600">描述</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {projects.map((project) => (
                    <tr key={project.id} className="hover:bg-gray-50/50">
                      <td className="px-4 py-3 font-medium text-gray-800">
                        <div className="flex items-center gap-2 min-w-0">
                          <span className="truncate" title={project.name}>{project.name}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-gray-600 whitespace-nowrap">{project.type}</td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <Tag color={project.status === 'active' ? 'green' : project.status === 'error' ? 'red' : 'blue'}>
                          {project.status === 'active' ? '运行中' : project.status === 'error' ? '异常' : '部署中'}
                        </Tag>
                      </td>
                      <td className="px-4 py-3 text-gray-500 whitespace-nowrap truncate" title={String(project.createdAt ?? '')}>
                        {formatDateTime(project.createdAt)}
                      </td>
                      <td className="px-4 py-3 text-gray-500">
                        <div className="truncate" title={project.description}>{project.description}</div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {projects.length === 0 && (
                <div className="py-8 text-center text-gray-400">该用户暂未创建任何数据库项目</div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};