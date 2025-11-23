import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import { viteMockServe } from 'vite-plugin-mock'

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, '.', '');
  return {
    plugins: [react(),
    viteMockServe({
      // 1. mock文件存放目录，默认为根目录下的 mock 文件夹
      mockPath: 'mock',
      // 2. 只有开发环境且 VITE_USE_MOCK 为 true 时开启
      enable: command === 'serve' && env.VITE_USE_MOCK === 'true',
      // 3. 关键：Docker 中监听文件变化可能需要这个配置，
      // 确保修改 mock 文件后能自动刷新
      watchFiles: true,
    }),
    ],
    server: {
      host: '0.0.0.0',      // 允许 Docker 外部访问
      port: 3000,           // 开发服务器端口
      proxy: {
        '/api': {

          target: 'http://backend:8000',
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