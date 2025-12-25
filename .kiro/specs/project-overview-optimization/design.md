# Design Document

## Overview

This design document outlines the implementation approach for optimizing the project overview display. The solution focuses on improving user experience through enhanced project card interactions, better visual hierarchy, and more efficient use of screen space.

The design emphasizes direct interaction patterns, visual feedback, and responsive layout principles to create a more intuitive project management interface.

## Architecture

### Component Structure

```
ProjectOverview
├── ProjectCardGrid
│   └── ProjectCard[]
│       ├── DatabaseIcon
│       ├── ProjectHeader
│       │   ├── ProjectName (truncated)
│       │   └── ActionButtons
│       ├── ProjectDescription (truncated)
│       ├── ProjectFooter
│       │   ├── ProjectStatus (bottom-left)
│       │   └── UpdatedDate (bottom-right)
│       └── HoverTooltip
└── ProjectDetailsModal
```

### State Management

The component will manage the following state:
- `hoveredCard`: Currently hovered project card ID
- `showDetailsModal`: Boolean for modal visibility
- `selectedProject`: Project data for modal display
- `tooltipPosition`: Calculated position for hover tooltip

## Components and Interfaces

### ProjectCard Component

```typescript
interface ProjectCardProps {
  project: {
    project_id: number;
    project_name: string;
    description: string;
    project_status: 'active' | 'inactive';
    updated_at: string;
    db_type: 'mysql' | 'postgresql' | 'sqlite';
  };
  onCardClick: (projectId: number) => void;
  onEdit: (projectId: number) => void;
  onDelete: (projectId: number) => void;
}
```

### HoverTooltip Component

```typescript
interface HoverTooltipProps {
  project: ProjectData;
  position: { x: number; y: number };
  visible: boolean;
}
```

### DatabaseIcon Component

```typescript
interface DatabaseIconProps {
  dbType: 'mysql' | 'postgresql' | 'sqlite';
  size?: number;
}
```

## Data Models

### Project Data Structure

```typescript
interface ProjectData {
  project_id: number;
  project_name: string;
  description: string;
  project_status: 'active' | 'inactive';
  updated_at: string; // ISO 8601 format
  db_type: 'mysql' | 'postgresql' | 'sqlite';
}
```

### Tooltip Position Calculation

```typescript
interface TooltipPosition {
  x: number;
  y: number;
  placement: 'top' | 'bottom' | 'left' | 'right';
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Card Click Navigation
*For any* project card with valid project data, clicking anywhere on the card (excluding action buttons) should trigger navigation to the project workspace with the correct project ID.
**Validates: Requirements 1.1, 1.4**

### Property 2: Hover Tooltip Display
*For any* project card, hovering over the card should display a tooltip containing all project information (name, description, database type, status, updated date) after a 500ms delay.
**Validates: Requirements 2.1, 2.2, 2.3**

### Property 3: Project Name Truncation
*For any* project name longer than 6 characters, the card display should show the name truncated with ellipsis, while the tooltip shows the complete name.
**Validates: Requirements 3.1, 3.2**

### Property 4: Database Icon Selection
*For any* project with a valid database type (mysql, postgresql, sqlite), the card should display the corresponding database icon, and for invalid/null types, should display a generic database icon.
**Validates: Requirements 4.2, 4.3, 4.4, 4.6**

### Property 5: Action Button Accessibility
*For any* project card, the edit and delete action buttons should maintain minimum 32x32 pixel clickable areas and be positioned in the top-right corner with proper spacing.
**Validates: Requirements 5.1, 5.3, 5.5**

### Property 6: Status Badge Display
*For any* project status value, the card should display a properly styled badge in the bottom-left corner with appropriate color coding (green for active, gray for inactive).
**Validates: Requirements 6.1, 6.3**

### Property 7: Description Truncation and Modal
*For any* project with a description that exceeds available card space, the card should truncate the description and provide a clickable element that opens a modal with complete project information.
**Validates: Requirements 7.1, 7.2, 7.3, 7.4**

### Property 8: Date Formatting
*For any* project update date, the card should display the date in "YYYY-MM-DD HH:mm" format, or "今天 HH:mm" if the date is today.
**Validates: Requirements 8.1, 8.5**

### Property 9: Layout Consistency
*For any* set of project cards, all cards should maintain consistent dimensions, spacing, and responsive behavior across different viewport sizes down to 320px width.
**Validates: Requirements 9.1, 9.2, 9.4, 9.5**

### Property 10: Tooltip Positioning
*For any* project card positioned near viewport edges, the hover tooltip should be repositioned to remain fully visible within the viewport boundaries.
**Validates: Requirements 2.4**

## Error Handling

### Invalid Project Data
- **Missing required fields**: Display placeholder values and log warnings
- **Invalid database type**: Fall back to generic database icon
- **Malformed dates**: Display "Invalid Date" with error styling
- **Empty descriptions**: Hide description area and truncation controls

### UI Interaction Errors
- **Tooltip positioning failures**: Fall back to default positioning (top-right of card)
- **Modal display errors**: Show error message in place of modal content
- **Navigation failures**: Display error toast and prevent navigation
- **Hover state conflicts**: Clear all hover states on component unmount

### Responsive Layout Failures
- **Insufficient space**: Hide non-essential elements progressively
- **Text overflow**: Apply ellipsis truncation as fallback
- **Icon loading failures**: Display text labels as fallback
- **CSS loading failures**: Apply inline styles for critical layout

## Testing Strategy

### Dual Testing Approach
This feature will use both unit tests and property-based tests to ensure comprehensive coverage:

**Unit Tests** will focus on:
- Specific examples of project data rendering
- Edge cases like empty descriptions, invalid dates
- Modal interaction flows
- Error conditions and fallback behaviors

**Property-Based Tests** will focus on:
- Universal properties that hold across all project data variations
- Layout consistency across different screen sizes
- Tooltip positioning logic with various viewport configurations
- Text truncation behavior with random string lengths

### Property-Based Testing Configuration
- **Testing Library**: React Testing Library with @fast-check/jest for property-based testing
- **Minimum iterations**: 100 per property test
- **Test tagging format**: **Feature: project-overview-optimization, Property {number}: {property_text}**

### Key Testing Areas

**Visual Regression Testing**:
- Card layout consistency across different project data
- Responsive behavior at various viewport sizes
- Hover states and transitions
- Modal appearance and positioning

**Interaction Testing**:
- Click handling for cards vs action buttons
- Hover tooltip timing and positioning
- Modal open/close behaviors
- Keyboard navigation support

**Data Handling Testing**:
- Project data parsing and display
- Date formatting with various input formats
- Text truncation with different string lengths
- Icon selection based on database types

**Accessibility Testing**:
- Minimum clickable area requirements
- Keyboard navigation support
- Screen reader compatibility
- Color contrast requirements

### Performance Considerations
- **Tooltip rendering**: Use virtualization for large project lists
- **Hover debouncing**: Implement 500ms delay to prevent excessive tooltip creation
- **Modal lazy loading**: Load modal content only when needed
- **Icon optimization**: Use SVG sprites for database icons to reduce bundle size