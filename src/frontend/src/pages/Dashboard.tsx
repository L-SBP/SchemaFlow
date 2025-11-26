import React, { useState, useRef, useEffect } from 'react';
// 注意：这里导入的是 API 定义的类型
import { ProjectDTO, fetchProjects, createProject, getProjectDetail } from '../api/project';
import { Card, Button, Tag, Modal, Input, ProgressBar, Steps } from '../components/UI';
import { Plus, Database, Server, Clock, ArrowRight, Terminal, Loader2, CheckCircle2, BrainCircuit, Code2, PlayCircle, Sparkles } from 'lucide-react';

// 常量定义
const DEPLOYMENT_STEPS = [
  { title: '需求分析', key: 'analyzing' },
  { title: '逻辑设计', key: 'generating_ddl' },
  { title: '环境部署', key: 'deploying' },
  { title: '服务就绪', key: 'completed' },
];

// 辅助函数：根据后端 stage 映射到 Step 索引
const getStepIndex = (stage?: string) => {
  if (!stage) return 0;
  const index = DEPLOYMENT_STEPS.findIndex(s => s.key === stage);
  return index === -1 ? 0 : index;
};

// 定义组件 Props，恢复 onProjectSelect 回调支持
interface DashboardProps {
  onProjectSelect?: (project: ProjectDTO) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onProjectSelect }) => {
  const [projects, setProjects] = useState<ProjectDTO[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // 部署状态管理
  const [isDeploying, setIsDeploying] = useState(false);
  const [currentProjectId, setCurrentProjectId] = useState<string | null>(null);

  // 详情数据 (全部来自 API)
  const [deploymentData, setDeploymentData] = useState<ProjectDTO | null>(null);

  // 表单状态
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectType, setNewProjectType] = useState<'MySQL' | 'PostgreSQL'>('MySQL');
  const [newProjectDesc, setNewProjectDesc] = useState('');

  const logsEndRef = useRef<HTMLDivElement>(null);
  const analysisScrollRef = useRef<HTMLDivElement>(null);
  const ddlScrollRef = useRef<HTMLDivElement>(null);

  // 1. 初始化加载项目列表
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

  // 2. 轮询逻辑：当处于部署状态且有 ProjectID 时执行
  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    if (isDeploying && currentProjectId) {
      intervalId = setInterval(async () => {
        try {
          const data = await getProjectDetail(currentProjectId);
          setDeploymentData(data);

          // 自动滚动日志
          if (logsEndRef.current) logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
          if (analysisScrollRef.current) analysisScrollRef.current.scrollTop = analysisScrollRef.current.scrollHeight;
          if (ddlScrollRef.current) ddlScrollRef.current.scrollTop = ddlScrollRef.current.scrollHeight;

          // 检查是否完成
          if (data.project_status === 'active') {
            setIsDeploying(false); // 停止轮询，保持模态框开启显示结果
            loadProjects(); // 刷新列表
          }
        } catch (error) {
          console.error("Polling error:", error);
        }
      }, 1000); // 每秒轮询一次
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [isDeploying, currentProjectId]);

  const handleCreateProject = async () => {
    if (!newProjectName || !newProjectDesc) return;

    try {
      setIsDeploying(true);
      // 1. 调用 API 创建项目
      const res = await createProject({
        name: newProjectName,
        type: newProjectType,
        description: newProjectDesc
      });

      // 2. 记录 ID，触发上面的 useEffect 开始轮询
      setCurrentProjectId(res.project_id);

    } catch (e) {
      console.error("Failed to create project:", e);
      setIsDeploying(false);
    }
  };

  const handleCloseModal = () => {
    if (isDeploying && deploymentData?.project_status !== 'active') {
      if (!confirm("部署正在云端进行中，关闭窗口不影响后台部署。确定关闭吗？")) return;
    }
    setIsModalOpen(false);
    // 重置表单和状态
    setTimeout(() => {
      setNewProjectName('');
      setNewProjectDesc('');
      setIsDeploying(false);
      setCurrentProjectId(null);
      setDeploymentData(null);
    }, 300);
  };

  // 渲染逻辑简化：直接读取 API 返回的 deploymentData
  const currentStep = getStepIndex(deploymentData?.creation_stage);
  const progress = deploymentData?.progress_percentage || 0;
  const analysisText = deploymentData?.analysis_result || '';
  const ddlText = deploymentData?.ddl_result || '';
  const logs = deploymentData?.deployment_logs || [];

  return (
    <div className="p-8 max-w-7xl mx-auto h-full overflow-y-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-2xl font-bold text-gray-800 tracking-tight">数据库项目</h2>
          <p className="text-gray-500 mt-1">管理您的 AI 驱动数据库实例 (Mock Mode: ON)</p>
        </div>
        <Button variant="primary" icon={<Plus size={16} />} onClick={() => setIsModalOpen(true)}>
          新建项目
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {projects.map(project => (
          <Card
            key={project.project_id}
            className="hover:shadow-lg transition-shadow cursor-pointer group border-gray-200"
            title={
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-blue-50 rounded-lg text-primary">
                  <Database size={20} />
                </div>
                <span className="font-semibold">{project.project_name}</span>
              </div>
            }
            extra={
              <Tag color={project.project_status === 'active' ? 'green' : 'orange'}>
                {project.project_status === 'active' ? '运行中' : '部署中'}
              </Tag>
            }
          >
            {/* 恢复点击事件，并在下方恢复按钮 */}
            <div className="space-y-4" onClick={() => onProjectSelect?.(project)}>
              <p className="text-gray-600 text-sm line-clamp-2 h-10 leading-relaxed">{project.description}</p>

              <div className="flex items-center justify-between text-xs text-gray-400 pt-4 border-t border-gray-50">
                <div className="flex items-center gap-1.5 bg-gray-50 px-2 py-1 rounded">
                  <Server size={12} /> {project.project_type}
                </div>
                <div className="flex items-center gap-1.5">
                  <Clock size={12} /> {new Date(project.created_at).toLocaleDateString()}
                </div>
              </div>

              {/* === 恢复的功能：进入工作台按钮 === */}
              <div className="flex justify-end pt-2 opacity-0 group-hover:opacity-100 transition-all duration-300 transform translate-y-2 group-hover:translate-y-0">
                <Button
                  variant="text"
                  className="text-primary text-xs hover:bg-blue-50 px-0"
                  onClick={(e) => {
                    e.stopPropagation(); // 防止重复触发
                    onProjectSelect?.(project);
                  }}
                >
                  进入工作台 <ArrowRight size={12} className="ml-1" />
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        title={!currentProjectId ? "创建新的数据库项目" : "自动化部署中心"}
        maxWidth={!currentProjectId ? 'max-w-md' : 'max-w-6xl'}
        footer={
          !currentProjectId ? (
            <>
              <Button onClick={handleCloseModal}>取消</Button>
              <Button variant="primary" onClick={handleCreateProject} icon={<PlayCircle size={16} />}>
                开始智能部署
              </Button>
            </>
          ) : deploymentData?.project_status === 'active' ? (
            <Button variant="primary" onClick={handleCloseModal} icon={<CheckCircle2 size={16} />}>
              完成并进入工作台
            </Button>
          ) : null
        }
      >
        {!currentProjectId ? (
          // === 表单视图 (未开始部署) ===
          <div className="space-y-6">
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-5 rounded-xl border border-blue-100 flex items-start gap-4">
              <div className="bg-white p-2 rounded-lg shadow-sm text-primary">
                <Sparkles size={24} />
              </div>
              <div className="text-sm text-blue-900">
                <p className="font-bold mb-1 text-base">AI 智能架构师</p>
                <p className="opacity-90 leading-relaxed">基于 Gemini 3.0 Pro 模型。只需用自然语言描述业务场景，系统将自动完成 3NF 范式建模、SQL 生成及环境部署。</p>
              </div>
            </div>

            <div className="space-y-4">
              <Input
                label="项目名称"
                placeholder="例如：企业级 CRM 客户管理系统"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
              />
              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-medium text-gray-700">数据库类型</label>
                <div className="grid grid-cols-2 gap-4">
                  {(['MySQL', 'PostgreSQL'] as const).map(type => (
                    <div
                      key={type}
                      onClick={() => setNewProjectType(type)}
                      className={`cursor-pointer px-4 py-3 rounded-lg border flex items-center gap-3 transition-all ${newProjectType === type
                          ? 'border-primary bg-blue-50 text-primary ring-1 ring-primary'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                        }`}
                    >
                      <Database size={18} className={newProjectType === type ? 'text-primary' : 'text-gray-400'} />
                      <span className="text-sm font-medium">{type === 'MySQL' ? 'MySQL 8.0' : 'PostgreSQL 14'}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-medium text-gray-700">业务场景描述</label>
                <textarea
                  className="px-4 py-3 bg-white border border-gray-300 rounded-lg text-sm focus:border-primary focus:ring-2 focus:ring-blue-100 transition-all h-32 resize-none leading-relaxed"
                  placeholder="请详细描述实体及关系..."
                  value={newProjectDesc}
                  onChange={(e) => setNewProjectDesc(e.target.value)}
                ></textarea>
              </div>
            </div>
          </div>
        ) : (
          // === 部署视图 (轮询 API 数据展示) ===
          <div className="flex flex-col h-[650px] -m-2">
            {/* Top: Progress Area */}
            <div className="mb-8 px-6 pt-2">
              <Steps steps={DEPLOYMENT_STEPS} current={currentStep} />
              <div className="mt-6 px-1">
                <ProgressBar progress={progress} />
              </div>
            </div>

            {/* Split Content Area */}
            <div className="flex-1 flex gap-6 min-h-0 px-2 pb-2">

              {/* Left: Schema Analysis */}
              <div className="flex-1 flex flex-col border border-gray-200 rounded-xl overflow-hidden shadow-sm bg-white">
                <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center gap-2.5">
                  <div className="p-1.5 bg-white rounded-md shadow-sm text-purple-600">
                    <BrainCircuit size={16} />
                  </div>
                  <span className="text-sm font-semibold text-gray-700">Schema 逻辑分析</span>
                </div>
                <div ref={analysisScrollRef} className="flex-1 p-5 overflow-y-auto text-sm leading-7 text-gray-700 font-sans prose prose-sm max-w-none">
                  {analysisText ? (
                    <div className="whitespace-pre-wrap">{analysisText}</div>
                  ) : (
                    <div className="h-full flex flex-col items-center justify-center text-gray-400 gap-2">
                      <Loader2 size={32} className="animate-spin opacity-20" />
                      <p>Waiting for API stream...</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Right: DDL Generation */}
              <div className="flex-1 flex flex-col border border-gray-800 rounded-xl overflow-hidden bg-[#1e1e1e] shadow-lg">
                <div className="bg-[#252526] px-4 py-3 border-b border-gray-700 flex items-center gap-2.5">
                  <div className="p-1.5 bg-gray-700 rounded-md text-blue-400">
                    <Code2 size={16} />
                  </div>
                  <span className="text-sm font-semibold text-gray-200">Generated DDL (SQL)</span>
                </div>
                <div ref={ddlScrollRef} className="flex-1 p-5 overflow-y-auto font-mono text-xs leading-6 bg-[#1e1e1e] text-[#d4d4d4]">
                  {ddlText ? (
                    <pre className="whitespace-pre-wrap"><code className="language-sql">{ddlText}</code></pre>
                  ) : (
                    <div className="h-full flex flex-col items-center justify-center text-gray-600 gap-2">
                      <Code2 size={32} className="opacity-20" />
                      <p>// Waiting for Schema lock...</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Bottom: Logs */}
            <div className="mt-4 mx-2 h-36 bg-black rounded-xl p-4 font-mono text-xs text-gray-300 overflow-y-auto shadow-inner border border-gray-800 relative">
              <div className="sticky top-0 left-0 bg-black/80 backdrop-blur-sm w-full pb-2 mb-2 border-b border-gray-800 flex items-center gap-2 text-gray-500 uppercase tracking-wider font-bold text-[10px]">
                <Terminal size={12} /> Deployment Logs (Remote)
              </div>
              <div className="space-y-1.5">
                {logs.map((log, i) => (
                  <div key={i} className="flex items-start gap-2 animate-in fade-in slide-in-from-left-2 duration-300">
                    <span className="text-gray-600 shrink-0">[{new Date().toLocaleTimeString()}]</span>
                    <span className={log.includes('❌') ? 'text-red-400 font-bold' : log.includes('✔') ? 'text-green-400 font-bold' : 'text-gray-300'}>
                      {log.replace('>>>', '').replace('✔', '').replace('❌', '')}
                    </span>
                  </div>
                ))}
                <div ref={logsEndRef} />
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};