import React, { useState, useEffect, useRef } from 'react';
import {
  Plus,
  Search,
  Trash2,
  Download,
  Upload,
  Edit2,
  Book,
  CheckSquare,
  Square,
  Filter,
  Loader2,
  FileText,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  CheckCircle2
} from 'lucide-react';
import { KnowledgeTerm, KnowledgeImportResponse } from '../types.ts';
import { glossaryApi, CreateTermParams } from '../api/glossary.ts';
import { fetchProjects, ProjectDTO } from '../api/project.ts';
import { Button, Input, Modal, Card } from '../components/UI.tsx';

export const Glossary: React.FC = () => {
  // --- 状态管理 ---

  // 项目列表 (从真实 API 获取)
  const [projectList, setProjectList] = useState<ProjectDTO[]>([]);
  const [loadingProjects, setLoadingProjects] = useState(false);

  // 当前选中的项目 ID
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');

  // 术语数据列表
  const [terms, setTerms] = useState<KnowledgeTerm[]>([]);
  const [total, setTotal] = useState(0);
  const [loadingTerms, setLoadingTerms] = useState(false);

  // 筛选与分页
  const [searchQuery, setSearchQuery] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 10; // 紧凑视图，每页 10 条
  const [hasMore, setHasMore] = useState(false);

  // 选中项 (用于批量删除)
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

  // 模态框与表单
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTerm, setEditingTerm] = useState<KnowledgeTerm | null>(null);
  const [formData, setFormData] = useState<CreateTermParams>({
    term: "",
    definition: "",
    examples: ""
  });
  const [isSaving, setIsSaving] = useState(false);

  // 文件导入相关状态
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [importResult, setImportResult] = useState<KnowledgeImportResponse | null>(null);
  const [isImportResultModalOpen, setIsImportResultModalOpen] = useState(false);

  // --- 初始化: 获取真实项目列表 ---
  useEffect(() => {
    const loadProjects = async () => {
      setLoadingProjects(true);
      try {
        const data = await fetchProjects();
        setProjectList(data);
        // 如果当前没有选中项目且获取到了项目列表，默认选中第一个
        if (data.length > 0 && !selectedProjectId) {
          setSelectedProjectId(data[0].project_id);
        }
      } catch (error) {
        console.error("Failed to fetch projects", error);
      } finally {
        setLoadingProjects(false);
      }
    };
    loadProjects();
  }, []);

  // --- 获取术语列表 (依赖 selectedProjectId) ---
  useEffect(() => {
    if (selectedProjectId) {
      fetchTerms();
      setSelectedIds(new Set()); // 切换项目时清空选中
    } else {
      setTerms([]); // 无项目时清空列表
    }
  }, [selectedProjectId, page, searchQuery]);

  const fetchTerms = async () => {
    if (!selectedProjectId) return;
    setLoadingTerms(true);
    try {
      const res = await glossaryApi.getList(selectedProjectId, page, pageSize, searchQuery || undefined);
      setTerms(res.items);
      setTotal(res.total);
      setHasMore(page * pageSize < res.total);
    } catch (error) {
      console.error("Failed to fetch terms", error);
    } finally {
      setLoadingTerms(false);
    }
  };

  // --- 交互处理 ---

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>, field: keyof CreateTermParams) => {
    setFormData(prev => ({ ...prev, [field]: e.target.value }));
  };

  const openModal = (termToEdit?: KnowledgeTerm) => {
    if (termToEdit) {
      setEditingTerm(termToEdit);
      setFormData({
        term: termToEdit.term,
        definition: termToEdit.definition,
        examples: termToEdit.examples || ""
      });
    } else {
      setEditingTerm(null);
      setFormData({ term: "", definition: "", examples: "" });
    }
    setIsModalOpen(true);
  };

  const handleSave = async () => {
    if (!selectedProjectId) {
      alert("请先选择一个项目");
      return;
    }
    if (!formData.term.trim() || !formData.definition.trim()) {
      alert("术语名称和定义不能为空");
      return;
    }

    setIsSaving(true);
    try {
      if (editingTerm) {
        // 更新
        await glossaryApi.update(selectedProjectId, editingTerm.knowledge_id, formData);
      } else {
        // 创建
        await glossaryApi.create(selectedProjectId, formData);
      }
      setIsModalOpen(false);
      fetchTerms(); // 刷新列表
    } catch (error: any) {
      console.error("Save failed", error);

      // 错误处理: 优先展示后端返回的 detail 信息
      const backendDetail = error.response?.data?.detail;
      const displayMsg = typeof backendDetail === 'string'
        ? backendDetail
        : (error.message || "保存失败，请重试");

      alert(displayMsg);
    } finally {
      setIsSaving(false);
    }
  };

  const handleBatchDelete = async () => {
    if (selectedIds.size === 0) return;
    if (!confirm(`确定要删除选中的 ${selectedIds.size} 个术语吗？`)) return;

    try {
      const idsArray = Array.from(selectedIds);
      const res = await glossaryApi.deleteBatch(selectedProjectId, idsArray);

      alert(`删除成功。成功: ${res.imported_count || selectedIds.size}, 失败: ${res.failed_count || 0}`);
      setSelectedIds(new Set());
      fetchTerms();
    } catch (error: any) {
      alert("删除失败");
    }
  };

  const toggleSelection = (id: number) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (selectedIds.size === terms.length && terms.length > 0) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(terms.map(t => t.knowledge_id)));
    }
  };

  // --- 导入导出 ---

  const handleExport = async () => {
    if (!selectedProjectId) return;
    try {
      const res = await glossaryApi.exportTerms(selectedProjectId);
      if (res.download_url) {
        window.open(res.download_url, '_blank');
      } else {
        alert("导出失败，未获取到下载链接");
      }
    } catch (error) {
      alert("导出请求失败");
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const fileName = file.name.toLowerCase();
    const validExtensions = ['.csv', '.xlsx', '.xls'];
    if (!validExtensions.some(ext => fileName.endsWith(ext))) {
      alert("文件格式不支持：请上传 Excel (.xlsx/.xls) 或 CSV 文件");
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    if (!selectedProjectId) {
      alert("请先选择项目");
      return;
    }

    setIsImporting(true);
    try {
      const res = await glossaryApi.importTerms(selectedProjectId, file);
      // 设置导入结果并打开结果模态框，替代 alert
      setImportResult(res);
      setIsImportResultModalOpen(true);

      if (res.imported_count > 0) {
        fetchTerms();
      }
    } catch (error: any) {
      alert(error.message || "导入失败");
    } finally {
      setIsImporting(false);
      if (fileInputRef.current) fileInputRef.current.value = ''; // 重置 input
    }
  };

  // --- 渲染 ---

  if (loadingProjects && projectList.length === 0) {
    return (
      <div className="flex justify-center items-center h-full">
        <Loader2 className="animate-spin text-primary" size={32} />
        <span className="ml-2 text-gray-500">加载项目列表...</span>
      </div>
    );
  }

  if (projectList.length === 0) {
    return <div className="p-8 text-center text-gray-500">您暂无数据库项目，请先在项目概览中创建。</div>;
  }

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="p-8 max-w-7xl mx-auto h-full flex flex-col overflow-hidden">
      {/* 头部与操作栏 - 固定在顶部 */}
      <div className="flex-shrink-0 flex flex-col gap-6 mb-4">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
            <Book className="text-primary" /> 业务术语表 (Glossary)
          </h2>
          {/* 项目选择器 (绑定真实数据) */}
          <div className="flex items-center gap-2 bg-white px-3 py-2 rounded-md border border-gray-300 shadow-sm">
            <Filter size={16} className="text-gray-400" />
            <select
              className="bg-transparent border-none text-sm font-medium text-gray-800 focus:ring-0 cursor-pointer min-w-[150px] outline-none"
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
            >
              {projectList.map(p => (
                <option key={p.project_id} value={p.project_id}>{p.project_name}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-between items-center bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
          <div className="relative w-full sm:w-96">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-4 w-4 text-gray-400" />
            </div>
            <input
              type="text"
              className="block w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-1 focus:ring-primary focus:border-primary outline-none transition-colors"
              placeholder="搜索术语名称..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && setPage(1)} // 回车重置页码
            />
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
            {selectedIds.size > 0 && (
              <Button
                variant="danger"
                onClick={handleBatchDelete}
                icon={<Trash2 size={16} />}
                className="h-9 text-xs"
              >
                删除 ({selectedIds.size})
              </Button>
            )}
            <div className="h-6 w-px bg-gray-200 hidden sm:block"></div>

            <Button variant="default" onClick={handleExport} icon={<Download size={16} />} className="h-9 text-xs hidden sm:flex">
              导出 (Excel/CSV)
            </Button>

            <Button
              variant="default"
              onClick={() => fileInputRef.current?.click()}
              icon={isImporting ? <Loader2 className="animate-spin" size={16} /> : <Upload size={16} />}
              disabled={isImporting}
              className="h-9 text-xs hidden sm:flex"
            >
              {isImporting ? '导入中' : '导入 (Excel/CSV)'}
            </Button>
            {/* 更新 accept 属性，允许选择 Excel 文件 */}
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              className="hidden"
              accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"
            />

            <Button variant="primary" onClick={() => openModal()} icon={<Plus size={16} />} className="h-9 text-xs">
              新增术语
            </Button>
          </div>
        </div>
      </div>

      {/* 列表内容区 - 可滚动 */}
      <div className="flex-1 overflow-y-auto min-h-0 pr-1">
        {loadingTerms && terms.length === 0 ? (
          <div className="flex justify-center items-center h-64">
            <Loader2 className="animate-spin text-primary" size={32} />
          </div>
        ) : terms.length === 0 ? (
          <div className="text-center py-20 bg-gray-50 rounded-xl border border-dashed border-gray-300">
            <Book size={48} className="mx-auto text-gray-300 mb-4" />
            <h3 className="text-gray-900 font-medium">暂无业务术语</h3>
            <p className="text-gray-500 text-sm mt-1">当前项目下还没有定义任何业务术语。</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3 pb-4">
            {/* 全选控制 */}
            <div className="flex items-center gap-3 px-2 text-sm text-gray-500">
              <button onClick={toggleAll} className="flex items-center gap-2 hover:text-primary">
                {selectedIds.size === terms.length && terms.length > 0 ? <CheckSquare size={16} className="text-primary" /> : <Square size={16} />}
                全选本页
              </button>
              <span>共 {total} 条记录</span>
            </div>

            {terms.map((term) => (
              <Card key={term.knowledge_id} className={`transition-all duration-200 group border-l-4 ${selectedIds.has(term.knowledge_id) ? 'border-l-primary bg-blue-50/30' : 'border-l-transparent hover:border-l-primary'}`}>
                <div className="p-3 flex gap-3">
                  <div className="pt-1">
                    <button
                      onClick={() => toggleSelection(term.knowledge_id)}
                      className="text-gray-400 hover:text-primary focus:outline-none transition-colors"
                    >
                      {selectedIds.has(term.knowledge_id) ? (
                        <CheckSquare className="h-5 w-5 text-primary" />
                      ) : (
                        <Square className="h-5 w-5" />
                      )}
                    </button>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0 pr-4">
                        <h3 className="text-base font-bold text-gray-900 group-hover:text-primary transition-colors flex items-center gap-2 truncate">
                          {term.term}
                        </h3>
                        <p className="mt-1 text-gray-600 leading-snug text-sm line-clamp-2">
                          <span className="font-semibold text-gray-400 text-xs mr-2">定义</span>
                          {term.definition}
                        </p>
                        {term.examples && (
                          <div className="mt-1.5 flex gap-2 items-start text-xs text-gray-500">
                            <FileText size={12} className="mt-0.5 shrink-0 text-gray-400" />
                            <div className="line-clamp-1">
                              <span className="text-gray-400">示例：</span>
                              {term.examples}
                            </div>
                          </div>
                        )}
                      </div>

                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                        <button
                          onClick={() => openModal(term)}
                          className="p-1.5 text-gray-400 hover:text-primary hover:bg-blue-50 rounded-full transition-all"
                          title="编辑"
                        >
                          <Edit2 size={14} />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* 分页控制栏 - 固定在底部 */}
      {total > 0 && (
        <div className="flex-shrink-0 pt-4 border-t border-gray-200 mt-2 bg-white">
          <div className="flex justify-between items-center">
            <div className="text-xs text-gray-500">
              显示第 {(page - 1) * pageSize + 1} 到 {Math.min(page * pageSize, total)} 条，共 {total} 条
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="default"
                disabled={page <= 1}
                onClick={() => setPage(p => p - 1)}
                className="h-8 px-2"
              >
                <ChevronLeft size={14} />
              </Button>

              <span className="text-sm text-gray-600 font-medium px-2">
                {page} / {totalPages}
              </span>

              <Button
                variant="default"
                disabled={page >= totalPages}
                onClick={() => setPage(p => p + 1)}
                className="h-8 px-2"
              >
                <ChevronRight size={14} />
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* 1. 新增/编辑 模态框 */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingTerm ? "编辑业务术语" : "新增业务术语"}
        footer={
          <>
            <Button onClick={() => setIsModalOpen(false)}>取消</Button>
            <Button variant="primary" onClick={handleSave} disabled={isSaving}>
              {isSaving ? '保存中...' : '保存'}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input
            label="术语名称"
            value={formData.term}
            onChange={(e) => handleInputChange(e, 'term')}
            placeholder="例如：GMV"
            required
          />
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-gray-700">定义描述 <span className="text-red-500"></span></label>
            <textarea
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-colors min-h-[100px] text-sm"
              value={formData.definition}
              onChange={(e) => handleInputChange(e, 'definition')}
              placeholder="请详细描述该术语的业务含义..."
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-gray-700">使用示例 (可选)</label>
            <textarea
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-colors min-h-[60px] text-sm"
              value={formData.examples || ''}
              onChange={(e) => handleInputChange(e, 'examples')}
              placeholder="例如：2023年第一季度的GMV统计..."
            />
          </div>
        </div>
      </Modal>

      {/* 2. 导入结果模态框 */}
      <Modal
        isOpen={isImportResultModalOpen}
        onClose={() => setIsImportResultModalOpen(false)}
        title="文件导入结果"
        maxWidth="max-w-lg"
        footer={
          <Button onClick={() => setIsImportResultModalOpen(false)}>关闭</Button>
        }
      >
        {importResult && (
          <div className="space-y-4">
            <div className="flex gap-6 text-sm mb-2">
              <div className="flex items-center gap-2 text-green-700">
                <CheckCircle2 size={18} />
                <span className="font-medium">成功: {importResult.imported_count}</span>
              </div>
              <div className="flex items-center gap-2 text-red-700">
                <AlertCircle size={18} />
                <span className="font-medium">失败: {importResult.failed_count}</span>
              </div>
            </div>

            {/* 失败列表 */}
            {importResult.failed_count > 0 && (
              <div className="bg-red-50 border border-red-100 rounded-lg overflow-hidden">
                <div className="px-4 py-2 bg-red-100/50 border-b border-red-100 text-xs font-bold text-red-800 uppercase tracking-wide">
                  错误详情 ({importResult.failed_count} 条)
                </div>
                <div className="max-h-[240px] overflow-y-auto p-0">
                  <ul className="divide-y divide-red-100">
                    {importResult.failures.map((fail, idx) => (
                      <li key={idx} className="px-4 py-3 text-xs text-red-800 flex gap-3 hover:bg-red-100/30 transition-colors">
                        <span className="font-mono bg-white border border-red-200 px-1.5 py-0.5 rounded text-red-600 shrink-0 h-fit">
                          Row {fail.row}
                        </span>
                        <span className="leading-relaxed">{fail.error}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* 全部成功提示 */}
            {importResult.failed_count === 0 && (
              <div className="text-center py-8 text-gray-500 bg-green-50 rounded-lg border border-green-100 border-dashed">
                <p className="text-green-700 font-medium">文件中的所有数据均已成功导入。</p>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};