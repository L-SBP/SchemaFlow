/**
 * ProjectOverview Component - Main integration component
 * Requirements: All requirements integration
 * 
 * This component integrates all project overview optimization components
 * and provides error handling, loading states, and fallbacks.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { ProjectData } from '../types/project-overview';
import ProjectCardGrid from './ProjectCardGrid';
import { Pagination } from '../components/Pagination';
import './ProjectOverview.css';

export interface ProjectOverviewProps {
  projects?: ProjectData[];
  loading?: boolean;
  error?: string | null;
  onCardClick?: (projectId: number) => void;
  onEdit?: (projectId: number) => void;
  onDelete?: (projectId: number) => void;
  onRefresh?: () => void;
  pageSize?: number; // 每页显示的项目数量
}

export interface ProjectOverviewState {
  validatedProjects: ProjectData[];
  hasErrors: boolean;
  errorMessages: string[];
}

/**
 * Validate project data and provide fallbacks for missing fields
 * Requirement: Error handling for invalid project data
 */
function validateProjectData(project: any): ProjectData | null {
  try {
    // Check required fields
    if (!project || typeof project !== 'object') {
      return null;
    }

    const {
      project_id,
      project_name,
      description,
      project_status,
      updated_at,
      db_type
    } = project;

    // Validate project_id
    if (typeof project_id !== 'number' || project_id <= 0) {
      return null;
    }

    // Validate and provide fallbacks
    const validatedProject: ProjectData = {
      project_id,
      project_name: typeof project_name === 'string' && project_name.trim()
        ? project_name.trim()
        : `Project ${project_id}`,
      description: typeof description === 'string'
        ? description.trim()
        : '',
      project_status: ['initializing', 'active', 'inactive'].includes(project_status)
        ? project_status
        : 'inactive',
      updated_at: typeof updated_at === 'string' && updated_at.trim()
        ? updated_at.trim()
        : new Date().toISOString(),
      db_type: ['mysql', 'postgresql', 'sqlite'].includes(db_type)
        ? db_type
        : 'sqlite' // Default fallback
    };

    return validatedProject;
  } catch (error) {
    console.warn('Error validating project data:', error);
    return null;
  }
}

/**
 * Process and validate array of projects
 */
function processProjects(projects: any[]): ProjectOverviewState {
  if (!Array.isArray(projects)) {
    return {
      validatedProjects: [],
      hasErrors: true,
      errorMessages: ['Invalid projects data: expected array']
    };
  }

  const validatedProjects: ProjectData[] = [];
  const errorMessages: string[] = [];

  projects.forEach((project, index) => {
    const validated = validateProjectData(project);
    if (validated) {
      validatedProjects.push(validated);
    } else {
      errorMessages.push(`Invalid project data at index ${index}`);
    }
  });

  return {
    validatedProjects,
    hasErrors: errorMessages.length > 0,
    errorMessages
  };
}

export const ProjectOverview: React.FC<ProjectOverviewProps> = ({
  projects = [],
  loading = false,
  error = null,
  onCardClick,
  onEdit,
  onDelete,
  onRefresh,
  pageSize = 9 // 每页显示9个项目
}) => {
  const [processedState, setProcessedState] = useState<ProjectOverviewState>({
    validatedProjects: [],
    hasErrors: false,
    errorMessages: []
  });

  // 分页状态
  const [currentPage, setCurrentPage] = useState(1);

  // 分页数据
  const paginatedProjects = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return processedState.validatedProjects.slice(start, start + pageSize);
  }, [processedState.validatedProjects, currentPage, pageSize]);

  const totalProjects = processedState.validatedProjects.length;

  // Process projects when they change
  useEffect(() => {
    const processed = processProjects(projects);
    setProcessedState(processed);
    // 重置到第一页
    setCurrentPage(1);

    // Log validation errors for debugging
    if (processed.hasErrors) {
      console.warn('Project validation errors:', processed.errorMessages);
    }
  }, [projects]);

  // Default handlers with error handling
  const handleCardClick = useCallback((projectId: number) => {
    try {
      if (onCardClick) {
        onCardClick(projectId);
      } else {
        console.warn('No onCardClick handler provided');
      }
    } catch (error) {
      console.error('Error handling card click:', error);
    }
  }, [onCardClick]);

  const handleEdit = useCallback((projectId: number) => {
    try {
      if (onEdit) {
        onEdit(projectId);
      } else {
        console.warn('No onEdit handler provided');
      }
    } catch (error) {
      console.error('Error handling edit:', error);
    }
  }, [onEdit]);

  const handleDelete = useCallback((projectId: number) => {
    try {
      if (onDelete) {
        onDelete(projectId);
      } else {
        console.warn('No onDelete handler provided');
      }
    } catch (error) {
      console.error('Error handling delete:', error);
    }
  }, [onDelete]);

  const handleRefresh = useCallback(() => {
    try {
      if (onRefresh) {
        onRefresh();
      }
    } catch (error) {
      console.error('Error handling refresh:', error);
    }
  }, [onRefresh]);

  // Loading state
  if (loading) {
    return (
      <div className="project-overview project-overview--loading">
        <div className="project-overview__loading">
          <div className="loading-spinner" aria-label="Loading projects...">
            <div className="spinner"></div>
          </div>
          <p className="loading-text">Loading projects...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="project-overview project-overview--error">
        <div className="project-overview__error">
          <div className="error-icon" aria-hidden="true">⚠️</div>
          <h3 className="error-title">Failed to load projects</h3>
          <p className="error-message">{error}</p>
          {onRefresh && (
            <button
              className="error-retry-button"
              onClick={handleRefresh}
              type="button"
            >
              Try Again
            </button>
          )}
        </div>
      </div>
    );
  }

  // Empty state
  if (processedState.validatedProjects.length === 0) {
    return (
      <div className="project-overview project-overview--empty">
        <div className="project-overview__empty">
          <div className="empty-icon" aria-hidden="true">📁</div>
          <h3 className="empty-title">No projects found</h3>
          <p className="empty-message">
            {processedState.hasErrors
              ? 'Some projects could not be loaded due to invalid data.'
              : 'You don\'t have any projects yet.'}
          </p>
          {onRefresh && (
            <button
              className="empty-refresh-button"
              onClick={handleRefresh}
              type="button"
            >
              Refresh
            </button>
          )}
        </div>
      </div>
    );
  }

  // Success state with validation warnings
  return (
    <div className="project-overview flex flex-col h-full">
      {/* Validation warnings */}
      {processedState.hasErrors && (
        <div className="project-overview__warnings" role="alert">
          <div className="warning-icon" aria-hidden="true">⚠️</div>
          <div className="warning-content">
            <p className="warning-title">Some projects have data issues</p>
            <p className="warning-message">
              {processedState.errorMessages.length} project(s) could not be loaded properly.
              Default values have been applied where possible.
            </p>
          </div>
        </div>
      )}

      {/* Project grid */}
      <div className="project-grid-container">
        <ProjectCardGrid
          projects={paginatedProjects}
          onCardClick={handleCardClick}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      </div>

      {/* 分页控件 - 固定在底部，始终显示 */}
      {totalProjects > 0 && (
        <div className="pagination-container">
          <div className="pagination-wrapper">
            <Pagination
              current={currentPage}
              total={totalProjects}
              pageSize={pageSize}
              onChange={setCurrentPage}
              showTotal={true}
              simple={window.innerWidth < 640}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectOverview;