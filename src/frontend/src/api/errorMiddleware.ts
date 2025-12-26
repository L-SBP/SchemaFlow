// src/frontend/src/api/errorMiddleware.ts
import { AxiosError, AxiosResponse } from 'axios';
import { BusinessError, BusinessCode, UnifiedResponse } from '../types';
import { globalErrorHandler } from '../utils/errorHandling';

/**
 * API错误处理中间件
 * 需求: 7.1, 7.2, 7.3, 7.4
 */

/**
 * 响应拦截器中间件
 * 统一处理UnifiedResponse格式和错误
 */
export const responseInterceptor = (response: AxiosResponse) => {
  const data = response.data as UnifiedResponse;

  // 检查是否为 UnifiedResponse 格式
  if (data && typeof data === 'object' && 'code' in data && 'message' in data && 'data' in data) {
    // 检查业务状态码
    if (data.code !== BusinessCode.SUCCESS) {
      // 创建业务错误并立即显示
      const businessError = new BusinessError(data.code, data.message);
      globalErrorHandler.handleError(businessError);
      throw businessError;
    }

    // 返回业务数据
    return data.data;
  }

  // 向后兼容：如果不是 UnifiedResponse 格式，直接返回原数据
  return response.data;
};

/**
 * 错误拦截器中间件
 * 统一处理HTTP错误和网络错误
 */
export const errorInterceptor = (error: AxiosError) => {
  // 如果是BusinessError，说明已经在responseInterceptor中处理过了，直接抛出
  if (error instanceof BusinessError) {
    return Promise.reject(error);
  }

  // 处理HTTP错误和网络错误
  globalErrorHandler.handleError(error);
  return Promise.reject(error);
};

/**
 * API调用包装器
 * 为API调用添加统一的错误处理
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
    // 可以在这里添加loading状态管理
    if (showLoading) {
      // 显示loading
    }

    const result = await apiCall();

    if (showLoading) {
      // 隐藏loading
    }

    return result;
  } catch (error) {
    if (showLoading) {
      // 隐藏loading
    }

    // 如果有自定义错误处理器，使用它
    if (customErrorHandler) {
      customErrorHandler(error);
    } else if (!suppressGlobalError) {
      // 否则使用全局错误处理器
      globalErrorHandler.handleError(error);
    }

    throw error;
  }
};

/**
 * 批量API调用错误处理
 * 处理多个并发API调用的错误
 */
export const withBatchErrorHandling = async <T>(
  apiCalls: Array<() => Promise<T>>,
  options: {
    failFast?: boolean; // 是否在第一个错误时停止
    collectErrors?: boolean; // 是否收集所有错误
  } = {}
): Promise<{
  results: Array<T | null>;
  errors: Array<Error | null>;
  hasErrors: boolean;
}> => {
  const { failFast = false, collectErrors = true } = options;
  const results: Array<T | null> = [];
  const errors: Array<Error | null> = [];

  if (failFast) {
    // 快速失败模式：使用Promise.all
    try {
      const allResults = await Promise.all(apiCalls.map(call => call()));
      return {
        results: allResults,
        errors: new Array(allResults.length).fill(null),
        hasErrors: false,
      };
    } catch (error) {
      globalErrorHandler.handleError(error);
      throw error;
    }
  } else {
    // 收集所有结果和错误
    const promises = apiCalls.map(async (call, index) => {
      try {
        const result = await call();
        results[index] = result;
        errors[index] = null;
      } catch (error) {
        results[index] = null;
        errors[index] = error as Error;

        if (collectErrors) {
          globalErrorHandler.handleError(error);
        }
      }
    });

    await Promise.all(promises);

    return {
      results,
      errors,
      hasErrors: errors.some(error => error !== null),
    };
  }
};

/**
 * 条件错误处理
 * 根据条件决定是否处理错误
 */
export const withConditionalErrorHandling = async <T>(
  apiCall: () => Promise<T>,
  condition: (error: any) => boolean,
  customHandler?: (error: any) => void
): Promise<T> => {
  try {
    return await apiCall();
  } catch (error) {
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
 * 错误恢复包装器
 * 在错误时提供默认值或恢复逻辑
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
    const shouldAttemptRecovery = shouldRecover ? shouldRecover(error) : true;

    if (shouldAttemptRecovery) {
      if (recoveryFn) {
        try {
          return await recoveryFn(error);
        } catch (recoveryError) {
          globalErrorHandler.handleError(recoveryError);
          throw recoveryError;
        }
      } else if (defaultValue !== undefined) {
        return defaultValue;
      }
    }

    globalErrorHandler.handleError(error);
    throw error;
  }
};

/**
 * 错误统计和监控
 */
export class ErrorMonitor {
  private errorCounts: Map<string, number> = new Map();
  private errorHistory: Array<{
    timestamp: number;
    error: any;
    context?: string;
  }> = [];

  /**
   * 记录错误
   */
  recordError(error: any, context?: string): void {
    const errorKey = this.getErrorKey(error);
    const currentCount = this.errorCounts.get(errorKey) || 0;
    this.errorCounts.set(errorKey, currentCount + 1);

    this.errorHistory.push({
      timestamp: Date.now(),
      error,
      context,
    });

    // 保持历史记录在合理范围内
    if (this.errorHistory.length > 1000) {
      this.errorHistory = this.errorHistory.slice(-500);
    }
  }

  /**
   * 获取错误统计
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
   * 清除错误统计
   */
  clearStats(): void {
    this.errorCounts.clear();
    this.errorHistory = [];
  }

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

// 创建全局错误监控实例
export const errorMonitor = new ErrorMonitor();

// 扩展全局错误处理器以包含监控
const originalHandleError = globalErrorHandler.handleError.bind(globalErrorHandler);
globalErrorHandler.handleError = (error: any) => {
  errorMonitor.recordError(error);
  originalHandleError(error);
};