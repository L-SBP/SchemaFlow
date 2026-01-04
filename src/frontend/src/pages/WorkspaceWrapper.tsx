/**
 * WorkspaceWrapper 组件
 * 处理从 URL 参数加载项目数据，支持直接访问 /workspace/:projectId
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Workspace } from './Workspace';
import { Project } from '../types';
import { getProjectDetail, ProjectDTO } from '../api/project';
import { Loader2 } from 'lucide-react';
import { ROUTES } from '../routes/index';

interface WorkspaceWrapperProps {
  /** 从父组件传入的已选项目（如果有） */
  selectedProject: Project | null;
  /** 设置选中项目的回调 */
  onProjectSelect: (project: Project) => void;
  /** 返回 Dashboard 的回调 */
  onBack: () => void;
}

export const WorkspaceWrapper: React.FC<WorkspaceWrapperProps> = ({
  selectedProject,
  onProjectSelect,
  onBack
}) => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 如果 URL 中有 projectId 但 selectedProject 为空，尝试从 API 加载
  useEffect(() => {
    const loadProject = async () => {
      if (!projectId) {
        navigate(ROUTES.DASHBOARD, { replace: true });
        return;
      }

      // 如果已有项目且 ID 匹配，无需重新加载
      if (selectedProject && selectedProject.id === projectId) {
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const projectDTO: ProjectDTO = await getProjectDetail(projectId);

        // 转换 DTO 为 Project 类型
        const dbTypeMap: Record<string, 'MySQL' | 'PostgreSQL' | 'SQLite'> = {
          'mysql': 'MySQL',
          'postgresql': 'PostgreSQL',
          'sqlite': 'SQLite'
        };

        const statusMap: Record<string, 'active' | 'deploying' | 'error' | 'deleted'> = {
          'initializing': 'deploying',
          'pending_confirmation': 'deploying',
          'active': 'active',
          'deleted': 'deleted',
          'error': 'error'
        };

        const project: Project = {
          id: projectDTO.project_id.toString(),
          name: projectDTO.project_name,
          type: dbTypeMap[projectDTO.db_type.toLowerCase()] || 'MySQL',
          description: projectDTO.description,
          status: statusMap[projectDTO.project_status.toLowerCase()] || 'active',
          createdAt: projectDTO.created_at
        };

        onProjectSelect(project);
      } catch (err: any) {
        console.error('Failed to load project:', err);
        setError('项目加载失败，即将返回项目列表...');
        // 延迟跳转，让用户看到错误信息
        setTimeout(() => {
          navigate(ROUTES.DASHBOARD, { replace: true });
        }, 2000);
      } finally {
        setLoading(false);
      }
    };

    loadProject();
  }, [projectId, selectedProject, navigate, onProjectSelect]);

  // 加载中状态
  if (loading) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-gray-50">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="animate-spin text-primary" size={40} />
          <p className="text-gray-500 text-sm">正在加载项目...</p>
        </div>
      </div>
    );
  }

  // 错误状态
  if (error) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-gray-50">
        <div className="flex flex-col items-center gap-3 text-center">
          <p className="text-red-500">{error}</p>
        </div>
      </div>
    );
  }

  // 项目已加载，渲染 Workspace
  if (selectedProject) {
    return <Workspace project={selectedProject} onBack={onBack} />;
  }

  // 兜底：无项目时显示加载
  return (
    <div className="flex h-full w-full items-center justify-center bg-gray-50">
      <Loader2 className="animate-spin text-primary" size={40} />
    </div>
  );
};
