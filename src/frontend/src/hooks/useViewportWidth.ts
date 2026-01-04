/**
 * @file useViewportWidth.ts
 * @module Hooks/Responsive-Layout
 * @description 响应式视口感知与断点分发钩子。
 * 本模块是系统“多分辨率适配”策略的核心实现工具，旨在提供实时、高性能的视口维度监控。
 * * 核心设计目标：
 * 1. 响应式布局：基于行业标准的断点协议（xs/sm/md/lg/xl）自动识别当前显示环境；
 * 2. 性能优化：通过内置的“事件防抖 (Debounce)”机制，有效抑制浏览器 resize 期间的重绘压力；
 * 3. 跨设备兼容：同步监听 orientationchange 事件，确保移动端横竖屏切换时的布局准确性。
 * * 对应需求：
 * - Requirement 1.1: 界面多分辨率自适应能力。
 * * @author Wang Lirong (王利蓉)
 * @version 2.2.0
 * @date 2026-01-02
 */

import { useState, useEffect } from 'react';

/**
 * 响应式断点标识符类型定义
 * @typedef {('xs' | 'sm' | 'md' | 'lg' | 'xl')} BreakpointId
 * @description 遵循现代 CSS 框架（如 Bootstrap/Tailwind）的栅格化语义。
 */
export type BreakpointId = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

/**
 * 视口状态详情信息接口
 * @interface ViewportWidthInfo
 * @description 封装了当前浏览器的物理维度及派生的逻辑断点状态。
 */
export interface ViewportWidthInfo {
  /** 当前视口的实时物理宽度（单位：像素 px） */
  width: number;
  /** 当前视口的实时物理高度（单位：像素 px） */
  height: number;
  /** 当前所属的响应式断点标识，用于组件侧的条件分支逻辑 */
  breakpoint: BreakpointId;
  /** * 语义化断点检查快捷对象 
   * 提供一组布尔值，用于模板中快速判断设备类型。
   */
  is: {
    /** 极小屏幕：通常指小屏手机 (width < 480px) */
    xs: boolean;    
    /** 小屏幕：大屏手机或竖屏平板 (480px - 768px) */
    sm: boolean;    
    /** 中等屏幕：横屏平板 (768px - 1024px) */
    md: boolean;    
    /** 大屏幕：笔记本或小尺寸显示器 (1024px - 1440px) */
    lg: boolean;    
    /** 超大屏幕：2K/4K 专业显示器 (width > 1440px) */
    xl: boolean;    
    /** 业务定义：移动端视图（合并 xs 与 sm） */
    mobile: boolean;    
    /** 业务定义：平板端视图（对应 md 档） */
    tablet: boolean;    
    /** 业务定义：桌面端视图（对应 lg 及以上） */
    desktop: boolean;   
  };
}

/**
 * 响应式断点物理阈值定义
 * @constant BREAKPOINTS
 * @description 严格对接设计稿的 UI 规范，作为视口识别的基准线。
 */
export const BREAKPOINTS = {
  /** 超小屏幕起始像素 */
  xs: 0,      
  /** 小屏幕阈值 (480px) */
  sm: 480,    
  /** 中等屏幕阈值 (768px) */
  md: 768,    
  /** 大屏幕阈值 (1024px) */
  lg: 1024,   
  /** 超大屏幕阈值 (1440px) */
  xl: 1440,   
} as const;

/**
 * 内部辅助算法：根据物理宽度映射至断点标识符
 * 执行标准的区间判定逻辑，返回当前视口所在的离散化档位。
 * @function getBreakpointId
 * @param {number} width - 待校验的视口宽度
 * @returns {BreakpointId} 匹配的断点 ID
 */
function getBreakpointId(width: number): BreakpointId {
  if (width < BREAKPOINTS.sm) return 'xs';
  if (width < BREAKPOINTS.md) return 'sm';
  if (width < BREAKPOINTS.lg) return 'md';
  if (width < BREAKPOINTS.xl) return 'lg';
  return 'xl';
}

/**
 * 内部辅助工厂：创建具备语义化布尔属性的断点检查对象
 * 旨在降低业务组件在处理响应式逻辑时的代码复杂度。
 * @function createBreakpointChecks
 * @param {number} width - 物理宽度
 * @param {BreakpointId} breakpoint - 档位 ID
 */
function createBreakpointChecks(width: number, breakpoint: BreakpointId) {
  return {
    // 精确档位判定
    xs: breakpoint === 'xs',
    sm: breakpoint === 'sm',
    md: breakpoint === 'md',
    lg: breakpoint === 'lg',
    xl: breakpoint === 'xl',
    // 聚合业务档位判定
    mobile: width < BREAKPOINTS.md,      // 判定依据：宽度小于 768px 被视为广义移动端
    tablet: width >= BREAKPOINTS.md && width < BREAKPOINTS.lg,  // 判定依据：768px 至 1023px
    desktop: width >= BREAKPOINTS.lg,    // 判定依据：1024px 以上进入桌面级交互模式
  };
}

/**
 * 内部状态机：计算并刷新当前完整的视口上下文信息
 * 封装了对浏览器全局 window 对象的直接访问逻辑。
 * @function calculateViewportInfo
 * @returns {ViewportWidthInfo}
 */
function calculateViewportInfo(): ViewportWidthInfo {
  // 获取浏览器视口的实时几何尺寸
  const width = window.innerWidth;
  const height = window.innerHeight;
  
  // 识别当前宽度所属的档位
  const breakpoint = getBreakpointId(width);
  // 生成语义化布尔对象
  const is = createBreakpointChecks(width, breakpoint);

  return {
    width,
    height,
    breakpoint,
    is,
  };
}

/**
 * 视口宽度监听自定义 Hook
 * @export @function useViewportWidth
 * @description 
 * 为组件提供对窗口缩放事件的感知能力。
 * 内置“防抖 (Debounce)”策略，有效防止在连续拖拽窗口大小时触发高频的 React 状态更新，
 * 从而显著降低页面的脚本执行负担和重排 (Reflow) 频率。
 * * @param {number} [debounceMs=100] - 防抖触发延迟（毫秒）。较高的值可提升性能，较低的值可增强响应实时性。
 * @returns {ViewportWidthInfo} 实时更新的视口元数据
 */
export function useViewportWidth(debounceMs: number = 100): ViewportWidthInfo {
  /**
   * 步骤 1：状态初始化。
   * 使用惰性初始化模式执行初次视口信息采集，确保服务端渲染 (SSR) 期间的安全。
   */
  const [viewportInfo, setViewportInfo] = useState<ViewportWidthInfo>(() => calculateViewportInfo());

  useEffect(() => {
    // 引用定时器 ID，用于防抖逻辑的清理
    let timeoutId: NodeJS.Timeout | null = null;

    /** 窗口缩放事件的回调封装 */
    const updateViewportInfo = () => {
      // 步骤 2：防抖逻辑介入。
      // 若在 debounceMs 毫秒内再次触发 resize，则撤销之前的更新任务。
      if (timeoutId) {
        clearTimeout(timeoutId);
      }

      // 步骤 3：设定延时更新任务。
      // 仅在浏览器停止缩放动作后指定的毫秒数，才正式计算视口信息。
      timeoutId = setTimeout(() => {
        const newViewportInfo = calculateViewportInfo();
        setViewportInfo(newViewportInfo);
        timeoutId = null;
      }, debounceMs);
    };

    /**
     * 步骤 4：注册系统级监听器。
     * 除了标准的 resize，还监听 orientationchange 以适配平板/手机的物理旋转操作。
     */
    window.addEventListener('resize', updateViewportInfo);
    window.addEventListener('orientationchange', updateViewportInfo);

    // 步骤 5：Effect 清理阶段。
    // 销毁监听器并清除未执行的定时器，防止内存泄漏。
    return () => {
      window.removeEventListener('resize', updateViewportInfo);
      window.removeEventListener('orientationchange', updateViewportInfo);

      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [debounceMs]); // 依赖项：仅当用户改变防抖策略时重新绑定

  return viewportInfo;
}

/**
 * 精简版视口宽度监听 Hook
 * @export @function useViewportWidthOnly
 * @description 
 * 适用于仅关注宽度数值、无需断点判断的轻量级场景（如：Canvas 动态绘图大小计算）。
 * @param {number} [debounceMs=100]
 * @returns {number} 当前视口物理宽度像素值
 */
export function useViewportWidthOnly(debounceMs: number = 100): number {
  const { width } = useViewportWidth(debounceMs);
  return width;
}

/**
 * 断点逻辑匹配 Hook (Conditional Matching)
 * @export @function useBreakpointMatch
 * @description 
 * 支持“多对一”匹配。常用于根据断点动态渲染不同的子组件或逻辑块。
 * @param {(BreakpointId | BreakpointId[] | 'mobile' | 'tablet' | 'desktop')} breakpoint - 待检查的一个或一组断点
 * @param {number} [debounceMs=100]
 * @returns {boolean} 当前视口是否命中了指定的断点条件
 */
export function useBreakpointMatch(
  breakpoint: BreakpointId | BreakpointId[] | 'mobile' | 'tablet' | 'desktop',
  debounceMs: number = 100
): boolean {
  // 从核心 Hook 中提取语义判定对象
  const { is } = useViewportWidth(debounceMs);

  // 分支逻辑：处理断点数组（如：['xs', 'sm'] 代表“是否为移动端”）
  if (Array.isArray(breakpoint)) {
    return breakpoint.some(bp => is[bp]);
  }

  // 默认逻辑：单一档位匹配
  return is[breakpoint as keyof typeof is];
}

export default useViewportWidth;