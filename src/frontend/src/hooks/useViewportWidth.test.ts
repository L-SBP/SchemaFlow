import { renderHook, act } from '@testing-library/react';
import { vi, beforeEach, afterEach, describe, it, expect } from 'vitest';
import { useViewportWidth, useViewportWidthOnly, useBreakpointMatch, BREAKPOINTS } from './useViewportWidth';

// Mock window.innerWidth and window.innerHeight
const mockWindowSize = (width: number, height: number = 800) => {
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: width,
  });
  Object.defineProperty(window, 'innerHeight', {
    writable: true,
    configurable: true,
    value: height,
  });
};

// Mock window.addEventListener and removeEventListener
const mockEventListeners: { [key: string]: EventListener[] } = {};
const originalAddEventListener = window.addEventListener;
const originalRemoveEventListener = window.removeEventListener;

beforeEach(() => {
  // Reset event listeners
  Object.keys(mockEventListeners).forEach(key => {
    delete mockEventListeners[key];
  });

  // Mock addEventListener
  window.addEventListener = vi.fn((event: string, listener: EventListener) => {
    if (!mockEventListeners[event]) {
      mockEventListeners[event] = [];
    }
    mockEventListeners[event].push(listener);
  });

  // Mock removeEventListener
  window.removeEventListener = vi.fn((event: string, listener: EventListener) => {
    if (mockEventListeners[event]) {
      const index = mockEventListeners[event].indexOf(listener);
      if (index > -1) {
        mockEventListeners[event].splice(index, 1);
      }
    }
  });
});

afterEach(() => {
  // Restore original methods
  window.addEventListener = originalAddEventListener;
  window.removeEventListener = originalRemoveEventListener;
  vi.clearAllTimers();
});

describe('useViewportWidth', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should return correct viewport info for xs breakpoint', () => {
    mockWindowSize(400);

    const { result } = renderHook(() => useViewportWidth());

    expect(result.current.width).toBe(400);
    expect(result.current.breakpoint).toBe('xs');
    expect(result.current.is.xs).toBe(true);
    expect(result.current.is.mobile).toBe(true);
    expect(result.current.is.desktop).toBe(false);
  });

  it('should return correct viewport info for sm breakpoint', () => {
    mockWindowSize(600);

    const { result } = renderHook(() => useViewportWidth());

    expect(result.current.width).toBe(600);
    expect(result.current.breakpoint).toBe('sm');
    expect(result.current.is.sm).toBe(true);
    expect(result.current.is.mobile).toBe(true);
    expect(result.current.is.desktop).toBe(false);
  });

  it('should return correct viewport info for md breakpoint', () => {
    mockWindowSize(900);

    const { result } = renderHook(() => useViewportWidth());

    expect(result.current.width).toBe(900);
    expect(result.current.breakpoint).toBe('md');
    expect(result.current.is.md).toBe(true);
    expect(result.current.is.tablet).toBe(true);
    expect(result.current.is.mobile).toBe(false);
    expect(result.current.is.desktop).toBe(false);
  });

  it('should return correct viewport info for lg breakpoint', () => {
    mockWindowSize(1200);

    const { result } = renderHook(() => useViewportWidth());

    expect(result.current.width).toBe(1200);
    expect(result.current.breakpoint).toBe('lg');
    expect(result.current.is.lg).toBe(true);
    expect(result.current.is.desktop).toBe(true);
    expect(result.current.is.mobile).toBe(false);
  });

  it('should return correct viewport info for xl breakpoint', () => {
    mockWindowSize(1600);

    const { result } = renderHook(() => useViewportWidth());

    expect(result.current.width).toBe(1600);
    expect(result.current.breakpoint).toBe('xl');
    expect(result.current.is.xl).toBe(true);
    expect(result.current.is.desktop).toBe(true);
  });

  it('should update viewport info on resize with debounce', () => {
    mockWindowSize(400);

    const { result } = renderHook(() => useViewportWidth(50));

    expect(result.current.width).toBe(400);
    expect(result.current.breakpoint).toBe('xs');

    // Simulate resize
    mockWindowSize(1200);

    // Trigger resize event
    act(() => {
      mockEventListeners.resize?.forEach(listener => listener(new Event('resize')));
    });

    // Should not update immediately due to debounce
    expect(result.current.width).toBe(400);

    // Fast-forward time to trigger debounce
    act(() => {
      vi.advanceTimersByTime(50);
    });

    expect(result.current.width).toBe(1200);
    expect(result.current.breakpoint).toBe('lg');
  });

  it('should register and cleanup event listeners', () => {
    const { unmount } = renderHook(() => useViewportWidth());

    expect(window.addEventListener).toHaveBeenCalledWith('resize', expect.any(Function));
    expect(window.addEventListener).toHaveBeenCalledWith('orientationchange', expect.any(Function));

    unmount();

    expect(window.removeEventListener).toHaveBeenCalledWith('resize', expect.any(Function));
    expect(window.removeEventListener).toHaveBeenCalledWith('orientationchange', expect.any(Function));
  });
});

describe('useViewportWidthOnly', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should return only the width value', () => {
    mockWindowSize(800);

    const { result } = renderHook(() => useViewportWidthOnly());

    expect(result.current).toBe(800);
    expect(typeof result.current).toBe('number');
  });
});

describe('useBreakpointMatch', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should match single breakpoint', () => {
    mockWindowSize(600);

    const { result } = renderHook(() => useBreakpointMatch('sm'));

    expect(result.current).toBe(true);
  });

  it('should match multiple breakpoints', () => {
    mockWindowSize(600);

    const { result } = renderHook(() => useBreakpointMatch(['sm', 'md']));

    expect(result.current).toBe(true);
  });

  it('should match device categories', () => {
    mockWindowSize(600);

    const { result: mobileResult } = renderHook(() => useBreakpointMatch('mobile'));
    const { result: tabletResult } = renderHook(() => useBreakpointMatch('tablet'));
    const { result: desktopResult } = renderHook(() => useBreakpointMatch('desktop'));

    expect(mobileResult.current).toBe(true);
    expect(tabletResult.current).toBe(false);
    expect(desktopResult.current).toBe(false);
  });

  it('should not match incorrect breakpoint', () => {
    mockWindowSize(600);

    const { result } = renderHook(() => useBreakpointMatch('lg'));

    expect(result.current).toBe(false);
  });
});

describe('BREAKPOINTS constant', () => {
  it('should have correct breakpoint values', () => {
    expect(BREAKPOINTS.xs).toBe(0);
    expect(BREAKPOINTS.sm).toBe(480);
    expect(BREAKPOINTS.md).toBe(768);
    expect(BREAKPOINTS.lg).toBe(1024);
    expect(BREAKPOINTS.xl).toBe(1440);
  });
});