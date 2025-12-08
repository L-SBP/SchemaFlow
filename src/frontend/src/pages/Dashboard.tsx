import React, { useState, useRef, useEffect } from 'react';
import { ProjectDTO, fetchProjects, createProject, getProjectDetail, updateProject, confirmDeleteProject, deleteProject } from '../api/project';
import { Card, Button, Tag, Modal, Input, ProgressBar, Steps } from '../components/UI';
import { Plus, Database, Server, Clock, ArrowRight, Loader2, CheckCircle2, BrainCircuit, Code2, PlayCircle, Sparkles, RefreshCw, Edit3, Save, Trash2, AlertTriangle } from 'lucide-react';

// 常量定义
const DEPLOYMENT_STEPS = [
  { title: '需求分析', key: 'analyzing' },
  { title: 'Schema 设计', key: 'generating_schema' }, // 细化步骤
  { title: 'DDL 生成', key: 'generating_ddl' },
  { title: '服务就绪', key: 'completed' },
];

// 辅助函数：安全格式化日期
const formatDate = (dateString?: string) => {
  if (!dateString) return null;
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return null; // 检查日期是否有效
  return date.toLocaleDateString();
};

// 流式文本展示组件 (模拟打字机效果)
const StreamingViewer: React.FC<{ text?: string; placeholder?: React.ReactNode }> = ({ text, placeholder }) => {
  const [displayedText, setDisplayedText] = useState('');

  useEffect(() => {
    if (!text) {
      setDisplayedText('');
      return;
    }
    if (displayedText === text) return;

    const target = text;
    if (!target.startsWith(displayedText) && displayedText.length > 0) {
      setDisplayedText('');
      return;
    }

    const timer = setInterval(() => {
      setDisplayedText(current => {
        if (current.length < target.length) {
          return target.slice(0, current.length + 5); // 加快一点速度
        } else {
          clearInterval(timer);
          return target;
        }
      });
    }, 10);

    return () => clearInterval(timer);
  }, [text]);

  if (!text && !displayedText) return <>{placeholder}</>;

  return <div className="whitespace-pre-wrap animate-in fade-in duration-500">{displayedText}</div>;
};

interface DashboardProps {
  onProjectSelect?: (project: ProjectDTO) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onProjectSelect }) => {
  const [projects, setProjects] = useState<ProjectDTO[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // 部署状态管理
  const [isDeploying, setIsDeploying] = useState(false);
  const [currentProjectId, setCurrentProjectId] = useState<string | null>(null);
  const [isRefining, setIsRefining] = useState(false);
  const [refineDesc, setRefineDesc] = useState('');

  // 详情数据
  const [deploymentData, setDeploymentData] = useState<ProjectDTO | null>(null);
  // 视觉进度条状态
  const [visualProgress, setVisualProgress] = useState(0);

  // 创建表单状态
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectType, setNewProjectType] = useState<'MySQL' | 'PostgreSQL'>('MySQL');
  const [newProjectDesc, setNewProjectDesc] = useState('');

  // --- 项目管理状态 (编辑/删除) ---
  const [projectToDelete, setProjectToDelete] = useState<ProjectDTO | null>(null);
  const [deleteConfirmation, setDeleteConfirmation] = useState('');
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);

  const [projectToEdit, setProjectToEdit] = useState<ProjectDTO | null>(null);
  const [editName, setEditName] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  const analysisScrollRef = useRef<HTMLDivElement>(null);
  const ddlScrollRef = useRef<HTMLDivElement>(null);

  // 1. 初始化加载
  const loadProjects = async () => {
    try {
      const data = await fetchProjects();
      setProjects(data);
    } catch (error) {
      console.error("Failed to load projects:", error);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  // 2. 进度条动画控制逻辑
  useEffect(() => {
    let timer: NodeJS.Timeout;

    // 动态计算进度上限
    // 逻辑：如果没有拿到 schema_definition，卡在 45% (Schema 设计阶段)
    // 只有当 schema_definition 存在时，才允许进度条突破 45% 继续向 90% 迈进
    const hasSchemaData = !!deploymentData?.schema_definition?.schema;
    const progressCap = hasSchemaData ? 90 : 45;

    if (isDeploying && visualProgress < progressCap) {
      timer = setInterval(() => {
        setVisualProgress((prev) => {
          // 动态速度：前期快，接近 Cap 时变慢
          let increment = 0.5;
          if (progressCap - prev < 10) increment = 0.1;

          const next = prev + increment;
          return next >= progressCap ? progressCap : next;
        });
      }, 100);
    }

    return () => clearInterval(timer);
  }, [isDeploying, visualProgress, deploymentData]);

  // 3. 轮询逻辑：获取实时进度 (GET /projects/{id})
  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    if (isDeploying && currentProjectId) {
      // 立即执行一次
      const poll = async () => {
        try {
          const data = await getProjectDetail(currentProjectId);
          setDeploymentData(data);

          // 如果后端返回了进度，同步到视觉进度（取最大值，防止倒退）
          if (data.progress_percentage !== undefined) {
            setVisualProgress(prev => {
              const backendProgress = data.progress_percentage!;
              // 如果后端完成了，直接 100
              if (data.project_status === 'active') return 100;
              // 否则取较大值，确保进度条不会因为重新生成而突然跳回
              return Math.max(prev, backendProgress);
            });
          }

          if (!isRefining) {
            setRefineDesc(data.description);
          }

          // 检查是否完成
          if (data.project_status === 'active') {
            setVisualProgress(100);
            setIsDeploying(false);
            loadProjects();
          }
        } catch (error) {
          console.error("Polling error:", error);
        }
      };

      poll();
      // 轮询间隔 10 秒
      intervalId = setInterval(poll, 10000);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [isDeploying, currentProjectId, isRefining]);

  // 创建项目 (POST)
  const handleCreateProject = async () => {
    if (!newProjectName || !newProjectDesc) return;

    setIsDeploying(true);
    setVisualProgress(5); // 初始进度

    setDeploymentData({
      project_id: 'temp_pending_id',
      project_name: newProjectName,
      project_type: newProjectType,
      description: newProjectDesc,
      project_status: 'initializing',
      created_at: new Date().toISOString(),
      creation_stage: 'analyzing',
      progress_percentage: 5,
      analysis_result: '正在连接 AI 引擎进行初步需求分析...\n>>> 载入领域知识库...',
      ddl_result: '',
    });

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
      setDeploymentData(null);
      alert("创建失败，请检查网络或重试");
    }
  };

  // 需求微调更新
  const handleUpdateProjectRefine = async () => {
    if (!currentProjectId || !refineDesc) return;

    setIsRefining(false);
    setIsDeploying(true);
    setVisualProgress(10); // 重置进度条

    setDeploymentData(prev => prev ? ({
      ...prev,
      analysis_result: prev.analysis_result + '\n\n>>> 用户更新需求，重新分析中...',
      schema_definition: undefined, // 关键：清空 Schema，使进度条重新受制于 45% 卡点
      ddl_result: '',
      creation_stage: 'analyzing',
      progress_percentage: 10
    }) : null);

    try {
      await updateProject(currentProjectId, {
        description: refineDesc,
      });
    } catch (e) {
      console.error("Failed to update project:", e);
      alert("更新失败，请重试");
    }
  };

  const handleCloseModal = () => {
    // 直接关闭，不弹出确认框，停止前端轮询即视为终止当前部署流程的监控
    setIsModalOpen(false);
    setTimeout(() => {
      setNewProjectName('');
      setNewProjectDesc('');
      setIsDeploying(false);
      setCurrentProjectId(null);
      setDeploymentData(null);
      setVisualProgress(0);
      setIsRefining(false);
    }, 300);
  };

  // --- 项目管理操作 ---
  const handleDeleteClick = (e: React.MouseEvent, project: ProjectDTO) => {
    e.stopPropagation();
    setProjectToDelete(project);
    setDeleteConfirmation('');
    setIsDeleteModalOpen(true);
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
      alert("删除失败，请确认输入的验证信息正确");
    }
  };

  const handleEditClick = (e: React.MouseEvent, project: ProjectDTO) => {
    e.stopPropagation();
    setProjectToEdit(project);
    setEditName(project.project_name);
    setEditDesc(project.description);
    setIsEditModalOpen(true);
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
      alert("更新项目信息失败");
    }
  };

  // 渲染变量
  const progress = visualProgress;
  const currentStep = Math.min(Math.floor(progress / 25), 3);

  const analysisText = deploymentData?.schema_definition?.schema || deploymentData?.analysis_result;
  const ddlText = deploymentData?.schema_definition?.ddl || deploymentData?.ddl_result;

  const canRefine = deploymentData?.project_status !== 'active';
  const showProgressView = isDeploying || !!currentProjectId;

  return (
    // 修改: p-8 -> p-4 sm:p-8，优化移动端间距
    <div className="p-4 sm:p-8 max-w-7xl mx-auto h-full overflow-y-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-2xl font-bold text-gray-800 tracking-tight">数据库项目</h2>
          <p className="text-gray-500 mt-1">管理您的 AI 驱动数据库实例</p>
        </div>
        <Button variant="primary" icon={<Plus size={16} />} onClick={() => setIsModalOpen(true)}>
          新建项目
        </Button>
      </div>

      {/* 修改: grid-cols-1 sm:grid-cols-2... -> grid-cols-[repeat(auto-fill,minmax(280px,1fr))] */}
      {/* 这样可以保证卡片最小宽度 280px，自动填充，不会出现单列巨宽的情况 */}
      <div className="grid grid-cols-[repeat(auto-fill,minmax(300px,1fr))] gap-6">
        {projects.map(project => {
          const createdDate = formatDate(project.created_at);
          const updatedDate = formatDate(project.updated_at);

          return (
            <Card
              key={project.project_id}
              className="hover:shadow-lg transition-shadow cursor-pointer group border-gray-200 h-full flex flex-col w-full min-w-0"
              title={
                <div className="flex items-center gap-2.5 overflow-hidden w-full min-w-0">
                  <div className="p-2 bg-blue-50 rounded-lg text-primary shrink-0">
                    <Database size={20} />
                  </div>
                  <span className="font-semibold truncate">{project.project_name}</span>
                </div>
              }
              extra={
                <div className="flex items-center gap-3 shrink-0">
                  <Tag color={project.project_status === 'active' ? 'green' : 'orange'}>
                    {project.project_status === 'active' ? '运行中' : '初始化中'}
                  </Tag>
                  <div className="flex items-center gap-1 bg-white rounded-md border border-gray-100 shadow-sm p-0.5">
                    <button
                      className="p-1.5 text-gray-500 hover:text-primary hover:bg-gray-100 rounded transition-colors"
                      onClick={(e) => handleEditClick(e, project)}
                      title="编辑项目"
                    >
                      <Edit3 size={16} />
                    </button>
                    <button
                      className="p-1.5 text-gray-500 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                      onClick={(e) => handleDeleteClick(e, project)}
                      title="删除项目"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              }
            >
              <div className="flex flex-col h-full" onClick={() => onProjectSelect?.(project)}>
                <p className="text-gray-600 text-sm line-clamp-2 h-10 leading-relaxed mb-4">
                  {project.description}
                </p>

                <div className="mt-auto">
                  <div className="flex items-end justify-between text-xs text-gray-400 pt-4 border-t border-gray-50">
                    <div className="flex items-center gap-1.5 bg-gray-50 px-2 py-1 rounded mb-0.5">
                      <Server size={12} /> {project.project_type}
                    </div>
                    <div className="flex flex-col items-end gap-1.5">
                      {createdDate && (
                        <div className="flex items-center gap-1.5" title="创建时间">
                          <Clock size={12} /> {createdDate}
                        </div>
                      )}
                      {updatedDate && (
                        <div className="flex items-center gap-1.5 text-gray-500" title={`最后更新于: ${updatedDate}`}>
                          <RefreshCw size={12} /> {updatedDate}
                        </div>
                      )}
                      {!createdDate && !updatedDate && (
                        <div className="text-gray-300 italic">No date info</div>
                      )}
                    </div>
                  </div>

                  <div className="flex justify-end pt-2 opacity-0 group-hover:opacity-100 transition-all duration-300 transform translate-y-2 group-hover:translate-y-0 h-6">
                    <Button variant="text" className="text-primary text-xs hover:bg-blue-50 px-0" onClick={(e) => { e.stopPropagation(); onProjectSelect?.(project); }}>
                      进入工作台 <ArrowRight size={12} className="ml-1" />
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          )
        })}
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
          ) : (
            <div className="w-full flex justify-between items-center">
              <div className="text-xs text-gray-500 flex items-center gap-2">
                {isDeploying && <Loader2 size={14} className="animate-spin text-primary" />}
                {isDeploying ? 'AI 正在实时构建中，请稍候...' : '部署操作已就绪'}
              </div>
              <div className="flex gap-2">
                {deploymentData?.project_status === 'active' ? (
                  <Button variant="primary" onClick={handleCloseModal} icon={<CheckCircle2 size={16} />}>
                    完成并进入工作台
                  </Button>
                ) : (
                  <Button disabled className="opacity-50 cursor-not-allowed bg-gray-100 text-gray-400 border-gray-200">
                    正在部署中...
                  </Button>
                )}
              </div>
            </div>
          )
        }
      >
        {!showProgressView ? (
          <div className="space-y-6">
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-5 rounded-xl border border-blue-100 flex items-start gap-4">
              <div className="bg-white p-2 rounded-lg shadow-sm text-primary">
                <Sparkles size={24} />
              </div>
              <div className="text-sm text-blue-900">
                <p className="font-bold mb-1 text-base">AI 智能架构师</p>
                <p className="opacity-90 leading-relaxed">基于大模型。只需用自然语言描述业务场景，系统将自动完成 3NF 范式建模、SQL 生成及环境部署。</p>
              </div>
            </div>
            <div className="space-y-6">
              <Input label="项目名称" placeholder="例如：企业级 CRM 客户管理系统" value={newProjectName} onChange={(e) => setNewProjectName(e.target.value)} />
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-gray-700">数据库类型</label>
                <div className="grid grid-cols-2 gap-4">
                  {(['MySQL', 'PostgreSQL'] as const).map(type => (
                    <div key={type} onClick={() => setNewProjectType(type)} className={`cursor-pointer px-4 py-3 rounded-lg border flex items-center gap-3 transition-all ${newProjectType === type ? 'border-primary bg-blue-50 text-primary ring-1 ring-primary' : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'}`}>
                      <Database size={18} className={newProjectType === type ? 'text-primary' : 'text-gray-400'} />
                      <span className="text-sm font-medium">{type === 'MySQL' ? 'MySQL 8.0' : 'PostgreSQL 14'}</span>
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
          <div className="flex flex-col h-[650px] -m-2">
            <div className="mb-4 px-6 pt-2">
              <Steps steps={DEPLOYMENT_STEPS} current={currentStep} />
              <div className="mt-4 px-1">
                <ProgressBar progress={progress} />
              </div>
            </div>

            <div className="flex-1 flex gap-6 min-h-0 px-2 pb-2">
              <div className="flex-1 flex flex-col border border-gray-200 rounded-xl overflow-hidden shadow-sm bg-white relative">
                <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex justify-between items-center">
                  <div className="flex items-center gap-2.5">
                    <div className="p-1.5 bg-white rounded-md shadow-sm text-purple-600">
                      <BrainCircuit size={16} />
                    </div>
                    <span className="text-sm font-semibold text-gray-700">Schema 逻辑分析</span>
                  </div>
                  {canRefine && !isRefining && (
                    <Button variant="text" className="h-6 px-2 text-xs text-primary" onClick={() => setIsRefining(true)} icon={<Edit3 size={12} />}>
                      调整需求
                    </Button>
                  )}
                </div>

                {isRefining ? (
                  <div className="flex-1 p-4 flex flex-col animate-in fade-in slide-in-from-bottom-2">
                    <div className="flex-1">
                      <label className="text-xs font-bold text-gray-500 mb-2 block">修正业务描述 (Prompt)</label>
                      <textarea
                        className="w-full h-[90%] p-3 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary resize-none"
                        value={refineDesc}
                        onChange={(e) => setRefineDesc(e.target.value)}
                        placeholder="请输入新的需求描述，AI 将基于此重新生成 Schema..."
                      />
                    </div>
                    <div className="flex justify-end gap-2 mt-2">
                      <Button variant="default" onClick={() => setIsRefining(false)}>取消</Button>
                      <Button variant="primary" onClick={handleUpdateProjectRefine} icon={<RefreshCw size={14} />}>
                        更新并重新生成
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div ref={analysisScrollRef} className="flex-1 p-5 overflow-y-auto text-sm leading-7 text-gray-700 font-sans prose prose-sm max-w-none relative">
                    <StreamingViewer
                      text={analysisText}
                      placeholder={
                        <div className="h-full flex flex-col items-center justify-center text-gray-400 gap-2">
                          <Loader2 size={32} className="animate-spin opacity-20" />
                          <p>Waiting for analysis stream...</p>
                        </div>
                      }
                    />
                  </div>
                )}
              </div>

              <div className="flex-1 flex flex-col border border-gray-200 rounded-xl overflow-hidden shadow-sm bg-white">
                <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center gap-2.5">
                  <div className="p-1.5 bg-white rounded-md shadow-sm text-blue-600">
                    <Code2 size={16} />
                  </div>
                  <span className="text-sm font-semibold text-gray-700">Generated DDL (SQL)</span>
                </div>
                <div ref={ddlScrollRef} className="flex-1 p-5 overflow-y-auto font-mono text-xs leading-6 bg-white text-gray-700">
                  {ddlText ? (
                    <pre className="whitespace-pre-wrap"><code className="language-sql">
                      <StreamingViewer text={ddlText} />
                    </code></pre>
                  ) : (
                    <div className="h-full flex flex-col items-center justify-center text-gray-600 gap-2">
                      <Code2 size={32} className="opacity-20" />
                      <p>// Waiting for Schema lock...</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
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
              placeholder="在此输入项目名称"
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