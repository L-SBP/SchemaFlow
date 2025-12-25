# Design Document: Workspace Responsive Layout

## Overview

本设计文档描述了工作区响应式布局优化的技术实现方案。主要目标是解决当前布局在不同屏幕尺寸和浏览器缩放级别下的显示问题，确保所有控件保持在其容器边界内，并提供流畅的用户体验。

### 设计目标

1. 实现真正的响应式布局，支持 320px 到 2560px 视口宽度
2. 支持 100% 到 500% 的浏览器缩放级别
3. 修复输入栏控件溢出问题
4. 修复顶部标题栏按钮溢出问题
5. 优化 DataViewer 面板的响应式行为
6. 修复面板切换按钮的点击区域问题

## Architecture

### 布局架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Workspace (flex)                          │
├──────────────┬─────────────────────────────┬───────────────────┤
│   DataViewer │      Chat Area (flex-1)      │   Session Panel   │
│   (可调整宽度) │                              │   (固定/可折叠)    │
│              │  ┌─────────────────────────┐ │                   │
│              │  │      Header Bar         │ │                   │
│              │  ├─────────────────────────┤ │                   │
│              │  │                         │ │                   │
│              │  │    Messages Area        │ │                   │
│              │  │                         │ │                   │
│              │  ├─────────────────────────┤ │                   │
│              │  │      Input Bar          │ │                   │
│              │  └─────────────────────────┘ │                   │
└──────────────┴─────────────────────────────┴───────────────────┘
```

### 响应式断点策略

| 断点 | 视口宽度 | 布局行为 |
|------|----------|----------|
| xs | < 480px | 单列布局，面板堆叠，控件紧凑模式 |
| sm | 480px - 768px | 双列布局，右侧面板可折叠 |
| md | 768px - 1024px | 三列布局，所有面板可见 |
| lg | 1024px - 1440px | 三列布局，宽松间距 |
| xl | > 1440px | 三列布局，最大内容宽度限制 |

## Components and Interfaces

### 1. Workspace 组件改进

```typescript
interface WorkspaceLayoutState {
  leftPanelWidth: number;        // DataViewer 宽度 (px)
  isLeftPanelOpen: boolean;      // 左侧面板是否展开
  isRightPanelOpen: boolean;     // 右侧面板是否展开
  viewportWidth: number;         // 当前视口宽度
  isCompactMode: boolean;        // 是否为紧凑模式
}

// 宽度约束
const LAYOUT_CONSTRAINTS = {
  leftPanel: {
    minWidth: 200,
    maxWidthPercent: 0.6,  // 最大占视口 60%
    defaultWidth: 800,
  },
  rightPanel: {
    width: 256,            // 固定宽度
    collapsedWidth: 0,
  },
  chatArea: {
    minWidth: 320,         // 最小宽度确保输入栏可用
  },
};
```

### 2. InputBar 组件改进

```typescript
interface InputBarProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  selectedModel: string;
  onModelChange: (model: string) => void;
  disabled?: boolean;
  isCompact?: boolean;  // 紧凑模式标志
}

// 控件布局模式
type InputBarLayoutMode = 'full' | 'compact' | 'minimal';
```

### 3. HeaderBar 组件改进

```typescript
interface HeaderBarProps {
  projectName: string;
  projectType: string;
  sessionName?: string;
  onInfoClick: () => void;
  onPanelToggle?: () => void;
  isCompact?: boolean;
}
```

### 4. PanelToggleButton 组件

```typescript
interface PanelToggleButtonProps {
  isOpen: boolean;
  onToggle: () => void;
  position: 'left' | 'right';
  title?: string;
}
```

## Data Models

### CSS 变量系统

```css
:root {
  /* 布局变量 */
  --workspace-left-panel-width: 800px;
  --workspace-right-panel-width: 256px;
  --workspace-min-chat-width: 320px;
  
  /* 间距变量 */
  --workspace-gap: 0px;
  --input-bar-padding: 1.5rem;
  --header-bar-padding: 1.5rem;
  
  /* 控件尺寸 */
  --button-min-size: 44px;
  --input-height: 56px;
  
  /* 响应式调整 */
  --compact-padding: 0.75rem;
  --compact-button-size: 36px;
}

/* 紧凑模式覆盖 */
@media (max-width: 768px) {
  :root {
    --input-bar-padding: var(--compact-padding);
    --header-bar-padding: var(--compact-padding);
    --button-min-size: var(--compact-button-size);
  }
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Based on the prework analysis, the following consolidated properties have been identified:

### Property 1: DataViewer 宽度钳制

*For any* drag delta value applied to the DataViewer resize handle, the resulting panel width shall be clamped between minWidth (200px) and maxWidth (60% of viewport width).

**Validates: Requirements 1.4**

### Property 2: 控件容器边界约束

*For any* viewport width (320px-2560px) and zoom level (100%-500%) combination, all child controls (Model_Selector, Send_Button, Header buttons) shall remain completely within their parent container boundaries (Input_Bar, Header_Bar respectively).

**Validates: Requirements 2.1, 2.5, 3.1, 3.3**

### Property 3: 无水平溢出

*For any* supported viewport width (320px to 2560px) and zoom level (100% to 500%), the Workspace shall not produce horizontal scrollbars at the page level (document.body.scrollWidth === document.body.clientWidth).

**Validates: Requirements 1.3, 5.3**

### Property 4: 最小可点击区域

*For any* interactive button element in the Workspace (including Panel_Toggle_Button, Send_Button, Header buttons), the clickable area shall be at least 36x36 pixels in compact mode or 44x44 pixels in normal mode.

**Validates: Requirements 2.4, 3.5, 6.2**

### Property 5: 点击区域与视觉边界一致性

*For any* Panel_Toggle_Button, the clickable area boundaries (as determined by the element's bounding rect and click handler) shall exactly match the visual button boundaries (no invisible click zones outside the visible button).

**Validates: Requirements 6.1, 6.4**

### Property 6: 响应式断点适配

*For any* viewport width below the defined breakpoint thresholds, the corresponding responsive behavior shall be triggered:
- Width < 768px: non-essential panels collapsed or stacked
- Width < 400px: Model_Selector shows icon only
- DataViewer width < 400px: explorer sidebar auto-collapses

**Validates: Requirements 1.2, 2.2, 2.3, 4.2**

## Error Handling

### 布局错误处理

1. **宽度计算溢出**: 当计算出的宽度超出有效范围时，使用 `Math.max()` 和 `Math.min()` 进行边界钳制
2. **CSS 变量回退**: 所有 CSS 变量使用 `var(--variable, fallback)` 语法提供回退值
3. **Resize Observer 错误**: 使用 try-catch 包装 ResizeObserver 回调，防止布局计算错误导致崩溃

### 响应式降级策略

```typescript
// 当空间不足时的降级顺序
const DEGRADATION_ORDER = [
  'hide-model-label',      // 1. 隐藏模型选择器标签
  'collapse-model-selector', // 2. 折叠模型选择器为图标
  'hide-project-type',     // 3. 隐藏项目类型标签
  'icon-only-buttons',     // 4. 按钮仅显示图标
  'collapse-right-panel',  // 5. 折叠右侧面板
  'collapse-left-panel',   // 6. 折叠左侧面板
];
```

## Testing Strategy

### 单元测试

1. **布局计算函数测试**
   - 测试宽度钳制函数在边界值的行为
   - 测试响应式断点判断逻辑
   - 测试 CSS 变量计算

2. **组件渲染测试**
   - 测试 InputBar 在不同布局模式下的渲染
   - 测试 HeaderBar 在不同宽度下的文本截断
   - 测试 PanelToggleButton 的点击区域

### 属性测试

使用 fast-check 进行属性测试：

1. **Property 1 测试**: 生成随机视口宽度和缩放级别，验证输入栏控件不溢出
2. **Property 3 测试**: 生成随机拖拽位移，验证宽度始终在有效范围内
3. **Property 4 测试**: 生成随机点击坐标，验证点击区域与视觉边界一致

### 视觉回归测试

1. 在多个断点截图对比
2. 在不同缩放级别截图对比
3. 面板展开/折叠状态截图对比

### 测试配置

- 属性测试库: fast-check
- 最小迭代次数: 100
- 测试标签格式: `**Feature: workspace-responsive-layout, Property {number}: {property_text}**`
