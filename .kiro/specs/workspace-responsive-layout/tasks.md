# Implementation Plan: Workspace Responsive Layout

## Overview

本实现计划将设计文档中的响应式布局优化方案转化为具体的编码任务。实现将采用渐进式方法，先修复关键的溢出问题，然后逐步完善响应式行为。

## Tasks

- [x] 1. 修复输入栏控件溢出问题
  - [x] 1.1 重构 Input_Bar 布局结构
    - 将固定像素的 `pr-[13rem]` 改为响应式的 flex 布局
    - 使用 `flex-shrink` 控制控件收缩行为
    - 添加 `min-width: 0` 防止 flex 子元素溢出
    - _Requirements: 2.1, 2.5_
  - [x] 1.2 实现 Model_Selector 响应式收缩
    - 添加媒体查询在窄屏时隐藏标签文字
    - 在极窄屏幕（<400px）时折叠为仅图标模式
    - 使用 `truncate` 类处理长模型名称
    - _Requirements: 2.2, 2.3_
  - [x] 1.3 确保 Send_Button 最小尺寸
    - 设置 `min-width` 和 `min-height` 为 36px
    - 添加 `shrink-0` 防止按钮被压缩
    - _Requirements: 2.4_
  - [x] 1.4 编写属性测试：控件容器边界约束
    - **Property 2: 控件容器边界约束**
    - **Validates: Requirements 2.1, 2.5, 3.1, 3.3**

- [x] 2. 修复顶部标题栏溢出问题
  - [x] 2.1 重构 Header_Bar 布局结构
    - 使用 flex 布局并设置 `min-width: 0` 在标题区域
    - 添加 `truncate` 类到项目名称
    - 确保按钮区域使用 `shrink-0`
    - _Requirements: 3.1, 3.2, 3.3_
  - [x] 2.2 实现按钮响应式降级
    - 添加媒体查询在窄屏时隐藏按钮文字
    - 保留图标确保功能可用
    - _Requirements: 3.4_
  - [x] 2.3 确保 Header_Bar 最小高度
    - 设置 `min-height: 48px` 或使用 `h-12` 类
    - _Requirements: 3.5_

- [x] 3. Checkpoint - 验证溢出修复
  - 确保所有测试通过，在不同视口宽度下手动验证布局
  - 如有问题请告知

- [x] 4. 修复面板切换按钮点击区域问题
  - [x] 4.1 创建 PanelToggleButton 组件
    - 提取重复的面板切换按钮逻辑为独立组件
    - 确保按钮尺寸与点击区域一致
    - 使用 `box-border` 确保 padding 不影响尺寸计算
    - _Requirements: 6.1, 6.4_
  - [x] 4.2 设置最小可点击区域
    - 设置按钮 `min-width` 和 `min-height` 为 44px
    - 使用 `p-2.5` 或类似 padding 扩大点击区域
    - 确保 hover 状态覆盖整个点击区域
    - _Requirements: 6.2, 6.5_
  - [x] 4.3 替换 Workspace 中的面板切换按钮
    - 用新的 PanelToggleButton 组件替换现有按钮
    - 保持功能一致性
    - _Requirements: 6.1, 6.2_
  - [x] 4.4 编写属性测试：点击区域与视觉边界一致性
    - **Property 5: 点击区域与视觉边界一致性**
    - **Validates: Requirements 6.1, 6.4**

- [x] 5. 优化 DataViewer 响应式布局
  - [x] 5.1 改进宽度钳制逻辑
    - 修改最大宽度约束为视口宽度的 60%
    - 添加视口宽度监听，动态调整最大宽度
    - _Requirements: 1.4_
  - [x] 5.2 实现 Explorer 侧边栏自动折叠
    - 当 DataViewer 宽度 < 400px 时自动折叠侧边栏
    - 添加 ResizeObserver 监听宽度变化
    - _Requirements: 4.2_
  - [x] 5.3 确保表格内容水平滚动
    - 验证 `overflow-x-auto` 类正确应用
    - 确保列头 sticky 定位正常工作
    - _Requirements: 4.3, 4.4_
  - [x] 5.4 编写属性测试：DataViewer 宽度钳制
    - **Property 1: DataViewer 宽度钳制**
    - **Validates: Requirements 1.4**

- [x] 6. Checkpoint - 验证 DataViewer 优化
  - 确保所有测试通过，验证拖拽调整宽度功能正常
  - 如有问题请告知

- [x] 7. 实现对话区优先显示和面板互斥展开逻辑
  - [x] 7.1 实现缩放级别检测 Hook
    - 创建 `useZoomLevel` 自定义 Hook
    - 检测当前浏览器缩放级别（通过 window.devicePixelRatio 和视口尺寸）
    - 返回缩放级别和是否为高缩放模式（>200%）
    - _Requirements: 1.3, 2.3_
  - [x] 7.2 实现面板互斥展开逻辑
    - 在 Workspace 组件中添加面板状态管理
    - 当缩放级别 >200% 且用户展开 DataViewer 时，自动最小化 Session 面板
    - 当缩放级别 >200% 且用户展开 Session 面板时，自动最小化 DataViewer 面板
    - 确保对话区始终保持最大可用空间
    - _Requirements: 2.4, 2.5, 2.6_
  - [x] 7.3 实现自适应面板最小化策略
    - 根据视口宽度和缩放级别自动最小化面板
    - 视口宽度 <1024px 时自动最小化 DataViewer 为图标模式
    - 视口宽度 <768px 时自动隐藏 Session 面板
    - 缩放级别 >200% 时按严格优先级渐进最小化面板：右侧会话栏 → 左侧数据库侧边栏 → 对话区（最后保留）
    - _Requirements: 2.1, 2.2, 2.3_
  - [x] 7.4 添加响应式 CSS 变量
    - 在 index.css 中定义布局相关 CSS 变量
    - 添加媒体查询覆盖不同断点的变量值
    - 调整 DataViewer 最大宽度约束为 40%
    - _Requirements: 1.4, 2.9_

- [x] 9. 实现全局前端界面元素缩放优化
  - [x] 9.1 实现全局缩放级别检测系统
    - 增强 `useZoomLevel` Hook，支持检测 300%、400% 和 500% 缩放阈值
    - 将 Hook 移至全局 context 或 utils，供整个前端应用使用
    - 计算当前有效缩放级别（结合 devicePixelRatio 和视口变化）
    - 返回建议的全局缩放因子（global scale factor）
    - _Requirements: 6.1, 6.2, 6.3_
  - [x] 9.2 实现根级 CSS 变量驱动的全局比例缩放
    - 在根级样式文件（index.css）中定义 `--global-ui-scale-factor` CSS 变量，默认值 1.0
    - 在缩放级别 >300% 时设置为 0.9，>400% 时设置为 0.8，>500% 时设置为 0.7
    - 更新所有组件样式，使用全局缩放因子：字体大小、内边距、外边距、按钮尺寸、图标尺寸
    - 确保最小可点击区域不受影响（保持可访问性）
    - 应用到所有前端页面：工作区、设置页、用户管理、数据库视图等
    - _Requirements: 6.3, 6.4, 6.5, 6.8_
  - [x] 9.3 实现全局平滑缩放过渡系统
    - 在根级添加 CSS transition 确保整个应用的缩放变化平滑
    - 使用 CSS 自定义属性实现全局缩放，避免使用 transform（可能影响布局）
    - 当缩放级别降低时，整个应用平滑恢复正常尺寸
    - _Requirements: 6.6, 6.7_
  - [x] 9.4 验证全局文本可读性和可访问性
    - 验证所有页面的文本在极高缩放下仍可读
    - 设置全局最小有效字体大小为 12px
    - 测试不同页面和组件在各缩放级别下的清晰度
    - 确保表单控件、导航元素、模态对话框等在高缩放下仍可用
    - _Requirements: 6.4, 6.8_

- [x] 8. 实现全局响应式断点适配
  - [x] 8.1 实现视口宽度监听 Hook
    - 创建 `useViewportWidth` 自定义 Hook
    - 返回当前视口宽度和断点标识
    - _Requirements: 1.1_
  - [x] 8.2 应用响应式断点到 Workspace
    - 在窄屏时自动折叠非必要面板
    - 调整间距和字体大小
    - _Requirements: 1.2, 1.5_
  - [x] 8.3 编写属性测试：面板互斥展开
    - **Property 7: 面板互斥展开**
    - **Validates: Requirements 2.4, 2.5, 2.6**
  - [x] 8.4 编写属性测试：响应式断点适配
    - **Property 6: 响应式断点适配**
    - **Validates: Requirements 1.2, 2.1, 2.2, 2.3**

- [x] 11. 实现缩放兼容性优化
  - [x] 11.1 添加高缩放级别样式适配
    - 使用 `clamp()` 函数设置响应式字体大小
    - 确保控件在高缩放下保持可用
    - _Requirements: 1.3, 3.3_
  - [ ] 11.2 实现优雅降级逻辑
    - 在极端缩放下隐藏装饰性元素
    - 保留核心功能控件
    - _Requirements: 1.3, 3.6_
  - [ ] 11.3 编写属性测试：比例缩放
### Property 8: 全局比例缩放

*For any* zoom level exceeding 300%, all interface elements across the entire frontend application (including workspace, settings, user management, database views, and other pages) shall apply proportional scaling reduction using the global scale factor, while maintaining minimum clickable areas for accessibility.

**Validates: Requirements 6.1, 6.2, 6.3, 6.5, 6.8**
  - [ ] 11.4 编写属性测试：无水平溢出
    - **Property 3: 无水平溢出**
    - **Validates: Requirements 1.3**
  - [ ] 11.5 编写属性测试：最小可点击区域
    - **Property 4: 最小可点击区域**
    - **Validates: Requirements 3.4**

- [x] 12. Final Checkpoint - 完整验证
  - 确保所有测试通过
  - 在多个断点和缩放级别下验证布局
  - 如有问题请告知

## Notes

- All tasks are required for comprehensive implementation
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
