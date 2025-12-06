// // mock/glossary.ts
// import { MockMethod } from 'vite-plugin-mock';

// // 初始模拟数据
// let glossaryList = [
//   { id: '1', projectId: '1', term: 'SKU', definition: '库存量单位。', synonyms: ['库存单元'], updatedAt: '2025-10-21' },
//   { id: '2', projectId: '1', term: 'GMV', definition: '商品交易总额。', synonyms: ['交易额', '流水'], updatedAt: '2025-10-22' },
//   { id: '3', projectId: '2', term: 'Leads', definition: '销售线索。', updatedAt: '2025-10-25' },
// ];

// export default [
//   // GET List
//   {
//     url: '/api/glossary',
//     method: 'get',
//     response: ({ query }: any) => {
//       const { projectId } = query;
//       const list = projectId ? glossaryList.filter(item => item.projectId === projectId) : glossaryList;
//       return { code: 200, message: '获取成功', data: list };
//     },
//   },
//   // POST Create
//   {
//     url: '/api/glossary',
//     method: 'post',
//     response: ({ body }: any) => {
//       const newTerm = {
//         id: Math.random().toString(36).substr(2, 9),
//         ...body,
//         updatedAt: new Date().toISOString().split('T')[0],
//       };
//       glossaryList.unshift(newTerm);
//       return { code: 200, message: '创建成功', data: newTerm };
//     },
//   },
//   // PUT Update
//   {
//     url: '/api/glossary/:id',
//     method: 'put',
//     response: ({ body }: any) => {
//       const id = body.id;
//       const index = glossaryList.findIndex(item => item.id === id);
//       if (index !== -1) {
//         glossaryList[index] = { ...glossaryList[index], ...body, updatedAt: new Date().toISOString().split('T')[0] };
//         return { code: 200, message: '更新成功', data: glossaryList[index] };
//       }
//       return { code: 404, message: '未找到' };
//     },
//   },
//   // DELETE
//   {
//     url: RegExp('/api/glossary/.+'),
//     method: 'delete',
//     response: ({ url }: any) => {
//       const id = url.split('/').pop();
//       glossaryList = glossaryList.filter(item => item.id !== id);
//       return { code: 200, message: '删除成功', data: null };
//     },
//   },
// ] as MockMethod[];