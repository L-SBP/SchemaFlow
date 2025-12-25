/**
 * ActionButtons Component
 * Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
 */

import React from 'react';
import { ActionButtonsProps } from '../types/project-overview';
import { CSS_CLASSES, ACTION_BUTTON_MIN_SIZE, ACTION_BUTTON_SPACING, ACTION_BUTTON_MARGIN } from '../constants/project-overview';
import './ActionButtons.css';

export const ActionButtons: React.FC<ActionButtonsProps> = ({
  projectId,
  onEdit,
  onDelete,
}) => {
  const handleEditClick = (event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent card click
    onEdit(projectId);
  };

  const handleDeleteClick = (event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent card click
    onDelete(projectId);
  };

  return (
    <div
      className={CSS_CLASSES.actionButtons}
      style={{
        display: 'flex',
        gap: `${ACTION_BUTTON_SPACING}px`,
        marginLeft: `${ACTION_BUTTON_MARGIN}px`,
      }}
    >
      {/* Edit Button */}
      <button
        className={`${CSS_CLASSES.actionButton} action-button--edit`}
        onClick={handleEditClick}
        title="编辑项目"
        aria-label={`编辑项目 ${projectId}`}
        style={{
          minWidth: `${ACTION_BUTTON_MIN_SIZE}px`,
          minHeight: `${ACTION_BUTTON_MIN_SIZE}px`,
        }}
      >
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
          <path d="m18.5 2.5 3 3L12 15l-4 1 1-4 9.5-9.5z" />
        </svg>
      </button>

      {/* Delete Button */}
      <button
        className={`${CSS_CLASSES.actionButton} action-button--delete`}
        onClick={handleDeleteClick}
        title="删除项目"
        aria-label={`删除项目 ${projectId}`}
        style={{
          minWidth: `${ACTION_BUTTON_MIN_SIZE}px`,
          minHeight: `${ACTION_BUTTON_MIN_SIZE}px`,
        }}
      >
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <polyline points="3,6 5,6 21,6" />
          <path d="m19,6v14a2,2 0 0,1 -2,2H7a2,2 0 0,1 -2,-2V6m3,0V4a2,2 0 0,1 2,-2h4a2,2 0 0,1 2,2v2" />
          <line x1="10" y1="11" x2="10" y2="17" />
          <line x1="14" y1="11" x2="14" y2="17" />
        </svg>
      </button>
    </div>
  );
};

export default ActionButtons;