import React, { useState, useEffect, useRef } from 'react';
import { Card, Button, Input, Tag, Modal } from '../components/UI.tsx';
import { Save, User as UserIcon, Loader2, Edit2, Camera, Shield, Mail, History, Globe, MapPin, X, Check, UploadCloud, Image as ImageIcon } from 'lucide-react';
import {
  getUserProfile,
  updateUsername,
  updateAvatar,
  updatePassword,
  sendEmailVerificationCode,
  confirmUpdateEmail,
  getLoginHistory,
  UserMe,
  LoginHistoryItem
} from '../api/user.ts';

interface ProfileProps {
  // 接收可选的 user prop 用于初始展示，但页面主要依赖内部 API 获取的数据
  user?: { name: string; role: any } | null;
  // 新增：登出回调，用于修改敏感信息后强制重新登录
  onLogout?: () => void;
}

export const Profile: React.FC<ProfileProps> = ({ onLogout }) => {
  const [activeTab, setActiveTab] = useState<'security' | 'email' | 'history'>('security');

  // --- 数据状态 ---
  const [userProfile, setUserProfile] = useState<UserMe | null>(null);
  const [loadingProfile, setLoadingProfile] = useState(false);

  // --- 编辑状态 ---
  const [isEditingName, setIsEditingName] = useState(false);
  const [editNameValue, setEditNameValue] = useState('');

  // 头像上传相关状态
  const [isAvatarModalOpen, setIsAvatarModalOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // --- 登录历史状态 ---
  const [historyData, setHistoryData] = useState<LoginHistoryItem[]>([]);
  const [historyTotal, setHistoryTotal] = useState(0);
  const [historyPage, setHistoryPage] = useState(1);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // --- 表单状态 ---
  const [loadingForm, setLoadingForm] = useState(false);
  // 密码
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPasswordInput, setConfirmPasswordInput] = useState('');
  // 邮箱
  const [newEmail, setNewEmail] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [emailStep, setEmailStep] = useState(1);

  // 初始化加载
  useEffect(() => {
    fetchUserProfile();
  }, []);

  // 切换到历史 Tab 时加载数据
  useEffect(() => {
    if (activeTab === 'history') {
      fetchLoginHistory(1);
    }
  }, [activeTab]);

  const fetchUserProfile = async () => {
    setLoadingProfile(true);
    try {
      const res = await getUserProfile() as any;
      // 修正：后端直接返回 UserMe 对象，无 code/data 包装
      if (res && res.user_id) {
        setUserProfile(res);
        setEditNameValue(res.username);
      } else if (res.code === 200) {
        // 兼容旧的包装格式
        setUserProfile(res.data);
        setEditNameValue(res.data.username);
      }
    } catch (error) {
      console.error("Failed to load profile", error);
    } finally {
      setLoadingProfile(false);
    }
  };

  const fetchLoginHistory = async (page: number) => {
    setLoadingHistory(true);
    try {
      const res = await getLoginHistory(page, 10) as any;
      // 修正：后端直接返回分页对象 { total, page, items: [] }
      if (res && Array.isArray(res.items)) {
        setHistoryData(res.items);
        setHistoryTotal(res.total);
        setHistoryPage(page);
      } else if (res.code === 200 && res.data && Array.isArray(res.data.items)) {
        // 兼容旧的包装格式
        setHistoryData(res.data.items);
        setHistoryTotal(res.data.total);
        setHistoryPage(page);
      }
    } catch (error) {
      console.error("Failed to load history", error);
    } finally {
      setLoadingHistory(false);
    }
  };

  // --- Handlers: 基本信息 ---

  const handleUpdateUsername = async () => {
    if (!editNameValue.trim()) return;
    try {
      const res = await updateUsername(editNameValue) as any;
      // 修正：PATCH /user/me 返回 UserMe 对象
      const updatedUser = res.username ? res : res.data;
      if (updatedUser && updatedUser.username) {
        setUserProfile(prev => prev ? { ...prev, username: updatedUser.username } : null);
        setIsEditingName(false);
        alert('用户名修改成功！');
      }
    } catch (error: any) {
      // 优先从 error.response.data.detail 获取详细信息，如果不可用则使用 error.message
      const errorMsg = error.response?.data?.detail || error.message || '';

      // 针对 "Username has been registered" 进行本地化处理
      if (typeof errorMsg === 'string' && errorMsg.includes('Username has been registered')) {
        alert('修改失败：该用户名已被注册，请尝试其他用户名。');
      } else {
        alert(typeof errorMsg === 'string' ? errorMsg : '更新用户名失败');
      }
    }
  };

  // 处理文件选择
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // 限制文件大小 (例如 2MB)
      if (file.size > 2 * 1024 * 1024) {
        alert('图片大小不能超过 2MB');
        return;
      }
      setSelectedFile(file);
      // 创建预览 URL
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviewUrl(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  // 触发文件选择器
  const handleSelectFileClick = () => {
    fileInputRef.current?.click();
  };

  // 重置头像模态框状态
  const closeAvatarModal = () => {
    setIsAvatarModalOpen(false);
    setSelectedFile(null);
    setPreviewUrl('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleUpdateAvatar = async () => {
    if (!previewUrl) {
      alert('请先选择图片');
      return;
    }

    // 注意：在实际生产环境中，此处应该先将 selectedFile 上传至 OSS/S3 服务器
    // 获取返回的 URL 后再调用 updateAvatar(url)。
    // 由于当前没有上传接口，我们将使用 Base64 字符串模拟 URL 进行更新。
    // 这在数据量较小时（如小头像）通常也能工作，取决于后端数据库字段长度限制。

    try {
      const res = await updateAvatar(previewUrl) as any;
      // 修正：POST /user/me/avatar 返回 UserUpdateAvatar 对象
      const updatedData = res.avatar_url ? res : res.data;
      if (updatedData && updatedData.avatar_url) {
        setUserProfile(prev => prev ? { ...prev, avatar_url: updatedData.avatar_url } : null);
        alert('头像更新成功！');
        closeAvatarModal();
      }
    } catch (error: any) {
      alert(error.message || '更新头像失败');
    }
  };

  // --- Handlers: 安全设置 ---

  const performLogout = () => {
    // 如果父组件传入了 onLogout，则使用它（推荐）
    if (onLogout) {
      onLogout();
    } else {
      // 否则执行本地强制登出：清除 Token 并刷新页面
      localStorage.removeItem('access_token');
      window.location.reload();
    }
  };

  const handleUpdatePassword = async () => {
    if (!currentPassword || !newPassword || !confirmPasswordInput) {
      alert('请填写所有密码字段');
      return;
    }
    if (newPassword !== confirmPasswordInput) {
      alert('新密码与确认密码不一致');
      return;
    }

    setLoadingForm(true);
    try {
      await updatePassword({
        old_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPasswordInput
      });
      alert('密码修改成功，请重新登录');
      performLogout(); // 强制登出
    } catch (error: any) {
      alert(error.message || '修改密码失败');
    } finally {
      setLoadingForm(false);
    }
  };

  const handleSendCode = async () => {
    if (!newEmail) {
      alert('请输入邮箱地址');
      return;
    }
    setLoadingForm(true);
    try {
      await sendEmailVerificationCode(newEmail);
      alert(`验证码已发送至 ${newEmail}`);
      setEmailStep(2);
    } catch (error: any) {
      alert(error.message || '发送失败');
    } finally {
      setLoadingForm(false);
    }
  };

  const handleBindEmail = async () => {
    if (!verificationCode) {
      alert('请输入验证码');
      return;
    }
    setLoadingForm(true);
    try {
      const res = await confirmUpdateEmail({ new_email: newEmail, code: verificationCode }) as any;
      // 修正：PUT /user/me/email 返回 UserMe 对象
      const updatedUser = res.email ? res : res.data;
      if (updatedUser && updatedUser.email) {
        alert('邮箱绑定成功，请使用新邮箱重新登录！');
        performLogout(); // 强制登出
      }
    } catch (error: any) {
      alert(error.message || '绑定失败');
    } finally {
      setLoadingForm(false);
    }
  };

  if (loadingProfile && !userProfile) {
    return <div className="flex h-full items-center justify-center"><Loader2 className="animate-spin text-primary" size={32} /></div>;
  }

  return (
    <div className="p-8 max-w-6xl mx-auto h-full overflow-y-auto">
      <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
        <Shield className="text-primary" /> 个人账户设置
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        {/* Left: User Info Card (4 cols) */}
        <div className="lg:col-span-4 space-y-6">
          <Card className="text-center h-full relative overflow-visible">
            {/* Avatar Section */}
            <div className="relative w-24 h-24 mx-auto mb-4 group">
              <div className="w-full h-full bg-blue-100 rounded-full flex items-center justify-center text-primary border-4 border-white shadow-sm overflow-hidden">
                {userProfile?.avatar_url ? (
                  <img src={userProfile.avatar_url} alt="Avatar" className="w-full h-full object-cover" />
                ) : (
                  <UserIcon size={48} />
                )}
              </div>
              <button
                onClick={() => setIsAvatarModalOpen(true)}
                className="absolute bottom-0 right-0 p-1.5 bg-white border border-gray-200 rounded-full shadow-md text-gray-500 hover:text-primary transition-colors"
                title="修改头像"
              >
                <Camera size={14} />
              </button>
            </div>

            {/* Username Section */}
            <div className="mb-2 flex items-center justify-center gap-2 h-8">
              {isEditingName ? (
                <div className="flex items-center gap-1 animate-in fade-in zoom-in duration-200">
                  <input
                    className="border border-primary rounded px-2 py-1 text-sm w-32 focus:outline-none"
                    value={editNameValue}
                    onChange={(e) => setEditNameValue(e.target.value)}
                    autoFocus
                  />
                  <button onClick={handleUpdateUsername} className="p-1 text-green-600 hover:bg-green-50 rounded"><Check size={16} /></button>
                  <button onClick={() => { setIsEditingName(false); setEditNameValue(userProfile?.username || ''); }} className="p-1 text-red-600 hover:bg-red-50 rounded"><X size={16} /></button>
                </div>
              ) : (
                <>
                  <h3 className="text-lg font-bold text-gray-800">{userProfile?.username}</h3>
                  <button onClick={() => setIsEditingName(true)} className="text-gray-400 hover:text-primary"><Edit2 size={14} /></button>
                </>
              )}
            </div>

            <p className="text-gray-500 text-sm mb-4 break-all">{userProfile?.email}</p>

            <div className="flex justify-center gap-2 mb-6">
              <Tag color={userProfile?.is_admin ? 'orange' : 'blue'}>
                {userProfile?.is_admin ? '管理员' : '普通用户'}
              </Tag>
              <Tag color={userProfile?.status === 'normal' ? 'green' : 'red'}>
                {userProfile?.status === 'normal' ? '状态正常' : '异常'}
              </Tag>
            </div>

            <div className="border-t border-gray-100 pt-6 text-left space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-500">项目额度</span>
                  {/* 修复：添加默认值 0，防止 userProfile 未加载时显示空 */}
                  <span className="font-medium text-gray-800">
                    {userProfile?.used_databases ?? 0} / {userProfile?.max_databases ?? 0}
                  </span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-1.5">
                  <div
                    className="bg-primary h-1.5 rounded-full"
                    style={{ width: `${Math.min(((userProfile?.used_databases || 0) / (userProfile?.max_databases || 1)) * 100, 100)}%` }}
                  ></div>
                </div>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">注册时间</span>
                {/* 修复：对 userProfile.created_at 进行存在性检查，避免 Invalid Date */}
                <span className="text-gray-800">
                  {userProfile?.created_at ? new Date(userProfile.created_at).toLocaleDateString() : '-'}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">上次登录</span>
                {/* 修复：对 userProfile.last_login_at 进行存在性检查 */}
                <span className="text-gray-800">
                  {userProfile?.last_login_at ? new Date(userProfile.last_login_at).toLocaleString() : '从未登录'}
                </span>
              </div>
            </div>
          </Card>
        </div>

        {/* Right: Tabs & Content (8 cols) */}
        <div className="lg:col-span-8">
          <Card className="min-h-[500px]">
            {/* Tabs Header */}
            <div className="flex border-b border-gray-100 mb-6">
              {[
                { id: 'security', label: '密码修改', icon: <Shield size={16} /> },
                { id: 'email', label: '邮箱绑定', icon: <Mail size={16} /> },
                { id: 'history', label: '登录历史', icon: <History size={16} /> },
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`px-6 py-3 text-sm font-medium border-b-2 transition-all flex items-center gap-2 ${activeTab === tab.id
                    ? 'border-primary text-primary bg-blue-50/50'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                    }`}
                >
                  {tab.icon} {tab.label}
                </button>
              ))}
            </div>

            {/* Tab: Security */}
            {activeTab === 'security' && (
              <div className="max-w-md mx-auto py-4 animate-in fade-in slide-in-from-right-4 duration-300">
                <div className="space-y-5">
                  <Input
                    label="当前密码"
                    type="password"
                    value={currentPassword}
                    onChange={e => setCurrentPassword(e.target.value)}
                    placeholder="请输入旧密码"
                  />
                  <Input
                    label="新密码"
                    type="password"
                    value={newPassword}
                    onChange={e => setNewPassword(e.target.value)}
                    placeholder="6-50位字符"
                  />
                  <Input
                    label="确认新密码"
                    type="password"
                    value={confirmPasswordInput}
                    onChange={e => setConfirmPasswordInput(e.target.value)}
                    placeholder="再次输入新密码"
                  />
                  <div className="pt-4 flex justify-end">
                    <Button
                      variant="primary"
                      icon={loadingForm ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                      onClick={handleUpdatePassword}
                      disabled={loadingForm}
                    >
                      {loadingForm ? '更新中...' : '保存更改'}
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {/* Tab: Email */}
            {activeTab === 'email' && (
              <div className="max-w-md mx-auto py-4 animate-in fade-in slide-in-from-right-4 duration-300">
                {emailStep === 1 ? (
                  <div className="space-y-5">
                    <div className="bg-blue-50 p-4 rounded-lg text-sm text-blue-800 mb-4">
                      当前绑定邮箱：<span className="font-bold">{userProfile?.email}</span>
                      <p className="mt-1 opacity-80 text-xs">更换邮箱后，您需要使用新邮箱进行登录。</p>
                    </div>
                    <Input
                      label="新邮箱地址"
                      placeholder="example@email.com"
                      value={newEmail}
                      onChange={e => setNewEmail(e.target.value)}
                    />
                    <div className="pt-4 flex justify-end">
                      <Button
                        variant="primary"
                        onClick={handleSendCode}
                        disabled={loadingForm}
                        icon={loadingForm ? <Loader2 size={16} className="animate-spin" /> : <Mail size={16} />}
                      >
                        {loadingForm ? '发送中...' : '发送验证码'}
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-5">
                    <div className="text-center mb-6">
                      <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center text-green-600 mx-auto mb-2">
                        <Mail size={24} />
                      </div>
                      <h4 className="font-bold text-gray-800">验证您的邮箱</h4>
                      <p className="text-sm text-gray-500 mt-1">验证码已发送至 {newEmail}</p>
                    </div>
                    <Input
                      label="6位验证码"
                      placeholder="请输入验证码"
                      value={verificationCode}
                      onChange={e => setVerificationCode(e.target.value)}
                      className="text-center tracking-widest text-lg"
                      maxLength={6}
                    />
                    <div className="pt-4 flex justify-between items-center">
                      <button
                        onClick={() => setEmailStep(1)}
                        className="text-sm text-gray-500 hover:text-gray-800"
                        disabled={loadingForm}
                      >
                        返回修改邮箱
                      </button>
                      <Button
                        variant="primary"
                        onClick={handleBindEmail}
                        disabled={loadingForm}
                        icon={loadingForm ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />}
                      >
                        {loadingForm ? '验证并绑定...' : '确认绑定'}
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Tab: History */}
            {activeTab === 'history' && (
              <div className="animate-in fade-in slide-in-from-right-4 duration-300">
                {loadingHistory ? (
                  <div className="flex justify-center py-12"><Loader2 className="animate-spin text-gray-400" size={32} /></div>
                ) : (
                  <>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-sm">
                        <thead className="bg-gray-50 border-b border-gray-100">
                          <tr>
                            <th className="px-4 py-3 font-medium text-gray-600">时间</th>
                            <th className="px-4 py-3 font-medium text-gray-600">IP 地址</th>
                            <th className="px-4 py-3 font-medium text-gray-600">设备信息</th>
                            <th className="px-4 py-3 font-medium text-gray-600 text-right">状态</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          {historyData.map((log) => (
                            <tr key={log.login_id} className="hover:bg-gray-50/50">
                              <td className="px-4 py-3 text-gray-700 whitespace-nowrap">
                                {new Date(log.login_time).toLocaleString()}
                              </td>
                              <td className="px-4 py-3 font-mono text-gray-600 text-xs">
                                {log.ip_address}
                              </td>
                              <td className="px-4 py-3 text-gray-500 max-w-xs truncate" title={log.user_agent || ''}>
                                {log.user_agent ? (
                                  <span className="flex items-center gap-1"><Globe size={12} /> {log.user_agent.split('(')[0]}</span>
                                ) : '-'}
                              </td>
                              <td className="px-4 py-3 text-right">
                                <Tag color={log.login_status === 'success' ? 'green' : 'red'}>
                                  {log.login_status === 'success' ? '成功' : '失败'}
                                </Tag>
                              </td>
                            </tr>
                          ))}
                          {historyData.length === 0 && (
                            <tr><td colSpan={4} className="text-center py-8 text-gray-400">暂无登录记录</td></tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                    {/* Pagination */}
                    {historyTotal > 10 && (
                      <div className="flex justify-between items-center mt-4 border-t border-gray-100 pt-4 px-1">
                        <span className="text-xs text-gray-500">
                          显示 {(historyPage - 1) * 10 + 1} - {Math.min(historyPage * 10, historyTotal)} 共 {historyTotal} 条
                        </span>
                        <div className="flex gap-2">
                          <Button
                            variant="default"
                            className="h-8 px-3 text-xs"
                            disabled={historyPage <= 1}
                            onClick={() => fetchLoginHistory(historyPage - 1)}
                          >
                            上一页
                          </Button>
                          <Button
                            variant="default"
                            className="h-8 px-3 text-xs"
                            disabled={historyPage * 10 >= historyTotal}
                            onClick={() => fetchLoginHistory(historyPage + 1)}
                          >
                            下一页
                          </Button>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

          </Card>
        </div>
      </div>

      {/* Avatar Edit Modal (Updated for File Upload) */}
      <Modal
        isOpen={isAvatarModalOpen}
        onClose={closeAvatarModal}
        title="修改头像"
        maxWidth="max-w-md"
        footer={
          <>
            <Button onClick={closeAvatarModal}>取消</Button>
            <Button variant="primary" onClick={handleUpdateAvatar} disabled={!previewUrl}>确认上传</Button>
          </>
        }
      >
        <div className="space-y-6 py-4">
          {/* Hidden File Input */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="image/png, image/jpeg, image/jpg, image/gif"
            className="hidden"
          />

          {/* Upload Area */}
          <div
            onClick={handleSelectFileClick}
            className="border-2 border-dashed border-gray-300 rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer hover:border-primary hover:bg-blue-50 transition-all group"
          >
            {previewUrl ? (
              <div className="relative w-32 h-32 rounded-full overflow-hidden shadow-md ring-4 ring-white">
                <img src={previewUrl} alt="Preview" className="w-full h-full object-cover" />
                <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <span className="text-white text-xs font-medium">点击更换</span>
                </div>
              </div>
            ) : (
              <>
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center text-primary mb-3 group-hover:scale-110 transition-transform">
                  <UploadCloud size={32} />
                </div>
                <p className="text-sm font-medium text-gray-700">点击选择图片上传</p>
                <p className="text-xs text-gray-400 mt-1">支持 PNG, JPG, GIF (最大 2MB)</p>
              </>
            )}
          </div>

          {previewUrl && (
            <div className="text-center">
              <p className="text-xs text-green-600 flex items-center justify-center gap-1">
                <Check size={12} /> 图片已选择，点击确认上传保存
              </p>
            </div>
          )}
        </div>
      </Modal>

    </div>
  );
};