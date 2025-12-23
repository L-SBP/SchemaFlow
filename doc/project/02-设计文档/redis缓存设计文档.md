# Redis 缓存设计文档

## 1. 概述

本文档描述了项目中公告功能的 Redis 缓存实现方案。通过引入 Redis 缓存，可以显著提升公告查询的性能，减少数据库访问压力。

## 2. 缓存策略

### 2.1 缓存范围

- **公告列表缓存**：只缓存已发布（published）状态的公告列表
- **公告详情缓存**：只缓存已发布（published）状态的公告详情
- **未发布、草稿、已下架等状态的公告不缓存**

### 2.2 缓存键设计

#### 2.2.1 公告列表缓存键

```
announcement:list:published:page_{page}:size_{page_size}
```

示例：
- `announcement:list:published:page_1:size_10`
- `announcement:list:published:page_2:size_20`

#### 2.2.2 公告详情缓存键

```
announcement:detail:{announcement_id}
```

示例：
- `announcement:detail:1`
- `announcement:detail:100`

### 2.3 缓存过期时间

- **过期时间**：3600 秒（1 小时）
- **过期策略**：自动过期 + 主动清除

## 3. 实现架构

### 3.1 组件层次

```
API 层 (announcement.py)
    ↓
CRUD 层 (crud_announcement.py)
    ↓
缓存服务层 (announcement_cache_service.py)
    ↓
Redis 连接层 (redis.py)
```

### 3.2 数据流程

#### 3.2.1 查询流程

1. **列表查询**：
   - 用户请求公告列表
   - CRUD 层检查是否为已发布状态
   - 尝试从 Redis 获取缓存
   - 缓存命中：返回缓存数据
   - 缓存未命中：查询数据库 → 转换数据格式 → 存入缓存 → 返回数据

2. **详情查询**：
   - 用户请求公告详情
   - CRUD 层检查公告状态
   - 尝试从 Redis 获取缓存
   - 缓存命中：返回缓存数据
   - 缓存未命中：查询数据库 → 转换数据格式 → 存入缓存 → 返回数据

#### 3.2.2 更新流程

1. **创建公告**：
   - 如果状态为已发布，创建后清除列表缓存
   - 如果状态为草稿，不操作缓存

2. **更新公告**：
   - 更新数据库
   - 清除列表缓存
   - 清除详情缓存

3. **删除公告**：
   - 删除数据库记录
   - 清除列表缓存
   - 清除详情缓存

## 4. 核心实现

### 4.1 缓存服务类

`AnnouncementCacheService` 提供以下核心方法：

#### 4.1.1 列表缓存方法

- `get_list_from_cache(page, page_size)`：从缓存获取列表
- `set_list_to_cache(page, page_size, total, items)`：设置列表缓存
- `invalidate_list_cache()`：清除列表缓存

#### 4.1.2 详情缓存方法

- `get_detail_from_cache(announcement_id)`：从缓存获取详情
- `set_detail_to_cache(announcement_id, announcement_data)`：设置详情缓存
- `invalidate_detail_cache(announcement_id)`：清除详情缓存

#### 4.1.3 辅助方法

- `invalidate_all_announcement_cache()`：清除所有公告缓存
- `get_fresh_data_from_db(db, page, page_size)`：从数据库获取最新数据

### 4.2 CRUD 层集成

在 `crud_announcement.py` 中：

1. **查询时**：优先从缓存获取，未命中则查询数据库并缓存
2. **创建时**：如果是已发布状态，清除列表缓存
3. **更新时**：清除列表和详情缓存
4. **删除时**：清除列表和详情缓存

## 5. 性能优化

### 5.1 缓存命中率

- 只缓存已发布状态的公告，避免无效缓存
- 合理的过期时间（1小时），平衡数据一致性和性能
- 分页缓存，避免大列表一次性加载

### 5.2 内存使用

- 使用 SCAN 命令清除缓存，避免 KEYS 命令阻塞
- JSON 序列化存储，压缩数据大小
- 合理的过期时间，自动清理过期数据

### 5.3 并发安全

- Redis 本身是单线程，保证操作原子性
- 使用 `setex` 命令保证设置和过期时间的原子性
- 数据库操作和缓存操作分离，避免事务冲突

## 6. 监控和维护

### 6.1 日志记录

所有缓存操作都有日志记录：

- 缓存命中：`Cache hit for announcement list: {key}`
- 缓存设置：`Cache set for announcement list: {key}`
- 缓存清除：`Deleted announcement list cache keys: {keys}`
- 错误日志：`Error getting announcement list from cache: {error}`

### 6.2 Redis 连接管理

- 使用 `get_redis()` 获取连接
- 连接不可用时自动降级到数据库查询
- 服务启动时初始化 Redis 连接

## 7. 扩展性

### 7.1 其他功能的缓存

此缓存架构可以轻松扩展到其他功能：

1. **用户信息缓存**：用户资料、权限等
2. **项目信息缓存**：项目列表、项目详情等
3. **知识库缓存**：知识文档、FAQ 等

### 7.2 缓存策略调整

可以根据实际需求调整：

1. **过期时间**：根据数据更新频率调整
2. **缓存粒度**：可以按用户、角色等维度缓存
3. **缓存层级**：可以添加多级缓存（本地缓存 + Redis）

## 8. 注意事项

### 8.1 数据一致性

- 缓存是最终一致的，不是强一致
- 允许 1 小时内的数据延迟
- 重要操作后主动清除缓存

### 8.2 Redis 可用性

- Redis 不可用时，系统自动降级到数据库查询
- 不会因为 Redis 故障导致系统不可用
- 建议配置 Redis 高可用（主从、哨兵或集群）

### 8.3 内存管理

- 定期监控 Redis 内存使用情况
- 根据实际情况调整过期时间
- 必要时可以清理过期缓存

## 9. 测试

### 9.1 单元测试

提供了测试脚本 `test_announcement_cache.py`，测试：

- 缓存设置和获取
- 缓存清除功能
- Redis 连接管理

### 9.2 集成测试

建议测试场景：

1. **正常流程**：查询 → 缓存命中 → 更新 → 缓存清除 → 重新查询
2. **并发场景**：多个用户同时查询和更新
3. **异常场景**：Redis 不可用、网络异常等

## 10. 部署建议

### 10.1 Redis 配置

```yaml
# redis.conf 建议配置
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### 10.2 监控指标

建议监控以下指标：

- 缓存命中率
- Redis 内存使用率
- Redis 连接数
- 缓存操作延迟

### 10.3 备份策略

- 定期备份 Redis 数据
- 配置持久化（RDB + AOF）
- 考虑跨机房备份

## 11. 总结

通过引入 Redis 缓存，公告功能的性能得到了显著提升：

1. **性能提升**：减少数据库查询，提升响应速度
2. **扩展性**：架构清晰，易于扩展到其他功能
3. **可靠性**：Redis 不可用时自动降级，不影响系统运行
4. **可维护性**：代码结构清晰，日志完善，易于维护

此缓存方案为项目的性能优化奠定了良好基础，后续可以逐步扩展到其他高频查询的功能模块。
