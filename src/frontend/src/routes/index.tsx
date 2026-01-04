/**
 * 路由配置
 * 定义应用的所有路由，保持与原有 activePage 逻辑一致
 */

// 路由路径常量
export const ROUTES = {
  // 公共路由
  LOGIN: '/login',

  // 普通用户路由
  DASHBOARD: '/dashboard',
  WORKSPACE: '/workspace/:projectId',
  REPORTS: '/reports',
  GLOSSARY: '/glossary',
  ANNOUNCEMENTS: '/announcements',
  PROFILE: '/profile',

  // 管理员路由
  ADMIN_USERS: '/admin/users',
  ADMIN_USER_DETAIL: '/admin/users/:userId',
  ADMIN_ANNOUNCEMENTS: '/admin/announcements',
  ADMIN_AI_MODELS: '/admin/ai-models',
  ADMIN_STATUS: '/admin/status',
} as const;

// activePage 到路由路径的映射（用于兼容旧代码）
export const PAGE_TO_ROUTE: Record<string, string> = {
  'dashboard': ROUTES.DASHBOARD,
  'workspace': '/workspace', // 需要拼接 projectId
  'reports': ROUTES.REPORTS,
  'glossary': ROUTES.GLOSSARY,
  'announcements': ROUTES.ANNOUNCEMENTS,
  'profile': ROUTES.PROFILE,
  'admin_users': ROUTES.ADMIN_USERS,
  'admin_user_detail': '/admin/users', // 需要拼接 userId
  'admin_announcements': ROUTES.ADMIN_ANNOUNCEMENTS,
  'admin_ai_models': ROUTES.ADMIN_AI_MODELS,
  'admin_status': ROUTES.ADMIN_STATUS,
};

// 路由路径到 activePage 的映射（用于 Sidebar 高亮）
export const ROUTE_TO_PAGE: Record<string, string> = {
  [ROUTES.DASHBOARD]: 'dashboard',
  [ROUTES.REPORTS]: 'reports',
  [ROUTES.GLOSSARY]: 'glossary',
  [ROUTES.ANNOUNCEMENTS]: 'announcements',
  [ROUTES.PROFILE]: 'profile',
  [ROUTES.ADMIN_USERS]: 'admin_users',
  [ROUTES.ADMIN_ANNOUNCEMENTS]: 'admin_announcements',
  [ROUTES.ADMIN_AI_MODELS]: 'admin_ai_models',
  [ROUTES.ADMIN_STATUS]: 'admin_status',
};

// 根据路径获取 activePage（支持动态路由）
export function getActivePageFromPath(pathname: string): string {
  // 精确匹配
  if (ROUTE_TO_PAGE[pathname]) {
    return ROUTE_TO_PAGE[pathname];
  }

  // 动态路由匹配
  if (pathname.startsWith('/workspace/')) {
    return 'workspace';
  }
  if (pathname.match(/^\/admin\/users\/\d+$/)) {
    return 'admin_user_detail';
  }
  if (pathname.startsWith('/admin/users')) {
    return 'admin_users';
  }

  // 默认
  return 'dashboard';
}

// 生成带参数的路由路径
export function generatePath(route: string, params: Record<string, string | number>): string {
  let path = route;
  Object.entries(params).forEach(([key, value]) => {
    path = path.replace(`:${key}`, String(value));
  });
  return path;
}
