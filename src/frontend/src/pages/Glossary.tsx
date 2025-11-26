import React, { useState, useRef, useEffect } from 'react';
import { Project, GlossaryTerm } from '../types'; // 保持引用
import { Card, Button, Input, Modal, Tag } from '../components/UI'; // 保持引用
import { Database, Plus, Search, FileUp, FileDown, Trash2, Edit2, Book, Filter, AlertCircle, Loader2 } from 'lucide-react';
// 【引入 API】
import { getTerms, createTerm, updateTerm, deleteTerm } from '../api/glossary';

interface GlossaryProps {
  projects: Project[];
}

export const Glossary: React.FC<GlossaryProps> = ({ projects }) => {
  const [selectedProjectId, setSelectedProjectId] = useState<string>(projects[0]?.id || '');
  const [terms, setTerms] = useState<GlossaryTerm[]>([]); // 初始为空，等待 API 加载
  const [loading, setLoading] = useState(false); // 加载状态

  const [searchTerm, setSearchTerm] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  // Form State
  const [termName, setTermName] = useState('');
  const [definition, setDefinition] = useState('');
  const [synonyms, setSynonyms] = useState('');

  const fileInputRef = useRef<HTMLInputElement>(null);

  // --- 核心逻辑变更：数据获取 ---
  const fetchGlossaryList = async () => {
    if (!selectedProjectId) return;
    setLoading(true);
    try {
      const res = await getTerms(selectedProjectId);
      // 根据 client.ts 的拦截器，res 实际上是 response.data
      // 假设 Mock 返回结构为 { code: 200, data: [...] }
      if (res && res.code === 200) {
        setTerms(res.data);
      }
    } catch (error) {
      console.error("Failed to fetch terms:", error);
    } finally {
      setLoading(false);
    }
  };

  // 监听 projectId 变化，自动刷新列表
  useEffect(() => {
    fetchGlossaryList();
  }, [selectedProjectId]);

  // 前端过滤 (搜索功能通常建议后端做，但在数据量小时前端做体验更好)
  const filteredTerms = terms.filter(t =>
    t.term.toLowerCase().includes(searchTerm.toLowerCase()) || t.definition.includes(searchTerm)
  );

  const handleOpenModal = (term?: GlossaryTerm) => {
    if (term) {
      setEditingId(term.id);
      setTermName(term.term);
      setDefinition(term.definition);
      setSynonyms(term.synonyms?.join(', ') || '');
    } else {
      setEditingId(null);
      setTermName('');
      setDefinition('');
      setSynonyms('');
    }
    setIsModalOpen(true);
  };

  // --- 核心逻辑变更：保存 ---
  const handleSave = async () => {
    if (!termName || !selectedProjectId) return;

    const synonymArray = synonyms.split(/[,，]/).map(s => s.trim()).filter(Boolean);

    try {
      if (editingId) {
        // 更新逻辑
        await updateTerm(editingId, {
          id: editingId, // 确保传给后端 ID
          term: termName,
          definition,
          synonyms: synonymArray,
          projectId: selectedProjectId
        });
      } else {
        // 新增逻辑
        await createTerm({
          projectId: selectedProjectId,
          term: termName,
          definition,
          synonyms: synonymArray,
          // relatedTable: '' // 如果有相关表字段可在此添加
        });
      }

      setIsModalOpen(false);
      fetchGlossaryList(); // 操作成功后刷新列表
    } catch (error) {
      alert('保存失败，请检查网络或重试');
    }
  };

  // --- 核心逻辑变更：删除 ---
  const handleDelete = async (id: string) => {
    if (confirm('确定要删除此术语吗？')) {
      try {
        await deleteTerm(id);
        fetchGlossaryList(); // 刷新列表
      } catch (error) {
        alert('删除失败');
      }
    }
  };

  // --- 导出功能 (保持前端逻辑即可，导出的是当前视图的数据) ---
  const handleExport = () => {
    const exportData = filteredTerms.map(({ id, ...rest }) => rest);
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `glossary_project_${selectedProjectId}_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // --- 导入功能 (改为解析 JSON 后循环调用 API 创建接口) ---
  const handleImportClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const content = e.target?.result as string;
        const importedData = JSON.parse(content);

        if (!Array.isArray(importedData)) throw new Error("Invalid format: expected array");

        // 简单的批量导入逻辑：循环调用 create 接口
        // 在实际生产中，建议后端提供一个 /batch-import 接口
        let successCount = 0;
        for (const item of importedData) {
          await createTerm({
            projectId: selectedProjectId,
            term: item.term || 'Untitled',
            definition: item.definition || '',
            synonyms: item.synonyms || [],
            relatedTable: item.relatedTable
          });
          successCount++;
        }

        alert(`成功导入 ${successCount} 条术语`);
        fetchGlossaryList(); // 刷新
      } catch (error) {
        alert('导入失败：文件格式错误或网络异常');
        console.error(error);
      } finally {
        if (fileInputRef.current) fileInputRef.current.value = '';
      }
    };
    reader.readAsText(file);
  };

  if (projects.length === 0) {
    return <div className="p-8 text-center text-gray-500">请先在仪表盘创建数据库项目。</div>;
  }

  return (
    <div className="p-8 max-w-7xl mx-auto h-full overflow-y-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
            <Book className="text-primary" /> 业务术语库
          </h2>
          <p className="text-gray-500 mt-1">统一业务名词定义，提升AI理解准确度</p>
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-2 bg-white px-3 py-2 rounded-md border border-gray-300 shadow-sm">
            <Filter size={16} className="text-gray-400" />
            <span className="text-sm text-gray-600 whitespace-nowrap">所属项目:</span>
            <select
              className="bg-transparent border-none text-sm font-medium text-gray-800 focus:ring-0 cursor-pointer min-w-[120px]"
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
            >
              {projects.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          <div className="relative grow md:grow-0">
            <input
              type="text"
              placeholder="搜索术语..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 pr-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-primary focus:border-primary w-full md:w-48"
            />
            <Search className="absolute left-3 top-2.5 text-gray-400" size={16} />
          </div>

          <div className="flex gap-2">
            <input type="file" ref={fileInputRef} className="hidden" accept=".json" onChange={handleFileChange} />
            <Button variant="default" className="px-3" icon={<FileUp size={16} />} title="导入 JSON" onClick={handleImportClick} />
            <Button variant="default" className="px-3" icon={<FileDown size={16} />} title="导出 JSON" onClick={handleExport} />
            <Button variant="primary" icon={<Plus size={16} />} onClick={() => handleOpenModal()}>
              新增术语
            </Button>
          </div>
        </div>
      </div>

      <Card className="p-0 overflow-hidden min-h-[400px]">
        {loading ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-400">
            <Loader2 className="animate-spin mb-2" size={32} />
            <p>加载数据中...</p>
          </div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-4 font-medium text-gray-600 w-1/5">术语名称</th>
                <th className="px-6 py-4 font-medium text-gray-600 w-2/5">定义描述</th>
                <th className="px-6 py-4 font-medium text-gray-600 w-1/5">同义词</th>
                <th className="px-6 py-4 font-medium text-gray-600">关联表</th>
                <th className="px-6 py-4 font-medium text-gray-600 text-right">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredTerms.map(term => (
                <tr key={term.id} className="hover:bg-gray-50/50">
                  <td className="px-6 py-4 font-bold text-gray-800">{term.term}</td>
                  <td className="px-6 py-4 text-gray-600">{term.definition}</td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1">
                      {term.synonyms?.map((s, i) => (
                        <Tag key={i} color="blue">{s}</Tag>
                      ))}
                      {!term.synonyms?.length && <span className="text-gray-300">-</span>}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-gray-500">
                    {term.relatedTable ? (
                      <span className="flex items-center gap-1 font-mono text-xs bg-gray-100 px-2 py-1 rounded w-fit">
                        <Database size={10} /> {term.relatedTable}
                      </span>
                    ) : <span className="text-gray-300">-</span>}
                  </td>
                  <td className="px-6 py-4 text-right flex justify-end gap-2">
                    <button onClick={() => handleOpenModal(term)} className="p-1 text-gray-400 hover:text-primary transition-colors">
                      <Edit2 size={16} />
                    </button>
                    <button onClick={() => handleDelete(term.id)} className="p-1 text-gray-400 hover:text-red-500 transition-colors">
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
              {filteredTerms.length === 0 && (
                <tr>
                  <td colSpan={5} className="text-center py-12 text-gray-400">
                    {searchTerm ? '未找到匹配的术语' : '暂无术语，请点击右上角添加或导入'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </Card>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingId ? "编辑业务术语" : "新增业务术语"}
        footer={
          <>
            <Button onClick={() => setIsModalOpen(false)}>取消</Button>
            <Button variant="primary" onClick={handleSave}>保存</Button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="bg-blue-50 p-3 rounded-lg flex items-start gap-2 text-xs text-blue-800 mb-4">
            <AlertCircle size={14} className="mt-0.5" />
            <p>定义好的术语将被 AI 优先用于理解您的自然语言查询，请确保定义准确。</p>
          </div>
          <Input
            label="术语名称"
            placeholder="例如：DAU"
            value={termName}
            onChange={(e) => setTermName(e.target.value)}
          />
          <Input
            label="同义词 (用逗号分隔)"
            placeholder="例如：日活, 日活跃用户"
            value={synonyms}
            onChange={(e) => setSynonyms(e.target.value)}
          />
          <div className="flex flex-col gap-1">
            <label className="text-sm text-gray-600">定义描述</label>
            <textarea
              className="px-3 py-2 bg-white border border-gray-300 rounded-md text-sm focus:border-primary focus:ring-1 focus:ring-primary h-24 resize-none"
              placeholder="请准确描述该术语的业务含义..."
              value={definition}
              onChange={(e) => setDefinition(e.target.value)}
            ></textarea>
          </div>
        </div>
      </Modal>
    </div>
  );
};