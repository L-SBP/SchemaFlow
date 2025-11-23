// src/api/client.ts
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

// 基础配置
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://api.dbplatform.example/v1';

const client: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 10000, // 10秒超时
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

// --- 响应拦截器：统一处理错误与数据解包 ---
client.interceptors.response.use(
  (response) => {
    // 直接返回 response.data，这样在调用处就不需要再写 .data 了
    return response.data;
  },
  (error: AxiosError) => {
    // 1. 处理 401 未授权 (Token 过期或无效)
    if (error.response?.status === 401) {
      console.warn('登录已过期，请重新登录');
      localStorage.removeItem('access_token');
      // 可选：触发全局事件或跳转
      // window.location.href = '/login'; 
    }

    // 2. 提取后端返回的错误信息
    // 假设后端错误格式为: { error: { message: "..." } } 或 { message: "..." }
    const errorData = error.response?.data as any;
    const errorMessage =
      errorData?.error?.message ||
      errorData?.message ||
      error.message ||
      '网络请求失败，请稍后重试';

    // 3. 构造新的 Error 对象抛出，方便 UI 层捕获
    const customError = new Error(errorMessage);
    (customError as any).code = error.response?.status;
    (customError as any).details = errorData?.error?.details;

    return Promise.reject(customError);
  }
);

export default client;