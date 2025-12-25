import React from 'react';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';

/**
 * 分页组件属性接口
 */
interface PaginationProps {
  /** 当前页码 (1-based) */
  current: number;
  /** 总条目数 */
  total: number;
  /** 每页条目数 */
  pageSize: number;
  /** 页码变化回调 */
  onChange: (page: number) => void;
  /** 是否显示总数信息 */
  showTotal?: boolean;
  /** 是否显示快速跳转 */
  showQuickJumper?: boolean;
  /** 是否简洁模式 */
  simple?: boolean;
  /** 自定义类名 */
  className?: string;
  /** 是否禁用 */
  disabled?: boolean;
}

/**
 * 通用分页组件
 * 支持响应式布局和高缩放级别
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
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const startItem = total === 0 ? 0 : (current - 1) * pageSize + 1;
  const endItem = Math.min(current * pageSize, total);

  // 生成页码数组
  const getPageNumbers = (): (number | 'ellipsis')[] => {
    const pages: (number | 'ellipsis')[] = [];
    const maxVisible = 5; // 最多显示的页码数

    if (totalPages <= maxVisible + 2) {
      // 总页数较少，全部显示
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // 总页数较多，显示省略号
      pages.push(1);

      if (current <= 3) {
        // 当前页靠近开头
        for (let i = 2; i <= Math.min(4, totalPages - 1); i++) {
          pages.push(i);
        }
        if (totalPages > 5) pages.push('ellipsis');
      } else if (current >= totalPages - 2) {
        // 当前页靠近结尾
        if (totalPages > 5) pages.push('ellipsis');
        for (let i = Math.max(totalPages - 3, 2); i < totalPages; i++) {
          pages.push(i);
        }
      } else {
        // 当前页在中间
        pages.push('ellipsis');
        for (let i = current - 1; i <= current + 1; i++) {
          pages.push(i);
        }
        pages.push('ellipsis');
      }

      pages.push(totalPages);
    }

    return pages;
  };

  const handlePageChange = (page: number) => {
    if (disabled || page < 1 || page > totalPages || page === current) return;
    onChange(page);
  };

  // 简洁模式
  if (simple) {
    return (
      <div className={`flex items-center justify-between gap-2 py-3 px-4 ${className}`}>
        {showTotal && (
          <span className="text-xs sm:text-sm text-gray-500 shrink-0 pagination-total-text">
            {total > 0 ? `${startItem}-${endItem} / ${total}` : '暂无数据'}
          </span>
        )}
        <div className="flex items-center gap-1 sm:gap-2">
          <button
            onClick={() => handlePageChange(current - 1)}
            disabled={disabled || current <= 1}
            className="inline-flex items-center justify-center w-8 h-8 sm:w-9 sm:h-9 rounded-md border border-gray-300 bg-white text-gray-600 hover:bg-gray-50 hover:border-gray-400 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white disabled:hover:border-gray-300 transition-colors"
            aria-label="上一页"
          >
            <ChevronLeft size={16} />
          </button>
          <span className="text-sm font-medium text-gray-700 px-2 min-w-[4rem] text-center">
            {current} / {totalPages}
          </span>
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

  // 完整模式
  return (
    <div className={`flex flex-col sm:flex-row items-center justify-between gap-3 py-3 px-4 ${className}`}>
      {/* 总数信息 - 右对齐 */}
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

      {/* 分页控件 */}
      <div className="flex items-center gap-1">
        {/* 首页 */}
        <button
          onClick={() => handlePageChange(1)}
          disabled={disabled || current <= 1}
          className="hidden sm:inline-flex items-center justify-center w-8 h-8 rounded-md border border-gray-300 bg-white text-gray-600 hover:bg-gray-50 hover:border-gray-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="首页"
        >
          <ChevronsLeft size={14} />
        </button>

        {/* 上一页 */}
        <button
          onClick={() => handlePageChange(current - 1)}
          disabled={disabled || current <= 1}
          className="inline-flex items-center justify-center w-8 h-8 rounded-md border border-gray-300 bg-white text-gray-600 hover:bg-gray-50 hover:border-gray-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="上一页"
        >
          <ChevronLeft size={16} />
        </button>

        {/* 页码按钮 */}
        <div className="flex items-center gap-1">
          {getPageNumbers().map((page, index) =>
            page === 'ellipsis' ? (
              <span
                key={`ellipsis-${index}`}
                className="w-8 h-8 flex items-center justify-center text-gray-400"
              >
                ···
              </span>
            ) : (
              <button
                key={page}
                onClick={() => handlePageChange(page)}
                disabled={disabled}
                className={`inline-flex items-center justify-center min-w-[2rem] h-8 px-2 rounded-md text-sm font-medium transition-colors ${page === current
                  ? 'bg-primary text-white border border-primary'
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

        {/* 下一页 */}
        <button
          onClick={() => handlePageChange(current + 1)}
          disabled={disabled || current >= totalPages}
          className="inline-flex items-center justify-center w-8 h-8 rounded-md border border-gray-300 bg-white text-gray-600 hover:bg-gray-50 hover:border-gray-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="下一页"
        >
          <ChevronRight size={16} />
        </button>

        {/* 末页 */}
        <button
          onClick={() => handlePageChange(totalPages)}
          disabled={disabled || current >= totalPages}
          className="hidden sm:inline-flex items-center justify-center w-8 h-8 rounded-md border border-gray-300 bg-white text-gray-600 hover:bg-gray-50 hover:border-gray-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="末页"
        >
          <ChevronsRight size={14} />
        </button>
      </div>

      {/* 快速跳转 */}
      {showQuickJumper && totalPages > 5 && (
        <div className="hidden md:flex items-center gap-2 text-sm text-gray-600">
          <span>跳至</span>
          <input
            type="number"
            min={1}
            max={totalPages}
            className="w-14 h-8 px-2 border border-gray-300 rounded-md text-center text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                const value = parseInt((e.target as HTMLInputElement).value);
                if (!isNaN(value)) {
                  handlePageChange(Math.min(Math.max(1, value), totalPages));
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
