import React, { useState } from 'react';
import { Button, Input } from '../components/UI';
import { UserRole } from '../types';
import { authApi } from '../api/auth'; // 引入 API 模块

interface LoginProps {
  onLogin: (role: UserRole, username: string, avatar_url?: string) => void;
}

export const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [verificationCode, setVerificationCode] = useState('');

  const [isRegister, setIsRegister] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [countdown, setCountdown] = useState(0);

  // 发送验证码逻辑
  const handleSendCode = async () => {
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
      alert('验证码已发送，请查收邮件');

      // 开启60秒倒计时
      setCountdown(60);
      const timer = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } catch (err: any) {
      setError(err.message || '发送验证码失败');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (isRegister) {
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

        alert(`注册成功！欢迎，${username}。请直接登录。`);
        setIsRegister(false);
        setPassword('');
        setConfirmPassword('');
        setVerificationCode('');
      } catch (err: any) {
        setError(err.message || '注册失败');
      } finally {
        setIsLoading(false);
      }

    } else {
      // --- 登录逻辑 ---
      if (!username || !password) {
        setError('请输入用户名和密码');
        return;
      }

      setIsLoading(true);
      try {
        const response = await authApi.login({ username, password });

        if (response.code !== 200) {
          throw new Error(response.message || '登录失败');
        }

        localStorage.setItem('access_token', response.data.access_token);

        const userData = response.data.user;
        const role = userData.is_admin ? UserRole.ADMIN : UserRole.USER;

        onLogin(role, userData.username, userData.avatar_url);
      } catch (err: any) {
        setError(err.message || '登录失败，请检查用户名或密码');
      } finally {
        setIsLoading(false);
      }
    }
  };

  const toggleMode = () => {
    setIsRegister(!isRegister);
    setError('');
    if (!isRegister) {
      setEmail('');
      setConfirmPassword('');
      setVerificationCode('');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#f0f2f5] bg-[url('https://gw.alipayobjects.com/zos/rmsportal/TVYTbAXWheQpRcWDaDMu.svg')] bg-center bg-no-repeat bg-contain">
      <div className="w-full max-w-sm bg-white p-8 rounded-xl shadow-lg animate-in fade-in zoom-in duration-300">
        <div className="text-center mb-8">
          {/* 修改: 增大Logo尺寸 (w-16 -> w-24) */}
          <img
            src="public/database-logo.svg"
            alt="AutoDB Logo"
            className="w-24 h-24 mx-auto mb-4 object-contain hover:scale-105 transition-transform duration-300"
          />
          <h1 className="text-2xl font-bold text-gray-800">AutoDB</h1>
          <p className="text-gray-500 mt-2 text-sm">基于大模型多智能体的数据库自动部署平台</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="用户名"
            value={username}
            onChange={e => setUsername(e.target.value)}
            placeholder={isRegister ? "设置用户名" : "输入用户名或邮箱"}
            disabled={isLoading}
          />

          {isRegister && (
            <div className="animate-in fade-in slide-in-from-top-2 duration-200 space-y-4">
              <Input
                label="邮箱地址"
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
                  onClick={handleSendCode}
                  disabled={countdown > 0 || isLoading}
                >
                  {countdown > 0 ? `${countdown}s` : '发送验证码'}
                </Button>
              </div>
            </div>
          )}

          <Input
            label="密码"
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder={isRegister ? "设置密码" : "输入密码"}
            disabled={isLoading}
          />

          {isRegister && (
            <div className="animate-in fade-in slide-in-from-top-2 duration-200">
              <Input
                label="确认密码"
                type="password"
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                placeholder="再次输入密码"
                disabled={isLoading}
              />
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
            {isRegister ? '注册并登录' : '登录'}
          </Button>

          <div className="flex justify-between text-sm mt-4">
            <span className="text-primary cursor-pointer hover:underline" onClick={!isLoading ? toggleMode : undefined}>
              {isRegister ? '已有账号？去登录' : '注册新账号'}
            </span>
            {!isRegister && <span className="text-gray-400 cursor-not-allowed" title="请联系管理员重置">忘记密码？</span>}
          </div>
        </form>

        <div className="mt-8 text-center text-xs text-gray-400">
          Copyright © 2025 AutoDB
        </div>
      </div>
    </div>
  );
};