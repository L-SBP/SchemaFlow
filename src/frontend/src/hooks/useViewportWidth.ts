import { useState, useEffect } from 'react';

/**
 * 视口宽度监听 Hook
 * 
 * 监听视口宽度变化并返回当前宽度和对应的响应式断点标识
 * 用于实现响应式布局和断点适配
 * 
 * Requirements: 1.1
 */

export type BreakpointId = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

export interface ViewportWidthInfo {
  /** 当前视口宽度（像素） */
  width: number;
  /** 当前视口高度（像素） */
  height: number;
  /** 当前断点标识 */
  breakpoint: BreakpointId;
  /** 断点检查函数 */
  is: {
    xs: boolean;    // < 480px
    sm: boolean;    // 480px - 768px
    md: boolean;    // 768px - 1024px
    lg: boolean;    // 1024px - 1440px
    xl: boolean;    // > 1440px
    mobile: boolean;    // < 768px
    tablet: boolean;    // 768px - 1024px
    desktop: boolean;   // > 1024px
  };
}

/**
 * 响应式断点定义
 * 基于设计文档中的断点策略
 */
export const BREAKPOINTS = {
  xs: 0,      // 0px - 479px
  sm: 480,    // 480px - 767px
  md: 768,    // 768px - 1023px
  lg: 1024,   // 1024px - 1439px
  xl: 1440,   // 1440px+
} as const;

/**
 * 根据宽度确定断点标识
 * 
 * @param width 视口宽度
 * @returns 断点标识
 */
function getBreakpointId(width: number): BreakpointId {
  if (width < BREAKPOINTS.sm) return 'xs';
  if (width < BREAKPOINTS.md) return 'sm';
  if (width < BREAKPOINTS.lg) return 'md';
  if (width < BREAKPOINTS.xl) return 'lg';
  return 'xl';
}

/**
 * 创建断点检查对象
 * 
 * @param width 视口宽度
 * @param breakpoint 当前断点
 * @returns 断点检查对象
 */
function createBreakpointChecks(width: number, breakpoint: BreakpointId) {
  return {
    xs: breakpoint === 'xs',
    sm: breakpoint === 'sm',
    md: breakpoint === 'md',
    lg: breakpoint === 'lg',
    xl: breakpoint === 'xl',
    mobile: width < BREAKPOINTS.md,      // < 768px
    tablet: width >= BREAKPOINTS.md && width < BREAKPOINTS.lg,  // 768px - 1023px
    desktop: width >= BREAKPOINTS.lg,    // >= 1024px
  };
}

/**
 * 计算当前视口信息
 * 
 * @returns ViewportWidthInfo 视口宽度信息
 */
function calculateViewportInfo(): ViewportWidthInfo {
  const width = window.innerWidth;
  const height = window.innerHeight;
  const breakpoint = getBreakpointId(width);
  const is = createBreakpointChecks(width, breakpoint);

  return {
    width,
    height,
    breakpoint,
    is,
  };
}

/**
 * 视口宽度监听 Hook
 * 
 * 监听视口宽度变化，返回当前视口宽度和断点标识
 * 支持防抖以提高性能
 * 
 * @param debounceMs 防抖延迟时间（毫秒），默认为 100ms
 * @returns ViewportWidthInfo 视口宽度信息
 */
export function useViewportWidth(debounceMs: number = 100): ViewportWidthInfo {
  const [viewportInfo, setViewportInfo] = useState<ViewportWidthInfo>(() => calculateViewportInfo());

  useEffect(() => {
    let timeoutId: NodeJS.Timeout | null = null;

    const updateViewportInfo = () => {
      // 清除之前的防抖定时器
      if (timeoutId) {
        clearTimeout(timeoutId);
      }

      // 设置新的防抖定时器
      timeoutId = setTimeout(() => {
        const newViewportInfo = calculateViewportInfo();
        setViewportInfo(newViewportInfo);
        timeoutId = null;
      }, debounceMs);
    };

    // 监听窗口大小变化
    window.addEventListener('resize', updateViewportInfo);

    // 监听方向变化（移动设备）
    window.addEventListener('orientationchange', updateViewportInfo);

    return () => {
      window.removeEventListener('resize', updateViewportInfo);
      window.removeEventListener('orientationchange', updateViewportInfo);

      // 清理防抖定时器
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [debounceMs]);

  return viewportInfo;
}

/**
 * 简化版视口宽度 Hook
 * 
 * 只返回当前视口宽度，不包含断点信息
 * 适用于只需要宽度数值的场景
 * 
 * @param debounceMs 防抖延迟时间（毫秒），默认为 100ms
 * @returns 当前视口宽度
 */
export function useViewportWidthOnly(debounceMs: number = 100): number {
  const { width } = useViewportWidth(debounceMs);
  return width;
}

/**
 * 断点匹配 Hook
 * 
 * 检查当前视口是否匹配指定的断点条件
 * 
 * @param breakpoint 要检查的断点或断点数组
 * @param debounceMs 防抖延迟时间（毫秒），默认为 100ms
 * @returns 是否匹配指定断点
 */
export function useBreakpointMatch(
  breakpoint: BreakpointId | BreakpointId[] | 'mobile' | 'tablet' | 'desktop',
  debounceMs: number = 100
): boolean {
  const { is } = useViewportWidth(debounceMs);

  if (Array.isArray(breakpoint)) {
    return breakpoint.some(bp => is[bp]);
  }

  return is[breakpoint as keyof typeof is];
}

export default useViewportWidth;