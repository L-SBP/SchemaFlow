# Requirements Document

## Introduction

本文档定义了项目概览栏显示优化的需求，主要解决项目卡片的用户体验问题，包括：
1. 移除进入工作区按钮，点击卡片直接进入项目
2. 增加鼠标悬停浮动提示效果
3. 优化项目名显示，长名称使用省略号
4. 重新设计卡片布局，包括图标、状态和操作按钮的位置
5. 优化项目详情显示和日期格式

## Glossary

- **Project_Overview**: 项目概览栏，显示所有项目的卡片列表
- **Project_Card**: 项目卡片，显示单个项目的基本信息
- **Database_Icon**: 数据库类型图标，显示项目使用的数据库类型（MySQL、PostgreSQL、SQLite）
- **Project_Status**: 项目状态，显示项目当前状态（active、inactive等）
- **Hover_Tooltip**: 鼠标悬停提示，显示完整的项目信息
- **Action_Buttons**: 操作按钮，包括编辑和删除按钮
- **Project_Details**: 项目详情，包括完整的项目描述信息

## Requirements

### Requirement 1: 项目卡片交互优化

**User Story:** As a user, I want to click directly on project cards to enter the workspace, so that I can access projects more efficiently without extra button clicks.

#### Acceptance Criteria

1. WHEN a user clicks anywhere on a Project_Card, THE system SHALL navigate directly to the project workspace
2. THE Project_Card SHALL remove the dedicated "进入工作区" button
3. WHEN a user hovers over a Project_Card, THE card SHALL show visual feedback indicating it's clickable
4. THE Project_Card click area SHALL exclude the Action_Buttons to prevent accidental navigation during edit/delete operations
5. THE Project_Card SHALL use cursor pointer to indicate clickable areas

### Requirement 2: 鼠标悬停浮动提示

**User Story:** As a user, I want to see detailed project information when hovering over project cards, so that I can quickly review project details without opening the project.

#### Acceptance Criteria

1. WHEN a user hovers over a Project_Card, THE system SHALL display a Hover_Tooltip with complete project information
2. THE Hover_Tooltip SHALL include project name, full description, database type, status, and last updated date
3. THE Hover_Tooltip SHALL appear after 500ms hover delay and disappear immediately when mouse leaves
4. THE Hover_Tooltip SHALL be positioned to avoid viewport edges and remain fully visible
5. THE Hover_Tooltip SHALL use a distinct visual style (shadow, border, background) to stand out from the card

### Requirement 3: 项目名称显示优化

**User Story:** As a user, I want project names to be displayed consistently regardless of length, so that the card layout remains uniform and readable.

#### Acceptance Criteria

1. WHEN a project name exceeds 6 characters, THE Project_Card SHALL truncate the name with ellipsis (...)
2. THE truncated project name SHALL show the full name in the Hover_Tooltip
3. THE project name text SHALL use a consistent font size and weight across all cards
4. THE project name SHALL be left-aligned with the Database_Icon
5. THE project name truncation SHALL preserve readability by showing at least the first 6 meaningful characters

### Requirement 4: 数据库类型图标显示

**User Story:** As a user, I want to quickly identify the database type of each project through visual icons, so that I can easily distinguish between different project types.

#### Acceptance Criteria

1. THE Project_Card SHALL display a Database_Icon on the left side of the project name
2. WHEN the database type is "mysql", THE system SHALL display the MySQL logo icon
3. WHEN the database type is "postgresql", THE system SHALL display the PostgreSQL logo icon  
4. WHEN the database type is "sqlite", THE system SHALL display the SQLite logo icon
5. THE Database_Icon SHALL be 20x20 pixels with 8px margin from the project name
6. IF the database type is unknown or null, THEN THE system SHALL display a generic database icon

### Requirement 5: 操作按钮布局优化

**User Story:** As a user, I want the edit and delete buttons to be compact and well-positioned, so that they don't interfere with the card's main content while remaining easily accessible.

#### Acceptance Criteria

1. THE Action_Buttons (edit and delete) SHALL be positioned in the top-right corner of the Project_Card
2. THE Action_Buttons SHALL use a compact design with reduced width compared to the current implementation
3. THE Action_Buttons SHALL maintain minimum 32x32 pixel clickable area for accessibility
4. THE Action_Buttons SHALL use icon-only display with tooltips for space efficiency
5. THE Action_Buttons SHALL have 4px spacing between them and 8px margin from card edges

### Requirement 6: 项目状态显示重新定位

**User Story:** As a user, I want to see the project status clearly positioned in the card layout, so that I can quickly identify active and inactive projects.

#### Acceptance Criteria

1. THE Project_Status SHALL be displayed in the bottom-left corner of the Project_Card
2. THE Project_Status SHALL replace the current database type display in the bottom-left position
3. THE Project_Status SHALL use a badge-style design with appropriate color coding (green for active, gray for inactive)
4. THE Project_Status text SHALL be capitalized and use a small font size (12px)
5. THE Project_Status SHALL have 8px margin from the card edges

### Requirement 7: 项目详情显示优化

**User Story:** As a user, I want to access complete project descriptions when they don't fit in the card display, so that I can read full project information without losing context.

#### Acceptance Criteria

1. WHEN the project description exceeds the available card space, THE Project_Card SHALL truncate the description with ellipsis
2. THE Project_Card SHALL provide a "查看完整详情" clickable text or icon when description is truncated
3. WHEN a user clicks "查看完整详情", THE system SHALL display the full description in a modal or expanded view
4. THE full description modal SHALL include all project information (name, description, database type, status, dates)
5. THE modal SHALL be dismissible by clicking outside, pressing ESC, or clicking a close button

### Requirement 8: 日期显示格式优化

**User Story:** As a user, I want project dates to be displayed in a readable and consistent format, so that I can easily understand when projects were last updated.

#### Acceptance Criteria

1. THE Project_Card SHALL display the updated_at date in "YYYY-MM-DD HH:mm" format
2. THE Project_Card SHALL remove the date refresh icon to simplify the layout
3. THE date display SHALL be positioned in the bottom-right corner of the card
4. THE date SHALL use a muted color (gray) and smaller font size (11px) to de-emphasize it
5. IF the date is from today, THEN THE system SHALL display "今天 HH:mm" instead of the full date

### Requirement 9: 卡片整体布局协调

**User Story:** As a user, I want all project cards to have a consistent and visually appealing layout, so that the project overview looks professional and organized.

#### Acceptance Criteria

1. THE Project_Card SHALL maintain consistent dimensions (width and height) across all cards
2. THE Project_Card SHALL use consistent spacing and margins for all internal elements
3. THE Project_Card SHALL have a subtle hover effect (elevation or border change) to indicate interactivity
4. THE Project_Card layout SHALL be responsive and adapt to different screen sizes
5. THE Project_Card SHALL ensure all text remains readable and all interactive elements remain accessible at minimum supported screen width (320px)