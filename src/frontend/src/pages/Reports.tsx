
import React, { useState, useMemo } from 'react';
import { Project, Report, ReportType, QueryResult } from '../types.ts';
import { Card, Button, Modal, Input, Tag, Steps } from '../components/UI.tsx';
import { Plus, BarChart2, PieChart, TrendingUp, Download, Trash2, Edit2, Filter, Database, Table as TableIcon, ScatterChart, ArrowRight, ArrowLeft, Save } from 'lucide-react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart as RePieChart, Pie, Cell, ScatterChart as ReScatterChart, Scatter, ZAxis } from 'recharts';

interface ReportsProps {
  projects: Project[];
}

const COLORS = ['#1677ff', '#52c41a', '#faad14', '#ff4d4f', '#722ed1', '#13c2c2'];

// --- Mock Query History Data (Simulating data from Workspace) ---
interface MockHistoryQuery {
  id: string;
  projectId: string;
  queryText: string;
  timestamp: string;
  result: QueryResult;
}

const MOCK_HISTORY_QUERIES: MockHistoryQuery[] = [
  {
    id: 'q1',
    projectId: '1',
    queryText: '统计 Top 5 产品销量',
    timestamp: '2025-11-05 10:30',
    result: {
      columns: ['产品名称', '总销量', '库存', '销售额'],
      data: [
        { '产品名称': '智能手表 Pro', '总销量': 1520, '库存': 45, '销售额': 456000 },
        { '产品名称': '无线降噪耳机', '总销量': 1280, '库存': 120, '销售额': 256000 },
        { '产品名称': '便携式咖啡机', '总销量': 980, '库存': 15, '销售额': 196000 },
        { '产品名称': '人体工学椅', '总销量': 750, '库存': 30, '销售额': 375000 },
        { '产品名称': '4K网络摄像头', '总销量': 620, '库存': 85, '销售额': 124000 },
      ]
    }
  },
  {
    id: 'q2',
    projectId: '1',
    queryText: '最近 7 天的日活趋势',
    timestamp: '2025-11-04 14:20',
    result: {
      columns: ['日期', 'DAU', '新增用户'],
      data: [
        { '日期': '11-01', 'DAU': 4500, '新增用户': 120 },
        { '日期': '11-02', 'DAU': 4700, '新增用户': 150 },
        { '日期': '11-03', 'DAU': 4600, '新增用户': 130 },
        { '日期': '11-04', 'DAU': 5100, '新增用户': 200 },
        { '日期': '11-05', 'DAU': 5300, '新增用户': 220 },
        { '日期': '11-06', 'DAU': 5200, '新增用户': 180 },
        { '日期': '11-07', 'DAU': 5500, '新增用户': 250 },
      ]
    }
  },
  {
    id: 'q3',
    projectId: '2',
    queryText: '客户来源渠道分布',
    timestamp: '2025-10-28 09:15',
    result: {
      columns: ['渠道', '客户数', '转化率'],
      data: [
        { '渠道': '搜索引擎', '客户数': 850, '转化率': 0.05 },
        { '渠道': '社交媒体', '客户数': 650, '转化率': 0.08 },
        { '渠道': '线下活动', '客户数': 400, '转化率': 0.12 },
        { '渠道': '朋友推荐', '客户数': 300, '转化率': 0.25 },
      ]
    }
  }
];

// --- Initial Reports Data ---
const MOCK_REPORTS: Report[] = [
  {
    id: 'r1',
    projectId: '1',
    name: '电商运营数据 - Top 5 产品销量',
    type: 'bar',
    description: '基于 11-05 的销量查询生成',
    data: MOCK_HISTORY_QUERIES[0].result.data,
    chartConfig: { xAxisKey: '产品名称', yAxisKey: '总销量' },
    sourceQueryId: 'q1',
    sourceQueryText: '统计 Top 5 产品销量',
    updatedAt: '2025-11-05'
  }
];

export const Reports: React.FC<ReportsProps> = ({ projects }) => {
  const [selectedProjectId, setSelectedProjectId] = useState<string>(projects[0]?.id || '');
  const [reports, setReports] = useState<Report[]>(MOCK_REPORTS);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  // --- Wizard State ---
  const [step, setStep] = useState(0); // 0: Select Data, 1: Configure Chart
  const [selectedQueryId, setSelectedQueryId] = useState<string>('');
  
  // Form State
  const [reportName, setReportName] = useState('');
  const [reportType, setReportType] = useState<ReportType>('bar');
  const [xAxisKey, setXAxisKey] = useState('');
  const [yAxisKey, setYAxisKey] = useState('');

  const filteredReports = reports.filter(r => r.projectId === selectedProjectId);
  const availableQueries = MOCK_HISTORY_QUERIES.filter(q => q.projectId === selectedProjectId);
  
  const selectedQueryObj = availableQueries.find(q => q.id === selectedQueryId);

  // Initialize form when query changes
  useMemo(() => {
    if (selectedQueryObj) {
      // Default report name to query text
      if (!reportName) setReportName(selectedQueryObj.queryText + ' 报表');
      // Default axis selection (heuristic: first string for X, first number for Y)
      const firstStringCol = selectedQueryObj.result.columns.find(c => typeof selectedQueryObj.result.data[0][c] === 'string');
      const firstNumberCol = selectedQueryObj.result.columns.find(c => typeof selectedQueryObj.result.data[0][c] === 'number');
      setXAxisKey(firstStringCol || selectedQueryObj.result.columns[0]);
      setYAxisKey(firstNumberCol || selectedQueryObj.result.columns[1]);
    }
  }, [selectedQueryObj]);

  const handleOpenModal = () => {
    setStep(0);
    setSelectedQueryId('');
    setReportName('');
    setReportType('bar');
    setXAxisKey('');
    setYAxisKey('');
    setIsModalOpen(true);
  };

  const handleCreateReport = () => {
    if (!reportName || !selectedQueryObj) return;
    
    const newReport: Report = {
      id: Date.now().toString(),
      projectId: selectedProjectId,
      name: reportName,
      type: reportType,
      description: `源自查询: ${selectedQueryObj.queryText}`,
      updatedAt: new Date().toISOString().split('T')[0],
      data: selectedQueryObj.result.data,
      chartConfig: {
        xAxisKey,
        yAxisKey
      },
      sourceQueryId: selectedQueryObj.id,
      sourceQueryText: selectedQueryObj.queryText
    };

    setReports([newReport, ...reports]);
    setIsModalOpen(false);
  };

  const handleDelete = (id: string) => {
    if (confirm('确定要删除此报表吗？')) {
      setReports(reports.filter(r => r.id !== id));
    }
  };

  const renderDynamicChart = (report: Report, height: number | string = "100%") => {
    const { type, data, chartConfig } = report;
    const X = chartConfig.xAxisKey;
    const Y = chartConfig.yAxisKey;

    if (!data || data.length === 0) return <div className="text-center text-gray-400">无数据</div>;

    // Common Components
    const CommonGrid = <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />;
    const CommonX = <XAxis dataKey={X} fontSize={11} tickLine={false} axisLine={{stroke: '#e5e7eb'}} />;
    const CommonY = <YAxis fontSize={11} tickLine={false} axisLine={false} />;
    const CommonTooltip = <Tooltip cursor={{fill: '#f9fafb'}} contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)'}} />;

    return (
      <ResponsiveContainer width="100%" height={height as any}>
        {type === 'bar' ? (
          <BarChart data={data}>
            {CommonGrid} {CommonX} {CommonY} {CommonTooltip}
            <Bar dataKey={Y} fill="#1677ff" radius={[4, 4, 0, 0]} barSize={40} name={Y} />
          </BarChart>
        ) : type === 'line' ? (
          <LineChart data={data}>
            {CommonGrid} {CommonX} {CommonY} {CommonTooltip}
            <Line type="monotone" dataKey={Y} stroke="#1677ff" strokeWidth={3} dot={{ r: 4, fill: '#1677ff', strokeWidth: 2, stroke: '#fff' }} activeDot={{ r: 6 }} name={Y} />
          </LineChart>
        ) : type === 'pie' ? (
          <RePieChart>
            <Pie data={data} cx="50%" cy="50%" innerRadius={60} outerRadius={80} fill="#8884d8" paddingAngle={2} dataKey={Y} nameKey={X} label>
              {data.map((entry, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}
            </Pie>
            <Tooltip />
          </RePieChart>
        ) : (
          <ScatterChart>
            {CommonGrid} {CommonX} {CommonY} {CommonTooltip}
            <ZAxis type="number" range={[60, 400]} />
            <Scatter name={Y} data={data} fill="#1677ff" />
          </ScatterChart>
        )}
      </ResponsiveContainer>
    );
  };

  if (projects.length === 0) {
    return <div className="p-8 text-center text-gray-500">请先在仪表盘创建数据库项目。</div>;
  }

  return (
    <div className="p-8 max-w-7xl mx-auto h-full overflow-y-auto">
      {/* Header & Filter */}
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-2xl font-bold text-gray-800">报表生成器</h2>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-white px-3 py-2 rounded-md border border-gray-300 shadow-sm">
            <Filter size={16} className="text-gray-400" />
            <select 
              className="bg-transparent border-none text-sm font-medium text-gray-800 focus:ring-0 cursor-pointer min-w-[120px]"
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
            >
              {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
          <Button variant="primary" icon={<Plus size={16} />} onClick={handleOpenModal}>
            新建报表
          </Button>
        </div>
      </div>

      {/* Reports Grid */}
      <div className="grid grid-cols-1 gap-8">
         {filteredReports.map(report => (
           <Card key={report.id} className="bg-white">
             <div className="flex flex-col h-full">
                {/* Report Toolbar */}
                <div className="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                  <div className="flex items-center gap-4">
                     <div className="flex gap-2">
                        <select 
                          className="text-xs border-gray-300 rounded bg-white py-1 pl-2 pr-6" 
                          value={report.projectId === selectedProjectId ? 'current' : ''} // Mock disabled
                          disabled
                        >
                          <option>{report.name}</option>
                        </select>
                        <div className="flex items-center gap-1 bg-blue-50 text-blue-700 px-2 py-1 rounded text-xs border border-blue-100">
                          <Database size={12} /> 源: {report.sourceQueryText}
                        </div>
                     </div>
                  </div>
                  <div className="flex gap-2">
                     <Button variant="primary" className="h-8 text-xs px-3" icon={<Database size={12}/>}>智能推荐</Button>
                     <Button variant="primary" className="h-8 text-xs px-3" icon={<Download size={12}/>}>导出图表</Button>
                     <div className="flex border border-gray-300 rounded-md overflow-hidden bg-white">
                        <button className="px-3 py-1 text-xs border-r border-gray-200 hover:bg-gray-50 flex items-center gap-1"><BarChart2 size={12}/> 柱状图</button>
                        <button className="px-3 py-1 text-xs border-r border-gray-200 hover:bg-gray-50 flex items-center gap-1"><TrendingUp size={12}/> 折线图</button>
                        <button className="px-3 py-1 text-xs border-r border-gray-200 hover:bg-gray-50 flex items-center gap-1"><PieChart size={12}/> 饼状图</button>
                        <button className="px-3 py-1 text-xs hover:bg-gray-50 flex items-center gap-1"><ScatterChart size={12}/> 散点图</button>
                     </div>
                  </div>
                </div>
                
                <div className="p-6 flex flex-col gap-4">
                   <div className="flex gap-4 mb-2">
                      <div className="flex-1 bg-white border border-gray-200 rounded px-3 py-2 text-sm flex justify-between items-center">
                         <span className="text-gray-500">产品名称</span>
                         <ArrowRight size={14} className="text-gray-300"/>
                      </div>
                      <div className="flex-1 bg-white border border-gray-200 rounded px-3 py-2 text-sm flex justify-between items-center">
                         <span className="text-gray-500">总销量</span>
                         <ArrowRight size={14} className="text-gray-300"/>
                      </div>
                   </div>
                   <div className="h-[500px] w-full">
                      {renderDynamicChart(report)}
                   </div>
                </div>
             </div>
           </Card>
         ))}
      </div>

      {/* Creation Wizard Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="报表生成向导"
        maxWidth="max-w-4xl"
        footer={
          <div className="flex justify-between w-full">
            {step === 1 ? (
              <Button onClick={() => setStep(0)} icon={<ArrowLeft size={16} />}>上一步</Button>
            ) : (
               <div></div> 
            )}
            <div className="flex gap-2">
              <Button onClick={() => setIsModalOpen(false)}>取消</Button>
              {step === 0 ? (
                <Button 
                  variant="primary" 
                  onClick={() => setStep(1)} 
                  disabled={!selectedQueryId}
                  icon={<ArrowRight size={16} />}
                >
                  下一步: 配置图表
                </Button>
              ) : (
                <Button 
                  variant="primary" 
                  onClick={handleCreateReport} 
                  disabled={!reportName || !xAxisKey || !yAxisKey}
                  icon={<Save size={16} />}
                >
                  完成并创建
                </Button>
              )}
            </div>
          </div>
        }
      >
        <div className="mb-6">
           <Steps 
             current={step} 
             steps={[{title: '选择数据源'}, {title: '可视化配置'}]} 
           />
        </div>

        <div className="h-[400px] overflow-y-auto px-1">
          {step === 0 && (
            <div className="space-y-4">
              <p className="text-sm text-gray-600">请从历史查询记录中选择一条作为报表的数据来源。</p>
              <div className="space-y-3">
                {availableQueries.map(q => (
                  <div 
                    key={q.id}
                    onClick={() => setSelectedQueryId(q.id)}
                    className={`p-4 border rounded-xl cursor-pointer transition-all hover:shadow-md ${
                      selectedQueryId === q.id 
                        ? 'border-primary bg-blue-50 ring-1 ring-primary' 
                        : 'border-gray-200 bg-white hover:border-blue-200'
                    }`}
                  >
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-bold text-gray-800 flex items-center gap-2">
                        <Database size={14} className="text-primary" />
                        {q.queryText}
                      </span>
                      <span className="text-xs text-gray-400">{q.timestamp}</span>
                    </div>
                    
                    {/* Data Preview (Mini Table) */}
                    <div className="bg-white/60 rounded border border-gray-200 overflow-hidden text-xs">
                       <div className="flex border-b border-gray-100 bg-gray-50 text-gray-500">
                         {q.result.columns.slice(0, 4).map(c => (
                           <div key={c} className="flex-1 px-2 py-1 truncate">{c}</div>
                         ))}
                       </div>
                       <div className="flex text-gray-700">
                          {q.result.columns.slice(0, 4).map(c => (
                            <div key={c} className="flex-1 px-2 py-1 truncate">{q.result.data[0][c]}</div>
                          ))}
                       </div>
                    </div>
                  </div>
                ))}
                {availableQueries.length === 0 && (
                   <div className="text-center py-10 text-gray-400 border border-dashed rounded-lg">
                     该项目下暂无历史查询记录，请先去工作台执行查询。
                   </div>
                )}
              </div>
            </div>
          )}

          {step === 1 && selectedQueryObj && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
               {/* Left: Config Panel */}
               <div className="col-span-1 space-y-4 border-r border-gray-100 pr-4">
                  <Input 
                    label="报表名称" 
                    value={reportName}
                    onChange={(e) => setReportName(e.target.value)}
                  />
                  
                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-1.5 block">图表类型</label>
                    <div className="grid grid-cols-2 gap-2">
                      {[
                        { id: 'bar', label: '柱状图', icon: <BarChart2 size={14}/> },
                        { id: 'line', label: '折线图', icon: <TrendingUp size={14}/> },
                        { id: 'pie', label: '饼图', icon: <PieChart size={14}/> },
                        { id: 'scatter', label: '散点图', icon: <ScatterChart size={14}/> },
                      ].map(t => (
                        <div 
                          key={t.id}
                          onClick={() => setReportType(t.id as ReportType)}
                          className={`flex items-center gap-2 px-3 py-2 rounded border cursor-pointer text-xs transition-colors ${
                            reportType === t.id ? 'bg-primary text-white border-primary' : 'bg-white text-gray-600 hover:bg-gray-50'
                          }`}
                        >
                          {t.icon} {t.label}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-1.5 block">X 轴 (分类/维度)</label>
                    <select 
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-100 focus:border-primary outline-none"
                      value={xAxisKey}
                      onChange={(e) => setXAxisKey(e.target.value)}
                    >
                      {selectedQueryObj.result.columns.map(col => (
                        <option key={col} value={col}>{col}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-1.5 block">Y 轴 (数值/指标)</label>
                    <select 
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-100 focus:border-primary outline-none"
                      value={yAxisKey}
                      onChange={(e) => setYAxisKey(e.target.value)}
                    >
                      {selectedQueryObj.result.columns.map(col => (
                        <option key={col} value={col}>{col}</option>
                      ))}
                    </select>
                  </div>
               </div>

               {/* Right: Preview */}
               <div className="col-span-2 bg-gray-50 rounded-xl border border-gray-200 p-4 flex flex-col">
                  <div className="text-xs font-bold text-gray-500 uppercase mb-2 flex justify-between">
                    <span>Preview</span>
                    <span>{selectedQueryObj.queryText}</span>
                  </div>
                  <div className="flex-1 bg-white rounded-lg border border-gray-200 shadow-sm p-2">
                    {renderDynamicChart({
                      id: 'preview',
                      projectId: '',
                      name: reportName,
                      type: reportType,
                      description: '',
                      updatedAt: '',
                      sourceQueryId: '',
                      sourceQueryText: '',
                      data: selectedQueryObj.result.data,
                      chartConfig: { xAxisKey, yAxisKey }
                    }, "100%")}
                  </div>
               </div>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
};
