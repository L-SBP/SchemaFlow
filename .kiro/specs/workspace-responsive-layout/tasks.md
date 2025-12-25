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

- [ ] 3. Checkpoint - 验证溢出修复
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

- [ ] 6. Checkpoint - 验证 DataViewer 优化
  - 确保所有测试通过，验证拖拽调整宽度功能正常
  - 如有问题请告知

- [ ] 7. 实现全局响应式断点适配
  - [ ] 7.1 添加响应式 CSS 变量
    - 在 index.css 中定义布局相关 CSS 变量
    - 添加媒体查询覆盖不同断点的变量值
    - _Requirements: 1.1, 1.2_
  - [ ] 7.2 实现视口宽度监听 Hook
    - 创建 `useViewportWidth` 自定义 Hook
    - 返回当前视口宽度和断点标识
    - _Requirements: 1.1_
  - [ ] 7.3 应用响应式断点到 Workspace
    - 在窄屏时自动折叠非必要面板
    - 调整间距和字体大小
    - _Requirements: 1.2, 5.2_
  - [ ] 7.4 编写属性测试：响应式断点适配
    - **Property 6: 响应式断点适配**
    - **Validates: Requirements 1.2, 2.2, 2.3, 4.2**

- [ ] 8. 实现缩放兼容性优化
  - [ ] 8.1 添加高缩放级别样式适配
    - 使用 `clamp()` 函数设置响应式字体大小
    - 确保控件在高缩放下保持可用
    - _Requirements: 5.1, 5.5_
  - [ ] 8.2 实现优雅降级逻辑
    - 在极端缩放下隐藏装饰性元素
    - 保留核心功能控件
    - _Requirements: 5.2, 5.4_
  - [ ] 8.3 编写属性测试：无水平溢出
    - **Property 3: 无水平溢出**
    - **Validates: Requirements 1.3, 5.3**
  - [ ] 8.4 编写属性测试：最小可点击区域
    - **Property 4: 最小可点击区域**
    - **Validates: Requirements 2.4, 3.5, 6.2**

- [ ] 9. Final Checkpoint - 完整验证
  - 确保所有测试通过
  - 在多个断点和缩放级别下验证布局
  - 如有问题请告知

## Notes

- All tasks are required for comprehensive implementation
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
