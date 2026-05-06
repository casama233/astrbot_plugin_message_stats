# 更新日志

## v1.9.2 (2026-05-07)

### 🐛 Bug 修复

- **临时文件泄漏全面修复**：`_check_milestone()`、`show_my_milestone()`、`_push_to_group()` 三处清理代码不在 try/finally 中，send_message 抛异常时跳过清理导致 tmp 文件残留。已修复：全部改用 try/finally 确保清理。
- **异常关闭时 tmp 文件残留**：插件被 kill -9/OOM/断电时 finally 不会执行。已修复：新增 `_cleanup_stale_temp_files()`，启动时扫描清理。
- **删除冗余的 `_calculate_daily_rank` 方法**：与 `_calculate_period_rank_optimized` 逻辑重复，统一走批量优化路径。

### 🔧 其他改进

- **main.py 精简**：删除 10 个无用的委托包装方法，合并重复 except 块，精简 docstring。
- **版本号更新至 1.9.2**：main.py 和 metadata.yaml 同步更新。

## v1.9.1 (2026-05-07)

- 跨平台真实头像获取（TG Bot API / Discord CDN）
- i18n 国际化文件全面优化
- 新增 `tg_bot_token` / `dc_bot_token` 配置项
- 新增 `aiohttp>=3.9.0` 依赖
- LLM 头衔持久化，重启后保留
- LLM 头衔稳定不变，新增用户才触发 LLM
- 头像跨平台支持（QQ qlogo / TG/DC 彩色文字回退）
- 定时任务改用文件锁防止重复推送
- 国际化文案覆盖问题修复

## v1.9.0 (2026-05-05)


- Web 数据管理面板大升级
- 群组数据删除功能
- 群名称持久化缓存
- 多项 Bug 修复
- Web 面板支持跟随系统深色/浅色模式

## v1.8.8 (2026-05-05)

- 放宽排行榜昵称显示限制
- 修复图片生成失败时 tmp 文件积累
- 修复手动查询里程碑后 tmp 文件不清理
- unified_msg_origin 持久化

## v1.8.7 (2026-05-04)

- LLM 头衔配色大师
- 修复定时推送头衔颜色丢失
- 修复 LLM 头衔不显示的问题
- 修复头衔显示为字典字符串
- 修复头衔颜色硬编码
- 修复头衔徽章垂直不对齐
- LLM 分析范围与排行榜显示人数绑定
- 修复 Fallback 渲染路径忽略头衔颜色
- 优化 Web 面板配置文案

## v1.8.5 (2026-05-04)

- 修复 `_handle_command_exception` 缺少 yield
- 修复昵称双重 HTML 转义
- 修复 TG 负数用户 ID 崩溃
- 修复定时推送没有数据
- 修复群组锁清理条件缺陷
- dirty_cache 添加大小上限

## v1.8.2 (2026-05-03)

- 修复数据丢失问题
- 修复今日发言榜无法使用
- 浏览器懒加载与高并发支持
- 按天聚合字典存储优化
- 延迟批量写入优化
- 发言里程碑推送
- 新增更新日志文档
- 紧凑 JSON 格式，文件体积减少约 50%
