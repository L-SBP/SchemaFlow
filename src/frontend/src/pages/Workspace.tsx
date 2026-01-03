import React, { useState, useRef, useEffect } from 'react';
import { Project, Message, QueryResult, ChatSession, ChatResponse, AIModelOption } from '../types';
import { Button, message as GlobalMessage, Modal, ConfirmDialog } from '../components/UI';
import { Send, Plus, MessageSquare, Edit2, Trash2, Check, X, ChevronLeft, Loader2, Sparkles, AlertTriangle, Play, Ban, Table as TableIcon, Info, Bot, Database } from 'lucide-react';
import { sessionApi } from '../api/session';
import { ProjectWizard } from '../components/ProjectWizard';
import { PanelToggleButton } from '../components/PanelToggleButton';
import DatabaseViewer from './DatabaseViewer';
import { useGlobalZoomLevel } from '../utils/globalZoomLevel';
import { useViewportWidth } from '../hooks/useViewportWidth';

interface WorkspaceProps {
  project: Project;
  onBack: () => void;
}

// --- 组件: 打字机效果 ---
// 用于模拟 AI 输出时的流式阅读体验
const Typewriter: React.FC<{ text: string; onComplete?: () => void }> = ({ text, onComplete }) => {
  const [displayedText, setDisplayedText] = useState('');
  const indexRef = useRef(0);

  useEffect(() => {
    // 重置状态
    indexRef.current = 0;
    setDisplayedText('');

    if (!text) {
      onComplete?.();
      return;
    }

    const intervalId = setInterval(() => {
      if (indexRef.current < text.length) {
        setDisplayedText((prev) => prev + text.charAt(indexRef.current));
        indexRef.current++;
      } else {
        clearInterval(intervalId);
        onComplete?.();
      }
    }, 15); // 打字速度：15ms/字

    return () => clearInterval(intervalId);
  }, [text]); // 依赖 text 变化

  // 使用 whitespace-pre-wrap 保持换行
  return <span className="whitespace-pre-wrap leading-relaxed">{displayedText}</span>;
};

// --- 组件: 模型选择器 ---
// 自定义下拉选择器，用于选择 AI 模型
interface ModelSelectorProps {
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
  isMobile: boolean;
}

const ModelSelector: React.FC<ModelSelectorProps> = ({ value, onChange, options, isMobile }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [menuPosition, setMenuPosition] = useState({ bottom: 0, left: 0 });
  const selectorRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // 点击外部关闭下拉菜单
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (selectorRef.current && !selectorRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // 计算下拉菜单位置
  const handleToggle = () => {
    if (!isOpen && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      setMenuPosition({
        bottom: window.innerHeight - rect.top + 4,
        left: rect.left
      });
    }
    setIsOpen(!isOpen);
  };

  const selectedOption = options.find(opt => opt.value === value);

  return (
    <div ref={selectorRef} className="relative">
      <button
        ref={buttonRef}
        type="button"
        onClick={handleToggle}
        className={`model-selector-compact flex items-center bg-white border border-gray-200 rounded-lg shadow-sm hover:border-primary/50 transition-all shrink-0 gap-1.5 ${isMobile ? 'px-1.5 h-8' : 'px-2 h-9'
          } ${isOpen ? 'border-primary/50 ring-1 ring-primary/20' : ''}`}
        title={`当前模型: ${value}`}
      >
        <Bot size={isMobile ? 12 : 14} className="text-primary/60 shrink-0" />
        <span className={`text-gray-700 font-medium truncate max-w-[100px] ${isMobile ? 'text-xs' : 'text-xs'}`}>
          {selectedOption?.label || value}
        </span>
        <svg
          className={`w-3 h-3 text-gray-400 transition-transform shrink-0 ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div
          className="fixed min-w-[200px] bg-white border border-gray-200 rounded-lg shadow-md overflow-hidden animate-in fade-in zoom-in-95 duration-150"
          style={{
            zIndex: 9999,
            bottom: menuPosition.bottom,
            left: menuPosition.left
          }}
        >
          <div className="overflow-y-auto py-1" style={{ maxHeight: 'calc(5 * 44px)' }}>
            {options.map((option) => (
              <div
                key={option.value}
                onClick={() => {
                  onChange(option.value);
                  setIsOpen(false);
                }}
                className={`px-3 py-2.5 text-sm cursor-pointer transition-colors flex items-center justify-between gap-3
                  ${option.value === value
                    ? 'bg-blue-50 text-primary font-medium'
                    : 'text-gray-700 hover:bg-gray-50'
                  }
                `}
              >
                <span className="whitespace-nowrap">{option.label}</span>
                {option.value === value && (
                  <Check size={14} className="text-primary shrink-0" />
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// --- 辅助函数: 消息转换 ---
// 将后端 API 返回的下划线格式字段映射为前端 Message 类型
const mapBackendMessageToFrontend = (msg: ChatResponse): Message => {
  let type: Message['type'] = 'text';
  let tableData: QueryResult | undefined = undefined;

  // 判断是否是错误消息
  const isError = msg.sql_type === 'ERROR' || (msg.content && msg.content.trim().startsWith('❌'));

  // 1. 如果是错误消息，设置为错误类型
  if (isError) {
    type = 'error';
  }
  // 2. 如果有 data 字段且不为空，优先展示表格
  else if (msg.data && Array.isArray(msg.data) && msg.data.length > 0) {
    type = 'table';
    tableData = {
      columns: msg.data.length > 0 ? Object.keys(msg.data[0]) : [],
      data: msg.data
    };
  }

  // 初始获取内容
  let displayText = msg.content || '';
  let sqlText = msg.sql_text; // 直接使用后端返回的sql_text

  // --- 关键修复：优先使用后端返回的sql_text，仅作为兜底才从文本提取 ---
  if (!sqlText && !isError) {
    // 1. 尝试匹配 Markdown 代码块 (```sql ... ```)
    const markdownMatch = displayText.match(/```(sql)?\s*([\s\S]*?)\s*```/i);
    if (markdownMatch && markdownMatch[2]) {
      sqlText = markdownMatch[2].trim();
    }
    // 2. 尝试匹配纯文本模式 (针对 "已生成查询语句：" 这种无 Markdown 的场景)
    else {
      const plainMatch = displayText.match(/(?:已生成SQL语句[：:]\s*)?\n?((?:SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\s+[\s\S]+?(?:;|\n\n|$))/i);
      if (plainMatch && plainMatch[1]) {
        const potentialSql = plainMatch[1].trim();
        if (potentialSql.length > 10) {
          sqlText = potentialSql;
        }
      }
    }
  }

  // 如果提取到了 SQL，进行文本清洗，避免重复显示
  if (sqlText && sqlText.trim() && !isError) {
    // 1. 优先移除 Markdown 块
    const codeBlockRegex = /```(sql)?\s*[\s\S]*?\s*```/gi;
    if (codeBlockRegex.test(displayText)) {
      displayText = displayText.replace(codeBlockRegex, '');
    }
    // 2. 针对纯文本 SQL 的清理逻辑
    else {
      displayText = displayText.replace(sqlText, '');
    }

    // 额外的清理：移除可能残留的空 Markdown 标记
    displayText = displayText.replace(/```\s*```/g, '');
    displayText = displayText.trim();
  }

  // 2. 映射字段
  return {
    id: msg.message_id.toString(),
    role: msg.message_type === 'assistant' ? 'model' : 'user',
    text: displayText, // 使用清洗后的文本
    type: type,
    sql: sqlText || undefined, // SQL 语句，有值时前端会渲染黑框
    tableData: tableData,
    timestamp: Date.now(), // 历史接口暂无时间戳，使用当前时间
    requiresConfirmation: msg.requires_confirmation || false // 使用后端返回的确认标志
  };
};

export const Workspace: React.FC<WorkspaceProps> = ({ project, onBack }) => {
  // --- 状态管理 ---
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>('');
  const [loadingSessions, setLoadingSessions] = useState(false);

  // 确认删除对话框状态
  const [isDeleteConfirmOpen, setIsDeleteConfirmOpen] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState<string>('');

  // 布局状态：左右面板最小化/展开
  const [isLeftPanelOpen, setIsLeftPanelOpen] = useState(true);
  const [isRightPanelOpen, setIsRightPanelOpen] = useState(true);
  const [leftPanelWidth, setLeftPanelWidth] = useState(800);
  const [isResizingLeftPanel, setIsResizingLeftPanel] = useState(false);

  // 用户手动操作状态跟踪，防止自动逻辑覆盖用户意图
  // 使用 ref 而不是 state，避免触发不必要的重渲染和 useEffect
  const userManuallyOpenedLeftRef = useRef(false);
  const userManuallyOpenedRightRef = useRef(false);

  const workspaceRootRef = useRef<HTMLDivElement>(null);
  const leftPanelWidthRef = useRef<number>(800);
  const pendingLeftPanelWidthRef = useRef<number>(800);
  const resizeRafIdRef = useRef<number | null>(null);

  // 跟踪上一次的环境状态，用于检测环境变化
  const prevZoomLevelRef = useRef(100);
  const prevBreakpointRef = useRef<string>('desktop');

  // 视口宽度状态 - 使用 useViewportWidth Hook
  const { width: viewportWidth, breakpoint, is } = useViewportWidth();

  // 缩放级别检测
  const { zoomLevel, isHighZoom, thresholds } = useGlobalZoomLevel();

  // 计算高缩放适配类名
  const getZoomAdaptiveClasses = (): string => {
    const classes: string[] = [];

    if (thresholds.above500 || zoomLevel >= 500) {
      classes.push('extreme-zoom-adaptive');
    } else if (thresholds.above300 || zoomLevel >= 300) {
      classes.push('high-zoom-adaptive');
    }

    // 工作区专用适配
    if (isHighZoom || zoomLevel > 200) {
      classes.push('workspace-zoom-adaptive');
    }

    return classes.join(' ');
  };

  // 面板切换逻辑
  // 用户手动操作优先，记录用户意图
  const handleLeftPanelToggle = (newState: boolean) => {
    console.log('用户手动操作左侧面板:', newState ? '展开' : '收起');
    setIsLeftPanelOpen(newState);

    // 记录用户手动操作状态
    if (newState) {
      // 用户手动展开面板，标记为用户主动展开
      userManuallyOpenedLeftRef.current = true;
      console.log('标记: 用户手动展开左侧面板');
    } else {
      // 用户手动收起面板，清除"手动展开"标记
      userManuallyOpenedLeftRef.current = false;
      console.log('标记: 用户手动收起左侧面板');
    }

    // 如果是高缩放模式且用户展开左侧面板，自动最小化右侧面板（互斥逻辑）
    if (isHighZoom && newState && isRightPanelOpen) {
      setIsRightPanelOpen(false);
      userManuallyOpenedRightRef.current = false;
      console.log('互斥逻辑: 展开左侧面板时自动关闭右侧面板');
    }
  };

  const handleRightPanelToggle = (newState: boolean) => {
    console.log('用户手动操作右侧面板:', newState ? '展开' : '收起');
    setIsRightPanelOpen(newState);

    // 记录用户手动操作状态
    if (newState) {
      // 用户手动展开面板，标记为用户主动展开
      userManuallyOpenedRightRef.current = true;
      console.log('标记: 用户手动展开右侧面板');
    } else {
      // 用户手动收起面板，清除"手动展开"标记
      userManuallyOpenedRightRef.current = false;
      console.log('标记: 用户手动收起右侧面板');
    }

    // 如果是高缩放模式且用户展开右侧面板，自动最小化左侧面板（互斥逻辑）
    if (isHighZoom && newState && isLeftPanelOpen) {
      setIsLeftPanelOpen(false);
      userManuallyOpenedLeftRef.current = false;
      console.log('互斥逻辑: 展开右侧面板时自动关闭左侧面板');
    }
  };

  // 自适应面板最小化策略
  // 根据视口宽度和缩放级别自动最小化面板
  // 核心原则：
  // 1. 只在环境变化时触发自动逻辑（缩放级别变化、断点变化）
  // 2. 用户手动展开的面板不会被自动收起
  // 3. 用户手动收起的面板不会被自动展开
  useEffect(() => {
    const prevZoomLevel = prevZoomLevelRef.current;
    const prevBreakpoint = prevBreakpointRef.current;

    // 检测环境是否发生变化
    const zoomLevelChanged = Math.abs(zoomLevel - prevZoomLevel) >= 10; // 缩放变化超过10%
    const breakpointChanged = breakpoint !== prevBreakpoint;

    // 更新 ref 记录当前环境
    prevZoomLevelRef.current = zoomLevel;
    prevBreakpointRef.current = breakpoint;

    // 响应式断点适配：视口宽度 <1024px 时自动最小化 DataViewer
    // 这是强制性的，不管用户是否手动展开
    if ((is.mobile || is.tablet) && breakpointChanged) {
      if (isLeftPanelOpen) {
        setIsLeftPanelOpen(false);
        userManuallyOpenedLeftRef.current = false;
        console.log('响应式断点: 自动收起左侧面板 (小屏幕)');
      }
    }

    // 响应式断点适配：视口宽度 <768px 时自动隐藏 Session 面板
    // 这是强制性的，不管用户是否手动展开
    if (is.mobile && breakpointChanged) {
      if (isRightPanelOpen) {
        setIsRightPanelOpen(false);
        userManuallyOpenedRightRef.current = false;
        console.log('响应式断点: 自动收起右侧面板 (移动端)');
      }
    }

    // 缩放级别响应式面板管理 - 只在缩放级别变化时触发
    // 并且只有在用户没有手动展开的情况下才自动收起
    if (zoomLevelChanged && zoomLevel > 200 && is.desktop) {
      // 首先最小化左侧数据库侧边栏（全局侧边栏）- 最先自动收起
      // 只有在用户没有手动展开的情况下才自动收起
      if (isLeftPanelOpen && !userManuallyOpenedLeftRef.current) {
        setIsLeftPanelOpen(false);
        console.log('缩放响应: 自动收起左侧数据库面板 (缩放级别:', zoomLevel + '%)');
      }

      // 如果缩放级别更高（>250%），也最小化右侧会话栏
      if (zoomLevel > 250 && isRightPanelOpen && !userManuallyOpenedRightRef.current) {
        setIsRightPanelOpen(false);
        console.log('缩放响应: 自动收起右侧会话面板 (缩放级别:', zoomLevel + '%)');
      }
    }

    // 注意：不自动展开面板，让用户完全控制面板状态
  }, [viewportWidth, zoomLevel, breakpoint, is, isLeftPanelOpen, isRightPanelOpen]);

  // 计算最大宽度（使用 CSS 变量定义的百分比，默认 40%）
  const getMaxLeftPanelWidth = () => {
    // 从 CSS 变量获取最大宽度百分比，默认为 40%
    const maxWidthPercent = parseFloat(
      getComputedStyle(document.documentElement)
        .getPropertyValue('--workspace-left-panel-max-width-percent')
        .replace('%', '')
    ) || 40;

    return Math.floor(viewportWidth * (maxWidthPercent / 100));
  };
  const getMinLeftPanelWidth = () => {
    const maxWidth = getMaxLeftPanelWidth();
    // 确保最小宽度不超过最大宽度，在极小视口下优先保证最大宽度约束
    return Math.min(200, maxWidth);
  };

  // 记住上次拖拽宽度
  useEffect(() => {
    try {
      const raw = localStorage.getItem('workspace.leftPanelWidth');
      const parsed = raw ? Number(raw) : NaN;
      if (Number.isFinite(parsed)) {
        const clamped = Math.max(getMinLeftPanelWidth(), Math.min(getMaxLeftPanelWidth(), parsed));
        setLeftPanelWidth(clamped);
      }
    } catch {
      // ignore
    }
  }, [viewportWidth]); // 依赖viewportWidth，当视口变化时重新计算

  useEffect(() => {
    leftPanelWidthRef.current = leftPanelWidth;
    pendingLeftPanelWidthRef.current = leftPanelWidth;
    // 同步 CSS 变量，确保非拖拽场景下也保持一致
    workspaceRootRef.current?.style.setProperty('--workspace-left-panel-width', `${leftPanelWidth}px`);
  }, [leftPanelWidth]);

  useEffect(() => {
    try {
      localStorage.setItem('workspace.leftPanelWidth', String(leftPanelWidth));
    } catch {
      // ignore
    }
  }, [leftPanelWidth]);

  // 会话重命名状态
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');

  // Project Info Modal
  const [isInfoModalOpen, setIsInfoModalOpen] = useState(false);

  // 聊天交互状态
  const [inputValue, setInputValue] = useState('');
  const [isSending, setIsSending] = useState(false); // 发送中/思考中
  const [isTyping, setIsTyping] = useState(false);   // 打字机效果进行中
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [availableModels, setAvailableModels] = useState<AIModelOption[]>([]); // 可用模型列表

  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const leftResizeStartXRef = useRef<number>(0);
  const leftResizeStartWidthRef = useRef<number>(420);
  const activeSession = sessions.find(s => s.id === activeSessionId);

  // 是否在消息底部附近（用于决定是否自动滚动）
  const isNearBottomRef = useRef(true);
  // 首次进入页面 / 切换会话时，使用非动画滚动，避免“返回工作区时”出现错误滑动
  const initialAutoScrollDoneRef = useRef(false);

  // 自动滚动到底部
  const scrollToBottom = (behavior: ScrollBehavior) => {
    messagesEndRef.current?.scrollIntoView({ behavior });
  };

  // 加载可用的 AI 模型列表
  useEffect(() => {
    const loadModels = async () => {
      try {
        const res = await sessionApi.getAIModelOptions();
        if (res.items && res.items.length > 0) {
          setAvailableModels(res.items);
          // 如果当前没有选中模型，选择第一个作为默认
          if (!selectedModel) {
            setSelectedModel(res.items[0].model_name);
          }
        }
      } catch (error) {
        console.error('Failed to load AI models:', error);
        // 如果加载失败，使用后备选项
        setAvailableModels([{ model_name: '默认模型', model_type: 'general_llm' }]);
        if (!selectedModel) {
          setSelectedModel('默认模型');
        }
      }
    };
    loadModels();
  }, []);

  // 切换会话时的处理（仅在 activeSessionId 变化时触发）
  useEffect(() => {
    // 切换会话时，重置首次滚动标记
    initialAutoScrollDoneRef.current = false;
    isNearBottomRef.current = true;

    // 切换会话时，读取该会话保存的模型
    if (activeSessionId) {
      const session = sessions.find(s => s.id === activeSessionId);
      if (session?.current_model && availableModels.some(m => m.model_name === session.current_model)) {
        setSelectedModel(session.current_model);
      }
    }
    // 注意：故意不将 sessions 加入依赖数组，避免发送消息时 sessions 更新导致模型被重置
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSessionId, availableModels]);

  useEffect(() => {
    if (!activeSessionId) return;

    // 首次进入/切换会话：直接跳到底部，不做平滑动画，避免回到页面时“滑动一下”
    if (!initialAutoScrollDoneRef.current) {
      scrollToBottom('auto');
      initialAutoScrollDoneRef.current = true;
      return;
    }

    // 后续更新：仅当用户已经在底部附近（或正在发送/打字）时才自动滚动
    if (isNearBottomRef.current || isSending || isTyping) {
      scrollToBottom('smooth');
    }
  }, [activeSessionId, activeSession?.messages.length, isSending, isTyping]);

  useEffect(() => {
    if (!isResizingLeftPanel) return;

    const prevUserSelect = document.body.style.userSelect;
    const prevCursor = document.body.style.cursor;
    document.body.style.userSelect = 'none';
    document.body.style.cursor = 'col-resize';

    const applyWidth = (width: number) => {
      workspaceRootRef.current?.style.setProperty('--workspace-left-panel-width', `${width}px`);
    };

    const handleMouseMove = (e: MouseEvent) => {
      const dx = e.clientX - leftResizeStartXRef.current;
      const nextWidth = leftResizeStartWidthRef.current + dx;
      const clamped = Math.max(getMinLeftPanelWidth(), Math.min(getMaxLeftPanelWidth(), nextWidth));
      pendingLeftPanelWidthRef.current = clamped;

      if (resizeRafIdRef.current != null) return;
      resizeRafIdRef.current = window.requestAnimationFrame(() => {
        resizeRafIdRef.current = null;
        applyWidth(pendingLeftPanelWidthRef.current);
      });
    };

    const handleMouseUp = () => {
      if (resizeRafIdRef.current != null) {
        window.cancelAnimationFrame(resizeRafIdRef.current);
        resizeRafIdRef.current = null;
      }

      document.body.style.userSelect = prevUserSelect;
      document.body.style.cursor = prevCursor;

      // mouseup 再提交 state，减少拖拽期间的 React 重渲染
      setLeftPanelWidth(pendingLeftPanelWidthRef.current);
      setIsResizingLeftPanel(false);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      if (resizeRafIdRef.current != null) {
        window.cancelAnimationFrame(resizeRafIdRef.current);
        resizeRafIdRef.current = null;
      }
      document.body.style.userSelect = prevUserSelect;
      document.body.style.cursor = prevCursor;
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizingLeftPanel]);

  // --- 1. 初始化: 加载会话列表 (真实 API) ---
  useEffect(() => {
    let isMounted = true;
    const fetchSessions = async () => {
      setLoadingSessions(true);
      try {
        if (!project.id) return;
        // 调用后端获取会话列表 - API已更新为UnifiedResponse格式
        const res = await sessionApi.getList(project.id);

        if (isMounted) {
          // 处理分页响应数据
          const sessionItems = Array.isArray(res) ? res : (res?.items || []);
          const mappedSessions: ChatSession[] = sessionItems.map(item => ({
            id: item.session_id.toString(),
            name: item.session_name,
            messages: [], // 列表接口不返回消息详情，需懒加载
            updated_at: new Date(item.created_at).getTime(),
            current_model: item.current_model
          }));
          setSessions(mappedSessions);

          // 默认选中第一个会话，并设置其保存的模型
          if (mappedSessions.length > 0 && !activeSessionId) {
            setActiveSessionId(mappedSessions[0].id);
            // 如果会话有保存的模型，使用它
            if (mappedSessions[0].current_model) {
              setSelectedModel(mappedSessions[0].current_model);
            }
          }
        }
      } catch (error) {
        console.error('Fetch sessions error:', error);
        // 错误已由API客户端统一处理，这里只需记录日志
        if (isMounted) {
          GlobalMessage.error('获取会话列表失败，请稍后重试');
        }
      } finally {
        if (isMounted) setLoadingSessions(false);
      }
    };

    fetchSessions();
    return () => { isMounted = false; };
  }, [project.id]);

  // --- 2. 切换会话: 加载历史消息 (真实 API) ---
  useEffect(() => {
    const fetchMessages = async () => {
      if (!activeSessionId) return;

      // 简单缓存策略: 如果内存中已有消息且不为空，暂不重复请求
      const current = sessions.find(s => s.id === activeSessionId);
      if (current && current.messages.length > 0) return;

      setLoadingSessions(true);
      try {
        // 调用后端获取消息历史 - API已更新为UnifiedResponse格式
        const res = await sessionApi.getMessages(Number(activeSessionId));

        // 处理响应数据 - 后端返回ChatResponse[]数组
        const messageItems = Array.isArray(res) ? res : [];
        // 使用更新后的 map 函数处理消息
        const mappedMessages = messageItems.map(mapBackendMessageToFrontend);

        setSessions(prev => prev.map(s =>
          s.id === activeSessionId ? { ...s, messages: mappedMessages } : s
        ));
      } catch (error) {
        console.error('Fetch messages error:', error);
        // 错误已由API客户端统一处理，这里只需记录日志
        GlobalMessage.error('获取消息历史失败，请稍后重试');
      } finally {
        setLoadingSessions(false);
      }
    };

    fetchMessages();
  }, [activeSessionId]);


  // --- 会话管理逻辑 (CRUD - 真实 API) ---

  const handleCreateSession = async () => {
    try {
      const res = await sessionApi.create(project.id); // 默认名称由后端或前端指定
      const newSession: ChatSession = {
        id: res.session_id.toString(),
        name: res.session_name,
        messages: [],
        updated_at: Date.now()
      };
      setSessions(prev => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      GlobalMessage.success('会话创建成功');
    } catch (error) {
      console.error('Create session error:', error);
      // 错误已由API客户端统一处理，这里只需记录日志
      GlobalMessage.error('创建会话失败，请稍后重试');
    }
  };

  const handleDeleteSession = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    setSessionToDelete(id);
    setIsDeleteConfirmOpen(true);
  };

  const confirmDeleteSession = async () => {
    if (!sessionToDelete) return;

    try {
      await sessionApi.delete(Number(sessionToDelete));
      setSessions(prev => {
        const remaining = prev.filter(s => s.id !== sessionToDelete);
        if (activeSessionId === sessionToDelete) {
          setActiveSessionId(remaining.length > 0 ? remaining[0].id : '');
        }
        return remaining;
      });
      GlobalMessage.success('会话已删除');
    } catch (error) {
      console.error('Delete session error:', error);
      // 错误已由API客户端统一处理，这里只需记录日志
      GlobalMessage.error('删除会话失败，请稍后重试');
    }
  };

  const startRenaming = (e: React.MouseEvent, session: ChatSession) => {
    e.stopPropagation();
    setEditingSessionId(session.id);
    setEditName(session.name);
  };

  const saveRename = async (e: React.MouseEvent | React.KeyboardEvent) => {
    e.stopPropagation();
    if (editingSessionId && editName.trim()) {
      try {
        await sessionApi.update(Number(editingSessionId), editName);
        setSessions(prev => prev.map(s =>
          s.id === editingSessionId ? { ...s, name: editName } : s
        ));
        GlobalMessage.success('重命名成功');
      } catch (error) {
        console.error('Rename session error:', error);
        // 错误已由API客户端统一处理，这里只需记录日志
        GlobalMessage.error('重命名失败，请稍后重试');
      }
    }
    setEditingSessionId(null);
  };

  // --- 核心: 发送消息逻辑 (真实 API) ---

  const handleSend = async (content: string = inputValue) => {
    const textToSend = content.trim();
    if (!textToSend || !activeSessionId) return;

    // 1. 乐观更新: 立即在界面显示用户消息，提升响应速度感
    const tempMsgId = `temp_${Date.now()}`;
    const userMsg: Message = {
      id: tempMsgId,
      role: 'user',
      text: textToSend,
      type: 'text',
      timestamp: Date.now()
    };

    setSessions(prev => prev.map(s =>
      s.id === activeSessionId
        ? { ...s, messages: [...s.messages, userMsg], updated_at: Date.now() }
        : s
    ));
    setInputValue('');
    setIsSending(true);

    try {
      // 2. 调用后端 API 发送消息
      const res = await sessionApi.sendMessage(Number(activeSessionId), textToSend, selectedModel);

      // 3. 处理响应并转换格式
      const aiMsg = mapBackendMessageToFrontend(res);

      // 计算是否需要智能重命名（并持久化到后端）
      const current = sessions.find(s => s.id === activeSessionId);
      const shouldAutoRename = !!current && current.messages.length <= 2 && current.name === '新会话';
      const autoName = shouldAutoRename
        ? (textToSend.length > 10 ? textToSend.substring(0, 10) + '...' : textToSend)
        : (current?.name ?? '');

      // 先更新本地状态（乐观更新）
      setSessions(prev => prev.map(s => {
        if (s.id !== activeSessionId) return s;
        return {
          ...s,
          name: shouldAutoRename ? autoName : s.name,
          messages: [...s.messages, aiMsg],
          current_model: selectedModel
        };
      }));

      // 若触发智能重命名，则调用后端持久化
      if (shouldAutoRename && autoName) {
        try {
          await sessionApi.update(Number(activeSessionId), autoName);
        } catch (e) {
          console.error('Auto rename session failed:', e);
          // 可选：提示用户失败，但保留本地名称以避免打断流程
        }
      }

      // 触发打字机效果 (如果是文本回复)
      if (aiMsg.text) setIsTyping(true);

    } catch (error: any) {
      console.error('Send message failed:', error);
      // 错误已由API客户端统一处理，这里只需记录日志和显示用户友好的错误消息
      const errorMsg: Message = {
        id: `err_${Date.now()}`,
        role: 'model',
        text: '抱歉，请求失败或超时，请稍后重试。如果问题持续存在，请联系管理员。',
        type: 'error',
        timestamp: Date.now()
      };
      setSessions(prev => prev.map(s =>
        s.id === activeSessionId ? { ...s, messages: [...s.messages, errorMsg] } : s
      ));
    } finally {
      setIsSending(false);
    }
  };

  // --- 处理高危操作确认 ---
  // 后端返回 requiresConfirmation=true 时，用户点击按钮触发
  const handleConfirmation = async (messageId: string, action: 'confirm' | 'cancel') => {
    if (action === 'confirm') {
      try {
        setIsSending(true);
        // 调用确认 API
        const res = await sessionApi.confirmMessage(Number(messageId));
        const aiMsg = mapBackendMessageToFrontend(res);

        setSessions(prev => prev.map(s => {
          if (s.id !== activeSessionId) return s;

          // 更新原消息状态，移除确认按钮
          const updatedMessages = s.messages.map(m => {
            if (m.id === messageId) {
              // 根据执行结果更新消息
              if (res.sql_type === 'ERROR') {
                return {
                  ...m,
                  requiresConfirmation: false,
                  type: 'error' as const,
                  text: res.content // 显示错误信息
                };
              } else {
                return {
                  ...m,
                  requiresConfirmation: false,
                  type: aiMsg.type,
                  tableData: aiMsg.tableData,
                  text: m.text + '\n\n✅ 执行成功'
                };
              }
            }
            return m;
          });

          return {
            ...s,
            messages: updatedMessages
          };
        }));
      } catch (error) {
        console.error('Confirm message failed:', error);
        // 错误已由API客户端统一处理，这里只需记录日志
        GlobalMessage.error('执行失败，请稍后重试');
      } finally {
        setIsSending(false);
      }
    } else {
      // 取消操作：调用后端取消接口，更新原消息内容（附加取消提示）
      try {
        setIsSending(true);
        const res = await sessionApi.cancelMessage(Number(messageId));
        const updatedMsg = mapBackendMessageToFrontend(res);

        // 更新原消息：隐藏确认按钮，并用后端返回的更新后内容替换
        setSessions(prev => prev.map(s => {
          if (s.id !== activeSessionId) return s;
          return {
            ...s,
            messages: s.messages.map(m =>
              m.id === messageId
                ? { ...updatedMsg, requiresConfirmation: false }
                : m
            )
          };
        }));
      } catch (error) {
        console.error('Cancel message failed:', error);
        GlobalMessage.error('取消失败，请稍后重试');
      } finally {
        setIsSending(false);
      }
    }
  };

  return (
    <div
      ref={workspaceRootRef}
      className={`h-full flex bg-white overflow-hidden ${
        // 响应式字体大小调整
        is.mobile ? 'text-sm' : is.tablet ? 'text-base' : 'text-base'
        } ${
        // 响应式间距调整
        is.mobile ? 'gap-0' : is.tablet ? 'gap-1' : 'gap-0'
        } ${
        // 响应式布局类
        is.mobile ? 'workspace-mobile' : is.tablet ? 'workspace-tablet' : 'workspace-desktop'
        } ${
        // 高缩放级别适配类
        getZoomAdaptiveClasses()
        }`}
      style={{ ['--workspace-left-panel-width' as any]: `${leftPanelWidth}px` }}
    >
      {/* 左侧收起后：最左侧展开把手 */}
      {!isLeftPanelOpen && (
        <div className="w-10 border-r border-gray-200 bg-white shrink-0 flex items-start justify-center pt-3">
          <PanelToggleButton
            isOpen={false}
            onToggle={() => handleLeftPanelToggle(true)}
            position="left"
          />
        </div>
      )}

      {/* 左侧：数据库导航树 + 数据内容（可最小化） */}
      <div
        className={`${isLeftPanelOpen ? '' : 'w-0'} transition-[width] duration-200 ease-in-out border-r border-gray-200 flex flex-col bg-white shrink-0 overflow-hidden`}
        style={isLeftPanelOpen ? { width: 'var(--workspace-left-panel-width)' } : undefined}
      >
        <div className="h-14 border-b border-gray-200 flex items-center justify-between px-4 bg-gray-50 shrink-0">
          <div className="flex items-center gap-2 min-w-0">
            <Database size={16} className="text-primary shrink-0" />
            <span className="font-medium text-gray-700 truncate">数据库</span>
          </div>
          <PanelToggleButton
            isOpen={true}
            onToggle={() => handleLeftPanelToggle(false)}
            position="left"
          />
        </div>
        <div className="flex-1 min-h-0 overflow-hidden">
          <DatabaseViewer projectId={Number(project.id)} className="h-full w-full" />
        </div>
      </div>

      {/* 拖拽条：调整左侧数据库面板宽度 */}
      {isLeftPanelOpen && (
        <div
          className={`w-1 bg-transparent hover:bg-gray-200 ${isResizingLeftPanel ? 'bg-gray-200' : ''} cursor-col-resize shrink-0`}
          onMouseDown={(e) => {
            leftResizeStartXRef.current = e.clientX;
            leftResizeStartWidthRef.current = leftPanelWidthRef.current;
            setIsResizingLeftPanel(true);
          }}
          onDoubleClick={() => setLeftPanelWidth(800)}
          title="拖拽调整宽度（双击重置）"
        />
      )}

      {/* 中间：对话区 */}
      <div className="flex-1 flex flex-col min-w-0 bg-white">
        {/* 顶部标题栏 */}
        <div className={`${
          // 响应式内边距调整
          is.mobile ? 'px-3 py-2' : is.tablet ? 'px-4 py-3' : 'px-6 py-4'
          } border-b border-gray-200 flex justify-between items-center bg-white sticky top-0 z-10 shadow-sm min-h-12`}>
          <div className="flex items-center gap-3 min-w-0 flex-1">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 mb-1 min-w-0">
                <h2 className={`font-bold text-gray-800 truncate min-w-0 ${
                  // 响应式标题字体大小
                  is.mobile ? 'text-base' : is.tablet ? 'text-lg' : 'text-lg'
                  }`}>{project.name}</h2>
                <span className={`px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full border border-gray-200 shrink-0 ${
                  // 响应式标签字体大小
                  is.mobile ? 'text-xs' : 'text-xs'
                  }`}>
                  {project.type}
                </span>
              </div>
              <p className={`text-gray-400 flex items-center gap-2 truncate ${
                // 响应式副标题字体大小
                is.mobile ? 'text-xs' : 'text-xs'
                }`}>
                <span className={`rounded-full shrink-0 ${activeSessionId ? 'bg-green-500' : 'bg-gray-300'
                  } ${
                  // 响应式状态指示器大小
                  is.mobile ? 'w-1.5 h-1.5' : 'w-2 h-2'
                  }`}></span>
                <span className="truncate">当前会话: {activeSession?.name || '未选择'}</span>
              </p>
            </div>
          </div>
          <div className={`flex items-center shrink-0 ${
            // 响应式按钮间距
            is.mobile ? 'gap-1' : 'gap-2'
            }`}>
            <Button
              variant="default"
              icon={<Info size={is.mobile ? 14 : 16} />}
              onClick={() => setIsInfoModalOpen(true)}
              className="header-button-icon-only"
            >
              <span className="header-button-text">项目详情</span>
            </Button>
            {!isRightPanelOpen && (
              <PanelToggleButton
                isOpen={false}
                onToggle={() => handleRightPanelToggle(true)}
                position="right"
              />
            )}
          </div>
        </div>

        {/* 消息列表区 */}
        <div
          ref={messagesContainerRef}
          onScroll={() => {
            const el = messagesContainerRef.current;
            if (!el) return;
            const distanceToBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
            isNearBottomRef.current = distanceToBottom < 80;
          }}
          className={`flex-1 overflow-y-auto bg-gray-50/30 ${
            // 响应式内边距和间距
            is.mobile ? 'p-3 space-y-3' : is.tablet ? 'p-4 space-y-4' : 'p-6 space-y-6'
            }`}
        >
          {!activeSessionId ? (
            <div className="h-full flex flex-col items-center justify-center text-gray-400">
              <Sparkles size={48} className="mb-4 text-gray-300" />
              <p>请选择或创建一个会话开始</p>
            </div>
          ) : (
            <>
              {activeSession?.messages.map((msg, index) => {
                const isLastMessage = index === activeSession.messages.length - 1;
                // 仅当是最后一条消息、且是AI发的、且当前正在打字时才显示动画
                const shouldAnimate = isLastMessage && msg.role === 'model' && isTyping;

                // 判断是否是高危 SQL (包含 UPDATE/DELETE/DROP/TRUNCATE)
                const isHighRisk = msg.sql && /^\s*(UPDATE|DELETE|DROP|TRUNCATE)/i.test(msg.sql);

                // 判断是否是错误消息
                const isError = msg.text?.startsWith('❌');

                return (
                  <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[85%] lg:max-w-[75%] ${msg.role === 'user' ? 'order-2' : 'order-1'}`}>
                      <div className={`flex items-start gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                        {/* 头像 */}
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-xs shadow-sm ${msg.role === 'user' ? 'bg-primary text-white' :
                          isError ? 'bg-red-100 text-red-600 border border-red-200' : 'bg-white border border-gray-200 text-primary'
                          }`}>
                          {msg.role === 'user' ? '我' : isError ? <AlertTriangle size={14} /> : <Sparkles size={14} />}
                        </div>

                        {/* 气泡内容 */}
                        <div className={`rounded-2xl px-5 py-4 shadow-sm ${msg.role === 'user'
                          ? 'bg-primary text-white rounded-tr-none'
                          : isError
                            ? 'bg-red-50 border border-red-200 text-red-800 rounded-tl-none'
                            : 'bg-white border border-gray-200 text-gray-800 rounded-tl-none'
                          }`}>
                          {/* 文本内容: 仅当文本非空时显示 */}
                          {msg.text && (
                            <div className="text-sm min-h-[1.25em]">
                              {shouldAnimate ? (
                                <Typewriter text={msg.text} onComplete={() => setIsTyping(false)} />
                              ) : (
                                <div className="whitespace-pre-wrap leading-relaxed">{msg.text}</div>
                              )}
                            </div>
                          )}

                          {/* SQL 代码块 (如果有) */}
                          {msg.sql && (
                            <div className="mt-3 bg-slate-800 text-slate-200 p-3 rounded-md font-mono text-xs overflow-x-auto border border-slate-700 relative group">
                              <div className="flex justify-between items-center mb-1 border-b border-slate-600 pb-1">
                                <span className="text-[10px] text-slate-400 font-bold">GENERATED SQL</span>
                                <span className="text-[10px] text-slate-500 uppercase">{project.type}</span>
                              </div>
                              <pre className="whitespace-pre-wrap">{msg.sql}</pre>
                            </div>
                          )}

                          {/* 确认操作区 (requiresConfirmation) */}
                          {msg.requiresConfirmation && (
                            <div className={`mt-3 p-3 border rounded-md animate-in fade-in slide-in-from-top-2 ${isHighRisk ? 'bg-red-50 border-red-200' : 'bg-yellow-50 border-yellow-200'}`}>
                              <div className={`flex items-center gap-2 font-bold text-xs mb-2 ${isHighRisk ? 'text-red-700' : 'text-yellow-700'}`}>
                                <AlertTriangle size={14} />
                                {isHighRisk ? '需确认操作' : '操作确认'}
                              </div>
                              <p className="text-xs text-gray-600 mb-3">
                                {isHighRisk
                                  ? '此操作将修改或删除数据库中的数据，请仔细核对 SQL 语句。是否继续？'
                                  : '是否执行上述操作？'}
                              </p>
                              <div className="flex gap-2">
                                <Button
                                  variant={isHighRisk ? 'danger' : 'primary'}
                                  className="h-7 px-3 text-xs"
                                  onClick={() => handleConfirmation(msg.id, 'confirm')}
                                  icon={<Play size={12} fill="currentColor" />}
                                  disabled={isSending}
                                >
                                  确认执行
                                </Button>
                                <Button
                                  variant="default"
                                  className="h-7 px-3 text-xs"
                                  onClick={() => handleConfirmation(msg.id, 'cancel')}
                                  icon={<Ban size={12} />}
                                  disabled={isSending}
                                >
                                  取消
                                </Button>
                              </div>
                            </div>
                          )}

                          {/* 查询结果为空提示 */}
                          {msg.sql && !msg.tableData && !isError && !msg.requiresConfirmation && /^\s*SELECT/i.test(msg.sql) && (
                            <div className="mt-4 bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm">
                              <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 flex items-center gap-2 text-xs font-semibold text-gray-600">
                                <TableIcon size={14} />
                                查询结果 (0 条)
                              </div>
                              <div className="p-8 text-center text-gray-400 text-sm">
                                查询结果为空
                              </div>
                            </div>
                          )}

                          {/* 数据表格 (Table Data) */}
                          {msg.type === 'table' && msg.tableData && (
                            <div className="mt-4 bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm">
                              <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 flex items-center gap-2 text-xs font-semibold text-gray-600">
                                <TableIcon size={14} />
                                {msg.sql && /^\s*(INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)/i.test(msg.sql) ? '执行结果' : '查询结果'} ({msg.tableData.data.length} 条)
                              </div>
                              <div className="overflow-x-auto max-h-[300px]">
                                <table className="w-full text-sm text-left">
                                  <thead className="bg-gray-50 text-gray-600 font-medium sticky top-0 z-10 shadow-sm">
                                    <tr>
                                      {msg.tableData.columns.map(col => (
                                        <th key={col} className="px-4 py-2 border-b whitespace-nowrap bg-gray-50">{col}</th>
                                      ))}
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {msg.tableData.data.map((row, i) => (
                                      <tr key={i} className="border-b last:border-0 hover:bg-gray-50 transition-colors">
                                        {msg.tableData?.columns.map(col => (
                                          <td key={col} className="px-4 py-2 text-gray-700 whitespace-nowrap">{row[col]}</td>
                                        ))}
                                      </tr>
                                    ))}
                                    {msg.tableData.data.length === 0 && (
                                      <tr><td colSpan={msg.tableData.columns.length} className="text-center py-4 text-gray-400">无数据</td></tr>
                                    )}
                                  </tbody>
                                </table>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </>
          )}

          {/* 思考中/加载中动画 */}
          {isSending && (
            <div className="flex justify-start animate-in fade-in slide-in-from-bottom-2 duration-300">
              <div className="max-w-[75%] order-1">
                <div className="flex items-start gap-3 flex-row">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-xs shadow-sm bg-white border border-gray-200 text-primary">
                    <Sparkles size={14} />
                  </div>
                  <div className="bg-white border border-gray-200 text-gray-500 rounded-2xl rounded-tl-none px-5 py-4 shadow-sm flex items-center gap-2">
                    <Loader2 className="animate-spin text-primary" size={16} />
                    <span className="text-sm">AI 正在思考并查询数据库...</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* 底部输入区 */}
        <div className={`bg-white border-t border-gray-200 ${
          // 响应式内边距
          is.mobile ? 'p-3' : is.tablet ? 'p-4' : 'p-4 sm:p-6'
          }`}>
          <div className="max-w-4xl mx-auto">
            {/* 响应式 flex 布局容器 - 改进的布局结构 */}
            <div className="input-bar-container flex items-center bg-gray-50 border border-gray-300 rounded-xl focus-within:ring-2 focus-within:ring-primary focus-within:border-primary shadow-sm overflow-hidden">
              {/* 输入框 - 使用 flex-1 和 min-w-0 防止溢出 */}
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder={activeSessionId ? "输入您的指令..." : "请先选择左侧会话"}
                className={`input-bar-textarea flex-1 min-w-0 bg-transparent border-none focus:ring-0 focus:outline-none resize-none overflow-y-auto disabled:opacity-60 disabled:cursor-not-allowed ${
                  // 响应式输入框样式
                  is.mobile ? 'pl-3 py-3 text-sm h-12' : 'pl-4 py-4 text-sm h-14'
                  }`}
                disabled={isSending || !activeSessionId}
              />

              {/* 右侧控件组容器 - 使用绝对定位确保不溢出 */}
              <div className={`input-bar-controls flex items-center shrink-0 ${
                // 响应式控件间距和内边距
                is.mobile ? 'gap-1 px-1.5 py-1.5' : 'gap-1.5 px-2 py-2'
                }`}>
                {/* 模型选择器 - 自定义下拉组件 */}
                <ModelSelector
                  value={selectedModel}
                  onChange={(newModel) => {
                    setSelectedModel(newModel);
                    if (activeSessionId) {
                      setSessions(prev => prev.map(s =>
                        s.id === activeSessionId ? { ...s, current_model: newModel } : s
                      ));
                    }
                  }}
                  options={availableModels.map(m => ({ value: m.model_name, label: m.model_name }))}
                  isMobile={is.mobile}
                />

                {/* 发送按钮 - 确保最小尺寸，不可压缩 */}
                <button
                  onClick={() => handleSend()}
                  disabled={isSending || !inputValue.trim() || !activeSessionId}
                  className="send-button bg-primary text-white rounded-lg hover:bg-primary-hover disabled:opacity-50 disabled:bg-gray-300 transition-colors shadow-sm flex items-center justify-center shrink-0"
                  style={{
                    minWidth: is.mobile ? '32px' : '36px',
                    minHeight: is.mobile ? '32px' : '36px',
                    padding: is.mobile ? '0.375rem' : '0.5rem'
                  }}
                >
                  {isSending ? <Loader2 size={is.mobile ? 14 : 16} className="animate-spin" /> : <Send size={is.mobile ? 14 : 16} />}
                </button>
              </div>
            </div>
          </div>
          <p className={`text-center text-gray-400 mt-2 ${
            // 响应式提示文字大小
            is.mobile ? 'text-xs' : 'text-xs'
            }`}>
            AI 内容仅供参考。涉及增删改操作时，系统会请求二次确认。
          </p>
        </div>
      </div>

      {/* 右侧：会话列表（可最小化） */}
      <div className={`${isRightPanelOpen ? 'w-64' : 'w-0'} transition-all duration-200 ease-in-out bg-gray-50 border-l border-gray-200 flex flex-col shrink-0 overflow-hidden`}>
        <div className="h-14 border-b border-gray-200 flex items-center justify-between px-4 bg-gray-50 shrink-0">
          <div className="flex items-center gap-2 min-w-0">
            <MessageSquare size={16} className="text-gray-500 shrink-0" />
            <span className="font-medium text-gray-700 truncate">会话</span>
          </div>
          <PanelToggleButton
            isOpen={true}
            onToggle={() => handleRightPanelToggle(false)}
            position="right"
          />
        </div>

        <div className={`p-${is.mobile ? '2' : '3'} border-b border-gray-200`}>
          <Button onClick={onBack} variant="text" className={`mb-4 text-gray-500 hover:text-gray-800 -ml-2 ${
            // 响应式按钮字体大小
            is.mobile ? 'text-sm' : 'text-sm'
            }`}>
            <ChevronLeft size={is.mobile ? 14 : 16} className="mr-1" /> 返回项目列表
          </Button>
          <Button onClick={handleCreateSession} variant="primary" className="w-full justify-center" icon={<Plus size={is.mobile ? 14 : 16} />}>
            新建会话
          </Button>
        </div>

        <div className={`flex-1 overflow-y-auto space-y-1 ${
          // 响应式会话列表内边距
          is.mobile ? 'p-2' : 'p-3'
          }`}>
          {loadingSessions ? (
            <div className="flex justify-center py-4"><Loader2 className="animate-spin text-gray-400" size={20} /></div>
          ) : sessions.map(session => (
            <div
              key={session.id}
              onClick={() => setActiveSessionId(session.id)}
              style={{ transform: 'none', minHeight: is.mobile ? '40px' : '44px' }}
              className={`group flex items-center gap-2 rounded-lg cursor-pointer border bg-white shadow-sm ${
                // 响应式会话项内边距
                is.mobile ? 'px-2 py-2.5' : 'px-3 py-3'
                } ${
                // 响应式会话项字体大小
                is.mobile ? 'text-sm' : 'text-sm'
                } ${activeSessionId === session.id
                  ? 'border-gray-200 text-primary'
                  : 'border-transparent text-gray-600 hover:bg-gray-50'
                }`}
            >
              <MessageSquare size={is.mobile ? 14 : 16} className="shrink-0" />

              {editingSessionId === session.id ? (
                <div className="flex-1 flex items-center gap-1 min-w-0">
                  <input
                    type="text"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    onClick={(e) => e.stopPropagation()}
                    onKeyDown={(e) => e.key === 'Enter' && saveRename(e)}
                    className="w-full px-1 py-0.5 text-xs border border-primary rounded focus:outline-none"
                    autoFocus
                  />
                  <button onClick={saveRename} className="session-action-btn hover:bg-green-100 text-green-600 rounded"><Check size={12} /></button>
                  <button onClick={(e) => { e.stopPropagation(); setEditingSessionId(null); }} className="session-action-btn hover:bg-red-100 text-red-600 rounded"><X size={12} /></button>
                </div>
              ) : (
                <>
                  <span className="flex-1 truncate">{session.name}</span>
                  <div className="flex items-center gap-0.5">
                    <button
                      onClick={(e) => startRenaming(e, session)}
                      className="session-action-btn hover:bg-gray-200 rounded text-gray-400 hover:text-gray-600"
                    >
                      <Edit2 size={12} />
                    </button>
                    <button
                      onClick={(e) => handleDeleteSession(e, session.id)}
                      className="session-action-btn hover:bg-red-50 rounded text-gray-400 hover:text-red-500"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                </>
              )}
            </div>
          ))}
          {!loadingSessions && sessions.length === 0 && (
            <div className="text-center text-xs text-gray-400 py-4">暂无会话，点击上方新建</div>
          )}
        </div>
      </div>

      <Modal
        isOpen={isInfoModalOpen}
        onClose={() => setIsInfoModalOpen(false)}
        title="项目详情"
        maxWidth="max-w-6xl"
        footer={<Button onClick={() => setIsInfoModalOpen(false)}>关闭</Button>}
      >
        <ProjectWizard
          projectId={project.id}
          onComplete={() => setIsInfoModalOpen(false)}
          onClose={() => setIsInfoModalOpen(false)}
          viewOnly={true}
        />
      </Modal>

      {/* 删除会话确认对话框 */}
      <ConfirmDialog
        isOpen={isDeleteConfirmOpen}
        onClose={() => setIsDeleteConfirmOpen(false)}
        onConfirm={confirmDeleteSession}
        title="删除会话"
        message="确定要删除此会话吗？删除后无法恢复。"
        confirmText="删除"
        cancelText="取消"
        isDangerous={true}
        showWarningIcon={true}
      />
    </div>
  );
};