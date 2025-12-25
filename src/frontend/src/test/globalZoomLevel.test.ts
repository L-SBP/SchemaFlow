/**
 * 全局缩放级别系统测试
 * 
 * 测试全局缩放级别检测和可访问性验证功能
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  calculateGlobalScaleFactor,
  applyGlobalScaleFactor,
  getCurrentGlobalScaleFactor,
  enableGlobalScaleTransition,
  disableGlobalScaleTransition,
  withoutTransition
} from '../utils/globalZoomLevel';
import {
  performGlobalAccessibilityCheck,
  generateAccessibilityReportSummary,
  MIN_FONT_SIZE_PX,
  MIN_TOUCH_TARGET_SIZE_PX
} from '../utils/accessibilityVerification';

// Mock DOM environment
const mockDocument = {
  documentElement: {
    style: {
      setProperty: vi.fn(),
      getPropertyValue: vi.fn(() => '1.0'),
    },
    classList: {
      add: vi.fn(),
      remove: vi.fn(),
      contains: vi.fn(() => false),
    },
  },
  querySelectorAll: vi.fn(() => []),
  getElementById: vi.fn(() => null),
  createElement: vi.fn(() => ({
    style: { cssText: '' },
    innerHTML: '',
    remove: vi.fn(),
  })),
  body: {
    appendChild: vi.fn(),
  },
};

const mockWindow = {
  getComputedStyle: vi.fn(() => ({
    fontSize: '16px',
    getPropertyValue: vi.fn(() => '1.0'),
  })),
  devicePixelRatio: 1,
  innerWidth: 1024,
  innerHeight: 768,
  screen: {
    width: 1920,
    height: 1080,
  },
  requestAnimationFrame: vi.fn((cb) => setTimeout(cb, 16)),
};

// Setup global mocks
beforeEach(() => {
  global.document = mockDocument as any;
  global.window = mockWindow as any;
  vi.clearAllMocks();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('全局缩放级别系统', () => {
  describe('calculateGlobalScaleFactor', () => {
    it('应该为低缩放级别（≤125%）返回 1.0', () => {
      expect(calculateGlobalScaleFactor(100)).toBe(1.0);
      expect(calculateGlobalScaleFactor(110)).toBe(1.0);
      expect(calculateGlobalScaleFactor(125)).toBe(1.0);
    });

    it('应该为 150% 缩放返回部分抵消因子', () => {
      const factor = calculateGlobalScaleFactor(150);
      // 公式: (100/150)^0.7 ≈ 0.76
      expect(factor).toBeGreaterThan(0.7);
      expect(factor).toBeLessThan(0.85);
    });

    it('应该为 200% 缩放返回部分抵消因子', () => {
      const factor = calculateGlobalScaleFactor(200);
      // 公式: (100/200)^0.7 ≈ 0.62
      expect(factor).toBeGreaterThan(0.55);
      expect(factor).toBeLessThan(0.7);
    });

    it('应该为 300% 缩放返回部分抵消因子', () => {
      const factor = calculateGlobalScaleFactor(300);
      // 公式: (100/300)^0.7 ≈ 0.48
      expect(factor).toBeGreaterThan(0.4);
      expect(factor).toBeLessThan(0.55);
    });

    it('应该为 400% 缩放返回部分抵消因子', () => {
      const factor = calculateGlobalScaleFactor(400);
      // 公式: (100/400)^0.7 ≈ 0.41
      expect(factor).toBeGreaterThan(0.35);
      expect(factor).toBeLessThan(0.5);
    });

    it('应该为 500% 缩放返回最小因子 0.35', () => {
      const factor = calculateGlobalScaleFactor(500);
      // 公式: (100/500)^0.7 ≈ 0.35，但被限制在最小值 0.35
      expect(factor).toBe(0.35);
    });

    it('应该为极高缩放返回最小因子 0.35', () => {
      expect(calculateGlobalScaleFactor(600)).toBe(0.35);
      expect(calculateGlobalScaleFactor(1000)).toBe(0.35);
    });

    it('缩放因子应该随缩放级别增加而减小', () => {
      const factor150 = calculateGlobalScaleFactor(150);
      const factor200 = calculateGlobalScaleFactor(200);
      const factor300 = calculateGlobalScaleFactor(300);
      const factor400 = calculateGlobalScaleFactor(400);

      expect(factor150).toBeGreaterThan(factor200);
      expect(factor200).toBeGreaterThan(factor300);
      expect(factor300).toBeGreaterThan(factor400);
    });
  });

  describe('applyGlobalScaleFactor', () => {
    it('应该设置 CSS 变量', () => {
      applyGlobalScaleFactor(0.8);

      expect(mockDocument.documentElement.style.setProperty).toHaveBeenCalledWith(
        '--global-ui-scale-factor',
        '0.8'
      );
    });

    it('应该在禁用过渡时临时设置过渡时长为 0', () => {
      applyGlobalScaleFactor(0.8, false);

      expect(mockDocument.documentElement.style.setProperty).toHaveBeenCalledWith(
        '--global-transition-duration',
        '0s'
      );
      expect(mockDocument.documentElement.style.setProperty).toHaveBeenCalledWith(
        '--global-ui-scale-factor',
        '0.8'
      );
    });
  });

  describe('getCurrentGlobalScaleFactor', () => {
    it('应该从 CSS 变量读取当前缩放因子', () => {
      mockWindow.getComputedStyle.mockReturnValue({
        getPropertyValue: vi.fn(() => '0.8'),
      });

      const factor = getCurrentGlobalScaleFactor();
      expect(factor).toBe(0.8);
    });

    it('应该在无法读取时返回默认值 1.0', () => {
      mockWindow.getComputedStyle.mockReturnValue({
        getPropertyValue: vi.fn(() => ''),
      });

      const factor = getCurrentGlobalScaleFactor();
      expect(factor).toBe(1.0);
    });
  });

  describe('过渡控制', () => {
    it('应该能够启用全局缩放过渡', () => {
      enableGlobalScaleTransition();

      expect(mockDocument.documentElement.classList.add).toHaveBeenCalledWith(
        'global-scale-transition'
      );
    });

    it('应该能够禁用全局缩放过渡', () => {
      disableGlobalScaleTransition();

      expect(mockDocument.documentElement.classList.remove).toHaveBeenCalledWith(
        'global-scale-transition'
      );
    });

    it('应该能够临时禁用过渡执行操作', () => {
      const callback = vi.fn();
      mockDocument.documentElement.classList.contains.mockReturnValue(true);

      withoutTransition(callback);

      expect(mockDocument.documentElement.classList.remove).toHaveBeenCalledWith(
        'global-scale-transition'
      );
      expect(callback).toHaveBeenCalled();
      expect(mockWindow.requestAnimationFrame).toHaveBeenCalled();
    });
  });
});

describe('可访问性验证系统', () => {
  describe('常量值', () => {
    it('应该定义正确的最小字体大小', () => {
      expect(MIN_FONT_SIZE_PX).toBe(12);
    });

    it('应该定义正确的最小可点击区域尺寸', () => {
      expect(MIN_TOUCH_TARGET_SIZE_PX).toBe(44);
    });
  });

  describe('performGlobalAccessibilityCheck', () => {
    beforeEach(() => {
      // Mock DOM elements for accessibility checks
      const mockElements = [
        { getBoundingClientRect: () => ({ width: 50, height: 50 }) },
        { getBoundingClientRect: () => ({ width: 30, height: 30 }) },
      ];

      mockDocument.querySelectorAll.mockImplementation((selector) => {
        if (selector.includes('button')) {
          return mockElements;
        }
        return [];
      });

      mockWindow.getComputedStyle.mockReturnValue({
        fontSize: '14px',
        getPropertyValue: vi.fn(() => '1.0'),
      });
    });

    it('应该执行所有可访问性检查', () => {
      const report = performGlobalAccessibilityCheck();

      expect(report).toHaveProperty('results');
      expect(report).toHaveProperty('overallPassed');
      expect(report).toHaveProperty('passedCount');
      expect(report).toHaveProperty('totalCount');
      expect(report).toHaveProperty('zoomLevel');
      expect(report).toHaveProperty('globalScaleFactor');

      expect(Array.isArray(report.results)).toBe(true);
      expect(report.results.length).toBeGreaterThan(0);
    });

    it('应该检查文本可读性', () => {
      const report = performGlobalAccessibilityCheck();
      const textCheck = report.results.find(r => r.checkName === '文本可读性检查');

      expect(textCheck).toBeDefined();
      expect(textCheck?.passed).toBeDefined();
      expect(textCheck?.details).toBeDefined();
    });

    it('应该检查可点击区域尺寸', () => {
      const report = performGlobalAccessibilityCheck();
      const clickCheck = report.results.find(r => r.checkName === '可点击区域尺寸检查');

      expect(clickCheck).toBeDefined();
      expect(clickCheck?.passed).toBeDefined();
      expect(clickCheck?.details).toBeDefined();
    });
  });

  describe('generateAccessibilityReportSummary', () => {
    it('应该生成可读的报告摘要', () => {
      const mockReport = {
        results: [
          {
            passed: true,
            checkName: '测试检查',
            details: '测试详情',
          },
        ],
        overallPassed: true,
        passedCount: 1,
        totalCount: 1,
        zoomLevel: 100,
        globalScaleFactor: 1.0,
      };

      const summary = generateAccessibilityReportSummary(mockReport);

      expect(summary).toContain('全局可访问性检查报告');
      expect(summary).toContain('缩放级别: 100%');
      expect(summary).toContain('全局缩放因子: 1');
      expect(summary).toContain('检查结果: 1/1 项通过');
      expect(summary).toContain('✅ 通过');
      expect(summary).toContain('测试检查');
      expect(summary).toContain('测试详情');
    });

    it('应该在检查失败时显示建议', () => {
      const mockReport = {
        results: [
          {
            passed: false,
            checkName: '失败检查',
            details: '失败详情',
            suggestions: ['建议1', '建议2'],
          },
        ],
        overallPassed: false,
        passedCount: 0,
        totalCount: 1,
        zoomLevel: 300,
        globalScaleFactor: 0.65,
      };

      const summary = generateAccessibilityReportSummary(mockReport);

      expect(summary).toContain('❌ 未通过');
      expect(summary).toContain('建议:');
      expect(summary).toContain('- 建议1');
      expect(summary).toContain('- 建议2');
    });
  });
});

// Property-based test for global scale factor calculation
describe('Property: 全局缩放因子计算', () => {
  it('应该为所有缩放级别返回有效的缩放因子', () => {
    // Test a range of zoom levels
    const zoomLevels = [50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 600];

    zoomLevels.forEach(zoomLevel => {
      const scaleFactor = calculateGlobalScaleFactor(zoomLevel);

      // Scale factor should be between 0.35 and 1.0
      expect(scaleFactor).toBeGreaterThanOrEqual(0.35);
      expect(scaleFactor).toBeLessThanOrEqual(1.0);

      // Scale factor should be one of the expected values
      expect([0.35, 0.5, 0.65, 0.8, 0.9, 1.0]).toContain(scaleFactor);
    });
  });

  it('应该在缩放级别增加时减少缩放因子', () => {
    const factor100 = calculateGlobalScaleFactor(100);
    const factor200 = calculateGlobalScaleFactor(200);
    const factor250 = calculateGlobalScaleFactor(250);
    const factor300 = calculateGlobalScaleFactor(300);
    const factor400 = calculateGlobalScaleFactor(400);
    const factor500 = calculateGlobalScaleFactor(500);

    expect(factor100).toBeGreaterThanOrEqual(factor200);
    expect(factor200).toBeGreaterThanOrEqual(factor250);
    expect(factor250).toBeGreaterThanOrEqual(factor300);
    expect(factor300).toBeGreaterThanOrEqual(factor400);
    expect(factor400).toBeGreaterThanOrEqual(factor500);
    expect(factor300).toBeGreaterThanOrEqual(factor400);
    expect(factor400).toBeGreaterThanOrEqual(factor500);
  });
});

// Export a function to calculate the global scale factor for use in other tests
export { calculateGlobalScaleFactor };