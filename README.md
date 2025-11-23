# 202326010

本项目包含 **前端 (React + Vite)** 和 **后端 (FastAPI + Celery + PostgreSQL + MySQL + Redis)**，推荐使用 Docker 进行本地开发和运行。

当前目录结构（简化版）：

- `src/frontend`：前端 React + Vite 工程
- `src/backend`：后端 FastAPI 工程
- `docker-compose.yml`：一键启动数据库、后端、前端的 Docker 编排文件

## 如何在 Docker 中进行前端开发

> 适合对 Node.js / Vite 不熟悉的同学，全部命令只需要在项目根目录执行。

### 1. 先安装好开发环境

- **必须安装**：
  - Docker Desktop（Windows 建议开启 WSL2 后端）
  - `git`（用于拉取项目，可选）

安装完成后，确保终端可以执行：

```bash
docker --version
docker compose version
```

### 2. （推荐）只启动前端开发环境

如果你暂时只想改前端页面，不需要数据库和后端：

```bash
cd D:\Desktop\202326010   # 进入项目根目录
docker compose up frontend
```

启动成功后：

- 在浏览器访问 `http://localhost:3000`
- 修改本地 `src/frontend` 目录下的代码，页面会自动热更新（HMR）

> 停止开发：在终端中按 `Ctrl + C` 即可退出前端容器。

### 3. 启动「前端 + 后端 + 数据库」整体环境

如果需要调试前后端联动：

```bash
cd D:\Desktop\202326010
docker compose up
```

- 前端：`http://localhost:3000`
- 后端 API：`http://localhost:8000`

你也可以只启动部分服务，例如：

```bash
docker compose up backend postgres-meta mysql-user redis
```

### 4. 修改代码后的体验

前端和后端的代码目录都挂载到了容器中：

- 修改 `src/frontend` 下的文件 → 前端页面自动刷新
- 修改 `src/backend` 下的文件 → FastAPI + Celery 会自动重载（`--reload`）

不需要在容器里重新安装依赖或重启容器，非常适合开发。

### 5. 常见问题

- **端口被占用**：
  - 如果 `3000` 或 `8000` 已被其他程序占用，可以修改 `docker-compose.yml` 中对应的端口映射（冒号左边的数字）。
- **前端打不开 / 白屏**：
  - 确认终端中前端容器日志没有明显报错；
  - 如果你本地也安装了 Node，不要同时在本机直接运行 `npm run dev` 和 Docker 里的前端服务，否则容易端口冲突。

> 如果你对终端命令不熟，只要记住：**进入项目目录，执行 `docker compose up frontend`，浏览器打开 `http://localhost:3000` 即可开始前端开发。**

