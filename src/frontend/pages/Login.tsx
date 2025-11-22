import React, { useState } from 'react';
import { Button, Input } from '../components/UI';
import { UserRole } from '../types';

interface LoginProps {
  onLogin: (role: UserRole, username: string) => void;
}

export const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [username, setUsername] = useState('user');
  const [password, setPassword] = useState('');
  const [isRegister, setIsRegister] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Mock Login Logic
    const role = username.includes('admin') ? UserRole.ADMIN : UserRole.USER;
    onLogin(role, username);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#f0f2f5] bg-[url('https://gw.alipayobjects.com/zos/rmsportal/TVYTbAXWheQpRcWDaDMu.svg')] bg-center bg-no-repeat bg-contain">
      <div className="w-full max-w-sm bg-white p-8 rounded-xl shadow-lg animate-in fade-in zoom-in duration-300">
        <div className="text-center mb-8">
          <div className="w-12 h-12 bg-primary rounded-lg mx-auto flex items-center justify-center text-white font-bold text-xl mb-3">AI</div>
          <h1 className="text-2xl font-bold text-gray-800">DB Master</h1>
          <p className="text-gray-500 mt-2 text-sm">基于大模型多智能体的数据库自动部署平台</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <Input 
            label="用户名" 
            value={username} 
            onChange={e => setUsername(e.target.value)} 
            placeholder="输入 'admin' 进入管理员后台" 
          />
          <Input 
            label="密码" 
            type="password" 
            value={password} 
            onChange={e => setPassword(e.target.value)} 
            placeholder="任意密码"
          />
          
          <Button variant="primary" className="w-full h-10 text-base" type="submit">
            {isRegister ? '注册并登录' : '登录'}
          </Button>

          <div className="flex justify-between text-sm mt-4">
            <span className="text-primary cursor-pointer hover:underline" onClick={() => setIsRegister(!isRegister)}>
              {isRegister ? '已有账号？去登录' : '注册新账号'}
            </span>
            <span className="text-gray-400 cursor-not-allowed">忘记密码？</span>
          </div>
        </form>
        
        <div className="mt-8 text-center text-xs text-gray-400">
          Copyright © 2025 DB Master Tech
        </div>
      </div>
    </div>
  );
};