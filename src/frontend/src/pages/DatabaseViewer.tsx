import React, { useState, useEffect } from 'react';
import {
  RefreshCw,
  Database,
  Table,
  ChevronRight,
  ChevronDown,
  HardDrive,
  Server,
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
    connection: true,
    database: true,
    tables: true
  });
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

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
    <div className={`flex h-full bg-white border-r border-gray-200 ${className}`}>
      {/* Sidebar */}
      <div className={`${isSidebarCollapsed ? 'w-10' : 'w-64'} border-r border-gray-200 bg-gray-50 flex flex-col transition-all duration-300 relative`}>
        <div className={`p-4 border-b border-gray-200 font-semibold text-gray-700 flex items-center gap-2 ${isSidebarCollapsed ? 'justify-center' : ''}`}>
          <Database className="w-5 h-5 shrink-0" />
          {!isSidebarCollapsed && <span>Explorer</span>}
        </div>

        <button
          onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
          className="absolute -right-3 top-14 bg-white border border-gray-200 rounded-full p-0.5 shadow-sm hover:bg-gray-50 z-10"
        >
          {isSidebarCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>

        <div className="flex-1 overflow-y-auto p-2 overflow-x-hidden">
          {!isSidebarCollapsed ? (
            /* Connection Node */
            <div className="mb-1">
              <div
                className="flex items-center gap-1 p-1 hover:bg-gray-200 rounded cursor-pointer text-sm"
                onClick={() => toggleExpand('connection')}
              >
                {expanded.connection ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                <Server className="w-4 h-4 text-blue-600" />
                <span className="font-medium">Connection</span>
              </div>

              {expanded.connection && (
                <div className="ml-4 border-l border-gray-300 pl-2 mt-1">
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
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center gap-4 mt-2">
              <div title="Connection"><Server className="w-4 h-4 text-blue-600" /></div>
              <div title="Database"><HardDrive className="w-4 h-4 text-yellow-600" /></div>
              <div title="Tables"><Table className="w-4 h-4 text-green-600" /></div>
            </div>
          )}
        </div>
      </div>

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
        <div className="flex-1 overflow-auto bg-gray-50 p-4">
          {selectedTable ? (
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
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