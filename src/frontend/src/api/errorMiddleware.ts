/**
 * @file errorMiddleware.ts
 * @module Middleware/API-Error
 * @description 统一 API 错误处理与响应拦截中间件。
 * 本模块作为前端与后端 RESTful API 交互的逻辑哨兵，主要职能包括：
 * 1. 响应解包与统一格式校验：处理后端定义的 UnifiedResponse 结构；
 * 2. 业务状态码 (BusinessCode) 转换：将后端逻辑异常映射为前端 BusinessError [cite: 543]；
 * 3. 异步任务容错包装：提供多种高级包装器（如 Fail-Fast, Batch-Handling）以提升系统可靠性；
 * 4. 实时错误监控与审计：结合 ErrorMonitor 类实现前端运行时的异常轨迹记录。
 * @author Wang Lirong (王利蓉)
 * @version 2.2.0
 * @date 2026-01-02
 */

import { AxiosError, AxiosResponse } from 'axios';
import { BusinessError, BusinessCode, UnifiedResponse } from '../types';
import { globalErrorHandler } from '../utils/errorHandling';

/**
 * API 错误处理中间件逻辑定义
 * 对应项目需求规格说明书中的全局稳定性保障条款：
 * 7.1 系统一致性 | 7.2 异常捕获策略 | 7.3 用户友好提示 | 7.4 监控审计集成 [cite: 187, 542]
 */

/**
 * 响应拦截器 (Response Interceptor)
 * 核心职能：对 Axios 返回的原始响应进行预处理，提取业务载荷并处理潜在的逻辑错误。
 * 该拦截器确保了业务代码可以直接接收到 data 字段中的有效信息，而无需重复判断响应状态。
 * @function responseInterceptor
 * @param {AxiosResponse} response - Axios 原始响应对象
 * @throws {BusinessError} 当后端返回的业务 code 不为 SUCCESS 时抛出
 * @returns {any} 剥离包装后的纯业务数据
 */
export const responseInterceptor = (response: AxiosResponse) => {
  // 获取后端统一返回格式的数据载荷
  const data = response.data as UnifiedResponse;

  // 步骤 1：检查返回数据是否符合系统预设的 UnifiedResponse 协议
  // 必须同时包含 code, message 和 data 三个核心字段 [cite: 183]
  if (data && typeof data === 'object' && 'code' in data && 'message' in data && 'data' in data) {
    
    // 步骤 2：验证业务状态码
    // 若 code 不等于 200 (Success)，则判定为业务逻辑层面的异常
    if (data.code !== BusinessCode.SUCCESS) {
      // 创建业务异常实例，并立即交由全局处理器进行 UI 弹窗提示
      const businessError = new BusinessError(data.code, data.message);
      globalErrorHandler.handleError(businessError);
      
      // 阻断 Promise 链，将控制权交给调用方的 catch 块
      throw businessError;
    }

    // 步骤 3：业务逻辑正常，直接透传有效数据载荷
    return data.data;
  }

  // 向后兼容处理：若返回数据不符合 UnifiedResponse 格式，则原样返回以防止系统解析崩溃
  return response.data;
};

/**
 * 错误拦截器 (Error Interceptor)
 * 核心职能：统一拦截所有非 2xx 状态码的 HTTP 错误及由于网络断开导致的物理连接错误。
 * @function errorInterceptor
 * @param {AxiosError} error - Axios 捕获的原始错误实例
 * @returns {Promise<never>}
 */
export const errorInterceptor = (error: AxiosError) => {
  // 判定分支：如果是 BusinessError，说明拦截器 responseInterceptor 已先行处理
  // 此处仅执行 Promise 的拒绝操作，避免二次弹窗提示
  if (error instanceof BusinessError) {
    return Promise.reject(error);
  }

  // 针对物理网络故障、DNS 失败或 HTTP 状态码错误（如 401, 500 等）调用全局处理器 [cite: 540-541]
  globalErrorHandler.handleError(error);
  return Promise.reject(error);
};

/**
 * API 调用高阶包装器
 * 核心职能：为单次异步 API 调用提供标准化的 Loading 状态管理和错误拦截逻辑。
 * 旨在简化页面组件代码，实现声明式的异常处理。
 * @async
 * @function withErrorHandling
 * @template T
 * @param {Function} apiCall - 待执行的异步业务请求闭包
 * @param {Object} [options] - 配置参数
 * @param {boolean} [options.showLoading=false] - 是否自动触发全局 Loading 蒙层
 * @param {Function} [options.customErrorHandler] - 可选的自定义错误处理逻辑，若提供则跳过全局处理
 * @param {boolean} [options.suppressGlobalError=false] - 是否静默处理错误（不显示提示框）
 * @returns {Promise<T>}
 */
export const withErrorHandling = async <T>(
  apiCall: () => Promise<T>,
  options: {
    showLoading?: boolean;
    customErrorHandler?: (error: any) => void;
    suppressGlobalError?: boolean;
  } = {}
): Promise<T> => {
  const { showLoading = false, customErrorHandler, suppressGlobalError = false } = options;

  try {
    // 处理请求前的 UI 反馈逻辑
    if (showLoading) {
      // 执行 Loading 开启逻辑（如调用 store.dispatch('showLoading')）
    }

    // 执行核心异步业务逻辑
    const result = await apiCall();

    // 请求成功，关闭 UI 反馈
    if (showLoading) {
      // 执行 Loading 隐藏逻辑
    }

    return result;
  } catch (error) {
    // 异常发生，确保 UI 反馈被正确回收
    if (showLoading) {
      // 执行 Loading 隐藏逻辑
    }

    // 步骤评估：判定采用哪种错误反馈策略
    if (customErrorHandler) {
      // 策略 A：采用业务方提供的特定错误处理器
      customErrorHandler(error);
    } else if (!suppressGlobalError) {
      // 策略 B：默认策略，交由全局统一处理模块进行用户反馈（SF10 账户提示等） [cite: 463]
      globalErrorHandler.handleError(error);
    }

    // 重新抛出，允许调用方感知失败并执行后续清理
    throw error;
  }
};

/**
 * 批量 API 调用错误管理策略
 * 核心职能：针对并发执行的多个 API 请求，提供“快速失败”或“全量收集”两种控制流模式。
 * 适用于如批量创建数据库表 (SF2) 或同步更新多项业务术语 (SF7) 的场景 [cite: 436, 444]。
 * @async
 * @function withBatchErrorHandling
 * @template T
 * @param {Array<Function>} apiCalls - 异步请求闭包数组
 * @param {Object} [options]
 * @param {boolean} [options.failFast=false] - 快速失败模式：任一请求失败则终止全体流程
 * @param {boolean} [options.collectErrors=true] - 是否自动上报各子请求的错误
 */
export const withBatchErrorHandling = async <T>(
  apiCalls: Array<() => Promise<T>>,
  options: {
    failFast?: boolean; 
    collectErrors?: boolean; 
  } = {}
): Promise<{
  results: Array<T | null>;
  errors: Array<Error | null>;
  hasErrors: boolean;
}> => {
  const { failFast = false, collectErrors = true } = options;
  const results: Array<T | null> = [];
  const errors: Array<Error | null> = [];

  // 分支逻辑 1：快速失败模式 (Fail-Fast Strategy)
  if (failFast) {
    try {
      // 使用 Promise.all 触发并发，利用其原生短路机制
      const allResults = await Promise.all(apiCalls.map(call => call()));
      return {
        results: allResults,
        errors: new Array(allResults.length).fill(null),
        hasErrors: false,
      };
    } catch (error) {
      // 捕获到首个错误即停止，并上报全局
      globalErrorHandler.handleError(error);
      throw error;
    }
  } else {
    // 分支逻辑 2：全量收集模式 (Collect-All Strategy)
    // 确保即使部分任务失败，其他子任务也能继续执行并记录结果
    const promises = apiCalls.map(async (call, index) => {
      try {
        const result = await call();
        results[index] = result;
        errors[index] = null;
      } catch (error) {
        results[index] = null;
        errors[index] = error as Error;

        // 若开启监控，则将每一个独立错误同步至全局处理器
        if (collectErrors) {
          globalErrorHandler.handleError(error);
        }
      }
    });

    // 等待所有并行任务（无论成功失败）最终结算
    await Promise.all(promises);

    return {
      results,
      errors,
      hasErrors: errors.some(error => error !== null),
    };
  }
};

/**
 * 条件式错误处理包装器
 * 核心职能：仅在满足特定断言条件时触发错误提示逻辑。
 * @async
 * @function withConditionalErrorHandling
 */
export const withConditionalErrorHandling = async <T>(
  apiCall: () => Promise<T>,
  condition: (error: any) => boolean,
  customHandler?: (error: any) => void
): Promise<T> => {
  try {
    return await apiCall();
  } catch (error) {
    // 步骤：评估错误是否符合预期的处理条件
    if (condition(error)) {
      if (customHandler) {
        customHandler(error);
      } else {
        globalErrorHandler.handleError(error);
      }
    }
    throw error;
  }
};

/**
 * 错误恢复与容错包装器 (Resilience Wrapper)
 * 核心职能：在 API 调用失败时，通过预设的默认值或补偿逻辑维持业务连续性。
 * 符合可靠性需求中的系统稳定性目标 [cite: 541]。
 * @async
 * @function withErrorRecovery
 */
export const withErrorRecovery = async <T>(
  apiCall: () => Promise<T>,
  recovery: {
    defaultValue?: T;
    recoveryFn?: (error: any) => T | Promise<T>;
    shouldRecover?: (error: any) => boolean;
  }
): Promise<T> => {
  const { defaultValue, recoveryFn, shouldRecover } = recovery;

  try {
    return await apiCall();
  } catch (error) {
    // 判定逻辑：当前错误场景是否允许执行恢复
    const shouldAttemptRecovery = shouldRecover ? shouldRecover(error) : true;

    if (shouldAttemptRecovery) {
      // 策略 A：执行特定的补偿函数
      if (recoveryFn) {
        try {
          return await recoveryFn(error);
        } catch (recoveryError) {
          globalErrorHandler.handleError(recoveryError);
          throw recoveryError;
        }
      } else if (defaultValue !== undefined) {
        // 策略 B：回退至预设的静态默认值
        return defaultValue;
      }
    }

    // 若不符合恢复条件或无恢复策略，则正常抛出异常并上报
    globalErrorHandler.handleError(error);
    throw error;
  }
};

/**
 * 运行时错误监控类 (Error Monitor)
 * 核心职能：实现前端运行时的异常数据记录与审计。
 * 为管理员提供“系统监控与分析” (SF11) 的原始数据支撑 [cite: 107, 218]。
 */
export class ErrorMonitor {
  // 错误类型统计字典
  private errorCounts: Map<string, number> = new Map();
  // 最近错误历史队列
  private errorHistory: Array<{
    timestamp: number;
    error: any;
    context?: string;
  }> = [];

  /**
   * 记录并归档当前捕获的错误
   * @method recordError
   * @param {any} error - 捕获的异常实例
   * @param {string} [context] - 错误发生的业务上下文描述
   */
  recordError(error: any, context?: string): void {
    const errorKey = this.getErrorKey(error);
    const currentCount = this.errorCounts.get(errorKey) || 0;
    this.errorCounts.set(errorKey, currentCount + 1);

    // 记录详细的时间戳及上下文信息，便于故障回溯 [cite: 542]
    this.errorHistory.push({
      timestamp: Date.now(),
      error,
      context,
    });

    // 步骤：维持固定窗口大小的本地历史记录，防止内存溢出
    if (this.errorHistory.length > 1000) {
      this.errorHistory = this.errorHistory.slice(-500);
    }
  }

  /**
   * 获取当前系统的实时错误统计报告
   * 常用于管理员仪表盘 (Dashboard) 的数据渲染 [cite: 253, 742]
   */
  getErrorStats(): {
    totalErrors: number;
    errorsByType: Record<string, number>;
    recentErrors: Array<any>;
  } {
    const totalErrors = Array.from(this.errorCounts.values()).reduce((sum, count) => sum + count, 0);
    const errorsByType = Object.fromEntries(this.errorCounts);
    const recentErrors = this.errorHistory.slice(-10);

    return {
      totalErrors,
      errorsByType,
      recentErrors,
    };
  }

  /**
   * 重置监控统计数据
   * @method clearStats
   */
  clearStats(): void {
    this.errorCounts.clear();
    this.errorHistory = [];
  }

  /**
   * 内部方法：生成错误的唯一标识键
   * 区分业务错误、HTTP 错误及网络级故障
   * @private
   */
  private getErrorKey(error: any): string {
    if (error instanceof BusinessError) {
      return `BusinessError_${error.code}`;
    }
    if (error.response?.status) {
      return `HttpError_${error.response.status}`;
    }
    if (error.code) {
      return `NetworkError_${error.code}`;
    }
    return 'UnknownError';
  }
}

// 创建单例模式的全局错误监控实例
export const errorMonitor = new ErrorMonitor();

/**
 * 装饰器/拦截模式：扩展全局错误处理器
 * 确保每一次通过 globalErrorHandler 的调用都会同步被监控器记录
 */
const originalHandleError = globalErrorHandler.handleError.bind(globalErrorHandler);
globalErrorHandler.handleError = (error: any) => {
  // 1. 同步执行审计记录逻辑
  errorMonitor.recordError(error);
  // 2. 执行原始的用户提示/反馈逻辑
  originalHandleError(error);
};