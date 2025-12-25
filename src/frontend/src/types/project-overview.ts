/**
 * TypeScript interfaces for Project Overview Optimization feature
 * Requirements: 4.2, 4.3, 4.4, 4.6
 */

// Core project data structure for project overview
export interface ProjectData {
  project_id: number;
  project_name: string;
  description: string;
  project_status: 'initializing' | 'active' | 'inactive';
  updated_at: string; // ISO 8601 format
  db_type: 'mysql' | 'postgresql' | 'sqlite';
}

// Project card component props
export interface ProjectCardProps {
  project: ProjectData;
  onCardClick: (projectId: number) => void;
  onEdit: (projectId: number) => void;
  onDelete: (projectId: number) => void;
}

// Database icon component props
export interface DatabaseIconProps {
  dbType: 'mysql' | 'postgresql' | 'sqlite';
  size?: number;
  className?: string;
}

// Project details modal component props
export interface ProjectDetailsModalProps {
  project: ProjectData | null;
  isOpen: boolean;
  onClose: () => void;
}

// Action buttons component props
export interface ActionButtonsProps {
  projectId: number;
  onEdit: (projectId: number) => void;
  onDelete: (projectId: number) => void;
}

// Project status badge props
export interface ProjectStatusBadgeProps {
  status: 'initializing' | 'active' | 'inactive';
  className?: string;
}

// Date formatter utility props
export interface DateFormatterProps {
  date: string;
  className?: string;
}

// Text truncation utility props
export interface TextTruncationProps {
  text: string;
  maxLength: number;
  showTooltip?: boolean;
}

// Project overview grid props
export interface ProjectOverviewGridProps {
  projects: ProjectData[];
  onCardClick: (projectId: number) => void;
  onEdit: (projectId: number) => void;
  onDelete: (projectId: number) => void;
}