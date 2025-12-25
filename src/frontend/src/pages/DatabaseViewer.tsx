import React, { useState, useEffect, useRef } from 'react';
import {
  RefreshCw,
  Database,
  Table,
  ChevronRight,
  ChevronDown,
  HardDrive,
  ChevronLeft
} from 'lucide-react';
import {
  fetchDatabaseStructure,
  fetchTableData,
  fetchTableSchema,
  TableInfo,
  ColumnInfo
} from '../api/database';

interface DatabaseViewerProps {
  sessionId: number;
  className?: string;
}

const DatabaseViewer: React.FC<DatabaseViewerProps> = ({ sessionId, className }) => {
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [columns, setColumns] = useState<ColumnInfo[]>([]);
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [expanded, setExpanded] = useState<{ [key: string]: boolean }>({
    database: true,
    tables: true
  });
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  const rootRef = useRef<HTMLDivElement>(null);
  const [explorerWidth, setExplorerWidth] = useState(256);
  const explorerWidthRef = useRef<number>(256);
  const pendingExplorerWidthRef = useRef<number>(256);
  const resizeStartXRef = useRef<number>(0);
  const resizeStartWidthRef = useRef<number>(256);
  const resizeRafIdRef = useRef<number | null>(null);
  const [isResizingExplorer, setIsResizingExplorer] = useState(false);
  const resizeObserverRef = useRef<ResizeObserver | null>(null);

  useEffect(() => {
    try {
      const raw = localStorage.getItem('databaseViewer.explorerWidth');
      const parsed = raw ? Number(raw) : NaN;
      if (Number.isFinite(parsed)) {
        const clamped = Math.max(200, Math.min(520, parsed));
        setExplorerWidth(clamped);
      }
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    explorerWidthRef.current = explorerWidth;
    pendingExplorerWidthRef.current = explorerWidth;
    rootRef.current?.style.setProperty('--dbv-explorer-width', `${explorerWidth}px`);
    try {
      localStorage.setItem('databaseViewer.explorerWidth', String(explorerWidth));
    } catch {
      // ignore
    }
  }, [explorerWidth]);

  // ResizeObserver 监听 DataViewer 宽度变化，自动折叠侧边栏
  useEffect(() => {
    const rootElement = rootRef.current;
    if (!rootElement) return;

    // 创建 ResizeObserver 监听容器宽度变化
    resizeObserverRef.current = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width } = entry.contentRect;

        // 当 DataViewer 宽度 < 400px 时自动折叠侧边栏
        if (width < 400 && !isSidebarCollapsed) {
          setIsSidebarCollapsed(true);
        }
        // 当宽度 >= 500px 时可以考虑自动展开（可选，避免频繁切换）
        else if (width >= 500 && isSidebarCollapsed) {
          // 只有在用户没有手动折叠的情况下才自动展开
          // 这里简化处理，可以根据需要添加更复杂的状态管理
          setIsSidebarCollapsed(false);
        }
      }
    });

    resizeObserverRef.current.observe(rootElement);

    return () => {
      if (resizeObserverRef.current) {
        resizeObserverRef.current.disconnect();
        resizeObserverRef.current = null;
      }
    };
  }, [isSidebarCollapsed]); // 依赖 isSidebarCollapsed 状态

  useEffect(() => {
    if (!isResizingExplorer) return;

    const prevUserSelect = document.body.style.userSelect;
    const prevCursor = document.body.style.cursor;
    document.body.style.userSelect = 'none';
    document.body.style.cursor = 'col-resize';

    const applyWidth = (width: number) => {
      rootRef.current?.style.setProperty('--dbv-explorer-width', `${width}px`);
    };

    const handleMouseMove = (e: MouseEvent) => {
      const dx = e.clientX - resizeStartXRef.current;
      const nextWidth = resizeStartWidthRef.current + dx;
      const clamped = Math.max(200, Math.min(520, nextWidth));
      pendingExplorerWidthRef.current = clamped;

      if (resizeRafIdRef.current != null) return;
      resizeRafIdRef.current = window.requestAnimationFrame(() => {
        resizeRafIdRef.current = null;
        applyWidth(pendingExplorerWidthRef.current);
      });
    };

    const handleMouseUp = () => {
      if (resizeRafIdRef.current != null) {
        window.cancelAnimationFrame(resizeRafIdRef.current);
        resizeRafIdRef.current = null;
      }

      document.body.style.userSelect = prevUserSelect;
      document.body.style.cursor = prevCursor;
      setExplorerWidth(pendingExplorerWidthRef.current);
      setIsResizingExplorer(false);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      if (resizeRafIdRef.current != null) {
        window.cancelAnimationFrame(resizeRafIdRef.current);
        resizeRafIdRef.current = null;
      }
      document.body.style.userSelect = prevUserSelect;
      document.body.style.cursor = prevCursor;
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizingExplorer]);

  useEffect(() => {
    loadTables();
  }, [sessionId]);

  const loadTables = async () => {
    try {
      setLoading(true);
      const result = await fetchDatabaseStructure(sessionId);
      setTables(result);
    } catch (error) {
      console.error('Failed to load tables:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTableSelect = async (tableName: string) => {
    try {
      setLoading(true);
      setSelectedTable(tableName);
      // Clear previous data to avoid showing stale data if fetch fails or returns empty
      setColumns([]);
      setData([]);

      const [schemaData, tableData] = await Promise.all([
        fetchTableSchema(sessionId, tableName),
        fetchTableData(sessionId, tableName)
      ]);

      setColumns(schemaData);
      setData(tableData);
    } catch (error) {
      console.error('Failed to load table data:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (key: string) => {
    setExpanded(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleRefresh = () => {
    if (selectedTable) {
      handleTableSelect(selectedTable);
    } else {
      loadTables();
    }
  };

  return (
    <div
      ref={rootRef}
      className={`flex h-full bg-white border-r border-gray-200 ${className}`}
      style={{ ['--dbv-explorer-width' as any]: `${explorerWidth}px` }}
    >
      {/* Sidebar */}
      <div
        className={`${isSidebarCollapsed ? 'w-10' : ''} border-r border-gray-200 bg-gray-50 flex flex-col relative ${isResizingExplorer ? '' : 'transition-[width] duration-200'} motion-reduce:transition-none`}
        style={!isSidebarCollapsed ? { width: 'var(--dbv-explorer-width)' } : undefined}
      >
        <div className={`p-4 border-b border-gray-200 font-semibold text-gray-700 flex items-center ${isSidebarCollapsed ? 'justify-center' : 'justify-between'}`}>
          <div className={`flex items-center gap-2 min-w-0 ${isSidebarCollapsed ? 'justify-center' : ''}`}>

            {!isSidebarCollapsed && <span className="truncate">Explorer</span>}
          </div>
          {!isSidebarCollapsed && (
            <button
              onClick={() => setIsSidebarCollapsed(true)}
              className="p-1 hover:bg-gray-200 rounded text-gray-500 transition-colors"
              title="最小化侧边栏"
              type="button"
            >
              <ChevronLeft size={16} />
            </button>
          )}
          {isSidebarCollapsed && (
            <button
              onClick={() => setIsSidebarCollapsed(false)}
              className="p-1 hover:bg-gray-200 rounded text-gray-500 transition-colors"
              title="展开侧边栏"
              type="button"
            >
              <ChevronRight size={16} />
            </button>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-2 overflow-x-hidden">
          {!isSidebarCollapsed ? (
            <div className="mb-1">
              {/* Database Node */}
              <div
                className="flex items-center gap-1 p-1 hover:bg-gray-200 rounded cursor-pointer text-sm"
                onClick={() => toggleExpand('database')}
              >
                {expanded.database ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                <HardDrive className="w-4 h-4 text-yellow-600" />
                <span className="font-medium">Database</span>
              </div>

              {expanded.database && (
                <div className="ml-4 border-l border-gray-300 pl-2 mt-1">
                  {/* Tables Node */}
                  <div
                    className="flex items-center gap-1 p-1 hover:bg-gray-200 rounded cursor-pointer text-sm"
                    onClick={() => toggleExpand('tables')}
                  >
                    {expanded.tables ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                    <Table className="w-4 h-4 text-green-600" />
                    <span className="font-medium">Tables</span>
                  </div>

                  {expanded.tables && (
                    <div className="ml-4 border-l border-gray-300 pl-2 mt-1">
                      {tables.map((table) => (
                        <div
                          key={table.name}
                          className={`flex items-center gap-2 p-1.5 rounded cursor-pointer text-sm mb-0.5 ${selectedTable === table.name
                            ? 'bg-blue-100 text-blue-700'
                            : 'hover:bg-gray-200 text-gray-600'
                            }`}
                          onClick={() => handleTableSelect(table.name)}
                        >
                          <Table className="w-3 h-3" />
                          <span className="truncate">{table.name}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : null}
        </div>
      </div>

      {/* 拖拽条：调整 Explorer 宽度 */}
      {!isSidebarCollapsed && (
        <div
          className={`w-1 bg-transparent hover:bg-gray-200 ${isResizingExplorer ? 'bg-gray-200' : ''} cursor-col-resize shrink-0`}
          onMouseDown={(e) => {
            resizeStartXRef.current = e.clientX;
            resizeStartWidthRef.current = explorerWidthRef.current;
            setIsResizingExplorer(true);
          }}
          onDoubleClick={() => setExplorerWidth(256)}
          title="拖拽调整 Explorer 宽度（双击重置）"
        />
      )}

      {/* Main Pane */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        {/* Header */}
        <div className="h-14 border-b border-gray-200 flex items-center justify-between px-4 bg-white shrink-0">
          <div className="flex items-center gap-4 min-w-0">
            <h2 className="text-lg font-semibold text-gray-800 truncate">
              {selectedTable || 'Select a table'}
            </h2>
            {selectedTable && (
              <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full border border-gray-200 font-medium shrink-0">
                Read-only
              </span>
            )}
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={handleRefresh}
              className="p-2 hover:bg-gray-100 rounded-md text-gray-600 transition-colors"
              title="Refresh"
            >
              <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden bg-gray-50 p-4">
          {selectedTable ? (
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden h-full flex flex-col">
              {/* 确保表格容器有正确的水平滚动 */}
              <div className="flex-1 overflow-auto">
                <table className="w-full text-sm text-left">
                  {/* 确保列头 sticky 定位正常工作 */}
                  <thead className="text-xs text-gray-700 uppercase bg-gray-50 border-b border-gray-200 sticky top-0 z-10">
                    <tr>
                      {columns.map((col) => (
                        <th key={col.field} className="px-6 py-3 font-medium whitespace-nowrap bg-gray-50">
                          <div className="flex flex-col gap-0.5">
                            <span>{col.field}</span>
                            <span className="text-[10px] text-gray-400 normal-case">{col.type}</span>
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {data.map((row, rowIndex) => (
                      <tr
                        key={rowIndex}
                        className="bg-white border-b border-gray-100 hover:bg-gray-50"
                      >
                        {columns.map((col) => (
                          <td key={`${rowIndex}-${col.field}`} className="px-6 py-4 whitespace-nowrap text-gray-600">
                            {row[col.field]?.toString() ?? <span className="text-gray-300 italic">null</span>}
                          </td>
                        ))}
                      </tr>
                    ))}
                    {data.length === 0 && !loading && (
                      <tr>
                        <td colSpan={columns.length} className="px-6 py-8 text-center text-gray-500">
                          No data available
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-gray-400">
              <Database className="w-16 h-16 mb-4 opacity-20" />
              <p>Select a table</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DatabaseViewer;