"""帮助菜单内容定义。

指令清单集中在此维护，图片渲染与文字回退共用同一份数据，
保证两种输出永远一致；内容变化时帮助图片的缓存键也会随之变化。
"""

from typing import Any, Dict, List


HELP_TITLE = "发言榜帮助"
HELP_SUBTITLE = "群发言统计插件 · 指令速查"

# 每个指令项：
#   cmd    指令名（不含唤醒前缀）
#   args   参数说明，可为空
#   desc   功能说明
#   alias  别名，可为空
#   admin  是否需要管理员权限
HELP_SECTIONS: List[Dict[str, Any]] = [
    {
        "icon": "🏆",
        "title": "排行榜",
        "items": [
            {
                "cmd": "发言榜",
                "args": "[日期]",
                "desc": "群总排行榜，可跟日期或日期区间",
                "alias": "水群榜 / B话榜 / 发言排行 / 发言统计",
            },
            {
                "cmd": "今日发言榜",
                "desc": "今天的发言排行",
                "alias": "今日水群榜 / 今日发言排行 / 今日B话榜",
            },
            {
                "cmd": "昨日发言榜",
                "desc": "昨天的发言排行",
                "alias": "昨天发言榜 / 昨日排行 / 昨日水群榜",
            },
            {
                "cmd": "本周发言榜",
                "desc": "本周的发言排行",
                "alias": "本周水群榜 / 本周发言排行",
            },
            {
                "cmd": "本月发言榜",
                "desc": "本月的发言排行",
                "alias": "本月水群榜 / 本月发言排行",
            },
            {
                "cmd": "本年发言榜",
                "desc": "今年的发言排行",
                "alias": "年榜 / 本年水群榜 / 本年发言排行",
            },
            {
                "cmd": "去年发言榜",
                "desc": "去年的发言排行",
                "alias": "去年水群榜 / 去年发言排行",
            },
        ],
    },
    {
        "icon": "👤",
        "title": "个人统计",
        "items": [
            {
                "cmd": "查看发言",
                "args": "[@某人 或 ID]",
                "desc": "查看自己或他人的发言资料卡",
                "alias": "查询发言 / 我的发言",
            },
            {
                "cmd": "发言榜里程碑",
                "desc": "查看自己的里程碑成就卡片",
                "alias": "发言里程碑",
            },
            {
                "cmd": "发言榜帮助",
                "desc": "显示本帮助菜单",
                "alias": "发言帮助 / 发言榜菜单 / 水群榜帮助",
            },
        ],
    },
    {
        "icon": "⚙️",
        "title": "管理设置",
        "items": [
            {
                "cmd": "设置发言榜数量",
                "args": "[5-50]",
                "desc": "设置排行榜显示人数",
                "admin": True,
            },
            {
                "cmd": "设置发言榜图片",
                "args": "[图片/文字]",
                "desc": "切换排行榜的图片或文字输出",
                "admin": True,
            },
            {
                "cmd": "清除发言榜单",
                "desc": "清空本群的全部发言数据",
                "admin": True,
            },
            {
                "cmd": "刷新发言榜群成员缓存",
                "desc": "重新拉取群成员昵称",
                "admin": True,
            },
            {
                "cmd": "发言榜缓存状态",
                "desc": "查看缓存命中与占用情况",
            },
        ],
    },
    {
        "icon": "⏰",
        "title": "定时推送",
        "items": [
            {
                "cmd": "发言榜定时状态",
                "desc": "查看定时推送配置",
            },
            {
                "cmd": "手动推送发言榜",
                "desc": "立刻推送一次排行榜",
                "admin": True,
            },
            {
                "cmd": "设置发言榜定时时间",
                "args": "[HH:MM]",
                "desc": "设置每日推送时间",
                "admin": True,
            },
            {
                "cmd": "设置发言榜定时群组",
                "args": "[群号]",
                "desc": "添加推送目标群",
                "admin": True,
            },
            {
                "cmd": "删除发言榜定时群组",
                "args": "[群号]",
                "desc": "移除推送目标群",
                "admin": True,
            },
            {
                "cmd": "设置发言榜定时类型",
                "args": "[日榜/周榜/月榜]",
                "desc": "设置推送的榜单类型",
                "admin": True,
            },
            {
                "cmd": "启用发言榜定时",
                "desc": "开启定时推送",
                "admin": True,
            },
            {
                "cmd": "禁用发言榜定时",
                "desc": "关闭定时推送",
                "admin": True,
            },
        ],
    },
]

HELP_TIPS: List[str] = [
    "直接发送「2026年6月1日发言榜」可查询指定日期，用「-」连接两个日期查询区间",
    "带 👑 的指令需要管理员权限",
    "主题、字体、里程碑等更多设置请在 AstrBot 插件配置页调整",
]


def format_command(item: Dict[str, Any], prefix: str = "/") -> str:
    """拼出带唤醒前缀和参数的完整指令文本"""
    text = f"{prefix}{item['cmd']}"
    args = item.get("args")
    if args:
        text = f"{text} {args}"
    return text


def build_help_sections(prefix: str = "/") -> List[Dict[str, Any]]:
    """生成渲染用的章节数据（指令已带上唤醒前缀）

    注意：指令列表的键名为 commands 而非 items，
    避免 Jinja2 把 section.items 解析成字典自带的 items 方法。
    """
    sections = []
    for section in HELP_SECTIONS:
        commands = []
        for item in section["items"]:
            commands.append({
                "command": format_command(item, prefix),
                "desc": item.get("desc", ""),
                "alias": item.get("alias", ""),
                "admin": bool(item.get("admin")),
            })
        sections.append({
            "icon": section.get("icon", ""),
            "title": section.get("title", ""),
            "commands": commands,
        })
    return sections


def build_help_text(prefix: str = "/") -> str:
    """生成文字版帮助，用于图片渲染不可用时的回退输出"""
    lines = [f"📊 {HELP_TITLE} · {HELP_SUBTITLE}"]

    for section in HELP_SECTIONS:
        lines.append("")
        lines.append(f"【{section.get('icon', '')} {section.get('title', '')}】")
        for item in section["items"]:
            crown = " 👑" if item.get("admin") else ""
            lines.append(f"· {format_command(item, prefix)}{crown} - {item.get('desc', '')}")
            alias = item.get("alias")
            if alias:
                lines.append(f"  别名: {alias}")

    if HELP_TIPS:
        lines.append("")
        lines.append("💡 小提示")
        for tip in HELP_TIPS:
            lines.append(f"· {tip}")

    return "\n".join(lines)
