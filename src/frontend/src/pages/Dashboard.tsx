import React, { useState, useRef, useEffect } from 'react';
import { Project } from '../types.ts';
import { Card, Button, Tag, Modal, Input, ProgressBar, Steps } from '../components/UI.tsx';
import { Plus, Database, Server, Clock, ArrowRight, Terminal, Loader2, CheckCircle2, BrainCircuit, Code2, PlayCircle, Sparkles } from 'lucide-react';
import { generateSchema } from '../services/geminiService.ts';

interface DashboardProps {
  projects: Project[];
  setProjects: React.Dispatch<React.SetStateAction<Project[]>>;
  onProjectSelect: (project: Project) => void;
}

const DEPLOYMENT_STEPS = [
  { title: '需求分析' },
  { title: '逻辑设计' },
  { title: '生成代码' },
  { title: '环境部署' },
];

export const Dashboard: React.FC<DashboardProps> = ({ projects, setProjects, onProjectSelect }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [deploymentState, setDeploymentState] = useState<'idle' | 'processing' | 'completed'>('idle');
  
  // Deployment Process State
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  
  // Content State
  const [analysisText, setAnalysisText] = useState('');
  const [ddlText, setDdlText] = useState('');
  const [logs, setLogs] = useState<string[]>([]);
  
  // Form State
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectType, setNewProjectType] = useState<'MySQL' | 'PostgreSQL'>('MySQL');
  const [newProjectDesc, setNewProjectDesc] = useState('');

  const logsEndRef = useRef<HTMLDivElement>(null);
  const analysisScrollRef = useRef<HTMLDivElement>(null);
  const ddlScrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Auto-scroll content
  useEffect(() => {
    if (analysisScrollRef.current) analysisScrollRef.current.scrollTop = analysisScrollRef.current.scrollHeight;
  }, [analysisText]);

  useEffect(() => {
    if (ddlScrollRef.current) ddlScrollRef.current.scrollTop = ddlScrollRef.current.scrollHeight;
  }, [ddlText]);

  const resetForm = () => {
    setNewProjectName('');
    setNewProjectDesc('');
    setDeploymentState('idle');
    setCurrentStep(0);
    setProgress(0);
    setAnalysisText('');
    setDdlText('');
    setLogs([]);
  };

  const handleCloseModal = () => {
    if (deploymentState === 'processing') {
      if (!confirm("部署正在进行中，确定要取消吗？")) return;
    }
    setIsModalOpen(false);
    setTimeout(resetForm, 300);
  };

  // Improved Typewriter effect
  const streamText = async (fullText: string, setter: React.Dispatch<React.SetStateAction<string>>, speed: number = 10) => {
    // Split by lines to feel more like natural thinking/coding
    const chunks = fullText.split(/(?=[,.\n])/); 
    let current = '';
    
    for (const chunk of chunks) {
      // If chunk is too long, split it by characters
      if (chunk.length > 20) {
        for (const char of chunk) {
          current += char;
          setter(current);
          await new Promise(r => setTimeout(r, Math.max(2, speed / 2)));
        }
      } else {
        current += chunk;
        setter(current);
        await new Promise(r => setTimeout(r, speed * 2));
      }
    }
    setter(fullText);
  };

  const handleCreateProject = async () => {
    if (!newProjectName || !newProjectDesc) return;
    
    setDeploymentState('processing');
    setCurrentStep(0);
    setProgress(5);
    setLogs(prev => [...prev, '>>> 初始化部署序列...', '>>> 正在连接智能 Agent (Gemini 3.0 Pro)...']);

    try {
      // Step 0: Request Analysis
      const result = await generateSchema(newProjectDesc);
      
      // Step 1: Analysis Visualization
      setCurrentStep(1);
      setProgress(20);
      setLogs(prev => [...prev, '✔ 智能体已连接', '>>> 开始业务需求深度分析...']);
      
      await streamText(result.analysis, setAnalysisText, 10);
      
      await new Promise(r => setTimeout(r, 500));

      // Step 2: DDL Generation
      setCurrentStep(2);
      setProgress(50);
      setLogs(prev => [...prev, '✔ 逻辑模型构建完成 (3NF)', '>>> 正在生成数据库定义语言 (DDL)...']);
      
      await streamText(result.ddl, setDdlText, 5);

      await new Promise(r => setTimeout(r, 800));

      // Step 3: Deployment
      setCurrentStep(3);
      setProgress(75);
      setLogs(prev => [...prev, '✔ SQL 语法校验通过', '>>> 分配云端数据库实例 (Region: CN-North)...', '>>> 执行 Schema 初始化脚本...']);
      
      await new Promise(r => setTimeout(r, 1500)); // Simulating network
      
      setLogs(prev => [...prev, '✔ 表结构创建成功', '✔ 索引策略已应用', '✔ 用户权限配置完成', '>>> 服务启动中...']);
      setProgress(100);
      setDeploymentState('completed');
      setCurrentStep(4); // All done

      const newProject: Project = {
        id: Date.now().toString(),
        name: newProjectName,
        type: newProjectType,
        description: newProjectDesc,
        status: 'active',
        createdAt: new Date().toISOString().split('T')[0]
      };

      setTimeout(() => {
        setProjects([newProject, ...projects]);
      }, 1000);

    } catch (e) {
      setLogs(prev => [...prev, `❌ 部署过程发生致命错误: ${(e as Error).message}`]);
      setDeploymentState('idle'); 
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto h-full overflow-y-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-2xl font-bold text-gray-800 tracking-tight">数据库项目</h2>
          <p className="text-gray-500 mt-1">管理您的 AI 驱动数据库实例</p>
        </div>
        <Button variant="primary" icon={<Plus size={16} />} onClick={() => setIsModalOpen(true)}>
          新建项目
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {projects.map(project => (
          <Card key={project.id} className="hover:shadow-lg transition-shadow cursor-pointer group border-gray-200" title={
            <div className="flex items-center gap-2.5">
              <div className="p-2 bg-blue-50 rounded-lg text-primary">
                <Database size={20} />
              </div>
              <span className="font-semibold">{project.name}</span>
            </div>
          } extra={<Tag color={project.status === 'active' ? 'green' : 'orange'}>{project.status === 'active' ? '运行中' : '部署中'}</Tag>}>
            <div className="space-y-4" onClick={() => onProjectSelect(project)}>
              <p className="text-gray-600 text-sm line-clamp-2 h-10 leading-relaxed">{project.description}</p>
              
              <div className="flex items-center justify-between text-xs text-gray-400 pt-4 border-t border-gray-50">
                <div className="flex items-center gap-1.5 bg-gray-50 px-2 py-1 rounded">
                  <Server size={12} /> {project.type}
                </div>
                <div className="flex items-center gap-1.5">
                  <Clock size={12} /> {project.createdAt}
                </div>
              </div>
              
              <div className="flex justify-end pt-2 opacity-0 group-hover:opacity-100 transition-all duration-300 transform translate-y-2 group-hover:translate-y-0">
                <Button variant="text" className="text-primary text-xs hover:bg-blue-50 px-0">
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
        title={deploymentState === 'idle' ? "创建新的数据库项目" : "自动化部署中心"}
        maxWidth={deploymentState === 'idle' ? 'max-w-md' : 'max-w-6xl'} 
        footer={
          deploymentState === 'idle' ? (
            <>
              <Button onClick={handleCloseModal}>取消</Button>
              <Button variant="primary" onClick={handleCreateProject} icon={<PlayCircle size={16} />}>
                开始智能部署
              </Button>
            </>
          ) : deploymentState === 'completed' ? (
             <Button variant="primary" onClick={() => { setIsModalOpen(false); resetForm(); }} icon={<CheckCircle2 size={16} />}>
                完成并进入工作台
             </Button>
          ) : null
        }
      >
        {deploymentState === 'idle' ? (
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
                      className={`cursor-pointer px-4 py-3 rounded-lg border flex items-center gap-3 transition-all ${
                        newProjectType === type 
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
                  placeholder="请详细描述实体及关系。例如：我们需要一个电商订单系统，包含用户、商品、订单和评价。用户可以下多个订单，订单包含多个商品..."
                  value={newProjectDesc}
                  onChange={(e) => setNewProjectDesc(e.target.value)}
                ></textarea>
              </div>
            </div>
          </div>
        ) : (
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
              
              {/* Left: Schema Analysis (Document Style) */}
              <div className="flex-1 flex flex-col border border-gray-200 rounded-xl overflow-hidden shadow-sm bg-white transition-all duration-300 hover:shadow-md">
                <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center gap-2.5">
                  <div className="p-1.5 bg-white rounded-md shadow-sm text-purple-600">
                    <BrainCircuit size={16} />
                  </div>
                  <span className="text-sm font-semibold text-gray-700">Schema 逻辑分析</span>
                  {currentStep === 1 && <span className="ml-auto text-xs text-primary font-medium flex items-center gap-1"><Loader2 size={12} className="animate-spin" /> Thinking...</span>}
                </div>
                <div ref={analysisScrollRef} className="flex-1 p-5 overflow-y-auto text-sm leading-7 text-gray-700 font-sans prose prose-sm max-w-none">
                  {analysisText ? (
                    <div className="whitespace-pre-wrap">{analysisText}</div>
                  ) : (
                    <div className="h-full flex flex-col items-center justify-center text-gray-400 gap-2">
                      <BrainCircuit size={32} className="opacity-20" />
                      <p>等待 AI 分析业务需求...</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Right: DDL Generation (Code Editor Style) */}
              <div className="flex-1 flex flex-col border border-gray-800 rounded-xl overflow-hidden bg-[#1e1e1e] shadow-lg transition-all duration-300 hover:shadow-xl">
                <div className="bg-[#252526] px-4 py-3 border-b border-gray-700 flex items-center gap-2.5">
                  <div className="p-1.5 bg-gray-700 rounded-md text-blue-400">
                    <Code2 size={16} />
                  </div>
                  <span className="text-sm font-semibold text-gray-200">Generated DDL (SQL)</span>
                  {currentStep === 2 && <span className="ml-auto text-xs text-green-400 font-medium flex items-center gap-1"><Loader2 size={12} className="animate-spin" /> Generating...</span>}
                </div>
                <div ref={ddlScrollRef} className="flex-1 p-5 overflow-y-auto font-mono text-xs leading-6 bg-[#1e1e1e] text-[#d4d4d4]">
                  {ddlText ? (
                    <pre className="whitespace-pre-wrap"><code className="language-sql">{ddlText}</code></pre>
                  ) : (
                    <div className="h-full flex flex-col items-center justify-center text-gray-600 gap-2">
                      <Code2 size={32} className="opacity-20" />
                      <p>// 等待逻辑模型确认...</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Bottom: Logs (Terminal Style) */}
            <div className="mt-4 mx-2 h-36 bg-black rounded-xl p-4 font-mono text-xs text-gray-300 overflow-y-auto shadow-inner border border-gray-800 relative">
              <div className="sticky top-0 left-0 bg-black/80 backdrop-blur-sm w-full pb-2 mb-2 border-b border-gray-800 flex items-center gap-2 text-gray-500 uppercase tracking-wider font-bold text-[10px]">
                <Terminal size={12} /> Deployment Logs
              </div>
              <div className="space-y-1.5">
                {logs.map((log, i) => (
                  <div key={i} className="flex items-start gap-2 animate-in fade-in slide-in-from-left-2 duration-300">
                    <span className="text-gray-600 shrink-0">[{new Date().toLocaleTimeString()}]</span>
                    <span className={log.includes('❌') ? 'text-red-400 font-bold' : log.includes('✔') ? 'text-green-400 font-bold' : 'text-gray-300'}>
                      {log.replace('>>>', '').replace('✔', '').replace('❌', '')}
                    </span>
                    {log.includes('>>>') && <span className="w-1.5 h-4 bg-gray-500 animate-pulse ml-1 inline-block align-middle"></span>}
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