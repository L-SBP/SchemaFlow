import React, { useState, useEffect, useRef } from 'react';
import { ProjectDTO, CreationStageEnum, ProjectStatusEnum } from '../types';
import { getProjectDetail, generateDDL, deployProject, updateProject } from '../api/project';
import { Button, ProgressBar, Input } from './UI';
import { Loader2, CheckCircle2, AlertTriangle, FileJson, Database, Code2, Play } from 'lucide-react';
import mermaid from 'mermaid';

// Initialize mermaid
mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'loose',
});

interface ProjectWizardProps {
  projectId: string | number;
  onComplete: () => void;
  onClose: () => void;
  viewOnly?: boolean;
}

const MermaidChart: React.FC<{ chart: string; className?: string }> = ({ chart, className = '' }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const renderChart = async () => {
      if (containerRef.current && chart) {
        try {
          containerRef.current.innerHTML = '';
          const id = `mermaid-${Date.now()}`;
          const { svg } = await mermaid.render(id, chart);
          if (containerRef.current) {
            containerRef.current.innerHTML = svg;
          }
        } catch (error) {
          console.error('Mermaid render error:', error);
          if (containerRef.current) {
            containerRef.current.innerHTML = '<div class="text-red-500">无法渲染图表</div>';
          }
        }
      }
    };
    renderChart();
  }, [chart]);

  return <div ref={containerRef} className={`overflow-auto p-4 bg-white rounded border ${className}`} />;
};

const formatDisplayContent = (content: any) => {
  if (!content) return '';
  let str = content;

  // 如果是对象，先转为 JSON 字符串
  if (typeof content !== 'string') {
    str = JSON.stringify(content, null, 2);
  } else {
    // 如果是字符串，尝试解析为 JSON 对象再转回字符串（为了格式化）
    try {
      const parsed = JSON.parse(content);
      str = JSON.stringify(parsed, null, 2);
    } catch (e) {
      // 解析失败，说明是普通字符串（如 DDL），保持原样
    }
  }

  // 后处理：将字面量 \n 转换为实际换行符，将 \" 转换为 "，以提升可读性
  // 注意：这可能会导致生成的文本不再是有效的 JSON，但更适合人类阅读
  return str.replace(/\\n/g, '\n').replace(/\\"/g, '"');
};

export const ProjectWizard: React.FC<ProjectWizardProps> = ({ projectId, onComplete, onClose, viewOnly = false }) => {
  const [project, setProject] = useState<ProjectDTO | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Edit states
  const [editedSchema, setEditedSchema] = useState<string>('');
  const [editedDDL, setEditedDDL] = useState<string>('');
  const [requirements, setRequirements] = useState<string>('');
  const [activeTab, setActiveTab] = useState('概览');

  // Progress animation state
  const [visualProgress, setVisualProgress] = useState(0);

  // Polling
  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    const fetchProject = async () => {
      try {
        const data = await getProjectDetail(projectId);
        setProject(data);
        setLoading(false);

        // Initialize edit states if empty
        if (data.creation_stage === CreationStageEnum.SCHEMA_GENERATED && !editedSchema && data.schema_definition) {
          setEditedSchema(formatDisplayContent(data.schema_definition));
        }
        if (data.creation_stage === CreationStageEnum.DDL_GENERATED && !editedDDL && data.ddl_statement) {
          setEditedDDL(formatDisplayContent(data.ddl_statement));
        }

        // Stop polling if completed
        if (data.project_status === ProjectStatusEnum.ACTIVE) {
          // Continue polling? Maybe not.
        }
      } catch (err) {
        console.error("Failed to fetch project:", err);
        setError("无法加载项目详情。");
      }
    };

    fetchProject();
    if (!viewOnly) {
      intervalId = setInterval(fetchProject, 3000); // Poll every 3 seconds
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [projectId, editedSchema, editedDDL, viewOnly]);

  // Progress Bar Animation Logic
  useEffect(() => {
    if (!project || viewOnly) return;

    const stage = project.creation_stage;
    let target = 0;

    // Determine target based on stage
    switch (stage) {
      case CreationStageEnum.INITIALIZING:
      case CreationStageEnum.GENERATING_SCHEMA:
        target = 90; // Aim for 90% while generating
        break;
      case CreationStageEnum.SCHEMA_GENERATED:
        target = 100; // Completed this step
        break;
      case CreationStageEnum.GENERATING_DDL:
        target = 90;
        break;
      case CreationStageEnum.DDL_GENERATED:
        target = 100;
        break;
      case CreationStageEnum.EXECUTING_DDL:
        target = 95;
        break;
      case CreationStageEnum.COMPLETED:
        target = 100;
        break;
      default:
        target = 0;
    }

    // 修复：如果处于已完成阶段且进度为0（刚打开弹窗），直接显示100%，避免重新跑进度条
    if (visualProgress === 0 && (
      stage === CreationStageEnum.SCHEMA_GENERATED ||
      stage === CreationStageEnum.DDL_GENERATED ||
      stage === CreationStageEnum.COMPLETED
    )) {
      setVisualProgress(100);
      return;
    }

    const timer = setInterval(() => {
      setVisualProgress(prev => {
        if (prev >= target) return prev;

        // Calculate increment: smaller as we get closer to target
        const remaining = target - prev;
        const increment = Math.max(0.1, remaining * 0.05); // 5% of remaining distance

        return Math.min(target, prev + increment);
      });
    }, 100); // Update every 100ms

    return () => clearInterval(timer);
  }, [project?.creation_stage, viewOnly]);

  // Reset progress when entering a new "generating" stage
  useEffect(() => {
    if (project?.creation_stage === CreationStageEnum.GENERATING_SCHEMA ||
      project?.creation_stage === CreationStageEnum.GENERATING_DDL ||
      project?.creation_stage === CreationStageEnum.EXECUTING_DDL) {
      setVisualProgress(0);
    }
  }, [project?.creation_stage]);


  const handleConfirmSchema = async () => {
    if (!project) return;
    try {
      setLoading(true);
      setVisualProgress(0); // Reset progress for next stage

      // 乐观更新：立即切换到生成 DDL 状态，显示进度条
      setProject(prev => prev ? { ...prev, creation_stage: CreationStageEnum.GENERATING_DDL } : null);

      await generateDDL(project.project_id, editedSchema, requirements);
      // State update will happen on next poll
    } catch (err) {
      console.error("Failed to confirm schema:", err);
      setError("确认 Schema 失败。");
      setLoading(false);
    }
  };

  const handleConfirmDDL = async () => {
    if (!project) return;
    try {
      setLoading(true);
      setVisualProgress(0); // Reset progress for next stage

      // 乐观更新：立即切换到执行 DDL 状态，显示进度条
      setProject(prev => prev ? { ...prev, creation_stage: CreationStageEnum.EXECUTING_DDL } : null);

      await deployProject(project.project_id, editedDDL);
      // State update will happen on next poll
    } catch (err) {
      console.error("Failed to deploy project:", err);
      setError("部署项目失败。");
      setLoading(false);
    }
  };

  if (!project) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin" /></div>;

  const renderStageContent = () => {
    const stage = viewOnly ? CreationStageEnum.COMPLETED : project.creation_stage;

    // Common height for display areas
    const displayHeightClass = "h-[600px]";

    switch (stage) {
      case CreationStageEnum.INITIALIZING:
      case CreationStageEnum.GENERATING_SCHEMA:
        return (
          <div className="text-center py-12">
            <Loader2 className="w-12 h-12 animate-spin mx-auto text-blue-500 mb-4" />
            <h3 className="text-lg font-medium">正在生成 Schema...</h3>
            <p className="text-gray-500 mt-2">AI 正在分析您的需求并设计数据库 Schema。</p>
            <div className="mt-6 max-w-md mx-auto">
              <ProgressBar progress={visualProgress} />
            </div>
          </div>
        );

      case CreationStageEnum.SCHEMA_GENERATED:
        return (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium flex items-center gap-2">
                <FileJson className="w-5 h-5 text-blue-500" />
                审查 Schema
              </h3>
              <span className="text-sm text-gray-500">请审查并在需要时修改生成的 Schema。</span>
            </div>

            <div className={`${displayHeightClass} border rounded-md overflow-hidden`}>
              <textarea
                className="w-full h-full p-4 font-mono text-sm resize-none focus:outline-none"
                value={editedSchema}
                onChange={(e) => setEditedSchema(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">额外需求 (可选)</label>
              <Input
                value={requirements}
                onChange={(e) => setRequirements(e.target.value)}
                placeholder="例如：在用户邮箱上添加索引..."
              />
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <Button variant="default" onClick={onClose}>取消</Button>
              <Button onClick={handleConfirmSchema} className="bg-blue-600 hover:bg-blue-700 text-white">
                确认并生成 DDL
              </Button>
            </div>
          </div>
        );

      case CreationStageEnum.GENERATING_DDL:
        return (
          <div className="text-center py-12">
            <Loader2 className="w-12 h-12 animate-spin mx-auto text-purple-500 mb-4" />
            <h3 className="text-lg font-medium">正在生成 DDL...</h3>
            <p className="text-gray-500 mt-2">正在将 Schema 转换为 {project.db_type} 的 SQL 语句。</p>
            <div className="mt-6 max-w-md mx-auto">
              <ProgressBar progress={visualProgress} />
            </div>
          </div>
        );

      case CreationStageEnum.DDL_GENERATED:
        return (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium flex items-center gap-2">
                <Code2 className="w-5 h-5 text-purple-500" />
                审查 DDL
              </h3>
              <span className="text-sm text-gray-500">请在部署前审查 SQL 语句。</span>
            </div>

            <div className={`${displayHeightClass} border rounded-md overflow-hidden bg-gray-50`}>
              <textarea
                className="w-full h-full p-4 font-mono text-sm resize-none focus:outline-none bg-transparent"
                value={editedDDL}
                onChange={(e) => setEditedDDL(e.target.value)}
              />
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <Button variant="default" onClick={onClose}>取消</Button>
              <Button onClick={handleConfirmDDL} className="bg-blue-600 hover:bg-blue-700 text-white">
                <Play className="w-4 h-4 mr-2" />
                部署项目
              </Button>
            </div>
          </div>
        );

      case CreationStageEnum.EXECUTING_DDL:
        return (
          <div className="text-center py-12">
            <Loader2 className="w-12 h-12 animate-spin mx-auto text-green-500 mb-4" />
            <h3 className="text-lg font-medium">正在部署数据库...</h3>
            <p className="text-gray-500 mt-2">正在执行 SQL 语句并初始化数据库。</p>
            <div className="mt-6 max-w-md mx-auto">
              <ProgressBar progress={visualProgress} />
            </div>
          </div>
        );

      case CreationStageEnum.COMPLETED:
        return (
          <div className="space-y-6">
            {!viewOnly && (
              <div className="text-center py-6 bg-green-50 rounded-lg border border-green-100">
                <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto mb-2" />
                <h3 className="text-xl font-bold text-green-800">项目部署成功！</h3>
                <p className="text-green-600">您的数据库已准备就绪。</p>
              </div>
            )}

            {/* Tabs */}
            <div className="border-b border-gray-200">
              <nav className="-mb-px flex space-x-8">
                {['概览', 'Schema', 'DDL'].map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`${activeTab === tab
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
                  >
                    {tab}
                  </button>
                ))}
              </nav>
            </div>

            <div className={`${displayHeightClass} w-full`}>
              {activeTab === '概览' && project.er_diagram_code && (
                <div className="h-full border rounded-lg p-4 overflow-hidden flex flex-col">
                  <h4 className="font-medium mb-4 text-gray-700 shrink-0">ER 图</h4>
                  <MermaidChart chart={project.er_diagram_code} className="flex-1 min-h-0" />
                </div>
              )}

              {activeTab === 'Schema' && (
                <div className="h-full border rounded-md overflow-hidden bg-gray-50">
                  <textarea
                    readOnly
                    className="w-full h-full p-4 font-mono text-sm resize-none focus:outline-none bg-transparent"
                    value={project.schema_definition ? formatDisplayContent(project.schema_definition) : ''}
                  />
                </div>
              )}

              {activeTab === 'DDL' && (
                <div className="h-full border rounded-md overflow-hidden bg-gray-50">
                  <textarea
                    readOnly
                    className="w-full h-full p-4 font-mono text-sm resize-none focus:outline-none bg-transparent"
                    value={project.ddl_statement ? formatDisplayContent(project.ddl_statement) : ''}
                  />
                </div>
              )}
            </div>

            {
              !viewOnly && (
                <div className="flex justify-center pt-4">
                  <Button onClick={onComplete} className="bg-blue-600 hover:bg-blue-700 text-white">
                    进入工作台
                  </Button>
                </div>
              )
            }
          </div >
        );

      default:
        return <div className="text-red-500">未知阶段: {project.creation_stage}</div>;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 max-w-4xl mx-auto w-full">
      <div className="mb-6 border-b pb-4">
        <h2 className="text-2xl font-bold text-gray-800">{project.project_name}</h2>
        <p className="text-gray-500">{project.description}</p>
      </div>

      {error && (
        <div className="bg-red-50 text-red-600 p-4 rounded-md mb-6 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" />
          {error}
        </div>
      )}

      {renderStageContent()}
    </div>
  );
};
