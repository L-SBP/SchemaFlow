import React, { useState, useRef, useEffect } from 'react';
import { Project, Message, QueryResult, ChatSession } from '../types';
import { Button, message as GlobalMessage } from '../components/UI';
import { Send, BarChart as BarChartIcon, Table as TableIcon, Plus, MessageSquare, Edit2, Trash2, Check, X, ChevronLeft, Loader2, Sparkles, AlertTriangle, Play, Ban, CheckCircle2 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { sessionApi, SessionItem, ChatMessageResponse } from '../api/session';

interface WorkspaceProps {
  project: Project;
  onBack: () => void;
}

// --- Typewriter Component ---
const Typewriter: React.FC<{ text: string; onComplete?: () => void }> = ({ text, onComplete }) => {
  const [displayedText, setDisplayedText] = useState('');
  const indexRef = useRef(0);
  const onCompleteRef = useRef(onComplete);

  useEffect(() => {
    onCompleteRef.current = onComplete;
  });

  useEffect(() => {
    indexRef.current = 0;
    setDisplayedText('');

    if (!text) {
      if (onCompleteRef.current) onCompleteRef.current();
      return;
    }

    const intervalId = setInterval(() => {
      if (indexRef.current < text.length) {
        setDisplayedText((prev) => prev + text.charAt(indexRef.current));
        indexRef.current++;
      } else {
        clearInterval(intervalId);
        if (onCompleteRef.current) onCompleteRef.current();
      }
    }, 15);

    return () => clearInterval(intervalId);
  }, [text]);

  return <span className="whitespace-pre-wrap leading-relaxed">{displayedText}</span>;
};

// 辅助函数：将后端消息转换为前端 Message 对象
const mapBackendMessageToFrontend = (msg: ChatMessageResponse): Message => {
  let type: Message['type'] = 'text';
  let tableData: QueryResult | undefined = undefined;

  // 如果有数据，优先展示表格
  if (msg.data && Array.isArray(msg.data) && msg.data.length > 0) {
    type = 'table';
    // 假设 data 是对象数组，取第一个对象的 key 作为列名
    const columns = Object.keys(msg.data[0]);
    tableData = {
      columns: columns,
      data: msg.data
    };
  }

  // 后端返回 message_type: 'assistant' | 'user'
  // 前端 Message: role: 'model' | 'user'
  return {
    id: msg.message_id.toString(),
    role: msg.message_type === 'assistant' ? 'model' : 'user',
    text: msg.content || '',
    type: type,
    sql: msg.sql_text || undefined,
    tableData: tableData,
    timestamp: Date.now(), // 暂无后端时间戳，使用当前时间
    requiresConfirmation: msg.requires_confirmation
  };
};

export const Workspace: React.FC<WorkspaceProps> = ({ project, onBack }) => {
  // Session State
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>('');
  const [loadingSessions, setLoadingSessions] = useState(false);

  // Editing State
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');

  // Chat State
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [isTyping, setIsTyping] = useState(false);

  // 获取当前激活的会话对象
  const activeSession = sessions.find(s => s.id === activeSessionId);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [activeSession?.messages, isLoading, isTyping]);

  // --- 1. Load Sessions ---
  useEffect(() => {
    let isMounted = true; // 防止卸载后状态更新

    const fetchSessions = async () => {
      setLoadingSessions(true);
      try {
        console.log(`[Workspace] Fetching sessions for project: ${project.id}`);
        // 确保 project.id 存在且有效
        if (!project.id) {
          console.warn('[Workspace] Project ID is missing');
          return;
        }

        const res = await sessionApi.getList(project.id);

        if (isMounted) {
          const mappedSessions: ChatSession[] = res.map(item => ({
            id: item.session_id.toString(),
            name: item.session_name,
            messages: [], // 列表接口不返回消息，后续懒加载
            updatedAt: new Date(item.created_at).getTime()
          }));
          setSessions(mappedSessions);

          // 默认选中第一个会话
          if (mappedSessions.length > 0 && !activeSessionId) {
            setActiveSessionId(mappedSessions[0].id);
          }
        }
      } catch (error) {
        console.error('[Workspace] Error fetching sessions:', error);
        if (isMounted) GlobalMessage.error('获取会话列表失败');
      } finally {
        if (isMounted) setLoadingSessions(false);
      }
    };

    if (project.id) {
      fetchSessions();
    }

    return () => { isMounted = false; };
  }, [project.id]);

  // --- 2. Load Messages for Active Session ---
  useEffect(() => {
    const fetchMessages = async () => {
      if (!activeSessionId) return;

      const currentSession = sessions.find(s => s.id === activeSessionId);
      // 如果消息已存在（长度>0），则不再重复请求（简单缓存策略）
      // 注意：如果需要实时性，可以去掉这个判断
      if (currentSession && currentSession.messages.length > 0) return;

      try {
        console.log(`[Workspace] Fetching messages for session: ${activeSessionId}`);
        const res = await sessionApi.getMessages(Number(activeSessionId));
        const mappedMessages = res.map(mapBackendMessageToFrontend);

        setSessions(prev => prev.map(s =>
          s.id === activeSessionId ? { ...s, messages: mappedMessages } : s
        ));
      } catch (error) {
        console.error('[Workspace] Failed to load messages:', error);
      }
    };

    fetchMessages();
  }, [activeSessionId]);

  // --- Session Management Handlers ---

  const handleCreateSession = async () => {
    try {
      console.log('[Workspace] Creating session...');
      const res = await sessionApi.create(project.id, `新会话 ${new Date().toLocaleTimeString()}`);

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
      console.error('[Workspace] Create session failed:', error);
      GlobalMessage.error('创建会话失败');
    }
  };

  const handleDeleteSession = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (confirm("确定要删除此会话吗？")) {
      try {
        await sessionApi.delete(Number(id));

        setSessions(prev => {
          const newSessions = prev.filter(s => s.id !== id);
          // 如果删除的是当前选中的会话，切换到第一个或置空
          if (activeSessionId === id) {
            // 使用 setTimeout 避免在渲染周期内直接 setState 的潜在冲突，但在 React 18 自动批处理下通常不需要
            // 这里直接在下一个 render cycle 生效
            setActiveSessionId(newSessions.length > 0 ? newSessions[0].id : '');
          }
          return newSessions;
        });

        GlobalMessage.success('会话已删除');
      } catch (error) {
        GlobalMessage.error('删除会话失败');
      }
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
        setSessions(prev => prev.map(s => s.id === editingSessionId ? { ...s, name: editName } : s));
        GlobalMessage.success('重命名成功');
      } catch (error) {
        GlobalMessage.error('重命名失败');
      }
    }
    setEditingSessionId(null);
  };

  const cancelRename = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingSessionId(null);
  };

  // --- Chat Logic ---

  const handleSend = async () => {
    if (!inputValue.trim() || !activeSessionId) return;

    // 1. Optimistic Update (前端先显示)
    const tempId = 'temp_' + Date.now();
    const userMsg: Message = {
      id: tempId,
      role: 'user',
      text: inputValue,
      type: 'text',
      timestamp: Date.now()
    };

    setSessions(prev => prev.map(s =>
      s.id === activeSessionId
        ? { ...s, messages: [...s.messages, userMsg], updatedAt: Date.now() }
        : s
    ));
    setInputValue('');
    setIsLoading(true);

    try {
      // 2. Call API
      console.log(`[Workspace] Sending message to session ${activeSessionId}:`, userMsg.text);
      const res = await sessionApi.sendMessage(Number(activeSessionId), userMsg.text);

      // 3. Add AI Response
      const aiMsg = mapBackendMessageToFrontend(res);

      setSessions(prev => prev.map(s =>
        s.id === activeSessionId
          ? {
            ...s,
            // 替换掉临时消息（可选，这里简单追加 AI 回复，保留用户消息）
            messages: [...s.messages, aiMsg],
            // 如果是第一条对话，自动更新会话名称
            name: s.messages.length <= 1 ? (userMsg.text.substring(0, 10) + (userMsg.text.length > 10 ? '...' : '')) : s.name
          }
          : s
      ));

    } catch (error) {
      console.error('[Workspace] Send message failed:', error);
      const errorMsg: Message = {
        id: Date.now().toString(),
        role: 'model',
        text: '抱歉，请求失败，请稍后重试。',
        type: 'error',
        timestamp: Date.now()
      };
      setSessions(prev => prev.map(s => s.id === activeSessionId ? { ...s, messages: [...s.messages, errorMsg] } : s));
    } finally {
      setIsLoading(false);
    }
  };

  // 模拟 DML 确认：目前后端接口未提供独立的 execute 接口，
  // 通常是通过再次发送 "确认" 文本给 AI 来触发下一步。
  const handleExecuteDML = async (messageId: string, sql: string) => {
    setInputValue("确认执行");
    // 这里可以让用户点击发送，或者直接调用 handleSend()
    // 为了体验更好，您可以直接在这里调用 handleSend 逻辑（需抽离 send 逻辑接收参数）
    // 或者简单地填入输入框引导用户点击
  };

  return (
    <div className="h-full flex bg-white">
      {/* Sidebar: Session List */}
      <div className="w-64 bg-gray-50 border-r border-gray-200 flex flex-col shrink-0">
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
                  <button onClick={cancelRename} className="p-1 hover:bg-red-100 text-red-600 rounded"><X size={12} /></button>
                </div>
              ) : (
                <>
                  <span className="flex-1 truncate">{session.name}</span>
                  <div className="hidden group-hover:flex items-center gap-1">
                    <button
                      onClick={(e) => startRenaming(e, session)}
                      className="p-1 hover:bg-gray-200 rounded text-gray-400 hover:text-gray-600"
                      title="重命名"
                    >
                      <Edit2 size={12} />
                    </button>
                    <button
                      onClick={(e) => handleDeleteSession(e, session.id)}
                      className="p-1 hover:bg-red-50 rounded text-gray-400 hover:text-red-500"
                      title="删除"
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

      {/* Main: Chat Area */}
      <div className="flex-1 flex flex-col min-w-0 bg-white">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center bg-white sticky top-0 z-10">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h2 className="font-bold text-gray-800 text-lg">{project.name}</h2>
              <span className="px-2 py-0.5 bg-gray-100 text-gray-500 text-xs rounded-full border border-gray-200">
                {project.type}
              </span>
            </div>
            <p className="text-xs text-gray-400 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500"></span>
              当前会话: {activeSession?.name || '未选择'}
            </p>
          </div>
          <Button variant="default" icon={<BarChartIcon size={16} />}>生成报表</Button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-gray-50/30">
          {!activeSessionId ? (
            <div className="h-full flex flex-col items-center justify-center text-gray-400">
              <Sparkles size={48} className="mb-4 text-gray-300" />
              <p>请选择或创建一个会话开始</p>
            </div>
          ) : (
            <>
              {activeSession?.messages.map((msg, index) => {
                const isLastMessage = index === activeSession.messages.length - 1;
                const shouldAnimate = isLastMessage && msg.role === 'model' && !isLoading;
                const isHighRisk = msg.sql && /^\s*(UPDATE|DELETE|DROP|TRUNCATE)/i.test(msg.sql) && !/\s+WHERE\s+/i.test(msg.sql);

                return (
                  <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[85%] lg:max-w-[75%] ${msg.role === 'user' ? 'order-2' : 'order-1'}`}>
                      <div className={`flex items-start gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                        {/* Avatar */}
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-xs shadow-sm ${msg.role === 'user' ? 'bg-primary text-white' : 'bg-white border border-gray-200 text-primary'}`}>
                          {msg.role === 'user' ? '我' : <Sparkles size={14} />}
                        </div>

                        {/* Content Bubble */}
                        <div className={`rounded-2xl px-5 py-4 shadow-sm ${msg.role === 'user'
                          ? 'bg-primary text-white rounded-tr-none'
                          : 'bg-white border border-gray-200 text-gray-800 rounded-tl-none'
                          }`}>
                          <div className="text-sm">
                            {shouldAnimate ? (
                              <Typewriter text={msg.text} onComplete={() => setIsTyping(false)} />
                            ) : (
                              <div className="whitespace-pre-wrap leading-relaxed">{msg.text}</div>
                            )}
                          </div>

                          {/* SQL Preview */}
                          {msg.sql && (
                            <div className="mt-3 bg-slate-800 text-slate-200 p-3 rounded-md font-mono text-xs overflow-x-auto border border-slate-700">
                              <div className="flex justify-between items-center mb-1 border-b border-slate-600 pb-1">
                                <span className="text-[10px] text-slate-400">GENERATED SQL</span>
                              </div>
                              {msg.sql}
                            </div>
                          )}

                          {/* DML Confirmation Block */}
                          {msg.requiresConfirmation && (
                            <div className={`mt-3 p-3 border rounded-md animate-in fade-in slide-in-from-top-2 ${isHighRisk ? 'bg-red-50 border-red-200' : 'bg-yellow-50 border-yellow-200'}`}>
                              <div className={`flex items-center gap-2 font-bold text-xs mb-2 ${isHighRisk ? 'text-red-700' : 'text-yellow-700'}`}>
                                <AlertTriangle size={14} />
                                {isHighRisk ? '高危操作警告' : '需要确认执行'}
                              </div>
                              <p className="text-xs text-gray-600 mb-3">
                                此操作将修改数据库数据，请仔细核对 SQL 语句。输入"确认"以执行。
                              </p>
                              <div className="flex gap-3">
                                <Button
                                  variant={isHighRisk ? 'danger' : 'primary'}
                                  className="h-8 px-3 text-xs"
                                  onClick={() => handleExecuteDML(msg.id, msg.sql!)}
                                  icon={<Play size={12} fill="currentColor" />}
                                >
                                  填入确认指令
                                </Button>
                              </div>
                            </div>
                          )}

                          {/* Data Table Visualization */}
                          {msg.type === 'table' && msg.tableData && (
                            <div className="mt-4 bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm">
                              <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 flex items-center gap-2 text-xs font-semibold text-gray-600">
                                <TableIcon size={14} /> 数据预览 (Top {msg.tableData.data.length})
                              </div>
                              <div className="overflow-x-auto max-h-[300px]">
                                <table className="w-full text-sm text-left">
                                  <thead className="bg-gray-50 text-gray-600 font-medium sticky top-0">
                                    <tr>
                                      {msg.tableData.columns.map(col => (
                                        <th key={col} className="px-4 py-2 border-b whitespace-nowrap bg-gray-50">{col}</th>
                                      ))}
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {msg.tableData.data.map((row, i) => (
                                      <tr key={i} className="border-b last:border-0 hover:bg-gray-50">
                                        {msg.tableData?.columns.map(col => (
                                          <td key={col} className="px-4 py-2 text-gray-700 whitespace-nowrap">{row[col]}</td>
                                        ))}
                                      </tr>
                                    ))}
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

          {/* Thinking/Loading Bubble */}
          {isLoading && (
            <div className="flex justify-start animate-in fade-in slide-in-from-bottom-2 duration-300">
              <div className="max-w-[75%] order-1">
                <div className="flex items-start gap-3 flex-row">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-xs shadow-sm bg-white border border-gray-200 text-primary">
                    <Sparkles size={14} />
                  </div>
                  <div className="bg-white border border-gray-200 text-gray-500 rounded-2xl rounded-tl-none px-5 py-4 shadow-sm flex items-center gap-2">
                    <Loader2 className="animate-spin text-primary" size={16} />
                    <span className="text-sm">AI 正在查询...</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-6 bg-white border-t border-gray-200">
          <div className="relative max-w-4xl mx-auto">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="输入您的指令，例如：查询本月销售额最高的商品..."
              className="w-full pl-4 pr-12 py-3 bg-gray-50 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary resize-none shadow-sm text-sm h-14 overflow-hidden disabled:opacity-60"
              disabled={isLoading || !activeSessionId}
            />
            <button
              onClick={handleSend}
              disabled={isLoading || !inputValue.trim() || !activeSessionId}
              className="absolute right-3 top-3 p-2 bg-primary text-white rounded-lg hover:bg-primary-hover disabled:opacity-50 disabled:bg-gray-300 transition-colors shadow-sm"
            >
              <Send size={16} />
            </button>
          </div>
          <p className="text-center text-xs text-gray-400 mt-2">
            AI 生成的内容可能不准确，执行 DML 操作前请务必确认 SQL 语句。
          </p>
        </div>
      </div>
    </div>
  );
};