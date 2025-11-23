
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
import { UserRole, Project, User, Announcement, UserStatus } from './types.ts';

// Mock initial projects
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

const MOCK_ANNOUNCEMENTS: Announcement[] = [
  { id: '1', title: '系统维护通知', content: '系统将于本周六凌晨进行升级维护，预计耗时2小时，期间服务不可用。', status: 'published', date: '2025-11-01' },
  { id: '2', title: '新功能上线：AI报表分析', content: '我们很高兴地推出新的AI驱动报表分析功能，您现在可以通过自然语言生成可视化图表。', status: 'published', date: '2025-11-05' },
  { id: '3', title: '草稿公告', content: '这是一条未发布的公告', status: 'draft', date: '2025-11-06' },
];

const App: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState<{role: UserRole, name: string} | null>(null);
  const [activePage, setActivePage] = useState('dashboard');
  
  // Shared State
  const [projects, setProjects] = useState<Project[]>(INITIAL_PROJECTS);
  const [users, setUsers] = useState<User[]>(INITIAL_USERS);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [viewingUser, setViewingUser] = useState<User | null>(null);
  const [announcements, setAnnouncements] = useState<Announcement[]>(MOCK_ANNOUNCEMENTS);

  const handleLogin = (role: UserRole, username: string) => {
    setIsAuthenticated(true);
    setCurrentUser({ role, name: username });
    setActivePage(role === UserRole.ADMIN ? 'admin_users' : 'dashboard');
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setCurrentUser(null);
    setSelectedProject(null);
    setViewingUser(null);
    setActivePage('dashboard');
  };

  const handleProjectSelect = (project: Project) => {
    setSelectedProject(project);
    setActivePage('workspace');
  };

  const handleViewUser = (user: User) => {
    setViewingUser(user);
    setActivePage('admin_user_detail');
  };

  const handleUpdateUser = (updatedUser: User) => {
    setUsers(prev => prev.map(u => u.id === updatedUser.id ? updatedUser : u));
    // Also update viewingUser if it's the same user
    if (viewingUser && viewingUser.id === updatedUser.id) {
      setViewingUser(updatedUser);
    }
  };

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

  // Render logic based on current state
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
        case 'admin_announcements': return <AdminAnnouncements announcements={announcements} setAnnouncements={setAnnouncements} />;
        case 'admin_status': return <AdminStatus />;
        case 'profile': return <Profile user={currentUser} />;
        default: return <AdminPanel users={users} onUpdateUser={handleUpdateUser} onViewUser={handleViewUser} />;
      }
    } else {
      // User View
      if (activePage === 'workspace' && selectedProject) {
        return <Workspace project={selectedProject} onBack={() => {
          setSelectedProject(null);
          setActivePage('dashboard');
        }} />;
      }
      
      switch (activePage) {
        case 'dashboard': return <Dashboard projects={projects} setProjects={setProjects} onProjectSelect={handleProjectSelect} />;
        case 'reports': return <Reports projects={projects} />;
        case 'glossary': return <Glossary projects={projects} />;
        case 'announcements': return <Announcements announcements={announcements} />;
        case 'profile': return <Profile user={currentUser} />;
        default: return <Dashboard projects={projects} setProjects={setProjects} onProjectSelect={handleProjectSelect} />;
      }
    }
  };

  return (
    <div className="flex h-screen bg-[#f0f2f5] bg-[url('https://gw.alipayobjects.com/zos/rmsportal/TVYTbAXWheQpRcWDaDMu.svg')] bg-center bg-no-repeat bg-contain overflow-hidden">
      <Sidebar 
        role={currentUser?.role || UserRole.USER} 
        activePage={activePage} 
        onNavigate={(page) => {
          // If navigating away from specific contexts, clear selections
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
