/**
 * @file project-overview.ts
 * @module Utils/UI-Optimization-Engine
 * @description 项目概览视图优化引擎工具集。
 * 本模块作为前端“项目仪表盘”的核心表现层驱动，专门用于解决大规模数据展示时的 UI 瓶颈。
 * * 核心功能涵盖：
 * 1. 动态文本截断算法：支持基于字符数及物理像素宽度的多维度截断逻辑（Usability-1）；
 * 2. 增强型 Canvas 文本测绘：利用离屏渲染技术精确计算字符串在不同字体下的物理占位；
 * 3. 语义化日期处理系统：实现基于当前时间差值的相对时间转换（如“今天 HH:mm”），符合 Format3 标准；
 * 4. 视口感知碰撞检测：计算 Tooltip 在极端边界情况下的自动位移与翻转坐标。
 * * @author Wang Lirong (王利蓉)
 * @version 2.3.1 (Hotfix: Unused parameter resolution)
 * @date 2026-01-02
 */

import { PROJECT_NAME_MAX_LENGTH } from '../constants/project-overview';

/**
 * 通用文本截断算法
 * 需求 3.1: 针对项目名称执行强制长度约束。
 * * 逻辑说明：
 * 若文本长度超过阈值，执行物理切割并追加省略号，确保栅格布局不会因内容溢出而崩塌。
 * * @function truncateText
 * @param {string} text - 待处理的原始字符串
 * @param {number} [maxLength=PROJECT_NAME_MAX_LENGTH] - 允许的最大逻辑长度（字符数）
 * @returns {string} 处理后的截断文本
 */
export function truncateText(text: string, maxLength: number = PROJECT_NAME_MAX_LENGTH): string {
  // 分支判定：内容未达阈值，直接返回原样引用以节省处理开销
  if (text.length <= maxLength) {
    return text;
  }
  // 截取前 maxLength 位字符并拼接半角省略号
  return text.substring(0, maxLength) + '...';
}

/**
 * 专用于项目名称的截断器
 * 需求 3.1: 强制项目名称在看板视图下截断至预设的 6 字符阈值。
 * * @function truncateProjectName
 * @param {string} projectName - 项目名称原文
 */
export function truncateProjectName(projectName: string): string {
  return truncateText(projectName, PROJECT_NAME_MAX_LENGTH);
}

/**
 * 智能描述文本截断（基于可用空间估算）
 * 需求 7.1: 根据项目卡片的实时物理宽度进行描述信息的自适应截断。
 * * 算法特性：
 * 1. 引入了“单词边界保护”机制（针对英文环境）；
 * 2. 允许指定单字符平均物理占位（characterWidth）。
 * * @function truncateDescription
 * @param {string} description - 业务需求描述文本
 * @param {number} availableWidth - 当前卡片容器可用的物理宽度（px）
 * @param {number} [characterWidth=8] - 预估的单字符平均宽度因子
 */
export function truncateDescription(description: string, availableWidth: number, characterWidth: number = 8): string {
  // 空值守卫
  if (!description) {
    return '';
  }

  // 步骤 1：基于可用像素宽度计算理论最大容纳字符数
  const maxCharacters = Math.floor(availableWidth / characterWidth);

  // 步骤 2：容量检查
  if (description.length <= maxCharacters) {
    return description;
  }

  // 步骤 3：尝试执行“词汇友好型”截断
  const truncated = description.substring(0, maxCharacters);
  const lastSpaceIndex = truncated.lastIndexOf(' ');

  /**
   * 启发式修正：若在截断点前 70% 范围内存在空格，则在空格处切断，
   * 避免将一个英文单词从中间强行拆分，提升语义连贯性。
   */
  if (lastSpaceIndex > maxCharacters * 0.7) {
    return truncated.substring(0, lastSpaceIndex) + '...';
  }

  // 兜底策略：若无合适词界，执行字符级硬截断
  return truncated + '...';
}

/**
 * 文本截断状态预测器
 * 用于在渲染前判断是否需要挂载 Tooltip 悬停提示组件。
 * * @function needsTruncation
 */
export function needsTruncation(text: string, maxLength: number = PROJECT_NAME_MAX_LENGTH): boolean {
  return text.length > maxLength;
}

/**
 * 描述信息截断状态预测器
 * 需求 7.1: 评估当前卡片空间是否足以完整显示业务场景描述。
 * * @function descriptionNeedsTruncation
 */
export function descriptionNeedsTruncation(description: string, availableWidth: number, characterWidth: number = 8): boolean {
  if (!description) {
    return false;
  }

  const maxCharacters = Math.floor(availableWidth / characterWidth);
  return description.length > maxCharacters;
}

/**
 * 高精度文本物理宽度测绘工具
 * 需求 3.5: 解决在复杂渲染环境下，逻辑字符数与物理像素宽度不匹配的问题。
 * * 技术实现：
 * 利用单例 Canvas API 执行 Off-screen 测绘。若环境不支持（如 SSR），则切换至逻辑预估算法。
 * * @function measureTextWidth
 * @param {string} text - 目标文本内容
 * @param {number} [fontSize=14] - 渲染时的逻辑像素字号
 * @param {string} [fontFamily='Arial'] - 应用的字体族
 * @returns {number} 文本在视口中实际占用的像素宽度 (px)
 */
export function measureTextWidth(text: string, fontSize: number = 14, fontFamily: string = 'Arial'): number {
  if (!text || typeof text !== 'string') {
    return 0;
  }

  // 步骤 1：探测宿主环境兼容性，确保 SSR 或测试脚本不抛出异常
  try {
    if (typeof document === 'undefined' || typeof window === 'undefined') {
      // 容错分支：基于统计学常数 0.6 估算平均宽度因子
      return text.length * (fontSize * 0.6);
    }

    // 步骤 2：初始化离屏 Canvas 测绘上下文
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');

    if (context) {
      // 注入目标样式参数
      context.font = `${fontSize}px ${fontFamily}`;
      // 执行原生 TextMetrics 测量
      const metrics = context.measureText(text);
      return metrics.width;
    }
  } catch (error) {
    // 异常拦截：当 Canvas 指纹保护等隐私设置导致 API 受限时，执行备选预估方案
    console.warn('Canvas text measurement failed, using fallback:', error);
  }

  // 步骤 3：通用兜底策略
  return text.length * (fontSize * 0.6);
}

/**
 * 物理像素级精准截断算法
 * 需求 3.5: 针对非定宽容器，计算最匹配可用空间的文本子集。
 * * 算法策略：
 * 采用二分搜索（Binary Search）优化截断性能，将 O(n) 的测量复杂度降低至 O(log n)。
 * * @function truncateToWidth
 * @param {string} text - 原始文本
 * @param {number} maxWidth - 容器允许的最大物理像素值 (px)
 */
export function truncateToWidth(text: string, maxWidth: number, fontSize: number = 14, fontFamily: string = 'Arial'): string {
  if (!text) {
    return '';
  }

  // 先检查全量渲染是否符合空间约束
  const fullWidth = measureTextWidth(text, fontSize, fontFamily);

  if (fullWidth <= maxWidth) {
    return text;
  }

  /**
   * 二分搜索执行逻辑：
   * 旨在快速定位“能容纳下”与“溢出”临界点之间的最大索引位。
   */
  let left = 0;
  let right = text.length;
  let bestFit = '';

  while (left <= right) {
    const mid = Math.floor((left + right) / 2);
    const candidate = text.substring(0, mid) + '...';
    // 执行 Canvas 实时测距
    const candidateWidth = measureTextWidth(candidate, fontSize, fontFamily);

    if (candidateWidth <= maxWidth) {
      // 当前长度可行，尝试向右探测更大的容量
      bestFit = candidate;
      left = mid + 1;
    } else {
      // 当前长度溢出，向左收缩查找空间
      right = mid - 1;
    }
  }

  return bestFit || '...';
}

/**
 * 语义化项目日期格式化引擎
 * 需求 8.1: 实现标准 YYYY-MM-DD HH:mm 展示。
 * 需求 8.5: 引入相对时间感知，增强对今日（Today）活动的识别度。
 * * @function formatProjectDate
 * @param {string} dateString - 符合 ISO 8601 标准的原始时间戳字符串
 * @returns {string} 用户友好的格式化日期
 */
export function formatProjectDate(dateString: string): string {
  try {
    const date = new Date(dateString);

    // 类型安全性校验：拦截解析失败的 Date 对象
    if (isNaN(date.getTime())) {
      return 'Invalid Date';
    }

    // 步骤 1：获取基准时间。计算当前“今日 0 点”的时间戳。
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate());

    // 步骤 2：判定是否为“今日”发生的业务活动
    if (dateOnly.getTime() === today.getTime()) {
      const hours = date.getHours().toString().padStart(2, '0');
      const minutes = date.getMinutes().toString().padStart(2, '0');
      // 增强 UX：展示为“今天 HH:mm”
      return `今天 ${hours}:${minutes}`;
    }

    /**
     * 步骤 3：常规日期转换。
     * 遵循 ISO 8601 补零规范，输出符合业务文档要求的标准格式。
     */
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');

    return `${year}-${month}-${day} ${hours}:${minutes}`;
  } catch (error) {
    // 异常恢复逻辑
    return 'Invalid Date';
  }
}

/**
 * 视口感知型 Tooltip 坐标计算算法
 * 需求 2.4: 精确控制浮窗位置，防止 UI 元素超出屏幕可视区域（Viewport Collision Detection）。
 * * 核心逻辑：
 * 1. 计算首选位置（Top/Bottom/Left/Right）；
 * 2. 执行屏幕边界审计，若发生溢出则自动执行“镜像翻转”或“强制校正”。
 * * @function calculateTooltipPosition
 */
export function calculateTooltipPosition(
  cardElement: HTMLElement,
  tooltipElement: HTMLElement,
  preferredPlacement: 'top' | 'bottom' | 'left' | 'right' = 'top'
): { x: number; y: number; placement: 'top' | 'bottom' | 'left' | 'right' } {
  try {
    // 参数验证：确保 DOM 节点已完成渲染且可被测量
    if (!cardElement || !tooltipElement) {
      console.warn('Invalid elements provided to calculateTooltipPosition');
      return { x: 0, y: 0, placement: 'top' };
    }

    // 调用浏览器原生 API 获取几何属性矩阵
    const cardRect = cardElement.getBoundingClientRect();
    const tooltipRect = tooltipElement.getBoundingClientRect();

    // 几何矩阵存在性检查
    if (!cardRect || !tooltipRect) {
      console.warn('Could not get element rectangles for tooltip positioning');
      return { x: 0, y: 0, placement: 'top' };
    }

    // 建立视口边界快照
    const viewport = {
      width: window.innerWidth || 1024, 
      height: window.innerHeight || 768, 
    };

    let x = 0;
    let y = 0;
    let placement = preferredPlacement;

    /**
     * 步骤 1：基于业务偏好方位计算初步相对坐标。
     * 每个分支均计算水平/垂直对齐及 8px 的视觉边距偏移。
     */
    switch (preferredPlacement) {
      case 'top':
        x = cardRect.left + cardRect.width / 2 - tooltipRect.width / 2;
        y = cardRect.top - tooltipRect.height - 8;
        break;
      case 'bottom':
        x = cardRect.left + cardRect.width / 2 - tooltipRect.width / 2;
        y = cardRect.bottom + 8;
        break;
      case 'left':
        x = cardRect.left - tooltipRect.width - 8;
        y = cardRect.top + cardRect.height / 2 - tooltipRect.height / 2;
        break;
      case 'right':
        x = cardRect.right + 8;
        y = cardRect.top + cardRect.height / 2 - tooltipRect.height / 2;
        break;
      default:
        // 兜底逻辑：默认上方居中
        x = cardRect.left + cardRect.width / 2 - tooltipRect.width / 2;
        y = cardRect.top - tooltipRect.height - 8;
        placement = 'top';
    }

    /**
     * 步骤 2：自适应碰撞检测（Collision Detection）。
     * 若计算出的 X/Y 轴坐标导致 Tooltip 溢出视口，则触发位移修正或对位翻转。
     */
    if (x < 8) {
      x = 8;
      if (placement === 'left') placement = 'right';
    }
    if (x + tooltipRect.width > viewport.width - 8) {
      x = viewport.width - tooltipRect.width - 8;
      if (placement === 'right') placement = 'left';
    }
    if (y < 8) {
      y = 8;
      if (placement === 'top') placement = 'bottom';
    }
    if (y + tooltipRect.height > viewport.height - 8) {
      y = viewport.height - tooltipRect.height - 8;
      if (placement === 'bottom') placement = 'top';
    }

    // 最终数值清洗：确保返回的是合法的非负像素值
    x = isNaN(x) ? 0 : Math.max(0, x);
    y = isNaN(y) ? 0 : Math.max(0, y);

    return { x, y, placement };
  } catch (error) {
    // 全局防崩溃兜底方案
    console.error('Error calculating tooltip position:', error);
    return { x: 0, y: 0, placement: 'top' };
  }
}

/**
 * 初始交互坐标计算引擎
 * 用于在鼠标首次进入（MouseEnter）时，快速锚定 Tooltip 的入场位置。
 * * * 架构标注：
 * 此处参数 _mouseEvent 前缀下划线，符合 TypeScript 强制性规范中对“占位符变量”的显式声明要求。
 * 旨在为后续版本的“动态光标追随”特性预留 API 接口定义，当前计算逻辑暂仅依赖 cardElement 的几何边界。
 * * * @function calculateTooltipPositionFromEvent
 * @param {HTMLElement} cardElement - 触发悬停的项目卡片 DOM 实例
 * @param {React.MouseEvent} _mouseEvent - React 原始鼠标事件（预留扩展参数）
 */
export function calculateTooltipPositionFromEvent(
  cardElement: HTMLElement,
  _mouseEvent: React.MouseEvent<HTMLDivElement>
): { x: number; y: number; placement: 'top' | 'bottom' | 'left' | 'right' } {
  try {
    if (!cardElement) {
      console.warn('Invalid card element provided to calculateTooltipPositionFromEvent');
      return { x: 0, y: 0, placement: 'top' };
    }

    const cardRect = cardElement.getBoundingClientRect();

    if (!cardRect) {
      console.warn('Could not get card rectangle for tooltip positioning');
      return { x: 0, y: 0, placement: 'top' };
    }

    // 设置默认中心悬停坐标。逻辑实现上，我们当前优先保证 Tooltip 的居中对称美感。
    const x = cardRect.left + cardRect.width / 2;
    const y = cardRect.top - 8;

    const safeX = isNaN(x) ? 0 : Math.max(0, x);
    const safeY = isNaN(y) ? 0 : Math.max(0, y);

    return { x: safeX, y: safeY, placement: 'top' };
  } catch (error) {
    console.error('Error calculating tooltip position from event:', error);
    return { x: 0, y: 0, placement: 'top' };
  }
}

/**
 * 项目状态多语言标签映射器
 * 将后端枚举值转换为符合用户认知的中文语义描述。
 * @param {'initializing' | 'active' | 'inactive'} status - 项目原始状态码
 */
export function getProjectStatusLabel(status: 'initializing' | 'active' | 'inactive'): string {
  const statusLabels = {
    initializing: '部署中',
    active: '运行中',
    inactive: '非活跃',
  };
  return statusLabels[status] || status;
}

/**
 * 项目状态枚举合法性校验器
 */
export function isValidProjectStatus(status: string): status is 'initializing' | 'active' | 'inactive' {
  return ['initializing', 'active', 'inactive'].includes(status);
}

/**
 * 动态样式类映射器
 * 根据项目状态返回对应的 BEM 规范 CSS 类名，用于 Badge 组件的着色。
 */
export function getStatusBadgeColorClass(status: 'initializing' | 'active' | 'inactive'): string {
  switch (status) {
    case 'initializing':
      return 'status-badge--initializing';
    case 'active':
      return 'status-badge--active';
    case 'inactive':
      return 'status-badge--inactive';
    default:
      return 'status-badge--inactive';
  }
}