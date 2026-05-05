🌐 **Язык / Language / 语言:** [中文](https://github.com/xiaoruange39/astrbot_plugin_message_stats/blob/main/README.md) | [English](https://github.com/xiaoruange39/astrbot_plugin_message_stats/blob/main/README_EN.md) | [**Русский**](https://github.com/xiaoruange39/astrbot_plugin_message_stats/blob/main/README_RU.md)

![:name](https://count.getloli.com/@astrbot_plugin_message_stats?name=astrbot_plugin_message_stats&theme=green&padding=7&offset=0&align=top&scale=1&pixelated=1&darkmode=auto&prefix=0)

# AstrBot Статистика сообщений групп

> 🤖 **Этот плагин создан с помощью ИИ**

Мощный плагин статистики сообщений для AstrBot, автоматически отслеживающий количество сообщений участников группы и создающий рейтинги.

![Preview](https://github.com/xiaoruange39/Plugin-Preview-Image/blob/main/image/E2EB0A38BA876A2227FA99D997CA1969.jpg) 

## 🚀 Установка

### Способ 1: Прямая загрузка
1. Скачайте архив плагина `astrbot_plugin_message_stats.zip`
2. Распакуйте в директорию плагинов AstrBot: `/AstrBot/data/plugins/`
3. Перезапустите AstrBot

### Способ 2: Git клонирование
```bash
cd /AstrBot/data/plugins/
git clone https://github.com/xiaoruange39/astrbot_plugin_message_stats.git
```

## 📖 Использование

### Основные команды

#### Просмотр рейтингов
- `#рейтинг` - Общий рейтинг
- `#сегодня` - Рейтинг за сегодня  
- `#неделя` - Рейтинг за неделю
- `#месяц` - Рейтинг за месяц
- `#год` - Рейтинг за год
- `#прошлый` - Рейтинг за прошлый год
- `#достижение` - Карточка достижений

#### Команды управления
- `#set_rank_count [число]` - Установить количество отображаемых (1-100)
- `#set_image_mode [режим]` - Режим отображения (1=изображение, 0=текст)
- `#clear_ranking` - Очистить данные группы

#### Команды таймера
- `#timer_status` - Статус таймера
- `#manual_push` - Ручная отправка рейтинга
- `#set_timer_time [время]` - Установить время отправки
- `#enable_timer` - Включить таймер
- `#disable_timer` - Отключить таймер

### Примеры использования

```
#рейтинг
Общий рейтинг
Всего: 156
━━━━━━━━━━━━━━
#1: Сяо Мин · 45 раз (28.85%)
#2: Сяо Хун · 32 раз (20.51%)
#3: Сяо Ган · 28 раз (17.95%)
```

## ⚙️ Настройка

### Параметры плагина

| Параметр | Тип | По умолч. | Описание |
|----------|-----|-----------|----------|
| `theme` | string | `default` | Тема оформления рейтинга |
| `auto_theme_switch` | bool | `false` | Авто переключение темы |
| `rand` | int | `20` | Количество участников в рейтинге |
| `if_send_pic` | string | `Изображение` | Режим вывода |
| `timer_enabled` | bool | `false` | Включить авторассылку |
| `timer_push_time` | string | `09:00` | Время рассылки |
| `timer_rank_type` | string | `daily` | Тип рейтинга для рассылки |
| `milestone_enabled` | bool | `false` | Отправка при достижении milestone |
| `blocked_users` | list | `[]` | Заблокированные пользователи |
| `blocked_groups` | list | `[]` | Заблокированные группы |
| `llm_enabled` | bool | `false` | LLM анализ титулов |
| `llm_provider_id` | string | `` | ID LLM провайдера |
| `image_language` | string | `zh-CN` | Язык изображения: `zh-CN`/`en-US`/`ru-RU` |

### Настройка изображений
Выберите язык в WebUI → Настройки плагина → **Язык изображения**:
- Китайский (zh-CN)
- English (en-US)
- Русский (ru-RU)

## 🌐 Поддержка языков

Плагин поддерживает три языка:
- **中文（zh-CN）** - Китайский (по умолчанию)
- **English（en-US）** - Английский
- **Русский（ru-RU）** - Русский

### Алиасы команд
- `#leaderboard` / `#发言榜` → аналог `#рейтинг`
- `#today` / `#今日发言榜` → аналог `#сегодня`
- `#week` / `#本周发言榜` → аналог `#неделя`
- `#month` / `#本月发言榜` → аналог `#месяц`
- `#year` / `#本年发言榜` → аналог `#год`
- `#lastyear` / `#去年发言榜` → аналог `#прошлый`
- `#milestone` / `#发言榜里程碑` → аналог `#достижение`

## 📁 Структура файлов

```
astrbot_plugin_message_stats/
├── main.py                 # Главная программа
├── metadata.yaml          # Метаданные плагина
├── README.md              # Документация (китайский)
├── README_EN.md           # Английская документация
├── README_RU.md           # Русская документация
├── requirements.txt       # Зависимости
├── _conf_schema.json      # Схема конфигурации
├── .astrbot-plugin/
│   └── i18n/             # Файлы перевода
│       ├── zh-CN.json    # Китайский перевод
│       ├── en-US.json    # Английский перевод
│       └── ru-RU.json    # Русский перевод
└── utils/                # Модули
```

## 📄 Лицензия

MIT License

---

**Если этот плагин вам помог, поставьте ⭐!**
