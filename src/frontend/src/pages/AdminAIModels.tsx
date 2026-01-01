/**
 * @file AdminAIModels.tsx
 * @module Pages/Administration/AI-Infrastructure
 * @description 系统 AI 算力基础设施配置中心。
 * 本模块作为多智能体框架的“能源中心”，负责管理底层推理引擎（LLMs）的接入协议、身份凭证及健康检查。
 * * * 核心管理维度：
 * 1. 异构模型路由: 支持通用模型与本地微调（Finetuned）模型的并存调度（SF12）；
 * 2. 连接审计 (Connectivity Audit): 集成实时连通性测试，监测 API 响应时延（Response Time）；
 * 3. 凭证安全保护: 实施 API Key 的隐式存储与动态更新策略，确保密钥不被非法回显；
 * 4. 动态资源发现: 为前端会话面板提供可用的模型候选项（Options）。
 * * * 技术栈：
 * - 接口通讯：adminApi (Wang Lirong 开发)
 * - 视觉图标：Lucide-react 语义化图标集
 * * @author Wang Lirong (王利蓉)
 * @version 2.3.0
 * @date 2026-01-02
 */

import React, { useState, useEffect } from 'react';
import { AIModelConfigResponse, AIModelConfigDetailResponse, AIModelConfigCreate, AIModelConfigUpdate } from '../types.ts';
import { Card, Button, Tag, Modal, Input, message, Select } from '../components/UI.tsx';
import { Bot, Plus, Edit3, Trash2, Loader2, RefreshCw, Eye, EyeOff, Zap, CheckCircle, XCircle } from 'lucide-react';
import { adminApi } from '../api/admin.ts';

/**
 * @component AdminAIModels
 * @description
 * 采用 React 函数式组件构建。该页面为管理员提供了完整的 AI 模型配置 CRUD 生命周期管理。
 * 集成了严苛的 URL 协议校验及密钥格式审查（Regex Validation）。
 */
export const AdminAIModels: React.FC = () => {
    // --- 1. 数据驱动状态 (Data-Driven States) ---
    /** 存储当前全量在线的模型配置快照 */
    const [models, setModels] = useState<AIModelConfigResponse[]>([]);
    /** 局部加载锁：用于处理列表刷新时的视觉反馈 */
    const [isLoading, setIsLoading] = useState(false);
    /** 分页控制状态机 */
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0);
    const pageSize = 10;

    // --- 2. 事务流控制状态 (Workflow States) ---
    /** 配置模态框显隐开关 */
    const [isModalOpen, setIsModalOpen] = useState(false);
    /** 存储当前正处于编辑生命周期的详情对象。若为 null 则标识为“创建”模式 */
    const [editingModel, setEditingModel] = useState<AIModelConfigDetailResponse | null>(null);
    /** 提交配置至后端时的异步状态锁 */
    const [isSaving, setIsSaving] = useState(false);

    // --- 3. 表单载荷与校验状态 (Form & Validation) ---
    /** 严格对应 AIModelConfigCreate 定义的表单缓冲区 */
    const [formData, setFormData] = useState<AIModelConfigCreate>({
        model_name: '',
        api_url: '',
        model_id: '',
        api_key: '',
        model_type: 'general_llm' // 缺省默认为通用大模型类型
    });
    /** API 密钥可视化开关 */
    const [showApiKey, setShowApiKey] = useState(false);
    /** 针对特定字段的深度验证错误信息采集器 */
    const [formErrors, setFormErrors] = useState<{ api_url?: string }>({});

    // --- 4. 基础设施健康度检测状态 (Infrastructure Healthcheck) ---
    /** 标识是否正在执行 API 握手测试 */
    const [isTesting, setIsTesting] = useState(false);
    /** 存储连接测试后的多维反馈结果，包含时延及错误信息 */
    const [testResult, setTestResult] = useState<{
        success: boolean;
        message: string;
        response_time_ms?: number;
    } | null>(null);

    // --- 5. 危险操作缓冲状态 (Risk Control) ---
    /** 待执行物理删除的目标对象引用 */
    const [deleteTarget, setDeleteTarget] = useState<AIModelConfigResponse | null>(null);
    /** 删除过程中的异步加载标识 */
    const [isDeleting, setIsDeleting] = useState(false);

    /**
     * 核心逻辑：拉取模型配置清单
     * @async @function fetchModels
     * @description
     * 调用管理端 API，同步云端最新的基础设施配置状态。
     */
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

    /**
     * 效应钩子：驱动分页与初次渲染逻辑
     */
    useEffect(() => {
        fetchModels();
    }, [page]);

    /**
     * 算法层：URL 协议合规性校验
     * @description
     * 严格限制 API Endpoint 必须遵循 HTTP/HTTPS 协议，防止跨站脚本攻击或非法地址解析。
     * @param {string} url - 待测 URL 文本
     * @returns {string|undefined} 错误描述信息
     */
    const validateUrl = (url: string): string | undefined => {
        const trimmed = url.trim();
        if (!trimmed) return '请输入 API 地址';
        try {
            const parsed = new URL(trimmed);
            if (!['http:', 'https:'].includes(parsed.protocol)) {
                return 'URL 协议必须是 http 或 https';
            }
        } catch {
            return 'URL 格式不正确，请检查';
        }
        return undefined;
    };

    /**
     * 处理器：处理 API 地址的即时联动
     * 变更时自动清除之前的连接测试历史，确保数据一致性。
     */
    const handleApiUrlChange = (value: string) => {
        const error = validateUrl(value);
        setFormData(prev => ({ ...prev, api_url: value }));
        setTestResult(null); // 地址变更后，历史测试结果失效
        setFormErrors(prev => ({ ...prev, api_url: error }));
    };

    // --- 事务交互逻辑集 (Interaction Logic) ---

    /**
     * 打开初始化创建窗口
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
        setFormErrors({});
        setTestResult(null);
        setIsModalOpen(true);
    };

    /**
     * 进入配置编辑模式
     * 包含一次异步详情获取过程，确保获取到的是云端最新的元数据。
     */
    const handleOpenEditModal = async (model: AIModelConfigResponse) => {
        try {
            const detail = await adminApi.getAIModelDetail(model.config_id);
            setEditingModel(detail);
            // 初始化表单，注意 api_key 默认设为空，采取“不输入即不修改”的策略
            setFormData({
                model_name: detail.model_name,
                api_url: detail.api_url,
                model_id: detail.model_id,
                api_key: '',
                model_type: detail.model_type
            });
            setShowApiKey(false);
            setFormErrors({});
            setTestResult(null);
            setIsModalOpen(true);
        } catch (error) {
            console.error("Get model detail failed", error);
            message.error('获取模型详情失败');
        }
    };

    /**
     * 核心技术特性：执行 API 连接压力与连通性测试
     * @async @function handleTestConnection
     * @description
     * 在持久化存储之前，模拟 Agent 发起一次 Ping 握手。
     * 逻辑逻辑：
     * 1. 校验 URL 格式；
     * 2. 审查 API Key 格式（必须符合常见大模型厂商的前缀规范）；
     * 3. 区分“新密钥测试”与“已存密钥测试”两种分流。
     */
    const handleTestConnection = async () => {
        // 步骤 1：合规性预检
        const urlError = validateUrl(formData.api_url);
        if (urlError) {
            setFormErrors({ api_url: urlError });
            return;
        }

        const hasNewApiKey = formData.api_key.trim().length > 0;
        
        // 步骤 2：安全边界校验
        if (!editingModel && !hasNewApiKey) {
            message.error('请先输入 API 密钥再测试连接');
            return;
        }

        // 密钥格式正则：匹配 sk- (OpenAI), ms- (DashScope), ak- (Baidu) 等标准
        if (hasNewApiKey && !/^(sk-|ms-|ak-)[A-Za-z0-9\-]{10,}/i.test(formData.api_key.trim())) {
            message.error('API 密钥格式不正确，需以 sk-/ms-/ak- 开头');
            return;
        }

        if (!formData.model_id.trim()) {
            message.error('请输入模型 ID');
            return;
        }

        setIsTesting(true);
        setTestResult(null);
        try {
            let res;
            /**
             * 策略分发逻辑：
             * A 场景：编辑已有配置且未修改密钥。利用后端已持久化的加密密钥执行测试。
             * B 场景：新建配置或已输入新密钥。透传当前内存中的密钥执行即时测试。
             */
            if (editingModel && !hasNewApiKey) {
                res = await adminApi.testAIModelConnection({
                    api_url: formData.api_url,
                    model_id: formData.model_id,
                    config_id: editingModel.config_id 
                });
            } else {
                res = await adminApi.testAIModelConnection({
                    api_url: formData.api_url,
                    api_key: formData.api_key,
                    model_id: formData.model_id
                });
            }

            setTestResult(res);
            // 实时反馈时延性能数据
            if (res.success) {
                message.success(`连接成功！响应时间: ${res.response_time_ms}ms`);
            } else {
                message.error(res.message || '连接失败');
            }
        } catch (error: any) {
            console.error('Test connection failed', error);
            setTestResult({ success: false, message: error?.message || '连接测试失败' });
            message.error(error?.message || '连接测试失败');
        } finally {
            setIsTesting(false);
        }
    };

    /**
     * 执行配置持久化操作
     * @async @function handleSave
     * @description
     * 该操作具备强制性前置依赖：必须通过 handleTestConnection 测试后方可允许保存。
     */
    const handleSave = async () => {
        setFormErrors({});

        // 基础非空校验
        if (!formData.model_name.trim()) {
            message.error('请输入模型名称');
            return;
        }

        const urlError = validateUrl(formData.api_url);
        if (urlError) {
            setFormErrors({ api_url: urlError });
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

        if (formData.api_key.trim()) {
            const key = formData.api_key.trim();
            if (!/^(sk-|ms-|ak-)[A-Za-z0-9\-]{10,}/i.test(key)) {
                message.error('API 密钥格式不正确，需以 sk-/ms-/ak- 开头');
                return;
            }
        }

        /**
         * 强制熔断机制：
         * 禁止未经测试或测试未通过的配置入库，确保推理引擎链路的绝对可靠性。
         */
        if (!testResult || !testResult.success) {
            message.error('请先点击"测试连接"并确保通过后再保存');
            return;
        }

        setIsSaving(true);
        try {
            if (editingModel) {
                // 构造更新数据载荷，实现 API Key 的增量更新
                const updateData: AIModelConfigUpdate = {
                    model_name: formData.model_name,
                    api_url: formData.api_url,
                    model_id: formData.model_id,
                    model_type: formData.model_type
                };
                if (formData.api_key.trim()) {
                    updateData.api_key = formData.api_key.trim();
                }
                await adminApi.updateAIModel(editingModel.config_id, updateData);
                message.success('模型配置已更新');
            } else {
                // 新建配置全量提交
                await adminApi.createAIModel(formData);
                message.success('模型配置已创建');
            }
            setIsModalOpen(false);
            fetchModels(); // 乐观刷新列表
        } catch (error: any) {
            console.error("Save model failed", error);
            message.error(error?.message || '保存失败');
        } finally {
            setIsSaving(false);
        }
    };

    /**
     * 物理注销配置
     * 仅注销 API 配置信息，不会影响已持久化的对话历史数据。
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

    /**
     * 渲染视图层
     */
    return (
        <div className="p-8 max-w-7xl mx-auto h-full overflow-y-auto">
            {/* 步骤 1：头部品牌与动作栏 */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-3">
                    <div className="p-2 bg-blue-100 text-blue-600 rounded-lg shrink-0">
                        <Bot size={20} />
                    </div>
                    算力基础设施管理
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
                        配置新模型
                    </Button>
                </div>
            </div>

            {/* 步骤 2：配置项列表展现层 
                采用 table-fixed 布局，并辅以 truncate 策略处理超长 API 链接。
            */}
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
                                    <th className="px-4 py-4 font-medium text-gray-600 whitespace-nowrap w-[15%]">配置名称</th>
                                    <th className="px-4 py-4 font-medium text-gray-600 whitespace-nowrap w-[18%]">模型识别码</th>
                                    <th className="px-4 py-4 font-medium text-gray-600 whitespace-nowrap w-[10%]">引擎属性</th>
                                    <th className="px-4 py-4 font-medium text-gray-600 whitespace-nowrap w-[27%]">Endpoint 地址</th>
                                    <th className="px-4 py-4 font-medium text-gray-600 whitespace-nowrap w-[18%]">最后同步</th>
                                    <th className="px-4 py-4 font-medium text-gray-600 text-right whitespace-nowrap w-[12%]">治理</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                {models.map(model => (
                                    <tr key={model.config_id} className="hover:bg-gray-50/50 transition-colors">
                                        <td className="px-4 py-4 truncate" title={model.model_name}>
                                            <span className="font-medium text-gray-800">{model.model_name}</span>
                                        </td>
                                        <td className="px-4 py-4 text-gray-600 font-mono text-xs truncate" title={model.model_id}>{model.model_id}</td>
                                        <td className="px-4 py-4 whitespace-nowrap">
                                            {/* 类型标签分发：区分本地自研模型与外部公有云 LLM */}
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
                                                    title="修正配置"
                                                >
                                                    <Edit3 size={14} />
                                                </Button>
                                                <Button
                                                    variant="text"
                                                    className="h-8 px-2 text-gray-500 hover:text-red-500"
                                                    onClick={() => setDeleteTarget(model)}
                                                    title="物理移除"
                                                >
                                                    <Trash2 size={14} />
                                                </Button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                                {/* 空态兜底描述 */}
                                {models.length === 0 && (
                                    <tr>
                                        <td colSpan={6} className="text-center py-12 text-gray-400">
                                            暂无活跃的 AI 模型底座，请通过上方入口建立连接
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* 分页导航器 */}
                {total > 0 && (
                    <div className="flex justify-between items-center px-6 py-4 border-t border-gray-100 bg-gray-50/50">
                        <span className="text-xs text-gray-500">
                            数据节点计数: {total} | 采样视图: 第 {page} 页
                        </span>
                        <div className="flex gap-2">
                            <Button variant="default" className="h-8 px-3 text-xs" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>上一页</Button>
                            <Button variant="default" className="h-8 px-3 text-xs" disabled={page * pageSize >= total} onClick={() => setPage(p => p + 1)}>下一页</Button>
                        </div>
                    </div>
                )}
            </Card>

            {/* 事务模块 A：配置编辑与测试对话框 */}
            <Modal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                title={editingModel ? '修正推理引擎配置' : '注册新推理引擎'}
                maxWidth="max-w-lg"
                footer={
                    <div className="flex justify-end gap-2">
                        <Button onClick={() => setIsModalOpen(false)}>暂存关闭</Button>
                        <Button variant="primary" onClick={handleSave} disabled={isSaving || !testResult?.success}>
                            {isSaving ? '正在执行物理持久化...' : '确认入库'}
                        </Button>
                    </div>
                }
            >
                <div className="space-y-4">
                    <Input
                        label="模型展示名称"
                        placeholder="例如: GPT-4-o (湖南大学定制版)"
                        value={formData.model_name}
                        onChange={(e) => {
                            setFormData(prev => ({ ...prev, model_name: e.target.value }));
                            setTestResult(null);
                        }}
                        required
                    />

                    <div>
                        <Input
                            label="API Endpoint (反向代理地址)"
                            placeholder="https://openai.proxy.com/v1/chat/completions"
                            value={formData.api_url}
                            onChange={(e) => handleApiUrlChange(e.target.value)}
                            required
                        />
                        {formErrors.api_url && (
                            <p className="text-xs text-red-500 mt-1 font-medium">{formErrors.api_url}</p>
                        )}
                    </div>

                    <Input
                        label="后端模型标识 (Model ID)"
                        placeholder="如: gpt-4, llama-3-70b-instruct"
                        value={formData.model_id}
                        onChange={(e) => {
                            setFormData(prev => ({ ...prev, model_id: e.target.value }));
                            setTestResult(null);
                        }}
                        required
                    />

                    <div className="relative">
                        <Input
                            label={editingModel ? "API 访问令牌 (留空则沿用旧令牌)" : "API 访问令牌"}
                            type={showApiKey ? "text" : "password"}
                            placeholder={editingModel ? "输入新令牌或保持空白" : "密钥通常以 sk- 开头"}
                            value={formData.api_key}
                            onChange={(e) => {
                                setFormData(prev => ({ ...prev, api_key: e.target.value }));
                                setTestResult(null);
                            }}
                            required={!editingModel}
                        />
                        {/* 密钥可视性切换器 */}
                        <button
                            type="button"
                            className="absolute right-3 top-8 text-gray-400 hover:text-gray-600 transition-colors"
                            onClick={() => setShowApiKey(!showApiKey)}
                        >
                            {showApiKey ? <EyeOff size={16} /> : <Eye size={16} />}
                        </button>
                        {editingModel && !formData.api_key.trim() && (
                            <div className="mt-1">
                                <span className="text-[10px] text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-100">
                                    [系统提示] 正在使用已托管的安全凭证
                                </span>
                            </div>
                        )}
                    </div>

                    {/* 关键组件：连接测试反馈区 */}
                    <div className="bg-gray-50/50 p-4 rounded-xl border border-gray-100 flex flex-col gap-3">
                        <div className="flex items-center justify-between">
                            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">连通性状态审计</span>
                            <Button
                                variant="default"
                                className="h-8 px-4 flex items-center gap-2 bg-white"
                                onClick={handleTestConnection}
                                disabled={isTesting}
                                icon={<Zap size={14} className={isTesting ? "animate-pulse" : ""} />}
                            >
                                {isTesting ? '正在嗅探链路...' : '执行连通性测试'}
                            </Button>
                        </div>
                        
                        {testResult && (
                            <div className={`flex items-start gap-2 p-2 rounded-lg text-sm ${testResult.success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-600'}`}>
                                <div className="mt-0.5 shrink-0">
                                    {testResult.success ? <CheckCircle size={16} /> : <XCircle size={16} />}
                                </div>
                                <div className="flex-1">
                                    <p className="font-bold">{testResult.success ? '测试成功' : '握手失败'}</p>
                                    <p className="text-xs opacity-80">{testResult.message}</p>
                                    {typeof testResult.response_time_ms === 'number' && testResult.success && (
                                        <div className="mt-1 inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 bg-green-100 rounded">
                                            <RefreshCw size={10} className="animate-spin-slow" />
                                            时延: {testResult.response_time_ms}ms
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>

                    <Select
                        label="模型应用策略 (引擎分流)"
                        className="w-full"
                        value={formData.model_type}
                        onChange={(val) => {
                            setFormData(prev => ({ ...prev, model_type: val as any }));
                            setTestResult(null);
                        }}
                        required
                        options={[
                            { value: 'general_llm', label: '通用 LLM (标准推理)' },
                            { value: 'local_finetune', label: '本地微调模型 (高精度语义映射)' }
                        ]}
                    />
                </div>
            </Modal>

            {/* 事务模块 B：销毁确认对话框 */}
            <Modal
                isOpen={!!deleteTarget}
                onClose={() => setDeleteTarget(null)}
                title="高危：资源销毁确认"
                maxWidth="max-w-sm"
                footer={
                    <div className="flex gap-2">
                        <Button onClick={() => setDeleteTarget(null)}>放弃操作</Button>
                        <Button variant="danger" onClick={handleDelete} disabled={isDeleting}>
                            {isDeleting ? '正在执行销毁...' : '确认注销配置'}
                        </Button>
                    </div>
                }
            >
                <div className="space-y-3">
                    <div className="p-3 bg-red-50 rounded-lg flex items-start gap-3 border border-red-100">
                        <Trash2 className="text-red-600 shrink-0 mt-0.5" size={18} />
                        <div className="text-xs text-red-900 leading-relaxed">
                            您正在尝试物理移除模型配置 <strong>{deleteTarget?.model_name}</strong>。
                            注销后，所有依赖此算力节点的智能体任务将无法继续执行。
                        </div>
                    </div>
                    <p className="text-[11px] text-gray-400 italic">注意：此项操作无法撤销，请谨慎操作。</p>
                </div>
            </Modal>
        </div>
    );
};