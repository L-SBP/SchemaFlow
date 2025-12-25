/**
 * ProjectCardGrid Component
 * Requirements: 9.1, 9.2, 9.4, 9.5
 * 
 * Responsive grid container for project cards that adapts to different screen sizes
 * and ensures accessibility at minimum 320px viewport width.
 */

import React from 'react';
import { ProjectData } from '../types/project-overview';
import ProjectCard from './ProjectCard';
import './ProjectCardGrid.css';

export interface ProjectCardGridProps {
  projects: ProjectData[];
  onCardClick: (projectId: number) => void;
  onEdit: (projectId: number) => void;
  onDelete: (projectId: number) => void;
}

export const ProjectCardGrid: React.FC<ProjectCardGridProps> = ({
  projects,
  onCardClick,
  onEdit,
  onDelete,
}) => {
  return (
    <div className="project-card-grid" role="grid" aria-label="项目列表">
      {projects.map((project) => (
        <div key={project.project_id} className="project-card-grid__item" role="gridcell">
          <ProjectCard
            project={project}
            onCardClick={onCardClick}
            onEdit={onEdit}
            onDelete={onDelete}
          />
        </div>
      ))}
    </div>
  );
};

export default ProjectCardGrid;