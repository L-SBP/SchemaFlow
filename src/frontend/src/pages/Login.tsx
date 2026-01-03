import React, { useState } from 'react';
import { Button, Input } from '../components/UI';
import { message } from '../components/UI';
import { UserRole } from '../types';
import { authApi } from '../api/auth'; // 引入 API 模块

interface LoginProps {
  onLogin: (role: UserRole, username: string, avatar_url?: string) => void;
}

export const Login: React.FC<LoginProps> = ({ onLogin }) => {
  type AuthView = 'login' | 'register' | 'forgot';

  const [authView, setAuthView] = useState<AuthView>('login');

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  // register / forgot
  const [email, setEmail] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [verificationCode, setVerificationCode] = useState('');

  // forgot: reset password by email code
  const [resetNewPassword, setResetNewPassword] = useState('');
  const [resetConfirmNewPassword, setResetConfirmNewPassword] = useState('');

  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [registerCountdown, setRegisterCountdown] = useState(0);
  const [resetCountdown, setResetCountdown] = useState(0);

  // 发送注册验证码
  const handleSendRegisterCode = async () => {
    if (!email) {
      setError('请先输入邮箱地址');
      return;
    }
    // 简单的邮箱格式校验
    if (!/\S+@\S+\.\S+/.test(email)) {
      setError('请输入有效的邮箱地址');
      return;
    }

    try {
      await authApi.sendRegisterCode(email);
      message.success('验证码已发送，请查收邮件');

      // 开启60秒倒计时
      setRegisterCountdown(60);
      const timer = setInterval(() => {
        setRegisterCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } catch (err: any) {
      // 错误已由响应拦截器自动处理并显示，这里只需记录日志
      console.error('Send register code failed:', err);
    }
  };

  // 发送重置密码验证码
  const handleSendResetCode = async () => {
    if (!email) {
      setError('请先输入邮箱地址');
      return;
    }
    if (!/\S+@\S+\.\S+/.test(email)) {
      setError('请输入有效的邮箱地址');
      return;
    }

    try {
      await authApi.sendPasswordResetCode(email);
      message.success('若账号存在，验证码已发送，请查收邮件。');

      setResetCountdown(60);
      const timer = setInterval(() => {
        setResetCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } catch (err: any) {
      // 错误已由响应拦截器自动处理并显示，这里只需记录日志
      console.error('Send reset code failed:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (authView === 'register') {
      // --- 注册逻辑 ---
      if (!username || !email || !password || !confirmPassword || !verificationCode) {
        setError('请填写所有必填项');
        return;
      }
      if (password !== confirmPassword) {
        setError('两次输入的密码不一致');
        return;
      }

      setIsLoading(true);
      try {
        await authApi.register({
          username,
          email,
          password,
          confirm_password: confirmPassword,
          verification_code: verificationCode
        });

        message.success('注册成功！请直接登录。');
        setAuthView('login');
        setPassword('');
        setConfirmPassword('');
        setVerificationCode('');
      } catch (err: any) {
        // 错误已由响应拦截器自动处理并显示，这里只需记录日志
        console.error('Register failed:', err);
      } finally {
        setIsLoading(false);
      }

    } else if (authView === 'login') {
      // --- 登录逻辑 ---
      if (!username || !password) {
        setError('请输入用户名和密码');
        return;
      }

      setIsLoading(true);
      try {
        const loginData = await authApi.login({ username, password });

        localStorage.setItem('access_token', loginData.access_token);

        const userData = loginData.user;
        const role = userData.is_admin ? UserRole.ADMIN : UserRole.USER;

        onLogin(role, userData.username, userData.avatar_url || undefined);
      } catch (err: any) {
        // 错误已由响应拦截器自动处理并显示，这里只需记录日志
        console.error('Login failed:', err);
      } finally {
        setIsLoading(false);
      }

    } else if (authView === 'forgot') {
      if (!email) {
        setError('请先输入邮箱地址');
        return;
      }
      if (!/\S+@\S+\.\S+/.test(email)) {
        setError('请输入有效的邮箱地址');
        return;
      }
      if (!verificationCode) {
        setError('请输入邮箱验证码');
        return;
      }
      if (!resetNewPassword || !resetConfirmNewPassword) {
        setError('请输入新密码并确认');
        return;
      }
      if (resetNewPassword !== resetConfirmNewPassword) {
        setError('两次输入的新密码不一致');
        return;
      }

      setIsLoading(true);
      try {
        await authApi.resetPasswordWithCode({
          email,
          verification_code: verificationCode,
          new_password: resetNewPassword,
          confirm_password: resetConfirmNewPassword,
        });
        message.success('密码已重置，请使用新密码登录。');

        setVerificationCode('');
        setResetNewPassword('');
        setResetConfirmNewPassword('');
        setAuthView('login');
      } catch (err: any) {
        // 错误已由响应拦截器自动处理并显示，这里只需记录日志
        console.error('Reset password failed:', err);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const goToLogin = () => {
    setAuthView('login');
    setError('');
  };

  const goToRegister = () => {
    setAuthView('register');
    setError('');
    setEmail('');
    setConfirmPassword('');
    setVerificationCode('');
    setRegisterCountdown(0);
  };

  const goToForgot = () => {
    setAuthView('forgot');
    setError('');
    setEmail('');
    setVerificationCode('');
    setResetNewPassword('');
    setResetConfirmNewPassword('');
    setResetCountdown(0);
  };

  return (
    <div className="min-h-screen min-h-[100dvh] flex items-center justify-center bg-[#f0f2f5] bg-[url('/background.svg')] bg-center bg-no-repeat bg-contain p-4">
      <div className="w-full max-w-sm bg-white p-6 sm:p-8 rounded-xl shadow-lg animate-in fade-in zoom-in duration-300">
        <div className="text-center mb-6 sm:mb-8">
          {/* 响应式Logo尺寸 */}
          <img
            src="/database-logo.svg"
            alt="AutoDB Logo"
            className="w-16 h-16 sm:w-24 sm:h-24 mx-auto mb-3 sm:mb-4 object-contain hover:scale-105 transition-transform duration-300"
          />
          <h1 className="text-xl sm:text-2xl font-bold text-gray-800">AutoDB</h1>
          <p className="text-gray-500 mt-2 text-xs sm:text-sm">基于大模型多智能体的数据库自动部署平台</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">

          {authView === 'login' && (
            <div className="space-y-4">
              <Input
                label="用户名"
                value={username}
                onChange={e => setUsername(e.target.value)}
                placeholder="输入用户名或邮箱"
                disabled={isLoading}
              />

              <Input
                label="密码"
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="输入密码"
                disabled={isLoading}
              />
            </div>
          )}

          {authView === 'register' && (
            <div className="space-y-4">
              <Input
                label="用户名"
                required
                value={username}
                onChange={e => setUsername(e.target.value)}
                placeholder="设置用户名"
                disabled={isLoading}
              />

              <div className="animate-in fade-in slide-in-from-top-2 duration-200 space-y-4">
                <Input
                  label="邮箱地址"
                  required
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="example@email.com"
                  disabled={isLoading}
                />

                <div className="flex items-end gap-2">
                  <div className="flex-1">
                    <Input
                      label="验证码"
                      required
                      value={verificationCode}
                      onChange={e => setVerificationCode(e.target.value)}
                      placeholder="6位验证码"
                      disabled={isLoading}
                    />
                  </div>
                  <Button
                    type="button"
                    variant="default"
                    className="mb-[2px] h-[42px] whitespace-nowrap w-28"
                    onClick={handleSendRegisterCode}
                    disabled={registerCountdown > 0 || isLoading}
                  >
                    {registerCountdown > 0 ? `${registerCountdown}s` : '发送验证码'}
                  </Button>
                </div>
              </div>

              <Input
                label="密码"
                required
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="设置密码"
                disabled={isLoading}
              />

              <div className="animate-in fade-in slide-in-from-top-2 duration-200">
                <Input
                  label="确认密码"
                  required
                  type="password"
                  value={confirmPassword}
                  onChange={e => setConfirmPassword(e.target.value)}
                  placeholder="再次输入密码"
                  disabled={isLoading}
                />
              </div>
            </div>
          )}

          {authView === 'forgot' && (
            <div className="space-y-4">
              <Input
                label="邮箱地址"
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="输入注册邮箱"
                disabled={isLoading}
              />
              <div className="flex items-end gap-2">
                <div className="flex-1">
                  <Input
                    label="验证码"
                    value={verificationCode}
                    onChange={e => setVerificationCode(e.target.value)}
                    placeholder="6位验证码"
                    disabled={isLoading}
                  />
                </div>
                <Button
                  type="button"
                  variant="default"
                  className="mb-[2px] h-[42px] whitespace-nowrap w-28"
                  onClick={handleSendResetCode}
                  disabled={resetCountdown > 0 || isLoading}
                >
                  {resetCountdown > 0 ? `${resetCountdown}s` : '发送验证码'}
                </Button>
              </div>

              <Input
                label="新密码"
                type="password"
                value={resetNewPassword}
                onChange={e => setResetNewPassword(e.target.value)}
                placeholder="设置新密码"
                disabled={isLoading}
              />

              <Input
                label="确认新密码"
                type="password"
                value={resetConfirmNewPassword}
                onChange={e => setResetConfirmNewPassword(e.target.value)}
                placeholder="再次输入新密码"
                disabled={isLoading}
              />

              <p className="text-xs text-gray-500">我们会向该邮箱发送验证码（若账号存在）。</p>
            </div>
          )}

          {error && <p className="text-red-500 text-xs">{error}</p>}

          <Button
            variant="primary"
            className="w-full h-10 text-base mt-2 flex items-center justify-center gap-2"
            type="submit"
            disabled={isLoading}
          >
            {isLoading && <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>}
            {authView === 'register' ? '注册并登录' : authView === 'forgot' ? '重置密码' : '登录'}
          </Button>

          <div className="flex justify-between text-sm mt-4">
            {authView === 'login' && (
              <>
                <span className="text-primary cursor-pointer hover:underline" onClick={!isLoading ? goToRegister : undefined}>
                  注册新账号
                </span>
                <span className="text-primary cursor-pointer hover:underline" onClick={!isLoading ? goToForgot : undefined}>
                  忘记密码？
                </span>
              </>
            )}

            {authView === 'register' && (
              <span className="text-primary cursor-pointer hover:underline" onClick={!isLoading ? goToLogin : undefined}>
                已有账号？去登录
              </span>
            )}

            {authView === 'forgot' && (
              <span className="text-primary cursor-pointer hover:underline" onClick={!isLoading ? goToLogin : undefined}>
                返回登录
              </span>
            )}
          </div>
        </form>

        <div className="mt-6 sm:mt-8 text-center text-xs text-gray-400">
          Copyright © 2025 AutoDB
        </div>
      </div>
    </div>
  );
};