import React, { useState } from 'react';
import { Card, Button, Input, Tag } from '../components/UI.tsx';
import { Save, User as UserIcon, Loader2 } from 'lucide-react';
import { UserRole } from '../types.ts';
import { updatePassword, sendEmailVerificationCode, bindEmail } from '../api/user';

interface ProfileProps {
  user: { name: string; role: UserRole } | null;
}

export const Profile: React.FC<ProfileProps> = ({ user }) => {
  const [activeTab, setActiveTab] = useState<'security' | 'email'>('security');
  const [loading, setLoading] = useState(false);

  // Security Form State
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Email Form State
  const [newEmail, setNewEmail] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [step, setStep] = useState(1);

  // --- 业务逻辑处理 ---

  // 处理修改密码
  const handleUpdatePassword = async () => {
    if (!currentPassword || !newPassword || !confirmPassword) {
      alert('请填写所有密码字段');
      return;
    }
    if (newPassword !== confirmPassword) {
      alert('两次输入的新密码不一致');
      return;
    }

    try {
      setLoading(true);
      // 调用 API
      await updatePassword({ oldPassword: currentPassword, newPassword });
      alert('密码修改成功，请重新登录');
      // 清空表单
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error: any) {
      alert(error.message || '修改密码失败');
    } finally {
      setLoading(false);
    }
  };

  // 处理发送验证码
  const handleSendCode = async () => {
    if (!newEmail) {
      alert('请输入邮箱地址');
      return;
    }

    try {
      setLoading(true);
      await sendEmailVerificationCode(newEmail);
      alert(`验证码已发送至 ${newEmail} (Mock环境请直接使用: 123456)`);
      setStep(2); // 进入下一步
    } catch (error: any) {
      alert(error.message || '发送验证码失败');
    } finally {
      setLoading(false);
    }
  };

  // 处理绑定邮箱
  const handleBindEmail = async () => {
    if (!verificationCode) {
      alert('请输入验证码');
      return;
    }

    try {
      setLoading(true);
      await bindEmail({ email: newEmail, code: verificationCode });
      alert('邮箱绑定成功！');
      // 重置状态
      setStep(1);
      setNewEmail('');
      setVerificationCode('');
    } catch (error: any) {
      alert(error.message || '绑定失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto h-full overflow-y-auto">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">个人账户设置</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left: User Info Card */}
        <div className="col-span-1">
          <Card className="text-center h-full">
            <div className="w-24 h-24 bg-blue-100 rounded-full flex items-center justify-center text-primary mx-auto mb-4 border-4 border-white shadow-sm">
              <UserIcon size={48} />
            </div>
            <h3 className="text-lg font-bold text-gray-800">{user?.name}</h3>
            <p className="text-gray-500 text-sm mb-4">DB Master 用户</p>
            <Tag color={user?.role === UserRole.ADMIN ? 'orange' : 'blue'}>
              {user?.role === UserRole.ADMIN ? '系统管理员' : '普通用户'}
            </Tag>
            <div className="mt-6 pt-6 border-t border-gray-100 text-left space-y-3">
              <div className="text-sm">
                <span className="text-gray-500">注册时间：</span>
                <span className="text-gray-800 float-right">2025-10-20</span>
              </div>
              <div className="text-sm">
                <span className="text-gray-500">项目额度：</span>
                <span className="text-gray-800 float-right">5 / 10</span>
              </div>
            </div>
          </Card>
        </div>

        {/* Right: Settings Tabs */}
        <div className="col-span-2">
          <Card>
            <div className="flex border-b border-gray-100 mb-6">
              <button
                onClick={() => setActiveTab('security')}
                className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === 'security' ? 'border-primary text-primary' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
              >
                修改密码
              </button>
              <button
                onClick={() => setActiveTab('email')}
                className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === 'email' ? 'border-primary text-primary' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
              >
                绑定邮箱
              </button>
            </div>

            {activeTab === 'security' && (
              <div className="space-y-4 animate-in fade-in slide-in-from-right-2 duration-200">
                <Input
                  label="当前密码 (Mock: 123456)"
                  type="password"
                  value={currentPassword}
                  onChange={e => setCurrentPassword(e.target.value)}
                />
                <Input
                  label="新密码"
                  type="password"
                  value={newPassword}
                  onChange={e => setNewPassword(e.target.value)}
                />
                <Input
                  label="确认新密码"
                  type="password"
                  value={confirmPassword}
                  onChange={e => setConfirmPassword(e.target.value)}
                />
                <div className="pt-4 flex justify-end">
                  <Button
                    variant="primary"
                    icon={loading ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                    onClick={handleUpdatePassword}
                    disabled={loading}
                  >
                    {loading ? '更新中...' : '更新密码'}
                  </Button>
                </div>
              </div>
            )}

            {activeTab === 'email' && (
              <div className="space-y-4 animate-in fade-in slide-in-from-right-2 duration-200">
                {step === 1 ? (
                  <>
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
                        disabled={loading}
                      >
                        {loading ? '发送中...' : '发送验证码'}
                      </Button>
                    </div>
                  </>
                ) : (
                  <>
                    <p className="text-sm text-gray-600 mb-2">验证码已发送至 {newEmail}</p>
                    <Input
                      label="验证码 (Mock: 123456)"
                      placeholder="6位数字"
                      value={verificationCode}
                      onChange={e => setVerificationCode(e.target.value)}
                    />
                    <div className="pt-4 flex justify-end gap-2">
                      <Button onClick={() => setStep(1)} disabled={loading}>返回</Button>
                      <Button
                        variant="primary"
                        icon={loading ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                        onClick={handleBindEmail}
                        disabled={loading}
                      >
                        {loading ? '绑定中...' : '确认绑定'}
                      </Button>
                    </div>
                  </>
                )}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};