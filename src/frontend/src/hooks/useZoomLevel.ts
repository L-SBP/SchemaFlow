import { useGlobalZoomLevel } from '../utils/globalZoomLevel';

/**
 * 缩放级别检测 Hook（兼容性包装器）
 * 
 * 检测当前浏览器缩放级别，通过 window.devicePixelRatio 和视口尺寸计算
 * 返回缩放级别和是否为高缩放模式（>200%）
 * 
 * 注意：这是一个兼容性包装器，新代码应该使用 useGlobalZoomLevel
 * 
 * Requirements: 1.3, 2.3
 */

export interface ZoomLevelInfo {
  /** 当前缩放级别（百分比，如 100, 150, 200） */
  zoomLevel: number;
  /** 是否为高缩放模式（>200%） */
  isHighZoom: boolean;
  /** 原始设备像素比 */
  devicePixelRatio: number;
  /** 当前视口宽度 */
  viewportWidth: number;
  /** 当前视口高度 */
  viewportHeight: number;
}

/**
 * 缩放级别检测 Hook（兼容性包装器）
 * 
 * 使用新的全局缩放级别检测系统，但保持原有接口兼容性
 * 新代码应该直接使用 useGlobalZoomLevel
 * 
 * @returns ZoomLevelInfo 缩放级别信息
 */
export function useZoomLevel(): ZoomLevelInfo {
  const globalZoomInfo = useGlobalZoomLevel();

  // 转换为原有接口格式
  return {
    zoomLevel: globalZoomInfo.zoomLevel,
    isHighZoom: globalZoomInfo.isHighZoom,
    devicePixelRatio: globalZoomInfo.devicePixelRatio,
    viewportWidth: globalZoomInfo.viewportWidth,
    viewportHeight: globalZoomInfo.viewportHeight,
  };
}

export default useZoomLevel;