# 更新日志

## v1.8.5 (2026-05-03)

### 🐛 Bug 修复

- **修复 `_handle_command_exception()` 缺少 `yield` 关键字**：`event.plain_result()` 是生成器方法，直接调用无法发送消息到聊天中。已将方法重构为仅记录日志，避免静默失败。

- **修复昵称双重 HTML 转义导致显示乱码**：`validate_nickname()` 原本使用 `html.escape()` 转义后存储，渲染图片时又再次转义，导致昵称出现 `&lt;` 等双重转义乱码。已修复：存储时不再做 HTML 转义，统一在渲染阶段进行一次转义。

- **修复 `_get_avatar_url()` 处理 Telegram 负数用户 ID 时的潜在崩溃**：`int(user_id) % 5` 对负数字符串 ID 直接 `int()` 转换可能抛出异常。现已改用 `abs(int(user_id))` 取绝对值，并添加 `ValueError`/`TypeError` 兜底处理。

- **修复定时推送没有数据的问题**：`timer_manager._filter_data_by_rank_type()` 只检查旧的 `user.history` 列表来判断用户是否有发言记录，但新版数据改用 `_message_dates` 字典存储。修复方案：添加 `user._ensure_message_dates()` 兜底保护，并同时检查 `_message_dates` 和 `history`。

### 🚀 性能与内存优化

- **修复群组锁清理条件缺陷**：`_get_group_lock()` 的过期锁清理条件原为 `len > 100 and len % 100 == 0`，导致 101~199 个锁时不会触发清理。现已改为 `>= 100 and (len % 50 == 0 or len > 1000)`，确保锁数量持续增长时仍能自动清理。

- **`_dirty_cache` 添加大小上限**：原脏缓存字典无容量限制，高负载场景下大量群组数据长期驻留内存。现已添加 500 条上限，达到上限时强制立即写盘防止内存泄漏。

## v1.8.2 (2026-05-03)

### 🐛 Bug 修复

- **修复数据丢失问题**：`data_cache`（TTL=5分钟）过期后，`get_group_data` 从文件重新加载数据，但 `GroupDataStore` 的延迟批量写入策略（积累10次修改才写盘一次）导致文件中的数据不是最新的，从而丢失了部分消息记录。修复方案：`get_group_data` 优先检查 `_dirty_cache`（延迟写入缓存），确保获取到最新的内存数据。

- **修复今日发言榜无法使用的问题**：数据存储格式升级后（从 `history` 列表改为 `_message_dates` 字典），排行榜计算逻辑未同步更新。修复方案：`_calculate_daily_rank` 和 `_calculate_period_rank_optimized` 改用 `user.get_message_count_in_period()` 方法，兼容新旧两种数据格式。

### 🚀 性能优化

- **浏览器懒加载与高并发支持**：引入了浏览器并发计数器和异步锁，实现"懒加载且支持高并发"。渲染和截图过程在互相独立的 Page 标签页中并行执行，完美解决了之前高并发下图片串台、以及因强行关闭浏览器导致的 `Target closed` 报错问题，兼顾了低内存占用与高并发性能。
- **按天聚合字典存储**：10万条消息最多 365 个键值对，内存占用从 O(n) 降到 O(365)。
- **延迟批量写入优化**：积累 10 次修改后批量写盘，减少磁盘 I/O 约 90%。
- **群组锁自动清理**：`_group_locks` 字典增加 TTL 机制，自动清理超过 1 小时未使用的锁，防止长期运行的内存泄漏。
- **批量写入循环优化**：增加 60 秒超时兜底写入，防止数据长时间滞留在内存中丢失；优化 `asyncio.wait` 为 `asyncio.wait_for`，减少不必要的 Task 创建。

### ✨ 新功能

- **发言里程碑推送**：当用户发言达到里程碑次数时，自动推送个人成就卡片。
- **更新日志文档**：新增 `CHANGELOG.md` 更新日志。

### 🔧 其他改进

- 插件关闭时确保脏缓存数据落盘（`flush_all`）。
- 紧凑 JSON 格式（`indent=None, separators=(',', ':')`），文件体积减少约 50%。
- 优化异常处理，替换过于宽泛的 `except Exception` 为具体异常类型。
