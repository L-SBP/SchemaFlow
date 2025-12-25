/**
 * 全局文本可读性和可访问性验证系统
 * 
 * 验证所有页面的文本在极高缩放下仍可读
 * 确保表单控件、导航元素、模态对话框等在高缩放下仍可用
 * 
 * Requirements: 6.4, 6.8
 */

export interface AccessibilityCheckResult {
  /** 检查是否通过 */
  passed: boolean;
  /** 检查项目名称 */
  checkName: string;
  /** 详细信息 */
  details: string;
  /** 建议的修复方案 */
  suggestions?: string[];
}

export interface GlobalAccessibilityReport {
  /** 所有检查结果 */
  results: AccessibilityCheckResult[];
  /** 总体是否通过 */
  overallPassed: boolean;
  /** 通过的检查数量 */
  passedCount: number;
  /** 总检查数量 */
  totalCount: number;
  /** 当前缩放级别 */
  zoomLevel: number;
  /** 当前全局缩放因子 */
  globalScaleFactor: number;
}

/**
 * 最小字体大小常量（像素）
 */
export const MIN_FONT_SIZE_PX = 12;

/**
 * 最小可点击区域尺寸（像素）- WCAG 2.1 AA 标准
 */
export const MIN_TOUCH_TARGET_SIZE_PX = 44;

/**
 * 紧凑模式最小可点击区域尺寸（像素）
 */
export const MIN_TOUCH_TARGET_SIZE_COMPACT_PX = 36;

/**
 * 获取元素的计算字体大小（像素）
 */
function getComputedFontSizePx(element: Element): number {
  const computedStyle = window.getComputedStyle(element);
  const fontSize = computedStyle.fontSize;
  return parseFloat(fontSize);
}

/**
 * 获取元素的可点击区域尺寸
 */
function getClickableAreaSize(element: Element): { width: number; height: number } {
  const rect = element.getBoundingClientRect();
  return {
    width: rect.width,
    height: rect.height,
  };
}

/**
 * 检查文本元素的字体大小是否符合最小要求
 */
function checkTextReadability(): AccessibilityCheckResult {
  const textElements = document.querySelectorAll('p, span, div, h1, h2, h3, h4, h5, h6, label, button, input, textarea, select, a, li');
  const failedElements: { element: Element; fontSize: number }[] = [];

  textElements.forEach(element => {
    const fontSize = getComputedFontSizePx(element);
    if (fontSize < MIN_FONT_SIZE_PX) {
      failedElements.push({ element, fontSize });
    }
  });

  const passed = failedElements.length === 0;
  const details = passed
    ? `所有 ${textElements.length} 个文本元素的字体大小都符合最小要求 (≥${MIN_FONT_SIZE_PX}px)`
    : `发现 ${failedElements.length} 个文本元素的字体大小小于 ${MIN_FONT_SIZE_PX}px`;

  const suggestions = passed ? undefined : [
    '使用 CSS 的 max() 函数确保最小字体大小：font-size: max(var(--font-size-base), 12px)',
    '检查 CSS 变量 --font-size-min 是否正确应用',
    '考虑在极高缩放级别下增加全局缩放因子的最小值'
  ];

  return {
    passed,
    checkName: '文本可读性检查',
    details,
    suggestions,
  };
}

/**
 * 检查可点击元素的尺寸是否符合可访问性要求
 */
function checkClickableAreaSize(): AccessibilityCheckResult {
  const clickableElements = document.querySelectorAll('button, [role="button"], a, input[type="button"], input[type="submit"], input[type="reset"], .btn, .panel-toggle-button');
  const failedElements: { element: Element; size: { width: number; height: number } }[] = [];

  clickableElements.forEach(element => {
    const size = getClickableAreaSize(element);
    const isCompact = element.classList.contains('btn-sm') || element.classList.contains('compact');
    const minSize = isCompact ? MIN_TOUCH_TARGET_SIZE_COMPACT_PX : MIN_TOUCH_TARGET_SIZE_PX;

    if (size.width < minSize || size.height < minSize) {
      failedElements.push({ element, size });
    }
  });

  const passed = failedElements.length === 0;
  const details = passed
    ? `所有 ${clickableElements.length} 个可点击元素的尺寸都符合可访问性要求`
    : `发现 ${failedElements.length} 个可点击元素的尺寸小于最小要求`;

  const suggestions = passed ? undefined : [
    '确保按钮使用 min-width 和 min-height 属性',
    '检查 CSS 变量 --button-min-size 和 --button-min-size-compact 是否正确应用',
    '使用 .min-touch-target 或 .min-touch-target-sm 工具类'
  ];

  return {
    passed,
    checkName: '可点击区域尺寸检查',
    details,
    suggestions,
  };
}

/**
 * 检查表单控件的可用性
 */
function checkFormControlUsability(): AccessibilityCheckResult {
  const formControls = document.querySelectorAll('input, textarea, select, button[type="submit"]');
  const issues: string[] = [];

  formControls.forEach((control, index) => {
    const fontSize = getComputedFontSizePx(control);
    const size = getClickableAreaSize(control);

    if (fontSize < MIN_FONT_SIZE_PX) {
      issues.push(`表单控件 #${index + 1} 字体过小 (${fontSize.toFixed(1)}px)`);
    }

    if (size.height < MIN_TOUCH_TARGET_SIZE_COMPACT_PX) {
      issues.push(`表单控件 #${index + 1} 高度过小 (${size.height.toFixed(1)}px)`);
    }
  });

  const passed = issues.length === 0;
  const details = passed
    ? `所有 ${formControls.length} 个表单控件都符合可用性要求`
    : `发现 ${issues.length} 个表单控件问题`;

  const suggestions = passed ? undefined : [
    '确保表单控件使用 --input-height 和 --input-padding CSS 变量',
    '为表单控件应用最小字体大小限制',
    '检查表单控件的 padding 和 border 设置'
  ];

  return {
    passed,
    checkName: '表单控件可用性检查',
    details: passed ? details : `${details}: ${issues.join(', ')}`,
    suggestions,
  };
}

/**
 * 检查导航元素的可访问性
 */
function checkNavigationAccessibility(): AccessibilityCheckResult {
  const navElements = document.querySelectorAll('nav, .sidebar-nav, .pagination, .breadcrumb, [role="navigation"]');
  const issues: string[] = [];

  navElements.forEach((nav, index) => {
    const links = nav.querySelectorAll('a, button, [role="button"]');

    links.forEach((link, linkIndex) => {
      const fontSize = getComputedFontSizePx(link);
      const size = getClickableAreaSize(link);

      if (fontSize < MIN_FONT_SIZE_PX) {
        issues.push(`导航 #${index + 1} 链接 #${linkIndex + 1} 字体过小`);
      }

      if (size.width < MIN_TOUCH_TARGET_SIZE_COMPACT_PX || size.height < MIN_TOUCH_TARGET_SIZE_COMPACT_PX) {
        issues.push(`导航 #${index + 1} 链接 #${linkIndex + 1} 点击区域过小`);
      }
    });
  });

  const passed = issues.length === 0;
  const details = passed
    ? `所有导航元素都符合可访问性要求`
    : `发现 ${issues.length} 个导航可访问性问题`;

  const suggestions = passed ? undefined : [
    '确保导航链接使用适当的 padding',
    '为导航元素应用 .sidebar-nav-link 样式类',
    '检查导航元素的字体大小设置'
  ];

  return {
    passed,
    checkName: '导航元素可访问性检查',
    details,
    suggestions,
  };
}

/**
 * 检查模态对话框的可用性
 */
function checkModalUsability(): AccessibilityCheckResult {
  const modals = document.querySelectorAll('.modal-content, [role="dialog"], [role="alertdialog"]');
  const issues: string[] = [];

  modals.forEach((modal, index) => {
    // 检查模态框标题
    const title = modal.querySelector('.modal-title, h1, h2, h3');
    if (title) {
      const fontSize = getComputedFontSizePx(title);
      if (fontSize < MIN_FONT_SIZE_PX) {
        issues.push(`模态框 #${index + 1} 标题字体过小`);
      }
    }

    // 检查模态框按钮
    const buttons = modal.querySelectorAll('button, .btn');
    buttons.forEach((button, buttonIndex) => {
      const fontSize = getComputedFontSizePx(button);
      const size = getClickableAreaSize(button);

      if (fontSize < MIN_FONT_SIZE_PX) {
        issues.push(`模态框 #${index + 1} 按钮 #${buttonIndex + 1} 字体过小`);
      }

      if (size.width < MIN_TOUCH_TARGET_SIZE_COMPACT_PX || size.height < MIN_TOUCH_TARGET_SIZE_COMPACT_PX) {
        issues.push(`模态框 #${index + 1} 按钮 #${buttonIndex + 1} 点击区域过小`);
      }
    });
  });

  const passed = issues.length === 0;
  const details = passed
    ? `所有模态对话框都符合可用性要求`
    : `发现 ${issues.length} 个模态对话框可用性问题`;

  const suggestions = passed ? undefined : [
    '确保模态框使用 .modal-content, .modal-title, .modal-body 样式类',
    '为模态框按钮应用适当的尺寸和字体大小',
    '检查模态框的响应式布局设置'
  ];

  return {
    passed,
    checkName: '模态对话框可用性检查',
    details,
    suggestions,
  };
}

/**
 * 获取当前缩放信息
 */
function getCurrentZoomInfo(): { zoomLevel: number; globalScaleFactor: number } {
  const root = document.documentElement;
  const globalScaleFactor = parseFloat(
    getComputedStyle(root).getPropertyValue('--global-ui-scale-factor').trim()
  ) || 1.0;

  // 估算缩放级别
  const devicePixelRatio = window.devicePixelRatio || 1;
  const viewportWidth = window.innerWidth;

  let zoomLevel = Math.round(devicePixelRatio * 100);
  if (viewportWidth < 400) {
    zoomLevel = Math.max(zoomLevel, 300);
  }

  return { zoomLevel, globalScaleFactor };
}

/**
 * 执行全局可访问性检查
 * 
 * 对当前页面进行全面的可访问性检查
 * 
 * @returns GlobalAccessibilityReport 检查报告
 */
export function performGlobalAccessibilityCheck(): GlobalAccessibilityReport {
  const { zoomLevel, globalScaleFactor } = getCurrentZoomInfo();

  const results: AccessibilityCheckResult[] = [
    checkTextReadability(),
    checkClickableAreaSize(),
    checkFormControlUsability(),
    checkNavigationAccessibility(),
    checkModalUsability(),
  ];

  const passedCount = results.filter(result => result.passed).length;
  const totalCount = results.length;
  const overallPassed = passedCount === totalCount;

  return {
    results,
    overallPassed,
    passedCount,
    totalCount,
    zoomLevel,
    globalScaleFactor,
  };
}

/**
 * 生成可访问性检查报告的文本摘要
 * 
 * @param report 检查报告
 * @returns 文本摘要
 */
export function generateAccessibilityReportSummary(report: GlobalAccessibilityReport): string {
  const { overallPassed, passedCount, totalCount, zoomLevel, globalScaleFactor } = report;

  let summary = `全局可访问性检查报告\n`;
  summary += `缩放级别: ${zoomLevel}%, 全局缩放因子: ${globalScaleFactor}\n`;
  summary += `检查结果: ${passedCount}/${totalCount} 项通过\n`;
  summary += `总体状态: ${overallPassed ? '✅ 通过' : '❌ 未通过'}\n\n`;

  report.results.forEach(result => {
    summary += `${result.passed ? '✅' : '❌'} ${result.checkName}\n`;
    summary += `   ${result.details}\n`;

    if (result.suggestions && result.suggestions.length > 0) {
      summary += `   建议:\n`;
      result.suggestions.forEach(suggestion => {
        summary += `   - ${suggestion}\n`;
      });
    }
    summary += '\n';
  });

  return summary;
}

/**
 * 在控制台输出可访问性检查报告
 * 
 * @param report 检查报告，如果未提供则执行新的检查
 */
export function logAccessibilityReport(report?: GlobalAccessibilityReport): void {
  const actualReport = report || performGlobalAccessibilityCheck();
  const summary = generateAccessibilityReportSummary(actualReport);

  if (actualReport.overallPassed) {
    console.log('%c' + summary, 'color: green; font-weight: bold;');
  } else {
    console.warn('%c' + summary, 'color: orange; font-weight: bold;');
  }
}

/**
 * 创建可访问性检查的调试面板
 * 
 * 在页面上显示一个浮动的调试面板，显示当前的可访问性状态
 */
export function createAccessibilityDebugPanel(): HTMLElement {
  // 移除现有的调试面板
  const existingPanel = document.getElementById('accessibility-debug-panel');
  if (existingPanel) {
    existingPanel.remove();
  }

  const panel = document.createElement('div');
  panel.id = 'accessibility-debug-panel';
  panel.style.cssText = `
    position: fixed;
    top: 10px;
    left: 10px;
    background: rgba(0, 0, 0, 0.9);
    color: white;
    padding: 12px;
    border-radius: 6px;
    font-family: monospace;
    font-size: 11px;
    z-index: 10000;
    max-width: 300px;
    pointer-events: none;
    line-height: 1.4;
  `;

  const updatePanel = () => {
    const report = performGlobalAccessibilityCheck();
    const { zoomLevel, globalScaleFactor, overallPassed, passedCount, totalCount } = report;

    panel.innerHTML = `
      <div style="font-weight: bold; margin-bottom: 8px;">
        可访问性状态 ${overallPassed ? '✅' : '❌'}
      </div>
      <div>缩放: ${zoomLevel}% (因子: ${globalScaleFactor})</div>
      <div>检查: ${passedCount}/${totalCount} 通过</div>
      <div style="margin-top: 8px; font-size: 10px;">
        ${report.results.map(r => `${r.passed ? '✅' : '❌'} ${r.checkName}`).join('<br>')}
      </div>
    `;
  };

  updatePanel();
  document.body.appendChild(panel);

  // 定期更新面板
  const intervalId = setInterval(updatePanel, 2000);

  // 提供清理方法
  (panel as any).cleanup = () => {
    clearInterval(intervalId);
    panel.remove();
  };

  return panel;
}

export default {
  performGlobalAccessibilityCheck,
  generateAccessibilityReportSummary,
  logAccessibilityReport,
  createAccessibilityDebugPanel,
  MIN_FONT_SIZE_PX,
  MIN_TOUCH_TARGET_SIZE_PX,
  MIN_TOUCH_TARGET_SIZE_COMPACT_PX,
};