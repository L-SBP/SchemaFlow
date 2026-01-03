/**
 * @file ProjectWizard.tsx
 * @module Components/Workflows/Project-Creation-Wizard
 * @description 数据库项目初始化向导核心组件。
 * 本组件采用分阶段状态机架构，驱动从自然语言需求到物理数据库部署的全生命周期。
 * * * 核心业务特性：
 * 1. 异步阶段流 (SF2): 深度集成 INITIALIZING -> SCHEMA -> DDL -> DEPLOY 的流水线；
 * 2. 人工介入审计 (SF3): 在关键节点提供文本编辑器，允许用户修正 AI 生成的逻辑偏差；
 * 3. 视觉进度欺骗 (UX Optimization): 采用渐进式异步增长算法，解决 AI 推理耗时不确定导致的白屏焦虑；
 * 4. 容灾恢复: 基于 localStorage 实现向导进度的断点续连。
 * * * 技术亮点：
 * - 双向同步 Ref 锁：解决 React 闭包陷阱导致的轮询状态回退问题；
 * - 动态 Footer 劫持：通过 Render Prop 模式实现模态框底部的动态上下文控制；
 * - 离屏 ER 图同步：在 Schema 变更时触发局部异步刷新。
 * * @author Wang Lirong (王利蓉)
 * @version 3.2.0
 * @date 2026-01-02
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ProjectDTO, CreationStageEnum, ProjectStatusEnum } from '../types';
import { getProjectDetail, generateDDL, deployProject, regenerateER } from '../api/project';
import { Button, ProgressBar } from './UI';
import { Loader2, CheckCircle2, AlertTriangle, FileJson, Code2, Play, RefreshCw } from 'lucide-react';
import { InteractiveERRenderer } from './InteractiveERRenderer';

/**
 * 严格定义向导阶段序列
 * @constant STAGE_ORDER
 * @description 用于实现状态单向增长逻辑，防止后端由于网络延迟返回旧状态导致的“页面回滚”现象。
 */
const STAGE_ORDER = [
  CreationStageEnum.INITIALIZING,
  CreationStageEnum.GENERATING_SCHEMA,
  CreationStageEnum.SCHEMA_GENERATED,
  CreationStageEnum.GENERATING_DDL,
  CreationStageEnum.DDL_GENERATED,
  CreationStageEnum.EXECUTING_DDL,
  CreationStageEnum.COMPLETED
];

/**
 * 获取阶段在序列中的索引位
 * @function getStageIndex
 */
const getStageIndex = (stage: CreationStageEnum | undefined | null): number => {
  if (!stage) return -1;
  return STAGE_ORDER.indexOf(stage);
};

/**
 * 项目向导组件属性定义
 * @interface ProjectWizardProps
 */
interface ProjectWizardProps {
  /** 目标项目的全局唯一识别码 */
  projectId: string | number;
  /** 全部阶段完成后触发的成功回调 */
  onComplete: () => void;
  /** 用户中途主动关闭向导的回调 */
  onClose: () => void;
  /** 只读模式标识：用于查看已完成项目的历史配置 */
  viewOnly?: boolean;
  /** 动态底部渲染函数：允许向导根据当前阶段向父级模态框“投影”操作按钮 */
  renderFooter?: (footer: React.ReactNode) => void;
}

/**
 * 文本内容语义化格式化工具
 * @function formatDisplayContent
 * @description 
 * 处理 AI 生成的原始字符串。支持：
 * 1. JSON 对象的结构化缩进排版；
 * 2. 字符串转义字符（\n, \"）的还原，提升人类阅读体验。
 */
const formatDisplayContent = (content: any) => {
  if (!content) return '';
  let str = content;

  // 类型分支：处理原生 JSON 对象
  if (typeof content !== 'string') {
    str = JSON.stringify(content, null, 2);
  } else {
    // 类型分支：尝试对 JSON 字符串执行二次美化
    try {
      const parsed = JSON.parse(content);
      str = JSON.stringify(parsed, null, 2);
    } catch (e) {
      // 容错：解析失败则判定为普通 DDL/SQL 文本，维持现状
    }
  }

  // 后处理：将技术转义符映射为物理表现字符
  return str.replace(/\\n/g, '\n').replace(/\\"/g, '"');
};

/**
 * 从多维 Schema 定义对象中提取核心逻辑描述
 * @function extractSchemaText
 */
const extractSchemaText = (schemaDefinition: any): string => {
  if (!schemaDefinition) return '';

  // 策略判定：优先提取字段中包含的 schema 核心代码块
  if (typeof schemaDefinition === 'object' && schemaDefinition.schema) {
    return formatDisplayContent(schemaDefinition.schema);
  }

  // 兜底策略：格式化全量元数据内容
  return formatDisplayContent(schemaDefinition);
};

/**
 * @component ProjectWizard
 * @description 
 * 向导主组件实现。通过 useEffect 驱动复杂的轮询逻辑与动画逻辑。
 */
export const ProjectWizard: React.FC<ProjectWizardProps> = ({ projectId, onComplete, onClose, viewOnly = false, renderFooter }) => {
  // --- 核心业务状态 ---
  const [project, setProject] = useState<ProjectDTO | null>(null);
  const [error, setError] = useState<string | null>(null);

  // --- 编辑态缓冲区 (Draft Buffer) ---
  /** 存储用户在 Schema 编辑区输入的文本，支持在确认前进行多轮微调 */
  const [editedSchema, setEditedSchema] = useState<string>('');
  /** 存储 AI 生成的 DDL 语句快照，作为最终部署前的审查底稿 */
  const [editedDDL, setEditedDDL] = useState<string>('');
  /** 存储向导执行过程中的额外增量需求 */
  const [requirements] = useState<string>('');
  /** 控制完成阶段视图下的 Tab 切换（概览/Schema/DDL） */
  const [activeTab, setActiveTab] = useState('概览');

  // --- 异步渲染状态监控 ---
  /** 标识 ER 图是否正处于 AI 重新生成的处理队列中 */
  const [isRegeneratingER, setIsRegeneratingER] = useState(false);
  /** 缓存本地已渲染的 ER 图代码，用于执行 DOM 局部刷新 */
  const [localERCode, setLocalERCode] = useState<string>('');
  /** 记录上一次成功的 ER 图快照，用于检测后端推送的数据是否产生实质变化 */
  const previousERCodeRef = useRef<string>('');

  // --- 策略控制状态 ---
  /** 控制 HTTP 轮询器的激活状态，在需要用户交互或操作已完成时进入休眠 */
  const [shouldPoll, setShouldPoll] = useState(true);

  // --- 视觉表现层状态 (UX Progress Engine) ---
  /** * @description 核心 UX 设计：
   * 实际的 AI 生成任务在后端执行，前端无法获取精确的百分比。
   * visualProgress 采用渐进式函数模拟“工作正在进行”的视觉反馈。
   */
  const [visualProgress, setVisualProgress] = useState(0);

  /** 持久化引用快照：用于在 Effect 销毁时将当前进度离线保存 */
  const progressSnapshotRef = useRef<{ stage: CreationStageEnum | null; progress: number }>({
    stage: null,
    progress: 0,
  });
  /** 恢复引用快照：记录从 localStorage 加载回来的历史进度 */
  const restoredSnapshotRef = useRef<{ stage: CreationStageEnum | null; progress: number } | null>(null);

  /** * @description 状态防护锁：
   * 存储最近一次感知到的阶段索引，防止轮询请求由于延迟导致的“状态倒流”。
   */
  const latestStageRef = useRef<number>(-1);

  /**
   * 业务轮询调度 Effect
   * 负责监控后端阶段转换，驱动向导界面的自动步进。
   */
  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null;

    const fetchProject = async () => {
      try {
        const data = await getProjectDetail(projectId);

        /**
         * 逻辑守卫：检测状态回退。
         * 如果当前获取的阶段在 STAGE_ORDER 中低于最新已确认阶段，则判定为过期请求并丢弃。
         */
        const currentStageIndex = getStageIndex(data.creation_stage);
        if (currentStageIndex < latestStageRef.current) {
          return;
        }

        // 更新最新阶段索引记录
        latestStageRef.current = currentStageIndex;
        setProject(data);

        /**
         * 步骤：状态缓冲区初始化。
         * 在数据到达且本地缓冲区为空时，将后端数据填充至编辑器。
         */
        if (!editedSchema && data.schema_definition) {
          setEditedSchema(extractSchemaText(data.schema_definition));
        }
        if (!editedDDL && data.ddl_statement) {
          setEditedDDL(formatDisplayContent(data.ddl_statement));
        }

        /**
         * 步骤：轮询状态机控制。
         * 判定当前阶段是否需要暂停轮询。
         * 情况 1：需要用户手动点击确认（SCHEMA_GENERATED/DDL_GENERATED）；
         * 情况 2：项目已完全激活（ACTIVE）。
         */
        const stage = data.creation_stage;
        if (!isRegeneratingER && (
          (stage === CreationStageEnum.SCHEMA_GENERATED && !!data.er_diagram_code) ||
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

    // 执行异步轮询逻辑
    if (!viewOnly && shouldPoll) {
      // 策略分支：常规任务 3s 一次，高频图形重绘 5s 一次以减轻服务器压力
      const pollInterval = isRegeneratingER ? 5000 : 3000;
      intervalId = setInterval(fetchProject, pollInterval);
    }

    // 清理逻辑：防止内存泄漏
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [projectId, viewOnly, shouldPoll, isRegeneratingER]);

  /** 状态快照实时同步 Effect */
  useEffect(() => {
    progressSnapshotRef.current = {
      stage: (project?.creation_stage ?? null) as CreationStageEnum | null,
      progress: visualProgress,
    };
  }, [project?.creation_stage, visualProgress]);

  /** * 离线进度恢复 Effect
   * 实现“刷新不丢失进度”的 UX 承诺。
   */
  useEffect(() => {
    if (viewOnly) return;

    const storageKey = `projectWizard.visualProgress.${projectId}`;
    try {
      const raw = localStorage.getItem(storageKey);
      if (raw) {
        const parsed = JSON.parse(raw) as { stage?: string; progress?: number };
        const stage = (parsed.stage ?? null) as CreationStageEnum | null;
        const progress = Number(parsed.progress);

        // 校验历史数据的有效性
        if (Number.isFinite(progress) && progress > 0) {
          const clamped = Math.max(0, Math.min(100, progress));
          restoredSnapshotRef.current = { stage, progress: clamped };
          setVisualProgress(clamped);
        }
      }
    } catch {
      // 静默处理存储异常
    }

    // 销毁前执行序列化存储
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

  /**
   * 视觉进度模拟算法引擎 (Visual Progress Engine)
   * @description 
   * 该算法基于 Asymptotic Growth (渐近增长) 逻辑：
   * 进度越接近目标阈值，单次增长步长越小。
   * 公式定义为：$$ \Delta P = \max(0.1, (P_{target} - P_{current}) \times 0.05) $$
   */
  useEffect(() => {
    if (!project || viewOnly) return;

    const stage = project.creation_stage || CreationStageEnum.INITIALIZING;
    let target = 0;

    // 分支判定：根据当前物理阶段设置视觉目标阈值
    switch (stage) {
      case CreationStageEnum.INITIALIZING:
      case CreationStageEnum.GENERATING_SCHEMA:
        target = 90; // 在后端生成期间，最高停留在 90%
        break;
      case CreationStageEnum.SCHEMA_GENERATED:
        target = 100; // 后端反馈生成完毕，视觉立即拉满
        break;
      case CreationStageEnum.GENERATING_DDL:
        target = 90;
        break;
      case CreationStageEnum.DDL_GENERATED:
        target = 100;
        break;
      case CreationStageEnum.EXECUTING_DDL:
        target = 95; // 物理执行阶段，由于涉及网络 IO 波动，最大设定为 95%
        break;
      case CreationStageEnum.COMPLETED:
        target = 100;
        break;
      default:
        target = 0;
    }

    // 断点续传优化：若当前阶段与缓存一致，则从缓存点继续动画
    const restored = restoredSnapshotRef.current;
    if (restored && restored.stage === stage && visualProgress < restored.progress) {
      setVisualProgress(restored.progress);
      return;
    }

    // 完成类阶段的即时响应逻辑
    const isCompletedStage = stage === CreationStageEnum.SCHEMA_GENERATED ||
      stage === CreationStageEnum.DDL_GENERATED ||
      stage === CreationStageEnum.COMPLETED;

    if (visualProgress === 0 && isCompletedStage && !restored) {
      setVisualProgress(100);
      return;
    }

    if (visualProgress >= target) return;

    /** 核心定时器：驱动进度条平滑增长 */
    const timer = setInterval(() => {
      setVisualProgress(prev => {
        if (prev >= target) return prev;
        const remaining = target - prev;
        const increment = Math.max(0.1, remaining * 0.05);
        return Math.min(target, prev + increment);
      });
    }, 100);

    return () => clearInterval(timer);
  }, [project?.creation_stage, viewOnly]);

  /** 进度重置策略 Effect */
  useEffect(() => {
    const currentStage = project?.creation_stage || CreationStageEnum.INITIALIZING;

    // 当跨入新的“生成类”阶段时，重置物理进度条
    if (currentStage === CreationStageEnum.GENERATING_SCHEMA ||
      currentStage === CreationStageEnum.GENERATING_DDL ||
      currentStage === CreationStageEnum.EXECUTING_DDL) {
      const restored = restoredSnapshotRef.current;
      if (restored && restored.stage === currentStage && restored.progress > 0) return;
      setVisualProgress(0);
    }

    // 流程完结，清理存储占用的资源
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

  /**
   * 业务动作：确认并提交 Schema
   * 触发从逻辑架构到 DDL 物理翻译的跃迁。
   */
  const handleConfirmSchema = useCallback(async () => {
    if (!project) return;
    try {
      restoredSnapshotRef.current = null;
      setShouldPoll(true);

      /**
       * 乐观更新 (Optimistic UI Update):
       * 在网络请求完成前，先行将 UI 切换至下一阶段的生成状态。
       */
      const nextStage = CreationStageEnum.GENERATING_DDL;
      latestStageRef.current = getStageIndex(nextStage);

      setProject(prev => prev ? { ...prev, creation_stage: nextStage } : null);
      setVisualProgress(0);

      // 发起异步业务请求
      await generateDDL(project.project_id, editedSchema, requirements);
    } catch (err) {
      console.error("Failed to confirm schema:", err);
      setError("确认 Schema 失败。");
    }
  }, [project, editedSchema, requirements]);

  /**
   * 业务动作：确认 DDL 并发起部署
   * 对应 SF1 自动化部署的核心触发点。
   */
  const handleConfirmDDL = useCallback(async () => {
    if (!project) return;
    try {
      restoredSnapshotRef.current = null;

      // 关键步骤：在部署这一敏感事务期间暂停背景轮询，防止乐观状态被服务器旧缓存覆盖
      setShouldPoll(false);

      const nextStage = CreationStageEnum.EXECUTING_DDL;
      latestStageRef.current = getStageIndex(nextStage);

      setProject(prev => prev ? { ...prev, creation_stage: nextStage } : null);
      setVisualProgress(0);

      // 执行物理部署
      const updatedProject = await deployProject(project.project_id, editedDDL);

      if (updatedProject) {
        const newStageIndex = getStageIndex(updatedProject.creation_stage);
        if (newStageIndex >= latestStageRef.current) {
          latestStageRef.current = newStageIndex;
          setProject(updatedProject);
        }
      }

      setShouldPoll(true);
    } catch (err) {
      console.error("Failed to deploy project:", err);
      setError("部署项目失败。");
      setShouldPoll(true);
    }
  }, [project, editedDDL]);

  /**
   * 业务动作：重新生成 ER 图可视化
   * 对应 SF5 可视化更新逻辑。
   */
  const handleRegenerateER = useCallback(async () => {
    if (!project || !editedSchema.trim()) return;

    // 保存前一个状态的副本
    previousERCodeRef.current = localERCode;

    setIsRegeneratingER(true);
    setError(null);
    setShouldPoll(true);

    try {
      await regenerateER(project.project_id, editedSchema);
    } catch (err) {
      console.error("Failed to regenerate ER:", err);
      setError("重新生成 ER 图失败。");
      setIsRegeneratingER(false);
    }
  }, [project, editedSchema, localERCode]);

  /**
   * ER 图数据感知 Effect
   * 监听后端推送的可视化 DSL 变化，并自动解除生成状态锁。
   */
  useEffect(() => {
    const newERCode = project?.er_diagram_code;
    if (!newERCode || newERCode === localERCode) return;

    // 若新代码已抵达且与旧代码不符，则判定重绘任务完成
    if (isRegeneratingER && newERCode !== previousERCodeRef.current) {
      setIsRegeneratingER(false);
      setShouldPoll(false);
    }

    setLocalERCode(newERCode);
    previousERCodeRef.current = newERCode;
  }, [project?.er_diagram_code]);

  /**
   * 底部操作栏渲染 Effect
   * @description 采用了“向下投影”模式：
   * 本组件将当前上下文的操作按钮实时回传给父级容器（通常是全局 Modal）。
   */
  useEffect(() => {
    if (!renderFooter || !project) {
      renderFooter?.(null);
      return;
    }

    const stage = viewOnly ? CreationStageEnum.COMPLETED : (project.creation_stage || CreationStageEnum.INITIALIZING);

    switch (stage) {
      case CreationStageEnum.SCHEMA_GENERATED:
        // 场景 A：Schema 已生成，提供修改与确认两个维度的动作
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
        // 场景 B：DDL 已准备就绪，仅提供最终部署确认
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
        // 场景 C：流程完结，提供应用入口
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
  }, [project?.creation_stage, viewOnly, isRegeneratingER, handleRegenerateER, handleConfirmSchema, handleConfirmDDL]);

  // --- 加载守卫 ---
  if (!project) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin" /></div>;

  /**
   * 渲染动态阶段内容
   * 根据当前向导状态返回特定的视图模块。
   */
  const renderStageContent = () => {
    const stage = viewOnly ? CreationStageEnum.COMPLETED : (project.creation_stage || CreationStageEnum.INITIALIZING);

    switch (stage) {
      /** 生成中：显示全局动画与虚拟进度 */
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

      /** 审计态：左右分布展示编辑器与可视化图形 */
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

            {/* 编辑与预览分屏布局 */}
            <div className="flex gap-4 h-[500px]">
              {/* 源码编辑区：支持手动干预 AI 逻辑偏差 */}
              <div className="flex-1 min-w-0 border rounded-md overflow-hidden">
                <textarea
                  className="w-full h-full p-4 font-mono text-sm resize-none focus:outline-none overflow-y-auto"
                  value={editedSchema}
                  onChange={(e) => setEditedSchema(e.target.value)}
                />
              </div>

              {/* 物理可视化预览区：基于 InteractiveERRenderer */}
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
                      <Loader2 className="w-12 h-12 animate-spin mx-auto text-blue-500 mb-2" />
                      <p>正在生成 ER 图...</p>
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

      /** DDL 审计态：展示最终生成的 SQL 脚本 */
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

      /** 完成态：展示全量概览与项目配置清单 */
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

            {/* 标签切换系统 */}
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
              {/* Tab: 可视化图表 */}
              {activeTab === '概览' && project?.er_diagram_code && project.er_diagram_code.trim() && (
                <div className="h-full border rounded-lg p-4 flex flex-col" style={{ overflow: 'hidden' }}>
                  <h4 className="font-medium mb-4 text-gray-700 shrink-0">ER 图</h4>
                  <InteractiveERRenderer chart={project.er_diagram_code} className="flex-1 min-h-0" />
                </div>
              )}

              {/* Tab: Schema 源码内容 */}
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

  /** * 渲染向导容器 
   * 实现统一的卡片布局与标题描述。
   */
  return (
    <div className="bg-white rounded-lg shadow-sm p-6 max-w-4xl mx-auto w-full flex flex-col">
      {/* 头部摘要信息区 */}
      <div className="mb-6 border-b pb-4 shrink-0">
        <h2 className="text-2xl font-bold text-gray-800">{project.project_name}</h2>
        <p className="text-gray-500">{project.description}</p>
      </div>

      {/* 错误提示浮窗 */}
      {error && (
        <div className="bg-red-50 text-red-600 p-4 rounded-md mb-6 flex items-center gap-2 shrink-0">
          <AlertTriangle className="w-5 h-5" />
          {error}
        </div>
      )}

      {/* 动态工作区 */}
      <div className="flex-1 min-h-0">
        {renderStageContent()}
      </div>
    </div>
  );
};