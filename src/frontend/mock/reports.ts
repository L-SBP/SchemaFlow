// mock/reports.ts
import { MockMethod } from 'vite-plugin-mock';

// --- 1. 模拟历史查询数据 (数据源) ---
// 包含了电商、运维监控、HR统计等不同场景的数据
const MOCK_HISTORY_QUERIES = [
  // === 项目 1 (Project ID: '1') - 电商业务 ===
  {
    id: 'q1',
    projectId: '1',
    queryText: '2025年 Q1 各品类销售额占比',
    timestamp: '2025-11-20 09:30',
    result: {
      columns: ['品类', '销售额', '订单数'],
      data: [
        { '品类': '电子数码', '销售额': 1250000, '订单数': 450 },
        { '品类': '家居生活', '销售额': 680000, '订单数': 890 },
        { '品类': '服饰鞋包', '销售额': 920000, '订单数': 1200 },
        { '品类': '美妆护肤', '销售额': 540000, '订单数': 600 },
        { '品类': '食品饮料', '销售额': 320000, '订单数': 2500 },
      ]
    }
  },
  {
    id: 'q2',
    projectId: '1',
    queryText: '近 7 天全站流量趋势',
    timestamp: '2025-11-25 10:15',
    result: {
      columns: ['日期', 'PV', 'UV', '跳出率'],
      data: [
        { '日期': '11-19', 'PV': 15000, 'UV': 3200, '跳出率': 0.45 },
        { '日期': '11-20', 'PV': 16200, 'UV': 3400, '跳出率': 0.42 },
        { '日期': '11-21', 'PV': 14800, 'UV': 3100, '跳出率': 0.48 },
        { '日期': '11-22', 'PV': 18500, 'UV': 4100, '跳出率': 0.38 },
        { '日期': '11-23', 'PV': 21000, 'UV': 5200, '跳出率': 0.35 },
        { '日期': '11-24', 'PV': 19800, 'UV': 4800, '跳出率': 0.36 },
        { '日期': '11-25', 'PV': 17500, 'UV': 3600, '跳出率': 0.40 },
      ]
    }
  },
  {
    id: 'q3',
    projectId: '1',
    queryText: '用户年龄与消费金额分布',
    timestamp: '2025-11-24 14:00',
    result: {
      columns: ['用户ID', '年龄', '累计消费'],
      data: [
        { '用户ID': 'U001', '年龄': 18, '累计消费': 500 },
        { '用户ID': 'U002', '年龄': 22, '累计消费': 1200 },
        { '用户ID': 'U003', '年龄': 25, '累计消费': 3500 },
        { '用户ID': 'U004', '年龄': 28, '累计消费': 5600 },
        { '用户ID': 'U005', '年龄': 32, '累计消费': 8900 },
        { '用户ID': 'U006', '年龄': 35, '累计消费': 7200 },
        { '用户ID': 'U007', '年龄': 40, '累计消费': 4500 },
        { '用户ID': 'U008', '年龄': 45, '累计消费': 3000 },
      ]
    }
  },

  // === 项目 2 (Project ID: '2') - 运维监控 ===
  {
    id: 'q4',
    projectId: '2',
    queryText: '生产环境 CPU 平均负载 (Top 5)',
    timestamp: '2025-11-26 08:00',
    result: {
      columns: ['服务器', 'CPU使用率', '内存使用率'],
      data: [
        { '服务器': 'Server-A', 'CPU使用率': 85, '内存使用率': 60 },
        { '服务器': 'Server-B', 'CPU使用率': 78, '内存使用率': 55 },
        { '服务器': 'Server-C', 'CPU使用率': 72, '内存使用率': 40 },
        { '服务器': 'Server-D', 'CPU使用率': 65, '内存使用率': 30 },
        { '服务器': 'Server-E', 'CPU使用率': 92, '内存使用率': 80 },
      ]
    }
  }
];

// --- 2. 模拟已生成的报表数据 ---
// 初始包含几个示例报表
let MOCK_REPORTS = [
  {
    id: 'r1',
    projectId: '1',
    name: 'Q1 品类销售占比图',
    type: 'pie',
    description: '展示各主要品类的营收贡献',
    data: MOCK_HISTORY_QUERIES[0].result.data,
    chartConfig: { xAxisKey: '品类', yAxisKey: '销售额' },
    sourceQueryId: 'q1',
    sourceQueryText: '2025年 Q1 各品类销售额占比',
    updatedAt: '2025-11-20'
  },
  {
    id: 'r2',
    projectId: '1',
    name: '全站流量周趋势',
    type: 'line',
    description: '监控每日 PV 变化情况',
    data: MOCK_HISTORY_QUERIES[1].result.data,
    chartConfig: { xAxisKey: '日期', yAxisKey: 'PV' },
    sourceQueryId: 'q2',
    sourceQueryText: '近 7 天全站流量趋势',
    updatedAt: '2025-11-25'
  },
  {
    id: 'r3',
    projectId: '1',
    name: '用户价值分析 (散点图)',
    type: 'scatter',
    description: '分析年龄段与购买力的关系',
    data: MOCK_HISTORY_QUERIES[2].result.data,
    chartConfig: { xAxisKey: '年龄', yAxisKey: '累计消费' },
    sourceQueryId: 'q3',
    sourceQueryText: '用户年龄与消费金额分布',
    updatedAt: '2025-11-24'
  },
  {
    id: 'r4',
    projectId: '2',
    name: '高负载服务器监控',
    type: 'bar',
    description: 'CPU 使用率 Top 5',
    data: MOCK_HISTORY_QUERIES[3].result.data,
    chartConfig: { xAxisKey: '服务器', yAxisKey: 'CPU使用率' },
    sourceQueryId: 'q4',
    sourceQueryText: '生产环境 CPU 平均负载 (Top 5)',
    updatedAt: '2025-11-26'
  }
];

export default [
  // 1. 获取报表列表 (支持 projectId 过滤)
  {
    url: '/api/reports',
    method: 'get',
    response: ({ query }) => {
      const { projectId } = query;
      if (projectId) {
        return MOCK_REPORTS.filter(r => r.projectId === projectId);
      }
      return MOCK_REPORTS;
    },
  },

  // 2. 创建新报表
  {
    url: '/api/reports',
    method: 'post',
    response: ({ body }) => {
      // 模拟服务器生成 ID 和时间
      const newReport = {
        ...body,
        id: Date.now().toString(),
        updatedAt: new Date().toISOString().split('T')[0],
      };
      // 将新报表插入到数组最前面
      MOCK_REPORTS.unshift(newReport);
      return newReport;
    },
  },

  // 3. 删除报表
  {
    url: RegExp('/api/reports/.+'), // 使用正则匹配路径参数 ID
    method: 'delete',
    response: ({ url }) => {
      // 从 URL 中提取 ID (假设 url 结尾是 id)
      const id = url.split('/').pop();
      const index = MOCK_REPORTS.findIndex(r => r.id === id);

      if (index !== -1) {
        MOCK_REPORTS.splice(index, 1);
        return { success: true };
      }
      return { code: 404, message: 'Report not found' };
    },
  },

  // 4. 获取历史查询记录 (Wizard 向导数据源)
  {
    url: '/api/history-queries',
    method: 'get',
    response: ({ query }) => {
      const { projectId } = query;
      if (projectId) {
        return MOCK_HISTORY_QUERIES.filter(q => q.projectId === projectId);
      }
      return []; // 如果没有 projectId，默认不返回数据，或返回所有
    },
  },
] as MockMethod[];