# 智能查询平台 - 前端 (React + Vite)

本项目是智能查询平台的前端应用，基于 React 和 Vite 构建，负责提供用户界面、交互逻辑，并与后端的 FastAPI 服务进行通信。

## 技术栈

* **构建工具:** Vite
* **核心框架:** React 18+
* **路由:** React Router v6 (需安装)
* **API 请求:** Axios (需安装)
* **状态管理:** React Context (用于全局认证)
* **样式:** (初定antd)

## 快速开始

### 1\. 环境准备

* [Node.js](https://nodejs.org/) (推荐 v18 或更高版本)
* `npm` (随 Node.js 自动安装)

### 2\. 安装依赖

此命令将安装`package.json`中已列出的`react`和`react-dom`。

```bash
npm install
```

**重要提示：** 为了实现我们设计的架构（路由、API请求），您还需要安装以下核心依赖：

```bash
npm install axios react-router-dom swr date-fns react-icons
```


### 3\. 配置环境变量
**目前这部分存疑**，不清楚是不是在docker里面配置了  
在项目根目录创建一个 `.env` 文件，并至少配置后端的 API 基地址：

```.env
# 后端 API 的基地址
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### 4\. 运行开发服务器

```bash
npm run dev
```

应用将在 `http://localhost:5173` (或 Vite 选定的其他端口) 上运行。

## 主要NPM脚本

(这些脚本已在您的 `package.json` 中定义)

* **`npm run dev`**: 启动本地开发服务器，支持热更新。
* **`npm run build`**: 将应用打包到 `dist/` 目录，用于生产环境部署。
* **`npm run lint`**: 运行 ESLint 检查代码规范。
* **`npm run preview`**: 在本地预览生产环境的构建包。

-----

## 项目结构

本项目的结构设计遵循“功能分离” (Separation of Concerns) 和“高内聚、低耦合”的原则，旨在提高可维护性和可扩展性。

```
src/
├── api/             # 1. API 服务层 (核心)
│   ├── axiosClient.js     # Axios 实例、拦截器 (Token注入, 错误处理)
│   ├── authApi.js         # 封装所有 /auth/*, /users/me 接口
│   ├── projectApi.js      # 封装 /projects/*, /sessions/*, /messages/* 接口
│   ├── adminApi.js        # 封装 /admin/* 接口
│   └── knowledgeApi.js    # 封装 /knowledge/* 接口
│
├── assets/            # 2. 静态资源 (图片, SVG, 字体)
│
├── components/        # 3. 可复用UI组件
│   ├── common/            # 通用基础组件 (Button, Input, Modal...)
│   ├── AdminRoute.jsx     # 管理员路由守卫
│   └── ProtectedRoute.jsx # 登录保护路由守卫
│
├── contexts/          # 4. 全局状态管理 (React Context)
│   └── AuthContext.jsx    # 核心: 管理 user, token, isLoading 状态
│
├── hooks/             # 5. 自定义 Hooks
│   ├── useAuth.js         # 快捷访问 AuthContext
│   ├── useDebounce.js     # (示例) 防抖 Hook
│   └── (其他如 useSWR, useQuery 等数据获取 Hook)
│
├── layouts/           # 6. 页面布局
│   ├── AppLayout.jsx      # 普通用户主界面 (带侧边栏/导航栏)
│   ├── AdminLayout.jsx    # 管理后台界面
│   └── AuthLayout.jsx     # 登录/注册页面的居中布局
│
├── pages/             # 7. 页面 (路由顶层组件)
│   ├── admin/             # 管理后台页面
│   │   ├── DashboardPage.jsx
│   │   └── UserManagementPage.jsx
│   ├── app/               # 核心应用页面
│   │   ├── ProjectListPage.jsx
│   │   └── ProjectQueryPage.jsx
│   ├── auth/              # 认证页面
│   │   ├── LoginPage.jsx
│   │   └── RegisterPage.jsx
│   └── NotFoundPage.jsx
│
├── router/            # 8. 路由配置
│   └── index.jsx          # 使用 useRoutes 集中定义所有路由规则
│
├── styles/            # 9. 全局样式
│   ├── global.css         # 全局样式, CSS 变量
│   └── (其他如 theme.js)
│
├── utils/             # 10. 通用工具函数
│   ├── formatDate.js      # 日期格式化
│   └── validators.js      # 表单验证逻辑
│
├── App.jsx            # 应用根组件 (渲染路由)
└── main.jsx           # 应用入口 (挂载 React, 注入 Context 和 Router)
```

-----

## 核心架构理念

### 1\. 路由与认证流程

1.  **入口 (`main.jsx`)**: `BrowserRouter` 包裹 `AuthProvider`，`AuthProvider` 再包裹 `App`。
2.  **全局状态 (`AuthContext.jsx`)**:
    * 应用加载时，`AuthContext` 会检查 `localStorage` 中的 `token`。
    * 如果 `token` 存在，它会立即调用 `api/authApi.js` 中的 `getMe()` (对应 `GET /users/me`) 来验证 `token` 并获取用户信息。
    * 在 `getMe()` 返回结果前，`isLoading` 状态为 `true`。
3.  **路由守卫 (`ProtectedRoute.jsx`)**:
    * 在 `isLoading` 为 `true` 时，显示全局加载动画。
    * 在 `isLoading` 为 `false` 后，检查 `user` 是否存在。
    * 如果 `user` 不存在，重定向到 `/auth/login`。
    * 如果 `user` 存在，渲染子路由 (`<Outlet />`)。
4.  **管理员守卫 (`AdminRoute.jsx`)**: 在 `ProtectedRoute` 的基础上，额外检查 `user.is_admin` 是否为 `true`。

### 2\. API 数据流

这是本项目数据交互的核心，严格禁止在 `pages/` 或 `components/` 中直接使用 `axios`。

**标准流程:** 页面组件 -\> (自定义Hook) -\> `api/*.js` -\> `axiosClient.js` -\> 后端

1.  **页面组件 (`pages/app/ProjectListPage.jsx`)**:

    * 负责展示UI和处理用户交互。
    * 当需要数据时，调用 `api/projectApi.js` 中封装好的函数。
    * *示例:* `useEffect(() => { projectApi.getProjects().then(setData); }, [])`

2.  **API 模块 (`api/projectApi.js`)**:

    * 负责封装**业务逻辑**。
    * 导入 `axiosClient` 并调用其 `get`, `post` 等方法，处理特定的 URL 和参数。
    * *示例:* `export const getProjects = (search) => client.get('/projects', { params: { search } });`

3.  **Axios 客户端 (`api/axiosClient.js`)**:

    * 负责处理**通用技术逻辑**。
    * **请求拦截器**: 自动从 `localStorage` (或 `AuthContext`) 获取 `token`，并将其注入到 `Authorization: Bearer <token>` 请求头中。
    * **响应拦截器**:
        * 全局处理 `401 Unauthorized` 错误（Token失效），自动清除用户信息并强制跳转到登录页。
        * 全局处理其他 `5xx` 等服务器错误，提供统一的错误提示。
        * 自动解包响应数据 (例如 `response.data`)。

### 3\. 状态管理

* **全局状态 (`contexts/AuthContext.jsx`)**: **仅用于**存储全局身份认证信息（`user`, `token`, `isLoading`）。
* **服务端状态 (推荐)**: 对于从API获取的数据（如项目列表、消息列表），强烈推荐使用 `SWR` 或 `React Query (TanStack Query)`。它们可以被封装在 `hooks/` 目录中 (例如 `useProjects`)，自动处理缓存、重新验证和加载状态，极大简化 `pages/` 中的逻辑。
* **本地状态 (`useState`, `useReducer`)**: 用于组件内部的UI状态（例如表单输入、弹窗开关等）。