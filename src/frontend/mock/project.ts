// import { MockMethod } from 'vite-plugin-mock';

// // 模拟内存数据库
// let projects: any[] = [
//   {
//     project_id: '101',
//     project_name: '企业级 CRM 客户管理系统',
//     project_type: 'MySQL',
//     description: '用于管理客户信息、销售机会及合同订单的核心系统。',
//     project_status: 'active',
//     created_at: '2023-11-20T10:00:00Z',
//     creation_stage: 'completed',
//     progress_percentage: 100,
//   },
//   {
//     project_id: '102',
//     project_name: '电商库存中心',
//     project_type: 'PostgreSQL',
//     description: '高并发库存扣减与多仓库调拨系统。',
//     project_status: 'initializing', // 模拟一个正在部署中的旧项目
//     created_at: new Date().toISOString(),
//     creation_stage: 'generating_schema',
//     progress_percentage: 45,
//   }
// ];

// // 预设的生成内容，用于模拟 AI 返回
// const MOCK_ANALYSIS = `
// ### 1. 核心实体识别
// - **User (用户)**: 系统使用者，包含基本信息及权限角色。
// - **Product (商品)**: 销售的核心单元，需包含库存、价格、类目等属性。
// - **Order (订单)**: 交易凭证，关联用户与商品，包含状态流转。
// - **Review (评价)**: 用户对商品的反馈，包含评分与内容。

// ### 2. 关系模型分析
// - User -> Order: 1:N (一个用户可创建多个订单)
// - Order -> Product: N:M (一个订单包含多个商品，通过 OrderItem 关联)
// - User -> Review: 1:N (用户可发布多条评价)
// - Product -> Review: 1:N (商品可拥有多条评价)
// `;

// const MOCK_DDL = `
// CREATE TABLE users (
//     user_id BIGINT PRIMARY KEY AUTO_INCREMENT,
//     username VARCHAR(50) NOT NULL,
//     email VARCHAR(100) UNIQUE NOT NULL,
//     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
// );

// CREATE TABLE products (
//     product_id BIGINT PRIMARY KEY AUTO_INCREMENT,
//     name VARCHAR(100) NOT NULL,
//     price DECIMAL(10, 2) NOT NULL,
//     stock INT DEFAULT 0
// );

// CREATE TABLE orders (
//     order_id BIGINT PRIMARY KEY AUTO_INCREMENT,
//     user_id BIGINT,
//     total_amount DECIMAL(12, 2),
//     status ENUM('pending', 'paid', 'shipped') DEFAULT 'pending',
//     FOREIGN KEY (user_id) REFERENCES users(user_id)
// );
// `;

// const MOCK_LOGS = [
//   '>>> 初始化部署序列...',
//   '>>> 正在连接智能 Agent (Gemini 3.0 Pro)...',
//   '✔ 智能体已连接',
//   '>>> 开始业务需求深度分析...',
//   '✔ 逻辑模型构建完成 (3NF)',
//   '>>> 正在生成数据库定义语言 (DDL)...',
//   '✔ SQL 语法校验通过',
//   '>>> 分配云端数据库实例 (Region: CN-North)...',
//   '>>> 执行 Schema 初始化脚本...',
//   '✔ 表结构创建成功',
//   '✔ 索引策略已应用',
//   '✔ 用户权限配置完成',
//   '>>> 服务启动中...',
//   '✔ 部署完成'
// ];

// export default [
//   // 1. 获取项目列表
//   {
//     url: '/api/projects',
//     method: 'get',
//     response: () => {
//       return {
//         code: 200,
//         message: 'success',
//         data: projects.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()),
//       };
//     },
//   },

//   // 2. 创建项目 (触发 AI 生成流程)
//   {
//     url: '/api/projects',
//     method: 'post',
//     response: ({ body }: any) => {
//       const newProject = {
//         project_id: Date.now().toString(),
//         project_name: body.name,
//         project_type: body.type,
//         description: body.description,
//         project_status: 'initializing', // 初始状态
//         created_at: new Date().toISOString(),
//         creation_stage: 'analyzing',    // 初始阶段
//         progress_percentage: 0,
//         // 以下字段初始为空，后续轮询时填充
//         analysis_result: '',
//         ddl_result: '',
//         deployment_logs: []
//       };
//       projects.unshift(newProject);
//       return {
//         code: 200,
//         message: 'Project created successfully',
//         data: { project_id: newProject.project_id }
//       };
//     },
//   },

//   // 3. 获取项目详情 (轮询接口，模拟随时间推移的进度)
//   {
//     url: RegExp('/api/projects/\\d+'), // 匹配 /api/projects/:id
//     method: 'get',
//     response: ({ url }: any) => {
//       const id = url.split('/').pop();
//       const project = projects.find(p => p.project_id === id);

//       if (!project) {
//         return { code: 404, message: 'Project not found' };
//       }

//       // === 核心 Mock 逻辑：根据创建时间模拟进度 ===
//       // 如果项目已经是完成状态，直接返回
//       if (project.project_status === 'active') {
//         return { code: 200, data: project };
//       }

//       const now = Date.now();
//       const created = new Date(project.created_at).getTime();
//       const elapsed = now - created;

//       // 模拟时间轴：
//       // 0-3秒: 分析阶段
//       // 3-6秒: DDL 生成阶段
//       // 6-9秒: 部署阶段
//       // >9秒: 完成

//       if (elapsed < 3000) {
//         project.creation_stage = 'analyzing';
//         project.progress_percentage = 20;
//         project.analysis_result = MOCK_ANALYSIS.substring(0, Math.floor(MOCK_ANALYSIS.length * (elapsed / 3000))); // 模拟打字机效果
//         project.deployment_logs = MOCK_LOGS.slice(0, 3);
//       } else if (elapsed < 6000) {
//         project.creation_stage = 'generating_ddl';
//         project.progress_percentage = 50;
//         project.analysis_result = MOCK_ANALYSIS;
//         project.ddl_result = MOCK_DDL.substring(0, Math.floor(MOCK_DDL.length * ((elapsed - 3000) / 3000)));
//         project.deployment_logs = MOCK_LOGS.slice(0, 7);
//       } else if (elapsed < 9000) {
//         project.creation_stage = 'deploying';
//         project.progress_percentage = 80;
//         project.analysis_result = MOCK_ANALYSIS;
//         project.ddl_result = MOCK_DDL;
//         project.deployment_logs = MOCK_LOGS.slice(0, 10);
//       } else {
//         project.project_status = 'active';
//         project.creation_stage = 'completed';
//         project.progress_percentage = 100;
//         project.analysis_result = MOCK_ANALYSIS;
//         project.ddl_result = MOCK_DDL;
//         project.deployment_logs = MOCK_LOGS;
//       }

//       return {
//         code: 200,
//         message: 'success',
//         data: project
//       };
//     },
//   },
// ] as MockMethod[];