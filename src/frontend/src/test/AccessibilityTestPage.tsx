import React, { useEffect, useState } from 'react';
import {
  performGlobalAccessibilityCheck,
  logAccessibilityReport,
  createAccessibilityDebugPanel,
  type GlobalAccessibilityReport
} from '../utils/accessibilityVerification';
import { useGlobalZoomContext } from '../contexts/GlobalZoomContext';

/**
 * 可访问性测试页面
 * 
 * 用于测试和验证全局可访问性系统
 * 包含各种UI元素以测试不同的可访问性检查
 */
export function AccessibilityTestPage() {
  const [report, setReport] = useState<GlobalAccessibilityReport | null>(null);
  const [showDebugPanel, setShowDebugPanel] = useState(false);
  const zoomInfo = useGlobalZoomContext();

  // 执行可访问性检查
  const runAccessibilityCheck = () => {
    const newReport = performGlobalAccessibilityCheck();
    setReport(newReport);
    logAccessibilityReport(newReport);
  };

  // 切换调试面板
  const toggleDebugPanel = () => {
    if (showDebugPanel) {
      const panel = document.getElementById('accessibility-debug-panel');
      if (panel && (panel as any).cleanup) {
        (panel as any).cleanup();
      }
      setShowDebugPanel(false);
    } else {
      createAccessibilityDebugPanel();
      setShowDebugPanel(true);
    }
  };

  // 自动运行检查
  useEffect(() => {
    const timer = setTimeout(runAccessibilityCheck, 1000);
    return () => clearTimeout(timer);
  }, [zoomInfo.globalScaleFactor]);

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">可访问性测试页面</h1>

      {/* 缩放信息 */}
      <div className="bg-blue-50 p-4 rounded-lg mb-6">
        <h2 className="text-lg font-semibold mb-2">当前缩放信息</h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>缩放级别: {zoomInfo.zoomLevel}%</div>
          <div>全局缩放因子: {zoomInfo.globalScaleFactor}</div>
          <div>高缩放模式: {zoomInfo.isHighZoom ? '是' : '否'}</div>
          <div>极高缩放模式: {zoomInfo.isExtremeZoom ? '是' : '否'}</div>
        </div>
      </div>

      {/* 控制按钮 */}
      <div className="flex gap-4 mb-6">
        <button
          onClick={runAccessibilityCheck}
          className="btn bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          运行可访问性检查
        </button>
        <button
          onClick={toggleDebugPanel}
          className="btn bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
        >
          {showDebugPanel ? '隐藏' : '显示'}调试面板
        </button>
      </div>

      {/* 测试元素区域 */}
      <div className="space-y-8">
        {/* 文本元素测试 */}
        <section>
          <h2 className="text-xl font-semibold mb-4">文本元素测试</h2>
          <div className="space-y-2">
            <p className="text-xs">超小文本 (text-xs)</p>
            <p className="text-sm">小文本 (text-sm)</p>
            <p className="text-base">基础文本 (text-base)</p>
            <p className="text-lg">大文本 (text-lg)</p>
            <p className="text-xl">超大文本 (text-xl)</p>
          </div>
        </section>

        {/* 按钮测试 */}
        <section>
          <h2 className="text-xl font-semibold mb-4">按钮测试</h2>
          <div className="flex flex-wrap gap-4">
            <button className="btn bg-blue-500 text-white px-4 py-2 rounded">
              标准按钮
            </button>
            <button className="btn-sm bg-green-500 text-white px-3 py-1 rounded text-sm">
              小按钮
            </button>
            <button className="btn-lg bg-red-500 text-white px-6 py-3 rounded text-lg">
              大按钮
            </button>
            <button className="btn-icon bg-gray-500 text-white p-2 rounded">
              <span className="icon-base">🔍</span>
            </button>
            <button className="panel-toggle-button">
              <span className="icon-base">☰</span>
            </button>
          </div>
        </section>

        {/* 表单控件测试 */}
        <section>
          <h2 className="text-xl font-semibold mb-4">表单控件测试</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">文本输入</label>
              <input
                type="text"
                className="input-responsive border border-gray-300 rounded px-3 py-2"
                placeholder="请输入文本"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">文本区域</label>
              <textarea
                className="input-responsive border border-gray-300 rounded px-3 py-2 w-full"
                rows={3}
                placeholder="请输入多行文本"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">选择框</label>
              <select className="input-responsive border border-gray-300 rounded px-3 py-2">
                <option>选项 1</option>
                <option>选项 2</option>
                <option>选项 3</option>
              </select>
            </div>
          </div>
        </section>

        {/* 导航测试 */}
        <section>
          <h2 className="text-xl font-semibold mb-4">导航测试</h2>
          <nav className="bg-gray-100 p-4 rounded">
            <ul className="sidebar-nav flex space-x-4">
              <li><a href="#" className="sidebar-nav-link">首页</a></li>
              <li><a href="#" className="sidebar-nav-link">产品</a></li>
              <li><a href="#" className="sidebar-nav-link">服务</a></li>
              <li><a href="#" className="sidebar-nav-link">联系</a></li>
            </ul>
          </nav>
        </section>

        {/* 分页测试 */}
        <section>
          <h2 className="text-xl font-semibold mb-4">分页测试</h2>
          <div className="pagination">
            <button className="pagination-btn">上一页</button>
            <button className="pagination-btn pagination-btn-active">1</button>
            <button className="pagination-btn">2</button>
            <button className="pagination-btn">3</button>
            <button className="pagination-btn">下一页</button>
          </div>
        </section>

        {/* 卡片测试 */}
        <section>
          <h2 className="text-xl font-semibold mb-4">卡片测试</h2>
          <div className="card-grid">
            <div className="bg-white border border-gray-200 rounded-lg shadow">
              <div className="card-header">
                <h3 className="card-title">卡片标题</h3>
                <p className="card-subtitle">卡片副标题</p>
              </div>
              <div className="card-content">
                <p>这是卡片的内容区域，用于测试文本在不同缩放级别下的可读性。</p>
              </div>
              <div className="card-footer">
                <button className="btn bg-blue-500 text-white px-4 py-2 rounded">
                  操作按钮
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>

      {/* 检查结果 */}
      {report && (
        <div className="mt-8 bg-gray-50 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">
            检查结果 {report.overallPassed ? '✅' : '❌'}
          </h2>
          <div className="mb-4">
            <div className="text-sm text-gray-600">
              通过: {report.passedCount}/{report.totalCount} 项
            </div>
          </div>
          <div className="space-y-4">
            {report.results.map((result, index) => (
              <div key={index} className="border-l-4 pl-4" style={{
                borderColor: result.passed ? '#10b981' : '#f59e0b'
              }}>
                <div className="font-medium">
                  {result.passed ? '✅' : '❌'} {result.checkName}
                </div>
                <div className="text-sm text-gray-600 mt-1">
                  {result.details}
                </div>
                {result.suggestions && result.suggestions.length > 0 && (
                  <div className="mt-2">
                    <div className="text-sm font-medium text-gray-700">建议:</div>
                    <ul className="text-sm text-gray-600 list-disc list-inside">
                      {result.suggestions.map((suggestion, suggestionIndex) => (
                        <li key={suggestionIndex}>{suggestion}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default AccessibilityTestPage;