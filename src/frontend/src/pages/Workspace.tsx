import React, { useState, useRef, useEffect } from 'react';
import { Project, Message, QueryResult, ChatSession } from '../types.ts';
import { Button, message as GlobalMessage } from '../components/UI.tsx';
import { Send, Plus, MessageSquare, Edit2, Trash2, Check, X, ChevronLeft, Loader2, Sparkles, AlertTriangle, Play, Ban, Table as TableIcon } from 'lucide-react';
import { sessionApi, ChatMessageResponse } from '../api/session.ts';

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
const mapBackendMessageToFrontend = (msg: ChatMessageResponse): Message => {
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

  // 2. 映射字段
  return {
    id: msg.message_id.toString(),
    role: msg.message_type === 'assistant' ? 'model' : 'user',
    text: msg.content || '', // 确保文本不为 null
    type: type,
    sql: msg.sql_text || undefined, // SQL 语句
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

  // 会话重命名状态
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');

  // 聊天交互状态
  const [inputValue, setInputValue] = useState('');
  const [isSending, setIsSending] = useState(false); // 发送中/思考中
  const [isTyping, setIsTyping] = useState(false);   // 打字机效果进行中

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const activeSession = sessions.find(s => s.id === activeSessionId);

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [activeSession?.messages, isSending, isTyping]);

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
      const res = await sessionApi.sendMessage(Number(activeSessionId), textToSend);

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
  const handleConfirmation = (action: 'confirm' | 'cancel') => {
    if (action === 'confirm') {
      // 发送确认指令，后端 Session 上下文会识别
      handleSend("确认执行");
    } else {
      handleSend("取消");
    }
  };

  return (
    <div className="h-full flex bg-white">
      {/* 侧边栏: 会话列表 */}
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

      {/* 主区域: 聊天窗口 */}
      <div className="flex-1 flex flex-col min-w-0 bg-white">
        {/* 顶部标题栏 */}
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center bg-white sticky top-0 z-10 shadow-sm">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h2 className="font-bold text-gray-800 text-lg">{project.name}</h2>
              <span className="px-2 py-0.5 bg-gray-100 text-gray-500 text-xs rounded-full border border-gray-200">
                {project.type}
              </span>
            </div>
            <p className="text-xs text-gray-400 flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${activeSessionId ? 'bg-green-500' : 'bg-gray-300'}`}></span>
              当前会话: {activeSession?.name || '未选择'}
            </p>
          </div>
        </div>

        {/* 消息列表区 */}
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
                // 仅当是最后一条消息、且是AI发的、且当前正在打字时才显示动画
                const shouldAnimate = isLastMessage && msg.role === 'model' && isTyping;

                // 判断是否是高危 SQL (包含 UPDATE/DELETE/DROP/TRUNCATE)
                const isHighRisk = msg.sql && /^\s*(UPDATE|DELETE|DROP|TRUNCATE)/i.test(msg.sql);

                return (
                  <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[85%] lg:max-w-[75%] ${msg.role === 'user' ? 'order-2' : 'order-1'}`}>
                      <div className={`flex items-start gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                        {/* 头像 */}
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-xs shadow-sm ${msg.role === 'user' ? 'bg-primary text-white' : 'bg-white border border-gray-200 text-primary'
                          }`}>
                          {msg.role === 'user' ? '我' : <Sparkles size={14} />}
                        </div>

                        {/* 气泡内容 */}
                        <div className={`rounded-2xl px-5 py-4 shadow-sm ${msg.role === 'user'
                            ? 'bg-primary text-white rounded-tr-none'
                            : 'bg-white border border-gray-200 text-gray-800 rounded-tl-none'
                          }`}>
                          {/* 文本内容 */}
                          <div className="text-sm min-h-[1.25em]">
                            {shouldAnimate ? (
                              <Typewriter text={msg.text} onComplete={() => setIsTyping(false)} />
                            ) : (
                              <div className="whitespace-pre-wrap leading-relaxed">{msg.text}</div>
                            )}
                          </div>

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
                                {isHighRisk ? '高危操作警告' : '操作确认'}
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
                                  onClick={() => handleConfirmation('confirm')}
                                  icon={<Play size={12} fill="currentColor" />}
                                  disabled={isSending}
                                >
                                  确认执行
                                </Button>
                                <Button
                                  variant="default"
                                  className="h-7 px-3 text-xs"
                                  onClick={() => handleConfirmation('cancel')}
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
                                查询结果 ({msg.tableData.data.length} 条)
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
              placeholder={activeSessionId ? "输入您的指令，例如：查询本月销售额最高的商品..." : "请先选择左侧会话"}
              className="w-full pl-4 pr-12 py-3 bg-gray-50 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary resize-none shadow-sm text-sm h-14 overflow-hidden disabled:opacity-60 disabled:cursor-not-allowed"
              disabled={isSending || !activeSessionId}
            />
            <button
              onClick={() => handleSend()}
              disabled={isSending || !inputValue.trim() || !activeSessionId}
              className="absolute right-3 top-3 p-2 bg-primary text-white rounded-lg hover:bg-primary-hover disabled:opacity-50 disabled:bg-gray-300 transition-colors shadow-sm"
            >
              {isSending ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            </button>
          </div>
          <p className="text-center text-xs text-gray-400 mt-2">
            AI 内容仅供参考。涉及增删改操作时，系统会请求二次确认。
          </p>
        </div>
      </div>
    </div>
  );
};