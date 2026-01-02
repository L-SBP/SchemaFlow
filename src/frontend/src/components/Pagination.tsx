/**
 * @file Pagination.tsx
 * @module Components/Navigation/Pagination
 * @description 通用数据分页组件。
 * 本组件作为系统“数据密集型”界面的核心导航工具，负责驱动长列表的按需加载逻辑。
 * * 核心设计目标：
 * 1. 性能优化 (Performance-1): 通过分页机制减轻单次 API 请求的数据载荷，降低首屏渲染耗时；
 * 2. 响应式布局: 支持“简洁模式”与“完整模式”自动切换，适配从移动端到桌面端的不同屏幕宽度；
 * 3. 交互友好 (Usability-1): 提供页码跳转、首末页快速锚定及省略号（Ellipsis）智能计算；
 * 4. 状态受控: 严格遵循 React 受控组件模式，通过 onChange 回调同步外部状态。
 * * 对应需求点：
 * - SF2: 项目列表的分页展示；
 * - SF9: 历史查询记录的翻页溯源。
 * * @author Wang Lirong (王利蓉)
 * @version 2.1.0
 * @date 2026-01-02
 */

import React from 'react';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';

/**
 * 分页组件属性接口定义
 * @interface PaginationProps
 */
interface PaginationProps {
  /** 当前活跃页码（基于 1 的索引） */
  current: number;
  /** 系统中符合过滤条件的条目总数 */
  total: number;
  /** 每页预设的显示数据行数 */
  pageSize: number;
  /** 页码发生变更时的回调函数，参数为目标页码 */
  onChange: (page: number) => void;
  /** 是否在组件左侧展示“显示第 X 到 Y 条”的汇总信息 */
  showTotal?: boolean;
  /** 是否展示快速跳转至特定页码的输入框 */
  showQuickJumper?: boolean;
  /** 是否启用极简模式（仅保留“当前/总计”及翻页箭头） */
  simple?: boolean;
  /** 允许外部注入的自定义 CSS 类名 */
  className?: string;
  /** 禁用状态标识：为 true 时禁止所有点击交互 */
  disabled?: boolean;
}

/**
 * 响应式通用分页组件实体
 * @component Pagination
 */
export const Pagination: React.FC<PaginationProps> = ({
  current,
  total,
  pageSize,
  onChange,
  showTotal = true,
  showQuickJumper = false,
  simple = false,
  className = '',
  disabled = false,
}) => {
  /** * 步骤 1：基础分页元数据计算
   * 基于向上取整算法计算总页数，确保即使只有一条数据也能显示第一页。
   */
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  
  /** 计算当前页面起始条目的绝对序号 */
  const startItem = total === 0 ? 0 : (current - 1) * pageSize + 1;
  
  /** 计算当前页面结束条目的绝对序号（取 pageSize 与 total 的最小值，防止溢出） */
  const endItem = Math.min(current * pageSize, total);

  /**
   * 步骤 2：核心算法 - 生成页码按钮序列
   * @description 
   * 实现“滑动窗口”分页算法。当总页数过多时，自动在中间插入省略号（ellipsis），
   * 保持组件在 UI 上的固定宽度，提升视觉稳定性。
   * @returns {(number | 'ellipsis')[]} 包含页码数字和省略号占位符的混合数组
   */
  const getPageNumbers = (): (number | 'ellipsis')[] => {
    const pages: (number | 'ellipsis')[] = [];
    const maxVisible = 5; // 窗口内最多展示的连续数字按钮数

    // 分支 A：总页数较少时，直接平铺展示所有页码
    if (totalPages <= maxVisible + 2) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // 分支 B：总页数较多，执行复杂的省略号计算逻辑
      pages.push(1); // 始终保留首页

      if (current <= 3) {
        // 子分支 B1：当前页靠近序列开头
        for (let i = 2; i <= Math.min(4, totalPages - 1); i++) {
          pages.push(i);
        }
        // 在尾部之前插入省略号
        if (totalPages > 5) pages.push('ellipsis');
      } else if (current >= totalPages - 2) {
        // 子分支 B2：当前页靠近序列结尾
        // 在首部之后插入省略号
        if (totalPages > 5) pages.push('ellipsis');
        for (let i = Math.max(totalPages - 3, 2); i < totalPages; i++) {
          pages.push(i);
        }
      } else {
        // 子分支 B3：当前页处于中间区域
        // 双向插入省略号，仅保留当前页及其前后相邻页
        pages.push('ellipsis');
        for (let i = current - 1; i <= current + 1; i++) {
          pages.push(i);
        }
        pages.push('ellipsis');
      }

      pages.push(totalPages); // 始终保留末页
    }

    return pages;
  };

  /**
   * 步骤 3：页码变更事件处理器
   * 包含前置守卫：拦截非法页码、禁用状态以及冗余的重复跳转。
   * @param {number} page - 目标页码
   */
  const handlePageChange = (page: number) => {
    if (disabled || page < 1 || page > totalPages || page === current) return;
    onChange(page);
  };

  /**
   * 渲染分支 A：简洁模式 (Simple Mode)
   * 适用于侧边栏、移动端或空间受限的局部容器。
   */
  if (simple) {
    return (
      <div className={`flex items-center justify-between gap-2 py-3 px-4 ${className}`}>
        {/* 数据摘要展示 */}
        {showTotal && (
          <span className="text-xs sm:text-sm text-gray-500 shrink-0 pagination-total-text">
            {total > 0 ? `${startItem}-${endItem} / ${total}` : '暂无数据'}
          </span>
        )}
        
        {/* 简洁导航控件组 */}
        <div className="flex items-center gap-1 sm:gap-2">
          {/* 上一页触发器 */}
          <button
            onClick={() => handlePageChange(current - 1)}
            disabled={disabled || current <= 1}
            className="inline-flex items-center justify-center w-8 h-8 sm:w-9 sm:h-9 rounded-md border border-gray-300 bg-white text-gray-600 hover:bg-gray-50 hover:border-gray-400 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white disabled:hover:border-gray-300 transition-colors"
            aria-label="上一页"
          >
            <ChevronLeft size={16} />
          </button>
          
          {/* 当前进度的文本描述（例：2 / 10） */}
          <span className="text-sm font-medium text-gray-700 px-2 min-w-[4rem] text-center">
            {current} / {totalPages}
          </span>
          
          {/* 下一页触发器 */}
          <button
            onClick={() => handlePageChange(current + 1)}
            disabled={disabled || current >= totalPages}
            className="inline-flex items-center justify-center w-8 h-8 sm:w-9 sm:h-9 rounded-md border border-gray-300 bg-white text-gray-600 hover:bg-gray-50 hover:border-gray-400 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white disabled:hover:border-gray-300 transition-colors"
            aria-label="下一页"
          >
            <ChevronRight size={16} />
          </button>
        </div>
      </div>
    );
  }

  /**
   * 渲染分支 B：完整模式 (Standard Mode)
   * 包含完整的数字页码选择器、首末页快速锚定及总数详细描述。
   */
  return (
    <div className={`flex flex-col sm:flex-row items-center justify-between gap-3 py-3 px-4 ${className}`}>
      
      {/* 步骤 4.1：总数详细统计信息 (Total Summary) */}
      {showTotal && (
        <div className="text-xs sm:text-sm text-gray-500 order-last sm:order-first pagination-total-text">
          {total > 0 ? (
            <>
              显示 <span className="font-medium text-gray-700">{startItem}</span> 到{' '}
              <span className="font-medium text-gray-700">{endItem}</span> 条，共{' '}
              <span className="font-medium text-gray-700">{total}</span> 条
            </>
          ) : (
            '暂无数据'
          )}
        </div>
      )}

      {/* 步骤 4.2：分页控制按钮群 (Pagination Control Group) */}
      <div className="flex items-center gap-1">
        
        {/* 首页快捷键：在移动端自动隐藏以节省空间 */}
        <button
          onClick={() => handlePageChange(1)}
          disabled={disabled || current <= 1}
          className="hidden sm:inline-flex items-center justify-center w-8 h-8 rounded-md border border-gray-300 bg-white text-gray-600 hover:bg-gray-50 hover:border-gray-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="首页"
        >
          <ChevronsLeft size={14} />
        </button>

        {/* 上一页按钮 */}
        <button
          onClick={() => handlePageChange(current - 1)}
          disabled={disabled || current <= 1}
          className="inline-flex items-center justify-center w-8 h-8 rounded-md border border-gray-300 bg-white text-gray-600 hover:bg-gray-50 hover:border-gray-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="上一页"
        >
          <ChevronLeft size={16} />
        </button>

        {/* 核心：动态页码渲染区域 */}
        <div className="flex items-center gap-1">
          {getPageNumbers().map((page, index) =>
            // 渲染省略号占位符
            page === 'ellipsis' ? (
              <span
                key={`ellipsis-${index}`}
                className="w-8 h-8 flex items-center justify-center text-gray-400"
              >
                ···
              </span>
            ) : (
              // 渲染具体的页码数字按钮
              <button
                key={page}
                onClick={() => handlePageChange(page)}
                disabled={disabled}
                className={`inline-flex items-center justify-center min-w-[2rem] h-8 px-2 rounded-md text-sm font-medium transition-colors ${page === current
                  ? 'bg-primary text-white border border-primary' // 活跃页应用品牌主题色
                  : 'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 hover:border-gray-400'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                aria-label={`第 ${page} 页`}
                aria-current={page === current ? 'page' : undefined}
              >
                {page}
              </button>
            )
          )}
        </div>

        {/* 下一页按钮 */}
        <button
          onClick={() => handlePageChange(current + 1)}
          disabled={disabled || current >= totalPages}
          className="inline-flex items-center justify-center w-8 h-8 rounded-md border border-gray-300 bg-white text-gray-600 hover:bg-gray-50 hover:border-gray-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="下一页"
        >
          <ChevronRight size={16} />
        </button>

        {/* 末页快捷键 */}
        <button
          onClick={() => handlePageChange(totalPages)}
          disabled={disabled || current >= totalPages}
          className="hidden sm:inline-flex items-center justify-center w-8 h-8 rounded-md border border-gray-300 bg-white text-gray-600 hover:bg-gray-50 hover:border-gray-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="末页"
        >
          <ChevronsRight size={14} />
        </button>
      </div>

      {/* 步骤 4.3：快速跳转模块 (Quick Jumper)
          允许用户通过键盘输入直接定位至目标页面，提升在海量数据下的导航效率。
      */}
      {showQuickJumper && totalPages > 5 && (
        <div className="hidden md:flex items-center gap-2 text-sm text-gray-600">
          <span>跳至</span>
          <input
            type="number"
            min={1}
            max={totalPages}
            className="w-14 h-8 px-2 border border-gray-300 rounded-md text-center text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
            onKeyDown={(e) => {
              // 监听回车键，执行跳转逻辑
              if (e.key === 'Enter') {
                const value = parseInt((e.target as HTMLInputElement).value);
                if (!isNaN(value)) {
                  // 执行带边界约束的页码跳转
                  handlePageChange(Math.min(Math.max(1, value), totalPages));
                  // 执行完成后清空输入框，优化交互流
                  (e.target as HTMLInputElement).value = '';
                }
              }
            }}
            aria-label="跳转到指定页"
          />
          <span>页</span>
        </div>
      )}
    </div>
  );
};

export default Pagination;