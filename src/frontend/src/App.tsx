import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar.tsx';
import { Header } from './components/Header.tsx';
import { ToastContainer } from './components/UI.tsx';
import { Login } from './pages/Login.tsx';
import { Dashboard } from './pages/Dashboard.tsx';
import { Workspace } from './pages/Workspace.tsx';
import { AdminPanel } from './pages/Admin.tsx';
import { AdminAnnouncements } from './pages/AdminAnnouncements.tsx';
import { UserProfile } from './pages/UserProfile.tsx';
import { Reports } from './pages/Reports.tsx';
import { Glossary } from './pages/Glossary.tsx';
import { Profile } from './pages/Profile.tsx';
import { AdminStatus } from './pages/AdminStatus.tsx';
import { Announcements } from './pages/Announcements.tsx';
import { UserRole, Project, User } from './types.ts';
import { authApi } from './api/auth.ts';
import { getUserProfile } from './api/user.ts'; // 新增：引入获取用户信息接口
import { ProjectDTO } from './api/project.ts';
import { Loader2 } from 'lucide-react'; // 新增：引入 Loading 图标

// Mock initial projects (仅保留用于 Reports 的兜底显示)
const INITIAL_PROJECTS: Project[] = [
  { id: '1', name: '电商订单系统', type: 'MySQL', description: '处理用户订单和库存', status: 'active', createdAt: '2025-10-20' },
  { id: '2', name: 'CRM客户管理', type: 'PostgreSQL', description: '销售线索跟踪', status: 'active', createdAt: '2025-10-25' },
];

const App: React.FC = () => {
  // 新增：isLoading 状态，用于在检查 Token 时显示加载动画，防止登录页闪烁
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState<{ role: UserRole, name: string, avatar_url?: string } | null>(null);
  const [activePage, setActivePage] = useState('dashboard');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // Shared State
  const [projects, setProjects] = useState<Project[]>(INITIAL_PROJECTS);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [viewingUser, setViewingUser] = useState<User | null>(null);

  // --- 新增：初始化时检查登录状态 ---
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token');

      // 如果没有 Token，直接结束加载，显示登录页
      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        // 有 Token，尝试获取用户信息来验证 Token 是否过期
        // 注意：这里复用了 Profile.tsx 中的数据处理逻辑
        const res = await getUserProfile() as any;

        let userData = null;
        // 兼容后端可能返回直接对象或 { code: 200, data: ... } 的结构
        if (res && res.user_id) {
          userData = res;
        } else if (res && res.data && res.data.user_id) {
          userData = res.data;
        }

        if (userData) {
          // Token 有效，恢复登录状态
          const role = userData.is_admin ? UserRole.ADMIN : UserRole.USER;
          setCurrentUser({
            role,
            name: userData.username,
            avatar_url: userData.avatar_url
          });
          setIsAuthenticated(true);

          // 根据角色恢复默认页面
          setActivePage(role === UserRole.ADMIN ? 'admin_users' : 'dashboard');
        } else {
          throw new Error('Invalid user data');
        }
      } catch (error) {
        console.warn('Auto login failed (Token expired or invalid):', error);
        // Token 无效，清除它
        localStorage.removeItem('access_token');
        setIsAuthenticated(false);
        setCurrentUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const handleLogin = (role: UserRole, username: string, avatar_url?: string) => {
    setIsAuthenticated(true);
    setCurrentUser({ role, name: username, avatar_url });
    setActivePage(role === UserRole.ADMIN ? 'admin_users' : 'dashboard');
  };

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.warn('Logout API failed:', error);
    } finally {
      localStorage.removeItem('access_token');
      setIsAuthenticated(false);
      setCurrentUser(null);
      setSelectedProject(null);
      setViewingUser(null);
      setActivePage('dashboard');
    }
  };

  const handleProjectSelect = (projectDTO: ProjectDTO) => {
    const dbTypeMap: Record<string, 'MySQL' | 'PostgreSQL' | 'SQLite'> = {
      'mysql': 'MySQL',
      'postgresql': 'PostgreSQL',
      'sqlite': 'SQLite'
    };

    const statusMap: Record<string, 'active' | 'deploying' | 'error' | 'deleted'> = {
      'initializing': 'deploying',
      'pending_confirmation': 'deploying',
      'active': 'active',
      'deleted': 'deleted',
      'error': 'error'
    };

    const project: Project = {
      id: projectDTO.project_id.toString(),
      name: projectDTO.project_name,
      type: dbTypeMap[projectDTO.db_type.toLowerCase()] || 'MySQL',
      description: projectDTO.description,
      status: statusMap[projectDTO.project_status.toLowerCase()] || 'active',
      createdAt: projectDTO.created_at
    };

    setSelectedProject(project);
    setActivePage('workspace');
  };

  const handleViewUser = (user: User) => {
    setViewingUser(user);
    setActivePage('admin_user_detail');
  };

  // --- 渲染逻辑 ---

  // 1. 如果正在检查 Token，显示全局 Loading
  if (isLoading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-[#f0f2f5]">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="animate-spin text-primary" size={48} />
          <p className="text-gray-500 text-sm">正在恢复会话...</p>
        </div>
      </div>
    );
  }

  // 2. 如果未认证，显示登录页
  if (!isAuthenticated) {
    return (
      <>
        <ToastContainer />
        <Login onLogin={handleLogin} />
      </>
    );
  }

  // 3. 已认证，渲染主布局
  const renderContent = () => {
    if (currentUser?.role === UserRole.ADMIN) {
      switch (activePage) {
        case 'admin_users':
          return <AdminPanel onViewUser={handleViewUser} />;
        case 'admin_user_detail':
          return viewingUser ? (
            <UserProfile
              user={viewingUser}
              onBack={() => {
                setViewingUser(null);
                setActivePage('admin_users');
              }}
            />
          ) : <AdminPanel onViewUser={handleViewUser} />;
        case 'admin_announcements': return <AdminAnnouncements />;
        case 'admin_status': return <AdminStatus />;
        case 'profile': return <Profile user={currentUser} onLogout={handleLogout} />;
        default: return <AdminPanel onViewUser={handleViewUser} />;
      }
    } else {
      if (activePage === 'workspace' && selectedProject) {
        return <Workspace project={selectedProject} onBack={() => {
          setSelectedProject(null);
          setActivePage('dashboard');
        }} />;
      }

      switch (activePage) {
        case 'dashboard': return <Dashboard onProjectSelect={handleProjectSelect} />;
        case 'reports': return <Reports projects={projects} />;
        case 'glossary': return <Glossary />;
        case 'announcements': return <Announcements />;
        case 'profile': return <Profile user={currentUser} onLogout={handleLogout} />;
        default: return <Dashboard onProjectSelect={handleProjectSelect} />;
      }
    }
  };

  return (
    <div className="flex h-screen bg-[#f0f2f5] bg-[url('https://gw.alipayobjects.com/zos/rmsportal/TVYTbAXWheQpRcWDaDMu.svg')] bg-center bg-no-repeat bg-contain overflow-hidden">
      <ToastContainer />

      <Sidebar
        role={currentUser?.role || UserRole.USER}
        activePage={activePage}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        onNavigate={(page) => {
          if (page !== 'workspace') setSelectedProject(null);
          if (page !== 'admin_user_detail') setViewingUser(null);
          setActivePage(page);
          setIsSidebarOpen(false);
        }}
      />
      <main className="flex-1 flex flex-col min-w-0">
        <Header
          user={currentUser}
          onLogout={handleLogout}
          onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
          onNavigate={(page) => {
            setSelectedProject(null);
            setViewingUser(null);
            setActivePage(page);
          }}
        />
        <div className="flex-1 overflow-auto relative">
          {renderContent()}
        </div>
      </main>
    </div>
  );
};

export default App;