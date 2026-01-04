/**
 * @file errorHandling.ts
 * @module Utils/Global-Error-Management
 * @description 全局异常生命周期管理与错误分发系统。
 * 本模块作为系统的“可靠性哨兵”，深度集成于“基于大模型多智能体框架的数据库自动部署与库表生成系统”。
 * * 核心设计目标遵循：
 * 1. Reliability-3: 针对 AI 生成的错误 SQL 或数据库约束冲突，执行非崩溃式捕获与优雅反馈 。
 * 2. Usability-1: 将底层技术异常（如 500 错误、外键约束）转化为非技术用户可感知的语义化提示 。
 * 3. Security-2 & 3: 在 401/403 等鉴权失败场景下，执行敏感数据的物理清理与会话强制下线 [cite: 178, 549, 550]。
 * * 模块架构：
 * - ErrorHandler: 负责处理由后端 BusinessCode 显式抛出的逻辑错误。
 * - HttpErrorHandler: 负责处理标准 HTTP 协议层面的状态异常及会话失效。
 * - NetworkErrorHandler: 负责底层网络连通性、超时及重连策略的监控。
 * * @author Wang Lirong (王利蓉)
 * @version 2.5.0
 * @date 2026-01-02
 */

import { BusinessError } from '../types';
import { message } from '../components/UI.tsx';

let authRedirectScheduled = false;

const forceLogoutAndRedirectToLogin = (options?: { messageText?: string }) => {
  // 物理销毁本地所有敏感持久化信息，确保 JWT Token 不被滥用
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user_info');

  // 广播全局事件，由 WorkspaceWrapper 等组件捕获并停止心跳轮询
  window.dispatchEvent(new CustomEvent('auth-expired'));

  if (!authRedirectScheduled) {
    authRedirectScheduled = true;

    // 允许调用方自定义提示；默认提示保持与原有 401 行为一致
    const text = options?.messageText || '登录已过期，请重新登录';
    message.error(text);

    // 延时执行强制重定向逻辑，为用户预留阅读提示的时间。
    setTimeout(() => {
      authRedirectScheduled = false;
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }, 1500);
  }
};

const isTokenRevokedMessage = (msg: string): boolean => {
  const text = (msg || '').trim();
  if (!text) return false;
  return text.includes('令牌已被撤销') || text.toLowerCase().includes('token revoked') || text.toLowerCase().includes('revoked');
};

/**
 * 错误处理器的运行时配置接口定义
 * @interface ErrorHandlingConfig
 */
export interface ErrorHandlingConfig {
  /** 是否将技术性错误信息过滤为用户友好的语义描述 */
  showUserFriendlyMessages: boolean;
  /** 是否在控制台或远端审计系统中记录错误详情 */
  logErrors: boolean;
  /** 是否开启基于 API Client 策略的自动化重试 */
  enableRetry: boolean;
  /** 网络级错误触发重试的最大尝试次数 */
  maxRetries: number;
  /** 初始重试延迟基数（毫秒） */
  retryDelay: number;
}

/**
 * 系统默认错误处理策略配置
 * 对应非功能性需求中的“可用性”与“可靠性”基准线。
 */
export const defaultErrorConfig: ErrorHandlingConfig = {
  showUserFriendlyMessages: true,
  logErrors: true,
  enableRetry: true,
  maxRetries: 3,
  retryDelay: 1000,
};

/**
 * 业务逻辑错误分类处理器 (Business Logic Error Processor)
 * 专门解析后端返回的非 200 业务状态码，实现多维度的 UI 反馈。
 */
export class ErrorHandler {
  /** 处理器当前实例的私有配置快照 */
  private config: ErrorHandlingConfig;

  /**
   * 构造函数：实现配置项的深度合并
   * @param {Partial<ErrorHandlingConfig>} [config={}] - 可选的覆盖配置
   */
  constructor(config: Partial<ErrorHandlingConfig> = {}) {
    this.config = { ...defaultErrorConfig, ...config };
  }

  /**
   * 业务错误的分发处理总入口
   * 需求 7.1: 当后端返回业务逻辑冲突时，系统必须展示 message 字段包含的详情描述。
   * @method handleBusinessError
   * @param {BusinessError} error - 自定义的业务异常实例
   */
  handleBusinessError(error: BusinessError): void {
    // 步骤 1：审计记录。若配置开启，则将完整堆栈与详情记录至日志系统。
    if (this.config.logErrors) {
      console.error('Business Error:', {
        code: error.code,
        message: error.message,
        details: error.details,
        stack: error.stack,
      });
    }

    // 特判：后端 BusinessException 会以 HTTP 200 返回，但 code 字段可能携带 401/403 等语义。
    // 当 token 失效/被撤销时，必须强制下线并跳转登录页。
    if (error.isHttpError()) {
      if (error.code === 401) {
        forceLogoutAndRedirectToLogin({ messageText: error.message || '登录已过期，请重新登录' });
        return;
      }

      // 令牌被撤销通常以 403 + 特定 message 表达
      if (error.code === 403 && isTokenRevokedMessage(error.message)) {
        forceLogoutAndRedirectToLogin({ messageText: error.message || '登录状态已失效，请重新登录' });
        return;
      }
    }

    // 步骤 2：类型断言分发。根据不同的错误码区间，路由至特定的 UI 提示逻辑。
    switch (true) {
      // 区间 10000-19999：前端/后端表单验证异常
      case error.isValidationError():
        this.handleValidationError(error);
        break;

      // 区间 20000-29999：通用业务逻辑冲突（如：余额不足、重复创建）
      case error.isBusinessError():
        this.handleLogicError(error);
        break;

      // 区间 30000-39999：项目级权限越权尝试
      case error.isPermissionError():
        this.handlePermissionError(error);
        break;

      // HTTP 状态码映射转换错误
      case error.isHttpError():
        this.handleHttpError(error);
        break;

      // 区 lot 50000+：后端致命异常
      case error.isSystemError():
        this.handleSystemError(error);
        break;

      default:
        // 后向兼容处理：处理未定义码段的兜底逻辑
        this.handleUnknownError(error);
    }
  }

  /**
   * 详细处理验证错误 (10000-19999)
   * 通常发生在 Schema Agent 设计后的参数校对阶段 [cite: 341]。
   * @private
   */
  private handleValidationError(error: BusinessError): void {
    if (this.config.showUserFriendlyMessages) {
      // 步骤：向用户弹出具体的验证失败原因（如“项目名长度不符合规范”）
      message.error(error.message || '输入数据验证失败');

      // 步骤：针对复杂对象（如 DDL 参数），执行细粒度的字段级解析
      if (error.details && typeof error.details === 'object') {
        this.handleFieldErrors(error.details);
      }
    }
  }

  /**
   * 详细处理业务逻辑错误 (20000-29999)
   * 例如：用户尝试删除正在部署中的项目。
   * @private
   */
  private handleLogicError(error: BusinessError): void {
    if (this.config.showUserFriendlyMessages) {
      // 直接展示业务层透传的错误文本，保持语义的一致性
      message.error(error.message || '操作失败，请检查操作条件');
    }
  }

  /**
   * 详细处理权限错误 (30000-39999)
   * 需求 7.4: 权限不足时，系统必须立即中断当前 UI 操作流，并显示拒绝访问提示 [cite: 329]。
   * @private
   */
  private handlePermissionError(error: BusinessError): void {
    if (this.config.showUserFriendlyMessages) {
      message.error(error.message || '权限不足，无法执行此操作');
    }

    // 步骤：通过 DOM 消息总线触发权限相关的全局通知逻辑
    this.emitPermissionError(error);
  }

  /**
   * 详细处理系统级崩溃错误 (50000+)
   * 旨在屏蔽底层敏感信息（如 Python 报错栈），提供统一的受挫提示。
   * @private
   */
  private handleSystemError(error: BusinessError): void {
    if (this.config.showUserFriendlyMessages) {
      message.error('系统错误，请稍后重试');
    }

    // 步骤：此类错误被标记为高优先级审计，通常需要运维人员介入。
    if (this.config.logErrors) {
      console.error('System Error - Requires attention:', error);
    }
  }

  /**
   * 处理 HTTP 转换后的业务异常
   * @private
   */
  private handleHttpError(error: BusinessError): void {
    if (this.config.showUserFriendlyMessages) {
      // 避免使用模糊的“请求失败”，尽可能从 response body 中提取原始反馈。
      message.error(error.message || '请求失败');
    }
  }

  /**
   * 兜底处理器：捕获所有不符合预定义协议的未知异常
   * @private
   */
  private handleUnknownError(error: BusinessError): void {
    if (this.config.showUserFriendlyMessages) {
      message.error(error.message || '操作失败');
    }
  }

  /**
   * 字段级深度验证解析器
   * 特别针对 FastAPI 的 ValidationError (Pydantic 风格) 进行结构化拆解。
   * @private
   * @param {any} details - 错误详情对象或数组
   */
  private handleFieldErrors(details: any): void {
    if (Array.isArray(details)) {
      // 解析典型的 loc 路径及 msg 信息，例如：body.project_name 过短
      details.forEach((fieldError: any) => {
        if (fieldError.msg && fieldError.loc) {
          const field = Array.isArray(fieldError.loc) ? fieldError.loc.join('.') : fieldError.loc;
          console.warn(`Field ${field}: ${fieldError.msg}`);
        }
      });
    } else if (typeof details === 'object') {
      // 处理自定义的键值对错误格式
      Object.entries(details).forEach(([field, error]) => {
        console.warn(`Field ${field}: ${error}`);
      });
    }
  }

  /**
   * 发射全局权限异常事件
   * 允许 Header 或 Sidebar 等独立组件感知并调整 UI 展示状态。
   * @private
   */
  private emitPermissionError(error: BusinessError): void {
    window.dispatchEvent(new CustomEvent('permission-error', {
      detail: { error }
    }));
  }
}

/**
 * HTTP 协议层错误处理器 (Transport Layer Error Handler)
 * 对应需求 7.2: 全局监控网络请求状态，当发生断网或超时时，立即响应。
 * 对应需求 7.3: 当接收到 401 响应时，执行“会话隔离清理”逻辑。
 */
export class HttpErrorHandler {
  private config: ErrorHandlingConfig;
  /** 记录最近一次错误消息，用于简单的去抖动处理 */
  private lastErrorMessage: string = '';
  /** 记录最近一次错误发生的时间戳 */
  private lastErrorTime: number = 0;
  /** 定义错误气泡的消隐间隔（3秒），防止在高频请求下的 UI 提示堆叠 */
  private readonly ERROR_DEBOUNCE_TIME = 3000;

  constructor(config: Partial<ErrorHandlingConfig> = {}) {
    this.config = { ...defaultErrorConfig, ...config };
  }

  /**
   * 错误消息节流逻辑
   * 确保相同类型的技术报错不会在短时间内重复打扰用户。
   * @private
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
   * HTTP 状态码标准化处理流程
   * 根据 RFC 7231 规范对返回的状态码进行业务语义映射。
   * @method handleHttpError
   * @param {number} status - HTTP 状态码
   * @param {any} [data] - 响应体原始数据
   */
  handleHttpError(status: number, data?: any): void {
    if (this.config.logErrors) {
      console.error('HTTP Error:', { status, data });
    }

    switch (status) {
      case 401:
        // 鉴权失败：Token 过期或非法
        this.handleAuthenticationError(data);
        break;

      case 403:
        // 禁止访问：当前用户无权访问目标资源
        this.handleForbiddenError(data);
        break;

      case 404:
        // 路由不存在或数据库项目记录已销毁
        this.handleNotFoundError(data);
        break;

      case 408:
        // 请求超时：后端 Agent 响应耗时超过 30s 预设阈值 [cite: 55-60]
        this.handleTimeoutError(data);
        break;

      case 429:
        // 请求频率限制：触发系统防火墙限流策略
        this.handleRateLimitError(data);
        break;

      case 500:
      case 502:
      case 503:
      case 504:
        // 服务端集群异常处理
        this.handleServerError(status, data);
        break;

      default:
        // 未定义的 HTTP 网络异常
        this.handleGenericHttpError(status, data);
    }
  }

  /**
   * 详细处理认证失效 (401 Unauthorized)
   * 需求 7.3: 一旦认证失效，必须物理清除本地缓存的凭证，强制跳转至登录页以保证安全 [cite: 326-327, 463]。
   * @private
   */
  private handleAuthenticationError(_data?: any): void {
    if (!this.config.showUserFriendlyMessages) {
      // 仍需强制登出，但不弹提示
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_info');
      window.dispatchEvent(new CustomEvent('auth-expired'));
      setTimeout(() => {
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }, 0);
      return;
    }

    // 复用统一登出逻辑（含去抖与延时跳转）
    forceLogoutAndRedirectToLogin({ messageText: '登录已过期，请重新登录' });
  }

  /**
   * 处理权限禁止错误 (403 Forbidden)
   * @private
   */
  private handleForbiddenError(data?: any): void {
    const message_text = this.extractErrorMessage(data) || '权限不足，无法访问此资源';

    if (this.config.showUserFriendlyMessages && this.shouldShowError(message_text)) {
      message.error(message_text);
    }
  }

  /**
   * 处理资源不存在错误 (404 Not Found)
   * @private
   */
  private handleNotFoundError(data?: any): void {
    const message_text = this.extractErrorMessage(data) || '请求的资源不存在';

    if (this.config.showUserFriendlyMessages && this.shouldShowError(message_text)) {
      message.error(message_text);
    }
  }

  /**
   * 处理请求超时错误 (408 Request Timeout)
   * 对应非功能性需求 Performance1 指标响应。
   * @private
   */
  private handleTimeoutError(_data?: any): void {
    const errorMessage = '请求超时，请检查网络连接后重试';
    if (this.config.showUserFriendlyMessages && this.shouldShowError(errorMessage)) {
      message.error(errorMessage);
    }
  }

  /**
   * 处理请求频率限制错误 (429 Too Many Requests)
   * @private
   */
  private handleRateLimitError(_data?: any): void {
    const errorMessage = '请求过于频繁，请稍后再试';
    if (this.config.showUserFriendlyMessages && this.shouldShowError(errorMessage)) {
      message.error(errorMessage);
    }
  }

  /**
   * 处理服务器内部错误 (5xx Server Errors)
   * @private
   */
  private handleServerError(status: number, _data?: any): void {
    if (this.config.showUserFriendlyMessages) {
      // 区分 503 维护状态与通用的 500 内部崩溃
      const message_text = status === 503
        ? '服务暂时不可用，请稍后重试'
        : '服务器内部错误，请稍后重试';

      if (this.shouldShowError(message_text)) {
        message.error(message_text);
      }
    }
  }

  /**
   * 处理未分类的通用 HTTP 错误
   * @private
   */
  private handleGenericHttpError(_status: number, data?: any): void {
    const message_text = this.extractErrorMessage(data) || '网络请求失败，请检查网络连接';

    if (this.config.showUserFriendlyMessages && this.shouldShowError(message_text)) {
      message.error(message_text);
    }
  }

  /**
   * 深度提取响应体中的错误描述信息
   * 适配 UnifiedResponse, FastAPI Detail, 以及标准 Error 对象。
   * @private
   * @param {any} data - 响应数据
   * @returns {string | null}
   */
  private extractErrorMessage(data?: any): string | null {
    if (!data) return null;

    // 格式 1：系统预设的 UnifiedResponse 包装
    if (data.message) {
      return data.message;
    }

    // 格式 2：FastAPI 自动生成的验证细节
    if (data.detail) {
      if (typeof data.detail === 'string') {
        return data.detail;
      }
      if (Array.isArray(data.detail) && data.detail.length > 0) {
        // 提取 Pydantic 抛出的第一条验证失败消息
        return data.detail[0]?.msg || data.detail[0] || null;
      }
    }

    // 格式 3：标准 JSON 错误响应
    if (data.error) {
      return typeof data.error === 'string' ? data.error : data.error.message;
    }

    return null;
  }
}

/**
 * 网络级异常处理器 (Connectivity Layer Error Handler)
 * 对应需求 7.2: 专门负责捕获由网卡、路由器或 DNS 层面引发的物理层连接失败。
 */
export class NetworkErrorHandler {
  private config: ErrorHandlingConfig;

  constructor(config: Partial<ErrorHandlingConfig> = {}) {
    this.config = { ...defaultErrorConfig, ...config };
  }

  /**
   * 处理无响应的底层网络连接错误
   * @method handleNetworkError
   * @param {any} error - 原始网络异常对象
   */
  handleNetworkError(error: any): void {
    if (this.config.logErrors) {
      console.error('Network Error:', error);
    }

    let message_text = '网络连接失败，请检查网络设置';

    // 步骤：根据 Axios 返回的错误枚举，提供极其精确的故障排查指引
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
   * 利用浏览器原生 Navigator 接口实时检测在线状态
   * @returns {boolean}
   */
  checkNetworkStatus(): boolean {
    return navigator.onLine;
  }

  /**
   * 注册全局网络状态变更监听器
   * 增强 Usability-1，通过顶部提示即时通知用户当前连通性。
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
 * 全局中央错误处理器 (Unified Central Error Handler)
 * 采用了门面模式 (Facade Pattern)，整合了业务层、传输层及物理层的异常分发逻辑。
 * 它是前端稳定性工程的唯一入口。
 */
export class GlobalErrorHandler {
  private businessErrorHandler: ErrorHandler;
  private httpErrorHandler: HttpErrorHandler;
  private networkErrorHandler: NetworkErrorHandler;

  /**
   * 构造函数：初始化所有特定的子处理器
   * @param {Partial<ErrorHandlingConfig>} [config={}]
   */
  constructor(config: Partial<ErrorHandlingConfig> = {}) {
    this.businessErrorHandler = new ErrorHandler(config);
    this.httpErrorHandler = new HttpErrorHandler(config);
    this.networkErrorHandler = new NetworkErrorHandler(config);
  }

  /**
   * 统一错误分发算法
   * 将拦截到的各种未知类型的 error 按照优先级进行评估并路由。
   * @method handleError
   * @param {any} error - 被捕获的异常对象
   */
  handleError(error: any): void {
    // 优先级 1：由 responseInterceptor 识别并抛出的业务逻辑错误
    if (error instanceof BusinessError) {
      this.businessErrorHandler.handleBusinessError(error);
    }
    // 优先级 2：由 Axios 识别的 HTTP 响应层错误 (status code >= 400)
    else if (error.response) {
      this.httpErrorHandler.handleHttpError(
        error.response.status,
        error.response.data
      );
    }
    // 优先级 3：请求已发起但未收到响应（如 DNS 失败、连接超时）
    else if (error.request) {
      this.networkErrorHandler.handleNetworkError(error);
    }
    // 优先级 4：代码执行期异常或其他未知逻辑错误
    else {
      console.error('Unknown Error:', error);
      if (error.message) {
        message.error(error.message);
      }
    }
  }

  /**
   * 全局异常捕获环境初始化
   * 绑定 window 级别的未捕获事件，作为系统最后一道防线。
   */
  initialize(): void {
    // 设置浏览器网络状态感知
    this.networkErrorHandler.setupNetworkStatusListener();

    // 监听同步代码执行中的未捕获异常
    window.addEventListener('error', (event) => {
      console.error('Global Error:', event.error);
    });

    // 监听异步 Promise 流中遗漏的 catch 异常
    // 确保任何 API 调用失败都能被正确处理 [cite: 543]
    window.addEventListener('unhandledrejection', (event) => {
      console.error('Unhandled Promise Rejection:', event.reason);
      this.handleError(event.reason);
    });
  }
}

/**
 * 创建单例模式的全局错误处理器实例
 * 确保整个 Web 应用在运行时共享同一套错误处理配置与状态记录。
 */
export const globalErrorHandler = new GlobalErrorHandler();

/**
 * 便捷导出函数：支持解构调用以简化代码。
 */
export const handleError = (error: any) => globalErrorHandler.handleError(error);

/**
 * 初始化应用级错误监控环境。
 */
export const initializeErrorHandling = () => globalErrorHandler.initialize();