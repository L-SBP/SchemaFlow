import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar.tsx';
import { Header } from './components/Header.tsx';
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
import { UserRole, Project, User, UserStatus } from './types.ts';
import { authApi } from './api/auth.ts';
import { ProjectDTO } from './api/project.ts';

// Mock initial projects (仅保留用于 Reports 的兜底显示，Glossary 已改为真实数据)
const INITIAL_PROJECTS: Project[] = [
  { id: '1', name: '电商订单系统', type: 'MySQL', description: '处理用户订单和库存', status: 'active', createdAt: '2025-10-20' },
  { id: '2', name: 'CRM客户管理', type: 'PostgreSQL', description: '销售线索跟踪', status: 'active', createdAt: '2025-10-25' },
];

// Mock initial users
const INITIAL_USERS: User[] = [
  { id: '1001', username: 'wang_li', email: 'wang@example.com', role: UserRole.USER, status: UserStatus.BANNED, lastLogin: '2025-10-28', projectQuota: 5 },
  { id: '1002', username: 'li_guo', email: 'li@example.com', role: UserRole.USER, status: UserStatus.NORMAL, lastLogin: '2025-11-04', projectQuota: 10 },
  { id: '1003', username: 'admin_sys', email: 'admin@sys.com', role: UserRole.ADMIN, status: UserStatus.NORMAL, lastLogin: '2025-11-05', projectQuota: 99 },
  { id: '1004', username: 'user_test', email: 'test@example.com', role: UserRole.USER, status: UserStatus.NORMAL, lastLogin: '2025-11-06', projectQuota: 2 },
];

const App: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState<{ role: UserRole, name: string, avatar_url?: string } | null>(null);
  const [activePage, setActivePage] = useState('dashboard');

  // Shared State
  const [projects, setProjects] = useState<Project[]>(INITIAL_PROJECTS);
  const [users, setUsers] = useState<User[]>(INITIAL_USERS);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [viewingUser, setViewingUser] = useState<User | null>(null);

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

  // 接收 ProjectDTO 并转换为 Project
  const handleProjectSelect = (projectDTO: ProjectDTO) => {
    const project: Project = {
      id: projectDTO.project_id,
      name: projectDTO.project_name,
      type: projectDTO.project_type,
      description: projectDTO.description,
      status: projectDTO.project_status === 'initializing' ? 'deploying' : projectDTO.project_status,
      createdAt: projectDTO.created_at
    };

    setSelectedProject(project);
    setActivePage('workspace');
  };

  const handleViewUser = (user: User) => {
    setViewingUser(user);
    setActivePage('admin_user_detail');
  };

  const handleUpdateUser = (updatedUser: User) => {
    setUsers(prev => prev.map(u => u.id === updatedUser.id ? updatedUser : u));
    if (viewingUser && viewingUser.id === updatedUser.id) {
      setViewingUser(updatedUser);
    }
  };

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

  const renderContent = () => {
    if (currentUser?.role === UserRole.ADMIN) {
      switch (activePage) {
        case 'admin_users':
          return <AdminPanel users={users} onUpdateUser={handleUpdateUser} onViewUser={handleViewUser} />;
        case 'admin_user_detail':
          return viewingUser ? (
            <UserProfile
              user={viewingUser}
              onBack={() => {
                setViewingUser(null);
                setActivePage('admin_users');
              }}
            />
          ) : <AdminPanel users={users} onUpdateUser={handleUpdateUser} onViewUser={handleViewUser} />;
        case 'admin_announcements': return <AdminAnnouncements />;
        case 'admin_status': return <AdminStatus />;
        case 'profile': return <Profile user={currentUser} onLogout={handleLogout} />;
        default: return <AdminPanel users={users} onUpdateUser={handleUpdateUser} onViewUser={handleViewUser} />;
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
        // 修复: 移除 projects 属性传递，Glossary 组件将自行请求真实数据
        case 'glossary': return <Glossary />;
        case 'announcements': return <Announcements />;
        case 'profile': return <Profile user={currentUser} onLogout={handleLogout} />;
        default: return <Dashboard onProjectSelect={handleProjectSelect} />;
      }
    }
  };

  return (
    <div className="flex h-screen bg-[#f0f2f5] bg-[url('https://gw.alipayobjects.com/zos/rmsportal/TVYTbAXWheQpRcWDaDMu.svg')] bg-center bg-no-repeat bg-contain overflow-hidden">
      <Sidebar
        role={currentUser?.role || UserRole.USER}
        activePage={activePage}
        onNavigate={(page) => {
          if (page !== 'workspace') setSelectedProject(null);
          if (page !== 'admin_user_detail') setViewingUser(null);
          setActivePage(page);
        }}
      />
      <main className="flex-1 flex flex-col min-w-0">
        <Header
          user={currentUser}
          onLogout={handleLogout}
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