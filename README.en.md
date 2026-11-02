# AstrBot Group Message Statistics Plugin

[简体中文](README.md) · [繁體中文](README.zh-TW.md) · **English**

> Some plugin code was generated with AI assistance.

Track group-chat message counts and generate leaderboards. Includes image/text/PDF rendering, scheduled reports, individual milestone cards and custom fonts.

![Leaderboard preview](https://s41.ax1x.com/2026/05/22/pmpwlSx.png)

## Installation

Download `astrbot_plugin_message_stats.zip`, extract it under `/AstrBot/data/plugins/`, and restart AstrBot. Alternatively:

```bash
cd /AstrBot/data/plugins/
git clone https://github.com/xiaoruange39/astrbot_plugin_message_stats.git
```

The URL above is the **original upstream author repository**. This maintained fork is [casama233/astrbot_plugin_message_stats](https://github.com/casama233/astrbot_plugin_message_stats); clone that repository if you intend to use its changes.

## Commands

**Copy the original Simplified Chinese commands exactly.** Translating this README does not imply English command aliases.

| Command | Purpose |
| --- | --- |
| `#发言榜帮助` | Visual command guide; aliases include `#发言帮助`, `#发言榜菜单`, `#水群榜帮助`, `#发言统计帮助` |
| `#发言榜` | All-time rankings |
| `#今日发言榜`, `#昨日发言榜` | Today/yesterday |
| `#本周发言榜`, `#本月发言榜` | Weekly/monthly rankings |
| `#本年发言榜`, `#去年发言榜` | Current/previous year |
| `#设置发言榜数量 [数量]` | Set leaderboard size (1–100) |
| `#设置发言榜图片 [模式]` | Image mode (1) or text mode (0) |
| `#清除发言榜单` | Clear this group's statistics |
| `#查看发言`, `#查询发言`, `#我的发言` | Inspect own/selected member's activity |
| `#发言榜里程碑` | Personal milestone card |
| `#刷新发言榜群成员缓存`, `#发言榜缓存状态` | Refresh/inspect member cache |
| `#发言榜定时状态`, `#手动推送发言榜` | View scheduled state or push now |
| `#设置发言榜定时时间 [时间]` | Set push time |
| `#设置发言榜定时群组 [群号]`, `#删除发言榜定时群组 [群号]` | Add/remove target groups |
| `#启用发言榜定时`, `#禁用发言榜定时` | Start/stop scheduled push |
| `#设置发言榜定时类型 [类型]` | Select ranking period |

The help image is cached by commands, theme, fonts and version. If Playwright or image rendering fails, a text response can be used instead.

## Configuration

Use AstrBot WebUI (recommended), commands or `data/config.json`.

| Setting | Default | Purpose |
| --- | --- | --- |
| `theme` | `default` | Other themes: `cartoon_light`, `cartoon_dark`, `liquid_glass`, `liquid_glass_dark` |
| `font_path` | Empty | Custom font file path |
| `auto_theme_switch` | `false` | Automatically switch light/dark themes |
| `theme_switch_light_time`, `theme_switch_dark_time` | `06:00`, `18:00` | Theme schedules |
| `rand` | `20` | Leaderboard count (1–100) |
| `render_mode` | `playwright` | `playwright`, `t2i`, `text`, `pdf`; fallback on failure |
| `detailed_logging_enabled` | `true` | Verbose logging |
| `timer_enabled` | `false` | Scheduled leaderboard push |
| `timer_push_time` | `09:00` | HH:MM or cron |
| `timer_target_groups` | `[]` | Group IDs or UMOs |
| `timer_rank_type` | `daily` | `daily`, `total`, `weekly`, `monthly`, `yearly`, `lastyear` |
| `milestone_enabled` | `false` | Milestone push |
| `milestone_targets` | `[666,1000,2333,5000,6666,10000,23333]` | Trigger thresholds |
| `blocked_users`, `blocked_groups` | `[]` | Exclusion lists |
| `tg_bot_token`, `dc_bot_token` | Empty | Optional Telegram/Discord avatar tokens |
| `llm_enabled` | `false` | LLM-generated personalized titles |
| `llm_provider_id` | Empty | LLM provider ID, default when unset |
| `llm_system_prompt` | Default prompt | Titles/style/color prompt |
| `llm_max_retries` | `2` | Retry limit |
| `llm_min_daily_messages` | `0` | Minimum daily messages for titles |
| `llm_enable_on_manual` | `false` | Invoke LLM during manual view, may incur token cost |

**Do not expose bot tokens** or account-specific configuration in public issues.

## PDF export across containers

`render_mode=pdf` uses local Chromium to generate PDF leaderboards. If AstrBot and OneBot/NapCat/Lagrange run in **different containers or hosts**, OneBot may not be able to read AstrBot's `/tmp` path (`retcode 1200`). Configure **`callback_api_base` in AstrBot's main configuration** to an AstrBot address reachable from the OneBot process, e.g. `http://astrbot:6185` on a shared Docker network. This lets AstrBot register the file as a download URL. Without it, PDF failures fall back to an image with a warning.

Image modes (`playwright`/`t2i`) transmit Base64 instead. QQ Official Bot, Telegram, Discord and Lark upload raw files and are unaffected by this OneBot path issue.

## Fonts and supported platforms

Supported fonts: `.ttf`, `.otf`, `.woff`, `.woff2`, `.ttc`. Use Plugin Pages' font manager to upload/select fonts, automatically setting `font_path`, or use absolute/relative paths. The plugin also checks `fonts/` and data-directory `resources/fonts/`. Invalid fonts fall back to defaults; cache changes are detected by path, modification time and size.

Supported platforms: **QQ (OneBot), Telegram, Discord and Lark/Feishu**.

Key files: `main.py`, `metadata.yaml`, `_conf_schema.json`, `data/`, `templates/`, `utils/`. See the [canonical Simplified Chinese README](README.md) for the complete directory listing and historical changelog.

## License, author and credits

[MIT](LICENSE). Original author **[xiaoruange39](https://github.com/xiaoruange39)**. This repository is a fork of [xiaoruange39/astrbot_plugin_message_stats](https://github.com/xiaoruange39/astrbot_plugin_message_stats) and retains the upstream MIT copyright notice. Thanks to AstrBot, [yunzai-plugin-example](https://github.com/KaedeharaLu/yunzai-plugin-example) and contributors. Fork changes do not relicense third-party assets, data or dependencies.
