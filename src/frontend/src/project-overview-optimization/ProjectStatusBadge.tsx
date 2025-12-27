/**
 * ProjectStatusBadge Component
 * Requirements: 6.1, 6.3, 6.4, 6.5
 */

import React from 'react';
import { ProjectStatusBadgeProps } from '../types/project-overview';
import { CSS_CLASSES, STATUS_BADGE_FONT_SIZE, CARD_ELEMENT_MARGIN } from '../constants/project-overview';
import { getStatusBadgeColorClass, getProjectStatusLabel } from '../utils/project-overview';
import './ProjectStatusBadge.css';

export const ProjectStatusBadge: React.FC<ProjectStatusBadgeProps> = ({
  status,
  className = '',
}) => {
  const colorClass = getStatusBadgeColorClass(status);
  const displayText = getProjectStatusLabel(status); // Use Chinese label

  return (
    <span
      className={`
        ${CSS_CLASSES.statusBadge}
        ${colorClass}
        ${className}
      `.trim()}
      style={{
        fontSize: `${STATUS_BADGE_FONT_SIZE}px`,
        marginBottom: `${CARD_ELEMENT_MARGIN}px`,
      }}
      aria-label={`项目状态: ${displayText}`}
    >
      {displayText}
    </span>
  );
};

export default ProjectStatusBadge;