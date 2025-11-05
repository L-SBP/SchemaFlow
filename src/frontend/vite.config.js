import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',      // 允许外部访问（Docker 必需！）
    port: 3000,           // 开发服务器端口
    strictPort: true,     // 端口被占用时直接报错（避免混淆）
    hmr: {
      port: 3001,         // 显式指定 HMR WebSocket 端口（与 docker-compose.yml 一致）
      clientPort: 3001,   // 客户端连接的端口（浏览器用）
    },
    // 如果后端 API 在同一主机，可通过 proxy 避免跨域（可选）
    // proxy: {
    //   '/api': {
    //     target: 'http://backend:8000',
    //     changeOrigin: true,
    //   }
    // }
  }
})