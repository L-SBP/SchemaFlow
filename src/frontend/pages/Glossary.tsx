
import React, { useState, useRef } from 'react';
import { Project, GlossaryTerm } from '../types';
import { Card, Button, Input, Modal, Tag } from '../components/UI';
import { Database, Plus, Search, FileUp, FileDown, Trash2, Edit2, Book, Filter, AlertCircle } from 'lucide-react';

interface GlossaryProps {
  projects: Project[];
}

// Mock Data
const MOCK_TERMS: GlossaryTerm[] = [
  { id: '1', projectId: '1', term: 'SKU', definition: '库存量单位，物理上不可分割的最小存货单元。', relatedTable: 'products', synonyms: ['库存单元'], updatedAt: '2025-10-21' },
  { id: '2', projectId: '1', term: 'GMV', definition: '商品交易总额，指一定时间段内的成交总额。', synonyms: ['交易额', '流水'], updatedAt: '2025-10-22' },
  { id: '3', projectId: '2', term: 'Leads', definition: '销售线索，指对产品感兴趣的潜在客户信息。', relatedTable: 'leads', updatedAt: '2025-10-25' },
];

export const Glossary: React.FC<GlossaryProps> = ({ projects }) => {
  const [selectedProjectId, setSelectedProjectId] = useState<string>(projects[0]?.id || '');
  const [terms, setTerms] = useState<GlossaryTerm[]>(MOCK_TERMS);
  const [searchTerm, setSearchTerm] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  // Form State
  const [termName, setTermName] = useState('');
  const [definition, setDefinition] = useState('');
  const [synonyms, setSynonyms] = useState('');

  const fileInputRef = useRef<HTMLInputElement>(null);

  const filteredTerms = terms.filter(t => 
    t.projectId === selectedProjectId && 
    (t.term.toLowerCase().includes(searchTerm.toLowerCase()) || t.definition.includes(searchTerm))
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

  const handleSave = () => {
    if (!termName || !selectedProjectId) return;

    const synonymArray = synonyms.split(/[,，]/).map(s => s.trim()).filter(Boolean);

    if (editingId) {
      setTerms(terms.map(t => t.id === editingId ? { ...t, term: termName, definition, synonyms: synonymArray, updatedAt: new Date().toISOString().split('T')[0] } : t));
    } else {
      const newTerm: GlossaryTerm = {
        id: Date.now().toString(),
        projectId: selectedProjectId,
        term: termName,
        definition,
        synonyms: synonymArray,
        updatedAt: new Date().toISOString().split('T')[0]
      };
      setTerms([newTerm, ...terms]);
    }
    setIsModalOpen(false);
  };

  const handleDelete = (id: string) => {
    if (confirm('确定要删除此术语吗？')) {
      setTerms(terms.filter(t => t.id !== id));
    }
  };

  // --- Export Functionality ---
  const handleExport = () => {
    const exportData = filteredTerms.map(({ id, ...rest }) => rest); // Exclude ID for portability
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

  // --- Import Functionality ---
  const handleImportClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        const importedData = JSON.parse(content);
        
        if (!Array.isArray(importedData)) throw new Error("Invalid format: expected array");

        const newTerms: GlossaryTerm[] = importedData.map((item: any) => ({
          id: Date.now().toString() + Math.random().toString(36).substr(2, 5),
          projectId: selectedProjectId, // Force import into current project
          term: item.term || 'Untitled',
          definition: item.definition || '',
          synonyms: item.synonyms || [],
          relatedTable: item.relatedTable,
          updatedAt: new Date().toISOString().split('T')[0]
        }));

        setTerms(prev => [...newTerms, ...prev]);
        alert(`成功导入 ${newTerms.length} 条术语`);
      } catch (error) {
        alert('导入失败：文件格式错误。请上传合法的 JSON 文件。');
        console.error(error);
      } finally {
        if (fileInputRef.current) fileInputRef.current.value = ''; // Reset
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

      <Card className="p-0 overflow-hidden">
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
                  暂无术语，请点击右上角添加或导入
                </td>
              </tr>
            )}
          </tbody>
        </table>
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
