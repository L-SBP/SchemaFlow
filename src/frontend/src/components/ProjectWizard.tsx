import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ProjectDTO, CreationStageEnum, ProjectStatusEnum } from '../types';
import { getProjectDetail, generateDDL, deployProject, regenerateER } from '../api/project';
import { Button, ProgressBar } from './UI';
import { Loader2, CheckCircle2, AlertTriangle, FileJson, Code2, Play, RefreshCw } from 'lucide-react';
import { InteractiveERRenderer } from './InteractiveERRenderer';

// 定义阶段顺序，用于防止状态回退
const STAGE_ORDER = [
  CreationStageEnum.INITIALIZING,
  CreationStageEnum.GENERATING_SCHEMA,
  CreationStageEnum.SCHEMA_GENERATED,
  CreationStageEnum.GENERATING_DDL,
  CreationStageEnum.DDL_GENERATED,
  CreationStageEnum.EXECUTING_DDL,
  CreationStageEnum.COMPLETED
];

const getStageIndex = (stage: CreationStageEnum | undefined | null): number => {
  if (!stage) return -1;
  return STAGE_ORDER.indexOf(stage);
};

interface ProjectWizardProps {
  projectId: string | number;
  onComplete: () => void;
  onClose: () => void;
  viewOnly?: boolean;
  renderFooter?: (footer: React.ReactNode) => void;
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

// 从 schema_definition 对象中提取 schema 文本
const extractSchemaText = (schemaDefinition: any): string => {
  if (!schemaDefinition) return '';

  // 如果是对象且有 schema 字段，提取它
  if (typeof schemaDefinition === 'object' && schemaDefinition.schema) {
    return formatDisplayContent(schemaDefinition.schema);
  }

  // 否则格式化整个内容
  return formatDisplayContent(schemaDefinition);
};

export const ProjectWizard: React.FC<ProjectWizardProps> = ({ projectId, onComplete, onClose, viewOnly = false, renderFooter }) => {
  const [project, setProject] = useState<ProjectDTO | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Edit states
  const [editedSchema, setEditedSchema] = useState<string>('');
  const [editedDDL, setEditedDDL] = useState<string>('');
  const [requirements] = useState<string>('');
  const [activeTab, setActiveTab] = useState('概览');

  // ER 图重新生成状态
  const [isRegeneratingER, setIsRegeneratingER] = useState(false);
  const [localERCode, setLocalERCode] = useState<string>('');
  const previousERCodeRef = useRef<string>('');

  // 轮询控制状态
  const [shouldPoll, setShouldPoll] = useState(true);

  // Progress animation state
  const [visualProgress, setVisualProgress] = useState(0);

  const progressSnapshotRef = useRef<{ stage: CreationStageEnum | null; progress: number }>({
    stage: null,
    progress: 0,
  });
  const restoredSnapshotRef = useRef<{ stage: CreationStageEnum | null; progress: number } | null>(null);

  // Track the latest stage index to prevent regression
  const latestStageRef = useRef<number>(-1);

  // Polling
  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null;

    const fetchProject = async () => {
      try {
        const data = await getProjectDetail(projectId);

        // Prevent stage regression (e.g. polling returns old status after optimistic update)
        const currentStageIndex = getStageIndex(data.creation_stage);
        if (currentStageIndex < latestStageRef.current) {
          return;
        }

        latestStageRef.current = currentStageIndex;
        setProject(data);

        // Initialize edit states if empty - 在任何需要显示的阶段都初始化数据
        // Schema: 在 SCHEMA_GENERATED, GENERATING_DDL, DDL_GENERATED 等阶段都需要
        if (!editedSchema && data.schema_definition) {
          setEditedSchema(extractSchemaText(data.schema_definition));
        }
        // DDL: 在 DDL_GENERATED, EXECUTING_DDL, COMPLETED 等阶段需要
        if (!editedDDL && data.ddl_statement) {
          setEditedDDL(formatDisplayContent(data.ddl_statement));
        }

        // 在需要用户操作的阶段停止轮询
        const stage = data.creation_stage;
        // 在用户需要操作的阶段停止轮询（除非正在重新生成 ER 图）
        if (!isRegeneratingER && (
          stage === CreationStageEnum.SCHEMA_GENERATED ||
          stage === CreationStageEnum.DDL_GENERATED ||
          stage === CreationStageEnum.COMPLETED ||
          data.project_status === ProjectStatusEnum.ACTIVE)) {
          setShouldPoll(false);
        }
      } catch (err) {
        console.error("Failed to fetch project:", err);
        setError("无法加载项目详情。");
      }
    };

    fetchProject();
    if (!viewOnly && shouldPoll) {
      // 重新生成 ER 图时使用较低的轮询频率（5秒），其他情况使用正常频率（3秒）
      const pollInterval = isRegeneratingER ? 5000 : 3000;
      intervalId = setInterval(fetchProject, pollInterval);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [projectId, viewOnly, shouldPoll, isRegeneratingER]);

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
    const restored = restoredSnapshotRef.current;
    if (restored && restored.stage === stage && visualProgress < restored.progress) {
      setVisualProgress(restored.progress);
      return; // 避免立即启动 timer
    }

    // 对于"已完成"类型的阶段（非生成中），如果进度为0且没有恢复快照，直接显示100%
    // 这是为了处理刚打开弹窗时的情况
    const isCompletedStage = stage === CreationStageEnum.SCHEMA_GENERATED ||
      stage === CreationStageEnum.DDL_GENERATED ||
      stage === CreationStageEnum.COMPLETED;

    if (visualProgress === 0 && isCompletedStage && !restored) {
      setVisualProgress(100);
      return;
    }

    // 如果已经达到目标，不启动 timer
    if (visualProgress >= target) return;

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
    // eslint-disable-next-line react-hooks/exhaustive-deps
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


  const handleConfirmSchema = useCallback(async () => {
    if (!project) return;
    try {
      // 清除恢复快照，确保进度从0开始
      restoredSnapshotRef.current = null;
      setShouldPoll(true); // 重新开启轮询

      // 乐观更新：立即切换到生成 DDL 状态，显示进度条
      // 注意：先更新 project 状态，再重置进度，避免进度条动画逻辑的干扰
      const nextStage = CreationStageEnum.GENERATING_DDL;
      latestStageRef.current = getStageIndex(nextStage);

      setProject(prev => prev ? { ...prev, creation_stage: nextStage } : null);
      setVisualProgress(0); // Reset progress for next stage

      await generateDDL(project.project_id, editedSchema, requirements);
      // State update will happen on next poll
    } catch (err) {
      console.error("Failed to confirm schema:", err);
      setError("确认 Schema 失败。");
    }
  }, [project, editedSchema, requirements]);

  const handleConfirmDDL = useCallback(async () => {
    if (!project) return;
    try {
      // 清除恢复快照，确保进度从0开始
      restoredSnapshotRef.current = null;

      // 关键修改 1: 部署期间暂停轮询，防止状态跳变
      setShouldPoll(false);

      // 乐观更新：立即切换到执行 DDL 状态，显示进度条
      const nextStage = CreationStageEnum.EXECUTING_DDL;
      latestStageRef.current = getStageIndex(nextStage);

      setProject(prev => prev ? { ...prev, creation_stage: nextStage } : null);
      setVisualProgress(0); // Reset progress for next stage

      // 关键修改 2: 获取返回值并直接更新状态
      const updatedProject = await deployProject(project.project_id, editedDDL);

      if (updatedProject) {
        const newStageIndex = getStageIndex(updatedProject.creation_stage);
        if (newStageIndex >= latestStageRef.current) {
          latestStageRef.current = newStageIndex;
          setProject(updatedProject);
        }
      }

      // 部署完成后再恢复轮询
      setShouldPoll(true);
    } catch (err) {
      console.error("Failed to deploy project:", err);
      setError("部署项目失败。");
      setShouldPoll(true); // 出错时恢复轮询
    }
  }, [project, editedDDL]);

  // 重新生成 ER 图
  const handleRegenerateER = useCallback(async () => {
    if (!project || !editedSchema.trim()) return;

    // 记录当前 ER 图代码，用于检测更新
    previousERCodeRef.current = localERCode;

    setIsRegeneratingER(true);
    setError(null);
    setShouldPoll(true); // 开启轮询等待 ER 图更新

    try {
      await regenerateER(project.project_id, editedSchema);
      // ER 图会在后台生成，通过轮询获取最新数据
    } catch (err) {
      console.error("Failed to regenerate ER:", err);
      setError("重新生成 ER 图失败。");
      setIsRegeneratingER(false);
    }
  }, [project, editedSchema, localERCode]);

  // 当 project 更新时，同步更新本地 ER 图代码
  useEffect(() => {
    const newERCode = project?.er_diagram_code;
    if (!newERCode || newERCode === localERCode) return;

    // 如果正在重新生成 ER 图，检测 ER 图是否真的更新了
    if (isRegeneratingER && newERCode !== previousERCodeRef.current) {
      setIsRegeneratingER(false);
      setShouldPoll(false);
    }

    // 更新本地 ER 图代码
    setLocalERCode(newERCode);
    // 更新 ref
    previousERCodeRef.current = newERCode;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [project?.er_diagram_code]);

  // 根据当前阶段更新 footer 内容
  useEffect(() => {
    if (!renderFooter || !project) {
      renderFooter?.(null);
      return;
    }

    const stage = viewOnly ? CreationStageEnum.COMPLETED : (project.creation_stage || CreationStageEnum.INITIALIZING);

    switch (stage) {
      case CreationStageEnum.SCHEMA_GENERATED:
        renderFooter(
          <div className="flex justify-between items-center w-full">
            <Button
              variant="default"
              onClick={handleRegenerateER}
              disabled={isRegeneratingER}
              icon={isRegeneratingER ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            >
              {isRegeneratingER ? '生成中...' : '修改'}
            </Button>
            <div className="flex gap-2 sm:gap-3">
              <Button variant="default" onClick={onClose}>取消</Button>
              <Button onClick={handleConfirmSchema} className="bg-blue-600 hover:bg-blue-700 text-white">
                确认并生成 DDL
              </Button>
            </div>
          </div>
        );
        break;
      case CreationStageEnum.DDL_GENERATED:
        renderFooter(
          <>
            <Button variant="default" onClick={onClose}>取消</Button>
            <Button onClick={handleConfirmDDL} className="bg-blue-600 hover:bg-blue-700 text-white">
              <Play className="w-4 h-4 mr-2" />
              部署项目
            </Button>
          </>
        );
        break;
      case CreationStageEnum.COMPLETED:
        if (!viewOnly) {
          renderFooter(
            <Button onClick={onComplete} className="bg-blue-600 hover:bg-blue-700 text-white">
              进入工作台
            </Button>
          );
        } else {
          renderFooter(null);
        }
        break;
      default:
        renderFooter(null);
        break;
    }
    // 注意：这里故意省略部分依赖项以避免无限循环
    // renderFooter, onClose, onComplete 是 props 函数，可能每次渲染都是新引用
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [project?.creation_stage, viewOnly, isRegeneratingER, handleRegenerateER, handleConfirmSchema, handleConfirmDDL]);

  if (!project) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin" /></div>;

  const renderStageContent = () => {
    const stage = viewOnly ? CreationStageEnum.COMPLETED : (project.creation_stage || CreationStageEnum.INITIALIZING);

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
          <div className="flex flex-col">
            <div className="flex justify-between items-center mb-4 shrink-0">
              <h3 className="text-lg font-medium flex items-center gap-2">
                <FileJson className="w-5 h-5 text-blue-500" />
                审查 Schema 与 ER 图
              </h3>
              <span className="text-sm text-gray-500">请审查并在需要时修改生成的 Schema，点击"修改"更新 ER 图。</span>
            </div>

            <div className="flex gap-4 h-[500px]">
              {/* 左侧：Schema 编辑区 */}
              <div className="flex-1 min-w-0 border rounded-md overflow-hidden">
                <textarea
                  className="w-full h-full p-4 font-mono text-sm resize-none focus:outline-none overflow-y-auto"
                  value={editedSchema}
                  onChange={(e) => setEditedSchema(e.target.value)}
                />
              </div>

              {/* 右侧：ER 图预览区 */}
              <div className="flex-1 min-w-0 border rounded-md overflow-hidden bg-gray-50 relative">
                {isRegeneratingER && (
                  <div className="absolute inset-0 bg-white/80 flex items-center justify-center z-10">
                    <div className="text-center">
                      <Loader2 className="w-8 h-8 animate-spin mx-auto text-blue-500 mb-2" />
                      <p className="text-sm text-gray-600">正在重新生成 ER 图...</p>
                    </div>
                  </div>
                )}
                {localERCode && localERCode.trim() ? (
                  <div className="h-full" style={{ touchAction: 'none' }}>
                    <InteractiveERRenderer chart={localERCode} className="h-full" />
                  </div>
                ) : (
                  <div className="h-full flex items-center justify-center text-gray-400">
                    <div className="text-center">
                      <FileJson className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p>ER 图预览</p>
                      <p className="text-sm">点击"确认修改"生成 ER 图</p>
                    </div>
                  </div>
                )}
              </div>
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
          <div className="flex flex-col">
            <div className="flex justify-between items-center mb-4 shrink-0">
              <h3 className="text-lg font-medium flex items-center gap-2">
                <Code2 className="w-5 h-5 text-purple-500" />
                查看 DDL
              </h3>
              <span className="text-sm text-gray-500"></span>
            </div>

            <div className="h-[500px] border rounded-md overflow-y-auto bg-gray-50">
              <pre className="w-full p-4 font-mono text-sm whitespace-pre-wrap" style={{ wordBreak: 'break-word' }}>
                {editedDDL}
              </pre>
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
          <div className="flex flex-col">
            {!viewOnly && (
              <div className="text-center py-6 bg-green-50 rounded-lg border border-green-100 mb-6 shrink-0">
                <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto mb-2" />
                <h3 className="text-xl font-bold text-green-800">项目部署成功！</h3>
                <p className="text-green-600">您的数据库已准备就绪。</p>
              </div>
            )}

            {/* Tabs */}
            <div className="border-b border-gray-200 shrink-0">
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

            <div className="h-[500px] w-full mt-6">
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
                    {project.schema_definition ? extractSchemaText(project.schema_definition) : ''}
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
          </div>
        );

      default:
        return <div className="text-red-500">未知阶段: {project.creation_stage || 'undefined'}</div>;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 max-w-4xl mx-auto w-full flex flex-col">
      <div className="mb-6 border-b pb-4 shrink-0">
        <h2 className="text-2xl font-bold text-gray-800">{project.project_name}</h2>
        <p className="text-gray-500">{project.description}</p>
      </div>

      {error && (
        <div className="bg-red-50 text-red-600 p-4 rounded-md mb-6 flex items-center gap-2 shrink-0">
          <AlertTriangle className="w-5 h-5" />
          {error}
        </div>
      )}

      <div className="flex-1 min-h-0">
        {renderStageContent()}
      </div>
    </div>
  );
};
