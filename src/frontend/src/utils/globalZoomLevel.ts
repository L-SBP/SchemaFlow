import { useState, useEffect } from 'react';

/**
 * 全局缩放级别检测系统
 * 
 * 增强版缩放级别检测，支持检测 300%、400% 和 500% 缩放阈值
 * 供整个前端应用使用，计算全局缩放因子
 * 
 * Requirements: 6.1, 6.2, 6.3
 */

export interface GlobalZoomLevelInfo {
  /** 当前缩放级别（百分比，如 100, 150, 200, 300, 400, 500） */
  zoomLevel: number;
  /** 是否为高缩放模式（>200%） */
  isHighZoom: boolean;
  /** 是否为极高缩放模式（>300%） */
  isExtremeZoom: boolean;
  /** 原始设备像素比 */
  devicePixelRatio: number;
  /** 当前视口宽度 */
  viewportWidth: number;
  /** 当前视口高度 */
  viewportHeight: number;
  /** 建议的全局缩放因子 (0.7-1.0) */
  globalScaleFactor: number;
  /** 缩放阈值检测 */
  thresholds: {
    above300: boolean;
    above400: boolean;
    above500: boolean;
  };
}

/**
 * 计算全局缩放因子
 * 根据缩放级别返回反向缩放因子，用于部分抵消浏览器缩放
 * 
 * 计算公式：scaleFactor = 100 / zoomLevel * adjustmentFactor
 * 其中 adjustmentFactor 用于控制抵消程度（不完全抵消，保留部分缩放效果）
 * 
 * 缩放级别对应的缩放因子（部分抵消）：
 * - 500%: ~0.35 (抵消约65%的缩放)
 * - 400%: ~0.45 (抵消约55%的缩放)
 * - 300%: ~0.55 (抵消约45%的缩放)
 * - 250%: ~0.65 (抵消约35%的缩放)
 * - 200%: ~0.75 (抵消约25%的缩放)
 * - 150%: ~0.85 (抵消约15%的缩放)
 * - <125%: 1.0  (正常，不抵消)
 * 
 * @param zoomLevel 当前缩放级别（百分比）
 * @returns 全局缩放因子 (0.35-1.0)
 */
export function calculateGlobalScaleFactor(zoomLevel: number): number {
  // 低于125%缩放时不进行抵消
  if (zoomLevel <= 125) {
    return 1.0;
  }

  // 计算反向缩放因子
  // 使用公式：scaleFactor = (100 / zoomLevel) ^ power
  // power < 1 表示部分抵消，power = 1 表示完全抵消
  const power = 0.7; // 抵消约70%的缩放效果
  const rawFactor = Math.pow(100 / zoomLevel, power);

  // 限制最小值为0.35，最大值为1.0
  const clampedFactor = Math.max(0.35, Math.min(1.0, rawFactor));

  // 四舍五入到两位小数
  return Math.round(clampedFactor * 100) / 100;
}

/**
 * 计算浏览器缩放级别（增强版）
 * 
 * 算法说明：
 * 1. 使用 window.devicePixelRatio 作为基础指标
 * 2. 结合视口尺寸变化来检测缩放
 * 3. 考虑不同设备的基础 DPR（如 Retina 屏幕）
 * 4. 支持检测高达 500% 的缩放级别
 */
function calculateGlobalZoomLevel(): GlobalZoomLevelInfo {
  const devicePixelRatio = window.devicePixelRatio || 1;
  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;

  // 基础缩放级别计算
  // 在标准显示器上，devicePixelRatio 通常为 1
  // 在高分辨率显示器（如 Retina）上，基础 DPR 可能为 2 或更高

  // 检测基础 DPR（未缩放时的 DPR）
  // 通过屏幕尺寸和视口尺寸的关系来推断
  const screenWidth = window.screen.width;
  const screenHeight = window.screen.height;

  // 估算基础 DPR（考虑常见的高分辨率屏幕）
  let baseDPR = 1;
  if (screenWidth >= 2560 || screenHeight >= 1440) {
    baseDPR = 2; // 可能是高分辨率屏幕
  } else if (screenWidth >= 1920 && devicePixelRatio >= 1.5) {
    baseDPR = devicePixelRatio > 2 ? 2 : 1;
  }

  // 计算相对于基础 DPR 的缩放级别
  const relativeZoom = devicePixelRatio / baseDPR;

  // 将缩放级别转换为百分比并四舍五入到常见值
  let zoomLevel = Math.round(relativeZoom * 100);

  // 校正到常见的缩放级别（包括高缩放级别）
  const commonZoomLevels = [50, 67, 75, 80, 90, 100, 110, 125, 150, 175, 200, 250, 300, 400, 500];
  const closest = commonZoomLevels.reduce((prev, curr) =>
    Math.abs(curr - zoomLevel) < Math.abs(prev - zoomLevel) ? curr : prev
  );

  // 如果计算结果接近常见缩放级别，使用常见值
  if (Math.abs(closest - zoomLevel) <= 15) {
    zoomLevel = closest;
  }

  // 额外的视口尺寸检查（增强版）
  // 如果视口非常小，可能是高缩放级别
  if (viewportWidth < 600 && zoomLevel < 300) {
    // 基于视口宽度推断可能的缩放级别
    if (viewportWidth < 150) zoomLevel = Math.max(zoomLevel, 500);
    else if (viewportWidth < 200) zoomLevel = Math.max(zoomLevel, 400);
    else if (viewportWidth < 300) zoomLevel = Math.max(zoomLevel, 300);
    else if (viewportWidth < 400) zoomLevel = Math.max(zoomLevel, 250);
    else if (viewportWidth < 500) zoomLevel = Math.max(zoomLevel, 200);
  }

  // 计算各种状态标志
  const isHighZoom = zoomLevel > 200;
  const isExtremeZoom = zoomLevel > 300;
  const globalScaleFactor = calculateGlobalScaleFactor(zoomLevel);

  // 缩放阈值检测
  const thresholds = {
    above300: zoomLevel > 300,
    above400: zoomLevel > 400,
    above500: zoomLevel > 500,
  };

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
 * 全局缩放级别检测 Hook
 * 
 * 增强版 Hook，支持检测 300%、400% 和 500% 缩放阈值
 * 返回建议的全局缩放因子，供整个前端应用使用
 * 
 * @returns GlobalZoomLevelInfo 全局缩放级别信息
 */
export function useGlobalZoomLevel(): GlobalZoomLevelInfo {
  const [zoomInfo, setZoomInfo] = useState<GlobalZoomLevelInfo>(() => calculateGlobalZoomLevel());

  useEffect(() => {
    const updateZoomLevel = () => {
      const newZoomInfo = calculateGlobalZoomLevel();
      setZoomInfo(newZoomInfo);
    };

    // 监听窗口大小变化
    window.addEventListener('resize', updateZoomLevel);

    // 监听设备像素比变化（缩放变化）
    // 使用 matchMedia 监听缩放变化（如果可用）
    let mediaQueryList: MediaQueryList | null = null;
    let handleMediaChange: (() => void) | null = null;

    if (typeof window.matchMedia === 'function') {
      try {
        mediaQueryList = window.matchMedia('(resolution: 1dppx)');
        handleMediaChange = () => {
          // 延迟一点执行，确保 devicePixelRatio 已更新
          setTimeout(updateZoomLevel, 10);
        };

        // 现代浏览器支持 addEventListener
        if (mediaQueryList.addEventListener) {
          mediaQueryList.addEventListener('change', handleMediaChange);
        } else {
          // 兼容旧浏览器（已废弃的方法）
          (mediaQueryList as any).addListener(handleMediaChange);
        }
      } catch (error) {
        // 忽略 matchMedia 错误，使用定期检查作为备用
        console.warn('matchMedia not supported, using fallback polling');
      }
    }

    // 定期检查（作为备用方案）
    const intervalId = setInterval(updateZoomLevel, 1000);

    return () => {
      window.removeEventListener('resize', updateZoomLevel);

      if (mediaQueryList && handleMediaChange) {
        try {
          if (mediaQueryList.removeEventListener) {
            mediaQueryList.removeEventListener('change', handleMediaChange);
          } else {
            // 兼容旧浏览器（已废弃的方法）
            (mediaQueryList as any).removeListener(handleMediaChange);
          }
        } catch (error) {
          // 忽略清理错误
        }
      }

      clearInterval(intervalId);
    };
  }, []);

  return zoomInfo;
}

export default useGlobalZoomLevel;