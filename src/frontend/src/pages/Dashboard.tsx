import React, { useState, useEffect } from 'react';
import { ProjectDTO, fetchProjects, createProject, updateProject, confirmDeleteProject, deleteProject } from '../api/project';
import { ProjectStatusEnum } from '../types';
import { Button, Modal, Input, message } from '../components/UI';
import { Plus, PlayCircle, Sparkles, AlertTriangle, LayoutDashboard, Database } from 'lucide-react';
import { ProjectWizard } from '../components/ProjectWizard';
import { ProjectOverview } from '../project-overview-optimization/ProjectOverview';
import { ProjectData } from '../types/project-overview';

// 数据转换函数：将 ProjectDTO 转换为 ProjectData
const convertProjectDTOToProjectData = (dto: ProjectDTO): ProjectData => {
  // 状态映射
  let projectStatus: 'initializing' | 'active' | 'inactive';
  switch (dto.project_status) {
    case ProjectStatusEnum.INITIALIZING:
      projectStatus = 'initializing';
      break;
    case ProjectStatusEnum.ACTIVE:
      projectStatus = 'active';
      break;
    default:
      projectStatus = 'inactive';
      break;
  }

  return {
    project_id: dto.project_id,
    project_name: dto.project_name,
    description: dto.description,
    project_status: projectStatus,
    updated_at: dto.updated_at || dto.created_at,
    db_type: dto.db_type
  };
};

interface DashboardProps {
  onProjectSelect?: (project: ProjectDTO) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onProjectSelect }) => {
  const [projects, setProjects] = useState<ProjectDTO[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 部署状态管理
  const [isDeploying, setIsDeploying] = useState(false);
  const [currentProjectId, setCurrentProjectId] = useState<string | number | null>(null);

  // 创建表单状态
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectType, setNewProjectType] = useState<'MySQL' | 'PostgreSQL' | 'SQLite'>('MySQL');
  const [newProjectDesc, setNewProjectDesc] = useState('');

  // --- 项目管理状态 (编辑/删除) ---
  const [projectToDelete, setProjectToDelete] = useState<ProjectDTO | null>(null);
  const [deleteConfirmation, setDeleteConfirmation] = useState('');
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);

  const [projectToEdit, setProjectToEdit] = useState<ProjectDTO | null>(null);
  const [editName, setEditName] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  // 1. 初始化加载
  const loadProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchProjects();
      setProjects(data.items);
    } catch (error) {
      console.error("Failed to load projects:", error);
      setError("Failed to load projects. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  // 创建项目 (POST)
  const handleCreateProject = async () => {
    if (!newProjectName || !newProjectDesc) return;

    setIsDeploying(true);

    try {
      const res = await createProject({
        name: newProjectName,
        type: newProjectType,
        description: newProjectDesc
      });
      setCurrentProjectId(res.project_id);
    } catch (e) {
      console.error("Failed to create project:", e);
      setIsDeploying(false);
      setCurrentProjectId(null);
      message.error("创建失败，请检查网络或重试");
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setTimeout(() => {
      setNewProjectName('');
      setNewProjectDesc('');
      setIsDeploying(false);
      setCurrentProjectId(null);
    }, 300);
    loadProjects();
  };

  // --- 项目管理操作 ---
  const handleCardClick = (projectId: number) => {
    const project = projects.find(p => p.project_id === projectId);
    if (project) {
      if (project.project_status === ProjectStatusEnum.ACTIVE) {
        onProjectSelect?.(project);
      } else {
        // Resume deployment
        setCurrentProjectId(project.project_id);
        setIsDeploying(true);
        setIsModalOpen(true);
      }
    }
  };

  const handleDeleteClick = (projectId: number) => {
    const project = projects.find(p => p.project_id === projectId);
    if (project) {
      setProjectToDelete(project);
      setDeleteConfirmation('');
      setIsDeleteModalOpen(true);
    }
  };

  const handleConfirmDelete = async () => {
    if (!projectToDelete) return;
    try {
      const { confirmation_token } = await confirmDeleteProject(projectToDelete.project_id, deleteConfirmation);
      await deleteProject(projectToDelete.project_id, confirmation_token);
      setIsDeleteModalOpen(false);
      setProjectToDelete(null);
      loadProjects();
    } catch (err) {
      console.error("Delete failed", err);
      message.error("删除失败，请确认输入的验证信息正确");
    }
  };

  const handleEditClick = (projectId: number) => {
    const project = projects.find(p => p.project_id === projectId);
    if (project) {
      setProjectToEdit(project);
      setEditName(project.project_name);
      setEditDesc(project.description);
      setIsEditModalOpen(true);
    }
  };

  const handleSaveEdit = async () => {
    if (!projectToEdit) return;
    try {
      await updateProject(projectToEdit.project_id, {
        project_name: editName,
        description: editDesc
      });
      setIsEditModalOpen(false);
      setProjectToEdit(null);
      loadProjects();
    } catch (err) {
      console.error("Update failed", err);
      message.error("更新项目信息失败");
    }
  };

  const showProgressView = isDeploying && !!currentProjectId;

  return (
    // 优化响应式间距和布局
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto h-full flex flex-col overflow-hidden">
      {/* 项目概览标题区域 - 使用与系统公告一致的样式 */}
      <div className="flex-shrink-0 flex items-center gap-3 mb-6">
        <div className="p-2 bg-blue-100 text-blue-600 rounded-lg shrink-0">
          <LayoutDashboard size={20} className="sm:w-6 sm:h-6" />
        </div>
        <div className="min-w-0">
          <h2 className="text-xl sm:text-2xl font-bold text-gray-800 truncate">项目概览</h2>
          <p className="text-gray-500 text-sm hidden sm:block">管理您的 AI 驱动数据库实例</p>
        </div>
        <div className="ml-auto">
          <Button variant="primary" icon={<Plus size={16} />} onClick={() => setIsModalOpen(true)} className="shrink-0 w-full sm:w-auto">
            新建项目
          </Button>
        </div>
      </div>

      {/* 使用优化后的项目概览组件 */}
      <div className="flex-1 min-h-0">
        <ProjectOverview
          projects={projects.map(convertProjectDTOToProjectData)}
          loading={loading}
          error={error}
          onCardClick={handleCardClick}
          onEdit={handleEditClick}
          onDelete={handleDeleteClick}
          onRefresh={loadProjects}
        />
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        title={!showProgressView ? "创建新的数据库项目" : "自动化部署中心"}
        maxWidth={!showProgressView ? 'max-w-2xl' : 'max-w-6xl'}
        footer={
          !showProgressView ? (
            <>
              <Button onClick={handleCloseModal}>取消</Button>
              <Button variant="primary" onClick={handleCreateProject} icon={<PlayCircle size={16} />}>
                开始智能部署
              </Button>
            </>
          ) : null
        }
      >
        {!showProgressView ? (
          <div className="space-y-6">
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-5 rounded-xl border border-blue-100 flex items-start gap-4">
              <div className="bg-white p-2 rounded-lg shadow-sm text-primary">
                <Sparkles size={24} />
              </div>
              <div className="text-sm text-blue-900">
                <p className="font-bold mb-1 text-base">AI 智能部署</p>
                <p className="opacity-90 leading-relaxed">基于大模型。只需用自然语言描述业务场景，系统将自动完成数据库部署。</p>
              </div>
            </div>
            <div className="space-y-6">
              <Input label="项目名称" placeholder="例如：企业级 CRM 客户管理系统" value={newProjectName} onChange={(e) => setNewProjectName(e.target.value)} />
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-gray-700">数据库类型</label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
                  {/* 更新：增加 SQLite 选项 */}
                  {(['MySQL', 'PostgreSQL', 'SQLite'] as const).map(type => (
                    <div key={type} onClick={() => setNewProjectType(type)} className={`cursor-pointer px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg border flex items-center gap-2 sm:gap-3 transition-all ${newProjectType === type ? 'border-primary bg-blue-50 text-primary ring-1 ring-primary' : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'}`}>
                      <Database size={18} className={newProjectType === type ? 'text-primary' : 'text-gray-400'} />
                      <span className="text-sm font-medium">{type}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-gray-700">业务场景描述</label>
                <textarea className="px-4 py-3 bg-white border border-gray-300 rounded-lg text-sm focus:border-primary focus:ring-2 focus:ring-blue-100 transition-all h-32 resize-none leading-relaxed" placeholder="请详细描述实体及关系..." value={newProjectDesc} onChange={(e) => setNewProjectDesc(e.target.value)}></textarea>
              </div>
            </div>
          </div>
        ) : (
          <ProjectWizard
            projectId={currentProjectId!}
            onComplete={handleCloseModal}
            onClose={handleCloseModal}
          />
        )}
      </Modal>

      {/* 删除确认模态框 */}
      <Modal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        title="确认删除项目"
        maxWidth="max-w-md"
        footer={
          <>
            <Button onClick={() => setIsDeleteModalOpen(false)}>取消</Button>
            <Button variant="danger" onClick={handleConfirmDelete} disabled={!deleteConfirmation}>
              确认删除
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="bg-red-50 p-4 rounded-lg flex items-start gap-3 text-sm text-red-800 border border-red-100">
            <AlertTriangle size={18} className="mt-0.5 shrink-0" />
            <div>
              <p className="font-bold mb-1">高风险操作</p>
              <p>此操作将永久删除项目 <strong>{projectToDelete?.project_name}</strong> 及其所有关联的数据（表结构、数据、Schema）。此操作无法撤销！</p>
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">
              请在此输入DELETE以确认删除：
            </label>
            <Input
              value={deleteConfirmation}
              onChange={(e) => setDeleteConfirmation(e.target.value)}
              placeholder=""
              className="border-red-300 focus:border-red-500 focus:ring-red-100"
            />
          </div>
        </div>
      </Modal>

      {/* 编辑项目模态框 */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="编辑项目信息"
        maxWidth="max-w-md"
        footer={
          <>
            <Button onClick={() => setIsEditModalOpen(false)}>取消</Button>
            <Button variant="primary" onClick={handleSaveEdit}>保存更改</Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input
            label="项目名称"
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            placeholder="项目名称"
          />
          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium text-gray-700">项目描述</label>
            <textarea
              className="px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm focus:border-primary focus:ring-2 focus:ring-blue-100 transition-all h-24 resize-none leading-relaxed"
              value={editDesc}
              onChange={(e) => setEditDesc(e.target.value)}
              placeholder="项目描述"
            ></textarea>
          </div>
        </div>
      </Modal>

    </div>
  );
};