// src/frontend/src/utils/errorHandling.ts
import { BusinessError } from '../types';
import { message } from '../components/UI.tsx';

/**
 * 统一错误处理中间件和工具函数
 * 需求: 7.1, 7.2, 7.3, 7.4
 */

// 错误处理配置
export interface ErrorHandlingConfig {
  showUserFriendlyMessages: boolean;
  logErrors: boolean;
  enableRetry: boolean;
  maxRetries: number;
  retryDelay: number;
}

// 默认错误处理配置
export const defaultErrorConfig: ErrorHandlingConfig = {
  showUserFriendlyMessages: true,
  logErrors: true,
  enableRetry: true,
  maxRetries: 3,
  retryDelay: 1000,
};

// 错误分类处理器
export class ErrorHandler {
  private config: ErrorHandlingConfig;

  constructor(config: Partial<ErrorHandlingConfig> = {}) {
    this.config = { ...defaultErrorConfig, ...config };
  }

  /**
   * 处理业务错误
   * 需求 7.1: API返回业务错误时显示后端返回的message信息
   */
  handleBusinessError(error: BusinessError): void {
    if (this.config.logErrors) {
      console.error('Business Error:', {
        code: error.code,
        message: error.message,
        details: error.details,
        stack: error.stack,
      });
    }

    switch (true) {
      case error.isValidationError():
        this.handleValidationError(error);
        break;

      case error.isBusinessError():
        this.handleLogicError(error);
        break;

      case error.isPermissionError():
        this.handlePermissionError(error);
        break;

      case error.isHttpError():
        this.handleHttpError(error);
        break;

      case error.isSystemError():
        this.handleSystemError(error);
        break;

      default:
        this.handleUnknownError(error);
    }
  }

  /**
   * 处理验证错误 (10000-19999)
   */
  private handleValidationError(error: BusinessError): void {
    if (this.config.showUserFriendlyMessages) {
      // 显示具体的验证错误信息
      message.error(error.message || '输入数据验证失败');

      // 如果有详细的字段错误信息，可以进一步处理
      if (error.details && typeof error.details === 'object') {
        this.handleFieldErrors(error.details);
      }
    }
  }

  /**
   * 处理业务逻辑错误 (20000-29999)
   */
  private handleLogicError(error: BusinessError): void {
    if (this.config.showUserFriendlyMessages) {
      message.error(error.message || '操作失败，请检查操作条件');
    }
  }

  /**
   * 处理权限错误 (30000-39999)
   * 需求 7.4: 权限不足时显示权限错误提示并阻止操作
   */
  private handlePermissionError(error: BusinessError): void {
    if (this.config.showUserFriendlyMessages) {
      message.error(error.message || '权限不足，无法执行此操作');
    }

    // 可以触发权限相关的全局事件
    this.emitPermissionError(error);
  }

  /**
   * 处理系统错误 (50000+)
   */
  private handleSystemError(error: BusinessError): void {
    if (this.config.showUserFriendlyMessages) {
      message.error('系统错误，请稍后重试');
    }

    // 系统错误需要特别记录
    if (this.config.logErrors) {
      console.error('System Error - Requires attention:', error);
    }
  }

  /**
   * 处理HTTP错误 (400-599)
   */
  private handleHttpError(error: BusinessError): void {
    if (this.config.showUserFriendlyMessages) {
      // 显示后端返回的具体错误信息，而不是通用的系统错误
      message.error(error.message || '请求失败');
    }
  }

  /**
   * 处理未知错误
   */
  private handleUnknownError(error: BusinessError): void {
    if (this.config.showUserFriendlyMessages) {
      message.error(error.message || '操作失败');
    }
  }

  /**
   * 处理字段级验证错误
   */
  private handleFieldErrors(details: any): void {
    if (Array.isArray(details)) {
      // FastAPI 风格的验证错误
      details.forEach((fieldError: any) => {
        if (fieldError.msg && fieldError.loc) {
          const field = Array.isArray(fieldError.loc) ? fieldError.loc.join('.') : fieldError.loc;
          console.warn(`Field ${field}: ${fieldError.msg}`);
        }
      });
    } else if (typeof details === 'object') {
      // 自定义字段错误格式
      Object.entries(details).forEach(([field, error]) => {
        console.warn(`Field ${field}: ${error}`);
      });
    }
  }

  /**
   * 触发权限错误事件
   */
  private emitPermissionError(error: BusinessError): void {
    // 可以通过事件系统通知其他组件
    window.dispatchEvent(new CustomEvent('permission-error', {
      detail: { error }
    }));
  }
}

/**
 * HTTP错误处理器
 * 需求 7.2: 网络请求失败时显示网络错误提示
 * 需求 7.3: 认证失败时清除本地认证信息并提示重新登录
 */
export class HttpErrorHandler {
  private config: ErrorHandlingConfig;
  private lastErrorMessage: string = '';
  private lastErrorTime: number = 0;
  private readonly ERROR_DEBOUNCE_TIME = 3000; // 3秒内相同错误只显示一次

  constructor(config: Partial<ErrorHandlingConfig> = {}) {
    this.config = { ...defaultErrorConfig, ...config };
  }

  /**
   * 检查是否应该显示错误消息（防止重复提示）
   */
  private shouldShowError(errorMessage: string): boolean {
    const now = Date.now();
    if (errorMessage === this.lastErrorMessage && now - this.lastErrorTime < this.ERROR_DEBOUNCE_TIME) {
      return false;
    }
    this.lastErrorMessage = errorMessage;
    this.lastErrorTime = now;
    return true;
  }

  /**
   * 处理HTTP状态码错误
   */
  handleHttpError(status: number, data?: any): void {
    if (this.config.logErrors) {
      console.error('HTTP Error:', { status, data });
    }

    switch (status) {
      case 401:
        this.handleAuthenticationError(data);
        break;

      case 403:
        this.handleForbiddenError(data);
        break;

      case 404:
        this.handleNotFoundError(data);
        break;

      case 408:
        this.handleTimeoutError(data);
        break;

      case 429:
        this.handleRateLimitError(data);
        break;

      case 500:
      case 502:
      case 503:
      case 504:
        this.handleServerError(status, data);
        break;

      default:
        this.handleGenericHttpError(status, data);
    }
  }

  /**
   * 处理认证错误 (401)
   * 需求 7.3: 认证失败时清除本地认证信息并提示重新登录
   */
  private handleAuthenticationError(data?: any): void {
    // 清除本地认证信息
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_info');

    const errorMessage = '登录已过期，请重新登录';
    if (this.config.showUserFriendlyMessages && this.shouldShowError(errorMessage)) {
      message.error(errorMessage);
    }

    // 触发全局认证失效事件
    window.dispatchEvent(new CustomEvent('auth-expired'));

    // 可以自动跳转到登录页
    setTimeout(() => {
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }, 1500);
  }

  /**
   * 处理权限禁止错误 (403)
   */
  private handleForbiddenError(data?: any): void {
    const message_text = this.extractErrorMessage(data) || '权限不足，无法访问此资源';

    if (this.config.showUserFriendlyMessages && this.shouldShowError(message_text)) {
      message.error(message_text);
    }
  }

  /**
   * 处理资源不存在错误 (404)
   */
  private handleNotFoundError(data?: any): void {
    const message_text = this.extractErrorMessage(data) || '请求的资源不存在';

    if (this.config.showUserFriendlyMessages && this.shouldShowError(message_text)) {
      message.error(message_text);
    }
  }

  /**
   * 处理请求超时错误 (408)
   */
  private handleTimeoutError(data?: any): void {
    const errorMessage = '请求超时，请检查网络连接后重试';
    if (this.config.showUserFriendlyMessages && this.shouldShowError(errorMessage)) {
      message.error(errorMessage);
    }
  }

  /**
   * 处理请求频率限制错误 (429)
   */
  private handleRateLimitError(data?: any): void {
    const errorMessage = '请求过于频繁，请稍后再试';
    if (this.config.showUserFriendlyMessages && this.shouldShowError(errorMessage)) {
      message.error(errorMessage);
    }
  }

  /**
   * 处理服务器错误 (5xx)
   */
  private handleServerError(status: number, data?: any): void {
    if (this.config.showUserFriendlyMessages) {
      const message_text = status === 503
        ? '服务暂时不可用，请稍后重试'
        : '服务器内部错误，请稍后重试';
      
      if (this.shouldShowError(message_text)) {
        message.error(message_text);
      }
    }
  }

  /**
   * 处理通用HTTP错误
   */
  private handleGenericHttpError(status: number, data?: any): void {
    const message_text = this.extractErrorMessage(data) || '网络请求失败，请检查网络连接';

    if (this.config.showUserFriendlyMessages && this.shouldShowError(message_text)) {
      message.error(message_text);
    }
  }

  /**
   * 从错误响应中提取错误信息
   */
  private extractErrorMessage(data?: any): string | null {
    if (!data) return null;

    // UnifiedResponse 格式
    if (data.message) {
      return data.message;
    }

    // FastAPI 验证错误格式
    if (data.detail) {
      if (typeof data.detail === 'string') {
        return data.detail;
      }
      if (Array.isArray(data.detail) && data.detail.length > 0) {
        return data.detail[0]?.msg || data.detail[0] || null;
      }
    }

    // 其他格式
    if (data.error) {
      return typeof data.error === 'string' ? data.error : data.error.message;
    }

    return null;
  }
}

/**
 * 网络错误处理器
 * 需求 7.2: 网络请求失败时显示网络错误提示
 */
export class NetworkErrorHandler {
  private config: ErrorHandlingConfig;

  constructor(config: Partial<ErrorHandlingConfig> = {}) {
    this.config = { ...defaultErrorConfig, ...config };
  }

  /**
   * 处理网络连接错误
   */
  handleNetworkError(error: any): void {
    if (this.config.logErrors) {
      console.error('Network Error:', error);
    }

    let message_text = '网络连接失败，请检查网络设置';

    // 根据错误类型提供更具体的提示
    if (error.code === 'NETWORK_ERROR') {
      message_text = '网络连接中断，请检查网络连接';
    } else if (error.code === 'TIMEOUT') {
      message_text = '网络请求超时，请稍后重试';
    } else if (error.code === 'ECONNREFUSED') {
      message_text = '无法连接到服务器，请稍后重试';
    }

    if (this.config.showUserFriendlyMessages) {
      message.error(message_text);
    }
  }

  /**
   * 检查网络连接状态
   */
  checkNetworkStatus(): boolean {
    return navigator.onLine;
  }

  /**
   * 监听网络状态变化
   */
  setupNetworkStatusListener(): void {
    window.addEventListener('online', () => {
      if (this.config.showUserFriendlyMessages) {
        message.success('网络连接已恢复');
      }
    });

    window.addEventListener('offline', () => {
      if (this.config.showUserFriendlyMessages) {
        message.warning('网络连接已断开');
      }
    });
  }
}

/**
 * 全局错误处理器
 * 整合所有错误处理逻辑
 */
export class GlobalErrorHandler {
  private businessErrorHandler: ErrorHandler;
  private httpErrorHandler: HttpErrorHandler;
  private networkErrorHandler: NetworkErrorHandler;

  constructor(config: Partial<ErrorHandlingConfig> = {}) {
    this.businessErrorHandler = new ErrorHandler(config);
    this.httpErrorHandler = new HttpErrorHandler(config);
    this.networkErrorHandler = new NetworkErrorHandler(config);
  }

  /**
   * 统一错误处理入口
   */
  handleError(error: any): void {
    if (error instanceof BusinessError) {
      this.businessErrorHandler.handleBusinessError(error);
    } else if (error.response) {
      // HTTP 错误
      this.httpErrorHandler.handleHttpError(
        error.response.status,
        error.response.data
      );
    } else if (error.request) {
      // 网络错误
      this.networkErrorHandler.handleNetworkError(error);
    } else {
      // 其他错误
      console.error('Unknown Error:', error);
      if (error.message) {
        message.error(error.message);
      }
    }
  }

  /**
   * 初始化全局错误处理
   */
  initialize(): void {
    // 设置网络状态监听
    this.networkErrorHandler.setupNetworkStatusListener();

    // 设置全局错误捕获
    window.addEventListener('error', (event) => {
      console.error('Global Error:', event.error);
    });

    window.addEventListener('unhandledrejection', (event) => {
      console.error('Unhandled Promise Rejection:', event.reason);
      this.handleError(event.reason);
    });
  }
}

// 创建全局错误处理器实例
export const globalErrorHandler = new GlobalErrorHandler();

// 导出便捷函数
export const handleError = (error: any) => globalErrorHandler.handleError(error);
export const initializeErrorHandling = () => globalErrorHandler.initialize();