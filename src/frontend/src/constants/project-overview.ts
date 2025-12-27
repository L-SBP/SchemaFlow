/**
 * Constants for Project Overview Optimization feature
 * Requirements: 4.2, 4.3, 4.4, 4.6
 */

// Icon dimensions (Requirement 4.5)
export const DATABASE_ICON_SIZE = 24; // 24x24 pixels (increased from 20px)
export const DATABASE_ICON_MARGIN = 8; // 8px margin from project name

// Text truncation limits (Requirement 3.1)
export const PROJECT_NAME_MAX_LENGTH = 6; // 6 characters before ellipsis

// Action button dimensions (Requirement 5.3)
export const ACTION_BUTTON_MIN_SIZE = 24; // 24x24 pixel minimum clickable area (缩小点击区域)
export const ACTION_BUTTON_SPACING = 4; // 4px spacing between buttons
export const ACTION_BUTTON_MARGIN = 8; // 8px margin from card edges

// Status badge styling (Requirement 6.4)
export const STATUS_BADGE_FONT_SIZE = 12; // 12px font size

// Date display styling (Requirement 8.4)
export const DATE_DISPLAY_FONT_SIZE = 11; // 11px font size

// Card margins and spacing (Requirement 6.5, 8.4)
export const CARD_ELEMENT_MARGIN = 8; // 8px margin from card edges

// Responsive breakpoints (Requirement 9.5)
export const MIN_VIEWPORT_WIDTH = 320; // 320px minimum supported width

// Project status translations (Requirement 6.1)
export const PROJECT_STATUS_LABELS = {
  initializing: '部署中',
  active: '运行中',
  inactive: '非活跃',
} as const;

// CSS class names for consistent styling
export const CSS_CLASSES = {
  projectCard: 'project-card',
  projectCardHover: 'project-card--hover',
  projectCardClickable: 'project-card--clickable',
  databaseIcon: 'database-icon',
  projectName: 'project-name',
  projectNameTruncated: 'project-name--truncated',
  projectDescription: 'project-description',
  projectDescriptionTruncated: 'project-description--truncated',
  actionButtons: 'action-buttons',
  actionButton: 'action-button',
  statusBadge: 'status-badge',
  statusBadgeActive: 'status-badge--active',
  statusBadgeInactive: 'status-badge--inactive',
  dateDisplay: 'date-display',
  tooltip: 'hover-tooltip',
  tooltipVisible: 'hover-tooltip--visible',
  modal: 'project-details-modal',
  modalOpen: 'project-details-modal--open',
} as const;