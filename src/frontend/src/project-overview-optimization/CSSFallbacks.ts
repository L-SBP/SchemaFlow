/**
 * CSS Fallbacks and Progressive Enhancement Utilities
 * Requirements: Error handling from design document - progressive enhancement for CSS failures
 */

/**
 * Check if CSS feature is supported
 */
export function supportsCSSFeature(property: string, value: string): boolean {
  try {
    if (typeof CSS === 'undefined' || typeof CSS.supports !== 'function') {
      return false;
    }
    return CSS.supports(property, value);
  } catch (error) {
    console.warn('CSS.supports check failed:', error);
    return false;
  }
}

/**
 * Apply inline styles as fallback for critical layout
 */
export function applyInlineStyleFallbacks(element: HTMLElement): void {
  try {
    if (!element) {
      return;
    }

    // Check if CSS Grid is supported, apply flexbox fallback if not
    if (!supportsCSSFeature('display', 'grid')) {
      if (element.classList.contains('project-card-grid')) {
        element.style.display = 'flex';
        element.style.flexWrap = 'wrap';
        element.style.gap = '16px';
      }
    }

    // Check if CSS custom properties are supported
    if (!supportsCSSFeature('color', 'var(--primary-color)')) {
      // Apply hardcoded colors as fallback
      if (element.classList.contains('project-card')) {
        element.style.backgroundColor = '#ffffff';
        element.style.border = '1px solid #e0e0e0';
        element.style.borderRadius = '8px';
      }
    }

    // Check if CSS transforms are supported for tooltips
    if (!supportsCSSFeature('transform', 'translateX(-50%)')) {
      if (element.classList.contains('hover-tooltip')) {
        // Use margin-based centering instead of transform
        const width = element.offsetWidth;
        element.style.marginLeft = `-${width / 2}px`;
      }
    }

  } catch (error) {
    console.error('Error applying CSS fallbacks:', error);
  }
}

/**
 * Initialize progressive enhancement for the project overview
 */
export function initializeProgressiveEnhancement(): void {
  try {
    // Add CSS feature detection classes to document
    const html = document.documentElement;

    // Test for CSS Grid support
    if (supportsCSSFeature('display', 'grid')) {
      html.classList.add('supports-grid');
    } else {
      html.classList.add('no-grid');
    }

    // Test for CSS Custom Properties support
    if (supportsCSSFeature('color', 'var(--test)')) {
      html.classList.add('supports-custom-properties');
    } else {
      html.classList.add('no-custom-properties');
    }

    // Test for CSS Flexbox support
    if (supportsCSSFeature('display', 'flex')) {
      html.classList.add('supports-flexbox');
    } else {
      html.classList.add('no-flexbox');
    }

    // Test for CSS Transforms support
    if (supportsCSSFeature('transform', 'translateX(0)')) {
      html.classList.add('supports-transforms');
    } else {
      html.classList.add('no-transforms');
    }

  } catch (error) {
    console.error('Error initializing progressive enhancement:', error);
  }
}

/**
 * Fallback styles for critical layout when CSS fails to load
 */
export const CRITICAL_INLINE_STYLES = {
  projectCard: {
    display: 'block',
    width: '280px',
    minHeight: '160px',
    padding: '16px',
    margin: '8px',
    backgroundColor: '#ffffff',
    border: '1px solid #e0e0e0',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    cursor: 'pointer',
    position: 'relative' as const,
  },
  projectCardGrid: {
    display: 'flex',
    flexWrap: 'wrap' as const,
    gap: '16px',
    padding: '16px',
    justifyContent: 'flex-start',
  },
  tooltip: {
    position: 'absolute' as const,
    zIndex: 1000,
    backgroundColor: '#333333',
    color: '#ffffff',
    padding: '12px',
    borderRadius: '6px',
    fontSize: '14px',
    maxWidth: '300px',
    boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
  },
  modal: {
    position: 'fixed' as const,
    top: '0',
    left: '0',
    width: '100%',
    height: '100%',
    backgroundColor: 'rgba(0,0,0,0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  modalContent: {
    backgroundColor: '#ffffff',
    padding: '24px',
    borderRadius: '8px',
    maxWidth: '500px',
    maxHeight: '80vh',
    overflow: 'auto',
    position: 'relative' as const,
  }
};

/**
 * Apply critical inline styles to an element
 */
export function applyCriticalStyles(element: HTMLElement, styleKey: keyof typeof CRITICAL_INLINE_STYLES): void {
  try {
    if (!element || !CRITICAL_INLINE_STYLES[styleKey]) {
      return;
    }

    const styles = CRITICAL_INLINE_STYLES[styleKey];
    Object.assign(element.style, styles);
  } catch (error) {
    console.error('Error applying critical styles:', error);
  }
}

/**
 * Check if external CSS has loaded properly
 */
export function checkCSSLoaded(): boolean {
  try {
    // Create a test element to check if CSS is loaded
    const testElement = document.createElement('div');
    testElement.className = 'project-card';
    testElement.style.visibility = 'hidden';
    testElement.style.position = 'absolute';
    testElement.style.top = '-9999px';

    document.body.appendChild(testElement);

    // Check if CSS styles are applied
    const computedStyle = window.getComputedStyle(testElement);
    const hasStyles = computedStyle.display !== 'block' ||
      computedStyle.padding !== '0px' ||
      computedStyle.backgroundColor !== 'rgba(0, 0, 0, 0)';

    document.body.removeChild(testElement);

    return hasStyles;
  } catch (error) {
    console.warn('Could not check CSS loading status:', error);
    return false;
  }
}

/**
 * Initialize fallback styles if CSS fails to load
 */
export function initializeCSSFallbacks(): void {
  try {
    // Wait a bit for CSS to load
    setTimeout(() => {
      if (!checkCSSLoaded()) {
        console.warn('CSS may not have loaded properly, applying fallback styles');

        // Apply fallback styles to existing elements
        const projectCards = document.querySelectorAll('.project-card');
        projectCards.forEach((card) => {
          if (card instanceof HTMLElement) {
            applyCriticalStyles(card, 'projectCard');
          }
        });

        const grids = document.querySelectorAll('.project-card-grid');
        grids.forEach((grid) => {
          if (grid instanceof HTMLElement) {
            applyCriticalStyles(grid, 'projectCardGrid');
          }
        });
      }
    }, 1000);
  } catch (error) {
    console.error('Error initializing CSS fallbacks:', error);
  }
}