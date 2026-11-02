# AstrBot 群組發言統計插件

[简体中文](README.md) · **繁體中文** · [English](README.en.md)

> 此插件由 AI 輔助編寫。

AstrBot 群組訊息統計插件，統計使用者發言次數、產生排行榜，提供圖像／文字／PDF 呈現、排程推送、里程碑卡片及自訂字型。

![排行榜預覽](https://s41.ax1x.com/2026/05/22/pmpwlSx.png)

## 安裝

可下載 `astrbot_plugin_message_stats.zip`，解壓至 `/AstrBot/data/plugins/` 並重啟 AstrBot；亦可安裝來源倉庫：

```bash
cd /AstrBot/data/plugins/
git clone https://github.com/xiaoruange39/astrbot_plugin_message_stats.git
```

以上 Git 位址是**原作者上游**，本分支倉庫為 [casama233/astrbot_plugin_message_stats](https://github.com/casama233/astrbot_plugin_message_stats)。使用本維護分支時請改為複製此 fork。

## 指令

命令須使用**實際的簡體中文指令名稱**；翻譯說明不代表新增繁中命令別名。

| 指令 | 用途 |
| --- | --- |
| `#发言榜帮助` | 顯示指令說明圖片；支援 `#发言帮助`、`#发言榜菜单`、`#水群榜帮助`、`#发言统计帮助` 等別名 |
| `#发言榜` | 全期間排行榜 |
| `#今日发言榜`、`#昨日发言榜` | 今日／昨日排行榜 |
| `#本周发言榜`、`#本月发言榜` | 週／月排行 |
| `#本年发言榜`、`#去年发言榜` | 年度／上年排行榜 |
| `#设置发言榜数量 [数量]` | 設定榜單顯示 1–100 人 |
| `#设置发言榜图片 [模式]` | 設為圖片（1）或文字（0） |
| `#清除发言榜单` | 清除本群發言數據 |
| `#查看发言`、`#查询发言`、`#我的发言` | 查詢自己或指定群員的發言 |
| `#发言榜里程碑` | 查看個人里程碑卡片 |
| `#刷新发言榜群成员缓存`、`#发言榜缓存状态` | 更新、檢查群員快取 |
| `#发言榜定时状态`、`#手动推送发言榜` | 查看排程或手動推送 |
| `#设置发言榜定时时间 [时间]` | 調整推送時間 |
| `#设置发言榜定时群组 [群号]`、`#删除发言榜定时群组 [群号]` | 管理目標群組，可一次設定多群 |
| `#启用发言榜定时`、`#禁用发言榜定时` | 啟停排程 |
| `#设置发言榜定时类型 [类型]` | 設定推送排行種類 |

幫助圖片會依指令、字型、主題、版本快取；缺少 Playwright 或渲染失敗時可退回文字。

## 設定

可在 AstrBot WebUI（建議）、指令或 `data/config.json` 管理。

| 欄位 | 預設 | 用途 |
| --- | --- | --- |
| `theme` | `default` | `cartoon_light`、`cartoon_dark`、`liquid_glass`、`liquid_glass_dark` 等主題 |
| `font_path` | 空 | 自訂字型路徑 |
| `auto_theme_switch` | `false` | 按時段切換深淺色 |
| `theme_switch_light_time`、`theme_switch_dark_time` | `06:00`、`18:00` | 自動切換時間 |
| `rand` | `20` | 顯示人數，1–100 |
| `render_mode` | `playwright` | `playwright`／`t2i`／`text`／`pdf`；失敗退回圖片或文字 |
| `detailed_logging_enabled` | `true` | 詳細日誌 |
| `timer_enabled` | `false` | 自動推送 |
| `timer_push_time` | `09:00` | HH:MM 或 cron |
| `timer_target_groups` | `[]` | 群 ID 或 UMO |
| `timer_rank_type` | `daily` | `daily`／`total`／`weekly`／`monthly`／`yearly`／`lastyear` |
| `milestone_enabled` | `false` | 發言里程碑推送 |
| `milestone_targets` | `[666,1000,2333,5000,6666,10000,23333]` | 里程碑次數 |
| `blocked_users`、`blocked_groups` | `[]` | 排除使用者／群組 |
| `tg_bot_token`、`dc_bot_token` | 空 | 可選 Telegram／Discord 頭像擷取憑證 |
| `llm_enabled` | `false` | 讓 LLM 生成發言頭銜 |
| `llm_provider_id` | 空 | LLM Provider ID，空白使用預設 |
| `llm_system_prompt` | 預設提示詞 | 頭銜風格／配色 |
| `llm_max_retries` | `2` | 失敗重試 |
| `llm_min_daily_messages` | `0` | 頭銜最低發言數 |
| `llm_enable_on_manual` | `false` | 手動查詢時也用 LLM，可能產生 Token 花費 |

**不要公開 Bot Token** 或包含帳號識別的配置檔。

## PDF 與多容器部署

`render_mode=pdf` 時，排行榜使用本地 Chromium 產生 PDF。若 AstrBot 與 OneBot／NapCat／Lagrange 分處不同容器或主機，OneBot 可能無法讀取 AstrBot 本機 `/tmp`，出現 `retcode 1200`。請在 **AstrBot 主配置**設定 OneBot 能連到的 `callback_api_base`，例如同 Docker 網路的 `http://astrbot:6185`。它會讓 AstrBot 提供可下載的 HTTP 檔案連結；未設定且 PDF 失敗時插件會退回圖片並提示。

圖片 `playwright`／`t2i` 以 Base64 傳送，不依賴此設定。QQ 官方 Bot、Telegram、Discord、飛書等直接上傳位元組，也不受上述 OneBot 路徑限制。

## 字型與跨平台

支援 `.ttf`、`.otf`、`.woff`、`.woff2`、`.ttc`。可在 Plugin Pages「字型管理」上傳並自動更新 `font_path`，或使用絕對／相對路徑；會尋找插件的 `fonts/` 與資料目錄的 `resources/fonts/`。無效字型回退主題預設；依檔案路徑、時間及大小更新快取。

支援 **QQ（OneBot）、Telegram、Discord、飛書（Lark）**。

主要來源：`main.py`、`metadata.yaml`、`_conf_schema.json`、`data/`、`templates/`、`utils/`；完整檔案清單及歷史更新紀錄見[簡中主文件](README.md)。

## 授權、作者及致謝

[MIT](LICENSE)。原作者 **[xiaoruange39](https://github.com/xiaoruange39)**，本倉庫為 [xiaoruange39/astrbot_plugin_message_stats](https://github.com/xiaoruange39/astrbot_plugin_message_stats) 的 fork，保留原版 MIT 署名。感謝 AstrBot、[yunzai-plugin-example](https://github.com/KaedeharaLu/yunzai-plugin-example) 與所有貢獻者。Fork 修改不改變第三方素材、資料及依賴的權利。
