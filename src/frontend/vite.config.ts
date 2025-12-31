import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// 检测是否在 Docker 容器内运行
const isDocker = process.env.DOCKER === 'true';

// 根据环境选择后端地址
const getApiTarget = () => {
  if (isDocker) {
    return 'http://backend:8000';  // Docker 内部网络
  }
  return 'http://localhost:8000';  // 本地开发
};

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, '.', '');
  const apiTarget = getApiTarget();
  
  return {
    plugins: [react()],
    server: {
      host: '0.0.0.0',      // 允许 Docker 外部访问
      port: 3000,           // 开发服务器端口
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          // 如果后端接口本身不带 /api 前缀，需要把路径里的 /api 去掉
          // rewrite: (path) => path.replace(/^\/api/, '') 

          configure: (proxy, options) => {
            proxy.on('proxyReq', (proxyReq, req, res) => {
              console.log('代理转发中:', req.url, '->', options.target + req.url);
            });
            proxy.on('error', (err, req, res) => {
              console.log('代理出错:', err);
            });
          }
        }
      },
      strictPort: true,
      hmr: {
        clientPort: 3000,   // 强制客户端连接到 3001 (需要在 docker-compose 中映射)
      },
      watch: {
        usePolling: true,   // 在某些 Docker 环境下（如 Windows）需要轮询
      }
    },
    // SPA 路由支持：所有非静态资源请求都返回 index.html
    appType: 'spa',
    define: {
      'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY),
      'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY)
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      }
    }
  };
});