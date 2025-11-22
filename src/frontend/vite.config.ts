import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '');
  return {
    plugins: [react()],
    server: {
      host: '0.0.0.0',      // 允许 Docker 外部访问
      port: 3000,           // 开发服务器端口
      strictPort: true,
      hmr: {
        clientPort: 3001,   // 强制客户端连接到 3001 (需要在 docker-compose 中映射)
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