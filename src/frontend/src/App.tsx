import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { Sidebar } from './components/Sidebar.tsx';
import { Header } from './components/Header.tsx';
import { ToastContainer } from './components/UI.tsx';
import { Login } from './pages/Login.tsx';
import { Dashboard } from './pages/Dashboard.tsx';
import { WorkspaceWrapper } from './pages/WorkspaceWrapper.tsx';
import { AdminPanel } from './pages/Admin.tsx';
import { AdminAnnouncements } from './pages/AdminAnnouncements.tsx';
import { UserProfile } from './pages/UserProfile.tsx';
import { Reports } from './pages/Reports.tsx';
import { Glossary } from './pages/Glossary.tsx';
import { Profile } from './pages/Profile.tsx';
import { AdminStatus } from './pages/AdminStatus.tsx';
import { AdminAIModels } from './pages/AdminAIModels.tsx';
import { Announcements } from './pages/Announcements.tsx';
import { UserRole, Project, User } from './types.ts';
import { authApi } from './api/auth.ts';
import { getUserProfile } from './api/user.ts';
import { ProjectDTO } from './api/project.ts';
import { Loader2 } from 'lucide-react';
import { ROUTES, getActivePageFromPath, generatePath } from './routes/index.tsx';

const App: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // 认证状态
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState<{ role: UserRole, name: string, avatar_url?: string } | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // Shared State
  const [projects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [viewingUser, setViewingUser] = useState<User | null>(null);

  // 根据当前路径计算 activePage（用于 Sidebar 高亮）
  const activePage = getActivePageFromPath(location.pathname);

  // 初始化时检查登录状态
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token');

      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        const res = await getUserProfile() as any;

        let userData = null;
        if (res && res.user_id) {
          userData = res;
        } else if (res && res.data && res.data.user_id) {
          userData = res.data;
        }

        if (userData) {
          const role = userData.is_admin ? UserRole.ADMIN : UserRole.USER;
          setCurrentUser({
            role,
            name: userData.username,
            avatar_url: userData.avatar_url
          });
          setIsAuthenticated(true);

          // 如果当前在登录页或根路径，跳转到默认页面
          if (location.pathname === '/login' || location.pathname === '/') {
            navigate(role === UserRole.ADMIN ? ROUTES.ADMIN_USERS : ROUTES.DASHBOARD, { replace: true });
          }
        } else {
          throw new Error('Invalid user data');
        }
      } catch (error) {
        console.warn('Auto login failed (Token expired or invalid):', error);
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
    navigate(role === UserRole.ADMIN ? ROUTES.ADMIN_USERS : ROUTES.DASHBOARD, { replace: true });
  };

  const updateCurrentUser = (updates: Partial<{ name: string; avatar_url: string }>) => {
    setCurrentUser(prev => prev ? { ...prev, ...updates } : null);
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
      navigate(ROUTES.LOGIN, { replace: true });
    }
  };

  // 设置选中项目（供 WorkspaceWrapper 使用）
  const handleSetSelectedProject = (project: Project) => {
    setSelectedProject(project);
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
    navigate(generatePath(ROUTES.WORKSPACE, { projectId: project.id }));
  };

  const handleViewUser = (user: User) => {
    setViewingUser(user);
    navigate(generatePath(ROUTES.ADMIN_USER_DETAIL, { userId: user.id }));
  };

  // 页面导航处理（供 Sidebar 使用）
  const handleNavigate = (page: string) => {
    if (page !== 'admin_user_detail') setViewingUser(null);

    switch (page) {
      case 'dashboard':
        navigate(ROUTES.DASHBOARD);
        break;
      case 'workspace':
        if (selectedProject) {
          navigate(generatePath(ROUTES.WORKSPACE, { projectId: selectedProject.id }));
        } else {
          navigate(ROUTES.DASHBOARD);
        }
        break;
      case 'reports':
        navigate(ROUTES.REPORTS);
        break;
      case 'glossary':
        navigate(ROUTES.GLOSSARY);
        break;
      case 'announcements':
        navigate(ROUTES.ANNOUNCEMENTS);
        break;
      case 'profile':
        navigate(ROUTES.PROFILE);
        break;
      case 'admin_users':
        navigate(ROUTES.ADMIN_USERS);
        break;
      case 'admin_announcements':
        navigate(ROUTES.ADMIN_ANNOUNCEMENTS);
        break;
      case 'admin_ai_models':
        navigate(ROUTES.ADMIN_AI_MODELS);
        break;
      case 'admin_status':
        navigate(ROUTES.ADMIN_STATUS);
        break;
      default:
        navigate(ROUTES.DASHBOARD);
    }
    setIsSidebarOpen(false);
  };

  // 返回 Dashboard 的处理
  const handleBackToDashboard = () => {
    setSelectedProject(null);
    navigate(ROUTES.DASHBOARD);
  };

  // 返回用户列表的处理
  const handleBackToUserList = () => {
    setViewingUser(null);
    navigate(ROUTES.ADMIN_USERS);
  };

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

  // 2. 如果未认证，只显示登录页
  if (!isAuthenticated) {
    return (
      <>
        <ToastContainer />
        <Routes>
          <Route path="/login" element={<Login onLogin={handleLogin} />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </>
    );
  }

  // 3. 已认证，渲染主布局 + 路由
  const isAdmin = currentUser?.role === UserRole.ADMIN;
  const defaultRoute = isAdmin ? ROUTES.ADMIN_USERS : ROUTES.DASHBOARD;

  return (
    <div className="flex h-screen h-[100dvh] bg-[#f0f2f5] bg-[url('/background.svg')] bg-center bg-no-repeat bg-contain overflow-hidden">
      <ToastContainer />

      <Sidebar
        role={currentUser?.role || UserRole.USER}
        user={currentUser}
        selectedProject={selectedProject}
        activePage={activePage}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        onLogout={handleLogout}
        onNavigate={handleNavigate}
      />
      <main className="flex-1 flex flex-col min-w-0 min-h-0">
        <Header onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)} />
        <div className="flex-1 overflow-hidden relative">
          <Routes>
            {/* 公共路由 - 两种角色都可访问 */}
            <Route path="/profile" element={<Profile user={currentUser} onLogout={handleLogout} onUpdateUser={updateCurrentUser} />} />

            {/* 普通用户路由 - 仅非管理员可访问 */}
            {!isAdmin && (
              <>
                <Route path="/dashboard" element={<Dashboard onProjectSelect={handleProjectSelect} />} />
                <Route
                  path="/workspace/:projectId"
                  element={
                    <WorkspaceWrapper
                      selectedProject={selectedProject}
                      onProjectSelect={handleSetSelectedProject}
                      onBack={handleBackToDashboard}
                    />
                  }
                />
                <Route path="/reports" element={<Reports projects={projects} selectedProject={selectedProject} />} />
                <Route path="/glossary" element={<Glossary selectedProject={selectedProject} />} />
                <Route path="/announcements" element={<Announcements />} />
              </>
            )}

            {/* 管理员路由 - 仅管理员可访问 */}
            {isAdmin && (
              <>
                <Route path="/admin/users" element={<AdminPanel onViewUser={handleViewUser} />} />
                <Route
                  path="/admin/users/:userId"
                  element={
                    viewingUser ? (
                      <UserProfile user={viewingUser} onBack={handleBackToUserList} />
                    ) : (
                      <Navigate to="/admin/users" replace />
                    )
                  }
                />
                <Route path="/admin/announcements" element={<AdminAnnouncements />} />
                <Route path="/admin/ai-models" element={<AdminAIModels />} />
                <Route path="/admin/status" element={<AdminStatus />} />
              </>
            )}

            {/* 默认路由 & 未匹配路由 - 重定向到角色对应首页 */}
            <Route path="/" element={<Navigate to={defaultRoute} replace />} />
            <Route path="*" element={<Navigate to={defaultRoute} replace />} />
          </Routes>
        </div>
      </main>
    </div>
  );
};

export default App;
