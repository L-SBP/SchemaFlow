// src/api/client.ts
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { BusinessError } from '../types';
import { GlobalErrorHandler } from '../utils/errorHandling';
import { responseInterceptor, errorInterceptor } from './errorMiddleware';

// 基础配置
const BASE_URL = '/api';

// 创建全局错误处理器实例
const errorHandler = new GlobalErrorHandler({
  showUserFriendlyMessages: true,
  logErrors: true,
  enableRetry: true,
  maxRetries: 3,
  retryDelay: 1000,
});

const client: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000, // 30秒超时
  headers: {
    'Content-Type': 'application/json',
  },
});

// --- 请求拦截器：自动携带 Token ---
client.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 从 localStorage 获取 Token
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// --- 响应拦截器：使用统一的错误处理中间件 ---
client.interceptors.response.use(responseInterceptor, errorInterceptor);


// 业务错误处理函数 (保持向后兼容)
export const handleBusinessError = (error: BusinessError) => {
  errorHandler.handleError(error);
};

// 自动重试机制
export const withRetry = async <T>(
  apiCall: () => Promise<T>,
  maxRetries: number = 3
): Promise<T> => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await apiCall();
    } catch (error) {
      if (i === maxRetries - 1 || !isRetryableError(error)) {
        throw error;
      }
      await delay(Math.pow(2, i) * 1000); // 指数退避
    }
  }
  throw new Error('Max retries exceeded');
};

// 判断是否为可重试的错误
const isRetryableError = (error: any): boolean => {
  if (error instanceof BusinessError) {
    return false; // 业务错误不重试
  }

  if (error.response?.status) {
    const status = error.response.status;
    // 5xx 服务器错误和 408 超时可以重试
    return status >= 500 || status === 408;
  }

  // 网络错误可以重试
  return error.code === 'NETWORK_ERROR' || error.code === 'TIMEOUT';
};

// 延迟函数
const delay = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

// 初始化全局错误处理
errorHandler.initialize();

// 导出错误处理器和客户端
export { errorHandler };
export default client;