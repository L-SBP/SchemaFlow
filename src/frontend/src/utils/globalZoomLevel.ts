/**
 * @file globalZoomLevel.ts
 * @module Utils/UI-Adaptation
 * @description 全局浏览器缩放感应与响应式缩放补偿系统。
 * 本模块是系统“用户友好交互 (Usability-1)”设计理念在底层视觉表现上的核心支撑。
 * * 核心解决痛点：
 * 1. 解决非技术用户在开启高倍率浏览器缩放（高达 500%）时，页面布局产生毁灭性错位的问题；
 * 2. 针对高分辨率设备（如 MacBook Retina 屏幕）与普通显示器的 DPR (Device Pixel Ratio) 差异进行平滑适配；
 * 3. 计算反向缩放因子 (Scale Factor)，为图形组件（如动态 ER 图）提供视觉补偿参数。
 * * 对应需求：
 * - SF5: 结果可视化（图形组件需感知缩放以维持坐标准确）
 * - Usability-1: 无需培训，各分辨率下均可直观操作
 * * @author Wang Lirong (王利蓉)
 * @version 2.1.0
 * @date 2026-01-02
 */

import { useState, useEffect } from 'react';

/**
 * 全局缩放级别状态详情接口
 * @interface GlobalZoomLevelInfo
 * @description 封装了从硬件像素层到应用逻辑层的所有关键视口元数据。
 */
export interface GlobalZoomLevelInfo {
  /** 当前用户设置的浏览器缩放级别（百分比数值，范围通常在 50 至 500 之间） */
  zoomLevel: number;
  /** 布尔标识：是否处于高缩放模式（>200%），用于触发移动端样式降级 */
  isHighZoom: boolean;
  /** 布尔标识：是否处于极高缩放模式（>300%），用于隐藏非核心装饰元素 */
  isExtremeZoom: boolean;
  /** 原始设备像素比，反映物理像素与逻辑像素的比例关系 */
  devicePixelRatio: number;
  /** 当前视口的物理逻辑宽度（单位：px） */
  viewportWidth: number;
  /** 当前视口的物理逻辑高度（单位：px） */
  viewportHeight: number;
  /** * 建议的全局缩放补偿因子。
   * 该值通过特定对数算法计算，用于 CSS transform: scale() 以部分抵消浏览器强制缩放带来的影响。
   */
  globalScaleFactor: number;
  /** 细化缩放阈值检测状态，供业务组件进行条件渲染判定 */
  thresholds: {
    /** 是否跨越 300% 阈值 */
    above300: boolean;
    /** 是否跨越 400% 阈值 */
    above400: boolean;
    /** 是否跨越 500% 极高阈值 */
    above500: boolean;
  };
}

/**
 * 核心算法：计算全局反向缩放补偿因子
 * * 设计背景：
 * 当用户放大浏览器至 400% 时，标准 UI 元素会变得极其庞大导致溢出。
 * 本函数通过计算一个介于 0.35 到 1.0 之间的因子，允许组件“适度缩小”以抵消部分溢出效果。
 * * 计算公式：
 * scaleFactor = clamp(min, max, (100 / zoomLevel) ^ power)
 * 其中 power = 0.7 用于实现“非线性部分抵消”，保留用户预期的适度放大感，同时兼顾布局完整性。
 * * @function calculateGlobalScaleFactor
 * @param {number} zoomLevel - 当前检测到的缩放百分比
 * @returns {number} 经过四舍五入的缩放因子（保留两位小数）
 */
export function calculateGlobalScaleFactor(zoomLevel: number): number {
  // 步骤 1：定义感知阈值。低于 125% 的缩放被视为标准视觉环境，不执行任何补偿。
  if (zoomLevel <= 125) {
    return 1.0;
  }

  /**
   * 步骤 2：执行幂函数计算反向缩放比。
   * power < 1 (0.7) 意味着我们只抵消约 70% 的缩放幅度，剩余 30% 留给系统原生表现。
   */
  const power = 0.7; 
  const rawFactor = Math.pow(100 / zoomLevel, power);

  /**
   * 步骤 3：范围裁剪 (Clamping)。
   * 限制最小补偿值为 0.35，防止在 500% 缩放时 UI 元素被过度缩小导致无法阅读。
   */
  const clampedFactor = Math.max(0.35, Math.min(1.0, rawFactor));

  // 步骤 4：执行数值修约，防止浮点数计算误差导致 CSS 渲染抖动。
  return Math.round(clampedFactor * 100) / 100;
}

/**
 * 核心算法：精确探测浏览器当前缩放级别
 * * 算法说明：
 * 1. 硬件级感知：利用 window.devicePixelRatio 作为核心输入参数；
 * 2. 屏幕特征评估：结合 screen.width 指标动态评估基础 DPR（区分 Retina 与普通屏）；
 * 3. 视口逆推：在极端宽度（宽度极窄）下执行启发式修正，以准确捕获 400%+ 的缩放；
 * 4. 离散化修正：将原始数值映射到最接近的标准浏览器缩放梯度（如 150, 175, 200）。
 * * @function calculateGlobalZoomLevel
 * @returns {GlobalZoomLevelInfo} 包含全量视口审计信息的对象
 */
function calculateGlobalZoomLevel(): GlobalZoomLevelInfo {
  // 获取环境原始数据
  const devicePixelRatio = window.devicePixelRatio || 1;
  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;

  // 步骤 1：基础 DPR (Base Device Pixel Ratio) 估算
  // 逻辑：在 4K 或 MacBook 等高分屏上，默认 DPR 为 2，此时 100% 缩放表现为 pixelRatio=2
  const screenWidth = window.screen.width;
  const screenHeight = window.screen.height;

  let baseDPR = 1;
  /**
   * 基于屏幕物理特征的分支判定逻辑：
   * 情况 A：超高分辨率屏幕（>= 2.5K），基础 DPR 通常设为 2。
   */
  if (screenWidth >= 2560 || screenHeight >= 1440) {
    baseDPR = 2; 
  } 
  /**
   * 情况 B：普通高清屏（1080P），但系统缩放倍率不为 1。
   */
  else if (screenWidth >= 1920 && devicePixelRatio >= 1.5) {
    baseDPR = devicePixelRatio > 2 ? 2 : 1;
  }

  // 步骤 2：计算相对缩放比例（当前 DPR / 硬件基础 DPR）
  const relativeZoom = devicePixelRatio / baseDPR;

  // 将比例转换为百分比整数
  let zoomLevel = Math.round(relativeZoom * 100);

  /**
   * 步骤 3：缩放梯度对齐（Quantization）。
   * 浏览器通常只支持固定的缩放梯度。我们将计算值对齐到最接近的标准梯度值，
   * 以消除由于窗口拖拽或微小像素偏差产生的中间非法值。
   */
  const commonZoomLevels = [50, 67, 75, 80, 90, 100, 110, 125, 150, 175, 200, 250, 300, 400, 500];
  const closest = commonZoomLevels.reduce((prev, curr) =>
    Math.abs(curr - zoomLevel) < Math.abs(prev - zoomLevel) ? curr : prev
  );

  // 若计算偏差在 15% 容差范围内，则执行自动吸附
  if (Math.abs(closest - zoomLevel) <= 15) {
    zoomLevel = closest;
  }

  /**
   * 步骤 4：视口启发式增强检查。
   * 特别针对非技术用户在小屏幕上开启极端缩放的情况。
   * 如果可用视口宽度被压缩至 600px 以下，系统将结合宽度阈值重新校验缩放等级。
   */
  if (viewportWidth < 600 && zoomLevel < 300) {
    // 建立视口宽度与最小预期缩放的映射关系
    if (viewportWidth < 150) zoomLevel = Math.max(zoomLevel, 500);
    else if (viewportWidth < 200) zoomLevel = Math.max(zoomLevel, 400);
    else if (viewportWidth < 300) zoomLevel = Math.max(zoomLevel, 300);
    else if (viewportWidth < 400) zoomLevel = Math.max(zoomLevel, 250);
    else if (viewportWidth < 500) zoomLevel = Math.max(zoomLevel, 200);
  }

  // 步骤 5：状态标志合成与阈值计算
  const isHighZoom = zoomLevel > 200;
  const isExtremeZoom = zoomLevel > 300;
  // 调用前文定义的幂函数计算补偿因子
  const globalScaleFactor = calculateGlobalScaleFactor(zoomLevel);

  // 步骤 6：生成复合状态阈值对象
  const thresholds = {
    above300: zoomLevel > 300,
    above400: zoomLevel > 400,
    above500: zoomLevel > 500,
  };

  // 最终封装返回完整的视口上下文报告
  return {
    zoomLevel,
    isHighZoom,
    isExtremeZoom,
    devicePixelRatio,
    viewportWidth,
    viewportHeight,
    globalScaleFactor,
    thresholds,
  };
}

/**
 * 全局缩放级别检测自定义 Hook (Custom Hook)
 * @export @function useGlobalZoomLevel
 * @description 为 React 函数式组件提供响应式的视口缩放感知能力。
 * 该 Hook 自动处理以下系统级交互：
 * 1. 初始化时的静默探测；
 * 2. 基于 'resize' 事件的布局重算；
 * 3. 基于 matchMedia API 的高清屏分辨率变更监听；
 * 4. 针对不支持现代 API 的浏览器提供 1000ms 定期轮询兜底逻辑。
 * * @returns {GlobalZoomLevelInfo} 当前实时更新的缩放信息快照
 */
export function useGlobalZoomLevel(): GlobalZoomLevelInfo {
  // 步骤 1：初始化组件状态。通过惰性初始化函数获取初次渲染时的视口数据。
  const [zoomInfo, setZoomInfo] = useState<GlobalZoomLevelInfo>(() => calculateGlobalZoomLevel());

  useEffect(() => {
    /** 状态更新闭包函数 */
    const updateZoomLevel = () => {
      const newZoomInfo = calculateGlobalZoomLevel();
      setZoomInfo(newZoomInfo);
    };

    // 监听器注册 A：监听窗口尺寸重置事件（通常伴随缩放操作）
    window.addEventListener('resize', updateZoomLevel);

    /**
     * 监听器注册 B：高级 DPI 侦测。
     * 利用 matchMedia 监听逻辑像素分辨率的变化。
     * 这是一个比 resize 更精确的缩放检测方式，能够覆盖单纯由于系统 DPI 切换引发的变更。
     */
    let mediaQueryList: MediaQueryList | null = null;
    let handleMediaChange: (() => void) | null = null;

    if (typeof window.matchMedia === 'function') {
      try {
        // 创建一个监控单位逻辑像素的媒体查询实例
        mediaQueryList = window.matchMedia('(resolution: 1dppx)');
        handleMediaChange = () => {
          // 步骤：执行 10ms 微任务延迟，确保底层 devicePixelRatio 状态完成硬更新
          setTimeout(updateZoomLevel, 10);
        };

        // 步骤：根据浏览器规范选择正确的事件绑定方式
        if (mediaQueryList.addEventListener) {
          mediaQueryList.addEventListener('change', handleMediaChange);
        } else {
          // 针对旧版 Safari 或 Edge 的向后兼容处理
          (mediaQueryList as any).addListener(handleMediaChange);
        }
      } catch (error) {
        // 异常处理：环境不支持 matchMedia 时，退回至常规事件流
        console.warn('matchMedia not supported, using fallback polling');
      }
    }

    /**
     * 策略模式：定期状态审计（Heartbeat）。
     * 每 1000 毫秒执行一次主动检查，确保在某些不触发 Resize 事件的极端场景下（如控制台内嵌缩放），
     * 系统状态依然能够与硬件保持最终一致性。
     */
    const intervalId = setInterval(updateZoomLevel, 1000);

    // 钩子清理阶段：撤销所有活动的资源引用，防止内存泄漏。
    return () => {
      window.removeEventListener('resize', updateZoomLevel);

      if (mediaQueryList && handleMediaChange) {
        try {
          if (mediaQueryList.removeEventListener) {
            mediaQueryList.removeEventListener('change', handleMediaChange);
          } else {
            // 兼容性清理逻辑
            (mediaQueryList as any).removeListener(handleMediaChange);
          }
        } catch (error) {
          // 抑制清理期间的静默异常
        }
      }

      // 销毁心跳定时器
      clearInterval(intervalId);
    };
  }, []);

  // 返回暴露给业务组件的只读状态快照
  return zoomInfo;
}

export default useGlobalZoomLevel;