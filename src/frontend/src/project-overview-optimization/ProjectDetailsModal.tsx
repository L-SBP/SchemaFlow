/**
 * ProjectDetailsModal component for displaying complete project information
 * Requirements: 7.3, 7.4, 7.5
 */

import React, { useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { ProjectDetailsModalProps } from '../types/project-overview';
import { formatProjectDate } from '../utils/project-overview';
import { CSS_CLASSES } from '../constants/project-overview';
import './ProjectDetailsModal.css';

export const ProjectDetailsModal: React.FC<ProjectDetailsModalProps> = ({
  project,
  isOpen,
  onClose,
}) => {
  // Handle ESC key press (Requirement 7.4)
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (event.key === 'Escape') {
      onClose();
    }
  }, [onClose]);

  // Handle click outside modal (Requirement 7.4)
  const handleBackdropClick = useCallback((event: React.MouseEvent<HTMLDivElement>) => {
    if (event.target === event.currentTarget) {
      onClose();
    }
  }, [onClose]);

  // Add/remove event listeners for ESC key
  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden';
    } else {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, handleKeyDown]);

  // Don't render if not open or no project data
  if (!isOpen || !project) {
    return null;
  }

  // Get database type display name
  const getDatabaseDisplayName = (dbType: string): string => {
    switch (dbType) {
      case 'mysql':
        return 'MySQL';
      case 'postgresql':
        return 'PostgreSQL';
      case 'sqlite':
        return 'SQLite';
      default:
        return '未知数据库';
    }
  };

  // Get status display name and class
  const getStatusInfo = (status: string) => {
    switch (status) {
      case 'initializing':
        return { display: '部署中', className: 'status--initializing' };
      case 'active':
        return { display: '运行中', className: 'status--active' };
      case 'inactive':
        return { display: '非活跃', className: 'status--inactive' };
      default:
        return { display: '未知状态', className: 'status--unknown' };
    }
  };

  const statusInfo = getStatusInfo(project.project_status);

  // 创建弹窗内容
  const modalContent = (
    <div
      className={`${CSS_CLASSES.modal} ${CSS_CLASSES.modalOpen}`}
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      aria-describedby="modal-description"
    >
      <div className="modal-content">
        {/* Modal Header */}
        <div className="modal-header">
          <h2 id="modal-title" className="modal-title">
            {project.project_name}
          </h2>
          <button
            className="modal-close-button"
            onClick={onClose}
            aria-label="关闭弹窗"
            type="button"
          >
            ×
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {/* Project Description */}
          <div className="modal-section">
            <h3 className="modal-section-title">项目描述</h3>
            <p id="modal-description" className="modal-description">
              {project.description && project.description.trim() ? project.description : '暂无项目描述'}
            </p>
          </div>

          {/* Project Details Grid */}
          <div className="modal-details-grid">
            <div className="modal-detail-item">
              <span className="modal-detail-label">数据库类型：</span>
              <span className="modal-detail-value">
                {getDatabaseDisplayName(project.db_type)}
              </span>
            </div>

            <div className="modal-detail-item">
              <span className="modal-detail-label">项目状态：</span>
              <span className={`modal-detail-value modal-status ${statusInfo.className}`}>
                {statusInfo.display}
              </span>
            </div>

            <div className="modal-detail-item">
              <span className="modal-detail-label">项目ID：</span>
              <span className="modal-detail-value">
                {project.project_id}
              </span>
            </div>

            <div className="modal-detail-item">
              <span className="modal-detail-label">最后更新：</span>
              <span className="modal-detail-value">
                {formatProjectDate(project.updated_at)}
              </span>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="modal-footer">
          <button
            className="modal-button modal-button--secondary"
            onClick={onClose}
            type="button"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  );

  // 使用 Portal 将弹窗渲染到 document.body 中，确保相对于整个页面定位
  return isOpen ? createPortal(modalContent, document.body) : null;
};

export default ProjectDetailsModal;