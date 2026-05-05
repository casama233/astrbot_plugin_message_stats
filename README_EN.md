🌐 **Language / 语言 / Язык:** [中文](https://github.com/xiaoruange39/astrbot_plugin_message_stats/blob/main/README.md) | [**English**](https://github.com/xiaoruange39/astrbot_plugin_message_stats/blob/main/README_EN.md) | [Русский](https://github.com/xiaoruange39/astrbot_plugin_message_stats/blob/main/README_RU.md)

![:name](https://count.getloli.com/@astrbot_plugin_message_stats?name=astrbot_plugin_message_stats&theme=green&padding=7&offset=0&align=top&scale=1&pixelated=1&darkmode=auto&prefix=0)

# AstrBot Group Message Stats Plugin

> 🤖 **This plugin was generated with AI assistance**

A powerful AstrBot group message statistics plugin that automatically tracks group member message counts and generates leaderboards.

![Preview](https://github.com/xiaoruange39/Plugin-Preview-Image/blob/main/image/E2EB0A38BA876A2227FA99D997CA1969.jpg) 

## 🚀 Installation

### Method 1: Direct Download
1. Download the plugin package `astrbot_plugin_message_stats.zip`
2. Extract to AstrBot plugin directory: `/AstrBot/data/plugins/`
3. Restart AstrBot

### Method 2: Git Clone
```bash
cd /AstrBot/data/plugins/
git clone https://github.com/xiaoruange39/astrbot_plugin_message_stats.git
```

## 📖 Usage

### Basic Commands

#### View Leaderboards
- `#leaderboard` - View all-time leaderboard
- `#today` - View today's leaderboard  
- `#week` - View this week's leaderboard
- `#month` - View this month's leaderboard
- `#year` - View this year's leaderboard
- `#lastyear` - View last year's leaderboard
- `#milestone` - View personal milestone card

#### Management Commands
- `#set_rank_count [number]` - Set leaderboard display count (1-100)
- `#set_image_mode [mode]` - Set display mode (1=image, 0=text)
- `#clear_ranking` - Clear group message data

#### Cache Management
- `#refresh_cache` - Refresh group member cache
- `#cache_status` - View cache status

#### Timer Commands
- `#timer_status` - View timer status
- `#manual_push` - Manual leaderboard push
- `#set_timer_time [time]` - Set timer push time
- `#set_timer_groups [group_id]` - Add timer push groups
- `#remove_timer_groups [group_id]` - Remove timer push groups
- `#enable_timer` - Enable timer push
- `#disable_timer` - Disable timer push
- `#set_timer_type [type]` - Set timer leaderboard type

### Usage Examples

```
#leaderboard
All-Time Leaderboard
Total: 156
━━━━━━━━━━━━━━
#1: Xiao Ming · 45 times (28.85%)
#2: Xiao Hong · 32 times (20.51%)
#3: Xiao Gang · 28 times (17.95%)
```

```
#set_rank_count 10
Leaderboard display count set to 10!
```

```
#set_image_mode 1
Display mode set to image!
```

## ⚙️ Configuration

### Plugin Settings

| Config | Type | Default | Description |
|--------|------|--------|-------------|
| `theme` | string | `default` | Leaderboard theme style: `default`, `liquid_glass`, `liquid_glass_dark` |
| `auto_theme_switch` | bool | `false` | Auto switch light/dark theme based on time |
| `theme_switch_light_time` | string | `06:00` | Light theme start time, format HH:MM |
| `theme_switch_dark_time` | string | `18:00` | Dark theme start time, format HH:MM |
| `rand` | int | `20` | Leaderboard display count (1-100) |
| `if_send_pic` | string | `Image` | Output mode: `Image` or `Text` |
| `detailed_logging_enabled` | bool | `true` | Enable detailed logging |
| `timer_enabled` | bool | `false` | Enable scheduled leaderboard push |
| `timer_push_time` | string | `09:00` | Push time (HH:MM or cron format) |
| `timer_target_groups` | list | `[]` | Target group IDs for push |
| `timer_rank_type` | string | `daily` | Push leaderboard type: `daily`/`total`/`weekly`/`monthly`/`yearly`/`lastyear` |
| `milestone_enabled` | bool | `false` | Milestone push when user reaches message milestones |
| `milestone_targets` | list | `[666, 1000, 2333, 5000, 6666, 10000, 23333]` | Milestone trigger counts |
| `blocked_users` | list | `[]` | Blocked user IDs |
| `blocked_groups` | list | `[]` | Blocked group IDs |
| `llm_enabled` | bool | `false` | Enable LLM title analysis for scheduled push |
| `llm_provider_id` | string | `` | LLM Provider ID, leave empty for default |
| `llm_system_prompt` | text | default prompt | Customize title generation prompt |
| `llm_max_retries` | int | `2` | LLM retry count on failure |
| `llm_min_daily_messages` | int | `0` | Min daily messages for LLM title generation |
| `llm_enable_on_manual` | bool | `false` | Also analyze LLM titles on manual queries (uses Tokens) |
| `image_language` | string | `zh-CN` | Image language: `zh-CN` Chinese/`en-US` English/`ru-RU` Russian |

### Configuration Methods
1. AstrBot Web Panel (recommended)
2. Command configuration
3. Edit config file: `data/config.json`

## 🌐 Multi-language Support

This plugin supports the following languages:

- **中文（zh-CN）** - Default language
- **English（en-US）** - English
- **Русский（ru-RU）** - Russian

### Plugin Card Localization
Plugin name, description, and config texts are translated via `.astrbot-plugin/i18n/*.json`. The WebUI will automatically display the correct language based on your browser settings.

### Leaderboard Image Language
You can choose the language for leaderboard images in WebUI → Plugin Settings → **Image Language**:
- Chinese (zh-CN)
- English (en-US)  
- Russian (ru-RU)

### Command Aliases
The plugin supports command aliases in Chinese, English, and Russian:
- `#leaderboard` / `#рейтинг` → Same as `#发言榜`
- `#today` / `#сегодня` → Same as `#今日发言榜`
- `#week` / `#неделя` → Same as `#本周发言榜`
- `#month` / `#месяц` → Same as `#本月发言榜`
- `#year` / `#год` → Same as `#本年发言榜`
- `#lastyear` / `#прошлый` → Same as `#去年发言榜`
- `#milestone` / `#достижение` → Same as `#发言榜里程碑`

### Web Page Localization
The statistics dashboard page (`pages/overview/index.html`) automatically detects your browser language and displays the interface in Chinese, English, or Russian.

## 📁 File Structure

```
astrbot_plugin_message_stats/
├── main.py                 # Main program
├── metadata.yaml          # Plugin metadata
├── README.md              # Chinese documentation
├── README_EN.md           # English documentation
├── requirements.txt       # Dependencies
├── config.yaml           # Config file
├── example_config.json   # Config example
├── _conf_schema.json     # Config schema (Web UI definition)
├── .astrbot-plugin/       # AstrBot plugin resources
│   └── i18n/             # Internationalization files
│       ├── zh-CN.json    # Chinese translation
│       ├── en-US.json    # English translation
│       └── ru-RU.json    # Russian translation
├── data/                 # Data directory
├── templates/            # HTML templates
└── utils/                # Utility modules
```

## 🌐 Platform Support

- **QQ (OneBot)** - Full support
- **Telegram** - Full support
- **Discord** - Full support
- **Lark/Feishu** - Full support

## 📝 Changelog

### v1.9.1 (2026-05-05)
- ✅ Plugin internationalization (zh-CN/en-US/ru-RU)
- ✅ Page i18n (auto-detect browser language)
- ✅ Leaderboard image multi-language
- ✅ Milestone card multi-language
- ✅ LLM Token text translation
- ✅ New `image_language` config option

### v1.9.0 (2026-05-05)
- ✅ Web panel overhaul
- ✅ Data deletion from Web UI
- ✅ Group name persistence
- ✅ Various bug fixes

## 📄 License

MIT License

## 👨‍💻 Author

**xiaoruange39**
- GitHub: [@xiaoruange39](https://github.com/xiaoruange39)

---

**If this plugin helps you, please give it a ⭐!**
