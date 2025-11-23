
import React, { useState, useRef, useEffect } from 'react';
import { Project, Message, QueryResult, ChartData, ChatSession } from '../types.ts';
import { Button } from '../components/UI.tsx';
import { Send, BarChart as BarChartIcon, Table as TableIcon, Plus, MessageSquare, Edit2, Trash2, Check, X, ChevronLeft, Loader2, Sparkles, AlertTriangle, Play, Ban, CheckCircle2 } from 'lucide-react';
import { generateSQL, summarizeData } from '../services/geminiService.ts';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface WorkspaceProps {
  project: Project;
  onBack: () => void;
}

// Mock data for demonstration
const MOCK_TABLE_DATA: QueryResult = {
  columns: ['id', 'product_name', 'category', 'sales', 'stock'],
  data: [
    { id: 1, product_name: '智能手表 Pro', category: '电子', sales: 1520, stock: 45 },
    { id: 2, product_name: '无线降噪耳机', category: '电子', sales: 1280, stock: 120 },
    { id: 3, product_name: '人体工学椅', category: '家具', sales: 850, stock: 15 },
    { id: 4, product_name: '机械键盘', category: '电子', sales: 750, stock: 60 },
    { id: 5, product_name: '4K显示器', category: '电子', sales: 620, stock: 30 },
  ]
};

const MOCK_CHART_DATA: ChartData[] = [
  { name: '智能手表 Pro', value: 1520 },
  { name: '无线降噪耳机', value: 1280 },
  { name: '人体工学椅', value: 850 },
  { name: '机械键盘', value: 750 },
  { name: '4K显示器', value: 620 },
];

// --- Typewriter Component ---
const Typewriter: React.FC<{ text: string; onComplete?: () => void }> = ({ text, onComplete }) => {
  const [displayedText, setDisplayedText] = useState('');
  const indexRef = useRef(0);
  const onCompleteRef = useRef(onComplete);

  // Keep ref updated with latest callback
  useEffect(() => {
    onCompleteRef.current = onComplete;
  });

  useEffect(() => {
    // Reset state when text changes (new message)
    indexRef.current = 0;
    setDisplayedText('');
    
    const intervalId = setInterval(() => {
      if (indexRef.current < text.length) {
        // Access text by index to avoid closure issues, though text is in dependency
        setDisplayedText((prev) => prev + text.charAt(indexRef.current));
        indexRef.current++;
      } else {
        clearInterval(intervalId);
        // Call latest callback
        if (onCompleteRef.current) onCompleteRef.current();
      }
    }, 15); // Speed: 15ms per character

    return () => clearInterval(intervalId);
  }, [text]); // Only re-run if the text content itself changes

  return <span className="whitespace-pre-wrap leading-relaxed">{displayedText}</span>;
};

export const Workspace: React.FC<WorkspaceProps> = ({ project, onBack }) => {
  // Session State
  const [sessions, setSessions] = useState<ChatSession[]>([
    {
      id: '1',
      name: '销售数据分析',
      updatedAt: Date.now(),
      messages: [
        {
          id: 'init',
          role: 'model',
          text: `欢迎来到 ${project.name} 工作台！我是您的AI数据库助手。`,
          type: 'text',
          timestamp: Date.now()
        }
      ]
    }
  ]);
  const [activeSessionId, setActiveSessionId] = useState<string>('1');
  
  // Editing State
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');

  // Chat State
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // State to track if the latest message is currently typing
  const [isTyping, setIsTyping] = useState(false);

  const activeSession = sessions.find(s => s.id === activeSessionId) || sessions[0];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Scroll when messages change, loading changes, or typing happens
  useEffect(() => {
    scrollToBottom();
  }, [activeSession?.messages, isLoading, isTyping]);

  // --- Session Management ---

  const handleCreateSession = () => {
    const newSession: ChatSession = {
      id: Date.now().toString(),
      name: '新会话',
      updatedAt: Date.now(),
      messages: [{
        id: Date.now().toString(),
        role: 'model',
        text: `新会话已创建。请告诉我您想查询什么？`,
        type: 'text',
        timestamp: Date.now()
      }]
    };
    setSessions([newSession, ...sessions]);
    setActiveSessionId(newSession.id);
  };

  const handleDeleteSession = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (sessions.length <= 1) {
      alert("至少需要保留一个会话");
      return;
    }
    if (confirm("确定要删除此会话吗？")) {
      const newSessions = sessions.filter(s => s.id !== id);
      setSessions(newSessions);
      if (activeSessionId === id) {
        setActiveSessionId(newSessions[0].id);
      }
    }
  };

  const startRenaming = (e: React.MouseEvent, session: ChatSession) => {
    e.stopPropagation();
    setEditingSessionId(session.id);
    setEditName(session.name);
  };

  const saveRename = (e: React.MouseEvent | React.KeyboardEvent) => {
    e.stopPropagation();
    if (editingSessionId && editName.trim()) {
      setSessions(sessions.map(s => s.id === editingSessionId ? { ...s, name: editName } : s));
    }
    setEditingSessionId(null);
  };

  const cancelRename = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingSessionId(null);
  };

  // --- Chat Logic ---

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      text: inputValue,
      type: 'text',
      timestamp: Date.now()
    };

    // Update UI immediately with user message
    const updatedSessions = sessions.map(s => 
      s.id === activeSessionId 
        ? { ...s, messages: [...s.messages, userMsg], updatedAt: Date.now() } 
        : s
    );
    setSessions(updatedSessions);
    setInputValue('');
    setIsLoading(true); // Start loading state

    try {
      // 1. Gemini: NL -> SQL
      const { sql, explanation } = await generateSQL(userMsg.text, "table schema context...");
      
      // Check if SQL is DML (INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE)
      const isDML = /^\s*(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE)/i.test(sql);

      // Safety Check (Mutation.NL.Safety.Check): Check for UPDATE/DELETE without WHERE
      const isHighRisk = /^\s*(UPDATE|DELETE)/i.test(sql) && !/\s+WHERE\s+/i.test(sql);

      const sqlMsg: Message = {
        id: Date.now().toString() + '_sql',
        role: 'model',
        text: explanation, // Use explanation as the main text
        type: 'text',
        sql: sql,
        timestamp: Date.now(),
        status: isDML ? 'pending' : undefined,
        // We can repurpose chartData or add a custom field, but here we'll use the presence of isHighRisk to modify UI in render
        // For now, let's encode it in the type or logic. 
        // Adding a temporary flag inside the object which Typescript might complain about if not in interface.
        // Let's handle it in the render logic by checking the SQL string again or assuming 'pending' + SQL content.
      };

      // Update session with SQL message
      setSessions(prev => prev.map(s => 
        s.id === activeSessionId 
          ? { 
              ...s, 
              messages: [...s.messages, sqlMsg],
              name: s.messages.length <= 1 ? (userMsg.text.substring(0, 10) + (userMsg.text.length > 10 ? '...' : '')) : s.name
            } 
          : s
      ));

      // If DML, stop here and wait for confirmation
      if (isDML) {
        setIsLoading(false);
        return;
      }

      // 2. Simulate Execution & Summarization (For SELECT queries)
      await new Promise(resolve => setTimeout(resolve, 800)); // Simulating network delay
      const resultData = MOCK_TABLE_DATA;
      const chartData = MOCK_CHART_DATA;
      const summary = await summarizeData(resultData.data, userMsg.text);

      const resultMsg: Message = {
        id: Date.now().toString() + '_result',
        role: 'model',
        text: summary,
        type: 'table',
        tableData: resultData,
        chartData: chartData,
        timestamp: Date.now()
      };

      setSessions(prev => prev.map(s => 
        s.id === activeSessionId 
          ? { ...s, messages: [...s.messages, resultMsg] }
          : s
      ));

    } catch (error) {
      const errorMsg: Message = {
        id: Date.now().toString(),
        role: 'model',
        text: '抱歉，处理您的请求时遇到错误。请重试。',
        type: 'error',
        timestamp: Date.now()
      };
      setSessions(prev => prev.map(s => s.id === activeSessionId ? { ...s, messages: [...s.messages, errorMsg] } : s));
    } finally {
      setIsLoading(false); // End loading state
    }
  };

  const handleExecuteDML = async (messageId: string, sql: string) => {
    // 1. Mark as executed
    setSessions(prev => prev.map(s => 
      s.id === activeSessionId 
        ? { 
            ...s, 
            messages: s.messages.map(m => m.id === messageId ? { ...m, status: 'executed' } : m)
          }
        : s
    ));

    setIsLoading(true);
    
    // 2. Simulate Execution
    try {
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulating network
      
      // Result Message
      const resultMsg: Message = {
        id: Date.now().toString(),
        role: 'model',
        text: '✅ SQL 执行成功。\n\n受影响行数: 1\n执行耗时: 45ms',
        type: 'text',
        timestamp: Date.now()
      };

      setSessions(prev => prev.map(s => 
        s.id === activeSessionId 
          ? { ...s, messages: [...s.messages, resultMsg] }
          : s
      ));

    } catch (error) {
      const errorMsg: Message = {
        id: Date.now().toString(),
        role: 'model',
        text: '执行失败: 数据库连接超时。',
        type: 'error',
        timestamp: Date.now()
      };
      setSessions(prev => prev.map(s => s.id === activeSessionId ? { ...s, messages: [...s.messages, errorMsg] } : s));
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancelDML = (messageId: string) => {
    // Mark as cancelled
    setSessions(prev => prev.map(s => 
      s.id === activeSessionId 
        ? { 
            ...s, 
            messages: s.messages.map(m => m.id === messageId ? { ...m, status: 'cancelled' } : m)
          }
        : s
    ));

    // Add cancellation message
    const cancelMsg: Message = {
      id: Date.now().toString(),
      role: 'model',
      text: '🚫 操作已取消，未对数据库进行任何修改。',
      type: 'text',
      timestamp: Date.now()
    };

    setSessions(prev => prev.map(s => 
      s.id === activeSessionId 
        ? { ...s, messages: [...s.messages, cancelMsg] }
        : s
    ));
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
          {sessions.map(session => (
            <div 
              key={session.id}
              onClick={() => setActiveSessionId(session.id)}
              className={`group flex items-center gap-3 px-3 py-3 rounded-lg text-sm cursor-pointer transition-colors border border-transparent ${
                activeSessionId === session.id 
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
              当前会话: {activeSession?.name}
            </p>
          </div>
          <Button variant="default" icon={<BarChartIcon size={16} />}>生成报表</Button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-gray-50/30">
          {activeSession?.messages.map((msg, index) => {
             const isLastMessage = index === activeSession.messages.length - 1;
             const shouldAnimate = isLastMessage && msg.role === 'model' && !isLoading && !msg.status; 

             const isHighRisk = msg.sql && /^\s*(UPDATE|DELETE)/i.test(msg.sql) && !/\s+WHERE\s+/i.test(msg.sql);

             return (
              <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] lg:max-w-[75%] ${msg.role === 'user' ? 'order-2' : 'order-1'}`}>
                  <div className={`flex items-start gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                    {/* Avatar */}
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-xs shadow-sm ${msg.role === 'user' ? 'bg-primary text-white' : 'bg-white border border-gray-200 text-primary'}`}>
                      {msg.role === 'user' ? '我' : <Sparkles size={14} />}
                    </div>
                    
                    {/* Content Bubble */}
                    <div className={`rounded-2xl px-5 py-4 shadow-sm ${
                      msg.role === 'user' 
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
                      {msg.status === 'pending' && (
                        <div className={`mt-3 p-3 border rounded-md animate-in fade-in slide-in-from-top-2 ${isHighRisk ? 'bg-red-50 border-red-200' : 'bg-yellow-50 border-yellow-200'}`}>
                          <div className={`flex items-center gap-2 font-bold text-xs mb-2 ${isHighRisk ? 'text-red-700' : 'text-yellow-700'}`}>
                            <AlertTriangle size={14} />
                            {isHighRisk ? '高危操作警告' : '需要确认执行'}
                          </div>
                          <p className="text-xs text-gray-600 mb-3">
                            {isHighRisk 
                              ? '检测到该操作没有 WHERE 条件，将影响全表数据！请务必确认。' 
                              : '此操作将修改数据库数据，请仔细核对 SQL 语句是否符合预期。'}
                          </p>
                          <div className="flex gap-3">
                            <Button 
                              variant={isHighRisk ? 'danger' : 'primary'}
                              className="h-8 px-3 text-xs" 
                              onClick={() => handleExecuteDML(msg.id, msg.sql!)} 
                              icon={<Play size={12} fill="currentColor" />}
                            >
                              确认执行
                            </Button>
                            <Button 
                              variant="default" 
                              className="h-8 px-3 text-xs bg-white hover:bg-gray-100" 
                              onClick={() => handleCancelDML(msg.id)}
                              icon={<Ban size={12} />}
                            >
                              取消
                            </Button>
                          </div>
                        </div>
                      )}

                      {msg.status === 'executed' && (
                        <div className="mt-2 text-xs text-green-600 flex items-center gap-1 font-medium">
                          <CheckCircle2 size={14} /> 已确认执行
                        </div>
                      )}

                      {msg.status === 'cancelled' && (
                        <div className="mt-2 text-xs text-gray-400 flex items-center gap-1 font-medium">
                          <Ban size={14} /> 已取消
                        </div>
                      )}

                      {/* Data Table Visualization */}
                      {msg.type === 'table' && msg.tableData && (
                        <div className="mt-4 bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm">
                          <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 flex items-center gap-2 text-xs font-semibold text-gray-600">
                            <TableIcon size={14} /> 数据预览 (Top 5)
                          </div>
                          <div className="overflow-x-auto">
                            <table className="w-full text-sm text-left">
                              <thead className="bg-gray-50 text-gray-600 font-medium">
                                <tr>
                                  {msg.tableData.columns.map(col => (
                                    <th key={col} className="px-4 py-2 border-b whitespace-nowrap">{col}</th>
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

                      {/* Chart Visualization */}
                      {msg.type === 'table' && msg.chartData && (
                        <div className="mt-4 h-64 w-full min-w-[350px] bg-white p-2 rounded-lg border border-gray-200 shadow-sm">
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={msg.chartData}>
                              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                              <XAxis dataKey="name" tick={{fontSize: 11}} interval={0} height={40} tickFormatter={(val) => val.length > 5 ? val.slice(0,5)+'...' : val} />
                              <YAxis tick={{fontSize: 11}} />
                              <Tooltip 
                                cursor={{fill: '#f9fafb'}} 
                                contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)'}} 
                              />
                              <Bar dataKey="value" fill="#1677ff" radius={[4, 4, 0, 0]} barSize={30} />
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
          
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
                    <span className="text-sm">AI 正在思考...</span>
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
              disabled={isLoading}
            />
            <button 
              onClick={handleSend}
              disabled={isLoading || !inputValue.trim()}
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
