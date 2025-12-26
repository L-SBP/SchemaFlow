/**
 * ProjectCard Component
 * Requirements: 1.1, 1.4, 9.1, 9.2
 */

import React, { useState } from 'react';
import { ProjectCardProps } from '../types/project-overview';
import { CSS_CLASSES } from '../constants/project-overview';
import { truncateProjectName, getProjectStatusLabel } from '../utils/project-overview';
import { Tag } from '../components/UI';
import DatabaseIcon from './DatabaseIcon';
import ActionButtons from './ActionButtons';
import DateDisplay from './DateDisplay';
import ProjectDetailsModal from './ProjectDetailsModal';
import './ProjectCard.css';

export const ProjectCard: React.FC<ProjectCardProps> = ({
  project,
  onCardClick,
  onEdit,
  onDelete,
}) => {
  const [showDetailsModal, setShowDetailsModal] = useState(false);

  // 获取项目状态的颜色和标签
  const getStatusColor = (status: string): 'blue' | 'green' | 'orange' | 'gray' => {
    switch (status) {
      case 'active':
        return 'green';
      case 'initializing':
        return 'orange';
      case 'inactive':
        return 'gray';
      default:
        return 'gray';
    }
  };

  // Handle "查看完整详情" click
  // Requirement 7.3: Open modal with complete project information
  const handleViewDetailsClick = (event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent card click
    setShowDetailsModal(true);
  };

  // Handle modal close
  const handleModalClose = () => {
    setShowDetailsModal(false);
  };

  // Handle card click (excluding action buttons)
  // Requirement 1.1: Click anywhere on card to navigate to project workspace
  // Requirement 1.4: Exclude action buttons from click area
  const handleCardClick = (event: React.MouseEvent<HTMLDivElement>) => {
    // Don't handle clicks if modal is open
    if (showDetailsModal) {
      return;
    }

    // Check if click target is an action button or its child
    const target = event.target as HTMLElement;
    const isActionButton = target.closest(`.${CSS_CLASSES.actionButtons}`);
    const isDetailsButton = target.closest('.view-details-button');

    if (!isActionButton && !isDetailsButton) {
      onCardClick(project.project_id);
    }
  };

  return (
    <div
      className={`
        ${CSS_CLASSES.projectCard}
        ${CSS_CLASSES.projectCardClickable}
      `.trim()}
      onClick={handleCardClick}
      role="button"
      tabIndex={0}
      aria-label={`Project: ${project.project_name}`}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onCardClick(project.project_id);
        }
      }}
    >
      {/* Header Section - Requirements 3.4, 5.1, 5.2, 5.5 */}
      <div className="project-card__header">
        <div className="project-card__header-left">
          {/* Requirement 4.1: Database icon on left side of project name */}
          <DatabaseIcon dbType={project.db_type} />

          {/* Requirement 3.1, 3.4: Truncated project name with proper alignment */}
          <span
            className={`${CSS_CLASSES.projectName} ${CSS_CLASSES.projectNameTruncated}`}
            title={project.project_name} // Show full name on hover
          >
            {truncateProjectName(project.project_name)}
          </span>
        </div>

        {/* Requirement 5.1, 5.5: Action buttons in top-right corner */}
        <ActionButtons
          projectId={project.project_id}
          onEdit={onEdit}
          onDelete={onDelete}
        />
      </div>

      {/* Content Section - 项目描述显示三行 */}
      <div className="project-card__content">
        {project.description && (
          <div className="project-description-container">
            <p className="project-description-multiline">
              {project.description}
            </p>
          </div>
        )}
      </div>

      {/* Footer Section - 状态、时间和查看详情按钮在同一行 */}
      <div className="project-card__footer">
        <div className="project-card__footer-left">
          {/* 使用 Tag 组件显示项目状态 */}
          <Tag color={getStatusColor(project.project_status)}>
            {getProjectStatusLabel(project.project_status as 'initializing' | 'active' | 'inactive')}
          </Tag>
        </div>

        {/* 中间显示时间 */}
        <div className="project-card__footer-center">
          <DateDisplay date={project.updated_at} />
        </div>

        {/* 右侧显示查看详情按钮 */}
        <div className="project-card__footer-right">
          <button
            className="view-details-button"
            onClick={handleViewDetailsClick}
            type="button"
            aria-label="查看项目详情"
            title="查看项目详情"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
          </button>
        </div>
      </div>

      {/* Project Details Modal - Requirements 7.3, 7.4, 7.5 */}
      {showDetailsModal && (
        <ProjectDetailsModal
          project={project}
          isOpen={showDetailsModal}
          onClose={handleModalClose}
        />
      )}
    </div>
  );
};

export default ProjectCard;