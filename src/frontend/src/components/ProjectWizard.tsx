import React, { useState, useEffect, useRef } from 'react';
import { ProjectDTO, CreationStageEnum, ProjectStatusEnum } from '../types';
import { getProjectDetail, generateDDL, deployProject } from '../api/project';
import { Button, ProgressBar } from './UI';
import { Loader2, CheckCircle2, AlertTriangle, FileJson, Code2, Play } from 'lucide-react';
import { InteractiveERRenderer } from './InteractiveERRenderer';

interface ProjectWizardProps {
  projectId: string | number;
  onComplete: () => void;
  onClose: () => void;
  viewOnly?: boolean;
}

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
  const [error, setError] = useState<string | null>(null);

  // Edit states
  const [editedSchema, setEditedSchema] = useState<string>('');
  const [editedDDL, setEditedDDL] = useState<string>('');
  const [requirements] = useState<string>('');
  const [activeTab, setActiveTab] = useState('概览');

  // Progress animation state
  const [visualProgress, setVisualProgress] = useState(0);

  const progressSnapshotRef = useRef<{ stage: CreationStageEnum | null; progress: number }>({
    stage: null,
    progress: 0,
  });
  const restoredSnapshotRef = useRef<{ stage: CreationStageEnum | null; progress: number } | null>(null);

  // Polling
  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    const fetchProject = async () => {
      try {
        const data = await getProjectDetail(projectId);
        setProject(data);

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

  useEffect(() => {
    progressSnapshotRef.current = {
      stage: (project?.creation_stage ?? null) as CreationStageEnum | null,
      progress: visualProgress,
    };
  }, [project?.creation_stage, visualProgress]);

  useEffect(() => {
    if (viewOnly) return;

    const storageKey = `projectWizard.visualProgress.${projectId}`;
    try {
      const raw = localStorage.getItem(storageKey);
      if (raw) {
        const parsed = JSON.parse(raw) as { stage?: string; progress?: number };
        const stage = (parsed.stage ?? null) as CreationStageEnum | null;
        const progress = Number(parsed.progress);
        if (Number.isFinite(progress) && progress > 0) {
          const clamped = Math.max(0, Math.min(100, progress));
          restoredSnapshotRef.current = { stage, progress: clamped };
          setVisualProgress(clamped);
        }
      }
    } catch {
      // ignore
    }

    return () => {
      try {
        const snapshot = progressSnapshotRef.current;
        if (!snapshot.stage) return;
        localStorage.setItem(storageKey, JSON.stringify({ stage: snapshot.stage, progress: snapshot.progress }));
      } catch {
        // ignore
      }
    };
  }, [projectId, viewOnly]);

  // Progress Bar Animation Logic
  useEffect(() => {
    if (!project || viewOnly) return;

    const stage = project.creation_stage || CreationStageEnum.INITIALIZING;
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

    // 如果是同一阶段从弹窗关闭后恢复，尽量从上次的进度继续增长（不从 0 重来）
    if (
      restoredSnapshotRef.current &&
      restoredSnapshotRef.current.stage === stage &&
      visualProgress < restoredSnapshotRef.current.progress
    ) {
      setVisualProgress(restoredSnapshotRef.current.progress);
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
    const currentStage = project?.creation_stage || CreationStageEnum.INITIALIZING;

    if (currentStage === CreationStageEnum.GENERATING_SCHEMA ||
      currentStage === CreationStageEnum.GENERATING_DDL ||
      currentStage === CreationStageEnum.EXECUTING_DDL) {
      const restored = restoredSnapshotRef.current;
      if (restored && restored.stage === currentStage && restored.progress > 0) return;
      setVisualProgress(0);
    }

    if (currentStage === CreationStageEnum.COMPLETED) {
      restoredSnapshotRef.current = null;
      if (!viewOnly) {
        try {
          localStorage.removeItem(`projectWizard.visualProgress.${projectId}`);
        } catch {
          // ignore
        }
      }
    }
  }, [project?.creation_stage]);


  const handleConfirmSchema = async () => {
    if (!project) return;
    try {
      setVisualProgress(0); // Reset progress for next stage

      // 乐观更新：立即切换到生成 DDL 状态，显示进度条
      setProject(prev => prev ? { ...prev, creation_stage: CreationStageEnum.GENERATING_DDL } : null);

      await generateDDL(project.project_id, editedSchema, requirements);
      // State update will happen on next poll
    } catch (err) {
      console.error("Failed to confirm schema:", err);
      setError("确认 Schema 失败。");
    }
  };

  const handleConfirmDDL = async () => {
    if (!project) return;
    try {
      setVisualProgress(0); // Reset progress for next stage

      // 乐观更新：立即切换到执行 DDL 状态，显示进度条
      setProject(prev => prev ? { ...prev, creation_stage: CreationStageEnum.EXECUTING_DDL } : null);

      await deployProject(project.project_id, editedDDL);
      // State update will happen on next poll
    } catch (err) {
      console.error("Failed to deploy project:", err);
      setError("部署项目失败。");
    }
  };

  if (!project) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin" /></div>;

  const renderStageContent = () => {
    const stage = viewOnly ? CreationStageEnum.COMPLETED : (project.creation_stage || CreationStageEnum.INITIALIZING);

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

            <div className={`${displayHeightClass} border rounded-md overflow-y-auto`}>
              <textarea
                className="w-full h-full p-4 font-mono text-sm resize-none focus:outline-none"
                value={editedSchema}
                onChange={(e) => setEditedSchema(e.target.value)}
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

            <div className={`${displayHeightClass} border rounded-md overflow-y-auto bg-gray-50`}>
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
              {activeTab === '概览' && project?.er_diagram_code && project.er_diagram_code.trim() && (
                <div className="h-full border rounded-lg p-4 flex flex-col" style={{ overflow: 'hidden' }}>
                  <h4 className="font-medium mb-4 text-gray-700 shrink-0">ER 图</h4>
                  <InteractiveERRenderer chart={project.er_diagram_code} className="flex-1 min-h-0" />
                </div>
              )}

              {activeTab === '概览' && (!project?.er_diagram_code || !project.er_diagram_code.trim()) && (
                <div className="h-full border rounded-lg p-4 flex flex-col" style={{ overflow: 'hidden' }}>
                  <h4 className="font-medium mb-4 text-gray-700 shrink-0">ER 图</h4>
                  <div className="flex-1 flex items-center justify-center text-gray-500">
                    <div className="text-center">
                      <p className="mb-2">ER 图不可用</p>
                      <p className="text-sm">暂无可用的 ER 图数据</p>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'Schema' && (
                <div className="h-full border rounded-md bg-gray-50 overflow-y-auto">
                  <div
                    className="w-full p-4 font-mono text-sm bg-transparent whitespace-pre-wrap"
                    style={{
                      wordBreak: 'break-word',
                      lineHeight: '1.5'
                    }}
                  >
                    {project.schema_definition ? formatDisplayContent(project.schema_definition) : ''}
                  </div>
                </div>
              )}

              {activeTab === 'DDL' && (
                <div className="h-full border rounded-md bg-gray-50 overflow-y-auto">
                  <div
                    className="w-full p-4 font-mono text-sm bg-transparent whitespace-pre-wrap"
                    style={{
                      wordBreak: 'break-word',
                      lineHeight: '1.5'
                    }}
                  >
                    {project.ddl_statement ? formatDisplayContent(project.ddl_statement) : ''}
                  </div>
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
        return <div className="text-red-500">未知阶段: {project.creation_stage || 'undefined'}</div>;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 max-w-4xl mx-auto w-full" style={{ overflow: 'hidden' }}>
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

      <div style={{ overflow: 'hidden' }}>
        {renderStageContent()}
      </div>
    </div>
  );
};
