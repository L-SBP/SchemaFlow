/**
 * @file client.ts
 * @module API/Client
 * @description 全局网络请求客户端核心配置文件。
 * 本模块基于 Axios 库构建，作为“基于大模型多智能体框架的数据库自动部署与库表生成系统”的前后端通讯基石。
 * 核心功能包含：
 * 1. 统一的 RESTful API 基础路径配置；
 * 2. 自动化身份认证拦截（JWT Bearer Token 注入）；
 * 3. 响应状态码及业务逻辑错误的集中化分发处理；
 * 4. 指数退避算法实现的自动化重试机制，确保在不稳定网络环境下的服务可用性。
 * @author Wang Lirong (王利蓉)
 * @version 2.4.0
 * @date 2026-01-02
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { BusinessError } from '../types';
import { GlobalErrorHandler } from '../utils/errorHandling';
import { responseInterceptor, errorInterceptor } from './errorMiddleware';

/**
 * 后端服务基础端点配置
 * 对应 Vite/Webpack 的代理配置前缀，统一路由至 /api/v1 路径下
 */
const BASE_URL = '/api';

/**
 * 初始化全局错误处理器实例
 * 配置项包括用户友好消息开关、错误日志归档以及预设的重试策略。
 * 旨在满足系统非功能性需求中的“可用性”与“可靠性”指标 [cite: 541, 544]。
 */
const errorHandler = new GlobalErrorHandler({
  showUserFriendlyMessages: true, // 是否向非技术用户展示语义化的错误提示 [cite: 545]
  logErrors: true,                // 是否开启生产环境错误上报
  enableRetry: true,              // 全局默认开启异常重试逻辑
  maxRetries: 3,                  // 最大尝试次数，避免无效请求死循环
  retryDelay: 1000,               // 初始重试延迟基数（毫秒）
});

/**
 * 创建 Axios 单例对象
 * 统一设置超时时间、基础路径及 Content-Type 策略。
 * 超时时间设定为 30 秒，以平衡 AI 模型推理的长连接需求与前端交互体验 [cite: 55-60]。
 */
const client: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000, // 30秒超时设定，针对复杂 DDL 生成及异步任务预留冗余 [cite: 238]
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * --- 请求拦截器：自动携带身份验证凭据 ---
 * 遵循 CON5 数据安全约束，系统在每次请求发出前自动检索并注入 JWT Token [cite: 227, 326]。
 */
client.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    /**
     * 从持久化存储 (localStorage) 中读取当前会话的访问令牌
     * 该令牌由 authApi.login 成功响应后写入。
     */
    const token = localStorage.getItem('access_token');
    
    // 若存在有效令牌，则按照 RFC 6750 规范将其置于 Authorization 头部
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error: AxiosError) => {
    // 处理请求发送前的预检错误
    return Promise.reject(error);
  }
);

/**
 * --- 响应拦截器：集成统一的错误处理中间件 ---
 * 使用分层架构中的拦截器模式，将响应结果解包逻辑与异常捕获逻辑外抽至 errorMiddleware [cite: 270]。
 */
client.interceptors.response.use(responseInterceptor, errorInterceptor);


/**
 * 业务错误处理函数 (兼容性封装)
 * 专门用于手动捕获并处理符合 BusinessError 协议的逻辑错误。
 * @function handleBusinessError
 * @param {BusinessError} error - 封装了业务状态码及消息的错误对象
 */
export const handleBusinessError = (error: BusinessError) => {
  // 转发给全局错误处理器的 handle 逻辑，执行弹窗提示或重定向
  errorHandler.handleError(error);
};

/**
 * 自动化请求重试高阶函数
 * 针对特定的临时性错误（如网络瞬断、服务器 5xx）采用指数退避算法进行重试。
 * 旨在提升系统在极端情况下的鲁棒性，满足核心服务可用性不低于 85% 的目标 [cite: 541]。
 * @async
 * @template T
 * @param {Function} apiCall - 封装了实际 API 调用的异步函数闭包
 * @param {number} [maxRetries=3] - 最大重试次数
 * @returns {Promise<T>} 返回原始请求预期的响应数据
 */
export const withRetry = async <T>(
  apiCall: () => Promise<T>,
  maxRetries: number = 3
): Promise<T> => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      // 尝试执行原始 API 调用
      return await apiCall();
    } catch (error) {
      /**
       * 终止条件判定：
       * 1. 已达到最大尝试次数限制；
       * 2. 捕获的错误被判定为“不可重试”（如 4xx 业务逻辑错误）。
       */
      if (i === maxRetries - 1 || !isRetryableError(error)) {
        throw error;
      }
      
      /**
       * 指数退避 (Exponential Backoff) 策略：
       * 随着失败次数增加，延迟时间呈 2^n 指数增长，旨在减轻后端服务器瞬间并发压力。
       */
      await delay(Math.pow(2, i) * 1000); 
    }
  }
  throw new Error('Max retries exceeded');
};

/**
 * 错误可重试性评估算法
 * @function isRetryableError
 * @private
 * @param {any} error - 捕获的原始错误对象
 * @returns {boolean} 若错误具备恢复可能性则返回 true
 */
const isRetryableError = (error: any): boolean => {
  // 业务逻辑错误（如参数校验失败、余额不足）代表逻辑终点，不应进行重试
  if (error instanceof BusinessError) {
    return false; 
  }

  // 针对 HTTP 状态码进行判定
  if (error.response?.status) {
    const status = error.response.status;
    /**
     * 判定准则：
     * 1. 5xx 系列服务器内部错误；
     * 2. 408 请求超时错误。
     */
    return status >= 500 || status === 408;
  }

  // 无状态码的网络级异常（如断网、DNS 故障、连接超时）判定为可重试
  return error.code === 'NETWORK_ERROR' || error.code === 'TIMEOUT';
};

/**
 * 通用异步延迟实用函数
 * 基于 Promise 封装的 setTimeout，用于在异步流中实现非阻塞暂停。
 * @function delay
 * @param {number} ms - 延迟时长（毫秒）
 */
const delay = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

/**
 * 执行全局错误处理器的初始化流程
 * 绑定全局事件监听器，准备接管未捕获的 Promise 异常。
 */
errorHandler.initialize();

/**
 * 模块导出定义
 * 提供单例 Axios 客户端及其关联的错误处理器。
 */
export { errorHandler };
export default client;