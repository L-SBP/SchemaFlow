import React, { useState, useRef, useEffect } from 'react';
import { Project, Message, QueryResult, ChatSession, ChatResponse } from '../types';
import { Button, message as GlobalMessage, Modal } from '../components/UI';
import { Send, Plus, MessageSquare, Edit2, Trash2, Check, X, ChevronLeft, Loader2, Sparkles, AlertTriangle, Play, Ban, Table as TableIcon, Info, Bot, Database, PanelLeftClose, PanelLeftOpen, PanelRightClose, PanelRightOpen } from 'lucide-react';
import { sessionApi } from '../api/session';
import { ProjectWizard } from '../components/ProjectWizard';
import DatabaseViewer from './DatabaseViewer';

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

// --- 辅助函数: 消息转换 ---
// 将后端 API 返回的下划线格式字段映射为前端 Message 类型
const mapBackendMessageToFrontend = (msg: ChatResponse): Message => {
  let type: Message['type'] = 'text';
  let tableData: QueryResult | undefined = undefined;

  // 1. 如果有 data 字段且不为空，优先展示表格
  if (msg.data && Array.isArray(msg.data) && msg.data.length > 0) {
    type = 'table';
    // 假设 data 是对象数组，取第一个对象的 key 作为列名
    const columns = Object.keys(msg.data[0]);
    tableData = {
      columns: columns,
      data: msg.data
    };
  }

  // 初始获取内容
  let displayText = msg.content || '';
  let sqlText = msg.sql_text;

  // 判断是否是错误消息
  const isError = displayText.trim().startsWith('❌');

  // --- 关键修复：如果后端未返回 sql_text (如历史记录)，尝试从文本提取 ---
  // FIX: 如果是错误消息，不尝试提取 SQL，避免将错误详情中的 SQL 关键字误判为代码
  if (!sqlText && !isError) {
    // 1. 尝试匹配 Markdown 代码块 (```sql ... ```)
    const markdownMatch = displayText.match(/```(sql)?\s*([\s\S]*?)\s*```/i);
    if (markdownMatch && markdownMatch[2]) {
      sqlText = markdownMatch[2].trim();
    }
    // 2. 尝试匹配纯文本模式 (针对 "已生成查询语句：" 这种无 Markdown 的场景)
    else {
      // FIX: 优化正则，使用非贪婪匹配 [\s\S]+? 并尝试在分号 ; 或双换行 \n\n 处停止，
      // 防止正则吞掉 SQL 语句后面的普通文本说明。
      const plainMatch = displayText.match(/(?:已生成SQL语句[：:]\s*)?\n?((?:SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\s+[\s\S]+?(?:;|\n\n|$))/i);
      if (plainMatch && plainMatch[1]) {
        // 简单的二次校验：长度大于 10 且包含空格，避免误判
        const potentialSql = plainMatch[1].trim();
        if (potentialSql.length > 10) {
          sqlText = potentialSql;
        }
      }
    }
  }

  // 如果提取到了 SQL，进行文本清洗，避免重复显示
  if (sqlText && sqlText.trim()) {
    // 1. 优先移除 Markdown 块 (Markdown 结构明确，移除是安全的)
    const codeBlockRegex = /```(sql)?\s*[\s\S]*?\s*```/gi;
    if (codeBlockRegex.test(displayText)) {
      displayText = displayText.replace(codeBlockRegex, '');
    }
    // 2. 针对纯文本 SQL 的清理逻辑：仅从文本中移除 SQL 部分，保留其他说明文字
    else {
      displayText = displayText.replace(sqlText, '');
    }

    // 3. 移除特定的提示语 (如果 SQL 被提取了，这些提示语也就没用了)
    // FIX: 注释掉此行，以保留 "已生成查询语句：" 这样的提示文字，实现文字与SQL的分离显示
    // displayText = displayText.replace(/已生成查询语句[：:]\s*/g, '');

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
    requiresConfirmation: msg.requires_confirmation // 是否需要确认
  };
};

export const Workspace: React.FC<WorkspaceProps> = ({ project, onBack }) => {
  // --- 状态管理 ---
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>('');
  const [loadingSessions, setLoadingSessions] = useState(false);
  // loadingMessages 未直接使用在 JSX 中，但可用于后续扩展 loading 骨架屏
  const [loadingMessages, setLoadingMessages] = useState(false);

  // 布局状态：左右面板最小化/展开
  const [isLeftPanelOpen, setIsLeftPanelOpen] = useState(true);
  const [isRightPanelOpen, setIsRightPanelOpen] = useState(true);
  const [leftPanelWidth, setLeftPanelWidth] = useState(800);
  const [isResizingLeftPanel, setIsResizingLeftPanel] = useState(false);

  const workspaceRootRef = useRef<HTMLDivElement>(null);
  const leftPanelWidthRef = useRef<number>(800);
  const pendingLeftPanelWidthRef = useRef<number>(800);
  const resizeRafIdRef = useRef<number | null>(null);

  // 记住上次拖拽宽度
  useEffect(() => {
    try {
      const raw = localStorage.getItem('workspace.leftPanelWidth');
      const parsed = raw ? Number(raw) : NaN;
      if (Number.isFinite(parsed)) {
        const clamped = Math.max(260, Math.min(1600, parsed));
        setLeftPanelWidth(clamped);
      }
    } catch {
      // ignore
    }
  }, []);

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
  const [selectedModel, setSelectedModel] = useState<string>('xiyan-sql'); // 模型选择

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

  useEffect(() => {
    // 切换会话时，重置首次滚动标记
    initialAutoScrollDoneRef.current = false;
    isNearBottomRef.current = true;
  }, [activeSessionId]);

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
      const clamped = Math.max(260, Math.min(1600, nextWidth));
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
        // 调用后端获取会话列表
        const res = await sessionApi.getList(project.id);

        if (isMounted) {
          const mappedSessions: ChatSession[] = res.map(item => ({
            id: item.session_id.toString(),
            name: item.session_name,
            messages: [], // 列表接口不返回消息详情，需懒加载
            updatedAt: new Date(item.created_at).getTime()
          }));
          setSessions(mappedSessions);

          // 默认选中第一个会话
          if (mappedSessions.length > 0 && !activeSessionId) {
            setActiveSessionId(mappedSessions[0].id);
          }
        }
      } catch (error) {
        console.error('Fetch sessions error:', error);
        GlobalMessage.error('获取会话列表失败');
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

      setLoadingMessages(true);
      try {
        // 调用后端获取消息历史
        const res = await sessionApi.getMessages(Number(activeSessionId));
        // 使用更新后的 map 函数处理消息
        const mappedMessages = res.map(mapBackendMessageToFrontend);

        setSessions(prev => prev.map(s =>
          s.id === activeSessionId ? { ...s, messages: mappedMessages } : s
        ));
      } catch (error) {
        console.error('Fetch messages error:', error);
      } finally {
        setLoadingMessages(false);
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
        updatedAt: Date.now()
      };
      setSessions(prev => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      GlobalMessage.success('会话创建成功');
    } catch (error) {
      GlobalMessage.error('创建会话失败');
    }
  };

  const handleDeleteSession = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (!confirm("确定要删除此会话吗？")) return;

    try {
      await sessionApi.delete(Number(id));
      setSessions(prev => {
        const remaining = prev.filter(s => s.id !== id);
        if (activeSessionId === id) {
          setActiveSessionId(remaining.length > 0 ? remaining[0].id : '');
        }
        return remaining;
      });
      GlobalMessage.success('会话已删除');
    } catch (error) {
      GlobalMessage.error('删除会话失败');
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
        GlobalMessage.error('重命名失败');
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
        ? { ...s, messages: [...s.messages, userMsg], updatedAt: Date.now() }
        : s
    ));
    setInputValue('');
    setIsSending(true);

    try {
      // 2. 调用后端 API 发送消息
      const res = await sessionApi.sendMessage(Number(activeSessionId), textToSend, selectedModel);

      // 3. 处理响应并转换格式
      const aiMsg = mapBackendMessageToFrontend(res);

      setSessions(prev => prev.map(s => {
        if (s.id !== activeSessionId) return s;

        // 智能重命名 (仅前端逻辑优化): 如果是前几条消息且名称为默认，尝试用问题更新会话标题
        let newName = s.name;
        if (s.messages.length <= 2 && s.name === '新会话') {
          newName = textToSend.length > 10 ? textToSend.substring(0, 10) + '...' : textToSend;
        }

        return {
          ...s,
          name: newName,
          messages: [...s.messages, aiMsg]
        };
      }));

      // 触发打字机效果 (如果是文本回复)
      if (aiMsg.text) setIsTyping(true);

    } catch (error: any) {
      console.error('Send message failed:', error);
      const errorMsg: Message = {
        id: `err_${Date.now()}`,
        role: 'model',
        text: '抱歉，请求失败或超时，请稍后重试。',
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
          const updatedMessages = s.messages.map(m =>
            m.id === messageId ? { ...m, requiresConfirmation: false } : m
          );

          return {
            ...s,
            messages: [...updatedMessages, aiMsg]
          };
        }));
      } catch (error) {
        console.error('Confirm message failed:', error);
        GlobalMessage.error('执行失败');
      } finally {
        setIsSending(false);
      }
    } else {
      // 取消操作
      handleSend("取消");
      // 隐藏原消息的确认按钮
      setSessions(prev => prev.map(s =>
        s.id === activeSessionId ? {
          ...s,
          messages: s.messages.map(m => m.id === messageId ? { ...m, requiresConfirmation: false } : m)
        } : s
      ));
    }
  };

  return (
    <div
      ref={workspaceRootRef}
      className="h-full flex bg-white overflow-hidden"
      style={{ ['--workspace-left-panel-width' as any]: `${leftPanelWidth}px` }}
    >
      {/* 左侧收起后：最左侧展开把手 */}
      {!isLeftPanelOpen && (
        <div className="w-10 border-r border-gray-200 bg-white shrink-0 flex items-start justify-center pt-3">
          <button
            onClick={() => setIsLeftPanelOpen(true)}
            className="p-1.5 hover:bg-gray-100 rounded-md text-gray-500 hover:text-gray-800 transition-colors"
            title="展开数据库面板"
            type="button"
          >
            <PanelLeftOpen size={18} />
          </button>
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
          <button
            onClick={() => setIsLeftPanelOpen(false)}
            className="p-1.5 hover:bg-gray-200 rounded-md text-gray-500 transition-colors"
            title="最小化数据库面板"
            type="button"
          >
            <PanelLeftClose size={18} />
          </button>
        </div>
        <div className="flex-1 min-h-0 overflow-hidden">
          {activeSessionId ? (
            <DatabaseViewer sessionId={Number(activeSessionId)} className="h-full w-full" />
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-gray-400 p-6 text-center bg-gray-50/30">
              <Database size={44} className="mb-3 opacity-20" />
              <p className="text-sm">请选择/创建会话后查看数据库</p>
            </div>
          )}
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
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center bg-white sticky top-0 z-10 shadow-sm">
          <div className="flex items-center gap-3 min-w-0">
            <div className="min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h2 className="font-bold text-gray-800 text-lg truncate">{project.name}</h2>
                <span className="px-2 py-0.5 bg-gray-100 text-gray-500 text-xs rounded-full border border-gray-200 shrink-0">
                  {project.type}
                </span>
              </div>
              <p className="text-xs text-gray-400 flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${activeSessionId ? 'bg-green-500' : 'bg-gray-300'}`}></span>
                当前会话: {activeSession?.name || '未选择'}
              </p>
            </div>
          </div>
          <div className="flex gap-2 items-center">
            <Button variant="default" icon={<Info size={16} />} onClick={() => setIsInfoModalOpen(true)}>
              项目详情
            </Button>
            {!isRightPanelOpen && (
              <button
                onClick={() => setIsRightPanelOpen(true)}
                className="p-1.5 hover:bg-gray-100 rounded-md text-gray-500 hover:text-gray-800 transition-colors"
                title="展开会话列表"
                type="button"
              >
                <PanelRightOpen size={18} />
              </button>
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
          className="flex-1 overflow-y-auto p-6 space-y-6 bg-gray-50/30"
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
        <div className="p-6 bg-white border-t border-gray-200">
          <div className="relative max-w-4xl mx-auto flex items-center">
            {/* 输入框 */}
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
              // 关键修改：右侧内边距设置为 13rem (约 208px)，为右侧的控件组预留空间
              className="w-full pl-4 pr-[13rem] py-4 bg-gray-50 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary resize-none shadow-sm text-sm h-14 overflow-hidden disabled:opacity-60 disabled:cursor-not-allowed"
              disabled={isSending || !activeSessionId}
            />

            {/* 右侧控件组容器: 包含模型选择器和发送按钮 */}
            <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-2">
              {/* 模型选择器 */}
              <div className="flex items-center bg-white border border-gray-200 rounded-lg shadow-sm px-2 h-9 hover:border-gray-300 transition-colors">
                <Bot size={14} className="text-gray-400 mr-1.5" />
                <span className="text-[10px] text-gray-400 mr-1 select-none">模型</span>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="text-xs bg-transparent border-none focus:ring-0 text-gray-700 font-medium cursor-pointer outline-none p-0 pr-1 max-w-[100px] truncate"
                  title="选择模型"
                >
                  <option value="xiyan-sql">xiyan-sql</option>
                  <option value="deepseek-v3">DeepSeek V3.1</option>
                  <option value="my-finetuned-sql">my-finetuned-sql</option>
                </select>
              </div>

              {/* 发送按钮 */}
              <button
                onClick={() => handleSend()}
                disabled={isSending || !inputValue.trim() || !activeSessionId}
                className="p-2 bg-primary text-white rounded-lg hover:bg-primary-hover disabled:opacity-50 disabled:bg-gray-300 transition-colors shadow-sm h-9 w-9 flex items-center justify-center"
              >
                {isSending ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
              </button>
            </div>
          </div>
          <p className="text-center text-xs text-gray-400 mt-2">
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
          <button
            onClick={() => setIsRightPanelOpen(false)}
            className="p-1.5 hover:bg-gray-200 rounded-md text-gray-500 transition-colors"
            title="最小化会话列表"
            type="button"
          >
            <PanelRightClose size={18} />
          </button>
        </div>

        <div className="p-4 border-b border-gray-200">
          <Button onClick={onBack} variant="text" className="mb-4 text-gray-500 hover:text-gray-800 -ml-2 text-sm">
            <ChevronLeft size={16} className="mr-1" /> 返回项目列表
          </Button>
          <Button onClick={handleCreateSession} variant="primary" className="w-full justify-center" icon={<Plus size={16} />}>
            新建会话
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          {loadingSessions ? (
            <div className="flex justify-center py-4"><Loader2 className="animate-spin text-gray-400" size={20} /></div>
          ) : sessions.map(session => (
            <div
              key={session.id}
              onClick={() => setActiveSessionId(session.id)}
              className={`group flex items-center gap-3 px-3 py-3 rounded-lg text-sm cursor-pointer transition-colors border border-transparent ${activeSessionId === session.id
                ? 'bg-white border-gray-200 shadow-sm text-primary'
                : 'text-gray-600 hover:bg-gray-200/50'
                }`}
            >
              <MessageSquare size={16} className="shrink-0" />

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
                  <button onClick={saveRename} className="p-1 hover:bg-green-100 text-green-600 rounded"><Check size={12} /></button>
                  <button onClick={(e) => { e.stopPropagation(); setEditingSessionId(null); }} className="p-1 hover:bg-red-100 text-red-600 rounded"><X size={12} /></button>
                </div>
              ) : (
                <>
                  <span className="flex-1 truncate">{session.name}</span>
                  <div className="hidden group-hover:flex items-center gap-1">
                    <button
                      onClick={(e) => startRenaming(e, session)}
                      className="p-1 hover:bg-gray-200 rounded text-gray-400 hover:text-gray-600"
                    >
                      <Edit2 size={12} />
                    </button>
                    <button
                      onClick={(e) => handleDeleteSession(e, session.id)}
                      className="p-1 hover:bg-red-50 rounded text-gray-400 hover:text-red-500"
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
    </div>
  );
};