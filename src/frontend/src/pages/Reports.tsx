import React, { useState, useMemo, useEffect } from 'react';
import { Project, Report, ReportType } from '../types.ts';
import { Card, Button, Modal, Input, Tag, Steps } from '../components/UI.tsx';
import { Plus, BarChart2, PieChart, TrendingUp, Download, Trash2, Edit2, Filter, Database, Table as TableIcon, ScatterChart, ArrowRight, ArrowLeft, Save, Loader2 } from 'lucide-react'; // 引入 Loader2
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart as RePieChart, Pie, Cell, ScatterChart as ReScatterChart, Scatter, ZAxis } from 'recharts';
import { reportApi, HistoryQuery } from '../api/reports.ts'; // 导入 API
import { fetchProjects, ProjectDTO } from '../api/project.ts';

interface ReportsProps {
  projects?: Project[];
}

const COLORS = ['#1677ff', '#52c41a', '#faad14', '#ff4d4f', '#722ed1', '#13c2c2'];

export const Reports: React.FC<ReportsProps> = ({ projects }) => {
  const [availableProjects, setAvailableProjects] = useState<Project[]>(projects || []);
  const [selectedProjectId, setSelectedProjectId] = useState<string>((projects || [])[0]?.id || '');

  const mapProjectDTOToProject = (projectDTO: ProjectDTO): Project => {
    const dbTypeMap: Record<string, 'MySQL' | 'PostgreSQL' | 'SQLite'> = {
      mysql: 'MySQL',
      postgresql: 'PostgreSQL',
      sqlite: 'SQLite'
    };

    const statusMap: Record<string, 'active' | 'deploying' | 'error' | 'deleted'> = {
      initializing: 'deploying',
      pending_confirmation: 'deploying',
      active: 'active',
      deleted: 'deleted',
      error: 'error'
    };

    return {
      id: projectDTO.project_id.toString(),
      name: projectDTO.project_name,
      type: dbTypeMap[(projectDTO.db_type || '').toLowerCase()] || 'MySQL',
      description: projectDTO.description,
      status: statusMap[(projectDTO.project_status || '').toLowerCase()] || 'active',
      createdAt: projectDTO.created_at
    };
  };

  // 若未传入项目（或为空），从后端拉取用户真实项目列表
  useEffect(() => {
    const ensureProjects = async () => {
      if (projects && projects.length > 0) {
        setAvailableProjects(projects);
        if (!selectedProjectId) setSelectedProjectId(projects[0].id);
        return;
      }

      try {
        const dtos = await fetchProjects();
        const mapped = (dtos || []).map(mapProjectDTOToProject);
        setAvailableProjects(mapped);
        if (!selectedProjectId && mapped.length > 0) setSelectedProjectId(mapped[0].id);
      } catch (error) {
        console.error('Failed to load projects for reports:', error);
      }
    };

    ensureProjects();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projects]);

  // State: API Data
  const [reports, setReports] = useState<Report[]>([]);
  const [historyQueries, setHistoryQueries] = useState<HistoryQuery[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // State: UI
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [step, setStep] = useState(0);
  const [selectedQueryId, setSelectedQueryId] = useState<string>('');

  // Delete confirm modal
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [deleteReportId, setDeleteReportId] = useState<string>('');

  // Form State
  const [reportName, setReportName] = useState('');
  const [reportType, setReportType] = useState<ReportType>('bar');
  const [xAxisKey, setXAxisKey] = useState('');
  const [yAxisKey, setYAxisKey] = useState('');

  // --- API: Load Reports ---
  const fetchReports = async (projectId: string) => {
    if (!projectId) return;
    setIsLoading(true);
    try {
      const data = await reportApi.getReports(projectId);
      setReports(data);
    } catch (error) {
      console.error("Failed to fetch reports", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchReports(selectedProjectId);
  }, [selectedProjectId]);

  // --- API: Load Queries (Lazy load when modal opens) ---
  useEffect(() => {
    if (isModalOpen && selectedProjectId) {
      reportApi.getHistoryQueries(selectedProjectId).then(data => {
        setHistoryQueries(data);
      });
    }
  }, [isModalOpen, selectedProjectId]);

  const selectedQueryObj = historyQueries.find(q => q.id === selectedQueryId);

  // Initialize form when query changes
  useMemo(() => {
    if (selectedQueryObj) {
      if (!reportName) setReportName(selectedQueryObj.queryText + ' 报表');

      const columns = selectedQueryObj.result?.columns || [];
      const fields = selectedQueryObj.result?.fields || [];

      // X：优先 string/date；Y：仅 number（避免图表数值轴报错）
      const xCandidate = fields.find(f => f.type === 'string' || f.type === 'date')?.name;
      const yCandidate = fields.find(f => f.type === 'number')?.name;

      setXAxisKey(xCandidate || columns[0] || '');
      setYAxisKey(yCandidate || columns[1] || columns[0] || '');
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

  // --- API: Create Report ---
  const handleCreateReport = async () => {
    if (!reportName || !selectedQueryObj) return;

    setIsSaving(true);
    try {
      await reportApi.createReport({
        projectId: selectedProjectId,
        name: reportName,
        type: reportType,
        description: `源自查询: ${selectedQueryObj.queryText}`,
        chartConfig: { xAxisKey, yAxisKey },
        sourceQueryId: selectedQueryObj.id
      });

      // 刷新列表
      await fetchReports(selectedProjectId);
      setIsModalOpen(false);
    } catch (error) {
      alert('创建失败'); // 实际项目中建议使用 Toast
      console.error(error);
    } finally {
      setIsSaving(false);
    }
  };

  // --- API: Delete Report ---
  const handleDelete = async (id: string) => {
    setDeleteReportId(id);
    setIsDeleteModalOpen(true);
  };

  const confirmDelete = async () => {
    if (!deleteReportId) return;
    try {
      await reportApi.deleteReport(deleteReportId);
      setReports(prev => prev.filter(r => r.id !== deleteReportId));
      setIsDeleteModalOpen(false);
      setDeleteReportId('');
    } catch (error) {
      console.error("Delete failed", error);
    }
  };

  const renderDynamicChart = (report: Partial<Report>, height: number | string = "100%") => {
    const { type, data, chartConfig } = report;
    const X = chartConfig?.xAxisKey || '';
    const Y = chartConfig?.yAxisKey || '';

    if (!data || data.length === 0) return <div className="text-center text-gray-400">无数据</div>;

    const CommonGrid = <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />;
    const xValue = (data?.[0] as any)?.[X];
    const yValue = (data?.[0] as any)?.[Y];

    const xIsNumber = typeof xValue === 'number';
    const yIsNumber = typeof yValue === 'number';

    const CommonX = (
      <XAxis
        dataKey={X}
        type={xIsNumber ? 'number' : 'category'}
        fontSize={11}
        tickLine={false}
        axisLine={{ stroke: '#e5e7eb' }}
      />
    );
    const CommonY = (
      <YAxis
        dataKey={Y}
        type={yIsNumber ? 'number' : 'category'}
        fontSize={11}
        tickLine={false}
        axisLine={false}
      />
    );
    const CommonTooltip = <Tooltip cursor={{ fill: '#f9fafb' }} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />;

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
              {data.map((entry: any, index: number) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}
            </Pie>
            <Tooltip />
          </RePieChart>
        ) : (
          <ReScatterChart>
            {CommonGrid} {CommonX} {CommonY} {CommonTooltip}
            <ZAxis type="number" range={[60, 400]} />
            <Scatter name={Y} data={data} fill="#1677ff" />
          </ReScatterChart>
        )}
      </ResponsiveContainer>
    );
  };

  if (availableProjects.length === 0) {
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
              {availableProjects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
          <Button variant="primary" icon={<Plus size={16} />} onClick={handleOpenModal}>
            新建报表
          </Button>
        </div>
      </div>

      {/* Reports Grid */}
      {isLoading ? (
        <div className="flex justify-center items-center h-64">
          <Loader2 className="animate-spin text-primary" size={32} />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-8">
          {reports.length === 0 && (
            <div className="text-center py-20 bg-gray-50 rounded-xl border border-dashed border-gray-300">
              <BarChart2 size={48} className="mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">该项目下暂无报表，点击右上角创建。</p>
            </div>
          )}
          {reports.map(report => (
            <Card key={report.id} className="bg-white group">
              <div className="flex flex-col h-full">
                {/* Report Toolbar */}
                <div className="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                  <div className="flex items-center gap-4">
                    <span className="font-bold text-gray-700">{report.name}</span>
                    <div className="flex items-center gap-1 bg-blue-50 text-blue-700 px-2 py-1 rounded text-xs border border-blue-100">
                      <Database size={12} /> 源: {report.sourceQueryText}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="text"
                      className="h-8 text-xs px-2 text-red-500 hover:bg-red-50"
                      icon={<Trash2 size={14} />}
                      onClick={() => handleDelete(report.id)}
                    />
                  </div>
                </div>

                <div className="p-6 flex flex-col gap-4">
                  <div className="h-[400px] w-full">
                    {renderDynamicChart(report)}
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

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
                  disabled={!reportName || !xAxisKey || !yAxisKey || isSaving}
                  icon={isSaving ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
                >
                  {isSaving ? '创建中...' : '完成并创建'}
                </Button>
              )}
            </div>
          </div>
        }
      >
        <div className="mb-6">
          <Steps
            current={step}
            steps={[{ title: '选择数据源' }, { title: '可视化配置' }]}
          />
        </div>

        <div className="h-[400px] overflow-y-auto px-1">
          {step === 0 && (
            <div className="space-y-4">
              <p className="text-sm text-gray-600">请从历史查询记录中选择一条作为报表的数据来源。</p>
              <div className="space-y-3">
                {historyQueries.map(q => (
                  <div
                    key={q.id}
                    onClick={() => setSelectedQueryId(q.id)}
                    className={`p-4 border rounded-xl cursor-pointer transition-all hover:shadow-md ${selectedQueryId === q.id
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

                    {/* Data Preview */}
                    <div className="bg-white/60 rounded border border-gray-200 overflow-hidden text-xs">
                      <div className="flex border-b border-gray-100 bg-gray-50 text-gray-500">
                        {(q.result?.columns || []).slice(0, 4).map((c: string) => (
                          <div key={c} className="flex-1 px-2 py-1 truncate">{c}</div>
                        ))}
                      </div>
                      <div className="flex text-gray-700">
                        {(q.result?.columns || []).slice(0, 4).map((c: string) => (
                          <div key={c} className="flex-1 px-2 py-1 truncate">
                            {q.result?.data?.[0]?.[c] ?? ''}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
                {historyQueries.length === 0 && (
                  <div className="text-center py-10 text-gray-400 border border-dashed rounded-lg">
                    该项目下暂无历史查询记录，请先去工作台执行查询。
                  </div>
                )}
              </div>
            </div>
          )}

          {step === 1 && selectedQueryObj && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
              {/* Config Panel */}
              <div className="col-span-1 space-y-4 border-r border-gray-100 pr-4">
                <Input
                  label="报表名称"
                  value={reportName}
                  onChange={(e) => setReportName(e.target.value)}
                />

                {/* ... (图表类型选择逻辑保持不变，省略以节省空间，直接复用原代码) ... */}
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-1.5 block">图表类型</label>
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      { id: 'bar', label: '柱状图', icon: <BarChart2 size={14} /> },
                      { id: 'line', label: '折线图', icon: <TrendingUp size={14} /> },
                      { id: 'pie', label: '饼图', icon: <PieChart size={14} /> },
                      { id: 'scatter', label: '散点图', icon: <ScatterChart size={14} /> },
                    ].map(t => (
                      <div
                        key={t.id}
                        onClick={() => setReportType(t.id as ReportType)}
                        className={`flex items-center gap-2 px-3 py-2 rounded border cursor-pointer text-xs transition-colors ${reportType === t.id ? 'bg-primary text-white border-primary' : 'bg-white text-gray-600 hover:bg-gray-50'
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
                    {(selectedQueryObj.result?.fields?.length
                      ? selectedQueryObj.result.fields
                      : (selectedQueryObj.result?.columns || []).map((c: string) => ({ name: c, type: 'string' as const }))
                    ).map((f: any) => (
                      <option key={f.name} value={f.name}>{f.name}</option>
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
                    {(
                      (selectedQueryObj.result?.fields || []).filter((f: any) => f.type === 'number')
                    ).length > 0 ? (
                      (selectedQueryObj.result?.fields || []).filter((f: any) => f.type === 'number').map((f: any) => (
                        <option key={f.name} value={f.name}>{f.name}</option>
                      ))
                    ) : (
                      // 兜底：没有 number 字段时仍允许选择列，但预期用户换成折线/柱状会无效
                      (selectedQueryObj.result?.columns || []).map((col: string) => (
                        <option key={col} value={col}>{col}</option>
                      ))
                    )}
                  </select>
                </div>
              </div>

              {/* Preview */}
              <div className="col-span-2 bg-gray-50 rounded-xl border border-gray-200 p-4 flex flex-col">
                <div className="text-xs font-bold text-gray-500 uppercase mb-2 flex justify-between">
                  <span>Preview</span>
                  <span>{selectedQueryObj.queryText}</span>
                </div>
                <div className="flex-1 bg-white rounded-lg border border-gray-200 shadow-sm p-2">
                  {renderDynamicChart({
                    data: selectedQueryObj.result.data,
                    type: reportType,
                    chartConfig: { xAxisKey, yAxisKey }
                  } as any, "100%")}
                </div>
              </div>
            </div>
          )}
        </div>
      </Modal>

      {/* Delete Confirm Modal */}
      <Modal
        isOpen={isDeleteModalOpen}
        onClose={() => {
          setIsDeleteModalOpen(false);
          setDeleteReportId('');
        }}
        title="删除报表"
        maxWidth="max-w-md"
        footer={
          <div className="flex justify-end gap-2 w-full">
            <Button onClick={() => {
              setIsDeleteModalOpen(false);
              setDeleteReportId('');
            }}>取消</Button>
            <Button variant="primary" className="bg-red-500 hover:bg-red-600" onClick={confirmDelete}>
              删除
            </Button>
          </div>
        }
      >
        <div className="text-sm text-gray-600">
          确定要删除此报表吗？该操作不可恢复。
        </div>
      </Modal>
    </div>
  );
};
