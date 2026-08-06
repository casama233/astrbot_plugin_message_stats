"""QQ 官方 Bot 平台辅助模块

参考 astrbot_plugin_meme_api_python 的实现，为 QQ 官方机器人
(qq_official / qq_official_webhook) 提供头像与昵称获取能力。

官方机器人与 OneBot(QQ 号) 的差异：
- 用户标识是 32 位 openid，而非数字 QQ 号，无法用 q*.qlogo.cn/g?nk= 拼接头像；
  头像需通过 https://q.qlogo.cn/qqapp/{appid}/{openid}/0 获取（依赖 bot 的 appid）。
- 没有 get_group_member_info / get_group_member_list 之类的接口可按 openid
  反查昵称；成员昵称只在其发言时携带于 d.author.username。因此这里在成员发言
  时缓存 openid -> 昵称，供后续引用复用。
"""

from urllib.parse import quote

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent

QQ_OFFICIAL_AVATAR_URL_TEMPLATE = "https://q.qlogo.cn/qqapp/{appid}/{user_id}/0"
OFFICIAL_PLATFORMS = {"qq_official", "qq_official_webhook"}

# openid -> 昵称 缓存（成员发言时填充，供 @ 引用等场景复用）
_OFFICIAL_NICK_CACHE: dict = {}
_OFFICIAL_NICK_CACHE_MAX = 2000


def platform_name(event: AstrMessageEvent) -> str:
    """返回事件所属平台的规范化名称（小写）。"""
    get_platform_name = getattr(event, "get_platform_name", None)
    if callable(get_platform_name):
        try:
            name = str(get_platform_name() or "").strip().lower()
            if name:
                return name
        except Exception:
            pass
    meta = getattr(event, "platform_meta", None)
    return str(getattr(meta, "name", "") or "").strip().lower()


def is_official_platform(event: AstrMessageEvent) -> bool:
    """判断事件是否来自 QQ 官方机器人平台。"""
    return platform_name(event) in OFFICIAL_PLATFORMS


def platform_client(event: AstrMessageEvent) -> object:
    """返回事件底层的平台 client/bot 实例。"""
    return getattr(event, "client", None) or getattr(event, "bot", None)


def official_bot_appid(event: AstrMessageEvent) -> str:
    """解析构建官方头像所需的 appid。"""
    client = platform_client(event)
    platform = getattr(client, "platform", None)
    for source in (platform, client, getattr(event, "platform_meta", None)):
        appid = getattr(source, "appid", None)
        if appid:
            return str(appid).strip()
    return ""


def official_avatar_url(event: AstrMessageEvent, user_id: str) -> str:
    """为官方机器人成员 openid 构建头像 URL；appid 不可用时返回空串。"""
    user_id = str(user_id or "").strip()
    if not user_id:
        return ""
    appid = official_bot_appid(event)
    if not appid:
        logger.debug("QQ 官方 Bot appid 不可用，无法获取头像")
        return ""
    return QQ_OFFICIAL_AVATAR_URL_TEMPLATE.format(
        appid=quote(appid, safe=""), user_id=quote(user_id, safe="")
    )


def _raw_event_dict(event: AstrMessageEvent) -> dict:
    """定位事件中的原始平台负载字典。"""
    message_obj = getattr(event, "message_obj", None)
    for value in (
        getattr(message_obj, "raw_message", None),
        getattr(message_obj, "raw_event", None),
        getattr(event, "raw_message", None),
        getattr(event, "raw_event", None),
    ):
        if isinstance(value, dict):
            return value
    return {}


def _official_author_payload(event: AstrMessageEvent) -> object:
    """定位事件上的 QQ 官方消息 author 对象/字典。"""
    message_obj = getattr(event, "message_obj", None)
    for raw in (
        getattr(message_obj, "raw_message", None),
        getattr(message_obj, "raw_event", None),
        getattr(event, "raw_message", None),
    ):
        if raw is None:
            continue
        author = getattr(raw, "author", None)
        if author is not None:
            return author
        if isinstance(raw, dict):
            data = raw.get("d") if isinstance(raw.get("d"), dict) else raw
            if isinstance(data, dict) and isinstance(data.get("author"), dict):
                return data["author"]
    return None


def official_author_fields(event: AstrMessageEvent) -> tuple:
    """提取当前官方消息作者的 (openid, username)；两值均可能为空。"""
    author = _official_author_payload(event)
    if author is None:
        return "", ""
    if isinstance(author, dict):
        user_id = str(
            author.get("member_openid")
            or author.get("user_openid")
            or author.get("id")
            or ""
        ).strip()
        name = str(author.get("username") or "").strip()
        return user_id, name
    user_id = str(
        getattr(author, "member_openid", "")
        or getattr(author, "user_openid", "")
        or getattr(author, "id", "")
        or ""
    ).strip()
    name = str(getattr(author, "username", "") or "").strip()
    return user_id, name


def _official_mention_payload(event: AstrMessageEvent) -> list:
    """定位官方消息 mentions 列表（频道/群 @ 负载携带 openid + username）。"""
    message_obj = getattr(event, "message_obj", None)
    for raw in (
        getattr(message_obj, "raw_message", None),
        getattr(message_obj, "raw_event", None),
        getattr(event, "raw_message", None),
    ):
        if raw is None:
            continue
        mentions = getattr(raw, "mentions", None)
        if isinstance(mentions, list) and mentions:
            return mentions
        if isinstance(raw, dict):
            data = raw.get("d") if isinstance(raw.get("d"), dict) else raw
            if isinstance(data, dict) and isinstance(data.get("mentions"), list):
                return data["mentions"]
    return []


def official_mention_fields(event: AstrMessageEvent) -> list:
    """从官方 mentions 负载提取 (openid, username) 列表；可能为空。"""
    results = []
    for entry in _official_mention_payload(event):
        if isinstance(entry, dict):
            user_id = str(
                entry.get("member_openid")
                or entry.get("user_openid")
                or entry.get("openid")
                or entry.get("id")
                or ""
            ).strip()
            name = str(entry.get("username") or entry.get("nick") or "").strip()
        else:
            user_id = str(
                getattr(entry, "member_openid", "")
                or getattr(entry, "user_openid", "")
                or getattr(entry, "openid", "")
                or getattr(entry, "id", "")
                or ""
            ).strip()
            name = str(
                getattr(entry, "username", "") or getattr(entry, "nick", "") or ""
            ).strip()
        if user_id or name:
            results.append((user_id, name))
    return results


def _remember_official_nick(user_id: str, name: str) -> None:
    """缓存官方成员 openid -> 昵称（FIFO 淘汰，限制容量）。"""
    user_id = str(user_id or "").strip()
    name = str(name or "").strip()
    if not user_id or not name or user_id == name:
        return
    if user_id in _OFFICIAL_NICK_CACHE:
        _OFFICIAL_NICK_CACHE.pop(user_id, None)
    elif len(_OFFICIAL_NICK_CACHE) >= _OFFICIAL_NICK_CACHE_MAX:
        _OFFICIAL_NICK_CACHE.pop(next(iter(_OFFICIAL_NICK_CACHE)), None)
    _OFFICIAL_NICK_CACHE[user_id] = name


def official_cached_nick(user_id: str) -> str:
    """返回已缓存的官方成员昵称，未命中返回空串。"""
    return _OFFICIAL_NICK_CACHE.get(str(user_id or "").strip(), "")


def cache_official_author_nick(event: AstrMessageEvent) -> None:
    """缓存当前官方消息作者及被 @ 成员的 openid -> 昵称。

    官方机器人只在成员发言时于 d.author.username 暴露昵称，且无接口按
    openid 反查昵称。发言/被 @ 时缓存，可供后续引用复用。
    """
    if not is_official_platform(event):
        return
    author_id, author_name = official_author_fields(event)
    if author_id and author_name:
        _remember_official_nick(author_id, author_name)
    for mention_id, mention_name in official_mention_fields(event):
        if mention_id and mention_name:
            _remember_official_nick(mention_id, mention_name)


def resolve_official_nickname(event: AstrMessageEvent, user_id: str) -> str:
    """尽力解析官方成员昵称：当前作者 > 被 @ 成员 > 缓存。"""
    user_id = str(user_id or "").strip()
    if not user_id:
        return ""
    author_id, author_name = official_author_fields(event)
    if author_id == user_id and author_name:
        _remember_official_nick(user_id, author_name)
        return author_name
    for mention_id, mention_name in official_mention_fields(event):
        if mention_id == user_id and mention_name:
            _remember_official_nick(user_id, mention_name)
            return mention_name
    return official_cached_nick(user_id)
