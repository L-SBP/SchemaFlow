# Frontend 前端服务

AI 数据库自动部署系统 - 基于 React 19 + TypeScript + Vite 的现代化前端应用。

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 19.2.0 | UI 框架 |
| TypeScript | 5.8.x | 类型安全 |
| Vite | 6.2.0 | 构建工具 |
| React Router | 7.11.0 | 路由管理 |
| Axios | 1.13.2 | HTTP 客户端 |
| Recharts | 3.4.1 | 数据图表 |
| Mermaid | 11.12.2 | 流程图渲染 |
| Lucide React | 0.554.0 | 图标库 |

## 目录结构

```
src/frontend/
├── public/                 # 静态资源
├── scripts/                # 构建脚本
│   └── check-compilation.ts
├── src/
│   ├── api/               # API 接口封装
│   ├── components/        # 通用组件
│   ├── constants/         # 常量定义
│   ├── hooks/             # 自定义 Hooks
│   ├── pages/             # 页面组件
│   │   ├── Admin.tsx              # 管理后台
│   │   ├── AdminAIModels.tsx      # AI 模型管理
│   │   ├── AdminAnnouncements.tsx # 公告管理
│   │   ├── AdminStatus.tsx        # 系统状态
│   │   ├── Announcements.tsx      # 公告页
│   │   ├── Dashboard.tsx          # 仪表盘
│   │   ├── DatabaseViewer.tsx     # 数据库查看器
│   │   ├── Glossary.tsx           # 术语表
│   │   ├── Login.tsx              # 登录页
│   │   ├── Profile.tsx            # 用户配置
│   │   ├── Reports.tsx            # 报表页
│   │   ├── UserProfile.tsx        # 用户资料
│   │   ├── Workspace.tsx          # 工作空间
│   │   └── WorkspaceWrapper.tsx   # 工作空间包装器
│   ├── routes/            # 路由配置
│   ├── types/             # TypeScript 类型定义
│   ├── utils/             # 工具函数
│   ├── App.tsx            # 应用入口组件
│   ├── index.tsx          # 应用入口文件
│   ├── index.css          # 全局样式
│   └── types.ts           # 类型定义
├── index.html             # HTML 模板
├── package.json           # 依赖配置
├── tsconfig.json          # TypeScript 配置
├── tsconfig.node.json     # Node TypeScript 配置
├── vite.config.ts         # Vite 配置
├── vite-env.d.ts          # Vite 环境类型声明
└── Dockerfile.dev         # Docker 开发镜像
```

## 快速开始

### 环境要求

- Node.js >= 20.x
- npm >= 10.x

### 1. 安装依赖

```bash
# 进入前端目录
cd src/frontend

# 配置国内镜像源（可选，提升下载速度）
npm config set registry https://registry.npmmirror.com/

# 安装依赖
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

开发服务器启动后，访问：http://localhost:3000

### 3. 构建生产版本

```bash
npm run build
```

构建产物输出到 `dist/` 目录。

## 开发指南

### API 代理配置

开发环境下，前端通过 Vite 代理将 `/api` 请求转发到后端服务：

```typescript
// vite.config.ts
proxy: {
  '/api': {
    target: 'http://localhost:8000',      // 本地后端
    // target: 'http://host.docker.internal:8000',  // Docker 环境
    changeOrigin: true,
  }
}
```

### 添加新页面

1. 在 `src/pages/` 下创建页面组件
2. 在 `src/routes/` 中注册路由

```tsx
// src/pages/MyPage.tsx
import React from 'react';

const MyPage: React.FC = () => {
  return <div>My New Page</div>;
};

export default MyPage;
```

### 添加 API 接口

在 `src/api/` 目录下封装 API 调用：

```typescript
// src/api/myApi.ts
import axios from 'axios';

export const getMyData = async () => {
  const response = await axios.get('/api/v1/my-endpoint');
  return response.data;
};
```

## 常用命令

| 命令 | 说明 |
|------|------|
| `npm run dev` | 启动开发服务器（热更新） |
| `npm run build` | 构建生产版本 |
| `npm run preview` | 预览构建结果 |
| `npm run type-check` | TypeScript 类型检查 |

## Docker 开发

使用 Docker Compose 启动（推荐）：

```bash
# 在项目根目录执行
docker-compose up -d frontend

# 查看日志
docker-compose logs -f frontend
```

前端服务将在 http://localhost:3000 启动。

## 常见问题

### Q: npm install 很慢或失败

配置国内镜像源：

```bash
npm config set registry https://registry.npmmirror.com/
```

### Q: 修改代码后页面没有更新

1. 确保开发服务器正在运行
2. 检查浏览器控制台是否有错误
3. 尝试清除浏览器缓存或强制刷新（Ctrl+Shift+R）

### Q: API 请求失败

1. 确保后端服务正在运行（http://localhost:8000）
2. 检查 Vite 代理配置是否正确
3. 检查浏览器网络面板查看具体错误

### Q: Docker 环境下文件修改不触发热更新

Docker 中使用轮询方式监听文件变化，已在 `vite.config.ts` 中配置：

```typescript
watch: {
  usePolling: true,
}
```

## 相关文档

- [后端 README](../backend/README.md)
- [部署启动文档](../../部署启动文档.md)
- [API 文档](http://localhost:8000/docs)
