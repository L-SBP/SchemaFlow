import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useZoomLevel } from './useZoomLevel';

/**
 * Tests for useZoomLevel hook
 * 
 * These tests verify the zoom level detection functionality
 * Requirements: 1.3, 2.3
 */

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

describe('useZoomLevel', () => {
  let originalDevicePixelRatio: number;
  let originalInnerWidth: number;
  let originalInnerHeight: number;
  let originalScreenWidth: number;
  let originalScreenHeight: number;

  beforeEach(() => {
    // Store original values
    originalDevicePixelRatio = window.devicePixelRatio;
    originalInnerWidth = window.innerWidth;
    originalInnerHeight = window.innerHeight;
    originalScreenWidth = window.screen.width;
    originalScreenHeight = window.screen.height;
  });

  afterEach(() => {
    // Restore original values
    Object.defineProperty(window, 'devicePixelRatio', {
      writable: true,
      configurable: true,
      value: originalDevicePixelRatio,
    });
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: originalInnerWidth,
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: originalInnerHeight,
    });
    Object.defineProperty(window.screen, 'width', {
      writable: true,
      configurable: true,
      value: originalScreenWidth,
    });
    Object.defineProperty(window.screen, 'height', {
      writable: true,
      configurable: true,
      value: originalScreenHeight,
    });
  });

  it('should detect normal zoom level (100%)', () => {
    // Mock standard display
    Object.defineProperty(window, 'devicePixelRatio', {
      writable: true,
      configurable: true,
      value: 1,
    });
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1200,
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: 800,
    });

    const { result } = renderHook(() => useZoomLevel());

    expect(result.current.zoomLevel).toBe(100);
    expect(result.current.isHighZoom).toBe(false);
    expect(result.current.devicePixelRatio).toBe(1);
    expect(result.current.viewportWidth).toBe(1200);
    expect(result.current.viewportHeight).toBe(800);
  });

  it('should detect high zoom level (>200%)', () => {
    // Mock high zoom scenario
    Object.defineProperty(window, 'devicePixelRatio', {
      writable: true,
      configurable: true,
      value: 2.5, // Simulating 250% zoom
    });
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 480, // Smaller viewport due to zoom
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: 320,
    });

    const { result } = renderHook(() => useZoomLevel());

    expect(result.current.zoomLevel).toBeGreaterThan(200);
    expect(result.current.isHighZoom).toBe(true);
    expect(result.current.devicePixelRatio).toBe(2.5);
    expect(result.current.viewportWidth).toBe(480);
    expect(result.current.viewportHeight).toBe(320);
  });

  it('should detect very small viewport as high zoom', () => {
    // Mock very small viewport (likely high zoom)
    Object.defineProperty(window, 'devicePixelRatio', {
      writable: true,
      configurable: true,
      value: 1.5,
    });
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 180, // Very small viewport - should trigger high zoom detection
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: 120,
    });

    const { result } = renderHook(() => useZoomLevel());

    // Should detect as high zoom due to very small viewport
    expect(result.current.zoomLevel).toBeGreaterThanOrEqual(200);
    expect(result.current.isHighZoom).toBe(true);
    expect(result.current.viewportWidth).toBe(180);
  });

  it('should handle Retina display correctly', () => {
    // Mock Retina display (high DPR but not zoomed)
    Object.defineProperty(window, 'devicePixelRatio', {
      writable: true,
      configurable: true,
      value: 2, // Retina display
    });
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1440, // Normal viewport size for Retina
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: 900,
    });
    Object.defineProperty(window.screen, 'width', {
      writable: true,
      configurable: true,
      value: 2880, // High resolution screen
    });
    Object.defineProperty(window.screen, 'height', {
      writable: true,
      configurable: true,
      value: 1800,
    });

    const { result } = renderHook(() => useZoomLevel());

    // Should detect as normal zoom level despite high DPR
    expect(result.current.zoomLevel).toBe(100);
    expect(result.current.isHighZoom).toBe(false);
    expect(result.current.devicePixelRatio).toBe(2);
  });

  it('should return valid zoom level info structure', () => {
    const { result } = renderHook(() => useZoomLevel());

    expect(result.current).toHaveProperty('zoomLevel');
    expect(result.current).toHaveProperty('isHighZoom');
    expect(result.current).toHaveProperty('devicePixelRatio');
    expect(result.current).toHaveProperty('viewportWidth');
    expect(result.current).toHaveProperty('viewportHeight');

    expect(typeof result.current.zoomLevel).toBe('number');
    expect(typeof result.current.isHighZoom).toBe('boolean');
    expect(typeof result.current.devicePixelRatio).toBe('number');
    expect(typeof result.current.viewportWidth).toBe('number');
    expect(typeof result.current.viewportHeight).toBe('number');
  });
});