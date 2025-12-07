// src/api/client.ts
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { message } from '../components/UI.tsx';

// 基础配置
const BASE_URL = '/api';

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
    // 【新增逻辑】检查业务状态码
    // 如果后端/Mock 返回的数据包含 code 字段，且不为 200
    if (response.data && response.data.code === 401) {
      // 1. 构造一个错误对象
      const errorMessage = response.data.message || '操作失败';
      const customError = new Error(errorMessage);

      // 2. 将后端返回的完整数据挂载到 error 对象上，以便后续使用
      (customError as any).response = {
        status: 401,
        data: response.data
      };

      // 3. 主动抛出错误，这样就会跳到组件的 catch (err) 逻辑里
      return Promise.reject(customError);
    }
    return response.data;
  },
  (error: AxiosError) => {
    // 1. 处理 401 未授权 (Token 过期或无效)
    if (error.response?.status === 401) {
      // 使用统一风格的弹窗提示，而非 console.warn
      message.error('用户名或密码错误');
      localStorage.removeItem('access_token');
      // 可选：触发全局事件或跳转
      // window.location.href = '/login'; 
    }

    // 2. 提取后端返回的错误信息
    const errorData = error.response?.data as any;

    // ✅ 修复核心：更健壮的错误信息提取逻辑
    // 优先处理 detail 为字符串的情况，防止 `detail[0]` 提取出字符串的第一个字符
    let errorMessage = '网络请求失败，请检查网络连接'; // 默认兜底信息

    if (errorData?.detail) {
      if (typeof errorData.detail === 'string') {
        // 情况 A: { detail: "Term '4444' already exists..." }
        errorMessage = errorData.detail;
      } else if (Array.isArray(errorData.detail) && errorData.detail.length > 0) {
        // 情况 B: FastAPI Validation Error [{ loc:.., msg:.. }] 或 字符串数组
        // 优先取 .msg，如果没有则直接取元素本身
        errorMessage = errorData.detail[0]?.msg || errorData.detail[0] || errorMessage;
      }
    } else if (errorData?.message) {
      // 情况 C: 常规 { message: "Error info" }
      errorMessage = errorData.message;
    }

    // 【核心变更】使用全局 Toast 展示错误信息，替代浏览器 alert 或 console.log
    // 只有当错误不是 401 (上面已处理) 时才弹通用错误，避免重复
    if (error.response?.status !== 401) {
      message.error(errorMessage);
    }

    // 3. 构造新的 Error 对象抛出，方便 UI 层捕获
    const customError = new Error(errorMessage);
    (customError as any).code = error.response?.status;
    (customError as any).details = errorData?.error?.details;

    return Promise.reject(customError);
  }
);

export default client;