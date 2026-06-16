from dataclasses import dataclass
from typing import Any, Iterable, Optional


@dataclass(frozen=True)
class GroupMessageSnapshot:
    nickname: str
    group_name: Optional[str] = None


def _clean_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _read_value(source: Any, key: str) -> Any:
    if source is None:
        return None
    if isinstance(source, dict):
        return source.get(key)
    return getattr(source, key, None)


def _iter_sources(event: Any) -> Iterable[Any]:
    if event is None:
        return

    seen = set()
    stack = [event]
    attr_names = (
        "raw_event",
        "message_obj",
        "message_event",
        "platform_event",
        "original_event",
        "event",
        "raw_message",
    )

    while stack:
        current = stack.pop(0)
        marker = id(current)
        if current is None or marker in seen:
            continue
        seen.add(marker)
        yield current

        for name in attr_names:
            nested = _read_value(current, name)
            if nested is not None:
                stack.append(nested)


def _read_event_sender_name(event: Any) -> Optional[str]:
    if event is None or not hasattr(event, "get_sender_name"):
        return None
    try:
        return _clean_text(event.get_sender_name())
    except Exception:
        return None


def extract_group_name_from_event(event: Any) -> Optional[str]:
    for source in _iter_sources(event):
        group_name = _clean_text(_read_value(source, "group_name"))
        if group_name:
            return group_name
    return None


def extract_group_message_snapshot(event: Any, user_id: str) -> GroupMessageSnapshot:
    framework_sender_name = _read_event_sender_name(event)
    card = None
    base_nickname = None
    group_name = None

    for source in _iter_sources(event):
        sender = _read_value(source, "sender")
        if sender is not None:
            if card is None:
                card = _clean_text(_read_value(sender, "card"))
            if base_nickname is None:
                base_nickname = _clean_text(_read_value(sender, "nickname"))

        if card is None:
            card = _clean_text(_read_value(source, "card"))
        if base_nickname is None:
            base_nickname = _clean_text(_read_value(source, "nickname"))
        if group_name is None:
            group_name = _clean_text(_read_value(source, "group_name"))

        if card and base_nickname and group_name:
            break

    nickname = framework_sender_name or card or base_nickname or f"用户{user_id}"
    return GroupMessageSnapshot(nickname=nickname, group_name=group_name)
