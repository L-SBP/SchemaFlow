/**
 * Utility functions for Project Overview Optimization feature
 * Requirements: 3.1, 3.5, 7.1, 8.1, 8.5
 */

import { PROJECT_NAME_MAX_LENGTH } from '../constants/project-overview';

/**
 * Truncate text with ellipsis if it exceeds the maximum length
 * Requirement 3.1: Project name truncation at 6 characters
 */
export function truncateText(text: string, maxLength: number = PROJECT_NAME_MAX_LENGTH): string {
  if (text.length <= maxLength) {
    return text;
  }
  return text.substring(0, maxLength) + '...';
}

/**
 * Truncate project name specifically at 6 characters with ellipsis
 * Requirement 3.1: Project name truncation at 6 characters with ellipsis
 */
export function truncateProjectName(projectName: string): string {
  return truncateText(projectName, PROJECT_NAME_MAX_LENGTH);
}

/**
 * Truncate description based on available space
 * Requirement 7.1: Description truncation logic based on available space
 */
export function truncateDescription(description: string, availableWidth: number, characterWidth: number = 8): string {
  if (!description) {
    return '';
  }

  // Calculate approximate characters that can fit in available space
  const maxCharacters = Math.floor(availableWidth / characterWidth);

  if (description.length <= maxCharacters) {
    return description;
  }

  // Truncate at word boundary if possible
  const truncated = description.substring(0, maxCharacters);
  const lastSpaceIndex = truncated.lastIndexOf(' ');

  // If we can break at a word boundary and it's not too short, do so
  if (lastSpaceIndex > maxCharacters * 0.7) {
    return truncated.substring(0, lastSpaceIndex) + '...';
  }

  // Otherwise, truncate at character boundary
  return truncated + '...';
}

/**
 * Check if text needs truncation
 */
export function needsTruncation(text: string, maxLength: number = PROJECT_NAME_MAX_LENGTH): boolean {
  return text.length > maxLength;
}

/**
 * Check if description needs truncation based on available space
 * Requirement 7.1: Check if description exceeds available card space
 */
export function descriptionNeedsTruncation(description: string, availableWidth: number, characterWidth: number = 8): boolean {
  if (!description) {
    return false;
  }

  const maxCharacters = Math.floor(availableWidth / characterWidth);
  return description.length > maxCharacters;
}

/**
 * Measure text width (utility for text measurement)
 * Requirement 3.5: Add utility functions for text measurement and truncation
 * Enhanced with error handling and fallbacks
 */
export function measureTextWidth(text: string, fontSize: number = 14, fontFamily: string = 'Arial'): number {
  if (!text || typeof text !== 'string') {
    return 0;
  }

  // Try to create a temporary canvas element to measure text
  try {
    // Check if we're in a browser environment
    if (typeof document === 'undefined' || typeof window === 'undefined') {
      // Fallback for server-side rendering or test environments
      return text.length * (fontSize * 0.6);
    }

    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');

    if (context) {
      context.font = `${fontSize}px ${fontFamily}`;
      const metrics = context.measureText(text);
      return metrics.width;
    }
  } catch (error) {
    console.warn('Canvas text measurement failed, using fallback:', error);
  }

  // Fallback: estimate based on character count and average character width
  // This is a rough approximation for testing purposes
  return text.length * (fontSize * 0.6);
}

/**
 * Truncate text to fit within a specific pixel width
 * Requirement 3.5: Add utility functions for text measurement and truncation
 */
export function truncateToWidth(text: string, maxWidth: number, fontSize: number = 14, fontFamily: string = 'Arial'): string {
  if (!text) {
    return '';
  }

  const fullWidth = measureTextWidth(text, fontSize, fontFamily);

  if (fullWidth <= maxWidth) {
    return text;
  }

  // Binary search to find the optimal truncation point
  let left = 0;
  let right = text.length;
  let bestFit = '';

  while (left <= right) {
    const mid = Math.floor((left + right) / 2);
    const candidate = text.substring(0, mid) + '...';
    const candidateWidth = measureTextWidth(candidate, fontSize, fontFamily);

    if (candidateWidth <= maxWidth) {
      bestFit = candidate;
      left = mid + 1;
    } else {
      right = mid - 1;
    }
  }

  return bestFit || '...';
}

/**
 * Format date for display
 * Requirement 8.1: "YYYY-MM-DD HH:mm" format
 * Requirement 8.5: "今天 HH:mm" for today's dates
 */
export function formatProjectDate(dateString: string): string {
  try {
    const date = new Date(dateString);

    // Check if date is invalid
    if (isNaN(date.getTime())) {
      return 'Invalid Date';
    }

    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate());

    // Check if the date is today
    if (dateOnly.getTime() === today.getTime()) {
      const hours = date.getHours().toString().padStart(2, '0');
      const minutes = date.getMinutes().toString().padStart(2, '0');
      return `今天 ${hours}:${minutes}`;
    }

    // Format as YYYY-MM-DD HH:mm
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');

    return `${year}-${month}-${day} ${hours}:${minutes}`;
  } catch (error) {
    return 'Invalid Date';
  }
}

/**
 * Calculate tooltip position to avoid viewport edges
 * Requirement 2.4: Tooltip positioning
 * Enhanced with error handling and fallbacks
 */
export function calculateTooltipPosition(
  cardElement: HTMLElement,
  tooltipElement: HTMLElement,
  preferredPlacement: 'top' | 'bottom' | 'left' | 'right' = 'top'
): { x: number; y: number; placement: 'top' | 'bottom' | 'left' | 'right' } {
  try {
    // Validate inputs
    if (!cardElement || !tooltipElement) {
      console.warn('Invalid elements provided to calculateTooltipPosition');
      return { x: 0, y: 0, placement: 'top' };
    }

    const cardRect = cardElement.getBoundingClientRect();
    const tooltipRect = tooltipElement.getBoundingClientRect();

    // Validate rectangles
    if (!cardRect || !tooltipRect) {
      console.warn('Could not get element rectangles for tooltip positioning');
      return { x: 0, y: 0, placement: 'top' };
    }

    const viewport = {
      width: window.innerWidth || 1024, // Fallback viewport width
      height: window.innerHeight || 768, // Fallback viewport height
    };

    let x = 0;
    let y = 0;
    let placement = preferredPlacement;

    // Calculate position based on preferred placement
    switch (preferredPlacement) {
      case 'top':
        x = cardRect.left + cardRect.width / 2 - tooltipRect.width / 2;
        y = cardRect.top - tooltipRect.height - 8;
        break;
      case 'bottom':
        x = cardRect.left + cardRect.width / 2 - tooltipRect.width / 2;
        y = cardRect.bottom + 8;
        break;
      case 'left':
        x = cardRect.left - tooltipRect.width - 8;
        y = cardRect.top + cardRect.height / 2 - tooltipRect.height / 2;
        break;
      case 'right':
        x = cardRect.right + 8;
        y = cardRect.top + cardRect.height / 2 - tooltipRect.height / 2;
        break;
      default:
        // Fallback to top placement
        x = cardRect.left + cardRect.width / 2 - tooltipRect.width / 2;
        y = cardRect.top - tooltipRect.height - 8;
        placement = 'top';
    }

    // Adjust if tooltip would go outside viewport
    if (x < 8) {
      x = 8;
      if (placement === 'left') placement = 'right';
    }
    if (x + tooltipRect.width > viewport.width - 8) {
      x = viewport.width - tooltipRect.width - 8;
      if (placement === 'right') placement = 'left';
    }
    if (y < 8) {
      y = 8;
      if (placement === 'top') placement = 'bottom';
    }
    if (y + tooltipRect.height > viewport.height - 8) {
      y = viewport.height - tooltipRect.height - 8;
      if (placement === 'bottom') placement = 'top';
    }

    // Ensure coordinates are valid numbers
    x = isNaN(x) ? 0 : Math.max(0, x);
    y = isNaN(y) ? 0 : Math.max(0, y);

    return { x, y, placement };
  } catch (error) {
    console.error('Error calculating tooltip position:', error);
    // Return safe fallback position
    return { x: 0, y: 0, placement: 'top' };
  }
}

/**
 * Calculate initial tooltip position from mouse event
 * Requirement 2.4: Tooltip positioning
 * Enhanced with error handling and fallbacks
 */
export function calculateTooltipPositionFromEvent(
  cardElement: HTMLElement,
  mouseEvent: React.MouseEvent<HTMLDivElement>
): { x: number; y: number; placement: 'top' | 'bottom' | 'left' | 'right' } {
  try {
    // Validate inputs
    if (!cardElement) {
      console.warn('Invalid card element provided to calculateTooltipPositionFromEvent');
      return { x: 0, y: 0, placement: 'top' };
    }

    const cardRect = cardElement.getBoundingClientRect();

    // Validate rectangle
    if (!cardRect) {
      console.warn('Could not get card rectangle for tooltip positioning');
      return { x: 0, y: 0, placement: 'top' };
    }

    // Default position above the card
    const x = cardRect.left + cardRect.width / 2;
    const y = cardRect.top - 8;

    // Ensure coordinates are valid numbers
    const safeX = isNaN(x) ? 0 : Math.max(0, x);
    const safeY = isNaN(y) ? 0 : Math.max(0, y);

    return { x: safeX, y: safeY, placement: 'top' };
  } catch (error) {
    console.error('Error calculating tooltip position from event:', error);
    // Return safe fallback position
    return { x: 0, y: 0, placement: 'top' };
  }
}

/**
 * Get Chinese label for project status
 */
export function getProjectStatusLabel(status: 'initializing' | 'active' | 'inactive'): string {
  const statusLabels = {
    initializing: '部署中',
    active: '运行中',
    inactive: '非活跃',
  };
  return statusLabels[status] || status;
}

/**
 * Check if a project status is valid
 */
export function isValidProjectStatus(status: string): status is 'initializing' | 'active' | 'inactive' {
  return ['initializing', 'active', 'inactive'].includes(status);
}

/**
 * Get status badge color class
 */
export function getStatusBadgeColorClass(status: 'initializing' | 'active' | 'inactive'): string {
  switch (status) {
    case 'initializing':
      return 'status-badge--initializing';
    case 'active':
      return 'status-badge--active';
    case 'inactive':
      return 'status-badge--inactive';
    default:
      return 'status-badge--inactive';
  }
}