// src/frontend/src/api/errorIntegration.ts
/**
 * 错误处理集成示例和工具函数
 * 展示如何在所有API模块中集成统一错误处理机制
 * 需求: 7.1, 7.2, 7.3, 7.4
 */

import client from './client';
import {
  withErrorHandling,
  withBatchErrorHandling,
  withConditionalErrorHandling,
  withErrorRecovery,
  errorMonitor
} from './errorMiddleware';
import { BusinessError } from '../types';

/**
 * API调用示例：展示如何在各个API模块中使用错误处理
 */

// 1. 基础API调用（已通过拦截器自动处理错误）
export const basicApiCall = async () => {
  // 错误会被响应拦截器自动处理
  return client.get('/api/users');
};

// 2. 带自定义错误处理的API调用
export const apiCallWithCustomErrorHandling = async () => {
  return withErrorHandling(
    () => client.get('/api/sensitive-data'),
    {
      showLoading: true,
      customErrorHandler: (error) => {
        if (error instanceof BusinessError && error.isPermissionError()) {
          // 自定义权限错误处理
          console.log('Custom permission error handling');
        }
      }
    }
  );
};

// 3. 批量API调用错误处理
export const batchApiCalls = async () => {
  const apiCalls = [
    () => client.get('/api/users'),
    () => client.get('/api/projects'),
    () => client.get('/api/reports'),
  ];

  return withBatchErrorHandling(apiCalls, {
    failFast: false, // 不快速失败，收集所有结果
    collectErrors: true, // 收集并处理所有错误
  });
};

// 4. 条件错误处理
export const conditionalErrorHandling = async () => {
  return withConditionalErrorHandling(
    () => client.get('/api/optional-data'),
    (error) => {
      // 只处理非404错误
      return !(error.response?.status === 404);
    },
    (error) => {
      console.log('Handling non-404 error:', error);
    }
  );
};

// 5. 错误恢复机制
export const apiCallWithRecovery = async () => {
  return withErrorRecovery(
    () => client.get('/api/user-preferences'),
    {
      defaultValue: { theme: 'light', language: 'zh-CN' }, // 默认值
      shouldRecover: (error) => {
        // 只在网络错误时使用默认值
        return !error.response;
      }
    }
  );
};

// 6. 高级错误恢复（使用恢复函数）
export const apiCallWithAdvancedRecovery = async () => {
  return withErrorRecovery(
    () => client.get('/api/dynamic-config'),
    {
      recoveryFn: async (error) => {
        // 尝试从缓存获取配置
        const cachedConfig = localStorage.getItem('cached-config');
        if (cachedConfig) {
          return JSON.parse(cachedConfig);
        }
        // 如果没有缓存，返回默认配置
        return { version: '1.0.0', features: [] };
      },
      shouldRecover: (error) => {
        // 在服务器错误时尝试恢复
        return error.response?.status >= 500;
      }
    }
  );
};

/**
 * 特定业务场景的错误处理示例
 */

// 用户认证相关的错误处理
export const authApiCall = async (credentials: any) => {
  return withErrorHandling(
    () => client.post('/api/auth/login', credentials),
    {
      customErrorHandler: (error) => {
        if (error instanceof BusinessError) {
          if (error.code === 30001) {
            // 特定的认证错误处理
            console.log('Invalid credentials');
          }
        }
      }
    }
  );
};

// 文件上传的错误处理
export const fileUploadApiCall = async (formData: FormData) => {
  return withErrorHandling(
    () => client.post('/api/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000, // 文件上传需要更长的超时时间
    }),
    {
      showLoading: true,
      customErrorHandler: (error) => {
        if (error.code === 'TIMEOUT') {
          console.log('File upload timeout - file might be too large');
        }
      }
    }
  );
};

// 分页数据获取的错误处理
export const paginatedApiCall = async (page: number, pageSize: number) => {
  return withErrorRecovery(
    () => client.get(`/api/data?page=${page}&page_size=${pageSize}`),
    {
      recoveryFn: async (error) => {
        // 如果请求的页面不存在，回退到第一页
        if (error.response?.status === 404 && page > 1) {
          return client.get(`/api/data?page=1&page_size=${pageSize}`);
        }
        throw error;
      }
    }
  );
};

/**
 * 错误监控和统计工具
 */

// 获取错误统计信息
export const getErrorStats = () => {
  return errorMonitor.getErrorStats();
};

// 清除错误统计
export const clearErrorStats = () => {
  errorMonitor.clearStats();
};

// 检查系统健康状态
export const checkSystemHealth = () => {
  const stats = errorMonitor.getErrorStats();
  const recentErrorCount = stats.recentErrors.length;
  const totalErrorCount = stats.totalErrors;

  return {
    isHealthy: recentErrorCount < 5 && totalErrorCount < 50,
    errorCount: totalErrorCount,
    recentErrorCount,
    recommendation: recentErrorCount > 10
      ? '系统错误频繁，建议检查网络连接或联系技术支持'
      : '系统运行正常'
  };
};

/**
 * 错误处理配置管理
 */

// 开发环境错误处理配置
export const developmentErrorConfig = {
  showUserFriendlyMessages: true,
  logErrors: true,
  enableRetry: true,
  maxRetries: 2,
  retryDelay: 500,
};

// 生产环境错误处理配置
export const productionErrorConfig = {
  showUserFriendlyMessages: true,
  logErrors: false, // 生产环境可能不需要控制台日志
  enableRetry: true,
  maxRetries: 3,
  retryDelay: 1000,
};

// 测试环境错误处理配置
export const testErrorConfig = {
  showUserFriendlyMessages: false, // 测试时不显示用户消息
  logErrors: true,
  enableRetry: false, // 测试时不重试
  maxRetries: 0,
  retryDelay: 0,
};

/**
 * 错误处理最佳实践示例
 */

// 1. 关键业务操作的错误处理
export const criticalBusinessOperation = async (data: any) => {
  try {
    // 使用事务性操作
    const result = await withErrorHandling(
      () => client.post('/api/critical-operation', data),
      {
        customErrorHandler: (error) => {
          // 关键操作失败时的特殊处理
          console.error('Critical operation failed:', error);
          // 可能需要回滚或补偿操作
        }
      }
    );
    return result;
  } catch (error) {
    // 记录关键操作失败
    console.error('Critical business operation failed:', error);
    throw error;
  }
};

// 2. 用户体验优化的错误处理
export const userFriendlyApiCall = async () => {
  return withErrorRecovery(
    () => client.get('/api/user-data'),
    {
      defaultValue: null,
      recoveryFn: async (error) => {
        // 尝试从本地存储恢复数据
        const localData = localStorage.getItem('user-data-backup');
        if (localData) {
          return JSON.parse(localData);
        }
        return null;
      }
    }
  );
};

// 3. 性能监控相关的错误处理
export const performanceAwareApiCall = async () => {
  const startTime = Date.now();

  try {
    const result = await client.get('/api/performance-sensitive');
    const duration = Date.now() - startTime;

    // 记录性能指标
    if (duration > 5000) {
      console.warn('Slow API call detected:', duration + 'ms');
    }

    return result;
  } catch (error) {
    const duration = Date.now() - startTime;
    console.error('API call failed after', duration + 'ms', error);
    throw error;
  }
};