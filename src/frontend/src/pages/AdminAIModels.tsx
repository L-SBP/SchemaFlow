import React, { useState, useEffect } from 'react';
import { AIModelConfigResponse, AIModelConfigDetailResponse, AIModelConfigCreate, AIModelConfigUpdate } from '../types.ts';
import { Card, Button, Tag, Modal, Input, message } from '../components/UI.tsx';
import { Bot, Plus, Edit3, Trash2, Loader2, RefreshCw, Eye, EyeOff } from 'lucide-react';
import { adminApi } from '../api/admin.ts';

/**
 * AI 模型配置管理面板（精简版）
 * 管理员可以添加、编辑、删除 AI 对话模型配置
 */
export const AdminAIModels: React.FC = () => {
    // --- 状态管理 ---
    const [models, setModels] = useState<AIModelConfigResponse[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0);
    const pageSize = 10;

    // 创建/编辑模态框状态
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingModel, setEditingModel] = useState<AIModelConfigDetailResponse | null>(null);
    const [isSaving, setIsSaving] = useState(false);

    // 表单数据
    const [formData, setFormData] = useState<AIModelConfigCreate>({
        model_name: '',
        api_url: '',
        model_id: '',
        api_key: '',
        model_type: 'general_llm'
    });
    const [showApiKey, setShowApiKey] = useState(false);

    // 删除确认
    const [deleteTarget, setDeleteTarget] = useState<AIModelConfigResponse | null>(null);
    const [isDeleting, setIsDeleting] = useState(false);

    // --- 数据获取 ---
    const fetchModels = async () => {
        setIsLoading(true);
        try {
            const res = await adminApi.getAIModels(page, pageSize);
            setModels(res.items);
            setTotal(res.total);
        } catch (error) {
            console.error("Fetch AI models failed", error);
            message.error('获取模型列表失败');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchModels();
    }, [page]);

    // --- 业务逻辑 ---

    /**
     * 打开创建模态框
     */
    const handleOpenCreateModal = () => {
        setEditingModel(null);
        setFormData({
            model_name: '',
            api_url: '',
            model_id: '',
            api_key: '',
            model_type: 'general_llm'
        });
        setShowApiKey(false);
        setIsModalOpen(true);
    };

    /**
     * 打开编辑模态框
     */
    const handleOpenEditModal = async (model: AIModelConfigResponse) => {
        try {
            const detail = await adminApi.getAIModelDetail(model.config_id);
            setEditingModel(detail);
            setFormData({
                model_name: detail.model_name,
                api_url: detail.api_url,
                model_id: detail.model_id,
                api_key: '', // 编辑时不显示原密钥，留空表示不修改
                model_type: detail.model_type
            });
            setShowApiKey(false);
            setIsModalOpen(true);
        } catch (error) {
            console.error("Get model detail failed", error);
            message.error('获取模型详情失败');
        }
    };

    /**
     * 保存模型配置
     */
    const handleSave = async () => {
        // 表单验证
        if (!formData.model_name.trim()) {
            message.error('请输入模型名称');
            return;
        }
        if (!formData.api_url.trim()) {
            message.error('请输入 API 地址');
            return;
        }
        if (!formData.model_id.trim()) {
            message.error('请输入模型 ID');
            return;
        }
        if (!editingModel && !formData.api_key.trim()) {
            message.error('请输入 API 密钥');
            return;
        }

        setIsSaving(true);
        try {
            if (editingModel) {
                // 更新
                const updateData: AIModelConfigUpdate = {
                    model_name: formData.model_name,
                    api_url: formData.api_url,
                    model_id: formData.model_id,
                    model_type: formData.model_type
                };
                // 只有填写了新密钥才更新
                if (formData.api_key.trim()) {
                    updateData.api_key = formData.api_key;
                }
                await adminApi.updateAIModel(editingModel.config_id, updateData);
                message.success('模型配置已更新');
            } else {
                // 创建
                await adminApi.createAIModel(formData);
                message.success('模型配置已创建');
            }
            setIsModalOpen(false);
            fetchModels();
        } catch (error: any) {
            console.error("Save model failed", error);
            message.error(error?.message || '保存失败');
        } finally {
            setIsSaving(false);
        }
    };

    /**
     * 删除模型配置
     */
    const handleDelete = async () => {
        if (!deleteTarget) return;

        setIsDeleting(true);
        try {
            await adminApi.deleteAIModel(deleteTarget.config_id);
            message.success('模型配置已删除');
            setDeleteTarget(null);
            fetchModels();
        } catch (error: any) {
            console.error("Delete model failed", error);
            message.error(error?.message || '删除失败');
        } finally {
            setIsDeleting(false);
        }
    };

    return (
        <div className="p-8 max-w-7xl mx-auto h-full overflow-y-auto">
            {/* 顶部标题与操作栏 */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-3">
                    <div className="p-2 bg-blue-100 text-blue-600 rounded-lg shrink-0">
                        <Bot size={20} />
                    </div>
                    模型配置
                </h2>

                <div className="flex gap-2">
                    <Button
                        variant="default"
                        className="h-9 px-3"
                        onClick={fetchModels}
                        icon={<RefreshCw size={14} />}
                    >
                        刷新
                    </Button>
                    <Button
                        variant="primary"
                        className="h-9 px-4"
                        onClick={handleOpenCreateModal}
                        icon={<Plus size={14} />}
                    >
                        添加模型
                    </Button>
                </div>
            </div>

            {/* 模型列表 */}
            <Card className="overflow-hidden p-0 min-h-[400px]">
                {isLoading ? (
                    <div className="flex justify-center items-center h-64">
                        <Loader2 className="animate-spin text-primary" size={32} />
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm table-fixed">
                            <thead className="bg-gray-50 border-b border-gray-200">
                                <tr>
                                    <th className="px-4 py-4 font-medium text-gray-600 whitespace-nowrap w-[15%]">模型名称</th>
                                    <th className="px-4 py-4 font-medium text-gray-600 whitespace-nowrap w-[18%]">模型 ID</th>
                                    <th className="px-4 py-4 font-medium text-gray-600 whitespace-nowrap w-[10%]">类型</th>
                                    <th className="px-4 py-4 font-medium text-gray-600 whitespace-nowrap w-[27%]">API 地址</th>
                                    <th className="px-4 py-4 font-medium text-gray-600 whitespace-nowrap w-[18%]">更新时间</th>
                                    <th className="px-4 py-4 font-medium text-gray-600 text-right whitespace-nowrap w-[12%]">操作</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                {models.map(model => (
                                    <tr key={model.config_id} className="hover:bg-gray-50/50">
                                        <td className="px-4 py-4 truncate" title={model.model_name}>
                                            <span className="font-medium text-gray-800">{model.model_name}</span>
                                        </td>
                                        <td className="px-4 py-4 text-gray-600 font-mono text-xs truncate" title={model.model_id}>{model.model_id}</td>
                                        <td className="px-4 py-4 whitespace-nowrap">
                                            <Tag color={model.model_type === 'local_finetune' ? 'blue' : 'orange'}>
                                                {model.model_type === 'local_finetune' ? '本地微调' : '通用LLM'}
                                            </Tag>
                                        </td>
                                        <td className="px-4 py-4 text-gray-500 text-xs truncate" title={model.api_url}>
                                            {model.api_url}
                                        </td>
                                        <td className="px-4 py-4 text-gray-500 whitespace-nowrap text-xs">
                                            {new Date(model.updated_at).toLocaleString()}
                                        </td>
                                        <td className="px-4 py-4 text-right whitespace-nowrap">
                                            <div className="flex justify-end gap-1">
                                                <Button
                                                    variant="text"
                                                    className="h-8 px-2 text-gray-500 hover:text-primary"
                                                    onClick={() => handleOpenEditModal(model)}
                                                    title="编辑"
                                                >
                                                    <Edit3 size={14} />
                                                </Button>
                                                <Button
                                                    variant="text"
                                                    className="h-8 px-2 text-gray-500 hover:text-red-500"
                                                    onClick={() => setDeleteTarget(model)}
                                                    title="删除"
                                                >
                                                    <Trash2 size={14} />
                                                </Button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                                {models.length === 0 && (
                                    <tr>
                                        <td colSpan={6} className="text-center py-12 text-gray-500">
                                            暂无模型配置，请点击"添加模型"创建
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* 分页器 */}
                {total > 0 && (
                    <div className="flex justify-between items-center px-6 py-4 border-t border-gray-100 bg-gray-50/50">
                        <span className="text-xs text-gray-500">
                            共 {total} 条记录，当前第 {page} 页
                        </span>
                        <div className="flex gap-2">
                            <Button variant="default" className="h-8 px-3 text-xs" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>上一页</Button>
                            <Button variant="default" className="h-8 px-3 text-xs" disabled={page * pageSize >= total} onClick={() => setPage(p => p + 1)}>下一页</Button>
                        </div>
                    </div>
                )}
            </Card>

            {/* 创建/编辑模态框 */}
            <Modal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                title={editingModel ? '编辑模型配置' : '添加模型配置'}
                maxWidth="max-w-lg"
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
                        label="模型名称"
                        placeholder="如: GPT-4, Qwen-32B"
                        value={formData.model_name}
                        onChange={(e) => setFormData(prev => ({ ...prev, model_name: e.target.value }))}
                    />

                    <Input
                        label="API 地址"
                        placeholder="https://api.example.com/v1/chat/completions"
                        value={formData.api_url}
                        onChange={(e) => setFormData(prev => ({ ...prev, api_url: e.target.value }))}
                    />

                    <Input
                        label="模型 ID"
                        placeholder="如: gpt-4, qwen-coder-32b"
                        value={formData.model_id}
                        onChange={(e) => setFormData(prev => ({ ...prev, model_id: e.target.value }))}
                    />

                    <div className="relative">
                        <Input
                            label={editingModel ? "API 密钥 (留空则不修改)" : "API 密钥"}
                            type={showApiKey ? "text" : "password"}
                            placeholder={editingModel ? "留空则保持原密钥不变" : "sk-xxxxx"}
                            value={formData.api_key}
                            onChange={(e) => setFormData(prev => ({ ...prev, api_key: e.target.value }))}
                        />
                        <button
                            type="button"
                            className="absolute right-3 top-8 text-gray-400 hover:text-gray-600"
                            onClick={() => setShowApiKey(!showApiKey)}
                        >
                            {showApiKey ? <EyeOff size={16} /> : <Eye size={16} />}
                        </button>
                        {editingModel && (
                            <p className="text-xs text-gray-500 mt-1">
                                当前密钥: {editingModel.api_key_masked}
                            </p>
                        )}
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">模型类型</label>
                        <select
                            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-primary focus:border-primary"
                            value={formData.model_type}
                            onChange={(e) => setFormData(prev => ({ ...prev, model_type: e.target.value as any }))}
                        >
                            <option value="general_llm">通用 LLM</option>
                            <option value="local_finetune">本地微调模型</option>
                        </select>
                    </div>
                </div>
            </Modal>

            {/* 删除确认模态框 */}
            <Modal
                isOpen={!!deleteTarget}
                onClose={() => setDeleteTarget(null)}
                title="确认删除"
                maxWidth="max-w-sm"
                footer={
                    <>
                        <Button onClick={() => setDeleteTarget(null)}>取消</Button>
                        <Button variant="danger" onClick={handleDelete} disabled={isDeleting}>
                            {isDeleting ? '删除中...' : '确认删除'}
                        </Button>
                    </>
                }
            >
                <div className="text-gray-600">
                    <p>确定要删除模型 <strong>{deleteTarget?.model_name}</strong> 吗？</p>
                    <p className="text-sm text-red-500 mt-2">此操作不可恢复！</p>
                </div>
            </Modal>
        </div>
    );
};
